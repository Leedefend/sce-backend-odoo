#!/usr/bin/env python3
"""Build the SCBSLY direct-project user-acceptance gap matrix."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ALIGNMENT = ROOT / "artifacts/migration/scbsly_direct_project_new_system_alignment_probe_v1.json"
OUTPUT = ROOT / "artifacts/migration/scbsly_direct_project_alignment_gap_matrix_v1.json"
OUTPUT_MD = ROOT / "artifacts/migration/scbsly_direct_project_alignment_gap_matrix_v1.md"

NO_MATCHED_SERVER_CARRIER = {"油卡登记", "充值登记", "加油登记"}
KNOWN_ALIAS_OR_ROUTE_GAPS = {
    "机械合同（合同）",
    "报价单",
    "方单",
    "零星用工",
    "分包方单",
    "机械台班记录",
    "租入",
    "还租",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def classify(row: dict[str, Any]) -> str:
    label = str(row.get("label") or "")
    failures = [str(item) for item in row.get("failures", []) if item]
    if row.get("status") == "PASS":
        return "pass"
    if "new_menu_missing" in failures:
        if label in NO_MATCHED_SERVER_CARRIER:
            return "missing_server_carrier"
        if label in KNOWN_ALIAS_OR_ROUTE_GAPS:
            return "missing_user_visible_menu_route"
        return "missing_or_unmapped_menu"
    if any(item.startswith("count_mismatch:") for item in failures):
        return "data_scope_count_mismatch"
    if "no_visible_list_headers" in failures:
        return "field_surface_gap"
    return "other_alignment_gap"


def count_mismatch_text(row: dict[str, Any]) -> str:
    if row.get("old_count") is None or row.get("new_count") is None:
        return ""
    return f"{row.get('new_count')} != {row.get('old_count')}"


def main() -> int:
    if not ALIGNMENT.exists():
        raise SystemExit(f"missing alignment evidence: {ALIGNMENT.relative_to(ROOT)}")
    source = load_json(ALIGNMENT)
    rows = source.get("rows")
    if not isinstance(rows, list):
        raise SystemExit("alignment evidence rows[] missing")

    matrix_rows: list[dict[str, Any]] = []
    buckets: dict[str, list[str]] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        bucket = classify(raw)
        label = str(raw.get("label") or "")
        buckets.setdefault(bucket, []).append(label)
        matrix_rows.append(
            {
                "category": raw.get("category"),
                "label": label,
                "bucket": bucket,
                "old_count": raw.get("old_count"),
                "new_count": raw.get("new_count"),
                "count_mismatch": count_mismatch_text(raw),
                "matched_label": raw.get("matched_label"),
                "menu_id": raw.get("menu_id"),
                "action_id": raw.get("action_id"),
                "model": raw.get("model"),
                "field_count": raw.get("field_count"),
                "failures": raw.get("failures") if isinstance(raw.get("failures"), list) else [],
            }
        )

    summary = {
        "status": "BLOCKED_NEEDS_REPLAY_OR_CARRIER_REMEDIATION" if source.get("status") != "PASS" else "PASS",
        "source_alignment": str(ALIGNMENT.relative_to(ROOT)),
        "generated_from": source.get("generated_at"),
        "checked_count": len(matrix_rows),
        "pass_count": len(buckets.get("pass", [])),
        "data_scope_count_mismatch_count": len(buckets.get("data_scope_count_mismatch", [])),
        "missing_user_visible_menu_route_count": len(buckets.get("missing_user_visible_menu_route", [])),
        "missing_server_carrier_count": len(buckets.get("missing_server_carrier", [])),
        "missing_or_unmapped_menu_count": len(buckets.get("missing_or_unmapped_menu", [])),
        "field_surface_gap_count": len(buckets.get("field_surface_gap", [])),
        "blocking_conclusion": (
            "daily-dev new system is aligned to the SCBSLY_V2 direct-project user acceptance surface."
            if source.get("status") == "PASS"
            else (
                "daily-dev new system is not aligned to the SCBSLY_V2 direct-project user acceptance surface; "
                "count mismatches require migration asset replay or acceptance carrier remediation, not contract-layer trimming."
            )
        ),
        "buckets": buckets,
        "rows": matrix_rows,
    }
    write_json(OUTPUT, summary)

    lines = [
        "# SCBSLY Direct Project Alignment Gap Matrix v1",
        "",
        f"Status: `{summary['status']}`",
        f"Source: `{summary['source_alignment']}`",
        "",
        "| Bucket | Count | Labels |",
        "| --- | ---: | --- |",
    ]
    bucket_order = [
        "pass",
        "data_scope_count_mismatch",
        "missing_user_visible_menu_route",
        "missing_server_carrier",
        "missing_or_unmapped_menu",
        "field_surface_gap",
        "other_alignment_gap",
    ]
    for bucket in bucket_order:
        labels = buckets.get(bucket, [])
        lines.append(f"| {bucket} | {len(labels)} | {'、'.join(labels)} |")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| 分类 | 菜单 | Bucket | 匹配菜单 | menu | action | model | 旧数 | 新数 | 字段 |",
            "| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for row in matrix_rows:
        lines.append(
            "| {category} | {label} | {bucket} | {matched_label} | {menu_id} | {action_id} | {model} | {old_count} | {new_count} | {field_count} |".format(
                category=row.get("category") or "",
                label=row.get("label") or "",
                bucket=row.get("bucket") or "",
                matched_label=row.get("matched_label") or "",
                menu_id=row.get("menu_id") or "",
                action_id=row.get("action_id") or "",
                model=row.get("model") or "",
                old_count="" if row.get("old_count") is None else row.get("old_count"),
                new_count="" if row.get("new_count") is None else row.get("new_count"),
                field_count=row.get("field_count") or 0,
            )
        )
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"SCBSLY_DIRECT_PROJECT_ALIGNMENT_GAP_MATRIX={summary['status']} output={OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
