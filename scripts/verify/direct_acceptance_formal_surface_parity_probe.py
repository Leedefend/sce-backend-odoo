#!/usr/bin/env python3
"""Verify formal menu list surfaces match direct acceptance list surfaces."""

from __future__ import annotations

import json
import os
import zlib
from pathlib import Path
from typing import Any

from lxml import etree


SOURCE_SYSTEM = "online_old_scbsly"
SOURCE_FACT_MODEL = "online_old_scbsly:direct_acceptance_fact"
SOURCE_DIRECT_MODEL = "online_old_scbsly:direct_acceptance"
OUTPUT_JSON_NAME = "direct_acceptance_formal_surface_parity_probe_result_v1.json"


SPECS = [
    ("材料计划", "project.material.plan", "legacy_fact", "smart_construction_core.action_direct_acceptance_redbox_formal_material_plan", "smart_construction_core.view_scbsly_direct_acceptance_material_plan_tree"),
    ("报价单", "sc.material.rfq", "legacy_fact", "smart_construction_core.action_direct_acceptance_redbox_formal_material_rfq", "smart_construction_core.view_scbsly_direct_acceptance_material_quote_tree"),
    ("入库", "sc.material.inbound", "legacy_fact", "smart_construction_core.action_direct_acceptance_redbox_formal_material_inbound", "smart_construction_core.view_scbsly_direct_acceptance_material_inbound_tree"),
    ("方单", "sc.labor.usage", "legacy_fact", "smart_construction_core.action_direct_acceptance_redbox_formal_labor_usage_ticket", "smart_construction_core.view_scbsly_direct_acceptance_labor_usage_tree"),
    ("零星用工", "sc.labor.usage", "legacy_fact", "smart_construction_core.action_direct_acceptance_redbox_formal_labor_casual", "smart_construction_core.view_scbsly_direct_acceptance_labor_casual_tree"),
    ("分包方单", "sc.subcontract.request", "legacy_fact", "smart_construction_core.action_direct_acceptance_redbox_formal_subcontract_request", "smart_construction_core.view_scbsly_direct_acceptance_subcontract_request_tree"),
    ("机械台班记录", "sc.equipment.usage", "legacy_fact", "smart_construction_core.action_direct_acceptance_redbox_formal_equipment_shift", "smart_construction_core.view_scbsly_direct_acceptance_equipment_shift_tree"),
    ("租入", "sc.material.rental.order", "legacy_fact", "smart_construction_core.action_direct_acceptance_redbox_formal_rental_in", "smart_construction_core.view_scbsly_direct_acceptance_rental_in_tree"),
    ("还租", "sc.material.rental.order", "legacy_fact", "smart_construction_core.action_direct_acceptance_redbox_formal_rental_return", "smart_construction_core.view_scbsly_direct_acceptance_rental_return_tree"),
    ("管理人员工资表", "sc.hr.payroll.document", "legacy_source_payroll", "smart_construction_core.action_direct_acceptance_redbox_formal_payroll_salary", "smart_construction_core.view_scbsly_direct_acceptance_salary_tree"),
    ("油卡登记", "sc.fund.account.operation", "legacy_source_record", "smart_construction_core.action_direct_acceptance_redbox_formal_fuel_card", "smart_construction_core.view_scbsly_direct_acceptance_fuel_card_tree"),
    ("充值登记", "sc.fund.account.operation", "legacy_source_record", "smart_construction_core.action_direct_acceptance_redbox_formal_fuel_recharge", "smart_construction_core.view_scbsly_direct_acceptance_fuel_recharge_tree"),
    ("施工日志（新）", "sc.construction.diary", "legacy_source_record", "smart_construction_core.action_direct_acceptance_redbox_formal_construction_diary", "smart_construction_core.view_scbsly_direct_acceptance_construction_diary_tree"),
]


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path(f"/tmp/direct_acceptance_redbox/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_test"
            probe.write_text("", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/direct_acceptance_redbox/{env.cr.dbname}")  # noqa: F821


def clean(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return "" if text.lower() in {"false", "none", "null"} else text


def source_key(label: str, fact) -> int:
    token = f"{SOURCE_SYSTEM}:{label}:{fact.legacy_record_id or fact.id}".encode("utf-8")
    return zlib.crc32(token) & 0x7FFFFFFF


def tree_columns(view) -> list[tuple[str, str]]:
    root = etree.fromstring(view.arch_db.encode("utf-8"))
    return [
        (node.get("name") or "", node.get("string") or "")
        for node in root.xpath(".//field")
        if (node.get("name") or "").startswith("legacy_visible_")
    ]


def formal_domain(label: str, mode: str):
    if mode == "legacy_fact":
        return [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", f"direct_acceptance:{label}")]
    if mode == "legacy_source_payroll":
        return [("legacy_source_table", "=", "direct_acceptance:管理人员工资表")]
    return [("legacy_source_model", "=", SOURCE_DIRECT_MODEL), ("legacy_source_table", "=", f"direct_acceptance:{label}")]


def formal_key(label: str, mode: str, row: dict) -> str:
    if mode == "legacy_fact":
        return str(row.get("legacy_fact_id") or "")
    if mode == "legacy_source_payroll":
        return clean(row.get("legacy_source_id"))
    return clean(row.get("legacy_record_id"))


def fact_key(label: str, mode: str, fact) -> str:
    if mode == "legacy_fact":
        return str(source_key(label, fact))
    if mode == "legacy_source_payroll":
        return clean(fact.legacy_record_id) or str(fact.id)
    return f"{label}:{fact.legacy_record_id or fact.id}"


results = []

for label, model_name, mode, action_xmlid, source_tree_xmlid in SPECS:
    action = env.ref(action_xmlid, raise_if_not_found=False)  # noqa: F821
    source_view = env.ref(source_tree_xmlid, raise_if_not_found=False)  # noqa: F821
    formal_view = action.view_id if action else False
    source_columns = tree_columns(source_view) if source_view else []
    formal_columns = tree_columns(formal_view) if formal_view else []
    fields = [name for name, _label in source_columns]
    key_fields = ["legacy_fact_id"] if mode == "legacy_fact" else (["legacy_source_id"] if mode == "legacy_source_payroll" else ["legacy_record_id"])
    formal_rows = env[model_name].sudo().with_context(active_test=False).search_read(  # noqa: F821
        formal_domain(label, mode),
        fields=key_fields + fields,
        limit=None,
    )
    formal_by_key = {formal_key(label, mode, row): row for row in formal_rows}
    facts = env["sc.legacy.direct.acceptance.fact"].sudo().search(  # noqa: F821
        [("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", label), ("active", "=", True)],
        order="document_no,legacy_record_id,id",
    )
    mismatches = []
    missing = []
    for fact in facts:
        key = fact_key(label, mode, fact)
        row = formal_by_key.get(key)
        if not row:
            missing.append(key)
            continue
        for field_name in fields:
            expected = clean(getattr(fact, field_name, ""))
            actual = clean(row.get(field_name))
            if expected != actual:
                mismatches.append({"key": key, "field": field_name, "expected": expected, "actual": actual})
                break
        if len(mismatches) >= 20:
            break
    results.append(
        {
            "label": label,
            "model": model_name,
            "source_count": len(facts),
            "formal_count": len(formal_rows),
            "column_count": len(source_columns),
            "columns_match": source_columns == formal_columns,
            "missing_count": len(missing),
            "mismatch_count_sampled": len(mismatches),
            "mismatch_samples": mismatches[:5],
            "status": "PASS" if len(facts) == len(formal_rows) and source_columns == formal_columns and not missing and not mismatches else "FAIL",
        }
    )

payload = {
    "status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
    "mode": "direct_acceptance_formal_surface_parity_probe",
    "database": env.cr.dbname,  # noqa: F821
    "results": results,
}
out = artifact_root() / OUTPUT_JSON_NAME
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("DIRECT_ACCEPTANCE_FORMAL_SURFACE_PARITY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
