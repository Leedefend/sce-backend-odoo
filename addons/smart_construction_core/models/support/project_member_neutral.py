# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectMemberNeutral(models.Model):
    _name = "sc.project.member.staging"
    _description = "历史项目成员中性承载"
    _order = "project_id, user_id, id"

    legacy_member_id = fields.Char(
        string="旧系统成员ID",
        required=True,
        index=True,
        copy=False,
        help="旧系统 BASE_SYSTEM_PROJECT_USER.ID，用于迁移幂等、审计和回滚。",
    )
    legacy_project_id = fields.Char(
        string="旧系统项目ID",
        required=True,
        index=True,
        copy=False,
        help="旧系统 BASE_SYSTEM_PROJECT_USER.XMID。",
    )
    legacy_user_ref = fields.Char(
        string="旧系统用户标识",
        required=True,
        index=True,
        copy=False,
        help="旧系统 BASE_SYSTEM_PROJECT_USER.USERID。",
    )
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="restrict",
        help="已映射的新系统项目，仅作为迁移证据关联，不代表责任角色。",
    )
    user_id = fields.Many2one(
        "res.users",
        string="用户",
        required=True,
        index=True,
        ondelete="restrict",
        help="已映射的新系统用户，仅作为迁移证据关联，不进入 project.responsibility。",
    )
    legacy_role_text = fields.Char(
        string="旧系统角色文本",
        copy=False,
        help="旧系统角色文本；当前批次缺失，保留空值作为后续提升证据位。",
    )
    role_fact_status = fields.Selection(
        [
            ("missing", "缺失"),
            ("unverified", "未验证"),
            ("verified", "已验证"),
        ],
        string="角色事实状态",
        required=True,
        default="missing",
        index=True,
    )
    import_batch = fields.Char(
        string="导入批次",
        required=True,
        index=True,
        copy=False,
    )
    evidence = fields.Char(
        string="迁移证据",
        copy=False,
        help="记录来源文件、旧表或行号等证据。",
    )
    notes = fields.Text(
        string="说明",
        help="中性承载说明；不得作为责任、审批或权限推导依据。",
    )
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_member_import_batch_unique",
            "unique(legacy_member_id, import_batch)",
            "同一批次中旧系统成员ID不可重复。",
        )
    ]
