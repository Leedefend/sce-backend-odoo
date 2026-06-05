#!/usr/bin/env python3
"""Sync the formal output-invoice-registration visible list contract."""

from __future__ import annotations

import json
import os
from pathlib import Path


OUTPUT_JSON_NAME = "output_invoice_registration_visible_contract_sync_result_v1.json"
ACTION_XMLID = "smart_construction_core.action_sc_invoice_registration_user"
MENU_XMLID = "smart_construction_core.menu_sc_invoice_registration_user"
VIEW_NAME = "scbs55.user.visible.040.output.invoice.registration.tree"
VIEW_LABEL = "销项开票登记"
SOURCE_MODEL = "online_old_scbs:C_JXXP_XXKPDJ:list890"
VISIBLE_FIELDS = [
    ("p1_visible_06fa8c6f628f", "单据状态"),
    ("p1_visible_f22832ce4781", "推送结果"),
    ("p1_visible_7f5da566c14e", "金蝶单据编号"),
    ("p1_visible_8fa8662ad38f", "单据编号"),
    ("p1_visible_3e7255522b33", "项目名称"),
    ("p1_visible_f9cc22d53aff", "受票方名称"),
    ("p1_visible_c73a8eab0d57", "含税金额"),
    ("p1_visible_99f753ed6262", "税额"),
    ("p1_visible_007363f27191", "不含税金额"),
    ("p1_visible_c1b95b8ca332", "附加税"),
    ("p1_visible_0e2126d6cf82", "开票张数"),
    ("p1_visible_37d56ad493cf", "税率"),
    ("p1_visible_964a2edc6942", "关联回款金额"),
    ("p1_visible_ada9a85eab00", "发票号"),
    ("p1_visible_bbe7bbee241e", "发票种类"),
    ("p1_visible_be5462bd6a62", "开票单位"),
    ("p1_visible_99f6fe6c41ad", "附件"),
    ("p1_visible_ee6a4d9e2956", "录入人"),
    ("p1_visible_d42c2d26610f", "开票日期"),
    ("p1_visible_dfc25d77dc39", "录入时间"),
]


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path(f"/tmp/output_invoice_registration/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/output_invoice_registration/{env.cr.dbname}")  # noqa: F821


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
menu = env.ref(MENU_XMLID, raise_if_not_found=False)  # noqa: F821
if not action:
    raise RuntimeError({"missing_action": ACTION_XMLID})
if action.res_model != "sc.invoice.registration":
    raise RuntimeError({"unexpected_action_model": action.res_model, "action_xmlid": ACTION_XMLID})

Model = env["sc.invoice.registration"]  # noqa: F821
missing_fields = [field_name for field_name, _label in VISIBLE_FIELDS if field_name not in Model._fields]
if missing_fields:
    raise RuntimeError({"missing_visible_fields": missing_fields})

arch = "\n".join(
    [f'<tree string="{VIEW_LABEL}" create="false" edit="false" delete="false">']
    + [field_xml(field_name, label) for field_name, label in VISIBLE_FIELDS]
    + ["</tree>"]
)

view = View.search([("name", "=", VIEW_NAME), ("model", "=", "sc.invoice.registration"), ("type", "=", "tree")], limit=1)
created = False
if view:
    view.write({"arch_db": arch, "active": True, "priority": 1})
else:
    view = View.create(
        {
            "name": VIEW_NAME,
            "model": "sc.invoice.registration",
            "type": "tree",
            "arch_db": arch,
            "active": True,
            "priority": 1,
        }
    )
    created = True

action.write(
    {
        "name": VIEW_LABEL,
        "domain": repr([("legacy_source_model", "=", SOURCE_MODEL)]),
        "context": "{'default_source_kind': 'output_invoice_tax', 'default_direction': 'output', 'default_invoice_content': '销项开票登记', 'search_default_group_project': 1}",
    }
)
if menu:
    menu.write({"name": VIEW_LABEL, "active": True, "action": f"ir.actions.act_window,{action.id}"})

binding = ActionView.search([("act_window_id", "=", action.id), ("view_mode", "=", "tree")], limit=1)
if binding:
    binding.write({"view_id": view.id, "sequence": 1})
else:
    ActionView.create({"act_window_id": action.id, "view_id": view.id, "view_mode": "tree", "sequence": 1})

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "output_invoice_registration_visible_contract_sync",
    "action_id": int(action.id),
    "menu_id": int(menu.id) if menu else None,
    "view_id": int(view.id),
    "view_name": view.name,
    "created": created,
    "source_model": SOURCE_MODEL,
    "fields": [field_name for field_name, _label in VISIBLE_FIELDS],
    "labels": [label for _field_name, label in VISIBLE_FIELDS],
}
write_json(artifact_root() / OUTPUT_JSON_NAME, payload)
print("OUTPUT_INVOICE_REGISTRATION_VISIBLE_CONTRACT_SYNC=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
