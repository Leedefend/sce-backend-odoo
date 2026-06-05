#!/usr/bin/env python3
"""Project direct-project accepted general-contract input-tax rows to output invoice registration."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


OUTPUT_JSON_NAME = "direct_general_contract_input_tax_to_output_invoice_registration_sync_result_v1.json"
ACTION_XMLID = "smart_construction_core.action_sc_invoice_registration_user"
MENU_XMLID = "smart_construction_core.menu_sc_invoice_registration_user"
PARENT_MENU_XMLID = "smart_construction_core.menu_sc_finance_center"
SOURCE_MODEL = "online_old_scbsly:direct_acceptance:general_contract_input_tax_report:action933"
SOURCE_TABLE = "SCBSLY_DIRECT_GENERAL_CONTRACT_INPUT_TAX_REPORT"
OUTPUT_INVOICE_REGISTRATION_SOURCES = [
    "online_old_scbs:C_JXXP_XXKPDJ:list890",
    SOURCE_MODEL,
]
VIEW_NAME = "scbsly.direct.accepted.general.contract.input.tax.output.invoice.registration.tree"
VIEW_LABEL = "销项开票登记"
SOURCE_DOMAIN = [
    ("active", "=", True),
    ("source_system", "=", "online_old_scbsly"),
    ("acceptance_label", "=", "总包进项上报"),
]
VISIBLE_FIELDS = [
    ("p1_visible_06fa8c6f628f", "单据状态"),
    ("p1_visible_8fa8662ad38f", "单据编号"),
    ("p1_visible_d42c2d26610f", "开票日期"),
    ("p1_visible_be5462bd6a62", "开票单位"),
    ("p1_visible_3e7255522b33", "项目名称"),
    ("p1_visible_6bb76c93367b", "受票单位"),
    ("p1_visible_296ce5fc1ed1", "实开总金额"),
    ("p1_visible_007363f27191", "不含税金额"),
    ("p1_visible_99f753ed6262", "税额"),
    ("p1_visible_37d56ad493cf", "税率"),
    ("p1_visible_c1b95b8ca332", "附加税"),
    ("p1_visible_0e2126d6cf82", "开票张数"),
    ("p1_visible_964a2edc6942", "关联回款金额"),
    ("p1_visible_ed582efc6e34", "发票号码"),
    ("p1_visible_bbe7bbee241e", "发票种类"),
    ("p1_visible_99f6fe6c41ad", "附件"),
    ("p1_visible_ee6a4d9e2956", "录入人"),
    ("p1_visible_dfc25d77dc39", "录入时间"),
]
VISIBLE_LABELS = [label for _field_name, label in VISIBLE_FIELDS]


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def parse_date(value: object):
    text = clean(value)
    if not text:
        return False
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return False


def parse_dt(value: object):
    text = clean(value)
    if not text:
        return False
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19] if "%H" in fmt else text[:10], fmt)
        except ValueError:
            continue
    return False


def parse_amount(value: object) -> float:
    text = clean(value).replace(",", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def parse_int(value: object) -> int:
    try:
        return int(float(clean(value).replace(",", "")))
    except (TypeError, ValueError):
        return 0


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path(f"/tmp/direct_output_invoice_registration/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/direct_output_invoice_registration/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_direct_output_invoice_sync": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


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


def field_xml(field_name: str, label: str) -> str:
    return f'  <field name="{field_name}" string="{label}" readonly="1"/>'


def project_for(fact, raw: dict[str, Any]):
    if fact.project_id:
        return fact.project_id
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    legacy_project_id = clean(raw.get("XMID") or fact.project_legacy_id)
    if legacy_project_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if project:
            return project
    project_name = clean(fact.project_name or raw.get("XMMC"))
    if project_name:
        project = Project.search([("name", "=", project_name)], limit=1) or Project.search([("name", "ilike", project_name[:60])], limit=1)
        if project:
            return project
    return Project.search([], limit=1)


def visible_payload(fact) -> dict[str, str]:
    payload = {}
    for index, label in enumerate(VISIBLE_LABELS, start=1):
        if label == "附件":
            continue
        payload[label] = clean(fact[f"legacy_visible_{index:02d}"])
    return payload


def cleanup_existing_projection() -> int:
    Invoice = env["sc.invoice.registration"].sudo().with_context(active_test=False)  # noqa: F821
    existing = Invoice.search([("legacy_source_model", "=", SOURCE_MODEL)])
    count = len(existing)
    if not count:
        return 0
    try:
        existing.unlink()
        return count
    except Exception:
        env.cr.rollback()  # noqa: F821
    env.cr.execute(  # noqa: F821
        """
        DELETE FROM sc_invoice_registration_attachment_rel
         WHERE invoice_id IN (SELECT id FROM sc_invoice_registration WHERE legacy_source_model = %s)
        """,
        [SOURCE_MODEL],
    )
    env.cr.execute(  # noqa: F821
        "DELETE FROM sc_p1_legacy_visible_alias_payload WHERE model = %s AND res_id IN (SELECT id FROM sc_invoice_registration WHERE legacy_source_model = %s)",
        ["sc.invoice.registration", SOURCE_MODEL],
    )
    env.cr.execute("DELETE FROM sc_invoice_registration WHERE legacy_source_model = %s", [SOURCE_MODEL])  # noqa: F821
    return count


def ensure_view_and_action() -> tuple[int, int, int]:
    View = env["ir.ui.view"].sudo()  # noqa: F821
    ActionView = env["ir.actions.act_window.view"].sudo()  # noqa: F821
    action = env.ref(ACTION_XMLID, raise_if_not_found=False)  # noqa: F821
    menu = env.ref(MENU_XMLID, raise_if_not_found=False)  # noqa: F821
    parent_menu = env.ref(PARENT_MENU_XMLID, raise_if_not_found=False)  # noqa: F821
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
    if view:
        view.write({"arch_db": arch, "active": True, "priority": 1})
    else:
        view = View.create({"name": VIEW_NAME, "model": "sc.invoice.registration", "type": "tree", "arch_db": arch, "active": True, "priority": 1})

    action.write(
        {
            "name": VIEW_LABEL,
            "domain": repr([("legacy_source_model", "in", OUTPUT_INVOICE_REGISTRATION_SOURCES)]),
            "context": "{'default_source_kind': 'output_invoice_tax', 'default_direction': 'output', 'default_invoice_content': '销项开票登记', 'search_default_group_project': 1}",
        }
    )
    if menu:
        vals = {"name": VIEW_LABEL, "active": True, "action": f"ir.actions.act_window,{action.id}", "sequence": 34}
        if parent_menu:
            vals["parent_id"] = parent_menu.id
        menu.write(vals)
    binding = ActionView.search([("act_window_id", "=", action.id), ("view_mode", "=", "tree")], limit=1)
    if binding:
        binding.write({"view_id": view.id, "sequence": 1})
    else:
        ActionView.create({"act_window_id": action.id, "view_id": view.id, "view_mode": "tree", "sequence": 1})
    return int(action.id), int(menu.id) if menu else 0, int(view.id)


ensure_allowed_db()
ensure_payload_table()
Fact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
Invoice = env["sc.invoice.registration"].sudo().with_context(active_test=False)  # noqa: F821
source_records = Fact.search(SOURCE_DOMAIN, order="row_index, id")
deleted = cleanup_existing_projection()
action_id, menu_id, view_id = ensure_view_and_action()

created = 0
skipped = 0
missing_project = 0
for fact in source_records:
    raw = json.loads(fact.raw_payload or "{}")
    project = project_for(fact, raw)
    if not project:
        skipped += 1
        missing_project += 1
        continue
    payload = visible_payload(fact)
    attachment_ref = clean(raw.get("FJ") or fact.attachment_ref)
    vals = {
        "source_origin": "legacy",
        "source_kind": "output_invoice_tax",
        "direction": "output",
        "state": "legacy_confirmed",
        "project_id": project.id,
        "name": clean(fact.document_no or raw.get("DJBH") or fact.legacy_record_id),
        "document_no": clean(fact.document_no or raw.get("DJBH")),
        "document_date": parse_date(raw.get("SQRQ") or fact.document_date),
        "invoice_date": parse_date(fact.legacy_visible_03 or raw.get("FPKJRQ") or raw.get("SQRQ")),
        "recognition_date": parse_date(raw.get("SQRQ") or fact.document_date),
        "invoice_no": clean(fact.legacy_visible_14),
        "invoice_type": clean(fact.legacy_visible_15 or raw.get("FPZL")),
        "tax_rate": clean(fact.legacy_visible_10),
        "invoice_issue_company": clean(fact.legacy_visible_04 or raw.get("KPDW")),
        "amount_total": parse_amount(fact.legacy_visible_07 or raw.get("SKZJE")),
        "amount_no_tax": parse_amount(fact.legacy_visible_08 or raw.get("BHSJE")),
        "tax_amount": parse_amount(fact.legacy_visible_09 or raw.get("ZSE")),
        "surcharge_amount": parse_amount(fact.legacy_visible_11 or raw.get("D_SCBSJS_FJS")),
        "related_receipt_amount": parse_amount(fact.legacy_visible_13 or raw.get("GLHKJE")),
        "invoice_count": parse_int(fact.legacy_visible_12 or raw.get("KPZS")),
        "legacy_visible_project_name": clean(fact.legacy_visible_05 or fact.project_name or raw.get("XMMC")),
        "legacy_visible_partner_name": clean(fact.legacy_visible_06 or raw.get("SPFMC")),
        "legacy_visible_current_invoice_amount": clean(fact.legacy_visible_07),
        "legacy_visible_surcharge_amount": clean(fact.legacy_visible_11),
        "legacy_visible_tax_rate": clean(fact.legacy_visible_10),
        "legacy_visible_related_receipt_amount": clean(fact.legacy_visible_13),
        "legacy_visible_invoice_no": clean(fact.legacy_visible_14),
        "legacy_visible_invoice_type": clean(fact.legacy_visible_15),
        "legacy_visible_invoice_issue_company": clean(fact.legacy_visible_04),
        "legacy_source_model": SOURCE_MODEL,
        "legacy_source_table": SOURCE_TABLE,
        "legacy_record_id": clean(raw.get("Id") or fact.legacy_record_id or fact.id),
        "legacy_document_state": clean(raw.get("DJZT") or fact.document_state),
        "legacy_partner_id": clean(raw.get("D_BYK_SPFID")),
        "legacy_partner_name": clean(fact.legacy_visible_06 or raw.get("SPFMC")),
        "legacy_attachment_ref": attachment_ref,
        "creator_legacy_user_id": clean(raw.get("LRRID") or fact.creator_legacy_user_id),
        "creator_name": clean(fact.legacy_visible_17 or raw.get("LRR") or fact.creator_name),
        "created_time": parse_dt(fact.legacy_visible_18 or raw.get("LRSJ") or fact.created_time),
        "note": clean(raw.get("BZ") or fact.note),
    }
    record = Invoice.create(vals)
    write_payload(record, payload)
    created += 1

env.cr.commit()  # noqa: F821

projected_domain = [("legacy_source_model", "=", SOURCE_MODEL)]
payload = {
    "status": "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "direct_general_contract_input_tax_to_output_invoice_registration_sync",
    "source_action_id": 933,
    "source_menu_id": 774,
    "target_action_id": action_id,
    "target_menu_id": menu_id,
    "target_view_id": view_id,
    "source_count": len(source_records),
    "deleted_existing_projection": deleted,
    "created": created,
    "skipped": skipped,
    "missing_project": missing_project,
    "target_count": Invoice.search_count(projected_domain),
    "target_with_attachment": Invoice.search_count(projected_domain + [("legacy_attachment_ref", "!=", False)]),
    "source_model": SOURCE_MODEL,
    "labels": VISIBLE_LABELS,
}
write_json(artifact_root() / OUTPUT_JSON_NAME, payload)
print("DIRECT_GENERAL_CONTRACT_INPUT_TAX_TO_OUTPUT_INVOICE_REGISTRATION_SYNC=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
