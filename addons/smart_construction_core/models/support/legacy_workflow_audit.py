# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ScLegacyWorkflowAudit(models.Model):
    _name = "sc.legacy.workflow.audit"
    _description = "Legacy Workflow Audit Fact"
    _order = "approved_at desc, received_at desc, id desc"
    _rec_name = "name"

    name = fields.Char(
        string="审计摘要",
        compute="_compute_name",
        store=True,
    )
    legacy_workflow_id = fields.Char(
        string="旧审批记录ID",
        required=True,
        index=True,
        copy=False,
        help="旧系统 S_Execute_Approval.Id，用于迁移幂等、审计和回放。",
    )
    legacy_pid = fields.Char(string="旧系统PID", index=True, copy=False)
    legacy_djid = fields.Char(
        string="旧系统业务单据ID",
        required=True,
        index=True,
        copy=False,
        help="旧系统 DJID，是历史审批事实锚定目标业务单据的主依据。",
    )
    legacy_business_id = fields.Char(
        string="旧系统流程业务ID",
        index=True,
        copy=False,
        help="旧系统 business_Id，保留为流程/配置上下文来源，不作为目标单据唯一依据。",
    )
    legacy_source_table = fields.Char(string="旧系统来源表", index=True, copy=False)
    legacy_detail_status_id = fields.Char(string="旧流程状态ID", index=True, copy=False)
    legacy_detail_step_id = fields.Char(string="旧流程明细步骤ID", index=True, copy=False)
    legacy_setup_step_id = fields.Char(string="旧流程步骤ID", index=True, copy=False)
    legacy_template_id = fields.Char(string="旧流程模板ID", index=True, copy=False)
    legacy_step_name = fields.Char(string="旧流程步骤名称", copy=False)
    legacy_template_name = fields.Char(string="旧流程模板名称", copy=False)

    target_model = fields.Char(
        string="目标模型",
        required=True,
        index=True,
        copy=False,
        help="新系统目标业务模型名；迁移资产使用 external id 锚定，不依赖数据库整数ID。",
    )
    target_external_id = fields.Char(
        string="目标外部ID",
        required=True,
        index=True,
        copy=False,
        help="目标业务记录的稳定 external id，用于 XML 重放和审计追踪。",
    )
    target_lane = fields.Selection(
        [
            ("actual_outflow", "实际支出"),
            ("contract", "业主合同"),
            ("outflow_request", "付款申请"),
            ("receipt", "收款申请"),
            ("supplier_contract", "供应商合同"),
        ],
        string="目标资产泳道",
        required=True,
        index=True,
    )

    actor_legacy_user_id = fields.Char(string="旧审批人ID", index=True, copy=False)
    actor_name = fields.Char(string="旧审批人", index=True, copy=False)
    approved_at = fields.Datetime(string="旧审批时间", index=True)
    received_at = fields.Datetime(string="旧接收时间", index=True)
    approval_note = fields.Text(string="旧审批意见")

    action_classification = fields.Selection(
        [
            ("unknown", "未知/原样保留"),
            ("approve", "疑似同意"),
            ("reject_or_back", "疑似退回"),
            ("reject_or_cancel", "疑似拒绝/取消"),
        ],
        string="动作归类",
        default="unknown",
        required=True,
        index=True,
        help="只作为旧数据筛选归类，不驱动新系统审批状态。",
    )
    legacy_status = fields.Char(
        string="旧审批状态",
        index=True,
        copy=False,
        help="旧系统 f_SPZT 原值；不得直接解释为新系统 approval state。",
    )
    legacy_back_type = fields.Char(
        string="旧退回类型",
        index=True,
        copy=False,
        help="旧系统 f_Back_YJLX 原值；不得直接解释为新系统 rejection state。",
    )
    legacy_approval_type = fields.Char(string="旧审批类型", index=True, copy=False)

    import_batch = fields.Char(
        string="导入批次",
        default="legacy_workflow_audit_asset_v1",
        required=True,
        index=True,
        copy=False,
    )
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "uniq_legacy_wf_batch",
            "unique(legacy_workflow_id, import_batch)",
            "同一批次中旧审批记录ID不可重复。",
        )
    ]

    @api.depends("actor_name", "action_classification", "target_lane", "approved_at", "legacy_workflow_id")
    def _compute_name(self):
        for rec in self:
            actor = rec.actor_name or "旧审批人"
            action = dict(rec._fields["action_classification"].selection).get(rec.action_classification) or "审批事实"
            lane = dict(rec._fields["target_lane"].selection).get(rec.target_lane) or rec.target_lane or "业务单据"
            date_text = fields.Datetime.to_string(rec.approved_at) if rec.approved_at else ""
            suffix = (" - %s" % date_text) if date_text else ""
            rec.name = "%s / %s / %s%s" % (actor, action, lane, suffix)

    @api.constrains("target_model", "target_external_id")
    def _check_target_anchor(self):
        for rec in self:
            if not (rec.target_model or "").strip() or not (rec.target_external_id or "").strip():
                raise ValidationError("历史审批审计事实必须保留目标模型和目标外部ID。")

    @api.constrains("legacy_workflow_id", "legacy_djid")
    def _check_legacy_anchor(self):
        for rec in self:
            if not (rec.legacy_workflow_id or "").strip() or not (rec.legacy_djid or "").strip():
                raise ValidationError("历史审批审计事实必须保留旧审批记录ID和旧业务单据ID。")
