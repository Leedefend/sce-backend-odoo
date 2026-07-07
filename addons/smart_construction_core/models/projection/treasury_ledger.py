# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryLedger(models.Model):
    _name = "sc.treasury.ledger"
    _description = "资金台账"
    _order = "id desc"
    _sc_readonly_navigation_button_methods = {
        "action_open_payment_request",
        "action_open_settlement",
    }

    name = fields.Char(string="流水号", required=True, default="新建", copy=False)
    date = fields.Date(string="发生日期", default=fields.Date.context_today, required=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, required=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True)
    settlement_id = fields.Many2one("sc.settlement.order", string="结算单", index=True)
    payment_request_id = fields.Many2one("payment.request", string="付款/收款申请", index=True)
    linked_settlement_count = fields.Integer(
        string="关联结算单数",
        compute="_compute_linked_settlement_summary",
        store=True,
        compute_sudo=True,
    )
    linked_settlement_summary = fields.Char(
        string="明细结算依据",
        compute="_compute_linked_settlement_summary",
        store=True,
        compute_sudo=True,
    )
    source_model = fields.Char(string="来源模型", index=True)
    source_res_id = fields.Integer(string="来源记录ID", index=True)
    direction = fields.Selection(
        [("out", "支出"), ("in", "收入")],
        string="方向",
        required=True,
        default="out",
    )
    amount = fields.Monetary(string="金额", required=True, currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    state = fields.Selection(
        [("posted", "已入账"), ("void", "作废")],
        string="状态",
        default="posted",
        required=True,
    )
    note = fields.Text(string="备注")
    source_kind = fields.Selection(
        [
            ("runtime", "运行时"),
            ("interfund", "往来资金"),
            ("self_funding", "自筹资金"),
            ("daily_line", "资金日报"),
            ("legacy_actual_outflow", "历史实付"),
            ("legacy_receipt", "历史收款"),
        ],
        string="来源类型",
        default="runtime",
        required=True,
        index=True,
    )
    legacy_record_id = fields.Char(string="历史记录ID", index=True)
    legacy_source_ref = fields.Char(string="历史来源", index=True)

    _sql_constraints = [
        ("payment_request_unique", "unique(payment_request_id)", "同一付款/收款申请只能生成一条资金流水。"),
    ]

    def init(self):
        self.env.cr.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS sc_treasury_ledger_source_unique
                ON sc_treasury_ledger(source_model, source_res_id, project_id, direction, source_kind)
             WHERE source_model IS NOT NULL
               AND source_res_id IS NOT NULL
            """
        )

    @api.model_create_multi
    def create(self, vals_list):
        # 限制只能通过业务动作创建
        if not self.env.context.get("allow_ledger_auto"):
            raise UserError(_("资金台账不能手工创建。"))
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name") in (False, "新建"):
                vals["name"] = seq.next_by_code("sc.treasury.ledger") or _("Ledger")
        return super().create(vals_list)

    @api.model
    def _ensure_interfund_ledger(
        self,
        source_record,
        *,
        project,
        partner=False,
        direction,
        amount,
        date=False,
        currency=False,
        note=False,
    ):
        if not project or not amount or amount <= 0:
            return self.browse()
        domain = [
            ("source_model", "=", source_record._name),
            ("source_res_id", "=", source_record.id),
            ("project_id", "=", project.id),
            ("direction", "=", direction),
            ("source_kind", "=", "interfund"),
        ]
        existing = self.sudo().search(domain, limit=1)
        if existing:
            existing.sudo().write(
                {
                    "date": date or existing.date or fields.Date.context_today(self),
                    "partner_id": partner.id if partner else False,
                    "amount": amount,
                    "currency_id": currency.id if currency else project.company_id.currency_id.id,
                    "state": "posted",
                    "note": note,
                }
            )
            return existing
        return self.sudo().with_context(allow_ledger_auto=True).create(
            {
                "date": date or fields.Date.context_today(self),
                "project_id": project.id,
                "partner_id": partner.id if partner else False,
                "direction": direction,
                "amount": amount,
                "currency_id": currency.id if currency else project.company_id.currency_id.id,
                "source_kind": "interfund",
                "source_model": source_record._name,
                "source_res_id": source_record.id,
                "note": note,
            }
        )

    @api.model
    def _void_stale_interfund_ledgers(self):
        """Void interfund ledger rows that no longer match current interfund facts."""
        self.env.cr.execute(
            """
            WITH expected AS (
                SELECT
                    f.source_model,
                    f.source_res_id,
                    f.source_project_id AS project_id,
                    'out'::varchar AS direction
                FROM sc_interfund_movement_fact f
                WHERE f.amount > 0
                  AND f.source_project_id IS NOT NULL
                  AND f.movement_type IN (
                        'project_to_project_transfer',
                        'project_to_company_transfer',
                        'project_to_contractor_borrow',
                        'project_to_company_repay'
                  )
                UNION ALL
                SELECT
                    f.source_model,
                    f.source_res_id,
                    f.target_project_id AS project_id,
                    'in'::varchar AS direction
                FROM sc_interfund_movement_fact f
                WHERE f.amount > 0
                  AND f.target_project_id IS NOT NULL
                  AND f.movement_type IN (
                        'project_to_project_transfer',
                        'company_to_project_transfer',
                        'company_to_project_borrow',
                        'contractor_to_project_repay'
                  )
            )
            UPDATE sc_treasury_ledger ledger
               SET state = 'void',
                   note = COALESCE(NULLIF(ledger.note, ''), 'auto:void_stale_interfund_ledger')
             WHERE ledger.source_kind = 'interfund'
               AND ledger.state != 'void'
               AND ledger.source_model IS NOT NULL
               AND ledger.source_res_id IS NOT NULL
               AND NOT EXISTS (
                   SELECT 1
                     FROM expected e
                    WHERE e.source_model = ledger.source_model
                      AND e.source_res_id = ledger.source_res_id
                      AND e.project_id = ledger.project_id
                      AND e.direction = ledger.direction
               )
            """
        )
        return True

    @api.constrains("amount")
    def _check_amount_positive(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("资金流水金额必须大于 0。"))

    @api.depends(
        "settlement_id",
        "settlement_id.name",
        "payment_request_id.outflow_line_ids.settlement_id",
        "payment_request_id.outflow_line_ids.settlement_id.name",
    )
    def _compute_linked_settlement_summary(self):
        for rec in self:
            settlements = rec._linked_settlement_orders()
            rec.linked_settlement_count = len(settlements)
            names = [settlement.display_name for settlement in settlements]
            if len(names) > 3:
                rec.linked_settlement_summary = "%s 等%s张" % ("、".join(names[:3]), len(names))
            else:
                rec.linked_settlement_summary = "、".join(names)

    def _linked_settlement_orders(self):
        self.ensure_one()
        settlements = self.settlement_id
        request = self.payment_request_id
        if request:
            settlements |= request._linked_settlement_orders()
        return settlements.exists()

    def action_open_payment_request(self):
        self.ensure_one()
        if not self.payment_request_id:
            raise UserError(_("当前资金流水没有关联付款/收款申请。"))
        return {
            "type": "ir.actions.act_window",
            "name": _("付款/收款申请"),
            "res_model": "payment.request",
            "res_id": self.payment_request_id.id,
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_project_id": self.project_id.id,
                "default_partner_id": self.partner_id.id,
            },
        }

    def action_open_settlement(self):
        self.ensure_one()
        settlement = self.settlement_id
        if not settlement:
            settlements = self._linked_settlement_orders()
            if len(settlements) == 1:
                settlement = settlements
            elif len(settlements) > 1:
                raise UserError(_("当前资金流水关联多张结算单，请在付款/收款申请明细中查看。"))
        if not settlement:
            raise UserError(_("当前资金流水没有关联结算单。"))
        return {
            "type": "ir.actions.act_window",
            "name": _("结算单"),
            "res_model": "sc.settlement.order",
            "res_id": settlement.id,
            "view_mode": "form",
            "target": "current",
            "context": {"default_project_id": self.project_id.id},
        }
