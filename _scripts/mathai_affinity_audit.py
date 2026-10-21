#!/usr/bin/env python3
"""
READ-ONLY audit of MATH-AI 2026 reviewer affinity scores and conflicts.

OpenReview access performed:
  - get_group(...)
  - get_all_notes(...)
  - get_edges(..., head=<paper id>)

No OpenReview write/edit/delete/post methods are called.

Outputs (default: openreview/mathai_affinity_audit/):
  mathai_affinity_audit/summary.txt
  mathai_affinity_audit/paper_coverage.csv
  mathai_affinity_audit/reviewer_coverage.csv
  mathai_affinity_audit/papers_lt4_positive_nonconflicted.csv
  mathai_affinity_audit/score_distribution.csv
"""

import argparse
import csv
from collections import Counter
from pathlib import Path

import openreview

VENUE = "NeurIPS.cc/2026/Workshop/MATH-AI"
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "openreview" / "mathai_affinity_audit"


def unwrap(v):
    return v["value"] if isinstance(v, dict) and "value" in v else v


def note_venueid(note):
    try:
        return unwrap(note.content.get("venueid", ""))
    except Exception:
        return ""


def paper_title(note):
    try:
        return unwrap(note.content.get("title", "")) or ""
    except Exception:
        return ""


def paper_number(note):
    n = getattr(note, "number", "")
    if n not in (None, ""):
        return n
    try:
        v = unwrap(note.content.get("number", ""))
        return v or ""
    except Exception:
        return ""


def get_edges_for_paper(client, invitation, paper_id):
    """
    Read-only. Current OpenReview API requires invitation-only edge queries
    to include another selector. We query by head=<paper id>, which is both
    valid and exactly what this audit needs.
    """
    return client.get_edges(invitation=invitation, head=paper_id)


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", default=VENUE)
    ap.add_argument("--username", help="OpenReview username/email")
    ap.add_argument("--password", help="OpenReview password")
    ap.add_argument("--token", help="OpenReview bearer token")
    ap.add_argument("--outdir", default=DEFAULT_OUT)
    ap.add_argument(
        "--positive-threshold",
        type=float,
        default=0.0,
        help="Scores strictly greater than this count as positive (default: 0).",
    )
    args = ap.parse_args()

    venue = args.venue
    reviewers_group = venue + "/Reviewers"
    submission_invitation = venue + "/-/Submission"
    affinity_invitation = reviewers_group + "/-/Affinity_Score"
    conflict_invitation = reviewers_group + "/-/Conflict"

    kwargs = {"baseurl": "https://api2.openreview.net"}
    if args.username:
        kwargs["username"] = args.username
    if args.password:
        kwargs["password"] = args.password
    if args.token:
        kwargs["token"] = args.token

    client = openreview.api.OpenReviewClient(**kwargs)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("Fetching current Reviewers group (read-only)...")
    reviewers = set(client.get_group(reviewers_group).members)
    print(f"  reviewers: {len(reviewers)}")

    print("Fetching submissions (read-only)...")
    all_submissions = client.get_all_notes(invitation=submission_invitation)

    # Inspect the actual venueid values. For OpenReview venues, active papers
    # during review commonly have venueid = "<VENUE>/Submission", not <VENUE>.
    venueid_counts = Counter(note_venueid(n) for n in all_submissions)
    print(f"  all submission notes: {len(all_submissions)}")
    print("  venueid distribution:")
    for vid, count in sorted(venueid_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"    {count:4d}  {vid!r}")

    # Active submissions in the pre-decision review stage normally use
    # VENUE/Submission. Accept VENUE itself too, for compatibility with
    # venues whose configuration uses the base venue id.
    active_venueids = {venue, venue + "/Submission"}
    active_submissions = [
        n for n in all_submissions
        if note_venueid(n) in active_venueids
    ]

    # Robust fallback: if the venue uses another active-status venueid,
    # include venue-local submission IDs while excluding obvious terminal
    # statuses. This remains read-only and prints exactly what it selected.
    if not active_submissions:
        terminal_markers = (
            "withdraw", "desk_reject", "desk reject", "retract",
            "reject", "accept"
        )
        candidates = []
        for n in all_submissions:
            vid = note_venueid(n)
            low = str(vid).lower()
            if str(vid).startswith(venue) and not any(m in low for m in terminal_markers):
                candidates.append(n)
        active_submissions = candidates

    active_submissions.sort(key=lambda n: (paper_number(n) or 10**9, n.id))
    selected_ids = Counter(note_venueid(n) for n in active_submissions)

    print(f"  active submissions selected: {len(active_submissions)}")
    print("  selected venueid value(s):")
    for vid, count in sorted(selected_ids.items(), key=lambda x: (-x[1], x[0])):
        print(f"    {count:4d}  {vid!r}")

    if not active_submissions:
        raise RuntimeError(
            "No active submissions could be identified from the venueid "
            "values printed above. No OpenReview data was changed."
        )

    score_by_pair = {}
    conflicts = set()

    print("Fetching affinity/conflict edges paper-by-paper (read-only)...")
    for i, note in enumerate(active_submissions, 1):
        pid = note.id

        affinity_edges = get_edges_for_paper(
            client, affinity_invitation, pid
        )
        for e in affinity_edges:
            if e.tail not in reviewers:
                continue
            try:
                score = float(e.weight if e.weight is not None else 0.0)
            except Exception:
                score = 0.0
            score_by_pair[(pid, e.tail)] = score

        conflict_edges = get_edges_for_paper(
            client, conflict_invitation, pid
        )
        for e in conflict_edges:
            if e.tail in reviewers:
                conflicts.add((pid, e.tail))

        if i % 20 == 0 or i == len(active_submissions):
            print(f"  processed {i}/{len(active_submissions)} papers")

    threshold = args.positive_threshold

    reviewer_stats = {
        r: {
            "positive_nonconflicted": 0,
            "zero_nonconflicted": 0,
            "negative_nonconflicted": 0,
            "conflicts": 0,
            "missing_affinity_nonconflicted": 0,
        }
        for r in reviewers
    }

    dist = Counter()
    paper_rows = []
    total_missing_affinity = 0
    total_conflicted = 0

    for note in active_submissions:
        pid = note.id
        positive = zero = negative = missing = conflicted = 0
        positive_scores = []

        for rid in reviewers:
            pair = (pid, rid)

            if pair in conflicts:
                conflicted += 1
                reviewer_stats[rid]["conflicts"] += 1
                continue

            if pair not in score_by_pair:
                missing += 1
                total_missing_affinity += 1
                reviewer_stats[rid]["missing_affinity_nonconflicted"] += 1
                continue

            s = score_by_pair[pair]

            if s > threshold:
                positive += 1
                positive_scores.append(s)
                reviewer_stats[rid]["positive_nonconflicted"] += 1
                dist["positive"] += 1
            elif s == threshold:
                zero += 1
                reviewer_stats[rid]["zero_nonconflicted"] += 1
                dist["zero"] += 1
            else:
                negative += 1
                reviewer_stats[rid]["negative_nonconflicted"] += 1
                dist["negative"] += 1

        total_conflicted += conflicted

        paper_rows.append({
            "paper_id": pid,
            "paper_number": paper_number(note),
            "title": paper_title(note),
            "reviewers_total": len(reviewers),
            "conflicted_reviewers": conflicted,
            "eligible_nonconflicted": len(reviewers) - conflicted,
            "positive_score_nonconflicted": positive,
            "zero_score_nonconflicted": zero,
            "negative_score_nonconflicted": negative,
            "missing_affinity_nonconflicted": missing,
            "max_positive_score": max(positive_scores) if positive_scores else "",
            "mean_positive_score": (
                sum(positive_scores) / len(positive_scores)
                if positive_scores else ""
            ),
        })

    paper_rows.sort(
        key=lambda r: (
            r["positive_score_nonconflicted"],
            r["paper_number"] if isinstance(r["paper_number"], int) else 10**9,
            r["paper_id"],
        )
    )

    reviewer_rows = [
        {"reviewer_id": rid, **stats}
        for rid, stats in reviewer_stats.items()
    ]
    reviewer_rows.sort(
        key=lambda r: (r["positive_nonconflicted"], r["reviewer_id"])
    )

    buckets = Counter()
    for row in paper_rows:
        n = row["positive_score_nonconflicted"]
        if n == 0:
            buckets["0"] += 1
        elif n <= 3:
            buckets["1-3"] += 1
        elif n <= 9:
            buckets["4-9"] += 1
        elif n <= 19:
            buckets["10-19"] += 1
        else:
            buckets["20+"] += 1

    fields = [
        "paper_id", "paper_number", "title", "reviewers_total",
        "conflicted_reviewers", "eligible_nonconflicted",
        "positive_score_nonconflicted", "zero_score_nonconflicted",
        "negative_score_nonconflicted", "missing_affinity_nonconflicted",
        "max_positive_score", "mean_positive_score",
    ]

    write_csv(outdir / "paper_coverage.csv", paper_rows, fields)

    lt4 = [
        r for r in paper_rows
        if r["positive_score_nonconflicted"] < 4
    ]
    write_csv(
        outdir / "papers_lt4_positive_nonconflicted.csv",
        lt4,
        fields,
    )

    write_csv(
        outdir / "reviewer_coverage.csv",
        reviewer_rows,
        [
            "reviewer_id",
            "positive_nonconflicted",
            "zero_nonconflicted",
            "negative_nonconflicted",
            "conflicts",
            "missing_affinity_nonconflicted",
        ],
    )

    possible_pairs = len(active_submissions) * len(reviewers)
    edge_pairs = dist["positive"] + dist["zero"] + dist["negative"]
    write_csv(
        outdir / "score_distribution.csv",
        [
            {"category": "positive", "count": dist["positive"]},
            {"category": "zero", "count": dist["zero"]},
            {"category": "negative", "count": dist["negative"]},
            {
                "category": "missing_affinity_nonconflicted",
                "count": total_missing_affinity,
            },
            {"category": "conflicted", "count": total_conflicted},
            {"category": "all_paper_reviewer_pairs", "count": possible_pairs},
        ],
        ["category", "count"],
    )

    summary = [
        "MATH-AI 2026 Affinity / Conflict Audit",
        "=" * 42,
        "",
        "READ-ONLY: only get_group, get_all_notes, and get_edges were used.",
        "No OpenReview writes/edits/posts/deletes are present in this script.",
        "",
        f"Current reviewers: {len(reviewers)}",
        f"All submission notes: {len(all_submissions)}",
        f"Active submissions: {len(active_submissions)}",
        f"Affinity edges for active papers/current reviewers: {len(score_by_pair)}",
        f"Conflict edges for active papers/current reviewers: {len(conflicts)}",
        f"Possible active-paper/reviewer pairs: {possible_pairs}",
        "",
        f"Positive threshold: score > {threshold}",
        "Positive-score, non-conflicted reviewer coverage per paper:",
        f"  0:      {buckets['0']}",
        f"  1-3:    {buckets['1-3']}",
        f"  4-9:    {buckets['4-9']}",
        f"  10-19:  {buckets['10-19']}",
        f"  20+:    {buckets['20+']}",
        "",
        f"Papers with <4 positive-score non-conflicted reviewers: {len(lt4)}",
        "",
        "Pair counts:",
        f"  positive affinity: {dist['positive']}",
        f"  explicit zero affinity: {dist['zero']}",
        f"  negative affinity: {dist['negative']}",
        f"  missing affinity, non-conflicted: {total_missing_affinity}",
        f"  conflicts: {total_conflicted}",
        (
            "  explicit-zero share among pairs having an affinity edge: "
            f"{(dist['zero'] / edge_pairs if edge_pairs else 0):.2%}"
        ),
        "",
        "For your matcher JSON, missing affinity edges are especially important",
        'because your current score specification uses "default": 0.',
        "",
        "Interpretation for matcher demand = 4:",
    ]

    if not lt4:
        summary.append(
            "  Every active paper has at least 4 positive-affinity, "
            "non-conflicted reviewers."
        )
    else:
        summary.append(
            f"  {len(lt4)} active paper(s) have fewer than 4 positive-affinity, "
            "non-conflicted reviewers."
        )

    (outdir / "summary.txt").write_text(
        "\n".join(summary) + "\n",
        encoding="utf-8",
    )

    print()
    print("\n".join(summary))
    print()
    print(f"Reports written to: {outdir.resolve()}")


if __name__ == "__main__":
    main()
