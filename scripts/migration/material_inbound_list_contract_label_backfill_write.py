# -*- coding: utf-8 -*-
"""Backfill material inbound legacy list contract labels.

Run with:
    odoo shell -d sc_demo -c /path/to/odoo.conf --no-http < scripts/migration/material_inbound_list_contract_label_backfill_write.py
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path


MATERIAL_INBOUND_LEGACY_VISIBLE_COLUMN_LABELS = {
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


def normalize_row(row):
    if isinstance(row, str):
        field_name = row.strip()
        label = MATERIAL_INBOUND_LEGACY_VISIBLE_COLUMN_LABELS.get(field_name)
        return {"name": field_name, "label": label, "string": label} if label else row
    if not isinstance(row, dict):
        return row
    field_name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
    label = MATERIAL_INBOUND_LEGACY_VISIBLE_COLUMN_LABELS.get(field_name)
    if not label:
        return row
    next_row = dict(row)
    next_row["label"] = label
    next_row["string"] = label
    return next_row


def backfill() -> dict:
    ensure_allowed_db()
    Contract = env["ui.business.config.contract"].sudo()  # noqa: F821
    contracts = Contract.search(
        [
            ("model", "=", "sc.material.inbound"),
            ("view_type", "in", ["tree", "list"]),
            ("status", "=", "published"),
        ],
        order="id",
    )
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
        context["material_inbound_list_label_backfill"] = "formal_business_labels_v1"
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
        "updated_contract_ids": updated,
        "updated_count": len(updated),
    }
    output = artifact_root() / "material_inbound_list_contract_label_backfill_result_v1.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[material_inbound_list_contract_label_backfill] %s" % json.dumps(result, ensure_ascii=False))
    return result


backfill()
