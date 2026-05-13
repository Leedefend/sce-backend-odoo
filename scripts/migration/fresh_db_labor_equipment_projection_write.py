# -*- coding: utf-8 -*-
"""Project reliable labor/equipment legacy facts into professional documents.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_labor_equipment_projection_write.py
"""

import json
import os
from pathlib import Path


def artifact_root():
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or "/mnt/artifacts/migration")
    try:
        root.mkdir(parents=True, exist_ok=True)
        return root
    except Exception:
        fallback = Path("/tmp/history_continuity/%s/adhoc" % env.cr.dbname)  # noqa: F821
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def first(*values):
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def as_date(value):
    if not value:
        return None
    return value.date() if hasattr(value, "date") else value


def amount(value):
    return float(value or 0.0)


def partner_by_name(name):
    text = first(name)
    if not text:
        return False
    Partner = env["res.partner"].sudo()  # noqa: F821
    partner = Partner.search([("name", "=", text)], limit=1)
    if not partner:
        partner = Partner.create({"name": text, "supplier_rank": 1, "company_type": "company"})
    return partner


ARTIFACT_DIR = artifact_root()
RESULT_JSON = ARTIFACT_DIR / "fresh_db_labor_equipment_projection_write_result_v1.json"

LaborFact = env["sc.legacy.labor.subcontract.fact"].sudo().with_context(active_test=False)  # noqa: F821
EquipmentFact = env["sc.legacy.equipment.lease.fact"].sudo().with_context(active_test=False)  # noqa: F821
AttendanceCheckin = env["sc.attendance.checkin"].sudo()  # noqa: F821
LaborSettlement = env["sc.labor.settlement"].sudo()  # noqa: F821
SubcontractRegister = env["sc.subcontract.register"].sudo()  # noqa: F821
SubcontractSettlement = env["sc.subcontract.settlement"].sudo()  # noqa: F821
EquipmentPlan = env["sc.equipment.plan"].sudo()  # noqa: F821
EquipmentUsage = env["sc.equipment.usage"].sudo()  # noqa: F821
EquipmentSettlement = env["sc.equipment.settlement"].sudo()  # noqa: F821
currency_id = env.company.currency_id.id  # noqa: F821
uid = env.uid  # noqa: F821

counts = {
    "attendance_checkin": {"source": 0, "created": 0, "updated": 0, "skipped": 0},
    "labor_settlement": {"source": 0, "created": 0, "updated": 0, "skipped": 0},
    "subcontract_register": {"source": 0, "created": 0, "updated": 0, "skipped": 0},
    "subcontract_settlement": {"source": 0, "created": 0, "updated": 0, "skipped": 0},
    "labor_settlement_cleanup": {"source": 0, "deleted": 0},
    "equipment_plan": {"source": 0, "created": 0, "updated": 0, "skipped": 0},
    "equipment_usage": {"source": 0, "created": 0, "updated": 0, "skipped": 0},
    "equipment_settlement": {"source": 0, "created": 0, "updated": 0, "skipped": 0},
}

labor_usage_facts = LaborFact.search(
    [
        ("active", "=", True),
        ("project_id", "!=", False),
        ("fact_type", "=", "labor_usage"),
    ]
)
counts["attendance_checkin"]["source"] = len(labor_usage_facts)
for fact in labor_usage_facts:
    partner = partner_by_name(fact.partner_name)
    work_content = first(fact.work_scope, fact.work_part, fact.contract_name, fact.document_no, "历史劳务用工")
    vals = {
        "name": first(fact.document_no, "历史考勤-%s" % fact.id),
        "project_id": fact.project_id.id,
        "attendance_date": as_date(fact.document_date or fact.start_date or fact.created_time),
        "labor_team": first(fact.partner_name, fact.department_name, "历史劳务班组"),
        "work_content": work_content,
        "attendance_qty": 1.0,
        "work_hours": 0.0,
        "contractor_id": partner.id if partner else False,
        "recorder_id": uid,
        "state": "confirmed" if fact.state == "legacy_confirmed" else "cancel",
        "note": "\n".join(
            item
            for item in [
                "历史劳务用工转考勤记录",
                "来源类型：%s" % fact.fact_type,
                "来源金额：%s" % amount(fact.amount_total or fact.amount_payable),
                "来源经办：%s" % first(fact.creator_name),
                first(fact.note),
            ]
            if item
        ),
        "legacy_fact_model": fact._name,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": fact.fact_type,
    }
    existing = AttendanceCheckin.search([("legacy_fact_model", "=", fact._name), ("legacy_fact_id", "=", fact.id)], limit=1)
    if existing:
        existing.write(vals)
        counts["attendance_checkin"]["updated"] += 1
    else:
        AttendanceCheckin.create(vals)
        counts["attendance_checkin"]["created"] += 1

labor_facts = LaborFact.search(
    [
        ("active", "=", True),
        ("project_id", "!=", False),
        ("partner_name", "!=", False),
        ("fact_type", "=", "labor_settlement"),
    ]
)
counts["labor_settlement"]["source"] = len(labor_facts)
for fact in labor_facts:
    partner = partner_by_name(fact.partner_name)
    if not partner:
        counts["labor_settlement"]["skipped"] += 1
        continue
    total = amount(fact.amount_settlement or fact.amount_total or fact.amount_payable)
    if total <= 0:
        counts["labor_settlement"]["skipped"] += 1
        continue
    name = first(fact.document_no, fact.contract_no, "历史劳务结算-%s" % fact.id)
    work_content = first(fact.work_scope, fact.work_part, fact.contract_name, fact.document_no, "历史劳务结算")
    qty = 1.0
    tax_rate = amount(fact.tax_rate)
    vals = {
        "name": name,
        "project_id": fact.project_id.id,
        "contractor_id": partner.id,
        "settlement_date": as_date(fact.document_date or fact.end_date or fact.created_time),
        "owner_id": uid,
        "currency_id": currency_id,
        "state": "draft",
        "note": "\n".join(
            item
            for item in [
                "历史劳务/分包结算",
                "来源类型：%s" % fact.fact_type,
                "来源合同：%s" % first(fact.contract_no, fact.contract_name),
                "来源经办：%s" % first(fact.creator_name),
                first(fact.note),
            ]
            if item
        ),
        "legacy_fact_model": fact._name,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": fact.fact_type,
        "line_ids": [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "labor_team": first(fact.partner_name, fact.department_name),
                    "work_content": work_content,
                    "qty": qty,
                    "unit_name": "项",
                    "unit_price": total,
                    "tax_rate": tax_rate,
                    "note": first(fact.work_part, fact.note),
                },
            ),
        ],
    }
    existing = LaborSettlement.search([("legacy_fact_model", "=", fact._name), ("legacy_fact_id", "=", fact.id)], limit=1)
    if existing:
        existing.write(vals)
        counts["labor_settlement"]["updated"] += 1
    else:
        LaborSettlement.create(vals)
        counts["labor_settlement"]["created"] += 1

legacy_subcontract_labor_rows = LaborSettlement.search(
    [("legacy_fact_model", "=", "sc.legacy.labor.subcontract.fact"), ("legacy_fact_type", "=", "subcontract_settlement")]
)
counts["labor_settlement_cleanup"]["source"] = len(legacy_subcontract_labor_rows)
if legacy_subcontract_labor_rows:
    counts["labor_settlement_cleanup"]["deleted"] = len(legacy_subcontract_labor_rows)
    legacy_subcontract_labor_rows.unlink()

subcontract_contract_facts = LaborFact.search(
    [
        ("active", "=", True),
        ("project_id", "!=", False),
        ("partner_name", "!=", False),
        ("fact_type", "=", "subcontract_contract"),
    ]
)
counts["subcontract_register"]["source"] = len(subcontract_contract_facts)
for fact in subcontract_contract_facts:
    partner = partner_by_name(fact.partner_name)
    total = amount(fact.amount_contract or fact.amount_total)
    if not partner or total <= 0:
        counts["subcontract_register"]["skipped"] += 1
        continue
    work_scope = first(fact.work_scope, fact.work_part, fact.contract_name, fact.document_no, "历史分包合同")
    vals = {
        "name": first(fact.document_no, fact.contract_no, "历史分包登记-%s" % fact.id),
        "project_id": fact.project_id.id,
        "register_date": as_date(fact.document_date or fact.start_date or fact.created_time),
        "start_date": as_date(fact.start_date),
        "end_date": as_date(fact.end_date),
        "subcontract_scope": work_scope,
        "subcontractor_id": partner.id,
        "responsible_id": uid,
        "currency_id": currency_id,
        "state": "active" if fact.state == "legacy_confirmed" else "cancel",
        "management_note": "\n".join(
            item
            for item in [
                "历史分包合同登记",
                "来源合同：%s" % first(fact.contract_no, fact.contract_name),
                "来源状态：%s/%s" % (first(fact.document_state), first(fact.state)),
                "来源经办：%s" % first(fact.creator_name),
            ]
            if item
        ),
        "note": first(fact.note),
        "legacy_fact_model": fact._name,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": fact.fact_type,
        "line_ids": [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "work_scope": work_scope,
                    "work_content": first(fact.contract_name, fact.work_part, work_scope),
                    "contract_qty": 1.0,
                    "unit_name": "项",
                    "registered_amount": total,
                    "note": first(fact.work_part, fact.note),
                },
            ),
        ],
    }
    existing = SubcontractRegister.search([("legacy_fact_model", "=", fact._name), ("legacy_fact_id", "=", fact.id)], limit=1)
    if existing:
        existing.write(vals)
        counts["subcontract_register"]["updated"] += 1
    else:
        SubcontractRegister.create(vals)
        counts["subcontract_register"]["created"] += 1

subcontract_settlement_facts = LaborFact.search(
    [
        ("active", "=", True),
        ("project_id", "!=", False),
        ("partner_name", "!=", False),
        ("fact_type", "=", "subcontract_settlement"),
    ]
)
counts["subcontract_settlement"]["source"] = len(subcontract_settlement_facts)
register_by_contract = {}
registers = SubcontractRegister.search(
    [("legacy_fact_model", "=", "sc.legacy.labor.subcontract.fact"), ("legacy_fact_type", "=", "subcontract_contract")]
)
for register in registers:
    key = first(register.name)
    if key:
        register_by_contract[key] = register
for fact in subcontract_settlement_facts:
    partner = partner_by_name(fact.partner_name)
    total = amount(fact.amount_settlement or fact.amount_total or fact.amount_payable)
    if not partner or total <= 0:
        counts["subcontract_settlement"]["skipped"] += 1
        continue
    work_scope = first(fact.work_scope, fact.work_part, fact.contract_name, fact.document_no, "历史分包结算")
    register = register_by_contract.get(first(fact.contract_no)) or register_by_contract.get(first(fact.document_no))
    vals = {
        "name": first(fact.document_no, fact.contract_no, "历史分包结算-%s" % fact.id),
        "project_id": fact.project_id.id,
        "register_id": register.id if register else False,
        "subcontractor_id": partner.id,
        "settlement_date": as_date(fact.document_date or fact.end_date or fact.created_time),
        "owner_id": uid,
        "currency_id": currency_id,
        "state": "confirmed" if fact.state == "legacy_confirmed" else "cancel",
        "note": "\n".join(
            item
            for item in [
                "历史分包结算",
                "来源合同：%s" % first(fact.contract_no, fact.contract_name),
                "来源状态：%s/%s" % (first(fact.document_state), first(fact.state)),
                "来源经办：%s" % first(fact.creator_name),
                first(fact.note),
            ]
            if item
        ),
        "legacy_fact_model": fact._name,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": fact.fact_type,
        "line_ids": [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "work_scope": work_scope,
                    "work_content": first(fact.contract_name, fact.work_part, work_scope),
                    "qty": 1.0,
                    "unit_name": "项",
                    "unit_price": total,
                    "tax_rate": amount(fact.tax_rate),
                    "note": first(fact.work_part, fact.note),
                },
            ),
        ],
    }
    existing = SubcontractSettlement.search([("legacy_fact_model", "=", fact._name), ("legacy_fact_id", "=", fact.id)], limit=1)
    if existing:
        existing.write(vals)
        counts["subcontract_settlement"]["updated"] += 1
    else:
        SubcontractSettlement.create(vals)
        counts["subcontract_settlement"]["created"] += 1

equipment_plan_facts = EquipmentFact.search(
    [("active", "=", True), ("project_id", "!=", False), ("equipment_name", "!=", False), ("fact_type", "=", "lease_contract")]
)
counts["equipment_plan"]["source"] = len(equipment_plan_facts)
for fact in equipment_plan_facts:
    supplier = partner_by_name(fact.partner_name)
    name = first(fact.document_no, fact.contract_no, "历史设备计划-%s" % fact.id)
    equipment_name = first(fact.equipment_name)
    vals = {
        "name": name,
        "project_id": fact.project_id.id,
        "plan_date": as_date(fact.document_date or fact.start_date or fact.created_time),
        "start_date": as_date(fact.start_date),
        "end_date": as_date(fact.end_date),
        "usage_location": first(fact.work_part, fact.department_name),
        "owner_id": uid,
        "supplier_id": supplier.id if supplier else False,
        "state": "draft",
        "note": "\n".join(
            item
            for item in [
                "历史设备租赁合同转设备计划",
                "来源合同：%s" % first(fact.contract_no, fact.document_no),
                "来源经办：%s" % first(fact.creator_name),
                first(fact.note),
            ]
            if item
        ),
        "legacy_fact_model": fact._name,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": fact.fact_type,
        "line_ids": [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "equipment_name": equipment_name,
                    "equipment_code": first(fact.equipment_legacy_id),
                    "planned_qty": fact.qty or 1.0,
                    "planned_hours": 0.0,
                    "usage_location": first(fact.work_part, fact.department_name),
                    "note": first(fact.equipment_spec, fact.equipment_uom, fact.note),
                },
            ),
        ],
    }
    existing = EquipmentPlan.search([("legacy_fact_model", "=", fact._name), ("legacy_fact_id", "=", fact.id)], limit=1)
    if existing:
        existing.write(vals)
        counts["equipment_plan"]["updated"] += 1
    else:
        EquipmentPlan.create(vals)
        counts["equipment_plan"]["created"] += 1

equipment_usage_facts = EquipmentFact.search(
    [("active", "=", True), ("project_id", "!=", False), ("equipment_name", "!=", False), ("fact_type", "=", "equipment_shift")]
)
counts["equipment_usage"]["source"] = len(equipment_usage_facts)
for fact in equipment_usage_facts:
    supplier = partner_by_name(fact.partner_name)
    vals = {
        "name": first(fact.document_no, "历史设备使用-%s" % fact.id),
        "project_id": fact.project_id.id,
        "usage_date": as_date(fact.document_date or fact.created_time),
        "equipment_name": first(fact.equipment_name),
        "equipment_code": first(fact.equipment_legacy_id),
        "usage_location": first(fact.work_part, fact.department_name, fact.project_name, "历史项目现场"),
        "operator_name": first(fact.creator_name, fact.partner_name, "历史经办人"),
        "usage_qty": fact.qty or 1.0,
        "usage_hours": fact.qty or 1.0,
        "supplier_id": supplier.id if supplier else False,
        "recorder_id": uid,
        "state": "draft",
        "note": "\n".join(
            item
            for item in [
                "历史设备台班/使用登记",
                "来源类型：%s" % fact.fact_type,
                "设备规格：%s" % first(fact.equipment_spec),
                first(fact.note),
            ]
            if item
        ),
        "legacy_fact_model": fact._name,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": fact.fact_type,
    }
    existing = EquipmentUsage.search([("legacy_fact_model", "=", fact._name), ("legacy_fact_id", "=", fact.id)], limit=1)
    if existing:
        existing.write(vals)
        counts["equipment_usage"]["updated"] += 1
    else:
        EquipmentUsage.create(vals)
        counts["equipment_usage"]["created"] += 1

equipment_settlement_facts = EquipmentFact.search(
    [
        ("active", "=", True),
        ("project_id", "!=", False),
        ("partner_name", "!=", False),
        ("fact_type", "in", ["lease_settlement", "lease_summary"]),
    ]
)
counts["equipment_settlement"]["source"] = len(equipment_settlement_facts)
for fact in equipment_settlement_facts:
    supplier = partner_by_name(fact.partner_name)
    total = amount(fact.amount_total or fact.amount_payable)
    if not supplier or total <= 0:
        counts["equipment_settlement"]["skipped"] += 1
        continue
    equipment_name = first(fact.equipment_name, fact.contract_no, fact.document_no, "历史设备结算")
    vals = {
        "name": first(fact.document_no, fact.contract_no, "历史设备结算-%s" % fact.id),
        "project_id": fact.project_id.id,
        "supplier_id": supplier.id,
        "settlement_date": as_date(fact.document_date or fact.end_date or fact.created_time),
        "owner_id": uid,
        "currency_id": currency_id,
        "state": "draft",
        "note": "\n".join(
            item
            for item in [
                "历史设备租赁结算",
                "来源类型：%s" % fact.fact_type,
                "来源合同：%s" % first(fact.contract_no),
                first(fact.note),
            ]
            if item
        ),
        "legacy_fact_model": fact._name,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": fact.fact_type,
        "line_ids": [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "equipment_name": equipment_name,
                    "equipment_code": first(fact.equipment_legacy_id),
                    "qty": fact.qty or 1.0,
                    "unit_name": first(fact.equipment_uom, "项"),
                    "unit_price": total / (fact.qty or 1.0),
                    "tax_rate": amount(fact.tax_rate),
                    "note": first(fact.equipment_spec, fact.work_part, fact.note),
                },
            ),
        ],
    }
    existing = EquipmentSettlement.search([("legacy_fact_model", "=", fact._name), ("legacy_fact_id", "=", fact.id)], limit=1)
    if existing:
        existing.write(vals)
        counts["equipment_settlement"]["updated"] += 1
    else:
        EquipmentSettlement.create(vals)
        counts["equipment_settlement"]["created"] += 1

env.cr.commit()  # noqa: F821

result = {
    "status": "PASS",
    "mode": "fresh_db_labor_equipment_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "counts": counts,
}
RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("FRESH_DB_LABOR_EQUIPMENT_PROJECTION_WRITE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
