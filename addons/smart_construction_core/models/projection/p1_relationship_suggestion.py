# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ScP1RelationshipSuggestion(models.Model):
    _name = "sc.p1.relationship.suggestion"
    _description = "P1关系建议"
    _auto = False
    _rec_name = "display_name"
    _order = "source_family, source_model, source_res_id"

    display_name = fields.Char(string="建议说明", readonly=True)
    source_family = fields.Selection(
        [
            ("income_receivable", "收入与收款"),
            ("tax_invoice", "税务与发票"),
        ],
        string="业务域",
        readonly=True,
        index=True,
    )
    source_model = fields.Char(string="来源模型", readonly=True, index=True)
    source_res_id = fields.Integer(string="来源记录ID", readonly=True, index=True)
    source_record_name = fields.Char(string="来源单号", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    target_model = fields.Char(string="目标模型", readonly=True, index=True)
    target_field = fields.Char(string="目标字段", readonly=True, index=True)
    partner_id = fields.Many2one("res.partner", string="建议往来单位", readonly=True, index=True)
    candidate_field = fields.Char(string="来源字段", readonly=True, index=True)
    candidate_value = fields.Char(string="来源值", readonly=True, index=True)
    match_basis = fields.Selection(
        [
            ("partner_name", "正式往来单位名称"),
            ("legacy_partner_map", "历史往来单位映射"),
        ],
        string="匹配依据",
        readonly=True,
        index=True,
    )
    confidence_score = fields.Float(string="置信度", readonly=True)
    recommendation = fields.Selection(
        [
            ("auto_candidate", "可自动建议"),
            ("manual_review_candidate", "需人工确认"),
        ],
        string="建议等级",
        readonly=True,
        index=True,
    )
    coverage_note = fields.Char(string="口径说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("P1关系建议是只读派生结果，请在正式办理单据或人工确认流程中维护关系。")

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
                to_regclass('sc_receipt_income'),
                to_regclass('sc_invoice_registration'),
                to_regclass('sc_tax_deduction_registration'),
                to_regclass('res_partner'),
                to_regclass('sc_legacy_partner_map')
            """
        )
        if not all(self._cr.fetchone()):
            return

        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH partner_alias AS (
                    SELECT
                        LOWER(BTRIM(rp.name::text)) AS norm,
                        rp.id AS partner_id,
                        'partner_name'::text AS match_basis,
                        1 AS priority
                    FROM res_partner rp
                    WHERE rp.active IS TRUE
                      AND NULLIF(BTRIM(rp.name::text), '') IS NOT NULL
                    UNION ALL
                    SELECT
                        LOWER(BTRIM(lpm.legacy_partner_name::text)) AS norm,
                        lpm.partner_id,
                        'legacy_partner_map'::text AS match_basis,
                        2 AS priority
                    FROM sc_legacy_partner_map lpm
                    WHERE lpm.active IS TRUE
                      AND lpm.partner_id IS NOT NULL
                      AND lpm.mapping_state = 'confirmed'
                      AND NULLIF(BTRIM(lpm.legacy_partner_name::text), '') IS NOT NULL
                ),
                partner_target AS (
                    SELECT DISTINCT ON (norm)
                        norm,
                        partner_id,
                        match_basis
                    FROM partner_alias
                    WHERE norm !~ '^[0-9[:space:][:punct:]]+$'
                    ORDER BY norm, priority, partner_id
                ),
                raw_candidates AS (
                    SELECT
                        'income_receivable'::text AS source_family,
                        'sc.receipt.income'::text AS source_model,
                        ri.id AS source_res_id,
                        ri.name::text AS source_record_name,
                        ri.company_id,
                        ri.currency_id,
                        ri.project_id,
                        'res.partner'::text AS target_model,
                        'partner_id'::text AS target_field,
                        'legacy_partner_name'::text AS candidate_field,
                        BTRIM(ri.legacy_partner_name::text) AS candidate_value,
                        1 AS field_rank,
                        0.95::numeric AS confidence_score
                    FROM sc_receipt_income ri
                    WHERE ri.active IS TRUE
                      AND ri.partner_id IS NULL
                      AND NULLIF(BTRIM(COALESCE(ri.legacy_partner_name, '')::text), '') IS NOT NULL
                    UNION ALL
                    SELECT
                        'tax_invoice'::text,
                        'sc.invoice.registration'::text,
                        inv.id,
                        inv.name::text,
                        inv.company_id,
                        inv.currency_id,
                        inv.project_id,
                        'res.partner'::text,
                        'partner_id'::text,
                        'invoice_issue_company'::text,
                        BTRIM(inv.invoice_issue_company::text),
                        1,
                        0.9::numeric
                    FROM sc_invoice_registration inv
                    WHERE inv.active IS TRUE
                      AND inv.partner_id IS NULL
                      AND NULLIF(BTRIM(COALESCE(inv.invoice_issue_company, '')::text), '') IS NOT NULL
                    UNION ALL
                    SELECT
                        'tax_invoice'::text,
                        'sc.invoice.registration'::text,
                        inv.id,
                        inv.name::text,
                        inv.company_id,
                        inv.currency_id,
                        inv.project_id,
                        'res.partner'::text,
                        'partner_id'::text,
                        'actual_invoice_issue_company'::text,
                        BTRIM(inv.actual_invoice_issue_company::text),
                        2,
                        0.9::numeric
                    FROM sc_invoice_registration inv
                    WHERE inv.active IS TRUE
                      AND inv.partner_id IS NULL
                      AND NULLIF(BTRIM(COALESCE(inv.actual_invoice_issue_company, '')::text), '') IS NOT NULL
                    UNION ALL
                    SELECT
                        'tax_invoice'::text,
                        'sc.invoice.registration'::text,
                        inv.id,
                        inv.name::text,
                        inv.company_id,
                        inv.currency_id,
                        inv.project_id,
                        'res.partner'::text,
                        'partner_id'::text,
                        'invoice_provider_name'::text,
                        BTRIM(inv.invoice_provider_name::text),
                        3,
                        0.85::numeric
                    FROM sc_invoice_registration inv
                    WHERE inv.active IS TRUE
                      AND inv.partner_id IS NULL
                      AND NULLIF(BTRIM(COALESCE(inv.invoice_provider_name, '')::text), '') IS NOT NULL
                    UNION ALL
                    SELECT
                        'tax_invoice'::text,
                        'sc.tax.deduction.registration'::text,
                        tax.id,
                        tax.name::text,
                        tax.company_id,
                        tax.currency_id,
                        tax.project_id,
                        'res.partner'::text,
                        'partner_id'::text,
                        'partner_name'::text,
                        BTRIM(tax.partner_name::text),
                        1,
                        0.9::numeric
                    FROM sc_tax_deduction_registration tax
                    WHERE tax.active IS TRUE
                      AND tax.partner_id IS NULL
                      AND NULLIF(BTRIM(COALESCE(tax.partner_name, '')::text), '') IS NOT NULL
                ),
                matched AS (
                    SELECT
                        raw.*,
                        target.partner_id,
                        target.match_basis,
                        ROW_NUMBER() OVER (
                            PARTITION BY raw.source_model, raw.source_res_id, raw.target_field
                            ORDER BY raw.field_rank, target.match_basis, target.partner_id
                        ) AS candidate_rank
                    FROM raw_candidates raw
                    JOIN partner_target target
                      ON target.norm = LOWER(BTRIM(raw.candidate_value))
                    WHERE LENGTH(raw.candidate_value) >= 2
                      AND LOWER(BTRIM(raw.candidate_value)) !~ '^[0-9[:space:][:punct:]]+$'
                )
                SELECT
                    ROW_NUMBER() OVER (
                        ORDER BY source_family, source_model, source_res_id, target_field
                    )::integer AS id,
                    source_record_name || ' -> ' || candidate_value AS display_name,
                    source_family,
                    source_model,
                    source_res_id,
                    source_record_name,
                    company_id,
                    currency_id,
                    project_id,
                    target_model,
                    target_field,
                    partner_id,
                    candidate_field,
                    candidate_value,
                    match_basis,
                    confidence_score::double precision,
                    CASE
                        WHEN confidence_score >= 0.9 THEN 'auto_candidate'
                        ELSE 'manual_review_candidate'
                    END AS recommendation,
                    '只读关系建议；用于后续人工确认或新办理单据带入，不回写用户已确认历史事实' AS coverage_note
                FROM matched
                WHERE candidate_rank = 1
            )
            """
        )
