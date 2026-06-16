# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScTenderGuaranteeSummary(models.Model):
    _name = "sc.tender.guarantee.summary"
    _description = "投标保证金报表"
    _auto = False
    _rec_name = "tender_project_name"
    _order = "registration_time, tender_project_name"
    _sc_readonly_navigation_button_methods = {
        "action_open_tender_registration",
        "action_open_self_funding",
        "action_open_self_funding_refund",
        "action_open_pay_guarantee",
        "action_open_pay_guarantee_refund",
    }

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

    def _tender_project_domain(self, field_name):
        self.ensure_one()
        name = (self.tender_project_name or "").strip()
        if name:
            return [(field_name, "=", name)]
        return [(field_name, "=", False)]

    def _open_action(self, action_xmlid, name, domain, context=None):
        self.ensure_one()
        action = self.env.ref(action_xmlid, raise_if_not_found=False)
        result = action.sudo().read()[0] if action else {"type": "ir.actions.act_window", "view_mode": "tree,form"}
        result.update(
            {
                "name": "%s / %s" % (self.tender_project_name or "投标项目", name),
                "domain": domain,
                "context": context or {},
                "target": "current",
            }
        )
        return result

    def action_open_tender_registration(self):
        return self._open_action(
            "smart_construction_core.action_sc_legacy_tender_registration_fact",
            "投标报名来源",
            self._tender_project_domain("project_name") + [("active", "=", True), ("document_state", "=", "2")],
        )

    def action_open_self_funding(self):
        return self._open_guarantee_facts("自筹保证金", "ZJGL_BZJGL_Branch_SBZJDJ")

    def action_open_self_funding_refund(self):
        return self._open_guarantee_facts("自筹保证金退回", "ZJGL_BZJGL_Branch_SBZJTH")

    def action_open_pay_guarantee(self):
        return self._open_guarantee_facts("付保证金", "ZJGL_BZJGL_Pay_FBZJ")

    def action_open_pay_guarantee_refund(self):
        return self._open_guarantee_facts("付保证金退回", "ZJGL_BZJGL_Pay_FBZJTH")

    def _open_guarantee_facts(self, name, source_table):
        return self._open_action(
            "smart_construction_core.action_sc_legacy_tender_guarantee_report_fact",
            name,
            self._tender_project_domain("legacy_tender_project_name")
            + [("legacy_source_table", "=", source_table)],
            {"search_default_group_source_table": 1},
        )

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
