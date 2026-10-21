#!/usr/bin/env python3
"""Remove already-invited OpenReview IDs from an invite list."""

from __future__ import annotations

import argparse
from pathlib import Path


def read_ids(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_ids(path: Path, ids: list[str]) -> None:
    path.write_text("\n".join(ids) + ("\n" if ids else ""), encoding="utf-8")


def dedupe(candidates: list[str], invited: set[str]) -> tuple[list[str], list[str]]:
    """Return (new_ids, already_invited_ids), preserving candidate order."""
    new_ids: list[str] = []
    duplicates: list[str] = []
    seen_new: set[str] = set()
    seen_dupes: set[str] = set()

    for openreview_id in candidates:
        if openreview_id in invited:
            if openreview_id not in seen_dupes:
                duplicates.append(openreview_id)
                seen_dupes.add(openreview_id)
        elif openreview_id not in seen_new:
            new_ids.append(openreview_id)
            seen_new.add(openreview_id)

    return new_ids, duplicates


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Deduplicate an OpenReview invite list against already-invited IDs. "
            "Writes new IDs and removed duplicates to separate files."
        )
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to newline-separated OpenReview IDs to invite",
    )
    parser.add_argument(
        "--invited",
        type=Path,
        default=None,
        help="Already-invited IDs (default: invited_ids.txt next to the input)",
    )
    parser.add_argument(
        "--new",
        type=Path,
        default=None,
        help="Output path for new IDs (default: <input_stem>_new.txt)",
    )
    parser.add_argument(
        "--duplicates",
        type=Path,
        default=None,
        help="Output path for removed duplicates (default: <input_stem>_duplicates.txt)",
    )
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")

    invited_path: Path = (
        args.invited
        if args.invited is not None
        else input_path.with_name("invited_ids.txt")
    )
    if not invited_path.is_file():
        raise SystemExit(f"Invited file not found: {invited_path}")

    new_path: Path = (
        args.new
        if args.new is not None
        else input_path.with_name(f"{input_path.stem}_new.txt")
    )
    duplicates_path: Path = (
        args.duplicates
        if args.duplicates is not None
        else input_path.with_name(f"{input_path.stem}_duplicates.txt")
    )

    candidates = read_ids(input_path)
    invited = set(read_ids(invited_path))
    new_ids, duplicates = dedupe(candidates, invited)

    write_ids(new_path, new_ids)
    write_ids(duplicates_path, duplicates)

    print(f"Candidates: {len(candidates)}")
    print(f"Already invited: {len(invited)}")
    print(f"Wrote {len(new_ids)} new IDs to {new_path}")
    print(f"Wrote {len(duplicates)} duplicates to {duplicates_path}")


if __name__ == "__main__":
    main()
