#!/usr/bin/env python3
"""
MATH-AI 2026 submission compliance triage.

What it does:
  1. Logs into OpenReview API v2.
  2. Retrieves submissions for NeurIPS.cc/2026/Workshop/MATH-AI.
  3. Keeps active/under-review submissions.
  4. Downloads PDFs.
  5. Flags likely page-limit and anonymity issues.
  6. Inspects submission fields for reciprocal-reviewer information.
  7. Writes:
       - mathai_triage.csv
       - mathai_submission_fields.csv
       - pdfs/submission_<N>.pdf

IMPORTANT:
  This is a TRIAGE tool, not an auto-desk-reject tool.
  Every flagged paper should be manually checked before a decision.
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import openreview
except ImportError:
    sys.exit("Missing package: openreview-py. Install with: pip install openreview-py")

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Missing package: pymupdf. Install with: pip install pymupdf")


VENUE_ID = "NeurIPS.cc/2026/Workshop/MATH-AI"
# Outputs contain submission PDFs; keep them in the git-ignored openreview/ folder.
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "openreview" / "mathai_triage_output"

EMAIL_RE = re.compile(
    r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b",
    flags=re.IGNORECASE,
)
URL_RE = re.compile(r"https?://[^\s<>()\]\[]+", flags=re.IGNORECASE)

ACK_RE = re.compile(
    r"\b(acknowledg(?:e)?ments?|we thank|thanks to|supported by|funded by|grant(?:s)?)\b",
    flags=re.IGNORECASE,
)

AFFILIATION_RE = re.compile(
    r"\b("
    r"university|université|universitaet|universität|college|institute|institution|"
    r"laboratory|laboratories|lab\b|department|school of|faculty of|"
    r"research center|research centre|corporation|corp\.?|inc\.?|llc|"
    r"google deepmind|deepmind|openai|anthropic|microsoft research|meta ai|"
    r"carnegie mellon|mit\b|stanford|berkeley|princeton|harvard"
    r")\b",
    flags=re.IGNORECASE,
)

REF_HEADING_RE = re.compile(r"^\s*(references|bibliography)\s*$", flags=re.IGNORECASE)
SUPP_HEADING_RE = re.compile(
    r"^\s*(appendix|supplementary material|supplemental material|supplement)\b",
    flags=re.IGNORECASE,
)


def value_of(v: Any) -> Any:
    """OpenReview API v2 content values are usually {'value': ...}."""
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    return v


def flatten_content(note) -> Dict[str, Any]:
    return {k: value_of(v) for k, v in (note.content or {}).items()}


def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def author_name_variants(authors: Iterable[str]) -> List[str]:
    """
    Generate conservative variants for exact-ish author-name matching.
    We intentionally avoid surname-only matching because references create
    too many false positives.
    """
    variants = set()
    for author in authors or []:
        author = normalize_space(str(author))
        if not author:
            continue
        variants.add(author.lower())

        # "First Middle Last" -> "First Last"
        bits = author.split()
        if len(bits) >= 2:
            variants.add((bits[0] + " " + bits[-1]).lower())

        # "Last, First Middle" -> "First Last"
        if "," in author:
            left, right = [x.strip() for x in author.split(",", 1)]
            rb = right.split()
            if rb:
                variants.add((rb[0] + " " + left).lower())

    # Ignore very short strings.
    return sorted(v for v in variants if len(v) >= 6)


def find_heading_page(doc, pattern: re.Pattern) -> Tuple[Optional[int], Optional[float]]:
    """
    Return (1-based page number, vertical fraction on page) of first heading.
    Uses text blocks so we can distinguish a heading at the top of a page
    from one that starts halfway down the page.
    """
    for i, page in enumerate(doc):
        height = float(page.rect.height) or 1.0
        blocks = page.get_text("blocks")
        for block in blocks:
            x0, y0, x1, y1, text, *_ = block
            # Split block because headings can be separate lines inside blocks.
            for line in text.splitlines():
                line = normalize_space(line)
                if pattern.match(line):
                    return i + 1, float(y0) / height
    return None, None


def estimate_content_pages(doc) -> Tuple[Optional[int], str]:
    """
    Heuristic for MATH-AI's "4 pages of content; unlimited references/supplement."

    If References begins near the top (first 20%) of page k, estimate k-1
    content pages. If it begins lower on page k, estimate k content pages.

    Supplementary heading is used only if references heading is absent.
    """
    total = len(doc)
    ref_page, ref_y = find_heading_page(doc, REF_HEADING_RE)
    if ref_page:
        est = ref_page - 1 if (ref_y is not None and ref_y <= 0.20) else ref_page
        return est, f"References heading on p.{ref_page} (y={ref_y:.2f})"

    supp_page, supp_y = find_heading_page(doc, SUPP_HEADING_RE)
    if supp_page:
        est = supp_page - 1 if (supp_y is not None and supp_y <= 0.20) else supp_page
        return est, f"Supplement heading on p.{supp_page} (y={supp_y:.2f}); no References heading detected"

    return None, f"No References/Supplement heading detected; total PDF pages={total}"


def analyze_pdf(pdf_path: Path, authors: List[str]) -> Dict[str, Any]:
    result = {
        "pdf_ok": False,
        "total_pdf_pages": "",
        "estimated_content_pages": "",
        "page_limit_flag": "",
        "page_limit_evidence": "",
        "author_name_hits": "",
        "email_hits": "",
        "acknowledgment_flag": "",
        "affiliation_flag": "",
        "suspicious_urls": "",
        "anonymity_flag": "",
        "pdf_error": "",
    }

    try:
        doc = fitz.open(pdf_path)
        result["pdf_ok"] = True
        result["total_pdf_pages"] = len(doc)

        est_pages, page_evidence = estimate_content_pages(doc)
        result["estimated_content_pages"] = "" if est_pages is None else est_pages
        result["page_limit_evidence"] = page_evidence

        if est_pages is not None:
            if est_pages > 4:
                result["page_limit_flag"] = "LIKELY_VIOLATION"
            elif est_pages == 4:
                result["page_limit_flag"] = "PASS_HEURISTIC"
            else:
                result["page_limit_flag"] = "PASS_HEURISTIC"
        else:
            # Raw total pages >4 is NOT itself a violation because refs/supp are unlimited.
            result["page_limit_flag"] = "MANUAL_CHECK" if len(doc) > 4 else "PASS_HEURISTIC"

        # Anonymity checks focus on the content pages, capped at first 4 pages.
        first_pages = []
        for p in range(min(4, len(doc))):
            first_pages.append(doc[p].get_text("text"))
        content_text = "\n".join(first_pages)
        content_lower = content_text.lower()

        # First page gets extra attention for explicit author headers.
        first_page_text = doc[0].get_text("text") if len(doc) else ""
        first_page_lower = first_page_text.lower()

        name_hits = []
        for variant in author_name_variants(authors):
            # Exact phrase in first 4 pages; first page is especially suspicious.
            if variant in content_lower:
                where = "p1" if variant in first_page_lower else "p1-4"
                name_hits.append(f"{variant} ({where})")
        result["author_name_hits"] = "; ".join(sorted(set(name_hits)))

        emails = sorted(set(EMAIL_RE.findall(content_text)))
        result["email_hits"] = "; ".join(emails)

        result["acknowledgment_flag"] = "YES" if ACK_RE.search(content_text) else ""
        result["affiliation_flag"] = "YES" if AFFILIATION_RE.search(first_page_text) else ""

        urls = sorted(set(URL_RE.findall(content_text)))
        suspicious_urls = [
            u for u in urls
            if any(token in u.lower() for token in [
                "github.com/", "gitlab.com/", "personal", "people.", "users/",
                "~", "linkedin.com/", "scholar.google"
            ])
        ]
        result["suspicious_urls"] = "; ".join(suspicious_urls[:20])

        anonymity_signals = sum(bool(result[k]) for k in [
            "author_name_hits", "email_hits", "acknowledgment_flag",
            "affiliation_flag", "suspicious_urls"
        ])
        if result["author_name_hits"] or result["email_hits"]:
            result["anonymity_flag"] = "LIKELY_ISSUE"
        elif anonymity_signals:
            result["anonymity_flag"] = "MANUAL_CHECK"
        else:
            result["anonymity_flag"] = "PASS_HEURISTIC"

        doc.close()
    except Exception as e:
        result["pdf_error"] = repr(e)
        result["page_limit_flag"] = "MANUAL_CHECK"
        result["anonymity_flag"] = "MANUAL_CHECK"

    return result


def candidate_reviewer_fields(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    We don't hard-code your reciprocal-reviewer field name because organizers
    often customize it. Capture anything whose key suggests reviewer/reviewing.
    """
    out = {}
    for k, v in content.items():
        lk = k.lower()
        if "review" in lk or "recipro" in lk:
            out[k] = v
    return out


def stringify(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple, set)):
        return "; ".join(map(str, v))
    if isinstance(v, dict):
        return repr(v)
    return str(v)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--venue", default=VENUE_ID)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--username", default=os.environ.get("OPENREVIEW_USERNAME"))
    parser.add_argument("--password", default=os.environ.get("OPENREVIEW_PASSWORD"))
    args = parser.parse_args()

    if not args.username or not args.password:
        sys.exit(
            "Set OPENREVIEW_USERNAME and OPENREVIEW_PASSWORD environment variables, "
            "or pass --username and --password."
        )

    outdir = Path(args.out)
    pdfdir = outdir / "pdfs"
    outdir.mkdir(parents=True, exist_ok=True)
    pdfdir.mkdir(parents=True, exist_ok=True)

    client = openreview.api.OpenReviewClient(
        baseurl="https://api2.openreview.net",
        username=args.username,
        password=args.password,
    )

    venue = client.get_group(args.venue)
    venue_content = {k: value_of(v) for k, v in venue.content.items()}

    submission_name = venue_content.get("submission_name", "Submission")
    submission_invitation = f"{args.venue}/-/{submission_name}"
    active_venue_id = venue_content.get("submission_venue_id")

    print(f"Venue: {args.venue}")
    print(f"Submission invitation: {submission_invitation}")
    print(f"Active submission venue id: {active_venue_id}")

    all_submissions = client.get_all_notes(invitation=submission_invitation)
    if active_venue_id:
        submissions = [
            n for n in all_submissions
            if value_of((n.content or {}).get("venueid")) == active_venue_id
        ]
    else:
        # Fallback: use all notes if venue status metadata is unavailable.
        submissions = all_submissions
        print("WARNING: submission_venue_id missing; unable to filter statuses reliably.")

    submissions.sort(key=lambda n: n.number or 0)

    print(f"All submission notes: {len(all_submissions)}")
    print(f"Active submissions selected for triage: {len(submissions)}")

    # Capture every field/key present, useful for identifying your reciprocal reviewer field.
    all_keys = sorted({
        key
        for note in submissions
        for key in (note.content or {}).keys()
    })

    field_inventory_path = outdir / "mathai_submission_fields.csv"
    with field_inventory_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["paper_number", "note_id"] + all_keys)
        for note in submissions:
            content = flatten_content(note)
            writer.writerow(
                [note.number, note.id] + [stringify(content.get(k)) for k in all_keys]
            )

    rows = []
    for idx, note in enumerate(submissions, start=1):
        content = flatten_content(note)
        title = stringify(content.get("title"))
        authors = content.get("authors") or []
        if not isinstance(authors, list):
            authors = [authors]

        print(f"[{idx}/{len(submissions)}] Submission {note.number}: {title[:80]}")

        pdf_path = pdfdir / f"submission_{note.number}.pdf"
        pdf_present = bool(content.get("pdf"))
        download_error = ""

        if pdf_present:
            try:
                pdf_bytes = client.get_attachment(field_name="pdf", id=note.id)
                pdf_path.write_bytes(pdf_bytes)
            except Exception as e:
                download_error = repr(e)
        else:
            download_error = "No PDF field/value."

        pdf_analysis = {}
        if pdf_present and not download_error and pdf_path.exists():
            pdf_analysis = analyze_pdf(pdf_path, authors)
        else:
            pdf_analysis = {
                "pdf_ok": False,
                "total_pdf_pages": "",
                "estimated_content_pages": "",
                "page_limit_flag": "MANUAL_CHECK",
                "page_limit_evidence": "",
                "author_name_hits": "",
                "email_hits": "",
                "acknowledgment_flag": "",
                "affiliation_flag": "",
                "suspicious_urls": "",
                "anonymity_flag": "MANUAL_CHECK",
                "pdf_error": download_error,
            }

        reviewer_fields = candidate_reviewer_fields(content)

        # Overall triage recommendation.
        reasons = []
        if not pdf_present or download_error or not pdf_analysis["pdf_ok"]:
            reasons.append("PDF_PROBLEM")
        if pdf_analysis["page_limit_flag"] == "LIKELY_VIOLATION":
            reasons.append("PAGE_LIMIT")
        elif pdf_analysis["page_limit_flag"] == "MANUAL_CHECK":
            reasons.append("PAGE_LIMIT_CHECK")
        if pdf_analysis["anonymity_flag"] == "LIKELY_ISSUE":
            reasons.append("ANONYMITY")
        elif pdf_analysis["anonymity_flag"] == "MANUAL_CHECK":
            reasons.append("ANONYMITY_CHECK")
        if not reviewer_fields:
            reasons.append("RECIPROCAL_REVIEWER_FIELD_NOT_DETECTED")

        if any(r in reasons for r in ["PDF_PROBLEM", "PAGE_LIMIT", "ANONYMITY"]):
            triage = "MANUAL_CHECK_HIGH_PRIORITY"
        elif reasons:
            triage = "MANUAL_CHECK"
        else:
            triage = "PASS_HEURISTIC"

        rows.append({
            "paper_number": note.number,
            "note_id": note.id,
            "title": title,
            "authors": "; ".join(map(str, authors)),
            "venueid": stringify(content.get("venueid")),
            "pdf_present": pdf_present,
            **pdf_analysis,
            "reviewer_related_fields": " | ".join(
                f"{k}={stringify(v)}" for k, v in reviewer_fields.items()
            ),
            "triage": triage,
            "triage_reasons": "; ".join(reasons),
        })

    triage_path = outdir / "mathai_triage.csv"
    fieldnames = list(rows[0].keys()) if rows else [
        "paper_number", "note_id", "title", "triage"
    ]
    with triage_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    high = sum(r.get("triage") == "MANUAL_CHECK_HIGH_PRIORITY" for r in rows)
    manual = sum(r.get("triage") == "MANUAL_CHECK" for r in rows)
    passed = sum(r.get("triage") == "PASS_HEURISTIC" for r in rows)

    print("\nDone.")
    print(f"  PASS_HEURISTIC:             {passed}")
    print(f"  MANUAL_CHECK:               {manual}")
    print(f"  MANUAL_CHECK_HIGH_PRIORITY: {high}")
    print(f"\nTriage CSV:   {triage_path}")
    print(f"Field CSV:    {field_inventory_path}")
    print(f"Downloaded PDFs: {pdfdir}")
    print("\nDo NOT desk-reject automatically from this report; inspect flagged PDFs first.")


if __name__ == "__main__":
    main()
