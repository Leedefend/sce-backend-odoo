# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ScP1RelationshipReviewQueue(models.Model):
    _name = "sc.p1.relationship.review.queue"
    _description = "P1关系人工复核队列"
    _auto = False
    _rec_name = "display_name"
    _order = "source_family, source_model, target_field, candidate_record_count desc"

    display_name = fields.Char(string="复核事项", readonly=True)
    source_family = fields.Selection(
        [
            ("payment_expense", "付款与费用"),
            ("tax_invoice", "税务与发票"),
            ("income_receivable", "收入与收款"),
            ("account_interfund", "账户与往来资金"),
            ("contract_settlement", "合同与结算"),
            ("project_master", "项目与主数据"),
            ("cost_control", "预算成本管控"),
        ],
        string="业务域",
        readonly=True,
        index=True,
    )
    source_model = fields.Char(string="来源模型", readonly=True, index=True)
    target_model = fields.Char(string="目标模型", readonly=True, index=True)
    target_field = fields.Char(string="目标字段", readonly=True, index=True)
    match_kind = fields.Selection(
        [
            ("partner", "往来单位"),
            ("contract", "合同"),
            ("payment_request", "付款申请"),
            ("fund_account", "资金账户"),
        ],
        string="匹配类型",
        readonly=True,
        index=True,
    )
    candidate_field = fields.Char(string="来源字段", readonly=True, index=True)
    candidate_value = fields.Char(string="来源值", readonly=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    candidate_record_count = fields.Integer(string="待复核记录数", readonly=True)
    target_match_count = fields.Integer(string="可匹配目标数", readonly=True)
    recommendation = fields.Selection(
        [
            ("hybrid_candidate", "半自动候选"),
            ("manual_review_candidate", "人工复核"),
            ("insufficient_evidence", "证据不足"),
        ],
        string="复核等级",
        readonly=True,
        index=True,
    )
    review_reason = fields.Char(string="复核原因", readonly=True)
    sample_record_names = fields.Char(string="来源单号", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("P1关系人工复核队列是只读派生结果，不能写回用户已确认历史事实。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def _table_exists(self, table):
        self._cr.execute("SELECT to_regclass(%s)", (table,))
        return bool(self._cr.fetchone()[0])

    def _column_exists(self, table, column):
        self._cr.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = %s
              AND column_name = %s
            """,
            (table, column),
        )
        return bool(self._cr.fetchone())

    @staticmethod
    def _quote(name):
        return '"' + name.replace('"', '""') + '"'

    def _raw_candidate_select(self, spec):
        table = spec["table"]
        target = spec["target_field"]
        candidate = spec["candidate_field"]
        required = {target, candidate}
        if not self._table_exists(table) or not all(self._column_exists(table, column) for column in required):
            return None

        project_expr = "src.project_id" if self._column_exists(table, "project_id") else "NULL::integer"
        if self._column_exists(table, "name"):
            record_name_expr = "src.name::text"
        elif self._column_exists(table, "document_no"):
            record_name_expr = "src.document_no::text"
        else:
            record_name_expr = "'#' || src.id::text"
        active_where = "AND src.active IS TRUE" if self._column_exists(table, "active") else ""

        return """
            SELECT
                '%(source_family)s'::text AS source_family,
                '%(source_model)s'::text AS source_model,
                '%(target_model)s'::text AS target_model,
                '%(target_field)s'::text AS target_field,
                '%(match_kind)s'::text AS match_kind,
                '%(candidate_field)s'::text AS candidate_field,
                '%(recommendation)s'::text AS recommendation,
                BTRIM(src.%(candidate_col)s::text) AS candidate_value,
                %(project_expr)s AS project_id,
                %(record_name_expr)s AS source_record_name
            FROM %(table)s src
            WHERE src.%(target_col)s IS NULL
              %(active_where)s
              AND NULLIF(BTRIM(COALESCE(src.%(candidate_col)s, '')::text), '') IS NOT NULL
        """ % {
            "source_family": spec["source_family"],
            "source_model": spec["source_model"],
            "target_model": spec["target_model"],
            "target_field": target,
            "match_kind": spec["match_kind"],
            "candidate_field": candidate,
            "recommendation": spec["recommendation"],
            "candidate_col": self._quote(candidate),
            "target_col": self._quote(target),
            "project_expr": project_expr,
            "record_name_expr": record_name_expr,
            "table": self._quote(table),
            "active_where": active_where,
        }

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)

        specs = [
            ("payment_expense", "sc.expense.claim", "sc_expense_claim", "res.partner", "partner_id", "partner", "payee", "manual_review_candidate"),
            ("payment_expense", "sc.expense.claim", "sc_expense_claim", "res.partner", "partner_id", "partner", "receipt_account_name", "manual_review_candidate"),
            ("payment_expense", "sc.expense.claim", "sc_expense_claim", "payment.request", "payment_request_id", "payment_request", "legacy_document_no", "manual_review_candidate"),
            ("payment_expense", "sc.payment.execution", "sc_payment_execution", "payment.request", "payment_request_id", "payment_request", "document_no", "manual_review_candidate"),
            ("payment_expense", "payment.request", "payment_request", "construction.contract", "contract_id", "contract", "document_no", "insufficient_evidence"),
            ("income_receivable", "sc.receipt.income", "sc_receipt_income", "construction.contract", "contract_id", "contract", "legacy_contract_no", "insufficient_evidence"),
            ("income_receivable", "sc.receipt.invoice.line", "sc_receipt_invoice_line", "construction.contract", "contract_id", "contract", "source_contract_no", "insufficient_evidence"),
            ("tax_invoice", "sc.invoice.registration", "sc_invoice_registration", "construction.contract", "contract_id", "contract", "document_no", "insufficient_evidence"),
            ("account_interfund", "sc.financing.loan", "sc_financing_loan", "res.partner", "partner_id", "partner", "legacy_counterparty_name", "manual_review_candidate"),
            ("contract_settlement", "sc.settlement.order", "sc_settlement_order", "res.partner", "partner_id", "partner", "legacy_counterparty_name", "insufficient_evidence"),
            ("contract_settlement", "sc.settlement.order", "sc_settlement_order", "construction.contract", "contract_id", "contract", "legacy_contract_no", "insufficient_evidence"),
            ("project_master", "sc.business.entity", "sc_business_entity", "res.partner", "partner_id", "partner", "name", "hybrid_candidate"),
            ("project_master", "project.project", "project_project", "res.partner", "partner_id", "partner", "partner_name", "insufficient_evidence"),
            ("cost_control", "project.cost.ledger", "project_cost_ledger", "res.partner", "partner_id", "partner", "note", "insufficient_evidence"),
        ]
        raw_selects = []
        for source_family, source_model, table, target_model, target_field, match_kind, candidate_field, recommendation in specs:
            select_sql = self._raw_candidate_select(
                {
                    "source_family": source_family,
                    "source_model": source_model,
                    "table": table,
                    "target_model": target_model,
                    "target_field": target_field,
                    "match_kind": match_kind,
                    "candidate_field": candidate_field,
                    "recommendation": recommendation,
                }
            )
            if select_sql:
                raw_selects.append(select_sql)

        raw_sql = "\nUNION ALL\n".join(raw_selects) if raw_selects else """
            SELECT
                NULL::text AS source_family,
                NULL::text AS source_model,
                NULL::text AS target_model,
                NULL::text AS target_field,
                NULL::text AS match_kind,
                NULL::text AS candidate_field,
                NULL::text AS recommendation,
                NULL::text AS candidate_value,
                NULL::integer AS project_id,
                NULL::text AS source_record_name
            WHERE FALSE
        """

        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH raw_candidates AS (
                    {raw_sql}
                ),
                normalized AS (
                    SELECT
                        raw.*
                    FROM raw_candidates raw
                    WHERE raw.candidate_value IS NOT NULL
                      AND LENGTH(raw.candidate_value) >= 2
                      AND LOWER(BTRIM(raw.candidate_value)) !~ '^[0-9[:space:][:punct:]]+$'
                ),
                grouped AS (
                    SELECT
                        source_family,
                        source_model,
                        target_model,
                        target_field,
                        match_kind,
                        candidate_field,
                        recommendation,
                        COUNT(*)::integer AS candidate_record_count,
                        MIN(candidate_value) AS sample_candidate_value,
                        MIN(source_record_name) FILTER (WHERE source_record_name IS NOT NULL) AS sample_record_name,
                        MIN(project_id) FILTER (WHERE project_id IS NOT NULL) AS sample_project_id
                    FROM normalized
                    GROUP BY
                        source_family,
                        source_model,
                        target_model,
                        target_field,
                        match_kind,
                        candidate_field,
                        recommendation
                ),
                field_summary AS (
                    SELECT
                        source_family,
                        source_model,
                        target_model,
                        target_field,
                        match_kind,
                        candidate_field,
                        recommendation,
                        SUM(candidate_record_count)::integer AS candidate_record_count,
                        0::integer AS target_match_count,
                        MIN(sample_candidate_value) AS sample_candidate_value,
                        MIN(sample_record_name) AS sample_record_name,
                        MIN(sample_project_id) AS sample_project_id
                    FROM grouped
                    GROUP BY
                        source_family,
                        source_model,
                        target_model,
                        target_field,
                        match_kind,
                        candidate_field,
                        recommendation
                )
                SELECT
                    ROW_NUMBER() OVER (
                        ORDER BY source_family, source_model, target_field, candidate_record_count DESC, candidate_field
                    )::integer AS id,
                    source_model || '.' || target_field || ' <- ' || candidate_field AS display_name,
                    source_family,
                    source_model,
                    target_model,
                    target_field,
                    match_kind,
                    candidate_field,
                    COALESCE(sample_candidate_value, '汇总候选值') AS candidate_value,
                    sample_project_id AS project_id,
                    candidate_record_count,
                    target_match_count,
                    recommendation,
                    CASE
                        WHEN recommendation = 'hybrid_candidate' THEN '探针显示存在较高人工确认价值，只能进入人工确认或新办理映射层'
                        WHEN recommendation = 'manual_review_candidate' THEN '探针显示仅有部分线索，必须人工确认后进入新办理或映射层'
                        ELSE '未找到可靠正式目标，需补主数据或从业务链路推导，禁止自动写回历史事实'
                    END AS review_reason,
                    LEFT(COALESCE(sample_record_name, ''), 240) AS sample_record_names
                FROM field_summary
            )
            """
        )
