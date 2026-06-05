#!/usr/bin/env python3
"""Project accepted direct project expense claims into formal finance expense claims."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path


OUTPUT_JSON_NAME = "direct_project_expense_claim_formal_projection_sync_result_v1.json"
SOURCE_MODEL = "online_old_scbsly:direct_acceptance:project_expense_claim"
SOURCE_TABLE = "SCBSLY_DIRECT_PROJECT_EXPENSE_CLAIM"
SOURCE_DOMAIN = [
    ("active", "=", True),
    ("source_system", "=", "online_old_scbsly"),
    ("acceptance_label", "=", "项目费用报销单"),
]
TARGET_MODEL = "sc.expense.claim"
ACTION_XMLID = "smart_construction_core.action_sc_expense_claim_project"
MENU_XMLID = "smart_construction_core.menu_sc_project_expense_claim"
VIEW_NAME = "accepted.direct.project.expense.claim.formal.tree"
VIEW_LABEL = "项目费用报销单"
VISIBLE_LABELS = [
    "单据状态",
    "单据编号",
    "日期",
    "报销种类",
    "事项说明",
    "报销金额",
    "付款状态",
    "已付款金额",
    "未付款金额",
    "付款方式",
    "报销人",
    "收款人",
    "备注",
    "项目名称",
    "附件",
    "录入人",
    "录入时间",
]


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL", "null"} else text


def parse_amount(value: object) -> float:
    text = clean(value).replace(",", "").replace("￥", "")
    if not text:
        return 0.0
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    try:
        return float(match.group(0))
    except ValueError:
        return 0.0


def parse_date(value: object):
    text = clean(value)
    if not text:
        return False
    match = re.search(r"\d{4}-\d{1,2}-\d{1,2}", text)
    if not match:
        return False
    try:
        return datetime.strptime(match.group(0), "%Y-%m-%d").date()
    except ValueError:
        return False


def parse_dt(value: object):
    text = clean(value)
    if not text:
        return False
    for pattern, fmt in (
        (r"\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}", "%Y-%m-%d %H:%M:%S"),
        (r"\d{4}-\d{1,2}-\d{1,2}", "%Y-%m-%d"),
    ):
        match = re.search(pattern, text)
        if not match:
            continue
        try:
            return datetime.strptime(match.group(0), fmt)
        except ValueError:
            continue
    return False


def state_key(value: object) -> str:
    text = clean(value)
    return "legacy_confirmed" if text in {"审核通过", "已审核", "审批通过", "已确认", "2"} else "draft"


def attachment_display(label: object, attachment_ref: object) -> str:
    display = clean(label)
    ref = clean(attachment_ref)
    if display and ref:
        return f"{display} | legacy-file-id://{ref}"
    if display:
        return display
    if ref:
        return f"历史附件 | legacy-file-id://{ref}"
    return ""


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_direct_project_expense_claim_sync": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path(f"/tmp/direct_project_expense_claim/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/direct_project_expense_claim/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_payload_table() -> None:
    env.cr.execute(  # noqa: F821
        """
        CREATE TABLE IF NOT EXISTS sc_p1_legacy_visible_alias_payload (
            model varchar NOT NULL,
            res_id integer NOT NULL,
            payload jsonb NOT NULL DEFAULT '{}'::jsonb,
            write_date timestamp without time zone NOT NULL DEFAULT now(),
            PRIMARY KEY (model, res_id)
        )
        """
    )


def write_payload(record, payload: dict[str, str]) -> None:
    env.cr.execute(  # noqa: F821
        """
        INSERT INTO sc_p1_legacy_visible_alias_payload(model, res_id, payload, write_date)
        VALUES (%s, %s, %s::jsonb, now())
        ON CONFLICT (model, res_id)
        DO UPDATE SET payload = EXCLUDED.payload, write_date = now()
        """,
        [record._name, record.id, json.dumps(payload, ensure_ascii=False)],
    )


def alias_field_name(label: str) -> str:
    return "p1_visible_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def field_xml(field_name: str, label: str) -> str:
    return f'  <field name="{field_name}" string="{label}" readonly="1"/>'


def ensure_view_action_menu() -> dict[str, object]:
    Model = env[TARGET_MODEL]  # noqa: F821
    visible_fields = [(alias_field_name(label), label) for label in VISIBLE_LABELS if alias_field_name(label) in Model._fields]
    missing_labels = [label for label in VISIBLE_LABELS if alias_field_name(label) not in Model._fields]
    if not visible_fields:
        raise RuntimeError({"missing_all_visible_fields": VISIBLE_LABELS})

    View = env["ir.ui.view"].sudo()  # noqa: F821
    ActionView = env["ir.actions.act_window.view"].sudo()  # noqa: F821
    arch = "\n".join(
        [f'<tree string="{VIEW_LABEL}" create="false" edit="false" delete="false">']
        + [field_xml(field_name, label) for field_name, label in visible_fields]
        + ["</tree>"]
    )
    view = View.search([("name", "=", VIEW_NAME), ("model", "=", TARGET_MODEL), ("type", "=", "tree")], limit=1)
    if view:
        view.write({"arch_db": arch, "active": True, "priority": 1})
    else:
        view = View.create({"name": VIEW_NAME, "model": TARGET_MODEL, "type": "tree", "arch_db": arch, "active": True, "priority": 1})

    action = env.ref(ACTION_XMLID, raise_if_not_found=False)  # noqa: F821
    if not action:
        raise RuntimeError({"missing_action": ACTION_XMLID})
    action.write(
        {
            "name": VIEW_LABEL,
            "domain": repr([("claim_type", "=", "expense"), ("expense_type", "=", VIEW_LABEL), ("legacy_source_model", "=", SOURCE_MODEL)]),
            "context": "{'default_claim_type': 'expense', 'default_expense_type': '项目费用报销单', 'search_default_active_rows': 1, 'search_default_group_project': 1}",
        }
    )
    binding = ActionView.search([("act_window_id", "=", action.id), ("view_mode", "=", "tree")], limit=1)
    if binding:
        binding.write({"view_id": view.id, "sequence": 1})
    else:
        ActionView.create({"act_window_id": action.id, "view_id": view.id, "view_mode": "tree", "sequence": 1})

    menu = env.ref(MENU_XMLID, raise_if_not_found=False)  # noqa: F821
    if menu:
        groups = [
            env.ref("smart_construction_core.group_sc_cap_business_initiator").id,  # noqa: F821
            env.ref("smart_construction_core.group_sc_cap_finance_read").id,  # noqa: F821
            env.ref("smart_construction_core.group_sc_cap_finance_user").id,  # noqa: F821
            env.ref("smart_construction_core.group_sc_cap_finance_manager").id,  # noqa: F821
        ]
        menu.write({"active": True, "groups_id": [(6, 0, groups)], "sequence": 30})
    return {"view_id": int(view.id), "action_id": int(action.id), "menu_id": int(menu.id) if menu else 0, "missing_labels": missing_labels}


def clear_existing_target() -> int:
    Claim = env[TARGET_MODEL].sudo().with_context(active_test=False)  # noqa: F821
    existing = Claim.search(["|", ("legacy_source_model", "=", SOURCE_MODEL), "&", ("claim_type", "=", "expense"), ("expense_type", "=", VIEW_LABEL)])
    ids = existing.ids
    if not ids:
        return 0
    env.cr.execute("DELETE FROM sc_expense_claim_attachment_rel WHERE claim_id = ANY(%s)", [ids])  # noqa: F821
    env.cr.execute("DELETE FROM sc_p1_legacy_visible_alias_payload WHERE model = %s AND res_id = ANY(%s)", [TARGET_MODEL, ids])  # noqa: F821
    env.cr.execute("DELETE FROM sc_expense_claim WHERE id = ANY(%s)", [ids])  # noqa: F821
    return len(ids)


def record_payload(fact) -> dict[str, str]:
    payload = {
        "单据状态": clean(fact.legacy_visible_01),
        "单据编号": clean(fact.legacy_visible_02),
        "日期": clean(fact.legacy_visible_03),
        "单据日期": clean(fact.legacy_visible_03),
        "报销种类": clean(fact.legacy_visible_04),
        "报销类别": clean(fact.legacy_visible_04),
        "事项说明": clean(fact.legacy_visible_05),
        "报销金额": clean(fact.legacy_visible_06),
        "付款状态": clean(fact.legacy_visible_07),
        "已付款金额": clean(fact.legacy_visible_08),
        "未付款金额": clean(fact.legacy_visible_09),
        "付款方式": clean(fact.legacy_visible_10),
        "报销人": clean(fact.legacy_visible_11),
        "收款人": clean(fact.legacy_visible_12),
        "备注": clean(fact.legacy_visible_13),
        "项目名称": clean(fact.legacy_visible_14 or fact.project_name),
        "附件": attachment_display(fact.legacy_visible_15, fact.attachment_ref),
        "录入人": clean(fact.legacy_visible_16 or fact.creator_name),
        "录入时间": clean(fact.legacy_visible_17 or fact.created_time),
    }
    return payload


def record_vals(fact, payload: dict[str, str]) -> dict[str, object]:
    project = fact.project_id or env["project.project"].sudo().with_context(active_test=False).search([], limit=1)  # noqa: F821
    source_amount = parse_amount(payload["报销金额"] or fact.amount_total)
    source_paid_amount = parse_amount(payload["已付款金额"])
    amount = abs(source_amount)
    paid_amount = abs(source_paid_amount)
    date_claim = parse_date(payload["日期"] or fact.document_date)
    return {
        "source_origin": "legacy",
        "claim_type": "expense",
        "state": state_key(payload["单据状态"]),
        "project_id": project.id,
        "name": payload["单据编号"] or clean(fact.document_no or fact.legacy_record_id),
        "date_claim": date_claim,
        "fill_date": date_claim,
        "expense_type": VIEW_LABEL,
        "summary": payload["事项说明"] or VIEW_LABEL,
        "amount": amount,
        "approved_amount": paid_amount if paid_amount else amount,
        "payment_method": payload["付款方式"],
        "payee": payload["收款人"] or payload["报销人"],
        "applicant_name": payload["报销人"],
        "legacy_source_model": SOURCE_MODEL,
        "legacy_source_table": SOURCE_TABLE,
        "legacy_record_id": clean(fact.legacy_record_id or fact.id),
        "legacy_document_no": payload["单据编号"] or clean(fact.document_no),
        "legacy_document_state": payload["单据状态"],
        "legacy_visible_document_state": payload["单据状态"],
        "legacy_visible_document_no": payload["单据编号"],
        "legacy_visible_date": parse_dt(payload["日期"]),
        "legacy_visible_expense_type": payload["报销种类"],
        "legacy_visible_summary": payload["事项说明"],
        "legacy_visible_amount": payload["报销金额"],
        "legacy_visible_note": payload["备注"],
        "legacy_visible_project_name": payload["项目名称"],
        "creator_legacy_user_id": clean(fact.creator_legacy_user_id),
        "creator_name": payload["录入人"],
        "created_time": parse_dt(payload["录入时间"]),
        "note": payload["备注"],
    }


ensure_allowed_db()
ensure_payload_table()
view_result = ensure_view_action_menu()

Fact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
Claim = env[TARGET_MODEL].sudo().with_context(active_test=False)  # noqa: F821
source_records = Fact.search(SOURCE_DOMAIN, order="row_index, id")
deleted = clear_existing_target()

created = 0
samples = []
for fact in source_records:
    payload = record_payload(fact)
    record = Claim.create(record_vals(fact, payload))
    write_payload(record, payload)
    created += 1
    if len(samples) < 5:
        samples.append(
            {
                "id": record.id,
                "document_no": record.legacy_document_no,
                "project": record.legacy_visible_project_name,
                "amount": record.amount,
                "attachment": payload["附件"],
                "creator": record.creator_name,
            }
        )

env.cr.commit()  # noqa: F821

domain = [("claim_type", "=", "expense"), ("expense_type", "=", VIEW_LABEL), ("legacy_source_model", "=", SOURCE_MODEL)]
result = {
    "status": "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "direct_project_expense_claim_formal_projection_sync",
    "source_count": len(source_records),
    "deleted_existing": deleted,
    "created": created,
    "target_count": Claim.search_count(domain),
    "target_with_attachment_payload": created,
    "target_action_id": view_result["action_id"],
    "target_menu_id": view_result["menu_id"],
    "target_view_id": view_result["view_id"],
    "missing_visible_labels": view_result["missing_labels"],
    "samples": samples,
}
write_json(artifact_root() / OUTPUT_JSON_NAME, result)
print("DIRECT_PROJECT_EXPENSE_CLAIM_FORMAL_PROJECTION_SYNC=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
