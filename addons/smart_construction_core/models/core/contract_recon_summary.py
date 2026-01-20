# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ScContractReconSummary(models.Model):
    _name = "sc.contract.recon.summary"
    _description = "Contract Reconciliation Summary"

    contract_id = fields.Many2one(
        "construction.contract",
        string="Contract",
        required=True,
        index=True,
    )
    project_id = fields.Many2one(
        "project.project",
        string="Project",
        related="contract_id.project_id",
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        related="contract_id.partner_id",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="contract_id.currency_id",
        store=True,
        readonly=True,
    )
    contract_amount_total = fields.Monetary(
        string="Contract Amount",
        currency_field="currency_id",
        related="contract_id.amount_total",
        store=False,
        readonly=True,
    )
    settlement_total = fields.Monetary(
        string="Settlement Total",
        currency_field="currency_id",
        compute="_compute_totals",
        store=False,
    )
    settlement_ids_count = fields.Integer(
        string="Settlement Count",
        compute="_compute_totals",
        store=False,
    )
    payment_total = fields.Monetary(
        string="Payment Total",
        currency_field="currency_id",
        compute="_compute_totals",
        store=False,
    )
    payment_ids_count = fields.Integer(
        string="Payment Count",
        compute="_compute_totals",
        store=False,
    )
    delta = fields.Monetary(
        string="Delta",
        currency_field="currency_id",
        compute="_compute_totals",
        store=False,
    )
    as_of_date = fields.Date(
        string="As Of",
        default=fields.Date.context_today,
    )

    @api.depends("contract_id")
    def _compute_totals(self):
        SettlementLine = self.env["sc.settlement.order.line"]
        Settlement = self.env["sc.settlement.order"]
        Payment = self.env["payment.request"]
        line_table = SettlementLine._table
        settle_table = Settlement._table
        pay_table = Payment._table
        for rec in self:
            settlement_total = 0.0
            settlement_count = 0
            payment_total = 0.0
            payment_count = 0
            if rec.contract_id:
                self.env.cr.execute(
                    f"""
                    SELECT COALESCE(SUM(COALESCE(l.qty, 0) * COALESCE(l.price_unit, 0)), 0)
                      FROM {line_table} l
                      JOIN {settle_table} s ON s.id = l.settlement_id
                     WHERE l.contract_id = %s
                       AND s.state IN ('approve', 'done')
                    """,
                    (rec.contract_id.id,),
                )
                settlement_total = self.env.cr.fetchone()[0] or 0.0
                self.env.cr.execute(
                    f"""
                    SELECT COUNT(*)
                      FROM {settle_table} s
                     WHERE s.contract_id = %s
                       AND s.state IN ('approve', 'done')
                    """,
                    (rec.contract_id.id,),
                )
                settlement_count = self.env.cr.fetchone()[0] or 0

                self.env.cr.execute(
                    f"""
                    SELECT COALESCE(SUM(COALESCE(amount, 0)), 0)
                      FROM {pay_table}
                     WHERE contract_id = %s
                       AND state IN ('approved', 'done')
                    """,
                    (rec.contract_id.id,),
                )
                payment_total = self.env.cr.fetchone()[0] or 0.0
                self.env.cr.execute(
                    f"""
                    SELECT COUNT(*)
                      FROM {pay_table}
                     WHERE contract_id = %s
                       AND state IN ('approved', 'done')
                    """,
                    (rec.contract_id.id,),
                )
                payment_count = self.env.cr.fetchone()[0] or 0

            rec.settlement_total = settlement_total
            rec.settlement_ids_count = settlement_count
            rec.payment_total = payment_total
            rec.payment_ids_count = payment_count
            rec.delta = settlement_total - payment_total
