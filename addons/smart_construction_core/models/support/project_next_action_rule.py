# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ScProjectNextActionRule(models.Model):
    _name = "sc.project.next_action.rule"
    _description = "项目下一步行动规则"
    _order = "sequence, id"

    name = fields.Char("动作名称", required=True)
    active = fields.Boolean("启用", default=True)
    sequence = fields.Integer("排序", default=10)

    lifecycle_state = fields.Selection(
        selection=lambda self: self.env["project.project"]._fields["lifecycle_state"].selection,
        string="生命周期阶段",
        required=True,
        index=True,
    )
    condition_expr = fields.Text(
        "条件表达式",
        help="安全表达式，支持变量：p(项目)、s(统计)、u(当前用户)。为空表示始终可用。",
    )

    action_type = fields.Selection(
        [
            ("act_window_xmlid", "窗口动作(XMLID)"),
            ("object_method", "对象方法"),
        ],
        string="动作类型",
        required=True,
        default="act_window_xmlid",
    )
    action_ref = fields.Char(
        "动作引用",
        required=True,
        help="窗口动作填 XMLID，对象方法填方法名",
    )
    hint_template = fields.Char(
        "提示模板",
        help="可使用 {contract_count}/{cost_count}/{payment_count}/{payment_pending}/{task_count}/{task_in_progress} 变量",
    )

    @api.model
    def _get_debug_flag(self):
        return bool(self.env.context.get("sc_next_action_debug"))
