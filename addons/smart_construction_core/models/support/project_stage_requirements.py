# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .state_machine import ScStateMachine


class ScProjectStageRequirementItem(models.Model):
    _name = "sc.project.stage.requirement.item"
    _description = "项目阶段要求项"
    _order = "lifecycle_state, sequence, id"

    name = fields.Char("要求项", required=True)
    active = fields.Boolean("启用", default=True)
    sequence = fields.Integer("排序", default=10)
    lifecycle_state = fields.Selection(
        ScStateMachine.selection(ScStateMachine.PROJECT),
        string="生命周期阶段",
        required=True,
        index=True,
    )
    required = fields.Boolean("必做", default=True)
    action_xmlid = fields.Char(
        "执行动作(XMLID)",
        help="可选：点击去完成时跳转的动作 XMLID",
    )


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
    line_ids = fields.One2many(
        "sc.project.stage.requirement.wizard.line",
        "wizard_id",
        string="阶段要求",
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        project_id = res.get("project_id") or self.env.context.get("default_project_id")
        if not project_id:
            return res
        project = self.env["project.project"].browse(project_id)
        state = res.get("lifecycle_state") or project.lifecycle_state
        res["lifecycle_state"] = state

        items = self.env["sc.project.stage.requirement.item"].search(
            [
                ("active", "=", True),
                ("lifecycle_state", "=", state),
            ],
            order="sequence, id",
        )
        res["line_ids"] = [
            (0, 0, {
                "project_id": project.id,
                "lifecycle_state": state,
                "sequence": item.sequence,
                "name": item.name,
                "required": item.required,
                "action_xmlid": item.action_xmlid or False,
            })
            for item in items
        ]
        return res


class ScProjectStageRequirementWizardLine(models.TransientModel):
    _name = "sc.project.stage.requirement.wizard.line"
    _description = "项目阶段要求行"
    _order = "sequence, id"

    wizard_id = fields.Many2one(
        "sc.project.stage.requirement.wizard",
        string="向导",
        required=True,
        ondelete="cascade",
    )
    project_id = fields.Many2one("project.project", string="项目", readonly=True)
    lifecycle_state = fields.Selection(
        ScStateMachine.selection(ScStateMachine.PROJECT),
        string="生命周期阶段",
        readonly=True,
    )
    sequence = fields.Integer("排序", readonly=True)
    name = fields.Char("要求项", readonly=True)
    required = fields.Boolean("必做", readonly=True)
    action_xmlid = fields.Char("执行动作", readonly=True)

    def action_go(self):
        self.ensure_one()
        if not self.action_xmlid:
            return False
        try:
            action = self.env.ref(self.action_xmlid).read()[0]
        except Exception:
            return False
        ctx = dict(action.get("context") or {})
        if self.project_id:
            ctx.setdefault("default_project_id", self.project_id.id)
            ctx.setdefault("search_default_project_id", self.project_id.id)
        action["context"] = ctx
        return action
