# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScTenderGuaranteeSummary(models.Model):
    _name = "sc.tender.guarantee.summary"
    _description = "投标保证金报表"
    _auto = False
    _rec_name = "tender_project_name"
    _order = "registration_time, tender_project_name"

    tender_project_name = fields.Char(string="投标项目名称", readonly=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    registration_time = fields.Datetime(string="登记时间", readonly=True, index=True)
    self_funding_amount = fields.Monetary(string="自筹保证金", currency_field="currency_id", readonly=True)
    pay_guarantee_amount = fields.Monetary(string="付保证金", currency_field="currency_id", readonly=True)
    pay_guarantee_refund_amount = fields.Monetary(string="付保证金退回", currency_field="currency_id", readonly=True)
    self_funding_refund_amount = fields.Monetary(string="自筹保证金退回", currency_field="currency_id", readonly=True)
    pay_guarantee_unreturned_amount = fields.Monetary(string="付保证金未退金额", currency_field="currency_id", readonly=True)
    self_funding_unreturned_amount = fields.Monetary(string="自筹保证金未退金额", currency_field="currency_id", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('sc_legacy_tender_registration_fact'),
                to_regclass('sc_legacy_tender_guarantee_report_fact'),
                to_regclass('res_company')
            """
        )
        if not all(self._cr.fetchone()):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH tender_rows AS (
                    SELECT
                        MIN(t.id)::integer AS id,
                        NULLIF(BTRIM(t.project_name), '') AS tender_project_name,
                        MIN(t.project_id) AS project_id,
                        MIN(t.company_id) AS company_id,
                        t.created_time AS registration_time
                    FROM sc_legacy_tender_registration_fact t
                    WHERE t.active IS TRUE
                      AND t.document_state = '2'
                      AND NULLIF(BTRIM(t.project_name), '') IS NOT NULL
                    GROUP BY NULLIF(BTRIM(t.project_name), ''), t.created_time
                ),
                deposit_by_tender_project AS (
                    SELECT
                        NULLIF(BTRIM(d.legacy_tender_project_name), '') AS tender_project_name,
                        COUNT(*) FILTER (WHERE d.legacy_source_table = 'ZJGL_BZJGL_Branch_SBZJDJ')
                            AS self_funding_count,
                        SUM(
                            CASE WHEN d.legacy_source_table = 'ZJGL_BZJGL_Branch_SBZJDJ'
                                THEN COALESCE(d.source_amount, 0.0) ELSE 0.0 END
                        ) AS self_funding_amount,
                        COUNT(*) FILTER (WHERE d.legacy_source_table = 'ZJGL_BZJGL_Branch_SBZJTH')
                            AS self_funding_refund_count,
                        SUM(
                            CASE WHEN d.legacy_source_table = 'ZJGL_BZJGL_Branch_SBZJTH'
                                THEN COALESCE(d.source_amount, 0.0) ELSE 0.0 END
                        ) AS self_funding_refund_amount,
                        COUNT(*) FILTER (WHERE d.legacy_source_table = 'ZJGL_BZJGL_Pay_FBZJ')
                            AS pay_guarantee_count,
                        SUM(
                            CASE WHEN d.legacy_source_table = 'ZJGL_BZJGL_Pay_FBZJ'
                                THEN COALESCE(d.source_amount, 0.0) ELSE 0.0 END
                        ) AS pay_guarantee_amount,
                        COUNT(*) FILTER (WHERE d.legacy_source_table = 'ZJGL_BZJGL_Pay_FBZJTH')
                            AS pay_guarantee_refund_count,
                        SUM(
                            CASE WHEN d.legacy_source_table = 'ZJGL_BZJGL_Pay_FBZJTH'
                                THEN COALESCE(d.source_amount, 0.0) ELSE 0.0 END
                        ) AS pay_guarantee_refund_amount
                    FROM sc_legacy_tender_guarantee_report_fact d
                    WHERE d.legacy_source_table IN (
                        'ZJGL_BZJGL_Branch_SBZJDJ',
                        'ZJGL_BZJGL_Branch_SBZJTH',
                        'ZJGL_BZJGL_Pay_FBZJ',
                        'ZJGL_BZJGL_Pay_FBZJTH'
                    )
                      AND NULLIF(BTRIM(d.legacy_tender_project_name), '') IS NOT NULL
                    GROUP BY NULLIF(BTRIM(d.legacy_tender_project_name), '')
                )
                SELECT
                    tr.id,
                    tr.tender_project_name,
                    tr.project_id,
                    tr.company_id,
                    COALESCE(c.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1)) AS currency_id,
                    tr.registration_time,
                    COALESCE(d.self_funding_amount, 0.0)
                        * GREATEST(COALESCE(d.self_funding_refund_count, 0), 1)
                        * GREATEST(COALESCE(d.pay_guarantee_count, 0), 1)
                        * GREATEST(COALESCE(d.pay_guarantee_refund_count, 0), 1)
                        AS self_funding_amount,
                    COALESCE(d.pay_guarantee_amount, 0.0)
                        * GREATEST(COALESCE(d.self_funding_count, 0), 1)
                        * GREATEST(COALESCE(d.self_funding_refund_count, 0), 1)
                        * GREATEST(COALESCE(d.pay_guarantee_refund_count, 0), 1)
                        AS pay_guarantee_amount,
                    COALESCE(d.pay_guarantee_refund_amount, 0.0)
                        * GREATEST(COALESCE(d.self_funding_count, 0), 1)
                        * GREATEST(COALESCE(d.self_funding_refund_count, 0), 1)
                        * GREATEST(COALESCE(d.pay_guarantee_count, 0), 1)
                        AS pay_guarantee_refund_amount,
                    COALESCE(d.self_funding_refund_amount, 0.0)
                        * GREATEST(COALESCE(d.self_funding_count, 0), 1)
                        * GREATEST(COALESCE(d.pay_guarantee_count, 0), 1)
                        * GREATEST(COALESCE(d.pay_guarantee_refund_count, 0), 1)
                        AS self_funding_refund_amount,
                    (
                        COALESCE(d.pay_guarantee_amount, 0.0)
                            * GREATEST(COALESCE(d.self_funding_count, 0), 1)
                            * GREATEST(COALESCE(d.self_funding_refund_count, 0), 1)
                            * GREATEST(COALESCE(d.pay_guarantee_refund_count, 0), 1)
                    ) - (
                        COALESCE(d.pay_guarantee_refund_amount, 0.0)
                            * GREATEST(COALESCE(d.self_funding_count, 0), 1)
                            * GREATEST(COALESCE(d.self_funding_refund_count, 0), 1)
                            * GREATEST(COALESCE(d.pay_guarantee_count, 0), 1)
                    ) AS pay_guarantee_unreturned_amount,
                    (
                        COALESCE(d.self_funding_amount, 0.0)
                            * GREATEST(COALESCE(d.self_funding_refund_count, 0), 1)
                            * GREATEST(COALESCE(d.pay_guarantee_count, 0), 1)
                            * GREATEST(COALESCE(d.pay_guarantee_refund_count, 0), 1)
                    ) - (
                        COALESCE(d.self_funding_refund_amount, 0.0)
                            * GREATEST(COALESCE(d.self_funding_count, 0), 1)
                            * GREATEST(COALESCE(d.pay_guarantee_count, 0), 1)
                            * GREATEST(COALESCE(d.pay_guarantee_refund_count, 0), 1)
                    ) AS self_funding_unreturned_amount,
                    '按旧投标保证金报表 SQL：P_ZTB_GCBMGL.f_GCMC = 保证金表.TBXMMC；原始事实保留旧 SQL 对保证金表不加 DEL/DJZT 过滤的口径'
                        AS coverage_note
                FROM tender_rows tr
                LEFT JOIN deposit_by_tender_project d ON d.tender_project_name = tr.tender_project_name
                LEFT JOIN res_company c ON c.id = tr.company_id
            )
            """
        )
