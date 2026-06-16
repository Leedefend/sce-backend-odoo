# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ScSalarySummary(models.Model):
    _name = "sc.salary.summary"
    _description = "工资统计表"
    _auto = False
    _rec_name = "display_name"
    _order = "period_year desc, period_month desc, department_id, payer_unit"
    _sc_readonly_navigation_button_methods = {"action_open_salary_documents"}

    display_name = fields.Char(string="汇总项", readonly=True)
    period_year = fields.Integer(string="年度", readonly=True, index=True)
    period_month = fields.Integer(string="月份", readonly=True, index=True)
    department_id = fields.Many2one("hr.department", string="部门", readonly=True, index=True)
    payer_unit = fields.Char(string="发放单位", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    salary_base = fields.Monetary(string="薪资基数", currency_field="currency_id", readonly=True)
    gross_amount = fields.Monetary(string="应发工资", currency_field="currency_id", readonly=True)
    deduction_amount = fields.Monetary(string="扣款合计", currency_field="currency_id", readonly=True)
    net_salary = fields.Monetary(string="实发工资", currency_field="currency_id", readonly=True)
    employee_count = fields.Integer(string="人员数", readonly=True)
    document_count = fields.Integer(string="工资单数", readonly=True)
    legacy_count = fields.Integer(string="历史工资数", readonly=True)
    manual_count = fields.Integer(string="新系统工资数", readonly=True)
    first_business_date = fields.Date(string="最早业务日期", readonly=True)
    last_business_date = fields.Date(string="最晚业务日期", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("工资统计表是历史事实汇总结果，请从来源工资登记维护数据。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def _empty_aware_domain(self, field_name, value):
        if value:
            return [(field_name, "=", value)]
        return ["|", (field_name, "=", False), (field_name, "=", "")]

    def _payer_unit_domain(self):
        self.ensure_one()
        if self.payer_unit == "未填写发放单位":
            return self._empty_aware_domain("payer_unit", False)
        return self._empty_aware_domain("payer_unit", self.payer_unit)

    def _salary_document_domain(self):
        self.ensure_one()
        return (
            [
                ("active", "=", True),
                ("fact_type", "=", "salary_registration"),
                ("state", "!=", "cancel"),
                ("period_year", "=", self.period_year),
                ("period_month", "=", self.period_month),
                ("department_id", "=", self.department_id.id if self.department_id else False),
            ]
            + self._payer_unit_domain()
        )

    def _open_action(self, action_xmlid, name, domain, context=None):
        self.ensure_one()
        action = self.env.ref(action_xmlid, raise_if_not_found=False)
        result = action.sudo().read()[0] if action else {"type": "ir.actions.act_window", "view_mode": "tree,form"}
        result.update(
            {
                "name": "%s / %s" % (self.display_name or "工资统计表", name),
                "domain": domain,
                "context": context or {"default_fact_type": "salary_registration"},
                "target": "current",
            }
        )
        return result

    def action_open_salary_documents(self):
        return self._open_action(
            "smart_construction_core.action_sc_salary_registration",
            "工资登记",
            self._salary_document_domain(),
            {
                "default_fact_type": "salary_registration",
                "default_department_id": self.department_id.id if self.department_id else False,
                "search_default_group_period_year": 1,
                "search_default_group_period_month": 1,
            },
        )

    def init(self):
        self._cr.execute("SELECT to_regclass('sc_hr_payroll_document'), to_regclass('res_company')")
        payroll_table, company_table = self._cr.fetchone()
        if not (payroll_table and company_table):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    row_number() OVER (
                        ORDER BY h.period_year DESC NULLS LAST,
                                 h.period_month DESC NULLS LAST,
                                 h.department_id NULLS LAST,
                                 h.payer_unit
                    )::integer AS id,
                    CONCAT_WS(
                        ' / ',
                        COALESCE(NULLIF(h.period_year::text, '0'), '未填写年度')
                            || '-' ||
                            COALESCE(lpad(NULLIF(h.period_month::text, '0'), 2, '0'), '未填写月份'),
                        COALESCE(d.name->>'zh_CN', d.name->>'en_US', '未填写部门'),
                        COALESCE(NULLIF(h.payer_unit, ''), '未填写发放单位')
                    ) AS display_name,
                    h.period_year,
                    h.period_month,
                    h.department_id,
                    COALESCE(NULLIF(h.payer_unit, ''), '未填写发放单位') AS payer_unit,
                    COALESCE(h.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1)) AS currency_id,
                    COALESCE(SUM(h.salary_base), 0.0) AS salary_base,
                    COALESCE(SUM(h.gross_amount), 0.0) AS gross_amount,
                    COALESCE(SUM(h.deduction_amount), 0.0) AS deduction_amount,
                    COALESCE(SUM(h.net_salary), 0.0) AS net_salary,
                    COUNT(DISTINCT COALESCE(NULLIF(h.employee_name, ''), h.employee_user_id::text, h.id::text))::integer
                        AS employee_count,
                    COUNT(*)::integer AS document_count,
                    COUNT(*) FILTER (WHERE h.legacy_source_id IS NOT NULL)::integer AS legacy_count,
                    COUNT(*) FILTER (WHERE h.legacy_source_id IS NULL)::integer AS manual_count,
                    MIN(h.business_date) AS first_business_date,
                    MAX(h.business_date) AS last_business_date,
                    '按年度、月份、部门和发放单位汇总工资登记事实' AS coverage_note
                FROM sc_hr_payroll_document h
                LEFT JOIN hr_department d ON d.id = h.department_id
                WHERE h.active IS TRUE
                  AND h.fact_type = 'salary_registration'
                  AND h.state <> 'cancel'
                GROUP BY
                    h.period_year,
                    h.period_month,
                    h.department_id,
                    h.payer_unit,
                    h.currency_id,
                    d.name->>'zh_CN',
                    d.name->>'en_US'
            )
            """
        )
