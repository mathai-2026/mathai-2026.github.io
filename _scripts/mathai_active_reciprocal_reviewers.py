#!/usr/bin/env python3
"""
MATH-AI 2026: fetch ACTIVE submissions + reciprocal reviewers.

READ-ONLY:
- Does NOT invite reviewers.
- Does NOT modify groups.
- Does NOT post notes, edges, decisions, or messages.

Outputs (default: openreview/mathai_active/):
  mathai_active/
    active_submissions.csv
    reciprocal_reviewer_by_submission.csv
    reciprocal_reviewers_unique.csv
    summary.txt
    pdfs/submission_<N>.pdf

Venue:
  NeurIPS.cc/2026/Workshop/MATH-AI

Fields used:
  reciprocal_reviewer
  reciprocal_reviewing_agreement
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

try:
    import openreview
except ImportError:
    sys.exit(
        "Missing package: openreview-py\n"
        "Install with: python -m pip install -U openreview-py"
    )

VENUE_ID = "NeurIPS.cc/2026/Workshop/MATH-AI"
# Outputs contain submission PDFs; keep them in the git-ignored openreview/ folder.
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "openreview" / "mathai_active"
REVIEWER_FIELD = "reciprocal_reviewer"
AGREEMENT_FIELD = "reciprocal_reviewing_agreement"


def value_of(v: Any) -> Any:
    """OpenReview API v2 content fields are commonly {'value': ...}."""
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    return v


def flatten_content(note) -> Dict[str, Any]:
    return {k: value_of(v) for k, v in (note.content or {}).items()}


def stringify(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple, set)):
        return "; ".join(str(x) for x in v)
    return str(v)


def get_preferred_name(profile) -> str:
    """
    Best-effort preferred/full name extraction.
    Works even if preferred-email access is unavailable.
    """
    try:
        # Newer Profile convenience method.
        name = profile.get_preferred_name()
        if name:
            return str(name)
    except Exception:
        pass

    try:
        names = value_of(profile.content.get("names")) or []
        if isinstance(names, list):
            preferred = [n for n in names if isinstance(n, dict) and n.get("preferred")]
            candidates = preferred or names
            if candidates:
                n = candidates[0]
                if isinstance(n, dict):
                    fullname = n.get("fullname")
                    if fullname:
                        return str(fullname)
                    parts = [n.get("first"), n.get("middle"), n.get("last")]
                    return " ".join(str(x) for x in parts if x)
    except Exception:
        pass

    return ""


def get_preferred_email(profile) -> str:
    """
    Best effort. For some venues/users, OpenReview may not expose an
    unobfuscated preferred email unless the caller has the relevant permission.
    The profile ID is sufficient for later OpenReview recruitment.
    """
    try:
        email = profile.get_preferred_email()
        if email:
            return str(email)
    except Exception:
        pass

    try:
        email = value_of(profile.content.get("preferredEmail"))
        if email:
            return str(email)
    except Exception:
        pass

    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--venue", default=VENUE_ID)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--username", default=os.environ.get("OPENREVIEW_USERNAME"))
    parser.add_argument("--password", default=os.environ.get("OPENREVIEW_PASSWORD"))
    parser.add_argument(
        "--skip-pdfs",
        action="store_true",
        help="Fetch metadata/reviewers only; do not download PDFs."
    )
    args = parser.parse_args()

    if not args.username or not args.password:
        sys.exit(
            "Please set OPENREVIEW_USERNAME and OPENREVIEW_PASSWORD, e.g.\n\n"
            "  export OPENREVIEW_USERNAME='you@example.com'\n"
            "  export OPENREVIEW_PASSWORD='your-password'\n"
        )

    outdir = Path(args.out)
    pdfdir = outdir / "pdfs"
    outdir.mkdir(parents=True, exist_ok=True)
    if not args.skip_pdfs:
        pdfdir.mkdir(parents=True, exist_ok=True)

    # API v2 client.
    client = openreview.api.OpenReviewClient(
        baseurl="https://api2.openreview.net",
        username=args.username,
        password=args.password,
    )

    # ---------------------------------------------------------------
    # 1. Resolve the venue's CURRENT "under review" venueid.
    # ---------------------------------------------------------------
    venue = client.get_group(args.venue)

    if "submission_venue_id" not in venue.content:
        sys.exit(
            "Venue group does not contain submission_venue_id. "
            "Cannot safely distinguish active papers from desk-rejected/withdrawn ones."
        )

    active_venue_id = value_of(venue.content["submission_venue_id"])

    print(f"Venue: {args.venue}")
    print(f"Active/under-review venueid: {active_venue_id}")

    # This is the key filter. OpenReview documents submission_venue_id as
    # the status identifier for papers still under review.
    submissions = client.get_all_notes(
        content={"venueid": active_venue_id}
    )
    submissions.sort(key=lambda n: (n.number or 0))

    print(f"Active submissions found: {len(submissions)}")

    # ---------------------------------------------------------------
    # 2. Fetch active submission metadata + optionally PDFs.
    # ---------------------------------------------------------------
    active_rows: List[Dict[str, Any]] = []
    mapping_rows: List[Dict[str, Any]] = []
    reviewer_to_papers = defaultdict(list)
    reviewer_ids = set()

    pdf_ok_count = 0
    pdf_error_count = 0

    for i, note in enumerate(submissions, start=1):
        c = flatten_content(note)

        number = note.number
        title = stringify(c.get("title"))
        authors = stringify(c.get("authors"))
        reviewer_id = stringify(c.get(REVIEWER_FIELD)).strip()
        agreement = stringify(c.get(AGREEMENT_FIELD)).strip()
        pdf_value = c.get("pdf")

        print(f"[{i}/{len(submissions)}] Submission {number}: {title[:75]}")

        pdf_status = "SKIPPED" if args.skip_pdfs else ""
        pdf_file = ""

        if not args.skip_pdfs:
            if not pdf_value:
                pdf_status = "MISSING_PDF_FIELD"
                pdf_error_count += 1
            else:
                try:
                    pdf_bytes = client.get_attachment(
                        field_name="pdf",
                        id=note.id
                    )
                    pdf_path = pdfdir / f"submission_{number}.pdf"
                    pdf_path.write_bytes(pdf_bytes)
                    pdf_file = str(pdf_path)
                    pdf_status = "OK"
                    pdf_ok_count += 1
                except Exception as e:
                    pdf_status = f"DOWNLOAD_ERROR: {e!r}"
                    pdf_error_count += 1

        reviewer_missing = not bool(reviewer_id)
        agreement_missing = not bool(agreement)

        active_rows.append({
            "paper_number": number,
            "note_id": note.id,
            "title": title,
            "authors": authors,
            "venueid": stringify(c.get("venueid")),
            "reciprocal_reviewer": reviewer_id,
            "agreement_present": not agreement_missing,
            "pdf_status": pdf_status,
            "pdf_file": pdf_file,
        })

        mapping_rows.append({
            "paper_number": number,
            "note_id": note.id,
            "title": title,
            "reciprocal_reviewer": reviewer_id,
            "agreement_present": not agreement_missing,
            "reviewer_missing": reviewer_missing,
        })

        if reviewer_id:
            reviewer_ids.add(reviewer_id)
            reviewer_to_papers[reviewer_id].append({
                "paper_number": number,
                "title": title,
                "agreement_present": not agreement_missing,
            })

    # ---------------------------------------------------------------
    # 3. Resolve OpenReview profiles for reciprocal reviewers.
    #    This remains read-only.
    # ---------------------------------------------------------------
    profile_info: Dict[str, Dict[str, str]] = {}

    reviewer_id_list = sorted(reviewer_ids)
    if reviewer_id_list:
        print(f"\nResolving {len(reviewer_id_list)} unique reciprocal reviewer profiles...")

        # First try OpenReview's preferred-email mechanism for venue organizers.
        profiles = []
        preferred_emails_invitation = f"{args.venue}/-/Preferred_Emails"

        try:
            profiles = openreview.tools.get_profiles(
                client,
                reviewer_id_list,
                with_preferred_emails=preferred_emails_invitation
            )
        except Exception as e:
            print(
                "Preferred-email profile lookup was unavailable; "
                "falling back to ordinary profile lookup.\n"
                f"Reason: {e!r}"
            )
            try:
                profiles = openreview.tools.get_profiles(
                    client,
                    reviewer_id_list
                )
            except Exception as e2:
                print(f"Bulk profile lookup failed: {e2!r}")
                profiles = []

        # get_profiles normally preserves one result per requested identity,
        # but use profile.id as the authoritative key.
        for p in profiles or []:
            if p is None:
                continue
            pid = getattr(p, "id", "") or ""
            if pid:
                profile_info[pid] = {
                    "profile_resolved": "YES",
                    "reviewer_name": get_preferred_name(p),
                    "preferred_email": get_preferred_email(p),
                }

        # Resolve anything not returned in bulk, one by one.
        for rid in reviewer_id_list:
            if rid in profile_info:
                continue
            try:
                p = client.get_profile(rid)
                profile_info[rid] = {
                    "profile_resolved": "YES",
                    "reviewer_name": get_preferred_name(p),
                    "preferred_email": get_preferred_email(p),
                }
            except Exception as e:
                profile_info[rid] = {
                    "profile_resolved": "NO",
                    "reviewer_name": "",
                    "preferred_email": "",
                    "profile_error": repr(e),
                }

    # ---------------------------------------------------------------
    # 4. Build unique reviewer table and duplicate checks.
    # ---------------------------------------------------------------
    unique_rows = []

    for reviewer_id in reviewer_id_list:
        papers = reviewer_to_papers[reviewer_id]
        info = profile_info.get(
            reviewer_id,
            {
                "profile_resolved": "NO",
                "reviewer_name": "",
                "preferred_email": "",
            }
        )

        paper_numbers = [str(x["paper_number"]) for x in papers]
        paper_titles = [x["title"] for x in papers]
        agreements_ok = all(x["agreement_present"] for x in papers)

        unique_rows.append({
            "reciprocal_reviewer": reviewer_id,
            "reviewer_name": info.get("reviewer_name", ""),
            "preferred_email": info.get("preferred_email", ""),
            "profile_resolved": info.get("profile_resolved", "NO"),
            "active_submission_count": len(papers),
            "duplicate_reviewer": "YES" if len(papers) > 1 else "",
            "all_agreements_present": agreements_ok,
            "paper_numbers": "; ".join(paper_numbers),
            "paper_titles": " | ".join(paper_titles),
            "profile_error": info.get("profile_error", ""),
        })

    # Add duplicate flag back to per-submission mapping.
    duplicate_ids = {
        rid for rid, papers in reviewer_to_papers.items()
        if len(papers) > 1
    }
    for row in mapping_rows:
        rid = row["reciprocal_reviewer"]
        row["duplicate_reviewer"] = "YES" if rid and rid in duplicate_ids else ""
        if rid:
            info = profile_info.get(rid, {})
            row["reviewer_name"] = info.get("reviewer_name", "")
            row["preferred_email"] = info.get("preferred_email", "")
            row["profile_resolved"] = info.get("profile_resolved", "NO")
        else:
            row["reviewer_name"] = ""
            row["preferred_email"] = ""
            row["profile_resolved"] = ""

    # ---------------------------------------------------------------
    # 5. Write CSVs.
    # ---------------------------------------------------------------
    def write_csv(path: Path, rows: List[Dict[str, Any]], fallback_fields: List[str]):
        fields = list(rows[0].keys()) if rows else fallback_fields
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    active_csv = outdir / "active_submissions.csv"
    mapping_csv = outdir / "reciprocal_reviewer_by_submission.csv"
    unique_csv = outdir / "reciprocal_reviewers_unique.csv"

    write_csv(
        active_csv,
        active_rows,
        ["paper_number", "note_id", "title", "reciprocal_reviewer"]
    )
    write_csv(
        mapping_csv,
        mapping_rows,
        ["paper_number", "title", "reciprocal_reviewer"]
    )
    write_csv(
        unique_csv,
        unique_rows,
        ["reciprocal_reviewer", "reviewer_name", "preferred_email"]
    )

    # ---------------------------------------------------------------
    # 6. Summary / sanity checks.
    # ---------------------------------------------------------------
    missing_reviewers = [r for r in mapping_rows if r["reviewer_missing"]]
    missing_agreements = [r for r in mapping_rows if not r["agreement_present"]]
    unresolved = [r for r in unique_rows if r["profile_resolved"] != "YES"]
    duplicates = [r for r in unique_rows if r["duplicate_reviewer"] == "YES"]

    summary_lines = [
        "MATH-AI 2026 active submission / reciprocal reviewer fetch",
        "==========================================================",
        f"Venue: {args.venue}",
        f"Active venueid: {active_venue_id}",
        "",
        f"Active submissions: {len(submissions)}",
        f"Unique reciprocal reviewers: {len(unique_rows)}",
        f"Submissions missing reciprocal reviewer: {len(missing_reviewers)}",
        f"Submissions missing reciprocal-reviewing agreement: {len(missing_agreements)}",
        f"Reciprocal reviewers attached to >1 active submission: {len(duplicates)}",
        f"Reviewer profiles unresolved: {len(unresolved)}",
    ]

    if not args.skip_pdfs:
        summary_lines += [
            f"PDFs downloaded successfully: {pdf_ok_count}",
            f"PDF download/missing errors: {pdf_error_count}",
        ]

    if missing_reviewers:
        summary_lines += [
            "",
            "SUBMISSIONS MISSING RECIPROCAL REVIEWER:",
            *[
                f"  #{r['paper_number']}: {r['title']}"
                for r in missing_reviewers
            ],
        ]

    if missing_agreements:
        summary_lines += [
            "",
            "SUBMISSIONS MISSING RECIPROCAL REVIEWING AGREEMENT:",
            *[
                f"  #{r['paper_number']}: {r['title']}"
                for r in missing_agreements
            ],
        ]

    if duplicates:
        summary_lines += [
            "",
            "DUPLICATE RECIPROCAL REVIEWERS (reviewer used by >1 active submission):",
            *[
                f"  {r['reciprocal_reviewer']} ({r['reviewer_name']}): "
                f"{r['active_submission_count']} papers [{r['paper_numbers']}]"
                for r in duplicates
            ],
        ]

    if unresolved:
        summary_lines += [
            "",
            "UNRESOLVED REVIEWER PROFILES:",
            *[
                f"  {r['reciprocal_reviewer']}"
                for r in unresolved
            ],
        ]

    summary_path = outdir / "summary.txt"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print("\n" + "\n".join(summary_lines[:12]))
    print("\nCreated:")
    print(f"  {active_csv}")
    print(f"  {mapping_csv}")
    print(f"  {unique_csv}")
    print(f"  {summary_path}")
    if not args.skip_pdfs:
        print(f"  {pdfdir}/")

    print(
        "\nREAD-ONLY COMPLETE. "
        "No reviewers were invited and nothing was modified on OpenReview."
    )


if __name__ == "__main__":
    main()
