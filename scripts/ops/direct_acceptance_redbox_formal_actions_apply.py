#!/usr/bin/env python3
"""Point accepted direct-project red-box menus at formal business models.

Run with:
    DB_NAME=sc_demo MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo \
      bash scripts/ops/odoo_shell_exec.sh < scripts/ops/direct_acceptance_redbox_formal_actions_apply.py
"""

from __future__ import annotations

import json
import os
from html import escape
from pathlib import Path


MODULE = "smart_construction_core"
OUTPUT_JSON_NAME = "direct_acceptance_redbox_formal_actions_apply_result_v1.json"
SOURCE_FACT_MODEL = "online_old_scbsly:direct_acceptance_fact"
SOURCE_DIRECT_MODEL = "online_old_scbsly:direct_acceptance"


SPECS = [
    {
        "label": "材料计划",
        "slug": "material_plan",
        "model": "project.material.plan",
        "menu_xmlid": "smart_construction_core.menu_project_material_plan",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_material_plan_tree",
        "domain": [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", "direct_acceptance:材料计划")],
    },
    {
        "label": "报价单",
        "slug": "material_rfq",
        "model": "sc.material.rfq",
        "menu_xmlid": "smart_construction_core.menu_sc_material_quote_acceptance",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_material_quote_tree",
        "domain": [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", "direct_acceptance:报价单")],
    },
    {
        "label": "入库",
        "slug": "material_inbound",
        "model": "sc.material.inbound",
        "menu_xmlid": "smart_construction_core.menu_sc_material_inbound",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_material_inbound_tree",
        "domain": [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", "direct_acceptance:入库")],
    },
    {
        "label": "方单",
        "slug": "labor_usage_ticket",
        "model": "sc.labor.usage",
        "menu_xmlid": "smart_construction_core.menu_sc_labor_usage_acceptance",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_labor_usage_tree",
        "domain": [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", "direct_acceptance:方单")],
    },
    {
        "label": "零星用工",
        "slug": "labor_casual",
        "model": "sc.labor.usage",
        "menu_xmlid": "smart_construction_core.menu_sc_labor_casual_acceptance",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_labor_casual_tree",
        "domain": [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", "direct_acceptance:零星用工")],
    },
    {
        "label": "分包方单",
        "slug": "subcontract_request",
        "model": "sc.subcontract.request",
        "menu_xmlid": "smart_construction_core.menu_sc_subcontract_request_acceptance",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_subcontract_request_tree",
        "domain": [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", "direct_acceptance:分包方单")],
    },
    {
        "label": "机械台班记录",
        "slug": "equipment_shift",
        "model": "sc.equipment.usage",
        "menu_xmlid": "smart_construction_core.menu_sc_equipment_shift_acceptance",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_equipment_shift_tree",
        "domain": [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", "direct_acceptance:机械台班记录")],
    },
    {
        "label": "租入",
        "slug": "rental_in",
        "model": "sc.material.rental.order",
        "menu_xmlid": "smart_construction_core.menu_sc_material_rental_in_acceptance",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_rental_in_tree",
        "domain": [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", "direct_acceptance:租入")],
    },
    {
        "label": "还租",
        "slug": "rental_return",
        "model": "sc.material.rental.order",
        "menu_xmlid": "smart_construction_core.menu_sc_material_rental_return_acceptance",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_rental_return_tree",
        "domain": [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", "direct_acceptance:还租")],
    },
    {
        "label": "管理人员工资表",
        "slug": "payroll_salary",
        "model": "sc.hr.payroll.document",
        "menu_xmlid": "smart_construction_core.menu_sc_salary_registration",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_salary_tree",
        "domain": [("legacy_source_table", "=", "direct_acceptance:管理人员工资表")],
    },
    {
        "label": "油卡登记",
        "slug": "fuel_card",
        "model": "sc.fund.account.operation",
        "menu_xmlid": "smart_construction_core.menu_sc_legacy_fuel_card_fact_acceptance",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_fuel_card_tree",
        "domain": [("legacy_source_model", "=", SOURCE_DIRECT_MODEL), ("legacy_source_table", "=", "direct_acceptance:油卡登记")],
    },
    {
        "label": "充值登记",
        "slug": "fuel_recharge",
        "model": "sc.fund.account.operation",
        "menu_xmlid": "smart_construction_core.menu_sc_legacy_fuel_card_recharge_fact_acceptance",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_fuel_recharge_tree",
        "domain": [("legacy_source_model", "=", SOURCE_DIRECT_MODEL), ("legacy_source_table", "=", "direct_acceptance:充值登记")],
    },
    {
        "label": "施工日志（新）",
        "slug": "construction_diary",
        "model": "sc.construction.diary",
        "menu_xmlid": "smart_construction_core.menu_sc_construction_diary",
        "source_tree_xmlid": "smart_construction_core.view_scbsly_direct_acceptance_construction_diary_tree",
        "domain": [("legacy_source_model", "=", SOURCE_DIRECT_MODEL), ("legacy_source_table", "=", "direct_acceptance:施工日志（新）")],
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
        raise RuntimeError({"db_name_not_allowed_for_redbox_actions": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def xml_name(slug: str) -> str:
    return "action_direct_acceptance_redbox_formal_" + slug


def ensure_xmlid(record, name: str) -> None:
    Imd = env["ir.model.data"].sudo()  # noqa: F821
    existing = Imd.search([("module", "=", MODULE), ("name", "=", name), ("model", "=", record._name)], limit=1)
    if existing:
        if int(existing.res_id or 0) != int(record.id):
            existing.write({"res_id": int(record.id)})
        return
    Imd.create({"module": MODULE, "name": name, "model": record._name, "res_id": int(record.id), "noupdate": True})


def view_xml_name(slug: str) -> str:
    return "view_direct_acceptance_redbox_formal_" + slug + "_tree"


def source_tree_columns(source_tree_xmlid: str) -> list[dict[str, str]]:
    source_view = env.ref(source_tree_xmlid, raise_if_not_found=False)  # noqa: F821
    if not source_view:
        raise RuntimeError({"missing_source_tree_view": source_tree_xmlid})
    try:
        from lxml import etree

        root = etree.fromstring(source_view.arch_db.encode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError({"invalid_source_tree_view": source_tree_xmlid, "error": repr(exc)}) from exc
    columns = []
    for node in root.xpath(".//field"):
        name = node.get("name") or ""
        if not name.startswith("legacy_visible_"):
            continue
        columns.append({"name": name, "string": node.get("string") or ""})
    if not columns:
        raise RuntimeError({"empty_source_tree_columns": source_tree_xmlid})
    return columns


def ensure_formal_tree_view(spec: dict) -> tuple[object, list[dict[str, str]]]:
    columns = source_tree_columns(spec["source_tree_xmlid"])
    fields_arch = "\n".join(
        f'        <field name="{column["name"]}" string="{escape(column["string"])}"/>'
        for column in columns
    )
    arch = (
        f'<tree string="{escape(spec["label"])}" create="false" edit="false" delete="false">\n'
        f"{fields_arch}\n"
        "</tree>"
    )
    view_name = view_xml_name(spec["slug"])
    view = env.ref(f"{MODULE}.{view_name}", raise_if_not_found=False)  # noqa: F821
    values = {
        "name": f'{spec["model"]}.{view_name}',
        "model": spec["model"],
        "type": "tree",
        "arch": arch,
    }
    if view:
        view.write(values)
    else:
        view = env["ir.ui.view"].sudo().create(values)  # noqa: F821
        ensure_xmlid(view, view_name)
    return view, columns


ensure_allowed_db()
Action = env["ir.actions.act_window"].sudo()  # noqa: F821
results = []

for spec in SPECS:
    if spec["model"] not in env:  # noqa: F821
        results.append({"label": spec["label"], "status": "FAIL", "reason": "missing_model", "model": spec["model"]})
        continue
    action_xml_name = xml_name(spec["slug"])
    action = env.ref(f"{MODULE}.{action_xml_name}", raise_if_not_found=False)  # noqa: F821
    tree_view, visible_columns = ensure_formal_tree_view(spec)
    values = {
        "name": spec["label"],
        "res_model": spec["model"],
        "view_mode": "tree,form",
        "view_id": int(tree_view.id),
        "domain": repr(spec["domain"]),
        "context": "{'create': False, 'search_default_active_rows': 1}",
    }
    if action:
        action.write(values)
    else:
        action = Action.create(values)
        ensure_xmlid(action, action_xml_name)
    menu = env.ref(spec["menu_xmlid"], raise_if_not_found=False)  # noqa: F821
    if not menu:
        results.append({"label": spec["label"], "status": "FAIL", "reason": "missing_menu", "menu_xmlid": spec["menu_xmlid"]})
        continue
    menu.sudo().write({"action": f"{action._name},{action.id}", "active": True})
    source_count = env["sc.legacy.direct.acceptance.fact"].sudo().search_count(  # noqa: F821
        [("source_system", "=", "online_old_scbsly"), ("acceptance_label", "=", spec["label"]), ("active", "=", True)]
    )
    formal_count = env[spec["model"]].sudo().with_context(active_test=False).search_count(spec["domain"])  # noqa: F821
    results.append(
        {
            "label": spec["label"],
            "status": "PASS",
            "model": spec["model"],
            "menu_xmlid": spec["menu_xmlid"],
            "action_xmlid": f"{MODULE}.{action_xml_name}",
            "action_id": int(action.id),
            "tree_view_xmlid": f"{MODULE}.{view_xml_name(spec['slug'])}",
            "visible_column_count": len(visible_columns),
            "visible_columns": [column["string"] for column in visible_columns],
            "source_count": source_count,
            "formal_count": formal_count,
        }
    )

env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
    "mode": "direct_acceptance_redbox_formal_actions_apply",
    "database": env.cr.dbname,  # noqa: F821
    "results": results,
}
out = artifact_root() / OUTPUT_JSON_NAME
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("DIRECT_ACCEPTANCE_REDBOX_FORMAL_ACTIONS_APPLY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
