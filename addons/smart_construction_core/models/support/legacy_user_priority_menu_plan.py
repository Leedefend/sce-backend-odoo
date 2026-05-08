# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyUserPriorityMenuPlan(models.Model):
    _name = "sc.legacy.user.priority.menu.plan"
    _description = "历史系统用户优先入口迭代计划"
    _order = "priority_sequence, legacy_menu_group, legacy_menu_name"

    priority_sequence = fields.Integer(string="优先级", required=True, index=True)
    source_document = fields.Char(string="来源文档", required=True, index=True)
    screenshot_ref = fields.Char(string="截图来源", index=True)
    legacy_menu_group = fields.Char(string="老系统菜单分组", required=True, index=True)
    legacy_menu_name = fields.Char(string="老系统入口", required=True, index=True)
    business_domain = fields.Char(string="业务域", index=True)
    current_round_action = fields.Selection(
        [
            ("plan_fact_landed", "本轮计划事实落库"),
            ("specialized_carrier_exists", "已有专题承接"),
            ("next_topic_required", "下轮专题实现"),
        ],
        string="本轮动作",
        default="plan_fact_landed",
        required=True,
        index=True,
    )
    target_iteration = fields.Char(string="目标迭代", index=True)
    old_system_path = fields.Char(string="老系统路径")
    legacy_source_tables = fields.Text(string="旧表线索")
    legacy_field_list = fields.Text(string="字段列表线索")
    extracted_evidence = fields.Text(string="提取证据")
    next_development_topic = fields.Char(string="下一轮专题")
    next_scope = fields.Text(string="下一轮实现范围")
    replay_status = fields.Selection(
        [("pending", "待重放"), ("replayed", "已重放"), ("verified", "已验证")],
        string="重放状态",
        default="pending",
        required=True,
        index=True,
    )
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_user_priority_menu_plan_unique",
            "unique(source_document, legacy_menu_group, legacy_menu_name)",
            "同一来源文档、菜单分组、老系统入口只能形成一条用户优先计划。",
        ),
    ]
