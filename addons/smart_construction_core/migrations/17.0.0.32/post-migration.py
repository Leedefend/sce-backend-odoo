# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


KIND_MAP = {
    "material_budget": ("material", "物资预算"),
    "labor_budget": ("labor", "人工预算"),
    "machine_budget": ("machine", "机械预算"),
    "subcontract_budget": ("subcontract", "分包预算"),
    "measure_budget": ("measure", "措施费"),
    "tax_budget": ("tax", "税费"),
}


def _migrate_project_budget_facts(env):
    Source = env["sc.project.budget.fact"].sudo()
    Budget = env["project.budget"].sudo()
    records = Source.search([("fact_type", "in", list(KIND_MAP)), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Budget.search([("legacy_source_model", "=", record._name), ("legacy_record_id", "=", str(record.id))], limit=1)
        if existing:
            continue
        kind, label = KIND_MAP[record.fact_type]
        amount = record.adjusted_budget_amount or record.original_budget_amount or record.amount or 0
        Budget.create(
            {
                "name": record.name or record.document_no or label,
                "budget_kind": kind,
                "project_id": record.project_id.id,
                "version": record.document_no or False,
                "version_date": record.business_date or record.create_date.date(),
                "is_active": record.state != "cancel",
                "currency_id": record.currency_id.id or env.company.currency_id.id,
                "amount_cost_target": amount,
                "amount_revenue_target": 0,
                "note": record.budget_basis or record.description or record.result_note,
                "legacy_source_model": record._name,
                "legacy_record_id": str(record.id),
                "legacy_document_state": record.state,
            }
        )
        created += 1
    return created


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"].sudo()
    if ICP.get_param("sc.professionalization.v17_0_0_32.done") == "1":
        return
    env.cr.execute("UPDATE project_budget SET budget_kind = 'general' WHERE budget_kind IS NULL")
    count = _migrate_project_budget_facts(env)
    ICP.set_param("sc.professionalization.v17_0_0_32.project_budget_count", str(count))
    ICP.set_param("sc.professionalization.v17_0_0_32.done", "1")
