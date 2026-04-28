# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class ScLegacyReportInventory(models.Model):
    _name = "sc.legacy.report.inventory"
    _description = "旧库报表承载清单"
    _order = "priority, click_count desc, name"
    _rec_name = "name"

    name = fields.Char(string="报表名称", required=True, index=True)
    legacy_function_id = fields.Char(string="旧功能编号", index=True)
    legacy_config_id = fields.Char(string="旧配置编号", index=True)
    legacy_url = fields.Char(string="旧入口")
    source_kind = fields.Selection(
        [
            ("lowcode_proc", "低代码存储过程"),
            ("lowcode_sql", "低代码SQL"),
            ("lowcode_sqlid", "低代码SQLID"),
            ("lowcode_list", "低代码列表"),
            ("legacy_page_proc", "旧页面存储过程"),
            ("legacy_page", "旧页面"),
        ],
        string="旧实现方式",
        required=True,
        default="legacy_page",
        index=True,
    )
    priority = fields.Selection(
        [("p0", "P0"), ("p1", "P1"), ("p2", "P2")],
        string="优先级",
        required=True,
        default="p1",
        index=True,
    )
    domain_group = fields.Selection(
        [
            ("ar_ap", "应收应付"),
            ("treasury", "资金收支"),
            ("operation", "经营统计"),
            ("cost", "成本"),
            ("contract", "合同履约"),
            ("invoice", "发票税务"),
            ("material", "材料库存"),
            ("expense", "费用报销"),
            ("other", "其他"),
        ],
        string="业务域",
        required=True,
        default="other",
        index=True,
    )
    click_count = fields.Integer(string="点击次数", index=True)
    user_count = fields.Integer(string="使用人数")
    last_click_date = fields.Date(string="最近使用日期", index=True)
    procedure_name = fields.Char(string="存储过程")
    sql_id = fields.Char(string="SQL编号")
    source_tables = fields.Text(string="依赖旧表")
    parameter_summary = fields.Text(string="参数")
    metric_summary = fields.Text(string="指标口径")
    target_model = fields.Char(string="新系统承载模型")
    carrier_status = fields.Selection(
        [
            ("ready", "已有事实基础"),
            ("partial", "部分具备"),
            ("gap", "存在缺口"),
            ("investigate", "待拆解"),
        ],
        string="承载状态",
        required=True,
        default="investigate",
        index=True,
    )
    next_action = fields.Text(string="下一步动作")
    evidence = fields.Text(string="旧库证据")
    active = fields.Boolean(default=True, index=True)

    def write(self, vals):
        protected_fields = {
            "name",
            "legacy_function_id",
            "legacy_config_id",
            "source_kind",
            "priority",
            "domain_group",
            "click_count",
            "user_count",
            "last_click_date",
            "procedure_name",
            "sql_id",
            "source_tables",
            "parameter_summary",
            "metric_summary",
            "target_model",
            "carrier_status",
            "next_action",
            "evidence",
        }
        allow_baseline_write = (
            self.env.context.get("allow_legacy_report_inventory_write")
            or self.env.context.get("install_mode")
            or self.env.context.get("module")
        )
        if protected_fields.intersection(vals) and not allow_baseline_write:
            raise UserError("旧库报表承载清单由迁移基线维护，业务端不可直接修改。")
        return super().write(vals)

    def unlink(self):
        if not self.env.context.get("allow_legacy_report_inventory_write"):
            raise UserError("旧库报表承载清单由迁移基线维护，业务端不可直接删除。")
        return super().unlink()
