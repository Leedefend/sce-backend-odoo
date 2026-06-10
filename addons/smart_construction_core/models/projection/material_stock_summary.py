# -*- coding: utf-8 -*-
from odoo import fields, models, tools
from odoo.osv import expression


class ScMaterialStockSummary(models.Model):
    _name = "sc.material.stock.summary"
    _description = "库存统计表（新）"
    _auto = False
    _rec_name = "display_name"
    _order = "material_name, project_name, material_spec"
    _sc_readonly_navigation_button_methods = {
        "action_open_stock_in_lines",
        "action_open_stock_out_lines",
        "action_open_all_stock_lines",
    }

    display_name = fields.Char(string="汇总项", readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True, index=True)
    material_code = fields.Char(string="材料编码", readonly=True, index=True)
    material_name = fields.Char(string="材料名称", readonly=True, index=True)
    material_spec = fields.Char(string="规格型号", readonly=True, index=True)
    material_uom = fields.Char(string="单位", readonly=True)
    partner_name = fields.Char(string="往来单位", readonly=True, index=True)
    contract_no = fields.Char(string="合同编号", readonly=True, index=True)
    warehouse_name = fields.Char(string="部门/仓库", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    in_qty = fields.Float(string="入库数量", readonly=True)
    in_amount = fields.Monetary(string="入库金额", currency_field="currency_id", readonly=True)
    in_avg_price = fields.Float(string="入库均价", readonly=True)
    out_qty = fields.Float(string="出库数量", readonly=True)
    out_amount = fields.Monetary(string="出库金额", currency_field="currency_id", readonly=True)
    out_avg_price = fields.Float(string="出库均价", readonly=True)
    profit_qty = fields.Float(string="利润数量", readonly=True)
    price_diff = fields.Float(string="价差", readonly=True)
    profit_amount = fields.Monetary(string="利润金额", currency_field="currency_id", readonly=True)
    stock_qty = fields.Float(string="库存数量", readonly=True)
    stock_amount = fields.Monetary(string="库存金额", currency_field="currency_id", readonly=True)
    stock_avg_price = fields.Float(string="库存均价", readonly=True)
    stock_in_line_count = fields.Integer(string="入库明细数", readonly=True)
    stock_out_line_count = fields.Integer(string="出库明细数", readonly=True)
    first_date = fields.Date(string="最早日期", readonly=True)
    last_date = fields.Date(string="最晚日期", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def _empty_aware_domain(self, field_name, value):
        value = value or False
        if value:
            return [(field_name, "=", value)]
        return expression.OR([[(field_name, "=", False)], [(field_name, "=", "")]])

    def _source_domain(self, fact_types):
        self.ensure_one()
        domain = [
            ("active", "=", True),
            ("state", "!=", "cancel"),
            ("fact_type", "in", fact_types),
        ]
        if self.project_id:
            domain = expression.AND([domain, expression.OR([[("project_id", "=", self.project_id.id)], [("project_id", "=", False)]])])
        else:
            domain.append(("project_id", "=", False))
        for field_name, value in (
            ("material_code", self.material_code),
            ("material_name", self.material_name),
            ("material_spec", self.material_spec),
            ("material_uom", self.material_uom),
        ):
            domain = expression.AND([domain, self._empty_aware_domain(field_name, value)])
        return domain

    def _source_context(self):
        self.ensure_one()
        return {
            "search_default_active_only": 1,
            "search_default_group_fact_type": 1,
            "default_project_id": self.project_id.id if self.project_id else False,
        }

    def _open_source_action(self, name, fact_types):
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_sc_legacy_material_stock_fact", raise_if_not_found=False)
        result = action.sudo().read()[0] if action else {"type": "ir.actions.act_window", "view_mode": "tree,form"}
        result.pop("groups_id", None)
        result.update(
            {
                "name": "%s / %s" % (self.display_name or "材料库存", name),
                "domain": self._source_domain(fact_types),
                "context": self._source_context(),
                "target": "current",
            }
        )
        return result

    def action_open_stock_in_lines(self):
        return self._open_source_action("入库来源", ["stock_in", "stock_in_line", "scbs_stock_in"])

    def action_open_stock_out_lines(self):
        return self._open_source_action("出库来源", ["stock_out", "stock_out_line"])

    def action_open_all_stock_lines(self):
        return self._open_source_action("库存来源", ["stock_in", "stock_in_line", "scbs_stock_in", "stock_out", "stock_out_line"])

    def init(self):
        self._cr.execute(
            "SELECT to_regclass('sc_legacy_material_stock_fact'), to_regclass('project_project'), to_regclass('res_company')"
        )
        fact_table, project_table, company_table = self._cr.fetchone()
        if not (fact_table and project_table and company_table):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH stock_fact AS (
                    SELECT
                        f.id,
                        f.fact_type,
                        f.material_code,
                        f.material_name,
                        f.material_spec,
                        f.material_uom,
                        COALESCE(f.project_id, parent.project_id) AS project_id,
                        COALESCE(NULLIF(f.project_name, ''), NULLIF(parent.project_name, '')) AS project_name,
                        COALESCE(NULLIF(f.partner_name, ''), NULLIF(parent.partner_name, '')) AS partner_name,
                        COALESCE(NULLIF(f.contract_no, ''), NULLIF(parent.contract_no, '')) AS contract_no,
                        COALESCE(NULLIF(f.department_name, ''), NULLIF(parent.department_name, '')) AS department_name,
                        COALESCE(f.document_date, parent.document_date) AS document_date,
                        CASE
                            WHEN f.fact_type IN ('stock_in', 'stock_in_line', 'scbs_stock_in')
                                THEN COALESCE(f.qty, 0.0)
                            ELSE 0.0
                        END AS stock_in_qty,
                        CASE
                            WHEN f.fact_type IN ('stock_in', 'stock_in_line', 'scbs_stock_in')
                                THEN COALESCE(f.amount_total, 0.0)
                            ELSE 0.0
                        END AS stock_in_amount,
                        CASE
                            WHEN f.fact_type IN ('stock_out', 'stock_out_line')
                                THEN COALESCE(f.qty, 0.0)
                            ELSE 0.0
                        END AS stock_out_qty,
                        CASE
                            WHEN f.fact_type IN ('stock_out', 'stock_out_line')
                                THEN COALESCE(f.amount_total, 0.0)
                            ELSE 0.0
                        END AS stock_out_amount
                    FROM sc_legacy_material_stock_fact f
                    LEFT JOIN sc_legacy_material_stock_fact parent
                      ON parent.source_table IN ('T_RK_RKD', 'T_CK_CKD')
                     AND parent.legacy_record_id = f.legacy_parent_id
                    WHERE f.active IS TRUE
                      AND f.state <> 'cancel'
                      AND f.fact_type IN ('stock_in', 'stock_in_line', 'scbs_stock_in', 'stock_out', 'stock_out_line')
                      AND COALESCE(NULLIF(f.material_name, ''), '') <> ''
                )
                SELECT
                    row_number() OVER (
                        ORDER BY
                            COALESCE(NULLIF(sf.material_name, ''), '未填写材料'),
                            COALESCE(p.name->>'zh_CN', p.name->>'en_US', NULLIF(sf.project_name, ''), '未匹配项目'),
                            COALESCE(NULLIF(sf.material_spec, ''), ''),
                            COALESCE(NULLIF(sf.material_uom, ''), '')
                    )::integer AS id,
                    CONCAT_WS(
                        ' / ',
                        CASE
                            WHEN COALESCE(p.name->>'zh_CN', p.name->>'en_US', NULLIF(sf.project_name, ''), '') ~ '^[0-9a-fA-F]{{32}}$'
                            THEN CONCAT('历史未归档项目 ', COALESCE(p.name->>'zh_CN', p.name->>'en_US', NULLIF(sf.project_name, '')))
                            ELSE COALESCE(p.name->>'zh_CN', p.name->>'en_US', NULLIF(sf.project_name, ''), '未匹配项目')
                        END,
                        COALESCE(NULLIF(sf.material_name, ''), '未填写材料'),
                        NULLIF(sf.material_spec, ''),
                        NULLIF(sf.material_uom, '')
                    ) AS display_name,
                    COALESCE(p.company_id, (SELECT id FROM res_company ORDER BY id LIMIT 1)) AS company_id,
                    sf.project_id,
                    CASE
                        WHEN COALESCE(p.name->>'zh_CN', p.name->>'en_US', NULLIF(sf.project_name, ''), '') ~ '^[0-9a-fA-F]{{32}}$'
                        THEN CONCAT('历史未归档项目 ', COALESCE(p.name->>'zh_CN', p.name->>'en_US', NULLIF(sf.project_name, '')))
                        ELSE COALESCE(p.name->>'zh_CN', p.name->>'en_US', NULLIF(sf.project_name, ''), '未匹配项目')
                    END AS project_name,
                    NULLIF(sf.material_code, '') AS material_code,
                    COALESCE(NULLIF(sf.material_name, ''), '未填写材料') AS material_name,
                    NULLIF(sf.material_spec, '') AS material_spec,
                    NULLIF(sf.material_uom, '') AS material_uom,
                    NULLIF(sf.partner_name, '') AS partner_name,
                    NULLIF(sf.contract_no, '') AS contract_no,
                    NULLIF(sf.department_name, '') AS warehouse_name,
                    rc.currency_id AS currency_id,
                    SUM(sf.stock_in_qty) AS in_qty,
                    SUM(sf.stock_in_amount) AS in_amount,
                    CASE WHEN SUM(sf.stock_in_qty) = 0.0 THEN 0.0 ELSE SUM(sf.stock_in_amount) / SUM(sf.stock_in_qty) END AS in_avg_price,
                    SUM(sf.stock_out_qty) AS out_qty,
                    SUM(sf.stock_out_amount) AS out_amount,
                    CASE WHEN SUM(sf.stock_out_qty) = 0.0 THEN 0.0 ELSE SUM(sf.stock_out_amount) / SUM(sf.stock_out_qty) END AS out_avg_price,
                    SUM(sf.stock_out_qty) AS profit_qty,
                    CASE
                        WHEN SUM(sf.stock_out_qty) = 0.0 OR SUM(sf.stock_in_qty) = 0.0 THEN 0.0
                        ELSE
                            CASE WHEN SUM(sf.stock_out_qty) = 0.0 THEN 0.0 ELSE SUM(sf.stock_out_amount) / SUM(sf.stock_out_qty) END
                            -
                            CASE WHEN SUM(sf.stock_in_qty) = 0.0 THEN 0.0 ELSE SUM(sf.stock_in_amount) / SUM(sf.stock_in_qty) END
                    END AS price_diff,
                    CASE
                        WHEN SUM(sf.stock_out_qty) = 0.0 OR SUM(sf.stock_in_qty) = 0.0 THEN 0.0
                        ELSE
                            (
                                CASE WHEN SUM(sf.stock_out_qty) = 0.0 THEN 0.0 ELSE SUM(sf.stock_out_amount) / SUM(sf.stock_out_qty) END
                                -
                                CASE WHEN SUM(sf.stock_in_qty) = 0.0 THEN 0.0 ELSE SUM(sf.stock_in_amount) / SUM(sf.stock_in_qty) END
                            )
                            * SUM(sf.stock_out_qty)
                    END AS profit_amount,
                    SUM(sf.stock_in_qty) - SUM(sf.stock_out_qty) AS stock_qty,
                    SUM(sf.stock_in_amount) - SUM(sf.stock_out_amount) AS stock_amount,
                    CASE
                        WHEN SUM(sf.stock_in_qty) - SUM(sf.stock_out_qty) = 0.0 THEN 0.0
                        ELSE (SUM(sf.stock_in_amount) - SUM(sf.stock_out_amount))
                            / (SUM(sf.stock_in_qty) - SUM(sf.stock_out_qty))
                    END AS stock_avg_price,
                    COUNT(*) FILTER (WHERE sf.fact_type IN ('stock_in', 'stock_in_line', 'scbs_stock_in'))::integer AS stock_in_line_count,
                    COUNT(*) FILTER (WHERE sf.fact_type IN ('stock_out', 'stock_out_line'))::integer AS stock_out_line_count,
                    MIN(sf.document_date::date) AS first_date,
                    MAX(sf.document_date::date) AS last_date,
                    '按项目、材料、规格和单位汇总历史出入库事实，库存=入库-出库' AS coverage_note
                FROM stock_fact sf
                JOIN project_project p ON p.id = sf.project_id AND p.active IS TRUE
                LEFT JOIN res_company rc ON rc.id = COALESCE(p.company_id, (SELECT id FROM res_company ORDER BY id LIMIT 1))
                GROUP BY
                    sf.project_id,
                    p.company_id,
                    rc.currency_id,
                    p.name->>'zh_CN',
                    p.name->>'en_US',
                    sf.project_name,
                    sf.material_code,
                    sf.material_name,
                    sf.material_spec,
                    sf.material_uom,
                    sf.partner_name,
                    sf.contract_no,
                    sf.department_name
            )
            """
        )
