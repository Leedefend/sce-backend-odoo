# -*- coding: utf-8 -*-
import ast

from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ScFinanceBusinessFact(models.Model):
    _name = "sc.finance.business.fact"
    _description = "项目收付款来源明细"
    _auto = False
    _rec_name = "display_name"
    _order = "document_date desc, id desc"
    _sc_readonly_navigation_button_methods = {
        "action_open_source_record",
        "action_open_business_entry",
    }

    _BUSINESS_ENTRY_ACTION_BY_FACT_TYPE = {
        "deduction_paid": "smart_construction_core.action_sc_expense_claim_deduction_paid",
        "deduction_refund": "smart_construction_core.action_sc_expense_claim_deduction_paid_refund",
        "tax_deducted": "smart_construction_core.action_sc_tax_deduction_registration_user",
        "guarantee_out": "smart_construction_core.action_sc_expense_claim_deposit",
        "guarantee_return": "smart_construction_core.action_sc_expense_claim_deposit",
    }

    display_name = fields.Char(string="业务摘要", readonly=True)
    business_domain = fields.Selection(
        [
            ("arrival_settlement", "到款确认"),
            ("deduction_clearing", "扣款实缴/退回"),
            ("tax_deduction", "抵扣登记"),
            ("self_funding", "自筹收入/退回"),
            ("guarantee_deposit", "保证金收退"),
        ],
        string="收付款类型",
        readonly=True,
        index=True,
    )
    fact_type = fields.Selection(
        [
            ("arrival_gross", "到款确认"),
            ("deduction_paid", "扣款实缴"),
            ("deduction_refund", "扣款退回"),
            ("tax_deducted", "税务抵扣"),
            ("self_funding_income", "自筹收入"),
            ("self_funding_refund", "自筹退回"),
            ("self_funding_visible_reference", "自筹可见参考"),
            ("guarantee_out", "保证金支出"),
            ("guarantee_return", "保证金退回"),
        ],
        string="业务类型",
        readonly=True,
        index=True,
    )
    balance_policy = fields.Selection(
        [
            ("canonical", "正式余额"),
            ("clearing_component", "清分组成"),
            ("noncash_tax", "非现金税务事实"),
            ("visible_reference", "可见追溯参考"),
            ("policy_required", "待口径确认"),
        ],
        string="余额策略",
        readonly=True,
        index=True,
    )
    classification_reason = fields.Char(string="口径说明", readonly=True)
    source_model = fields.Char(string="来源模型", readonly=True, index=True)
    source_res_id = fields.Integer(string="来源记录ID", readonly=True, index=True)
    source_record_name = fields.Char(string="来源单据号", readonly=True, index=True)
    source_document_no = fields.Char(string="来源编号", readonly=True, index=True)
    source_menu_hint = fields.Char(string="来源业务入口", readonly=True, index=True)
    document_date = fields.Date(string="发生日期", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    amount = fields.Monetary(string="业务金额", currency_field="currency_id", readonly=True)
    balance_effect = fields.Monetary(string="余额影响", currency_field="currency_id", readonly=True)
    cash_in_amount = fields.Monetary(string="现金流入", currency_field="currency_id", readonly=True)
    cash_out_amount = fields.Monetary(string="现金流出", currency_field="currency_id", readonly=True)
    deduction_amount = fields.Monetary(string="扣款/清分金额", currency_field="currency_id", readonly=True)
    paid_amount = fields.Monetary(string="拨付/实付金额", currency_field="currency_id", readonly=True)
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id", readonly=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位/人员", readonly=True, index=True)
    partner_name = fields.Char(string="往来单位/人员名称", readonly=True, index=True)
    state = fields.Char(string="来源状态", readonly=True, index=True)
    legacy_source_model = fields.Char(string="历史来源模型", readonly=True, index=True)
    legacy_source_table = fields.Char(string="历史来源表", readonly=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", readonly=True, index=True)
    legacy_visible_note = fields.Text(string="历史可见说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("项目收付款来源明细是只读汇总，请从来源业务单据维护数据。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def _action_domain(self, action_result):
        raw_domain = action_result.get("domain") or []
        if isinstance(raw_domain, str):
            try:
                parsed = ast.literal_eval(raw_domain)
            except (SyntaxError, ValueError):
                parsed = []
            return list(parsed) if isinstance(parsed, list) else []
        return list(raw_domain) if isinstance(raw_domain, list) else []

    def _source_record(self):
        self.ensure_one()
        if not self.source_model or not self.source_res_id or self.source_model not in self.env:
            raise UserError("没有可打开的来源业务单据。")
        source = self.env[self.source_model].browse(self.source_res_id).exists()
        if not source:
            raise UserError("来源业务单据不存在或已归档。")
        return source

    def action_open_source_record(self):
        self.ensure_one()
        source = self._source_record()
        return {
            "type": "ir.actions.act_window",
            "name": self.source_menu_hint or source.display_name,
            "res_model": self.source_model,
            "res_id": source.id,
            "views": [(False, "form")],
            "view_mode": "form",
            "target": "current",
        }

    def action_open_business_entry(self):
        self.ensure_one()
        action_xmlid = self._BUSINESS_ENTRY_ACTION_BY_FACT_TYPE.get(self.fact_type)
        if not action_xmlid:
            return self.action_open_source_record()
        action = self.env.ref(action_xmlid, raise_if_not_found=False)
        if not action:
            return self.action_open_source_record()
        result = action.sudo().read()[0]
        domain = self._action_domain(result)
        if self.project_id:
            domain.append(("project_id", "=", self.project_id.id))
        if self.partner_id and result.get("res_model") in {"sc.expense.claim", "sc.tax.deduction.registration"}:
            domain.append(("partner_id", "=", self.partner_id.id))
        result.update(
            {
                "name": "%s / 同类正式办理" % (self.source_menu_hint or result.get("name") or "业务办理"),
                "domain": domain,
                "target": "current",
            }
        )
        return result

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('sc_legacy_fund_confirmation_document'),
                to_regclass('sc_expense_claim'),
                to_regclass('sc_tax_deduction_registration'),
                to_regclass('sc_legacy_self_funding_fact'),
                to_regclass('tender_guarantee'),
                to_regclass('tender_bid'),
                to_regclass('project_project'),
                to_regclass('res_company')
            """
        )
        if not all(self._cr.fetchone()):
            return

        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH default_company AS (
                    SELECT id AS company_id, currency_id
                      FROM res_company
                     ORDER BY id
                     LIMIT 1
                ),
                project_company AS (
                    SELECT
                        p.id AS project_id,
                        COALESCE(p.company_id, dc.company_id) AS company_id,
                        COALESCE(c.currency_id, dc.currency_id) AS currency_id
                    FROM project_project p
                    CROSS JOIN default_company dc
                    LEFT JOIN res_company c ON c.id = p.company_id
                ),
                arrival AS (
                    SELECT
                        100000000 + d.id AS id,
                        COALESCE(d.document_no, d.project_name, '到款确认') AS display_name,
                        'arrival_settlement' AS business_domain,
                        'arrival_gross' AS fact_type,
                        'canonical' AS balance_policy,
                        'arrival confirmation keeps gross receipt, deducted amount, and paid amount on one business fact' AS classification_reason,
                        'sc.legacy.fund.confirmation.document' AS source_model,
                        d.id AS source_res_id,
                        d.document_no AS source_record_name,
                        d.document_no AS source_document_no,
                        '到款确认表' AS source_menu_hint,
                        d.receipt_time::date AS document_date,
                        COALESCE(pc.company_id, dc.company_id) AS company_id,
                        COALESCE(pc.currency_id, dc.currency_id) AS currency_id,
                        COALESCE(d.actual_fund_amount, 0.0) AS amount,
                        COALESCE(d.actual_fund_amount, 0.0) AS balance_effect,
                        COALESCE(d.actual_fund_amount, 0.0) AS cash_in_amount,
                        0.0 AS cash_out_amount,
                        COALESCE(d.deducted_amount_total, 0.0) AS deduction_amount,
                        COALESCE(d.paid_amount_total, 0.0) AS paid_amount,
                        0.0 AS tax_amount,
                        d.project_id,
                        NULL::integer AS partner_id,
                        d.construction_unit_name AS partner_name,
                        d.document_state AS state,
                        'online_old_scbs:fund_confirmation' AS legacy_source_model,
                        'sc_legacy_fund_confirmation_document' AS legacy_source_table,
                        d.legacy_header_id AS legacy_record_id,
                        d.attachment_links AS legacy_visible_note
                    FROM sc_legacy_fund_confirmation_document d
                    CROSS JOIN default_company dc
                    LEFT JOIN project_company pc ON pc.project_id = d.project_id
                    WHERE d.active IS TRUE
                ),
                deduction_paid AS (
                    SELECT
                        200000000 + c.id AS id,
                        COALESCE(c.name, c.legacy_document_no, '扣款实缴') AS display_name,
                        'deduction_clearing' AS business_domain,
                        'deduction_paid' AS fact_type,
                        'canonical' AS balance_policy,
                        'formal menu source domain online_old_scbs:T_KK_SJDJB:list897' AS classification_reason,
                        'sc.expense.claim' AS source_model,
                        c.id AS source_res_id,
                        c.name AS source_record_name,
                        COALESCE(c.legacy_document_no, c.legacy_visible_document_no, c.name) AS source_document_no,
                        '扣款实缴登记' AS source_menu_hint,
                        c.date_claim AS document_date,
                        c.company_id,
                        c.currency_id,
                        COALESCE(NULLIF(c.approved_amount, 0.0), c.amount, 0.0) AS amount,
                        COALESCE(NULLIF(c.approved_amount, 0.0), c.amount, 0.0) AS balance_effect,
                        COALESCE(NULLIF(c.approved_amount, 0.0), c.amount, 0.0) AS cash_in_amount,
                        0.0 AS cash_out_amount,
                        COALESCE(NULLIF(c.approved_amount, 0.0), c.amount, 0.0) AS deduction_amount,
                        COALESCE(c.paid_amount, 0.0) AS paid_amount,
                        0.0 AS tax_amount,
                        c.project_id,
                        c.partner_id,
                        COALESCE(rp.name, c.payee, c.applicant_name) AS partner_name,
                        c.state,
                        c.legacy_source_model,
                        c.legacy_source_table,
                        c.legacy_record_id,
                        COALESCE(c.legacy_visible_note, c.legacy_visible_summary, c.summary) AS legacy_visible_note
                    FROM sc_expense_claim c
                    LEFT JOIN res_partner rp ON rp.id = c.partner_id
                    WHERE c.active IS TRUE
                      AND c.legacy_source_model = 'online_old_scbs:T_KK_SJDJB:list897'
                ),
                deduction_refund AS (
                    SELECT
                        210000000 + c.id AS id,
                        COALESCE(c.name, c.legacy_document_no, '扣款退回') AS display_name,
                        'deduction_clearing' AS business_domain,
                        'deduction_refund' AS fact_type,
                        'canonical' AS balance_policy,
                        'formal menu source domain online_old_scbs:T_KK_SJTHB:list898' AS classification_reason,
                        'sc.expense.claim' AS source_model,
                        c.id AS source_res_id,
                        c.name AS source_record_name,
                        COALESCE(c.legacy_document_no, c.legacy_visible_document_no, c.name) AS source_document_no,
                        '扣款实缴退回' AS source_menu_hint,
                        c.date_claim AS document_date,
                        c.company_id,
                        c.currency_id,
                        COALESCE(NULLIF(c.approved_amount, 0.0), c.amount, 0.0) AS amount,
                        -COALESCE(NULLIF(c.approved_amount, 0.0), c.amount, 0.0) AS balance_effect,
                        0.0 AS cash_in_amount,
                        COALESCE(NULLIF(c.approved_amount, 0.0), c.amount, 0.0) AS cash_out_amount,
                        COALESCE(NULLIF(c.approved_amount, 0.0), c.amount, 0.0) AS deduction_amount,
                        COALESCE(c.paid_amount, 0.0) AS paid_amount,
                        0.0 AS tax_amount,
                        c.project_id,
                        c.partner_id,
                        COALESCE(rp.name, c.payee, c.applicant_name) AS partner_name,
                        c.state,
                        c.legacy_source_model,
                        c.legacy_source_table,
                        c.legacy_record_id,
                        COALESCE(c.legacy_visible_note, c.legacy_visible_summary, c.summary) AS legacy_visible_note
                    FROM sc_expense_claim c
                    LEFT JOIN res_partner rp ON rp.id = c.partner_id
                    WHERE c.active IS TRUE
                      AND c.legacy_source_model = 'online_old_scbs:T_KK_SJTHB:list898'
                ),
                tax_deduction AS (
                    SELECT
                        300000000 + t.id AS id,
                        COALESCE(t.name, t.document_no, '抵扣登记') AS display_name,
                        'tax_deduction' AS business_domain,
                        'tax_deducted' AS fact_type,
                        'noncash_tax' AS balance_policy,
                        'tax deduction is a fiscal fact; it does not change cash balance directly' AS classification_reason,
                        'sc.tax.deduction.registration' AS source_model,
                        t.id AS source_res_id,
                        t.name AS source_record_name,
                        COALESCE(t.document_no, t.name) AS source_document_no,
                        '抵扣登记' AS source_menu_hint,
                        COALESCE(t.deduction_confirm_date, t.document_date) AS document_date,
                        t.company_id,
                        t.currency_id,
                        COALESCE(t.deduction_amount, 0.0) AS amount,
                        0.0 AS balance_effect,
                        0.0 AS cash_in_amount,
                        0.0 AS cash_out_amount,
                        COALESCE(t.withholding_amount, 0.0) AS deduction_amount,
                        0.0 AS paid_amount,
                        COALESCE(t.deduction_tax_amount, 0.0) AS tax_amount,
                        t.project_id,
                        t.partner_id,
                        COALESCE(rp.name, t.partner_name, t.deduction_unit_name) AS partner_name,
                        t.state,
                        t.legacy_source_model,
                        t.legacy_source_table,
                        t.legacy_record_id,
                        COALESCE(t.deduction_reason, t.note) AS legacy_visible_note
                    FROM sc_tax_deduction_registration t
                    LEFT JOIN res_partner rp ON rp.id = t.partner_id
                    WHERE t.active IS TRUE
                ),
                self_funding AS (
                    SELECT
                        400000000 + f.id AS id,
                        COALESCE(f.document_no, f.title, f.project_name, '自筹资金') AS display_name,
                        'self_funding' AS business_domain,
                        CASE
                            WHEN f.line_type = 'income' THEN 'self_funding_income'
                            WHEN f.line_type = 'refund' THEN 'self_funding_refund'
                            ELSE 'self_funding_visible_reference'
                        END AS fact_type,
                        CASE
                            WHEN f.line_type IN ('income', 'refund') THEN 'canonical'
                            WHEN f.line_type IN ('income_visible', 'refund_visible') THEN 'visible_reference'
                            ELSE 'policy_required'
                        END AS balance_policy,
                        CASE
                            WHEN f.line_type = 'income' THEN 'canonical self funding income source family'
                            WHEN f.line_type = 'refund' THEN 'canonical self funding refund source family'
                            WHEN f.line_type = 'income_visible' THEN 'visible family is near-duplicate of income and is excluded from balance'
                            WHEN f.line_type = 'refund_visible' THEN 'visible refund rows carry zero refund amount and are excluded from balance'
                            ELSE 'self funding line type requires policy confirmation'
                        END AS classification_reason,
                        'sc.legacy.self.funding.fact' AS source_model,
                        f.id AS source_res_id,
                        f.document_no AS source_record_name,
                        f.document_no AS source_document_no,
                        CASE
                            WHEN f.line_type IN ('income', 'income_visible') THEN '自筹收入'
                            WHEN f.line_type IN ('refund', 'refund_visible') THEN '自筹退回'
                            ELSE '自筹资金'
                        END AS source_menu_hint,
                        f.document_date,
                        COALESCE(pc.company_id, dc.company_id) AS company_id,
                        COALESCE(pc.currency_id, dc.currency_id) AS currency_id,
                        CASE
                            WHEN f.line_type IN ('income', 'income_visible') THEN COALESCE(f.self_funding_amount, 0.0)
                            WHEN f.line_type IN ('refund', 'refund_visible') THEN COALESCE(f.refund_amount, 0.0)
                            ELSE COALESCE(f.unreturned_amount, 0.0)
                        END AS amount,
                        CASE
                            WHEN f.line_type = 'income' THEN COALESCE(f.self_funding_amount, 0.0)
                            WHEN f.line_type = 'refund' THEN -COALESCE(f.refund_amount, 0.0)
                            ELSE 0.0
                        END AS balance_effect,
                        CASE WHEN f.line_type = 'income' THEN COALESCE(f.self_funding_amount, 0.0) ELSE 0.0 END AS cash_in_amount,
                        CASE WHEN f.line_type = 'refund' THEN COALESCE(f.refund_amount, 0.0) ELSE 0.0 END AS cash_out_amount,
                        0.0 AS deduction_amount,
                        0.0 AS paid_amount,
                        0.0 AS tax_amount,
                        f.project_id,
                        f.partner_id,
                        COALESCE(rp.name, f.partner_name) AS partner_name,
                        COALESCE(f.document_state_label, f.document_state) AS state,
                        'online_old_scbs:self_funding' AS legacy_source_model,
                        f.source_table AS legacy_source_table,
                        f.legacy_record_id,
                        COALESCE(f.note, f.attachment_text, f.kingdee_document_no) AS legacy_visible_note
                    FROM sc_legacy_self_funding_fact f
                    CROSS JOIN default_company dc
                    LEFT JOIN project_company pc ON pc.project_id = f.project_id
                    LEFT JOIN res_partner rp ON rp.id = f.partner_id
                    WHERE f.active IS TRUE
                      AND COALESCE(f.deleted_flag, '0') IN ('0', '')
                ),
                guarantee AS (
                    SELECT
                        500000000 + g.id AS id,
                        COALESCE(g.legacy_visible_document_no, b.name, b.tender_name, '保证金') AS display_name,
                        'guarantee_deposit' AS business_domain,
                        CASE WHEN g.type = 'return' THEN 'guarantee_return' ELSE 'guarantee_out' END AS fact_type,
                        'canonical' AS balance_policy,
                        'formal tender.guarantee preserves out/return balance; legacy source family remains available in source report facts' AS classification_reason,
                        'tender.guarantee' AS source_model,
                        g.id AS source_res_id,
                        COALESCE(g.legacy_visible_document_no, b.name) AS source_record_name,
                        COALESCE(g.legacy_visible_document_no, b.name) AS source_document_no,
                        CASE WHEN g.type = 'return' THEN '保证金退回' ELSE '保证金支出' END AS source_menu_hint,
                        g.date AS document_date,
                        COALESCE(pc.company_id, dc.company_id) AS company_id,
                        COALESCE(g.currency_id, pc.currency_id, dc.currency_id) AS currency_id,
                        COALESCE(g.amount, 0.0) AS amount,
                        CASE WHEN g.type = 'return' THEN -COALESCE(g.amount, 0.0) ELSE COALESCE(g.amount, 0.0) END AS balance_effect,
                        CASE WHEN g.type = 'return' THEN COALESCE(g.amount, 0.0) ELSE 0.0 END AS cash_in_amount,
                        CASE WHEN g.type = 'return' THEN 0.0 ELSE COALESCE(g.amount, 0.0) END AS cash_out_amount,
                        0.0 AS deduction_amount,
                        0.0 AS paid_amount,
                        0.0 AS tax_amount,
                        b.project_id,
                        b.owner_id AS partner_id,
                        COALESCE(rp.name, b.legacy_owner_name) AS partner_name,
                        g.state,
                        b.legacy_fact_model AS legacy_source_model,
                        'tender_guarantee' AS legacy_source_table,
                        NULLIF(b.legacy_fact_id::varchar, '') AS legacy_record_id,
                        COALESCE(g.remark, b.legacy_note) AS legacy_visible_note
                    FROM tender_guarantee g
                    JOIN tender_bid b ON b.id = g.bid_id
                    CROSS JOIN default_company dc
                    LEFT JOIN project_company pc ON pc.project_id = b.project_id
                    LEFT JOIN res_partner rp ON rp.id = b.owner_id
                )
                SELECT * FROM arrival
                UNION ALL SELECT * FROM deduction_paid
                UNION ALL SELECT * FROM deduction_refund
                UNION ALL SELECT * FROM tax_deduction
                UNION ALL SELECT * FROM self_funding
                UNION ALL SELECT * FROM guarantee
            )
            """
        )
