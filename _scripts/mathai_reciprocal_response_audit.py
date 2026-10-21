#!/usr/bin/env python3
"""
MATH-AI — live reciprocal-reviewer response audit.

READ ONLY. Does not send reminders or modify OpenReview.

Compares each active submission's reciprocal reviewer against the actual
Reviewers / Invited / Declined group memberships. OpenReview may return
reciprocal_reviewer as a one-element list (e.g. ['~First_Last1']) rather than
a bare string; normalize_profile_id() handles both.

Submissions exempted from reciprocal reviewing can be skipped with
--exempt <number> [<number> ...].

Outputs (default: openreview/mathai_reciprocal_response_audit/):
  mathai_reciprocal_response_audit/
    reciprocal_reviewer_status.csv
    reciprocal_reviewers_pending.txt
    reciprocal_reviewers_declined.txt
    reciprocal_reviewers_not_found.txt
    summary.txt
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from collections import defaultdict

try:
    import openreview
except ImportError:
    sys.exit("Install first: python -m pip install -U openreview-py")

VENUE = "NeurIPS.cc/2026/Workshop/MATH-AI"
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "openreview" / "mathai_reciprocal_response_audit"


def value_of(v):
    """Unwrap API-v2 content objects of the form {'value': ...}."""
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    return v


def flatten(note):
    return {k: value_of(v) for k, v in (note.content or {}).items()}


def normalize_profile_id(v):
    """
    Convert an OpenReview field value into one bare profile ID.

    Handles:
      '~First_Last1'
      ['~First_Last1']
      {'value': '~First_Last1'}
      {'value': ['~First_Last1']}
    """
    v = value_of(v)

    if v is None:
        return ""

    if isinstance(v, (list, tuple)):
        if len(v) == 0:
            return ""
        if len(v) != 1:
            raise ValueError(
                f"Expected one reciprocal reviewer but found {len(v)} values: {v!r}"
            )
        v = value_of(v[0])

    if not isinstance(v, str):
        raise ValueError(f"Unexpected reciprocal reviewer value: {v!r}")

    return v.strip()


def normalize_member(v):
    """Normalize a group member for safe set comparison."""
    if isinstance(v, (list, tuple)) and len(v) == 1:
        v = v[0]
    return str(v).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", default=VENUE)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument(
        "--exempt",
        type=int,
        nargs="*",
        default=[],
        help="Submission numbers exempt from reciprocal reviewing (skipped entirely).",
    )
    ap.add_argument("--username", default=os.environ.get("OPENREVIEW_USERNAME"))
    ap.add_argument("--password", default=os.environ.get("OPENREVIEW_PASSWORD"))
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    if not args.username or not args.password:
        sys.exit("Set OPENREVIEW_USERNAME and OPENREVIEW_PASSWORD first.")

    client = openreview.api.OpenReviewClient(
        baseurl="https://api2.openreview.net",
        username=args.username,
        password=args.password,
    )

    venue = client.get_group(args.venue)
    active_venue_id = value_of(venue.content["submission_venue_id"])

    submissions = client.get_all_notes(content={"venueid": active_venue_id})
    submissions.sort(key=lambda n: n.number or 0)

    rr_to_papers = defaultdict(list)
    missing = []
    malformed = []
    exempted = []

    for note in submissions:
        c = flatten(note)
        if note.number in args.exempt:
            exempted.append((note.number, str(c.get("title") or "")))
            continue

        try:
            rid = normalize_profile_id(c.get("reciprocal_reviewer"))
        except Exception as e:
            malformed.append((note.number, str(c.get("title") or ""), repr(e)))
            continue

        if not rid:
            missing.append((note.number, str(c.get("title") or "")))
            continue

        rr_to_papers[rid].append((note.number, str(c.get("title") or "")))

    # Fetch the three recruitment-state groups directly.
    reviewers_group = client.get_group(f"{args.venue}/Reviewers")
    invited_group = client.get_group(f"{args.venue}/Reviewers/Invited")
    declined_group = client.get_group(f"{args.venue}/Reviewers/Declined")

    accepted = {normalize_member(x) for x in (reviewers_group.members or [])}
    invited = {normalize_member(x) for x in (invited_group.members or [])}
    declined = {normalize_member(x) for x in (declined_group.members or [])}

    if args.debug:
        print("DEBUG:")
        print("  first reciprocal reviewer IDs:", list(sorted(rr_to_papers))[:5])
        print("  first accepted members:", list(sorted(accepted))[:5])
        print("  first invited members:", list(sorted(invited))[:5])
        print("  first declined members:", list(sorted(declined))[:5])
        print()

    rows = []
    pending_ids = []
    declined_ids = []
    not_found_ids = []

    for rid in sorted(rr_to_papers):
        # Accepted takes precedence in case OpenReview retains a member in Invited.
        if rid in accepted:
            status = "ACCEPTED"
        elif rid in declined:
            status = "DECLINED"
            declined_ids.append(rid)
        elif rid in invited:
            status = "PENDING"
            pending_ids.append(rid)
        else:
            status = "NOT_FOUND_IN_RECRUITMENT_GROUPS"
            not_found_ids.append(rid)

        papers = rr_to_papers[rid]
        rows.append({
            "reciprocal_reviewer": rid,
            "status": status,
            "active_submission_count": len(papers),
            "paper_numbers": "; ".join(str(p[0]) for p in papers),
            "paper_titles": " | ".join(p[1] for p in papers),
        })

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "reciprocal_reviewer",
        "status",
        "active_submission_count",
        "paper_numbers",
        "paper_titles",
    ]
    with (out / "reciprocal_reviewer_status.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    def write_ids(filename, ids):
        (out / filename).write_text(
            "\n".join(ids) + ("\n" if ids else ""), encoding="utf-8"
        )

    write_ids("reciprocal_reviewers_pending.txt", pending_ids)
    write_ids("reciprocal_reviewers_declined.txt", declined_ids)
    write_ids("reciprocal_reviewers_not_found.txt", not_found_ids)

    counts = defaultdict(int)
    for row in rows:
        counts[row["status"]] += 1

    summary = [
        "MATH-AI reciprocal-reviewer response audit",
        "==========================================",
        f"Active submissions: {len(submissions)}",
        f"Exempted submissions: {len(exempted)}"
        + (
            f" ({', '.join(str(n) for n, _ in sorted(exempted))})"
            if exempted
            else ""
        ),
        f"Unique current reciprocal reviewers: {len(rr_to_papers)}",
        f"ACCEPTED: {counts['ACCEPTED']}",
        f"PENDING: {counts['PENDING']}",
        f"DECLINED: {counts['DECLINED']}",
        f"NOT_FOUND_IN_RECRUITMENT_GROUPS: {counts['NOT_FOUND_IN_RECRUITMENT_GROUPS']}",
        f"Malformed reciprocal-reviewer fields: {len(malformed)}",
        f"Active submissions missing reciprocal reviewer: {len(missing)}",
        "",
        "No OpenReview data was modified.",
    ]

    if malformed:
        summary += ["", "MALFORMED RECIPROCAL REVIEWER VALUES:"]
        summary += [
            f"  Paper {num}: {title} — {err}"
            for num, title, err in malformed[:20]
        ]

    (out / "summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")

    print("\n".join(summary))
    print()
    print("Pending reviewer IDs:", out / "reciprocal_reviewers_pending.txt")
    print("Declined reviewer IDs:", out / "reciprocal_reviewers_declined.txt")
    print("Not-found reviewer IDs:", out / "reciprocal_reviewers_not_found.txt")
    print("Full status CSV:", out / "reciprocal_reviewer_status.csv")


if __name__ == "__main__":
    main()
