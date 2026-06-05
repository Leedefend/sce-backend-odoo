#!/usr/bin/env python3
"""Project accepted input invoice tax rows to the formal finance input invoice model."""

from __future__ import annotations

import json
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any


OUTPUT_JSON_NAME = "input_invoice_acceptance_to_formal_projection_sync_result_v1.json"

TARGET_MODEL = "sc.invoice.registration"
TARGET_SOURCE_KIND = "input_invoice_tax"
TARGET_DIRECTION = "input"

JOINT_SOURCE_MODEL = "online_old_scbs:C_JXXP_ZYFPJJD:list892"
JOINT_SOURCE_TABLE = "online_old_scbs:C_JXXP_ZYFPJJD:list892"
JOINT_SOURCE_LEGACY_TABLE = "C_JXXP_ZYFPJJD"
JOINT_SOURCE_DOMAIN = [("legacy_source_table", "=", JOINT_SOURCE_TABLE)]

DIRECT_SOURCE_MODEL = "online_old_scbsly:direct_acceptance:input_tax_report:action932"
DIRECT_SOURCE_TABLE = "SCBSLY_DIRECT_INPUT_TAX_REPORT"
DIRECT_SOURCE_DOMAIN = [
    ("active", "=", True),
    ("source_system", "=", "online_old_scbsly"),
    ("acceptance_label", "=", "进项上报"),
]

ACTION_XMLIDS = [
    "smart_construction_core.action_sc_invoice_input",
    "smart_construction_core.action_sc_invoice_input_report_user",
]
MENU_XMLIDS = [
    "smart_construction_core.menu_sc_invoice_input",
    "smart_construction_core.menu_sc_invoice_input_report_user",
]
VIEW_NAME = "accepted.input.invoice.tax.formal.tree"
VIEW_LABEL = "进项发票"

VISIBLE_LABELS = [
    "口径",
    "状态",
    "单据编号",
    "项目名称",
    "发票开具日期",
    "受票单位",
    "开票单位",
    "实际开票单位",
    "价税合计",
    "税额",
    "不含税金额",
    "发票号码",
    "数量",
    "税率",
    "发票类型",
    "备注",
    "发票备注",
    "录入人",
    "附件",
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


def format_amount(value: object) -> str:
    text = clean(value)
    if text:
        return text
    amount = parse_amount(value)
    return "" if amount == 0.0 else f"{amount:.2f}"


def tax_rate_from_amounts(tax_amount: float, amount_no_tax: float) -> str:
    if not amount_no_tax:
        return ""
    rate = tax_amount / amount_no_tax * 100
    if abs(rate - round(rate)) < 0.0001:
        return f"{int(round(rate))}%"
    return f"{rate:.2f}%"


def state_value(value: object) -> str:
    text = clean(value)
    return {"2": "已确认", "1": "审批中", "0": "草稿"}.get(text, text)


def joint_invoice_note(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    match = re.search(r"(?:^|;\s*)invoice_note=(.*)$", text)
    if match:
        return clean(match.group(1))
    if text.startswith("SCBS55 old visible surface mirror:"):
        return ""
    return text


def joint_attachment_display(note: object, attachment_ref: object) -> str:
    ref = clean(attachment_ref)
    note_text = clean(note)
    match = re.search(r"(?:^|;\s*)attachment=([^;]*)", note_text)
    label = clean(match.group(1)) if match else ""
    if re.match(r"^[0-9a-f]{32}$", label):
        label = ""
    if label and ref:
        return f"{label} | legacy-file-id://{ref}"
    if label:
        return label
    if ref:
        return f"历史附件 | legacy-file-id://{ref}"
    return ""


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path(f"/tmp/input_invoice_projection/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/input_invoice_projection/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_input_invoice_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


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


def legacy_payload(record) -> dict[str, str]:
    env.cr.execute(  # noqa: F821
        """
        SELECT payload
          FROM sc_p1_legacy_visible_alias_payload
         WHERE model = %s
           AND res_id = %s
         LIMIT 1
        """,
        [record._name, record.id],
    )
    row = env.cr.fetchone()  # noqa: F821
    if row and isinstance(row[0], dict):
        return row[0]
    return {}


def field_xml(field_name: str, label: str) -> str:
    return f'  <field name="{field_name}" string="{label}" readonly="1"/>'


def alias_field_name(label: str) -> str:
    return "p1_visible_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def ensure_view_and_actions() -> dict[str, object]:
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

    action_ids = []
    for xmlid in ACTION_XMLIDS:
        action = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if not action:
            raise RuntimeError({"missing_action": xmlid})
        if action.res_model != TARGET_MODEL:
            raise RuntimeError({"unexpected_action_model": action.res_model, "action_xmlid": xmlid})
        action.write(
            {
                "name": VIEW_LABEL,
                "domain": repr([("source_kind", "=", TARGET_SOURCE_KIND), ("direction", "=", TARGET_DIRECTION)]),
                "context": "{'default_source_kind': 'input_invoice_tax', 'default_direction': 'input', 'default_invoice_content': '进项税额上报', 'search_default_group_project': 1}",
            }
        )
        binding = ActionView.search([("act_window_id", "=", action.id), ("view_mode", "=", "tree")], limit=1)
        if binding:
            binding.write({"view_id": view.id, "sequence": 1})
        else:
            ActionView.create({"act_window_id": action.id, "view_id": view.id, "view_mode": "tree", "sequence": 1})
        action_ids.append(int(action.id))

    menu_ids = []
    for xmlid in MENU_XMLIDS:
        menu = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if menu:
            menu.write({"active": True})
            menu_ids.append(int(menu.id))
    return {"view_id": int(view.id), "action_ids": action_ids, "menu_ids": menu_ids, "missing_visible_labels": missing_labels}


def clear_formal_input_invoices() -> int:
    env.cr.execute(  # noqa: F821
        """
        SELECT id
          FROM sc_invoice_registration
         WHERE direction = %s
           AND source_kind = %s
        """,
        [TARGET_DIRECTION, TARGET_SOURCE_KIND],
    )
    ids = [row[0] for row in env.cr.fetchall()]  # noqa: F821
    if not ids:
        return 0
    env.cr.execute(  # noqa: F821
        """
        DELETE FROM sc_invoice_registration_attachment_rel
         WHERE invoice_id = ANY(%s)
        """,
        [ids],
    )
    env.cr.execute(  # noqa: F821
        """
        DELETE FROM sc_p1_legacy_visible_alias_payload
         WHERE model = %s
           AND res_id = ANY(%s)
        """,
        [TARGET_MODEL, ids],
    )
    env.cr.execute(  # noqa: F821
        """
        DELETE FROM sc_invoice_registration
         WHERE id = ANY(%s)
        """,
        [ids],
    )
    return len(ids)


def raw_dict(fact) -> dict[str, Any]:
    try:
        payload = json.loads(fact.raw_payload or "{}")
    except (TypeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def first_project():
    return env["project.project"].sudo().with_context(active_test=False).search([], limit=1)  # noqa: F821


def joint_vals(fact) -> tuple[dict[str, object], dict[str, str]]:
    source_payload = legacy_payload(fact)
    amount_total = float(fact.source_amount or 0.0)
    tax_amount = float(fact.source_tax_amount or 0.0)
    amount_no_tax = float(fact.source_amount_untaxed or 0.0)
    if not amount_no_tax and amount_total:
        amount_no_tax = amount_total - tax_amount
    tax_rate = tax_rate_from_amounts(tax_amount, amount_no_tax)
    attachment_ref = clean(fact.attachment_ref)
    attachment_display = joint_attachment_display(fact.note, attachment_ref)
    invoice_date = fact.document_date or False
    partner_name = clean(fact.legacy_partner_name)
    issue_company = clean(fact.invoice_issue_company or partner_name)
    provider_name = clean(fact.invoice_provider_name or issue_company or partner_name)
    visible_note = joint_invoice_note(fact.note)
    invoice_no = clean(source_payload.get("发票号码") or fact.invoice_no)
    creator_name = clean(source_payload.get("录入人") or fact.creator_name)
    created_time = parse_dt(source_payload.get("录入时间") or fact.created_time)
    payload = {
        "口径": "联营口径",
        "状态": state_value(fact.legacy_state),
        "单据编号": clean(fact.document_no),
        "项目名称": clean(fact.legacy_project_name or fact.project_id.name),
        "发票开具日期": clean(fact.document_date),
        "受票单位": partner_name,
        "开票单位": issue_company,
        "实际开票单位": provider_name,
        "价税合计": format_amount(fact.source_amount),
        "税额": format_amount(fact.source_tax_amount),
        "不含税金额": format_amount(fact.source_amount_untaxed or amount_no_tax),
        "发票号码": invoice_no,
        "发票号": invoice_no,
        "数量": "",
        "税率": clean(tax_rate),
        "发票类型": clean(fact.invoice_type),
        "备注": visible_note,
        "发票备注": visible_note,
        "录入人": creator_name,
        "附件": attachment_display,
        "录入时间": clean(source_payload.get("录入时间") or fact.created_time),
    }
    vals = {
        "source_origin": "legacy",
        "source_kind": TARGET_SOURCE_KIND,
        "direction": TARGET_DIRECTION,
        "state": "legacy_confirmed",
        "project_id": fact.project_id.id or first_project().id,
        "name": clean(fact.document_no or fact.legacy_record_id),
        "document_no": clean(fact.document_no),
        "document_date": invoice_date,
        "invoice_date": invoice_date,
        "recognition_date": invoice_date,
        "invoice_no": invoice_no,
        "invoice_type": clean(fact.invoice_type),
        "tax_rate": clean(tax_rate),
        "invoice_content": "进项税额上报",
        "invoice_company_type": clean(fact.invoice_company_type),
        "invoice_issue_company": issue_company,
        "invoice_provider_name": provider_name,
        "push_result": clean(fact.push_result),
        "kingdee_document_no": clean(fact.kingdee_document_no),
        "amount_no_tax": amount_no_tax,
        "tax_amount": tax_amount,
        "amount_total": amount_total,
        "legacy_visible_data_type": "联营口径",
        "legacy_visible_project_name": clean(fact.legacy_project_name or fact.project_id.name),
        "legacy_visible_partner_name": partner_name,
        "legacy_visible_current_invoice_amount": clean(fact.source_amount),
        "legacy_visible_tax_rate": clean(tax_rate),
        "legacy_visible_invoice_no": invoice_no,
        "legacy_visible_invoice_type": clean(fact.invoice_type),
        "legacy_visible_invoice_issue_company": issue_company,
        "legacy_source_model": JOINT_SOURCE_MODEL,
        "legacy_source_table": JOINT_SOURCE_TABLE,
        "legacy_record_id": clean(fact.legacy_record_id),
        "legacy_document_state": clean(fact.legacy_state),
        "legacy_partner_id": clean(fact.legacy_partner_id),
        "legacy_partner_name": partner_name,
        "legacy_partner_tax_no": clean(fact.legacy_partner_tax_no),
        "legacy_attachment_ref": attachment_ref,
        "creator_legacy_user_id": clean(fact.creator_legacy_user_id),
        "creator_name": creator_name,
        "created_time": created_time or fact.created_time or False,
        "note": visible_note,
    }
    return vals, payload


def direct_vals(fact) -> tuple[dict[str, object], dict[str, str]]:
    raw = raw_dict(fact)
    document_no = clean(fact.legacy_visible_02 or fact.document_no or raw.get("DJBH") or fact.legacy_record_id)
    invoice_date = parse_date(fact.legacy_visible_04 or raw.get("FPKJRQ") or fact.document_date)
    amount_total = parse_amount(fact.legacy_visible_08 or fact.amount_total or raw.get("JSHJ"))
    tax_amount = parse_amount(fact.legacy_visible_09 or raw.get("SE"))
    amount_no_tax = parse_amount(fact.legacy_visible_10 or raw.get("BHSJE"))
    if not amount_no_tax and amount_total:
        amount_no_tax = amount_total - tax_amount
    issue_company = clean(fact.legacy_visible_06 or raw.get("KPDW"))
    actual_issue_company = clean(fact.legacy_visible_07 or raw.get("SJKPDW") or issue_company)
    partner_name = clean(fact.legacy_visible_05 or fact.partner_name or raw.get("SPDW"))
    attachment_ref = clean(fact.legacy_visible_17 or fact.attachment_ref or raw.get("FJ"))
    created_time = parse_dt(fact.legacy_visible_18 or fact.created_time or raw.get("LRSJ"))
    project = fact.project_id or first_project()
    payload = {
        "口径": "直营口径",
        "状态": clean(fact.legacy_visible_01 or fact.document_state),
        "单据编号": document_no,
        "项目名称": clean(fact.legacy_visible_03 or fact.project_name or project.name),
        "发票开具日期": clean(fact.legacy_visible_04),
        "受票单位": partner_name,
        "开票单位": issue_company,
        "实际开票单位": actual_issue_company,
        "价税合计": clean(fact.legacy_visible_08),
        "税额": clean(fact.legacy_visible_09),
        "不含税金额": clean(fact.legacy_visible_10),
        "发票号码": clean(fact.legacy_visible_11),
        "数量": clean(fact.legacy_visible_12),
        "税率": clean(fact.legacy_visible_13),
        "发票类型": clean(fact.legacy_visible_14),
        "备注": clean(fact.legacy_visible_15 or fact.note),
        "录入人": clean(fact.legacy_visible_16 or fact.creator_name),
        "附件": attachment_ref,
        "录入时间": clean(fact.legacy_visible_18),
    }
    vals = {
        "source_origin": "legacy",
        "source_kind": TARGET_SOURCE_KIND,
        "direction": TARGET_DIRECTION,
        "state": "legacy_confirmed",
        "project_id": project.id,
        "name": document_no,
        "document_no": document_no,
        "document_date": invoice_date or parse_date(fact.document_date),
        "invoice_date": invoice_date,
        "recognition_date": invoice_date,
        "invoice_no": clean(fact.legacy_visible_11),
        "invoice_type": clean(fact.legacy_visible_14),
        "tax_rate": clean(fact.legacy_visible_13),
        "invoice_content": "进项上报",
        "invoice_issue_company": issue_company,
        "invoice_provider_name": actual_issue_company,
        "amount_no_tax": amount_no_tax,
        "tax_amount": tax_amount,
        "amount_total": amount_total,
        "legacy_visible_data_type": "直营口径",
        "legacy_visible_project_name": payload["项目名称"],
        "legacy_visible_partner_name": partner_name,
        "legacy_visible_current_invoice_amount": payload["价税合计"],
        "legacy_visible_tax_rate": payload["税率"],
        "legacy_visible_invoice_no": payload["发票号码"],
        "legacy_visible_invoice_type": payload["发票类型"],
        "legacy_visible_invoice_issue_company": issue_company,
        "legacy_source_model": DIRECT_SOURCE_MODEL,
        "legacy_source_table": DIRECT_SOURCE_TABLE,
        "legacy_record_id": clean(fact.legacy_record_id or fact.id),
        "legacy_document_state": clean(fact.legacy_visible_01 or fact.document_state),
        "legacy_partner_name": partner_name,
        "legacy_attachment_ref": attachment_ref,
        "creator_legacy_user_id": clean(fact.creator_legacy_user_id),
        "creator_name": payload["录入人"],
        "created_time": created_time,
        "note": payload["备注"],
    }
    return vals, payload


def create_records(records, mapper) -> tuple[int, int, list[dict[str, object]]]:
    Invoice = env[TARGET_MODEL].sudo().with_context(active_test=False)  # noqa: F821
    created = 0
    skipped = 0
    samples = []
    for fact in records:
        vals, payload = mapper(fact)
        if not vals.get("project_id"):
            skipped += 1
            continue
        record = Invoice.create(vals)
        write_payload(record, payload)
        created += 1
        if len(samples) < 3:
            samples.append(
                {
                    "id": record.id,
                    "document_no": record.document_no,
                    "project": record.legacy_visible_project_name,
                    "amount_total": record.amount_total,
                    "tax_amount": record.tax_amount,
                    "attachment": record.legacy_attachment_ref,
                    "source": record.legacy_source_model,
                }
            )
    return created, skipped, samples


ensure_allowed_db()
ensure_payload_table()
view_result = ensure_view_and_actions()

JointFact = env["sc.legacy.invoice.tax.fact"].sudo().with_context(active_test=False)  # noqa: F821
DirectFact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
Invoice = env[TARGET_MODEL].sudo().with_context(active_test=False)  # noqa: F821

joint_records = JointFact.search(JOINT_SOURCE_DOMAIN, order="document_date, id")
direct_records = DirectFact.search(DIRECT_SOURCE_DOMAIN, order="row_index, id")
old_count = Invoice.search_count([("direction", "=", TARGET_DIRECTION), ("source_kind", "=", TARGET_SOURCE_KIND)])
deleted = clear_formal_input_invoices()

joint_created, joint_skipped, joint_samples = create_records(joint_records, joint_vals)
direct_created, direct_skipped, direct_samples = create_records(direct_records, direct_vals)

env.cr.execute(  # noqa: F821
    """
    SELECT legacy_source_model, count(*)
      FROM sc_invoice_registration
     WHERE direction = %s
       AND source_kind = %s
     GROUP BY legacy_source_model
     ORDER BY legacy_source_model
    """,
    [TARGET_DIRECTION, TARGET_SOURCE_KIND],
)
source_counts = dict(env.cr.fetchall())  # noqa: F821

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "input_invoice_acceptance_to_formal_projection_sync",
    "target_model": TARGET_MODEL,
    "target_action_ids": view_result["action_ids"],
    "target_menu_ids": view_result["menu_ids"],
    "target_view_id": view_result["view_id"],
    "old_formal_input_invoice_count": old_count,
    "deleted_formal_input_invoice_count": deleted,
    "joint_source_count": len(joint_records),
    "joint_created": joint_created,
    "joint_skipped": joint_skipped,
    "direct_source_count": len(direct_records),
    "direct_created": direct_created,
    "direct_skipped": direct_skipped,
    "target_count": Invoice.search_count([("direction", "=", TARGET_DIRECTION), ("source_kind", "=", TARGET_SOURCE_KIND)]),
    "target_with_attachment": Invoice.search_count(
        [("direction", "=", TARGET_DIRECTION), ("source_kind", "=", TARGET_SOURCE_KIND), ("legacy_attachment_ref", "!=", False)]
    ),
    "source_counts": source_counts,
    "joint_samples": joint_samples,
    "direct_samples": direct_samples,
    "labels": VISIBLE_LABELS,
    "missing_visible_labels": view_result["missing_visible_labels"],
}
write_json(artifact_root() / OUTPUT_JSON_NAME, payload)
print("INPUT_INVOICE_ACCEPTANCE_TO_FORMAL_PROJECTION_SYNC=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
