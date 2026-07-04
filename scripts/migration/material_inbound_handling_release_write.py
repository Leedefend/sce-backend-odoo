# -*- coding: utf-8 -*-
"""Publish the formal material inbound handling entry and list contract.

Run with:
    MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo \
    odoo shell -d sc_demo -c /path/to/odoo.conf --no-http \
      < scripts/migration/material_inbound_handling_release_write.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from odoo.addons.smart_core.handlers.form_field_configuration import (
    _business_config_contract_name,
    _business_config_view_orchestration_payload,
)


FORMAL_COLUMNS = [
    "name",
    "project_id",
    "business_category_id",
    "operation_strategy",
    "inbound_date",
    "material_name_summary",
    "material_spec_summary",
    "material_uom_summary",
    "total_qty",
    "unit_price_summary",
    "amount_total",
    "acceptance_id",
    "supplier_id",
    "warehouse_id",
    "dest_location_id",
    "keeper_id",
    "line_note_summary",
    "state",
    "source_created_by",
    "source_created_at",
]

FORMAL_LABELS = {
    "name": "入库单号",
    "project_id": "项目",
    "business_category_id": "业务分类",
    "operation_strategy": "经营方式",
    "inbound_date": "入库日期",
    "material_name_summary": "材料名称",
    "material_spec_summary": "规格型号",
    "material_uom_summary": "单位",
    "total_qty": "入库数量合计",
    "unit_price_summary": "单价",
    "amount_total": "金额合计",
    "acceptance_id": "来源验收单",
    "supplier_id": "供应商",
    "warehouse_id": "仓库",
    "dest_location_id": "入库库位",
    "keeper_id": "保管员",
    "line_note_summary": "备注",
    "state": "状态",
    "source_created_by": "录入人",
    "source_created_at": "录入时间",
}

SEARCH_FILTERS = [
    "project_id",
    "business_category_id",
    "supplier_id",
    "warehouse_id",
    "keeper_id",
    "state",
    "inbound_date",
]

SEARCH_GROUP_BY = [
    "project_id",
    "business_category_id",
    "supplier_id",
    "warehouse_id",
    "state",
]

LEGACY_VISIBLE_LABELS = {
    "legacy_visible_01": "单据状态",
    "legacy_visible_02": "入库单号",
    "legacy_visible_03": "单据日期",
    "legacy_visible_04": "供应商名称",
    "legacy_visible_05": "材料名称",
    "legacy_visible_06": "规格型号",
    "legacy_visible_07": "数量",
    "legacy_visible_08": "单价",
    "legacy_visible_09": "税率",
    "legacy_visible_10": "含税金额",
    "legacy_visible_11": "入库总数量",
    "legacy_visible_12": "付款状态",
    "legacy_visible_13": "已付款金额",
    "legacy_visible_14": "未付款金额",
    "legacy_visible_15": "结算状态",
    "legacy_visible_16": "已结算金额",
    "legacy_visible_17": "项目名称",
    "legacy_visible_18": "备注",
    "legacy_visible_19": "附件",
    "legacy_visible_20": "录入人",
    "legacy_visible_21": "录入时间",
    "legacy_visible_22": "采购人",
    "source_created_by": "录入人",
    "source_created_at": "录入时间",
}


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def _valid_names(names: list[str]) -> list[str]:
    fields = set(getattr(env["sc.material.inbound"], "_fields", {}) or {})  # noqa: F821
    return [name for name in names if name in fields]


def _with_tree_labels(payload: dict) -> dict:
    orchestration = payload.setdefault("view_orchestration", {})
    views = orchestration.setdefault("views", {})
    tree = views.setdefault("tree", {})
    columns = tree.get("columns") if isinstance(tree.get("columns"), list) else []
    for row in columns:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        label = FORMAL_LABELS.get(name)
        if label:
            row["label"] = label
            row["string"] = label
    context = orchestration.get("context") if isinstance(orchestration.get("context"), dict) else {}
    context["material_inbound_handling_contract"] = "formal_business_labels_v1"
    orchestration["context"] = context
    return payload


def _upsert_contract(*, model: str, view_type: str, action_id: int, payload: dict):
    Contract = env["ui.business.config.contract"].sudo()  # noqa: F821
    name = _business_config_contract_name(model, view_type, action_id, 0)
    domain = [
        ("name", "=", name),
        ("company_id", "=", env.company.id),  # noqa: F821
        ("view_type", "=", view_type),
        ("action_id", "=", action_id),
        ("view_id", "=", False),
        ("role_key", "=", False),
    ]
    vals = {
        "name": name,
        "model": model,
        "view_type": view_type,
        "action_id": action_id,
        "view_id": False,
        "role_key": False,
        "contract_json": payload,
        "status": "published",
    }
    rec = Contract.search(domain, limit=1)
    if rec:
        rec.write(vals)
    else:
        rec = Contract.create(vals)
    rec.action_publish()
    return rec


def _normalize_legacy_row(row):
    if isinstance(row, str):
        label = LEGACY_VISIBLE_LABELS.get(row)
        return {"name": row, "label": label, "string": label} if label else row
    if not isinstance(row, dict):
        return row
    name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
    label = LEGACY_VISIBLE_LABELS.get(name)
    if not label:
        return row
    next_row = dict(row)
    next_row["label"] = label
    next_row["string"] = label
    return next_row


def _backfill_legacy_history_labels(formal_action_id: int) -> list[int]:
    Contract = env["ui.business.config.contract"].sudo()  # noqa: F821
    updated = []
    contracts = Contract.search(
        [
            ("model", "=", "sc.material.inbound"),
            ("view_type", "in", ["tree", "list"]),
            ("status", "=", "published"),
        ],
        order="id",
    )
    for contract in contracts:
        if contract.action_id and contract.action_id.id == formal_action_id:
            continue
        payload = dict(contract.contract_json or {})
        orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
        views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
        changed = False
        for view_key in ("tree", "list"):
            spec = views.get(view_key)
            if not isinstance(spec, dict):
                continue
            for row_key in ("columns", "fields"):
                rows = spec.get(row_key)
                if not isinstance(rows, list):
                    continue
                next_rows = [_normalize_legacy_row(row) for row in rows]
                if next_rows != rows:
                    spec[row_key] = next_rows
                    changed = True
        if changed:
            context = orchestration.get("context") if isinstance(orchestration.get("context"), dict) else {}
            context["material_inbound_list_label_backfill"] = "formal_business_labels_v1"
            orchestration["context"] = context
            contract.write({"contract_json": payload, "version_no": int(contract.version_no or 1) + 1})
            updated.append(contract.id)
    return updated


def publish() -> dict:
    ensure_allowed_db()
    menu = env.ref("smart_construction_core.menu_sc_material_inbound", raise_if_not_found=False)  # noqa: F821
    action = env.ref("smart_construction_core.action_sc_material_inbound_handling", raise_if_not_found=False)  # noqa: F821
    if not menu or not action:
        raise RuntimeError("missing material inbound menu or formal handling action")

    previous_action = "%s,%s" % (menu.action.type, menu.action.id) if menu.action else ""
    menu.write({"action": "ir.actions.act_window,%s" % action.id})

    model = "sc.material.inbound"
    tree_payload = _business_config_view_orchestration_payload(
        view_type="tree",
        names=_valid_names(FORMAL_COLUMNS),
    )
    tree = _upsert_contract(
        model=model,
        view_type="tree",
        action_id=action.id,
        payload=_with_tree_labels(tree_payload),
    )

    search_payload = _business_config_view_orchestration_payload(
        view_type="search",
        names=_valid_names(SEARCH_FILTERS),
        search_key="filters",
    )
    search_payload = _business_config_view_orchestration_payload(
        view_type="search",
        names=_valid_names(SEARCH_GROUP_BY),
        existing=search_payload,
        search_key="group_by",
    )
    search = _upsert_contract(
        model=model,
        view_type="search",
        action_id=action.id,
        payload=search_payload,
    )

    legacy_updated = _backfill_legacy_history_labels(action.id)
    env.cr.commit()  # noqa: F821
    result = {
        "database": env.cr.dbname,  # noqa: F821
        "menu_id": menu.id,
        "previous_menu_action": previous_action,
        "current_menu_action": "ir.actions.act_window,%s" % action.id,
        "formal_action_id": action.id,
        "tree_contract_id": tree.id,
        "search_contract_id": search.id,
        "legacy_label_contract_ids": legacy_updated,
    }
    output = artifact_root() / "material_inbound_handling_release_result_v1.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[material_inbound_handling_release] %s" % json.dumps(result, ensure_ascii=False))
    return result


publish()
