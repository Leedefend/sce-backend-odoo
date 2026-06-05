#!/usr/bin/env python3
"""Sync the formal partner-payment visible list contract.

Run with:
    DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/ops/partner_payment_visible_contract_sync.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path


OUTPUT_JSON_NAME = "partner_payment_visible_contract_sync_result_v1.json"
ACTION_XMLID = "smart_construction_core.action_sc_payment_execution_partner_payment"
VIEW_NAME = "scbs55.user.visible.310.c7ac088568bd.tree"
VIEW_LABEL = "往来单位付款"
VISIBLE_FIELDS = [
    ("p1_visible_06fa8c6f628f", "单据状态"),
    ("p1_visible_f22832ce4781", "推送结果"),
    ("p1_visible_7f5da566c14e", "金蝶单据编号"),
    ("p1_visible_8fa8662ad38f", "单据编号"),
    ("p1_visible_80f75ce4d56c", "項目名称"),
    ("p1_visible_cf44ec3f55f9", "供应商名称"),
    ("p1_visible_058f511c98cf", "付款日期"),
    ("p1_visible_d890d302f7f7", "付款金额"),
    ("p1_visible_e0361480e3a5", "备注"),
    ("p1_visible_514ce8cde553", "其他备注"),
    ("p1_visible_f35ba3fab897", "付款方式名称"),
    ("p1_visible_71e47f617269", "填写人"),
    ("p1_visible_48a64eb40c71", "开户行"),
    ("p1_visible_c3d92b20c8a3", "账户"),
    ("p1_visible_48eb67df430f", "付款账户"),
    ("p1_visible_dacbd33c31fd", "付款账户名称"),
    ("p1_visible_a4aa6578aa87", "支付申请单号"),
    ("p1_visible_99f6fe6c41ad", "附件"),
    ("p1_visible_48312867161c", "录入日期"),
]


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path(f"/tmp/partner_payment/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/partner_payment/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")  # noqa: F821
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
ActionView = env["ir.actions.act_window.view"].sudo()  # noqa: F821
action = env.ref(ACTION_XMLID, raise_if_not_found=False)  # noqa: F821
if not action:
    raise RuntimeError({"missing_action": ACTION_XMLID})
if action.res_model != "sc.payment.execution":
    raise RuntimeError({"unexpected_action_model": action.res_model, "action_xmlid": ACTION_XMLID})

Model = env["sc.payment.execution"]  # noqa: F821
missing_fields = [field_name for field_name, _label in VISIBLE_FIELDS if field_name not in Model._fields]
if missing_fields:
    raise RuntimeError({"missing_visible_fields": missing_fields})

arch = "\n".join(
    [f'<tree string="{VIEW_LABEL}" create="false" edit="false" delete="false">']
    + [field_xml(field_name, label) for field_name, label in VISIBLE_FIELDS]
    + ["</tree>"]
)

view = View.search([("name", "=", VIEW_NAME), ("model", "=", "sc.payment.execution"), ("type", "=", "tree")], limit=1)
created = False
if view:
    view.write({"arch_db": arch, "active": True, "priority": 1})
else:
    view = View.create(
        {
            "name": VIEW_NAME,
            "model": "sc.payment.execution",
            "type": "tree",
            "arch_db": arch,
            "active": True,
            "priority": 1,
        }
    )
    created = True

binding = ActionView.search([("act_window_id", "=", action.id), ("view_mode", "=", "tree")], limit=1)
if binding:
    binding.write({"view_id": view.id, "sequence": 1})
else:
    ActionView.create({"act_window_id": action.id, "view_id": view.id, "view_mode": "tree", "sequence": 1})

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "partner_payment_visible_contract_sync",
    "action_id": int(action.id),
    "view_id": int(view.id),
    "view_name": view.name,
    "created": created,
    "fields": [field_name for field_name, _label in VISIBLE_FIELDS],
    "labels": [label for _field_name, label in VISIBLE_FIELDS],
}
write_json(artifact_root() / OUTPUT_JSON_NAME, payload)
print("PARTNER_PAYMENT_VISIBLE_CONTRACT_SYNC=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
