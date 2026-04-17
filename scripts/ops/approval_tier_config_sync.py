"""Configure the default approval tier for payable request lifecycle.

Run through Odoo shell:
odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < /mnt/scripts/ops/approval_tier_config_sync.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path


RUN_ID = "ITER-2026-04-17-APPROVAL-TIER-CONFIG-SYNC"
TARGET_DB = "sc_demo"
DEFINITION_NAME = "付款申请财务经理审批"
TARGET_MODEL = "payment.request"
APPROVED_ACTION_NAME = "付款申请审批通过回调（运行时兼容）"
REJECTED_ACTION_NAME = "付款申请审批驳回回调（运行时兼容）"

OUTPUT_JSON = Path("/mnt/artifacts/ops/approval_tier_config_sync_result_v1.json")
ROLLBACK_JSON = Path("/mnt/artifacts/ops/approval_tier_config_sync_rollback_v1.json")


def clean(value):
    return "" if value is None or value is False else str(value).strip()


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def definition_payload(definition):
    return {
        "id": definition.id,
        "name": clean(definition.name),
        "model": clean(definition.model),
        "active": bool(definition.active),
        "review_type": clean(definition.review_type),
        "reviewer_group_xmlid": clean(definition.reviewer_group_id.get_external_id().get(definition.reviewer_group_id.id))
        if definition.reviewer_group_id
        else "",
        "server_action_xmlid": clean(definition.server_action_id.get_external_id().get(definition.server_action_id.id))
        if definition.server_action_id
        else "",
        "rejected_server_action_xmlid": clean(
            definition.rejected_server_action_id.get_external_id().get(definition.rejected_server_action_id.id)
        )
        if definition.rejected_server_action_id
        else "",
        "approve_sequence": bool(definition.approve_sequence),
        "notify_on_create": bool(definition.notify_on_create),
    }


def collect_state():
    Definition = env["tier.definition"].sudo()  # noqa: F821
    Action = env["ir.actions.server"].sudo()  # noqa: F821
    definitions = Definition.search([("model", "=", TARGET_MODEL)])
    return {
        "definition_count": len(definitions),
        "definitions": [definition_payload(item) for item in definitions],
        "runtime_action_count": Action.search_count(
            [
                ("model_id.model", "=", TARGET_MODEL),
                ("name", "in", [APPROVED_ACTION_NAME, REJECTED_ACTION_NAME]),
            ]
        ),
    }


def ensure_server_action(name, model, code):
    Action = env["ir.actions.server"].sudo()  # noqa: F821
    action = Action.search([("name", "=", name), ("model_id", "=", model.id)], limit=1)
    vals = {
        "name": name,
        "model_id": model.id,
        "state": "code",
        "code": code,
    }
    if action:
        updates = {key: value for key, value in vals.items() if action[key] != value}
        if updates:
            action.write(updates)
        return action
    return Action.create(vals)


def main():
    mode = clean(os.environ.get("SYNC_MODE") or "check")
    if mode not in {"check", "write"}:
        raise RuntimeError({"invalid_sync_mode": mode})
    if env.cr.dbname != TARGET_DB:  # noqa: F821
        raise RuntimeError({"database_not_sc_demo": env.cr.dbname})  # noqa: F821

    before = collect_state()
    write_json(ROLLBACK_JSON, {"run_id": RUN_ID, "database": env.cr.dbname, "before": before})  # noqa: F821

    model = env["ir.model"].sudo().search([("model", "=", TARGET_MODEL)], limit=1)  # noqa: F821
    if not model:
        raise RuntimeError({"missing_ir_model": TARGET_MODEL})
    reviewer_group = env.ref("smart_construction_core.group_sc_cap_finance_manager")  # noqa: F821
    approved_code = """
target_model = env.context.get("active_model")
target_ids = env.context.get("active_ids") or ([env.context.get("active_id")] if env.context.get("active_id") else [])
target_records = env[target_model].browse(target_ids).exists() if target_model and target_ids else records
if target_records:
    target_records.action_on_tier_approved()
"""
    rejected_code = """
target_model = env.context.get("active_model")
target_ids = env.context.get("active_ids") or ([env.context.get("active_id")] if env.context.get("active_id") else [])
target_records = env[target_model].browse(target_ids).exists() if target_model and target_ids else records
if target_records:
    target_records.action_on_tier_rejected(reason="审批驳回")
"""

    Definition = env["tier.definition"].sudo()  # noqa: F821
    existing = Definition.search([("model", "=", TARGET_MODEL)])
    created_id = False
    approved_action = None
    rejected_action = None
    if mode == "write":
        if len(existing) > 1:
            raise RuntimeError({"duplicate_active_definition_risk": len(existing)})
        approved_action = ensure_server_action(APPROVED_ACTION_NAME, model, approved_code)
        rejected_action = ensure_server_action(REJECTED_ACTION_NAME, model, rejected_code)
        if not existing:
            definition = Definition.create(
                {
                    "name": DEFINITION_NAME,
                    "model_id": model.id,
                    "review_type": "group",
                    "reviewer_group_id": reviewer_group.id,
                    "server_action_id": approved_action.id,
                    "rejected_server_action_id": rejected_action.id,
                    "approve_sequence": False,
                    "notify_on_create": False,
                    "notify_on_pending": False,
                    "notify_on_accepted": False,
                    "notify_on_rejected": False,
                    "active": True,
                }
            )
            created_id = definition.id
        else:
            definition = existing
            definition.write(
                {
                    "name": DEFINITION_NAME,
                    "review_type": "group",
                    "reviewer_group_id": reviewer_group.id,
                    "server_action_id": approved_action.id,
                    "rejected_server_action_id": rejected_action.id,
                    "approve_sequence": False,
                    "notify_on_create": False,
                    "notify_on_pending": False,
                    "notify_on_accepted": False,
                    "notify_on_rejected": False,
                    "active": True,
                }
            )
        env.cr.commit()  # noqa: F821

    after = collect_state()
    result = {
        "run_id": RUN_ID,
        "database": env.cr.dbname,  # noqa: F821
        "mode": mode,
        "before": before,
        "after": after,
        "created_definition_id": created_id,
        "rollback_json": str(ROLLBACK_JSON),
    }
    write_json(OUTPUT_JSON, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


main()
