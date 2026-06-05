#!/usr/bin/env python3
"""Verify red-box accepted rows are exposed through formal business menus.

Run after projection and action wiring:
    DB_NAME=sc_demo MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo \
      bash scripts/ops/odoo_shell_exec.sh < scripts/verify/direct_acceptance_redbox_formal_menu_parity_probe.py
"""

from __future__ import annotations

import ast
import json
import os
import zlib
from pathlib import Path
from typing import Any


MODULE = "smart_construction_core"
SOURCE_SYSTEM = "online_old_scbsly"
SOURCE_FACT_MODEL = "online_old_scbsly:direct_acceptance_fact"
SOURCE_DIRECT_MODEL = "online_old_scbsly:direct_acceptance"
OUTPUT_JSON_NAME = "direct_acceptance_redbox_formal_menu_parity_probe_result_v1.json"


SPECS = [
    {
        "label": "材料计划",
        "slug": "material_plan",
        "model": "project.material.plan",
        "menu_xmlid": "smart_construction_core.menu_project_material_plan",
        "mode": "legacy_fact",
    },
    {
        "label": "报价单",
        "slug": "material_rfq",
        "model": "sc.material.rfq",
        "menu_xmlid": "smart_construction_core.menu_sc_material_quote_acceptance",
        "mode": "legacy_fact",
    },
    {
        "label": "入库",
        "slug": "material_inbound",
        "model": "sc.material.inbound",
        "menu_xmlid": "smart_construction_core.menu_sc_material_inbound",
        "mode": "legacy_fact",
    },
    {
        "label": "方单",
        "slug": "labor_usage_ticket",
        "model": "sc.labor.usage",
        "menu_xmlid": "smart_construction_core.menu_sc_labor_usage_acceptance",
        "mode": "legacy_fact",
    },
    {
        "label": "零星用工",
        "slug": "labor_casual",
        "model": "sc.labor.usage",
        "menu_xmlid": "smart_construction_core.menu_sc_labor_casual_acceptance",
        "mode": "legacy_fact",
    },
    {
        "label": "分包方单",
        "slug": "subcontract_request",
        "model": "sc.subcontract.request",
        "menu_xmlid": "smart_construction_core.menu_sc_subcontract_request_acceptance",
        "mode": "legacy_fact",
    },
    {
        "label": "机械台班记录",
        "slug": "equipment_shift",
        "model": "sc.equipment.usage",
        "menu_xmlid": "smart_construction_core.menu_sc_equipment_shift_acceptance",
        "mode": "legacy_fact",
    },
    {
        "label": "租入",
        "slug": "rental_in",
        "model": "sc.material.rental.order",
        "menu_xmlid": "smart_construction_core.menu_sc_material_rental_in_acceptance",
        "mode": "legacy_fact",
    },
    {
        "label": "还租",
        "slug": "rental_return",
        "model": "sc.material.rental.order",
        "menu_xmlid": "smart_construction_core.menu_sc_material_rental_return_acceptance",
        "mode": "legacy_fact",
    },
    {
        "label": "管理人员工资表",
        "slug": "payroll_salary",
        "model": "sc.hr.payroll.document",
        "menu_xmlid": "smart_construction_core.menu_sc_salary_registration",
        "mode": "payroll_source",
    },
    {
        "label": "油卡登记",
        "slug": "fuel_card",
        "model": "sc.fund.account.operation",
        "menu_xmlid": "smart_construction_core.menu_sc_legacy_fuel_card_fact_acceptance",
        "mode": "legacy_source",
    },
    {
        "label": "充值登记",
        "slug": "fuel_recharge",
        "model": "sc.fund.account.operation",
        "menu_xmlid": "smart_construction_core.menu_sc_legacy_fuel_card_recharge_fact_acceptance",
        "mode": "legacy_source",
    },
    {
        "label": "施工日志（新）",
        "slug": "construction_diary",
        "model": "sc.construction.diary",
        "menu_xmlid": "smart_construction_core.menu_sc_construction_diary",
        "mode": "legacy_source",
    },
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


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_redbox_parity": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def clean(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"false", "none", "null"} else text


def source_key(label: str, fact) -> int:
    token = f"{SOURCE_SYSTEM}:{label}:{fact.legacy_record_id or fact.id}".encode("utf-8")
    return zlib.crc32(token) & 0x7FFFFFFF


def action_xmlid(slug: str) -> str:
    return f"{MODULE}.action_direct_acceptance_redbox_formal_{slug}"


def formal_domain(spec: dict[str, str]) -> list[tuple[str, str, Any]]:
    label = spec["label"]
    if spec["mode"] == "legacy_fact":
        return [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", f"direct_acceptance:{label}")]
    if spec["mode"] == "payroll_source":
        return [("legacy_source_table", "=", "direct_acceptance:管理人员工资表")]
    return [("legacy_source_model", "=", SOURCE_DIRECT_MODEL), ("legacy_source_table", "=", f"direct_acceptance:{label}")]


def expected_keys(spec: dict[str, str], facts) -> set[str]:
    label = spec["label"]
    if spec["mode"] == "legacy_fact":
        return {str(source_key(label, fact)) for fact in facts}
    if spec["mode"] == "payroll_source":
        return {clean(fact.legacy_record_id) or str(fact.id) for fact in facts}
    return {f"{label}:{fact.legacy_record_id or fact.id}" for fact in facts}


def actual_keys(spec: dict[str, str], records) -> set[str]:
    if spec["mode"] == "legacy_fact":
        return {str(record.legacy_fact_id) for record in records}
    if spec["mode"] == "payroll_source":
        return {clean(record.legacy_source_id) for record in records}
    return {clean(record.legacy_record_id) for record in records}


ensure_allowed_db()
results = []

for spec in SPECS:
    label = spec["label"]
    facts = env["sc.legacy.direct.acceptance.fact"].sudo().search(  # noqa: F821
        [("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", label), ("active", "=", True)],
        order="document_no,legacy_record_id,id",
    )
    Model = env[spec["model"]].sudo().with_context(active_test=False)  # noqa: F821
    domain = formal_domain(spec)
    records = Model.search(domain)
    menu = env.ref(spec["menu_xmlid"], raise_if_not_found=False)  # noqa: F821
    action = env.ref(action_xmlid(spec["slug"]), raise_if_not_found=False)  # noqa: F821
    action_domain = []
    if action and action.domain:
        action_domain = ast.literal_eval(action.domain)
    expected = expected_keys(spec, facts)
    actual = actual_keys(spec, records)
    missing = sorted(expected - actual)[:20]
    extra = sorted(actual - expected)[:20]
    menu_action_ok = bool(menu and action and menu.action and menu.action.id == action.id)
    domain_ok = action_domain == domain
    count_ok = len(facts) == len(records)
    key_ok = expected == actual
    results.append(
        {
            "label": label,
            "model": spec["model"],
            "menu_xmlid": spec["menu_xmlid"],
            "action_xmlid": action_xmlid(spec["slug"]),
            "source_count": len(facts),
            "formal_count": len(records),
            "menu_action_ok": menu_action_ok,
            "domain_ok": domain_ok,
            "count_ok": count_ok,
            "key_ok": key_ok,
            "missing_keys_sample": missing,
            "extra_keys_sample": extra,
            "status": "PASS" if menu_action_ok and domain_ok and count_ok and key_ok else "FAIL",
        }
    )

payload = {
    "status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
    "mode": "direct_acceptance_redbox_formal_menu_parity_probe",
    "database": env.cr.dbname,  # noqa: F821
    "results": results,
}
out = artifact_root() / OUTPUT_JSON_NAME
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("DIRECT_ACCEPTANCE_REDBOX_FORMAL_MENU_PARITY_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
