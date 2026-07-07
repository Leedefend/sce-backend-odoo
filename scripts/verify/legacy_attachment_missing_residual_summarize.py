#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize strict legacy attachment missing-file TSV output.

This is a host-side utility. It does not connect to Odoo or mutate data; it
turns the full missing-row manifest into a stable residual summary that
separates reference rows from unique missing paths.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_INPUT = "/data/odoo/legacy_attachments/checks/prod_legacy_attachment_missing_latest.tsv"
DEFAULT_OUTPUT = "/data/odoo/legacy_attachments/checks/prod_legacy_attachment_missing_unique_summary.json"


def _int(value: object) -> int:
    try:
        return int(str(value or "0").strip() or "0")
    except ValueError:
        return 0


def _row_key(row: dict[str, str]) -> str:
    return (
        (row.get("relative_path") or "").strip()
        or (row.get("basename") or "").strip()
        or (row.get("legacy_file_id") or "").strip()
        or (row.get("id") or "").strip()
    )


def summarize(rows: list[dict[str, str]], input_path: Path) -> dict[str, object]:
    by_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    rows_by_source = Counter()
    rows_by_size = Counter()
    missing_bytes_by_source = Counter()

    for row in rows:
        source = (row.get("source_table") or "<blank>").strip() or "<blank>"
        size = _int(row.get("file_size"))
        rows_by_source[source] += 1
        rows_by_size["zero"] += int(size <= 0)
        rows_by_size["nonzero"] += int(size > 0)
        missing_bytes_by_source[source] += size
        by_path[_row_key(row)].append(row)

    unique_paths = []
    unique_by_source_combo = Counter()
    for relative_path, items in by_path.items():
        sizes = [_int(item.get("file_size")) for item in items]
        sources = sorted(set((item.get("source_table") or "<blank>").strip() or "<blank>" for item in items))
        entry = {
            "relative_path": relative_path,
            "refs": len(items),
            "sources": sources,
            "file_size": max(sizes or [0]),
            "file_names": sorted(
                set((item.get("file_name") or "").strip() for item in items if (item.get("file_name") or "").strip())
            )[:10],
            "ids": [(item.get("id") or "").strip() for item in items if (item.get("id") or "").strip()],
        }
        unique_paths.append(entry)
        unique_by_source_combo["+".join(sources)] += 1

    nonzero_unique = [item for item in unique_paths if int(item["file_size"]) > 0]
    zero_unique = [item for item in unique_paths if int(item["file_size"]) <= 0]
    return {
        "scope": "legacy_attachment_missing_residual_summary",
        "input": str(input_path),
        "reference_rows": len(rows),
        "unique_missing_paths": len(unique_paths),
        "duplicate_reference_rows": len(rows) - len(unique_paths),
        "rows_by_source": dict(rows_by_source),
        "rows_by_size": dict(rows_by_size),
        "missing_bytes_by_source": dict(missing_bytes_by_source),
        "unique_by_source_combo": dict(unique_by_source_combo),
        "nonzero_unique_paths": len(nonzero_unique),
        "zero_size_unique_paths": len(zero_unique),
        "nonzero_unique_bytes": sum(int(item["file_size"]) for item in nonzero_unique),
        "top_duplicate_paths": sorted(unique_paths, key=lambda item: int(item["refs"]), reverse=True)[:20],
        "nonzero_unique_examples": nonzero_unique[:50],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    with input_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    summary = summarize(rows, input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
