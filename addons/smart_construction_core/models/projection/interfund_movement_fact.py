# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ScInterfundMovementFact(models.Model):
    _name = "sc.interfund.movement.fact"
    _description = "资金往来事实"
    _auto = False
    _rec_name = "display_name"
    _order = "document_date desc, id desc"

    display_name = fields.Char(string="事实摘要", readonly=True)
    movement_type = fields.Selection(
        [
            ("company_to_project_borrow", "公司借款给项目"),
            ("project_to_company_repay", "项目归还公司款"),
            ("project_to_project_transfer", "项目间账户调拨"),
            ("same_project_account_transfer", "同项目账户调拨"),
            ("project_to_contractor_borrow", "项目借款给承包人"),
            ("contractor_to_project_repay", "承包人归还项目款"),
            ("project_to_company_transfer", "项目账户转公司账户"),
            ("company_to_project_transfer", "公司账户转项目账户"),
            ("unclassified_account_transfer", "未完全分类账户调拨"),
        ],
        string="往来类型",
        readonly=True,
        index=True,
    )
    direction = fields.Selection(
        [
            ("in", "流入项目"),
            ("out", "流出项目"),
            ("transfer", "账户调拨"),
        ],
        string="项目视角方向",
        readonly=True,
        index=True,
    )
    classification_confidence = fields.Selection(
        [("high", "高"), ("medium", "中"), ("low", "低")],
        string="分类置信度",
        readonly=True,
        index=True,
    )
    classification_reason = fields.Char(string="分类依据", readonly=True)
    source_model = fields.Char(string="来源模型", readonly=True, index=True)
    source_res_id = fields.Integer(string="来源记录ID", readonly=True, index=True)
    source_record_name = fields.Char(string="来源单据号", readonly=True, index=True)
    source_document_no = fields.Char(string="来源编号", readonly=True, index=True)
    source_menu_hint = fields.Char(string="来源业务入口提示", readonly=True, index=True)
    document_date = fields.Date(string="发生日期", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    amount = fields.Monetary(string="金额", currency_field="currency_id", readonly=True)
    source_project_id = fields.Many2one("project.project", string="资金来源项目", readonly=True, index=True)
    source_project_name = fields.Char(string="资金来源项目名称", readonly=True)
    target_project_id = fields.Many2one("project.project", string="资金目标项目", readonly=True, index=True)
    target_project_name = fields.Char(string="资金目标项目名称", readonly=True)
    project_id = fields.Many2one("project.project", string="业务归属项目", readonly=True, index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位/人员", readonly=True, index=True)
    partner_name = fields.Char(string="往来单位/人员名称", readonly=True, index=True)
    source_account_id = fields.Many2one("sc.fund.account", string="付款账户", readonly=True, index=True)
    source_account_name = fields.Char(string="付款账户名称", readonly=True)
    target_account_id = fields.Many2one("sc.fund.account", string="收款账户", readonly=True, index=True)
    target_account_name = fields.Char(string="收款账户名称", readonly=True)
    state = fields.Char(string="来源状态", readonly=True, index=True)
    legacy_source_model = fields.Char(string="历史来源模型", readonly=True, index=True)
    legacy_source_table = fields.Char(string="历史来源表", readonly=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", readonly=True, index=True)
    legacy_visible_note = fields.Text(string="历史可见说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("资金往来事实是只读归一投影，请从来源业务单据维护数据。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('sc_fund_account_operation'),
                to_regclass('sc_fund_account'),
                to_regclass('sc_financing_loan'),
                to_regclass('sc_expense_claim'),
                to_regclass('project_project')
            """
        )
        if not all(self._cr.fetchone()):
            return

        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH project_names AS (
                    SELECT
                        id,
                        COALESCE(name->>'zh_CN', name->>'en_US') AS project_name
                    FROM project_project
                ),
                account_transfer AS (
                    SELECT
                        10000000 + op.id AS id,
                        COALESCE(op.name, '账户间资金往来') AS display_name,
                        CASE
                            WHEN src.project_id IS NOT NULL
                             AND dst.project_id IS NOT NULL
                             AND src.project_id <> dst.project_id
                                THEN 'project_to_project_transfer'
                            WHEN src.project_id IS NOT NULL
                             AND dst.project_id IS NOT NULL
                             AND src.project_id = dst.project_id
                                THEN 'same_project_account_transfer'
                            WHEN src.project_id IS NOT NULL
                             AND dst.project_id IS NULL
                                THEN 'project_to_company_transfer'
                            WHEN src.project_id IS NULL
                             AND dst.project_id IS NOT NULL
                                THEN 'company_to_project_transfer'
                            ELSE 'unclassified_account_transfer'
                        END AS movement_type,
                        'transfer' AS direction,
                        CASE
                            WHEN src.id IS NOT NULL AND dst.id IS NOT NULL THEN 'high'
                            ELSE 'low'
                        END AS classification_confidence,
                        CASE
                            WHEN src.project_id IS NOT NULL
                             AND dst.project_id IS NOT NULL
                             AND src.project_id <> dst.project_id
                                THEN 'source_account.project_id differs from target_account.project_id'
                            WHEN src.project_id IS NOT NULL
                             AND dst.project_id IS NOT NULL
                             AND src.project_id = dst.project_id
                                THEN 'source_account.project_id equals target_account.project_id'
                            WHEN src.project_id IS NOT NULL
                             AND dst.project_id IS NULL
                                THEN 'source account has project and target account has no project'
                            WHEN src.project_id IS NULL
                             AND dst.project_id IS NOT NULL
                                THEN 'target account has project and source account has no project'
                            ELSE 'transfer_between without enough project/account anchors'
                        END AS classification_reason,
                        'sc.fund.account.operation' AS source_model,
                        op.id AS source_res_id,
                        op.name AS source_record_name,
                        op.legacy_visible_document_no AS source_document_no,
                        '账户间资金往来' AS source_menu_hint,
                        op.operation_date AS document_date,
                        op.company_id,
                        op.currency_id,
                        COALESCE(op.amount, 0.0) AS amount,
                        src.project_id AS source_project_id,
                        src_project.project_name AS source_project_name,
                        dst.project_id AS target_project_id,
                        dst_project.project_name AS target_project_name,
                        op.project_id,
                        NULL::integer AS partner_id,
                        NULL::varchar AS partner_name,
                        op.source_account_id,
                        COALESCE(src.display_name, op.legacy_visible_account_name) AS source_account_name,
                        op.target_account_id,
                        COALESCE(dst.display_name, op.legacy_visible_counterparty_account_name) AS target_account_name,
                        op.state,
                        op.legacy_source_model,
                        op.legacy_source_table,
                        op.legacy_record_id,
                        COALESCE(op.legacy_visible_reason, op.operation_reason, op.legacy_visible_note) AS legacy_visible_note
                    FROM sc_fund_account_operation op
                    LEFT JOIN sc_fund_account src ON src.id = op.source_account_id
                    LEFT JOIN sc_fund_account dst ON dst.id = op.target_account_id
                    LEFT JOIN project_names src_project ON src_project.id = src.project_id
                    LEFT JOIN project_names dst_project ON dst_project.id = dst.project_id
                    WHERE op.active IS TRUE
                      AND op.operation_type = 'transfer_between'
                ),
                financing_borrow AS (
                    SELECT
                        20000000 + loan.id AS id,
                        COALESCE(loan.name, '借款事实') AS display_name,
                        CASE
                            WHEN COALESCE(loan.purpose, '') ILIKE '%借%'
                             AND COALESCE(loan.purpose, '') ILIKE '%项目%'
                             AND COALESCE(loan.purpose, '') ILIKE '%款%'
                                THEN 'project_to_contractor_borrow'
                            ELSE 'company_to_project_borrow'
                        END AS movement_type,
                        CASE
                            WHEN COALESCE(loan.purpose, '') ILIKE '%借%'
                             AND COALESCE(loan.purpose, '') ILIKE '%项目%'
                             AND COALESCE(loan.purpose, '') ILIKE '%款%'
                                THEN 'out'
                            ELSE 'in'
                        END AS direction,
                        CASE
                            WHEN COALESCE(loan.purpose, '') ILIKE '%借%'
                             AND COALESCE(loan.purpose, '') ILIKE '%项目%'
                             AND COALESCE(loan.purpose, '') ILIKE '%款%'
                                THEN 'medium'
                            ELSE 'medium'
                        END AS classification_confidence,
                        CASE
                            WHEN COALESCE(loan.purpose, '') ILIKE '%借%'
                             AND COALESCE(loan.purpose, '') ILIKE '%项目%'
                             AND COALESCE(loan.purpose, '') ILIKE '%款%'
                                THEN 'loan_type=borrowing_request and purpose text matches contractor/project borrow pattern'
                            ELSE 'loan_type=borrowing_request and direction=borrowed_fund'
                        END AS classification_reason,
                        'sc.financing.loan' AS source_model,
                        loan.id AS source_res_id,
                        loan.name AS source_record_name,
                        loan.document_no AS source_document_no,
                        CASE
                            WHEN COALESCE(loan.purpose, '') ILIKE '%借%'
                             AND COALESCE(loan.purpose, '') ILIKE '%项目%'
                             AND COALESCE(loan.purpose, '') ILIKE '%款%'
                                THEN '承包人借项目款'
                            ELSE '项目借公司款登记'
                        END AS source_menu_hint,
                        loan.document_date,
                        loan.company_id,
                        loan.currency_id,
                        COALESCE(loan.amount, 0.0) AS amount,
                        CASE
                            WHEN COALESCE(loan.purpose, '') ILIKE '%借%'
                             AND COALESCE(loan.purpose, '') ILIKE '%项目%'
                             AND COALESCE(loan.purpose, '') ILIKE '%款%'
                                THEN loan.project_id
                            ELSE NULL::integer
                        END AS source_project_id,
                        CASE
                            WHEN COALESCE(loan.purpose, '') ILIKE '%借%'
                             AND COALESCE(loan.purpose, '') ILIKE '%项目%'
                             AND COALESCE(loan.purpose, '') ILIKE '%款%'
                                THEN p.project_name
                            ELSE NULL::varchar
                        END AS source_project_name,
                        CASE
                            WHEN COALESCE(loan.purpose, '') ILIKE '%借%'
                             AND COALESCE(loan.purpose, '') ILIKE '%项目%'
                             AND COALESCE(loan.purpose, '') ILIKE '%款%'
                                THEN NULL::integer
                            ELSE loan.project_id
                        END AS target_project_id,
                        CASE
                            WHEN COALESCE(loan.purpose, '') ILIKE '%借%'
                             AND COALESCE(loan.purpose, '') ILIKE '%项目%'
                             AND COALESCE(loan.purpose, '') ILIKE '%款%'
                                THEN NULL::varchar
                            ELSE p.project_name
                        END AS target_project_name,
                        loan.project_id,
                        loan.partner_id,
                        COALESCE(rp.name, loan.legacy_visible_counterparty_name, loan.legacy_counterparty_name) AS partner_name,
                        NULL::integer AS source_account_id,
                        COALESCE(loan.legacy_visible_payer_unit, loan.legacy_visible_loan_account, loan.legacy_visible_company_name) AS source_account_name,
                        NULL::integer AS target_account_id,
                        COALESCE(loan.legacy_visible_receiver_unit, loan.legacy_visible_receipt_account, loan.legacy_visible_counterparty_account) AS target_account_name,
                        loan.state,
                        loan.legacy_source_model,
                        loan.legacy_source_table,
                        loan.legacy_record_id,
                        COALESCE(loan.purpose, loan.legacy_visible_note) AS legacy_visible_note
                    FROM sc_financing_loan loan
                    LEFT JOIN project_names p ON p.id = loan.project_id
                    LEFT JOIN res_partner rp ON rp.id = loan.partner_id
                    WHERE loan.active IS TRUE
                      AND loan.loan_type = 'borrowing_request'
                      AND loan.direction = 'borrowed_fund'
                ),
                expense_repay AS (
                    SELECT
                        30000000 + claim.id AS id,
                        COALESCE(claim.name, '还款事实') AS display_name,
                        CASE
                            WHEN claim.claim_type = 'project_company_repay'
                                THEN 'project_to_company_repay'
                            ELSE 'contractor_to_project_repay'
                        END AS movement_type,
                        CASE
                            WHEN claim.claim_type = 'project_company_repay' THEN 'out'
                            ELSE 'in'
                        END AS direction,
                        CASE
                            WHEN claim.claim_type = 'project_company_repay'
                             AND claim.expense_type = '项目还公司款登记'
                                THEN 'high'
                            WHEN claim.claim_type = 'project_company_repay'
                                THEN 'medium'
                            ELSE 'high'
                        END AS classification_confidence,
                        CASE
                            WHEN claim.claim_type = 'project_company_repay'
                             AND claim.expense_type = '项目还公司款登记'
                                THEN 'claim_type=project_company_repay and expense_type=项目还公司款登记'
                            WHEN claim.claim_type = 'project_company_repay'
                                THEN 'claim_type=project_company_repay, source menu label may differ'
                            ELSE 'expense_type=承包人还项目款 and formal menu claim_type domain'
                        END AS classification_reason,
                        'sc.expense.claim' AS source_model,
                        claim.id AS source_res_id,
                        claim.name AS source_record_name,
                        claim.legacy_document_no AS source_document_no,
                        CASE
                            WHEN claim.claim_type = 'project_company_repay'
                                THEN '项目还公司款登记'
                            ELSE '承包人还项目款'
                        END AS source_menu_hint,
                        claim.date_claim AS document_date,
                        claim.company_id,
                        claim.currency_id,
                        COALESCE(NULLIF(claim.approved_amount, 0.0), claim.amount, 0.0) AS amount,
                        CASE
                            WHEN claim.claim_type = 'project_company_repay' THEN claim.project_id
                            ELSE NULL::integer
                        END AS source_project_id,
                        CASE
                            WHEN claim.claim_type = 'project_company_repay' THEN p.project_name
                            ELSE NULL::varchar
                        END AS source_project_name,
                        CASE
                            WHEN claim.claim_type = 'project_company_repay' THEN NULL::integer
                            ELSE claim.project_id
                        END AS target_project_id,
                        CASE
                            WHEN claim.claim_type = 'project_company_repay' THEN NULL::varchar
                            ELSE p.project_name
                        END AS target_project_name,
                        claim.project_id,
                        claim.partner_id,
                        COALESCE(rp.name, claim.payee, claim.legacy_visible_borrower) AS partner_name,
                        NULL::integer AS source_account_id,
                        claim.payment_account_name AS source_account_name,
                        NULL::integer AS target_account_id,
                        claim.receipt_account_name AS target_account_name,
                        claim.state,
                        claim.legacy_source_model,
                        claim.legacy_source_table,
                        claim.legacy_record_id,
                        COALESCE(claim.summary, claim.legacy_visible_summary, claim.legacy_visible_note) AS legacy_visible_note
                    FROM sc_expense_claim claim
                    LEFT JOIN project_names p ON p.id = claim.project_id
                    LEFT JOIN res_partner rp ON rp.id = claim.partner_id
                    WHERE claim.active IS TRUE
                      AND (
                            claim.claim_type = 'project_company_repay'
                         OR (
                                claim.expense_type = '承包人还项目款'
                            AND claim.claim_type IN ('expense', 'deposit_receive')
                            )
                      )
                )
                SELECT * FROM account_transfer
                UNION ALL
                SELECT * FROM financing_borrow
                UNION ALL
                SELECT * FROM expense_repay
            )
            """
        )
