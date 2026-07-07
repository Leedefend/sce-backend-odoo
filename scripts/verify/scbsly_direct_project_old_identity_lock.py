#!/usr/bin/env python3
"""Lock row identity sets for SCBSLY direct-project historical-source dumps."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "artifacts/migration/scbsly_direct_project_old_row_dump_summary_v1.json"
OUTPUT = ROOT / "artifacts/migration/scbsly_direct_project_old_identity_lock_v1.json"
OUTPUT_MD = ROOT / "artifacts/migration/scbsly_direct_project_old_identity_lock_v1.md"

PREFERRED_FIELDS = ("DJBH", "Id", "ID", "pid", "PID", "Pid", "BH")
FALLBACK_FIELDS = ("RowIndex",)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clean(value: object) -> str:
    return str(value or "").strip()


def hash_values(values: list[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(values):
        digest.update(value.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def field_stats(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [clean(row.get(field)) for row in rows]
    present = [value for value in values if value]
    return {
        "field": field,
        "total": len(rows),
        "missing_count": len(rows) - len(present),
        "unique_count": len(set(present)),
        "set_sha256": hash_values(present),
    }


def choose_identity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "identity_policy": "empty_list",
            "identity_field": "",
            "total": 0,
            "missing_count": 0,
            "unique_count": 0,
            "set_sha256": hash_values([]),
            "candidate_stats": [],
        }
    candidate_stats = [
        field_stats(rows, field)
        for field in (*PREFERRED_FIELDS, *FALLBACK_FIELDS)
        if any(field in row for row in rows)
    ]
    for stats in candidate_stats:
        if stats["field"] in PREFERRED_FIELDS and stats["missing_count"] == 0 and stats["unique_count"] == len(rows):
            return {**stats, "identity_policy": "single_preferred_field", "candidate_stats": candidate_stats}
    for stats in candidate_stats:
        if stats["field"] in FALLBACK_FIELDS and stats["missing_count"] == 0 and stats["unique_count"] == len(rows):
            return {**stats, "identity_policy": "single_row_index_fallback", "candidate_stats": candidate_stats}
    row_hashes = [hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest() for row in rows]
    return {
        "identity_policy": "row_hash_fallback",
        "identity_field": "__row_hash",
        "total": len(rows),
        "missing_count": 0,
        "unique_count": len(set(row_hashes)),
        "set_sha256": hash_values(row_hashes),
        "candidate_stats": candidate_stats,
    }


def markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBSLY Direct Project Old Identity Lock v1",
        "",
        f"Status: `{payload['status']}`",
        f"Generated At: `{payload['generated_at']}`",
        f"List Count: `{payload['list_count']}`",
        f"Row Count: `{payload['total_rows']}`",
        "",
        "| 分类 | 菜单 | 行数 | Identity | Policy | Missing | Unique | Status |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {category} | {label} | {total} | `{identity_field}` | {identity_policy} | {missing_count} | {unique_count} | {status} |".format(
                **row
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    if not SUMMARY.exists():
        raise SystemExit(f"missing old row dump summary: {SUMMARY.relative_to(ROOT)}")
    summary = load_json(SUMMARY)
    rows_out: list[dict[str, Any]] = []
    for item in summary.get("rows", []):
        if not isinstance(item, dict):
            continue
        dump_path = Path(str(item.get("path") or ""))
        if not dump_path.exists():
            rows_out.append(
                {
                    "category": item.get("category"),
                    "label": item.get("label"),
                    "status": "FAIL",
                    "failure": "missing_dump_file",
                    "identity_field": "",
                    "identity_policy": "",
                    "total": 0,
                    "missing_count": 0,
                    "unique_count": 0,
                    "set_sha256": "",
                }
            )
            continue
        dump = load_json(dump_path)
        rows = [row for row in dump.get("rows", []) if isinstance(row, dict)]
        identity = choose_identity(rows)
        status = "PASS" if identity["unique_count"] == len(rows) and identity["missing_count"] == 0 else "FAIL"
        rows_out.append(
            {
                "category": item.get("category"),
                "label": item.get("label"),
                "config_id": item.get("config_id"),
                "dump_path": str(dump_path),
                "status": status,
                "identity_field": identity.get("field") or identity.get("identity_field"),
                "identity_policy": identity["identity_policy"],
                "total": len(rows),
                "missing_count": identity["missing_count"],
                "unique_count": identity["unique_count"],
                "set_sha256": identity["set_sha256"],
                "candidate_stats": identity["candidate_stats"],
            }
        )
    failures = [row for row in rows_out if row["status"] != "PASS"]
    payload = {
        "status": "PASS" if not failures else "FAIL",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_summary": str(SUMMARY.relative_to(ROOT)),
        "list_count": len(rows_out),
        "total_rows": sum(int(row["total"]) for row in rows_out),
        "preferred_identity_count": len([row for row in rows_out if row["identity_policy"] == "single_preferred_field"]),
        "row_index_fallback_count": len([row for row in rows_out if row["identity_policy"] == "single_row_index_fallback"]),
        "row_hash_fallback_count": len([row for row in rows_out if row["identity_policy"] == "row_hash_fallback"]),
        "empty_list_count": len([row for row in rows_out if row["identity_policy"] == "empty_list"]),
        "failure_count": len(failures),
        "failures": failures,
        "rows": rows_out,
    }
    write_json(OUTPUT, payload)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(markdown(payload), encoding="utf-8")
    print(f"SCBSLY_DIRECT_PROJECT_OLD_IDENTITY_LOCK={payload['status']} output={OUTPUT}")
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
