# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.tools.float_utils import float_compare


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
        if not self.project_id:
            return []
        if not self.partner_id:
            partner_name = self._responsibility_context_partner_name()
            if not partner_name:
                return []
            return [
                ("project_id", "=", self.project_id.id),
                ("partner_id", "=", False),
                ("partner_name", "=", partner_name),
            ]
        return [
            ("project_id", "=", self.project_id.id),
            ("partner_id", "=", self.partner_id.id),
        ]

    def _responsibility_context_partner_name_fields(self):
        return (
            "partner_name",
            "legacy_partner_name",
            "actual_payee_unit",
            "legacy_visible_actual_payee_unit",
            "legacy_visible_supplier_name",
            "legacy_visible_payee_unit",
            "payee",
            "deduction_unit_name",
        )

    def _responsibility_context_partner_name(self):
        self.ensure_one()
        for field_name in self._responsibility_context_partner_name_fields():
            if field_name not in self._fields:
                continue
            value = self[field_name]
            if isinstance(value, str) and value.strip():
                return value.strip()
        return False

    def _empty_company_contractor_responsibility_context(self):
        self.company_contractor_responsibility_summary_id = False
        self.company_contractor_responsibility_state = False
        self.company_contractor_arrival_unprocessed_amount = 0.0
        self.company_contractor_arrival_over_processed_amount = 0.0
        self.company_contractor_self_funding_balance = 0.0
        self.company_contractor_responsibility_notice = _("未匹配公司-承包人责任余额")

    def _set_company_contractor_responsibility_context(self, summary):
        self.ensure_one()
        if not summary:
            self._empty_company_contractor_responsibility_context()
            return
        self.company_contractor_responsibility_summary_id = summary
        self.company_contractor_responsibility_state = summary.responsibility_state
        self.company_contractor_arrival_unprocessed_amount = summary.arrival_unprocessed_amount
        self.company_contractor_arrival_over_processed_amount = summary.arrival_over_processed_amount
        self.company_contractor_self_funding_balance = summary.self_funding_balance
        self.company_contractor_responsibility_notice = self._company_contractor_responsibility_notice(summary)

    @api.depends("project_id", "partner_id")
    def _compute_company_contractor_responsibility_context(self):
        Summary = self.env["sc.company.contractor.responsibility.summary"].sudo()
        partner_records = self.filtered(lambda rec: rec.project_id and rec.partner_id)
        partner_name_records = self - partner_records
        summaries_by_partner = {}
        summaries_by_partner_name = {}

        if partner_records:
            project_ids = list(set(partner_records.mapped("project_id").ids))
            partner_ids = list(set(partner_records.mapped("partner_id").ids))
            summaries = Summary.search(
                [
                    ("project_id", "in", project_ids),
                    ("partner_id", "in", partner_ids),
                ]
            )
            for summary in summaries:
                key = (summary.project_id.id, summary.partner_id.id)
                summaries_by_partner.setdefault(key, summary)

        partner_name_keys = {}
        for rec in partner_name_records:
            if not rec.project_id:
                rec._empty_company_contractor_responsibility_context()
                continue
            partner_name = rec._responsibility_context_partner_name()
            if not partner_name:
                rec._empty_company_contractor_responsibility_context()
                continue
            partner_name_keys[(rec.project_id.id, partner_name)] = True

        if partner_name_keys:
            summaries = Summary.search(
                [
                    ("project_id", "in", list({key[0] for key in partner_name_keys})),
                    ("partner_id", "=", False),
                    ("partner_name", "in", list({key[1] for key in partner_name_keys})),
                ]
            )
            for summary in summaries:
                key = (summary.project_id.id, summary.partner_name)
                summaries_by_partner_name.setdefault(key, summary)

        for rec in partner_records:
            summary = summaries_by_partner.get((rec.project_id.id, rec.partner_id.id))
            rec._set_company_contractor_responsibility_context(summary)

        for rec in partner_name_records:
            if not rec.project_id:
                continue
            partner_name = rec._responsibility_context_partner_name()
            if not partner_name:
                continue
            summary = summaries_by_partner_name.get((rec.project_id.id, partner_name))
            rec._set_company_contractor_responsibility_context(summary)

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

    def _company_contractor_responsibility_balance_failures(self, summary, amount, amount_label=None):
        rounding = summary.currency_id.rounding if getattr(summary, "currency_id", False) else 0.01
        over_processed = getattr(summary, "arrival_over_processed_amount", 0.0) or 0.0
        available = getattr(summary, "arrival_unprocessed_amount", 0.0) or 0.0
        checked_amount = amount or 0.0
        label = amount_label or _("本次办理金额")
        failures = []
        if float_compare(over_processed, 0.0, precision_rounding=rounding) == 1:
            failures.append(_("公司-承包人责任余额已显示到款超处理，继续办理前需先复核到款、拨付或扣款来源。"))
        if (
            float_compare(available, 0.0, precision_rounding=rounding) == 1
            and float_compare(checked_amount, available, precision_rounding=rounding) == 1
        ):
            failures.append(_("%s %.2f 超过到款可处理余额 %.2f。") % (label, checked_amount, available))
        return failures

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
                    "default_partner_name": self._responsibility_context_partner_name(),
                },
            }
        )
        return action
