# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class CompanyContractorResponsibilityContextMixin(models.AbstractModel):
    _name = "sc.company.contractor.responsibility.context.mixin"
    _description = "公司-承包人资金责任办理上下文"

    company_contractor_responsibility_summary_id = fields.Many2one(
        "sc.company.contractor.responsibility.summary",
        string="公司-承包人责任余额",
        compute="_compute_company_contractor_responsibility_context",
    )
    company_contractor_responsibility_state = fields.Selection(
        [
            ("open", "到款待处理"),
            ("over_processed", "到款超处理"),
            ("self_funding_open", "自筹未退"),
            ("settled", "已平衡"),
        ],
        string="责任状态",
        compute="_compute_company_contractor_responsibility_context",
    )
    company_contractor_arrival_unprocessed_amount = fields.Float(
        string="到款可处理余额",
        compute="_compute_company_contractor_responsibility_context",
    )
    company_contractor_arrival_over_processed_amount = fields.Float(
        string="到款超处理金额",
        compute="_compute_company_contractor_responsibility_context",
    )
    company_contractor_self_funding_balance = fields.Float(
        string="自筹未退余额",
        compute="_compute_company_contractor_responsibility_context",
    )
    company_contractor_responsibility_notice = fields.Char(
        string="责任提示",
        compute="_compute_company_contractor_responsibility_context",
    )

    def _responsibility_context_domain(self):
        self.ensure_one()
        if not self.project_id or not self.partner_id:
            return []
        return [
            ("project_id", "=", self.project_id.id),
            ("partner_id", "=", self.partner_id.id),
        ]

    def _empty_company_contractor_responsibility_context(self):
        self.company_contractor_responsibility_summary_id = False
        self.company_contractor_responsibility_state = False
        self.company_contractor_arrival_unprocessed_amount = 0.0
        self.company_contractor_arrival_over_processed_amount = 0.0
        self.company_contractor_self_funding_balance = 0.0
        self.company_contractor_responsibility_notice = _("未匹配公司-承包人责任余额")

    @api.depends("project_id", "partner_id")
    def _compute_company_contractor_responsibility_context(self):
        Summary = self.env["sc.company.contractor.responsibility.summary"].sudo()
        for rec in self:
            domain = rec._responsibility_context_domain()
            if not domain:
                rec._empty_company_contractor_responsibility_context()
                continue
            summary = Summary.search(domain, limit=1)
            if not summary:
                rec._empty_company_contractor_responsibility_context()
                continue
            rec.company_contractor_responsibility_summary_id = summary
            rec.company_contractor_responsibility_state = summary.responsibility_state
            rec.company_contractor_arrival_unprocessed_amount = summary.arrival_unprocessed_amount
            rec.company_contractor_arrival_over_processed_amount = summary.arrival_over_processed_amount
            rec.company_contractor_self_funding_balance = summary.self_funding_balance
            rec.company_contractor_responsibility_notice = rec._company_contractor_responsibility_notice(summary)

    def _company_contractor_responsibility_notice(self, summary):
        self.ensure_one()
        state = summary.responsibility_state
        if state == "over_processed":
            return _("到款已超处理，继续办理前需复核拨付、扣款或退回来源")
        if state == "open":
            return _("存在到款可处理余额，可作为拨付、扣款、退回或核销约束")
        if state == "self_funding_open":
            return _("存在自筹未退余额，继续办理前需关注公司与承包人责任")
        if state == "settled":
            return _("公司-承包人责任已平衡")
        return _("未匹配公司-承包人责任余额")

    def action_view_company_contractor_responsibility_summary(self):
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_sc_company_contractor_responsibility_summary").sudo().read()[0]
        domain = self._responsibility_context_domain()
        if self.company_contractor_responsibility_summary_id:
            domain = [("id", "=", self.company_contractor_responsibility_summary_id.id)]
        action.update(
            {
                "domain": domain or [("id", "=", 0)],
                "context": {
                    "search_default_project_id": self.project_id.id if self.project_id else False,
                    "search_default_partner_id": self.partner_id.id if self.partner_id else False,
                },
            }
        )
        return action
