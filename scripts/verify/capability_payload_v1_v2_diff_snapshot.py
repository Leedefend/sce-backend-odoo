#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _load_json_list_from_text(text: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    loaded = json.loads(text)
    if not isinstance(loaded, list):
        return []
    return [item for item in loaded if isinstance(item, dict)]


def _load_payload(sample_json: str | None, sample_file: str | None) -> List[Dict[str, Any]]:
    if sample_json:
        return _load_json_list_from_text(sample_json)
    if sample_file:
        text = Path(sample_file).read_text(encoding="utf-8")
        return _load_json_list_from_text(text)
    return []


def _by_key(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("key") or "").strip()
        if key:
            out[key] = row
    return out


def _row_changed(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    return json.dumps(a, sort_keys=True, ensure_ascii=False) != json.dumps(b, sort_keys=True, ensure_ascii=False)


def build_diff(v1_rows: List[Dict[str, Any]], v2_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    v1 = _by_key(v1_rows)
    v2 = _by_key(v2_rows)
    v1_keys = set(v1.keys())
    v2_keys = set(v2.keys())

    added_keys = sorted(list(v2_keys - v1_keys))
    removed_keys = sorted(list(v1_keys - v2_keys))
    common_keys = sorted(list(v1_keys & v2_keys))
    changed_keys = [key for key in common_keys if _row_changed(v1[key], v2[key])]

    return {
        "summary": {
            "v1_count": len(v1_rows),
            "v2_count": len(v2_rows),
            "added_count": len(added_keys),
            "removed_count": len(removed_keys),
            "changed_count": len(changed_keys),
        },
        "added_keys": added_keys,
        "removed_keys": removed_keys,
        "changed_keys": changed_keys,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare capability payload snapshots between v1 and v2 paths.")
    parser.add_argument("--sample-v1", default="", help="inline JSON list for v1 payload")
    parser.add_argument("--sample-v2", default="", help="inline JSON list for v2 payload")
    parser.add_argument("--sample-v1-file", default="", help="file containing JSON list for v1 payload")
    parser.add_argument("--sample-v2-file", default="", help="file containing JSON list for v2 payload")
    parser.add_argument("--out", required=True, help="output file path")
    args = parser.parse_args()

    v1_rows = _load_payload(args.sample_v1, args.sample_v1_file)
    v2_rows = _load_payload(args.sample_v2, args.sample_v2_file)
    result = build_diff(v1_rows, v2_rows)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
