# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ScExpenseReimbursementSummary(models.Model):
    _name = "sc.expense.reimbursement.summary"
    _description = "报销统计"
    _auto = False
    _rec_name = "display_name"
    _order = "project_id, expense_type, applicant_name"
    _sc_readonly_navigation_button_methods = {"action_open_expense_claims"}

    display_name = fields.Char(string="汇总项", readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", readonly=True, index=True)
    applicant_name = fields.Char(string="申请人", readonly=True, index=True)
    expense_type = fields.Char(string="费用类型", readonly=True, index=True)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        readonly=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submit", "已提交"),
            ("approved", "已批准"),
            ("done", "已完成"),
            ("legacy_confirmed", "历史已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        readonly=True,
        index=True,
    )
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    amount = fields.Monetary(string="申请金额", currency_field="currency_id", readonly=True)
    approved_amount = fields.Monetary(string="批准金额", currency_field="currency_id", readonly=True)
    claim_count = fields.Integer(string="报销单数", readonly=True)
    legacy_count = fields.Integer(string="历史报销数", readonly=True)
    manual_count = fields.Integer(string="新系统报销数", readonly=True)
    first_date = fields.Date(string="最早日期", readonly=True)
    last_date = fields.Date(string="最晚日期", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("报销统计是历史事实汇总结果，请从来源报销单据维护数据。")

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

    def _applicant_domain(self):
        self.ensure_one()
        if self.applicant_name == "未填写申请人":
            return self._empty_aware_domain("applicant_name", False)
        return self._empty_aware_domain("applicant_name", self.applicant_name)

    def _expense_type_domain(self):
        self.ensure_one()
        if self.expense_type == "未填写费用类型":
            return self._empty_aware_domain("expense_type", False)
        return self._empty_aware_domain("expense_type", self.expense_type)

    def _expense_claim_domain(self):
        self.ensure_one()
        return (
            [
                ("active", "=", True),
                ("claim_type", "=", "expense"),
                ("state", "!=", "cancel"),
                ("project_id", "=", self.project_id.id if self.project_id else False),
                ("partner_id", "=", self.partner_id.id if self.partner_id else False),
                ("source_origin", "=", self.source_origin),
                ("state", "=", self.state),
            ]
            + self._applicant_domain()
            + self._expense_type_domain()
        )

    def _open_action(self, action_xmlid, name, domain, context=None):
        self.ensure_one()
        action = self.env.ref(action_xmlid, raise_if_not_found=False)
        result = action.sudo().read()[0] if action else {"type": "ir.actions.act_window", "view_mode": "tree,form"}
        result.update(
            {
                "name": "%s / %s" % (self.display_name or "报销统计", name),
                "domain": domain,
                "context": context or {"default_claim_type": "expense"},
                "target": "current",
            }
        )
        return result

    def action_open_expense_claims(self):
        return self._open_action(
            "smart_construction_core.action_sc_expense_claim",
            "报销单据",
            self._expense_claim_domain(),
            {
                "default_claim_type": "expense",
                "default_project_id": self.project_id.id if self.project_id else False,
                "default_partner_id": self.partner_id.id if self.partner_id else False,
                "search_default_group_project": 1,
            },
        )

    def init(self):
        self._cr.execute(
            "SELECT to_regclass('sc_expense_claim'), to_regclass('project_project'), to_regclass('res_company')"
        )
        claim_table, project_table, company_table = self._cr.fetchone()
        if not (claim_table and project_table and company_table):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    row_number() OVER (
                        ORDER BY c.project_id NULLS LAST, c.expense_type, c.applicant_name, c.source_origin, c.state
                    )::integer AS id,
                    CONCAT_WS(
                        ' / ',
                        COALESCE(p.name->>'zh_CN', p.name->>'en_US', '未匹配项目'),
                        COALESCE(NULLIF(c.expense_type, ''), '未填写费用类型'),
                        COALESCE(NULLIF(c.applicant_name, ''), '未填写申请人'),
                        CASE c.source_origin WHEN 'legacy' THEN '历史迁移' ELSE '新系统登记' END
                    ) AS display_name,
                    c.company_id,
                    c.project_id,
                    c.partner_id,
                    COALESCE(NULLIF(c.applicant_name, ''), '未填写申请人') AS applicant_name,
                    COALESCE(NULLIF(c.expense_type, ''), '未填写费用类型') AS expense_type,
                    c.source_origin,
                    c.state,
                    COALESCE(c.currency_id, rc.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1))
                        AS currency_id,
                    COALESCE(SUM(c.amount), 0.0) AS amount,
                    COALESCE(SUM(c.approved_amount), 0.0) AS approved_amount,
                    COUNT(*)::integer AS claim_count,
                    COUNT(*) FILTER (WHERE c.source_origin = 'legacy')::integer AS legacy_count,
                    COUNT(*) FILTER (WHERE c.source_origin = 'manual')::integer AS manual_count,
                    MIN(c.date_claim) AS first_date,
                    MAX(c.date_claim) AS last_date,
                    '按项目、费用类型、申请人、来源和状态汇总费用报销事实' AS coverage_note
                FROM sc_expense_claim c
                LEFT JOIN project_project p ON p.id = c.project_id
                LEFT JOIN res_company rc ON rc.id = c.company_id
                WHERE c.active IS TRUE
                  AND c.claim_type = 'expense'
                  AND c.state <> 'cancel'
                GROUP BY
                    c.company_id,
                    c.project_id,
                    c.partner_id,
                    c.applicant_name,
                    c.expense_type,
                    c.source_origin,
                    c.state,
                    c.currency_id,
                    rc.currency_id,
                    p.name->>'zh_CN',
                    p.name->>'en_US'
            )
            """
        )
