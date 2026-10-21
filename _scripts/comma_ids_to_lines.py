#!/usr/bin/env python3
"""Convert comma-separated OpenReview IDs into one ID per line."""

from __future__ import annotations

import argparse
from pathlib import Path


def convert(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Turn comma-separated OpenReview IDs into one ID per line."
    )
    parser.add_argument("input", type=Path, help="Path to a comma-separated .txt file")
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=None,
        help="Output path (default: <input_stem>_ids.txt next to the input)",
    )
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")

    output_path: Path = (
        args.output
        if args.output is not None
        else input_path.with_name(f"{input_path.stem}_ids.txt")
    )

    ids = convert(input_path.read_text(encoding="utf-8"))
    output_path.write_text("\n".join(ids) + ("\n" if ids else ""), encoding="utf-8")
    print(f"Wrote {len(ids)} IDs to {output_path}")


if __name__ == "__main__":
    main()
