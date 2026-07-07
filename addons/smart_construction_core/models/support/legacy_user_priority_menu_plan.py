# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyUserPriorityMenuPlan(models.Model):
    _name = "sc.legacy.user.priority.menu.plan"
    _description = "历史系统用户优先入口迭代计划"
    _order = "priority_sequence, legacy_menu_group, legacy_menu_name"

    priority_sequence = fields.Integer(string="优先级", required=True, index=True)
    source_document = fields.Char(string="来源文档", required=True, index=True)
    screenshot_ref = fields.Char(string="截图来源", index=True)
    legacy_menu_group = fields.Char(string="历史系统菜单分组", required=True, index=True)
    legacy_menu_name = fields.Char(string="历史系统入口", required=True, index=True)
    business_domain = fields.Char(string="业务域", index=True)
    target_model = fields.Char(string="主承载模型", index=True)
    target_model_id = fields.Many2one("ir.model", string="主承载模型记录", ondelete="set null", index=True)
    target_action_id = fields.Many2one("ir.actions.act_window", string="承载动作", ondelete="set null", index=True)
    target_view_id = fields.Many2one("ir.ui.view", string="承载视图", ondelete="set null", index=True)
    candidate_models_json = fields.Json(string="候选承载模型", default=list)
    list_field_contract = fields.Json(string="列表字段契约", default=list)
    search_contract = fields.Json(string="搜索/排序契约", default=dict)
    form_section_contract = fields.Json(string="表单分区契约", default=list)
    default_order = fields.Char(string="默认排序")
    attachment_required = fields.Boolean(string="要求附件区", default=True)
    chatter_required = fields.Boolean(string="要求日志区", default=True)
    surface_contract_status = fields.Selection(
        [
            ("pending", "待结构化"),
            ("runtime_spec_landed", "运行态规格已落地"),
            ("view_gap_audit_required", "待视图差异审计"),
            ("view_aligned", "视图已对齐"),
        ],
        string="可见面契约状态",
        default="pending",
        required=True,
        index=True,
    )
    runtime_gap_summary = fields.Text(string="运行态差异摘要")
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
    old_system_path = fields.Char(string="历史系统路径")
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
            "同一来源文档、菜单分组、历史系统入口只能形成一条用户优先计划。",
        ),
    ]
