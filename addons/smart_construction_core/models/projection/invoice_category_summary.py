# -*- coding: utf-8 -*-
from odoo import fields, models, tools
from odoo.osv import expression


class ScInvoiceCategorySummary(models.Model):
    _name = "sc.invoice.category.summary"
    _description = "发票分类汇总表"
    _auto = False
    _rec_name = "display_name"
    _order = "company_id, project_id, direction, source_kind, invoice_type, tax_rate"
    _sc_readonly_navigation_button_methods = {
        "action_open_invoices",
    }

    display_name = fields.Char(string="汇总项", readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", readonly=True, index=True)
    direction = fields.Selection(
        [
            ("input", "进项"),
            ("output", "销项"),
            ("prepaid", "预缴"),
            ("unknown", "未识别"),
        ],
        string="收支方向",
        readonly=True,
        index=True,
    )
    source_kind = fields.Selection(
        [
            ("invoice_registration", "发票登记"),
            ("input_invoice_tax", "进项税额"),
            ("output_invoice_tax", "销项税额"),
            ("prepaid_tax", "预缴税"),
        ],
        string="业务类型",
        readonly=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("registered", "已登记"),
            ("legacy_confirmed", "历史已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        readonly=True,
        index=True,
    )
    invoice_type = fields.Char(string="发票类型", readonly=True, index=True)
    tax_rate = fields.Char(string="税率", readonly=True, index=True)
    cost_category_name = fields.Char(string="成本类别", readonly=True, index=True)
    invoice_content = fields.Char(string="开票内容", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    amount_no_tax = fields.Monetary(string="不含税金额", currency_field="currency_id", readonly=True)
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id", readonly=True)
    amount_total = fields.Monetary(string="价税合计", currency_field="currency_id", readonly=True)
    invoice_count = fields.Integer(string="发票数", readonly=True)
    legacy_invoice_count = fields.Integer(string="历史发票数", readonly=True)
    manual_invoice_count = fields.Integer(string="新系统发票数", readonly=True)
    first_invoice_date = fields.Date(string="最早发票日期", readonly=True)
    last_invoice_date = fields.Date(string="最晚发票日期", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def _empty_aware_domain(self, field_name, value):
        if value == "未填写":
            return expression.OR(
                [
                    [(field_name, "=", False)],
                    [(field_name, "=", "")],
                ]
            )
        return [(field_name, "=", value)]

    def _invoice_domain(self):
        self.ensure_one()
        domain = [("active", "=", True), ("state", "!=", "cancel")]
        for field_name in ("company_id", "project_id", "partner_id"):
            value = self[field_name]
            domain.append((field_name, "=", value.id if value else False))
        for field_name in ("direction", "source_kind", "state"):
            if self[field_name]:
                domain.append((field_name, "=", self[field_name]))
        for field_name in ("invoice_type", "tax_rate", "cost_category_name", "invoice_content"):
            value = self[field_name]
            if value:
                domain = expression.AND([domain, self._empty_aware_domain(field_name, value)])
        return domain

    def action_open_invoices(self):
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_sc_invoice_registration", raise_if_not_found=False)
        if action:
            result = action.sudo().read()[0]
        else:
            result = {
                "type": "ir.actions.act_window",
                "res_model": "sc.invoice.registration",
                "view_mode": "tree,form",
            }
        result.update(
            {
                "name": "%s / 发票登记" % (self.display_name or "发票分类"),
                "domain": self._invoice_domain(),
                "context": {
                    "search_default_group_source_kind": 1,
                    "default_project_id": self.project_id.id if self.project_id else False,
                    "default_partner_id": self.partner_id.id if self.partner_id else False,
                    "default_direction": self.direction,
                    "default_source_kind": self.source_kind,
                },
                "target": "current",
            }
        )
        return result

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('sc_invoice_registration'),
                to_regclass('project_project'),
                to_regclass('res_company')
            """
        )
        invoice_table, project_table, company_table = self._cr.fetchone()
        if not (invoice_table and project_table and company_table):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH invoice_base AS (
                    SELECT
                        i.company_id,
                        i.project_id,
                        i.partner_id,
                        i.direction,
                        i.source_kind,
                        i.state,
                        COALESCE(NULLIF(i.invoice_type, ''), '未填写') AS invoice_type,
                        COALESCE(NULLIF(i.tax_rate, ''), '未填写') AS tax_rate,
                        COALESCE(NULLIF(i.cost_category_name, ''), '未填写') AS cost_category_name,
                        COALESCE(NULLIF(i.invoice_content, ''), '未填写') AS invoice_content,
                        i.currency_id,
                        i.invoice_date,
                        i.source_origin,
                        COALESCE(i.amount_no_tax, 0.0) AS amount_no_tax,
                        COALESCE(i.tax_amount, 0.0) AS tax_amount,
                        COALESCE(i.amount_total, 0.0) AS amount_total
                    FROM sc_invoice_registration i
                    WHERE i.active IS TRUE
                      AND i.state <> 'cancel'
                )
                SELECT
                    row_number() OVER (
                        ORDER BY
                            b.company_id NULLS LAST,
                            b.project_id NULLS LAST,
                            b.direction,
                            b.source_kind,
                            b.invoice_type,
                            b.tax_rate,
                            b.cost_category_name,
                            b.invoice_content
                    )::integer AS id,
                    CONCAT_WS(
                        ' / ',
                        COALESCE(p.name->>'zh_CN', p.name->>'en_US', '未匹配项目'),
                        CASE b.direction
                            WHEN 'input' THEN '进项'
                            WHEN 'output' THEN '销项'
                            WHEN 'prepaid' THEN '预缴'
                            ELSE '未识别'
                        END,
                        CASE b.source_kind
                            WHEN 'invoice_registration' THEN '发票登记'
                            WHEN 'input_invoice_tax' THEN '进项税额'
                            WHEN 'output_invoice_tax' THEN '销项税额'
                            WHEN 'prepaid_tax' THEN '预缴税'
                            ELSE '未识别业务'
                        END,
                        b.invoice_type,
                        b.tax_rate
                    ) AS display_name,
                    b.company_id,
                    b.project_id,
                    b.partner_id,
                    b.direction,
                    b.source_kind,
                    b.state,
                    b.invoice_type,
                    b.tax_rate,
                    b.cost_category_name,
                    b.invoice_content,
                    COALESCE(b.currency_id, c.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1))
                        AS currency_id,
                    COALESCE(SUM(b.amount_no_tax), 0.0) AS amount_no_tax,
                    COALESCE(SUM(b.tax_amount), 0.0) AS tax_amount,
                    COALESCE(SUM(b.amount_total), 0.0) AS amount_total,
                    COUNT(*)::integer AS invoice_count,
                    COUNT(*) FILTER (WHERE b.source_origin = 'legacy')::integer AS legacy_invoice_count,
                    COUNT(*) FILTER (WHERE b.source_origin = 'manual')::integer AS manual_invoice_count,
                    MIN(b.invoice_date) AS first_invoice_date,
                    MAX(b.invoice_date) AS last_invoice_date,
                    '按项目、方向、业务类型、发票类型、税率、成本类别和开票内容汇总已承载发票事实'
                        AS coverage_note
                FROM invoice_base b
                LEFT JOIN project_project p ON p.id = b.project_id
                LEFT JOIN res_company c ON c.id = b.company_id
                GROUP BY
                    b.company_id,
                    b.project_id,
                    b.partner_id,
                    b.direction,
                    b.source_kind,
                    b.state,
                    b.invoice_type,
                    b.tax_rate,
                    b.cost_category_name,
                    b.invoice_content,
                    b.currency_id,
                    c.currency_id,
                    p.name->>'zh_CN',
                    p.name->>'en_US'
            )
            """
        )
