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
    # 基础资料 pages are mirrored from the live old-system page grain. The
    # canonical business entity map only contains deduplicated mapping rows.
    10: [("legacy_company_id", "=", "online_old_scbs:T_Base_CooperatCompany:list853")],
    20: [("legacy_company_id", "=", "online_old_scbs:T_Base_CooperatCompany:list854")],
    30: [("legacy_contract_id", "!=", False), ("legacy_income_surface_visible", "=", True)],
    40: [("legacy_source_table", "=", "online_old_scbs:SGZL_RZRJ:list856")],
    50: [("legacy_source_table", "=", "online_old_scbs:BGGL_HBZJ_XZD_QJXJSPB:list857")],
    60: [("legacy_source_table", "=", "online_old_scbs:BGGL_XZD_YZSYSPB:list858")],
    80: [("source_table", "=", "online_old_scbs:BASE_SYSTEM_USER:list859")],
    90: [("legacy_source_table", "=", "online_old_scbs:D_SCBSJS_BGGL_XZ_SBRY:list860")],
    100: [("legacy_source_table", "=", "online_old_scbs:BGGL_XZ_JXDJ_ZB:list861")],
    110: [("legacy_source_table", "=", "online_old_scbs:BGGL_XZ_GZ:list862")],
    120: [("legacy_source_table", "=", "online_old_scbs:BGGL_XZ_BZ:list863")],
    140: [("fact_type", "=", "certificate_registration")],
    150: [("legacy_source_table", "=", "online_old_scbs:ZJGL_ZSJYGL:list865")],
    160: [("legacy_fact_model", "=", "online_old_scbs:P_ZTB_GCBMGL:list866")],
    170: [("legacy_source_table", "=", "online_old_scbs:BGGL_ZTBJHT_TBBM_TBBMFSQ:list895")],
    180: [("bid_id.legacy_fact_model", "=", "online_old_scbs:ZJGL_BZJGL_Branch_SBZJDJ:list868")],
    190: [("bid_id.legacy_fact_model", "=", "online_old_scbs:ZJGL_BZJGL_Branch_SBZJTH:list869")],
    200: [("bid_id.legacy_fact_model", "=", "online_old_scbs:ZJGL_BZJGL_Pay_FBZJ:list870")],
    210: [("bid_id.legacy_fact_model", "=", "online_old_scbs:ZJGL_BZJGL_Pay_FBZJTH:list871")],
    220: [("legacy_source_model", "=", "online_old_scbs:BGGL_JHK_JKSQ:list872")],
    230: [("legacy_source_model", "=", "online_old_scbs:BGGL_JHK_HKDJ:list873")],
    240: [("legacy_source_model", "=", "online_old_scbs:CWGL_FYBX:list874")],
    250: [("legacy_source_model", "=", "online_old_scbs:C_CWSFK_GSCWSR:list875")],
    260: [("legacy_source_model", "=", "online_old_scbs:C_CWSFK_GSCWZC:list876")],
    270: [("legacy_source_model", "=", "online_old_scbs:ZJGL_ZCDFSZ_FXJK_HK:list896")],
    280: [("legacy_source_model", "=", "online_old_scbs:ZJGL_ZCDFSZ_FXJK_JK:list878")],
    # 支付申请 is the old C_ZFSQGL list. Exclude blank-source residual rows and
    # T_FK_Supplier actual-payment rows so the browser count matches old SCBS.
    290: [("legacy_source_table", "=", "C_ZFSQGL")],
    300: [("legacy_source_model", "=", "online_old_scbs:C_ZFSQGL_KKD:list880")],
    # 往来单位付款 is mirrored from the live old-system T_FK_SUPPLIER list,
    # because prior fact imports use a different row grain than the old page.
    310: [("legacy_source_model", "=", "online_old_scbs:T_FK_SUPPLIER:list881")],
    320: [("legacy_source_model", "=", "online_old_scbs:C_FKGL_ZHJZJWL:list882")],
    330: [("legacy_source_model", "=", "online_old_scbs:T_KK_SJDJB:list897")],
    340: [("legacy_source_model", "=", "online_old_scbs:T_KK_SJTHB:list898")],
    350: [("legacy_header_id", "like", "online_old_scbs:ZJGL_SZQR_DKQRB:list885:%")],
    360: [("source_table", "=", "online_old_scbs:D_SCBSJS_ZJGL_ZJSZ_ZJRBB:list886")],
    370: [("legacy_source_model", "=", "online_old_scbs:ZJGL_ZJSZ_DKGL_DKDJ:list887")],
    380: [("legacy_source_model", "=", "online_old_scbs:ZJGL_ZJSZ_DKGL_HKDJ:list888")],
    390: [("legacy_source_model", "=", "online_old_scbs:C_JXXP_KJFPSQ:list889")],
    400: [("legacy_source_model", "=", "online_old_scbs:C_JXXP_XXKPDJ:list890")],
    410: [("legacy_source_model", "=", "online_old_scbs:C_JXXP_YJSKDJ:list891")],
    420: [("legacy_source_table", "=", "online_old_scbs:C_JXXP_ZYFPJJD:list892")],
    430: [("legacy_source_model", "=", "online_old_scbs:C_JXXP_DKDJ_New:list893")],
    440: [("source_table", "=", "online_old_scbs:ZJGL_WJZ_WJZDJB:list894")],
}

TARGET_MODEL_OVERRIDES_BY_SEQUENCE = {
    270: "sc.expense.claim",
    330: "sc.expense.claim",
    340: "sc.expense.claim",
}

LIST_CONTRACT_LABEL_OVERRIDES_BY_SEQUENCE = {
    140: ["证照名称", "编号", "持有人", "有效期", "附件"],
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
            '  <field name="%s" string="%s" readonly="1"/>'
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
    has_domain_override = record.priority_sequence in DOMAIN_OVERRIDES_BY_SEQUENCE
    domain_override = DOMAIN_OVERRIDES_BY_SEQUENCE.get(record.priority_sequence)
    domain = repr(domain_override) if has_domain_override else base_action.domain or "[]"
    source_tables = [
        item.strip()
        for item in re.split(r"[;,，；]", str(record.legacy_source_tables or ""))
        if item.strip()
    ]
    model_fields = env[record.target_model]._fields  # noqa: F821
    if has_domain_override:
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
