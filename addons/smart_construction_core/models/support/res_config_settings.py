# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
    兜底：部分继承视图里引用了 is_installed_sale，
    在未安装 sale/purchase 组合时字段不存在会导致设置页加载失败。
    """

    _inherit = "res.config.settings"

    is_installed_sale = fields.Boolean(
        string="Sale Installed (placeholder)",
        readonly=True,
        help="占位字段，防止视图引用缺失。真实是否安装销售模块以实际环境为准。",
    )

    days_to_purchase = fields.Float(
        string="Days to Purchase (placeholder)",
        readonly=True,
        help="占位字段，用于兼容视图中对 days_to_purchase 的引用；"
             "未安装采购库存模块时不会实际生效。",
    )

    sc_cost_from_account_move = fields.Boolean(
        string="成本台账来源：凭证",
        default=True,
        config_parameter="smart_construction_core.sc_cost_from_account_move",
        help="勾选后凭证过账会写入项目成本台账。",
    )
    sc_cost_from_purchase = fields.Boolean(
        string="成本台账来源：采购",
        default=False,
        config_parameter="smart_construction_core.sc_cost_from_purchase",
        help="勾选后采购订单确认写入项目成本台账。",
    )
    sc_cost_from_stock = fields.Boolean(
        string="成本台账来源：入库",
        default=False,
        config_parameter="smart_construction_core.sc_cost_from_stock",
        help="勾选后入库完成写入项目成本台账。",
    )

    def set_values(self):
        res = super().set_values()
        # 软提醒：同一公司同时开启多个成本入口，可能导致重复计入
        for company in self.company_id or self.env.companies:
            params = self.env["ir.config_parameter"].sudo().with_company(company)
            flags = [
                params.get_param("smart_construction_core.sc_cost_from_account_move", default="False"),
                params.get_param("smart_construction_core.sc_cost_from_purchase", default="False"),
                params.get_param("smart_construction_core.sc_cost_from_stock", default="False"),
            ]
            enabled = sum(1 for v in flags if str(v).lower() in ("1", "true", "yes"))
            if enabled > 1:
                self.env['ir.logging'].sudo().create({
                    'name': 'CostLedgerConfigWarning',
                    'type': 'server',
                    'dbname': self._cr.dbname,
                    'level': 'WARNING',
                    'message': f"[{company.display_name}] 成本台账入口开启了多个来源，建议只保留一个以避免重复计入。",
                    'path': __name__,
                    'line': '0',
                    'func': 'set_values',
                })
        return res
