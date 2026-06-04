#!/usr/bin/env python3
"""Sync the formal engineering-progress income visible list contract.

Run with:
    DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/ops/engineering_progress_income_visible_contract_sync.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path


OUTPUT_JSON_NAME = "engineering_progress_income_visible_contract_sync_result_v1.json"
ACTION_XMLID = "smart_construction_core.action_sc_receipt_income_engineering_progress"
VIEW_NAME = "scbs55.user.visible.250.aaaf7ca11e80.tree"
VIEW_LABEL = "工程进度款收入登记"
VISIBLE_FIELDS = [
    ("p1_visible_06fa8c6f628f", "单据状态"),
    ("p1_visible_3e7255522b33", "项目名称"),
    ("p1_visible_00381a68b952", "往来单位"),
    ("p1_visible_8cd973ab9373", "承包单位"),
    ("p1_visible_205fcc1bc5d4", "施工管理合同"),
    ("p1_visible_8fa8662ad38f", "单据编号"),
    ("p1_visible_71e47f617269", "填写人"),
    ("p1_visible_49a5d541678c", "收款账户"),
    ("p1_visible_2ff90909b29b", "进账金额"),
    ("p1_visible_807b71479e35", "收入类别"),
    ("p1_visible_0d20172efa91", "收款时间"),
    ("p1_visible_e0361480e3a5", "备注"),
    ("p1_visible_99f6fe6c41ad", "附件"),
    ("p1_visible_ee6a4d9e2956", "录入人"),
    ("p1_visible_dfc25d77dc39", "录入时间"),
]


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path(f"/tmp/engineering_progress_income/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/engineering_progress_income/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_visible_contract_sync": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def field_xml(field_name: str, label: str) -> str:
    return f'  <field name="{field_name}" string="{label}" readonly="1"/>'


ensure_allowed_db()
View = env["ir.ui.view"].sudo()  # noqa: F821
Action = env["ir.actions.act_window"].sudo()  # noqa: F821
action = env.ref(ACTION_XMLID, raise_if_not_found=False)  # noqa: F821
if not action:
    raise RuntimeError({"missing_action": ACTION_XMLID})
if action.res_model != "sc.receipt.income":
    raise RuntimeError({"unexpected_action_model": action.res_model, "action_xmlid": ACTION_XMLID})

missing_fields = [
    field_name
    for field_name, _label in VISIBLE_FIELDS
    if field_name not in env["sc.receipt.income"]._fields  # noqa: F821
]
if missing_fields:
    raise RuntimeError({"missing_visible_fields": missing_fields})

arch = "\n".join(
    [f'<tree string="{VIEW_LABEL}" create="false" edit="false" delete="false">']
    + [field_xml(field_name, label) for field_name, label in VISIBLE_FIELDS]
    + ["</tree>"]
)

view = View.search([("name", "=", VIEW_NAME), ("model", "=", "sc.receipt.income"), ("type", "=", "tree")], limit=1)
created = False
if view:
    view.write({"arch_db": arch, "active": True, "priority": 1})
else:
    view = View.create(
        {
            "name": VIEW_NAME,
            "model": "sc.receipt.income",
            "type": "tree",
            "arch_db": arch,
            "active": True,
            "priority": 1,
        }
    )
    created = True

ActionView = env["ir.actions.act_window.view"].sudo()  # noqa: F821
binding = ActionView.search([("act_window_id", "=", action.id), ("view_mode", "=", "tree")], limit=1)
if binding:
    binding.write({"view_id": view.id, "sequence": 1})
else:
    ActionView.create({"act_window_id": action.id, "view_id": view.id, "view_mode": "tree", "sequence": 1})

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "engineering_progress_income_visible_contract_sync",
    "action_id": int(action.id),
    "view_id": int(view.id),
    "view_name": view.name,
    "created": created,
    "fields": [field_name for field_name, _label in VISIBLE_FIELDS],
}
write_json(artifact_root() / OUTPUT_JSON_NAME, payload)
print("ENGINEERING_PROGRESS_INCOME_VISIBLE_CONTRACT_SYNC=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
