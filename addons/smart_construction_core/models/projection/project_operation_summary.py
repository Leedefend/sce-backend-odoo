# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ScProjectOperationSummary(models.Model):
    _name = "sc.project.operation.summary"
    _description = "项目经营统计表"
    _auto = False
    _rec_name = "project_name"
    _order = "legacy_pid desc, project_name"
    _sc_readonly_navigation_button_methods = {
        "action_open_project",
        "action_open_source_fact",
    }

    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True, index=True)
    legacy_project_id = fields.Char(string="旧项目ID", readonly=True, index=True)
    legacy_pid = fields.Char(string="旧项目排序号", readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)

    other_amount = fields.Monetary(string="其他", currency_field="currency_id", readonly=True)
    current_receipt_amount = fields.Monetary(string="本期收款", currency_field="currency_id", readonly=True)
    vat_amount = fields.Monetary(string="增值税", currency_field="currency_id", readonly=True)
    vat_nonrefundable_amount = fields.Monetary(string="增值税(不可退)", currency_field="currency_id", readonly=True)
    vat_three_percent_amount = fields.Monetary(string="增值税3%", currency_field="currency_id", readonly=True)
    prepaid_vat_amount = fields.Monetary(string="预缴增值税", currency_field="currency_id", readonly=True)
    output_deduction_tax_diff_amount = fields.Monetary(
        string="销项税金/扣款税金差额",
        currency_field="currency_id",
        readonly=True,
    )
    output_tax_amount = fields.Monetary(string="销项金额", currency_field="currency_id", readonly=True)
    net_income_amount = fields.Monetary(string="净收入", currency_field="currency_id", readonly=True)
    operation_income_amount = fields.Monetary(string="经营收入", currency_field="currency_id", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("项目经营统计表是历史经营统计事实汇总结果，请从来源项目或统计事实维护数据。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def _open_action(self, action_xmlid, name, domain, context=None):
        self.ensure_one()
        action = self.env.ref(action_xmlid, raise_if_not_found=False)
        result = action.sudo().read()[0] if action else {"type": "ir.actions.act_window", "view_mode": "tree,form"}
        result.update(
            {
                "name": "%s / %s" % (self.project_name or "项目经营统计表", name),
                "domain": domain,
                "context": context or {"create": False},
                "target": "current",
            }
        )
        return result

    def action_open_project(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s / 项目档案" % (self.project_name or "项目经营统计表"),
            "res_model": "project.project",
            "view_mode": "tree,form",
            "domain": [("id", "=", self.project_id.id if self.project_id else 0)],
            "context": {"create": False},
            "target": "current",
        }

    def action_open_source_fact(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s / 旧项目经营统计事实" % (self.project_name or "项目经营统计表"),
            "res_model": "sc.legacy.project.operation.report.fact",
            "view_mode": "tree,form",
            "domain": [("legacy_project_id", "=", self.legacy_project_id)],
            "context": {"create": False, "edit": False, "delete": False},
            "target": "current",
        }

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('sc_legacy_project_operation_report_fact'),
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
                SELECT
                    f.id::integer AS id,
                    f.project_id,
                    COALESCE(
                        NULLIF(f.legacy_project_name, ''),
                        p.name->>'zh_CN',
                        p.name->>'en_US',
                        ''
                    ) AS project_name,
                    f.legacy_project_id,
                    f.legacy_pid,
                    p.company_id,
                    COALESCE(c.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1)) AS currency_id,
                    COALESCE(f.other_amount, 0.0) AS other_amount,
                    COALESCE(f.current_receipt_amount, 0.0) AS current_receipt_amount,
                    COALESCE(f.vat_amount, 0.0) AS vat_amount,
                    COALESCE(f.vat_nonrefundable_amount, 0.0) AS vat_nonrefundable_amount,
                    COALESCE(f.vat_three_percent_amount, 0.0) AS vat_three_percent_amount,
                    COALESCE(f.prepaid_vat_amount, 0.0) AS prepaid_vat_amount,
                    (
                        COALESCE(f.output_tax_amount, 0.0)
                        - (
                            COALESCE(f.vat_amount, 0.0)
                            + COALESCE(f.vat_nonrefundable_amount, 0.0)
                            + COALESCE(f.vat_three_percent_amount, 0.0)
                            + COALESCE(f.prepaid_vat_amount, 0.0)
                        )
                    ) AS output_deduction_tax_diff_amount,
                    COALESCE(f.output_tax_amount, 0.0) AS output_tax_amount,
                    COALESCE(f.net_income_amount, 0.0) AS net_income_amount,
                    COALESCE(f.operation_income_amount, 0.0) AS operation_income_amount,
                    '按旧存储过程 SELECT_XMJYTJB 输出行承载；XSSJKKSJZC 按旧列公式 XSJE-(ZZS+ZZS_BKT+ZZS_3+YJSJ) 计算'
                        AS coverage_note
                FROM sc_legacy_project_operation_report_fact f
                LEFT JOIN project_project p ON p.id = f.project_id
                LEFT JOIN res_company c ON c.id = p.company_id
            )
            """
        )
