#!/usr/bin/env python3
"""Generate action-specific SCBS55 tree views from the legacy visible contract.

This is intentionally action-scoped instead of model-scoped: several SCBS55
menus share the same Odoo carrier model but require different old-system column
orders. The script expects the p1_visible_* alias fields to be present on each
target model.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from xml.sax.saxutils import escape


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
OUTPUT_JSON_NAME = "scbs_55_user_visible_surface_action_tree_alias_write_result_v1.json"

DOMAIN_OVERRIDES_BY_SEQUENCE = {
    # These user-facing menus already have runtime projections, but the
    # historical plan records keep the old SQL table names. Use the runtime
    # carrier's stable classification so the menu does not appear empty.
    40: [("fact_type", "=", "company_document_archive")],
    100: [("fact_type", "=", "social_registration")],
    110: [("fact_type", "=", "salary_registration")],
    120: [("fact_type", "=", "subsidy")],
    150: [("fact_type", "=", "document_borrow")],
    270: [("claim_type", "=", "project_company_repay"), ("expense_type", "=", "还款登记")],
    330: [("claim_type", "=", "expense"), ("expense_type", "=", "扣款实缴登记")],
    340: [("claim_type", "=", "deduction_refund"), ("expense_type", "=", "扣款实缴退回")],
    # The legacy prepaid-tax menu is a detail-line surface. Exclude blank
    # child rows imported only to preserve source identity; users need rows
    # with a real tax/payment amount.
    410: [
        ("source_kind", "=", "prepaid_tax"),
        ("direction", "=", "prepaid"),
        ("amount_total", "!=", 0),
    ],
}

TARGET_MODEL_OVERRIDES_BY_SEQUENCE = {
    270: "sc.expense.claim",
    330: "sc.expense.claim",
    340: "sc.expense.claim",
}

LIST_CONTRACT_LABEL_OVERRIDES_BY_SEQUENCE = {
    # Source: old prepaid-tax export header
    # /home/odoo/workspace/partner_import_source/3/+预缴税款639153288551406250.xlsx
    410: [
        "状态",
        "项目名称",
        "单据编号",
        "受票方名称",
        "交税类型",
        "金额",
        "不含税金额",
        "税额",
        "发票开具日期",
        "预缴税款日期",
        "完税凭证号码",
        "附件",
        "数据类型",
        "录入人",
    ],
}


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_55_visible_surface/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_55_visible_surface/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def alias_field_name(label: str) -> str:
    return "p1_visible_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def slug(value: str) -> str:
    raw = re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_").lower()
    return raw[:48] or hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def contract_labels(record) -> list[str]:
    labels: list[str] = []
    for item in record.list_field_contract or []:
        if not isinstance(item, dict):
            continue
        label = str(item.get("legacy_label") or "").strip()
        if label:
            labels.append(label)
    return labels


def list_field_contract_from_labels(labels: list[str]) -> list[dict[str, object]]:
    return [
        {
            "legacy_label": label,
            "target_field": alias_field_name(label),
            "sequence": index * 10,
        }
        for index, label in enumerate(labels, start=1)
    ]


def tree_arch(record, labels: list[str]) -> str:
    parts = [
        '<tree string="%s" create="false" edit="false" delete="false">'
        % escape(record.legacy_menu_name or "SCBS55")
    ]
    for label in labels:
        escaped = escape(label)
        parts.append(
            '  <field name="%s" string="%s" optional="show" readonly="1"/>'
            % (alias_field_name(label), escaped)
        )
    parts.append("</tree>")
    return "\n".join(parts)


ensure_allowed_db()
artifact_dir = artifact_root()
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
View = env["ir.ui.view"].sudo()  # noqa: F821
Action = env["ir.actions.act_window"].sudo()  # noqa: F821
ActionView = env["ir.actions.act_window.view"].sudo()  # noqa: F821
Menu = env["ir.ui.menu"].sudo().with_context(active_test=False)  # noqa: F821

rows = Plan.search([("source_document", "=", SOURCE_DOCUMENT)], order="priority_sequence")
updated = 0
skipped: list[dict[str, object]] = []
missing_alias_fields: list[dict[str, object]] = []
view_rows: list[dict[str, object]] = []


def acceptance_menu(record):
    menus = Menu.search([("name", "=", record.legacy_menu_name)])
    for menu in menus:
        if "用户核对菜单" in (menu.complete_name or ""):
            return menu
    return Menu.browse()


def action_for_record(record, base_action, view):
    action_name = "SCBS55 %03d %s" % (record.priority_sequence, record.legacy_menu_name)
    action = Action.search([("name", "=", action_name), ("res_model", "=", record.target_model)], limit=1)
    domain_override = DOMAIN_OVERRIDES_BY_SEQUENCE.get(record.priority_sequence)
    domain = repr(domain_override) if domain_override else base_action.domain or "[]"
    source_tables = [
        item.strip()
        for item in re.split(r"[;,，；]", str(record.legacy_source_tables or ""))
        if item.strip()
    ]
    model_fields = env[record.target_model]._fields  # noqa: F821
    if domain_override:
        domain = repr(domain_override)
    elif source_tables and "legacy_source_table" in model_fields:
        domain = repr([("legacy_source_table", "in", source_tables)])
    elif source_tables and "source_table" in model_fields:
        domain = repr([("source_table", "in", source_tables)])
    values = {
        "name": action_name,
        "res_model": record.target_model,
        "view_mode": base_action.view_mode or "tree,form",
        "view_id": view.id,
        "domain": domain,
        "context": base_action.context or "{}",
        "search_view_id": base_action.search_view_id.id if base_action.search_view_id else False,
        "target": base_action.target or "current",
        "help": base_action.help or False,
    }
    if action:
        action.write(values)
    else:
        action = Action.create(values)
    action_view = ActionView.search([("act_window_id", "=", action.id), ("view_mode", "=", "tree")], limit=1)
    action_view_values = {
        "sequence": 1,
        "view_id": view.id,
        "act_window_id": action.id,
        "view_mode": "tree",
    }
    if action_view:
        action_view.write(action_view_values)
    else:
        ActionView.create(action_view_values)
    return action

for record in rows:
    target_model_override = TARGET_MODEL_OVERRIDES_BY_SEQUENCE.get(record.priority_sequence)
    if target_model_override and record.target_model != target_model_override:
        ir_model = env["ir.model"].sudo().search([("model", "=", target_model_override)], limit=1)  # noqa: F821
        record.write(
            {
                "target_model": target_model_override,
                "target_model_id": ir_model.id or False,
                "current_round_action": "specialized_carrier_exists",
                "target_iteration": "user_page_aligned_v3",
            }
        )
    override_labels = LIST_CONTRACT_LABEL_OVERRIDES_BY_SEQUENCE.get(record.priority_sequence)
    labels = override_labels or contract_labels(record)
    if override_labels:
        record.write(
            {
                "list_field_contract": list_field_contract_from_labels(labels),
                "target_iteration": "user_page_aligned_v4",
            }
        )
    action = record.target_action_id
    model = str(record.target_model or "")
    if not labels:
        skipped.append({"seq": record.priority_sequence, "name": record.legacy_menu_name, "reason": "empty_contract"})
        continue
    if not action or not model or model not in env:  # noqa: F821
        skipped.append(
            {
                "seq": record.priority_sequence,
                "name": record.legacy_menu_name,
                "reason": "missing_action_or_model",
                "model": model,
                "action_id": int(action.id or 0),
            }
        )
        continue

    missing = [label for label in labels if alias_field_name(label) not in env[model]._fields]  # noqa: F821
    if missing:
        missing_alias_fields.append(
            {
                "seq": record.priority_sequence,
                "name": record.legacy_menu_name,
                "model": model,
                "missing_labels": missing,
            }
        )
        continue

    view_name = "scbs55.user.visible.%03d.%s.tree" % (record.priority_sequence, slug(record.legacy_menu_name or "menu"))
    arch = tree_arch(record, labels)
    view = View.search([("name", "=", view_name), ("model", "=", model), ("type", "=", "tree")], limit=1)
    values = {
        "name": view_name,
        "model": model,
        "type": "tree",
        "mode": "primary",
        "priority": 1,
        "arch": arch,
    }
    if view:
        view.write(values)
    else:
        view = View.create(values)

    dedicated_action = action_for_record(record, action, view)
    menu = acceptance_menu(record)
    if menu:
        menu.write({"action": "ir.actions.act_window,%d" % dedicated_action.id})
    record.write(
        {
            "target_action_id": dedicated_action.id,
            "target_view_id": view.id,
            "surface_contract_status": "runtime_spec_landed",
        }
    )
    view_rows.append(
        {
            "seq": record.priority_sequence,
            "name": record.legacy_menu_name,
            "model": model,
            "base_action_id": int(action.id),
            "action_id": int(dedicated_action.id),
            "menu_id": int(menu.id or 0),
            "view_id": int(view.id),
            "field_count": len(labels),
        }
    )
    updated += 1

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS" if not missing_alias_fields and updated > 0 else "FAIL",
    "mode": "scbs_55_user_visible_surface_action_tree_alias_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "row_count": len(rows),
    "updated": updated,
    "skipped": skipped,
    "missing_alias_fields": missing_alias_fields,
    "views": view_rows,
    "db_writes": updated,
    "decision": "scbs55_action_tree_alias_views_landed" if not missing_alias_fields else "STOP_MISSING_ALIAS_FIELDS",
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
print("SCBS_55_USER_VISIBLE_SURFACE_ACTION_TREE_ALIAS_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
