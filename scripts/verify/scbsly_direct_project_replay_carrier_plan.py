#!/usr/bin/env python3
"""Build the replay/carrier remediation plan for SCBSLY direct-project acceptance."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ALIGNMENT = ROOT / "artifacts/migration/scbsly_direct_project_new_system_alignment_probe_v1.json"
IDENTITY_LOCK = ROOT / "artifacts/migration/scbsly_direct_project_old_identity_lock_v1.json"
OUTPUT = ROOT / "artifacts/migration/scbsly_direct_project_replay_carrier_plan_v1.json"
OUTPUT_MD = ROOT / "artifacts/migration/scbsly_direct_project_replay_carrier_plan_v1.md"

MENU_ALIAS_TARGETS = {
    "机械合同（合同）": ("sc.equipment.request", "menu_sc_equipment_contract_acceptance"),
    "报价单": ("sc.material.rfq", "menu_sc_material_quote_acceptance"),
    "方单": ("sc.labor.usage", "menu_sc_labor_usage_acceptance"),
    "零星用工": ("sc.labor.usage", "menu_sc_labor_casual_acceptance"),
    "分包方单": ("sc.subcontract.request", "menu_sc_subcontract_request_acceptance"),
    "机械台班记录": ("sc.equipment.usage", "menu_sc_equipment_shift_acceptance"),
    "租入": ("sc.material.rental.order", "menu_sc_material_rental_in_acceptance"),
    "还租": ("sc.material.rental.order", "menu_sc_material_rental_return_acceptance"),
}

CARRIER_ADDED_TARGETS = {
    "油卡登记": "sc.legacy.fuel.card.fact",
    "充值登记": "sc.legacy.fuel.card.recharge.fact",
    "加油登记": "sc.legacy.fuel.card.refuel.fact",
}

REPORT_LABELS = {"库存统计表（新）", "成本统计表（数据）"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def identity_by_label() -> dict[str, dict[str, Any]]:
    payload = load_json(IDENTITY_LOCK)
    return {str(row.get("label") or ""): row for row in payload.get("rows", []) if isinstance(row, dict)}


def plan_bucket(row: dict[str, Any], identity: dict[str, Any] | None) -> str:
    label = str(row.get("label") or "")
    if label in REPORT_LABELS:
        return "report_route_no_row_replay"
    failures = [str(item) for item in row.get("failures", []) if item]
    if label in CARRIER_ADDED_TARGETS:
        return "legacy_fuel_carrier_added_requires_replay"
    if label in MENU_ALIAS_TARGETS:
        if identity and int(identity.get("total") or 0) == 0:
            return "menu_alias_added_empty_old_list"
        return "menu_alias_added_requires_replay"
    if any(item.startswith("count_mismatch:") for item in failures):
        return "existing_carrier_requires_identity_replay_or_scoped_surface"
    if row.get("status") == "PASS":
        return "pass_current_report_or_surface"
    return "unclassified_requires_manual_review"


def target_model(row: dict[str, Any]) -> str:
    label = str(row.get("label") or "")
    if label in MENU_ALIAS_TARGETS:
        return MENU_ALIAS_TARGETS[label][0]
    if label in CARRIER_ADDED_TARGETS:
        return CARRIER_ADDED_TARGETS[label]
    return str(row.get("model") or "")


def menu_patch(row: dict[str, Any]) -> str:
    label = str(row.get("label") or "")
    return MENU_ALIAS_TARGETS.get(label, ("", ""))[1]


def priority(bucket: str, row: dict[str, Any], identity: dict[str, Any] | None) -> int:
    count = int((identity or {}).get("total") or row.get("old_count") or 0)
    if bucket == "legacy_fuel_carrier_added_requires_replay":
        return 20
    if bucket == "existing_carrier_requires_identity_replay_or_scoped_surface" and count >= 5000:
        return 30
    if bucket == "menu_alias_added_requires_replay" and count >= 5000:
        return 35
    if bucket in {"existing_carrier_requires_identity_replay_or_scoped_surface", "menu_alias_added_requires_replay"}:
        return 40
    if bucket == "menu_alias_added_empty_old_list":
        return 70
    return 90


def markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBSLY Direct Project Replay Carrier Plan v1",
        "",
        f"Status: `{payload['status']}`",
        f"Generated At: `{payload['generated_at']}`",
        "",
        "| Bucket | Count | Old Rows |",
        "| --- | ---: | ---: |",
    ]
    for bucket, stats in payload["bucket_summary"].items():
        lines.append(f"| {bucket} | {stats['count']} | {stats['old_rows']} |")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| P | 分类 | 菜单 | Bucket | Target Model | Old | New | Identity | Menu Patch |",
            "| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for row in payload["rows"]:
        display = dict(row)
        display["new_count"] = "" if row.get("new_count") is None else row.get("new_count")
        lines.append(
            "| {priority} | {category} | {label} | {bucket} | `{target_model}` | {old_count} | {new_count} | `{identity_field}` | {menu_patch} |".format(
                **display,
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    alignment = load_json(ALIGNMENT)
    identities = identity_by_label()
    rows_out: list[dict[str, Any]] = []
    for row in alignment.get("rows", []):
        if not isinstance(row, dict):
            continue
        label = str(row.get("label") or "")
        identity = identities.get(label)
        bucket = plan_bucket(row, identity)
        old_count = int((identity or {}).get("total") or row.get("old_count") or 0)
        rows_out.append(
            {
                "category": row.get("category"),
                "label": label,
                "bucket": bucket,
                "priority": priority(bucket, row, identity),
                "target_model": target_model(row),
                "current_model": row.get("model") or "",
                "menu_patch": menu_patch(row),
                "old_count": old_count,
                "new_count": row.get("new_count"),
                "identity_field": (identity or {}).get("identity_field") or "",
                "identity_policy": (identity or {}).get("identity_policy") or "",
                "identity_set_sha256": (identity or {}).get("set_sha256") or "",
                "required_action": {
                    "report_route_no_row_replay": "keep report route evidence; no list replay",
                    "pass_current_report_or_surface": "keep current evidence; revalidate after server upgrade",
                    "menu_alias_added_empty_old_list": "deploy menu alias; verify new-system visible count remains zero",
                    "menu_alias_added_requires_replay": "deploy menu alias, then replay old identity set into target carrier",
                    "legacy_fuel_carrier_added_requires_replay": "deploy legacy fuel fact carrier and menu/action, then replay old identity set",
                    "existing_carrier_requires_identity_replay_or_scoped_surface": "replay old identity set or build scoped acceptance surface on target model",
                    "unclassified_requires_manual_review": "manual review required",
                }[bucket],
                "failures": row.get("failures") if isinstance(row.get("failures"), list) else [],
            }
        )
    rows_out.sort(key=lambda item: (int(item["priority"]), str(item["category"]), str(item["label"])))

    bucket_summary: dict[str, dict[str, int]] = {}
    for row in rows_out:
        stats = bucket_summary.setdefault(str(row["bucket"]), {"count": 0, "old_rows": 0})
        stats["count"] += 1
        stats["old_rows"] += int(row["old_count"] or 0)
    payload = {
        "status": "READY_FOR_REPLAY_IMPLEMENTATION_WITH_BLOCKERS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_alignment": str(ALIGNMENT.relative_to(ROOT)),
        "source_identity_lock": str(IDENTITY_LOCK.relative_to(ROOT)),
        "menu_alias_patch_file": "addons/smart_construction_core/views/menu_business_taxonomy.xml",
        "checked_count": len(rows_out),
        "old_list_identity_count": len(identities),
        "bucket_summary": bucket_summary,
        "rows": rows_out,
    }
    write_json(OUTPUT, payload)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(markdown(payload), encoding="utf-8")
    print(f"SCBSLY_DIRECT_PROJECT_REPLAY_CARRIER_PLAN={payload['status']} output={OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
