# -*- coding: utf-8 -*-
from odoo import api, fields, models

from ..support.state_guard import raise_guard


class ProjectProgressEntry(models.Model):
    _name = "project.progress.entry"
    _description = "项目进度计量记录"
    _order = "date desc, id desc"

    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submitted", "已提交"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
    )

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
    )
    wbs_id = fields.Many2one(
        "construction.work.breakdown",
        string="工程结构(WBS)",
        required=True,
        index=True,
    )

    date = fields.Date("计量日期", default=fields.Date.context_today, index=True)

    qty_done = fields.Float("本期完成工程量")
    qty_cum = fields.Float("累计完成工程量", help="可通过定时任务自动更新")

    progress_rate = fields.Float("累计完成比例(%)")
    note = fields.Char("备注")

    def _ensure_manager_role(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_project_manager"):
            raise_guard(
                "PROGRESS_GUARD_ROLE_REQUIRED",
                "Progress Entry",
                "Revert",
                reasons=["manager role required"],
            )

    def _ensure_immutable(self, operation_label="Write"):
        for rec in self:
            if rec.state == "submitted" and not self.env.context.get("allow_progress_edit"):
                raise_guard(
                    "PROGRESS_GUARD_IMMUTABLE",
                    rec.display_name or "Progress Entry",
                    operation_label,
                    reasons=["submitted record is immutable"],
                )

    def _ensure_no_direct_state_write(self, vals):
        if "state" in vals and not self.env.context.get("allow_progress_transition"):
            raise_guard(
                "PROGRESS_GUARD_DIRECT_STATE_WRITE",
                "Progress Entry",
                "Write",
                reasons=["state change must use transition methods"],
            )

    def _audit_transition(self, event_code, action, before_state, after_state, reason=None, require_reason=False):
        Audit = self.env["sc.audit.log"]
        for rec in self:
            Audit.write_event(
                event_code=event_code,
                model=rec._name,
                res_id=rec.id,
                action=action,
                before={
                    "state": before_state,
                    "progress_rate": rec.progress_rate,
                    "qty_done": rec.qty_done,
                    "qty_cum": rec.qty_cum,
                },
                after={
                    "state": after_state,
                    "progress_rate": rec.progress_rate,
                    "qty_done": rec.qty_done,
                    "qty_cum": rec.qty_cum,
                },
                reason=reason,
                require_reason=require_reason,
                project_id=rec.project_id.id if rec.project_id else False,
                company_id=rec.project_id.company_id.id if rec.project_id else False,
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._ensure_no_direct_state_write(vals)
        project_ids = {vals.get("project_id") for vals in vals_list if vals.get("project_id")}
        if project_ids:
            projects = self.env["project.project"].browse(project_ids)
            projects._ensure_operation_allowed(
                operation_label="新增进度计量",
                blocked_states=("paused", "closed", "closing"),
            )
        return super().create(vals_list)

    def write(self, vals):
        self._ensure_no_direct_state_write(vals)
        self._ensure_immutable("Write")
        return super().write(vals)

    def unlink(self):
        self._ensure_immutable("Delete")
        return super().unlink()

    def action_submit_progress(self):
        for rec in self:
            if rec.project_id:
                rec.project_id._ensure_operation_allowed(
                    operation_label="提交进度计量",
                    blocked_states=("paused", "closed", "closing"),
                )
            rec._ensure_immutable("Submit")
            before_state = rec.state
            rec.with_context(allow_progress_transition=True, allow_progress_edit=True).write(
                {"state": "submitted"}
            )
            rec._audit_transition("progress_submitted", "action_submit_progress", before_state, "submitted")
        return True

    def action_revert_progress(self, reason=None):
        self._ensure_manager_role()
        for rec in self:
            before_state = rec.state
            rec.with_context(allow_progress_transition=True, allow_progress_edit=True).write(
                {"state": "draft"}
            )
            rec._audit_transition(
                "progress_reverted",
                "action_revert_progress",
                before_state,
                "draft",
                reason=reason,
                require_reason=True,
            )
        return True
