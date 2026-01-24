# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .state_machine import ScStateMachine


class ScProjectStageRequirementWizard(models.TransientModel):
    _name = "sc.project.stage.requirement.wizard"
    _description = "项目阶段要求"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        readonly=True,
    )
    lifecycle_state = fields.Selection(
        ScStateMachine.selection(ScStateMachine.PROJECT),
        string="当前阶段",
        readonly=True,
    )
    checklist = fields.Text(
        string="阶段要求",
        compute="_compute_checklist",
        readonly=True,
    )

    @api.depends("project_id", "project_id.lifecycle_state", "lifecycle_state")
    def _compute_checklist(self):
        for rec in self:
            state = rec.lifecycle_state or rec.project_id.lifecycle_state
            rec.lifecycle_state = state
            rec.checklist = "\n".join(self._get_checklist_lines(state))

    def _get_checklist_lines(self, state):
        checklist_map = {
            "draft": [
                "补齐项目基本信息（名称、业主、负责人/经理）",
                "确定项目地点与类型",
                "准备合同与预算基础信息",
            ],
            "in_progress": [
                "持续更新项目任务与执行结构",
                "维护成本台账与付款申请",
                "跟踪合同执行与项目进度",
            ],
        }
        return checklist_map.get(state, ["暂无阶段要求"])
