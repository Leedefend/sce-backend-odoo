# -*- coding: utf-8 -*-
"""Backfill material plan list contract labels.

Run with:
    odoo shell -d sc_demo -c /path/to/odoo.conf --no-http < scripts/migration/material_plan_list_contract_label_backfill_write.py
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path


MATERIAL_PLAN_LEGACY_VISIBLE_COLUMN_LABELS = {
    "legacy_visible_01": "单据状态",
    "legacy_visible_02": "单据编号",
    "legacy_visible_03": "单据日期",
    "legacy_visible_04": "到货时间",
    "legacy_visible_05": "采购材料名称",
    "legacy_visible_06": "规格型号",
    "legacy_visible_07": "单位",
    "legacy_visible_08": "数量",
    "legacy_visible_09": "材料别名(设计/清单)",
    "legacy_visible_10": "备注",
    "legacy_visible_11": "附件",
    "legacy_visible_12": "项目名称",
    "legacy_visible_13": "录入人",
    "legacy_visible_14": "录入时间",
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


def normalize_row(row):
    if isinstance(row, str):
        field_name = row.strip()
        label = MATERIAL_PLAN_LEGACY_VISIBLE_COLUMN_LABELS.get(field_name)
        return {"name": field_name, "label": label, "string": label} if label else row
    if not isinstance(row, dict):
        return row
    field_name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
    label = MATERIAL_PLAN_LEGACY_VISIBLE_COLUMN_LABELS.get(field_name)
    if not label:
        return row
    next_row = dict(row)
    next_row["label"] = label
    next_row["string"] = label
    return next_row


def backfill() -> dict:
    ensure_allowed_db()
    Contract = env["ui.business.config.contract"].sudo()  # noqa: F821
    action = env.ref("smart_construction_core.action_project_material_plan", raise_if_not_found=False)  # noqa: F821
    action_id = action.id if action else 0
    domain = [
        ("model", "=", "project.material.plan"),
        ("view_type", "in", ["tree", "list"]),
        ("status", "=", "published"),
    ]
    if action_id:
        domain.append(("action_id", "=", action_id))
    contracts = Contract.search(domain, order="id")
    updated = []
    for contract in contracts:
        payload = deepcopy(contract.contract_json or {})
        if not isinstance(payload, dict):
            continue
        orchestration = payload.get("view_orchestration")
        if not isinstance(orchestration, dict):
            continue
        views = orchestration.get("views")
        if not isinstance(views, dict):
            continue
        changed = False
        for view_key in ("tree", "list"):
            spec = views.get(view_key)
            if not isinstance(spec, dict):
                continue
            for row_key in ("columns", "fields"):
                rows = spec.get(row_key)
                if not isinstance(rows, list):
                    continue
                next_rows = [normalize_row(row) for row in rows]
                if next_rows != rows:
                    spec[row_key] = next_rows
                    changed = True
        if not changed:
            continue
        context = dict(orchestration.get("context") or {})
        context["material_plan_list_label_backfill"] = "formal_business_labels_v1"
        orchestration["context"] = context
        contract.write(
            {
                "contract_json": payload,
                "version_no": int(contract.version_no or 1) + 1,
            }
        )
        updated.append(contract.id)
    env.cr.commit()  # noqa: F821
    result = {
        "database": env.cr.dbname,  # noqa: F821
        "action_id": action_id,
        "updated_contract_ids": updated,
        "updated_count": len(updated),
    }
    output = artifact_root() / "material_plan_list_contract_label_backfill_result_v1.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[material_plan_list_contract_label_backfill] %s" % json.dumps(result, ensure_ascii=False))
    return result


backfill()
