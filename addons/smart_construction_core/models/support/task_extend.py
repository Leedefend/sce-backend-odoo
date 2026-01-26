# -*- coding: utf-8 -*-
import json

from odoo import api, fields, models

from .state_guard import raise_guard


class ProjectTask(models.Model):
    _inherit = "project.task"

    sc_state = fields.Selection(
        [
            ("draft", "草稿"),
            ("ready", "就绪"),
            ("in_progress", "进行中"),
            ("done", "已完成"),
            ("cancelled", "已取消"),
        ],
        string="工程状态",
        default="draft",
        required=True,
        index=True,
    )

    readiness_status = fields.Selection(
        [
            ("ready", "就绪"),
            ("blocked", "阻断"),
            ("missing", "缺失"),
        ],
        string="就绪状态",
        compute="_compute_readiness",
        store=False,
    )
    readiness_missing_fields = fields.Text(
        string="就绪缺失字段",
        compute="_compute_readiness",
        store=False,
    )
    readiness_blockers = fields.Text(
        string="就绪阻断项",
        compute="_compute_readiness",
        store=False,
    )

    boq_generated = fields.Boolean("来源: BOQ聚合", default=False, index=True)
    boq_group_key = fields.Char("BOQ分组键", index=True)
    boq_section_type = fields.Selection(
        [
            ("building", "建筑"),
            ("installation", "安装/机电"),
            ("decoration", "装饰"),
            ("landscape", "景观"),
            ("other", "其他"),
        ],
        string="工程类别",
        index=True,
    )
    work_id = fields.Many2one(
        "construction.work.breakdown",
        string="工程结构节点",
        ondelete="set null",
        index=True,
    )
    boq_line_ids = fields.Many2many(
        "project.boq.line",
        "project_task_boq_rel",
        "task_id",
        "boq_id",
        string="关联BOQ行",
        readonly=True,
    )
    boq_uom_id = fields.Many2one("uom.uom", string="工程量单位", readonly=True)

    boq_quantity_total = fields.Float(
        "BOQ工程量",
        compute="_compute_boq_totals",
        store=True,
        readonly=True,
    )
    boq_amount_total = fields.Monetary(
        "BOQ合价汇总",
        currency_field="currency_id",
        compute="_compute_boq_totals",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="project_id.company_id.currency_id",
        store=True,
        readonly=True,
    )

    def _compute_boq_totals(self):
        for task in self:
            qty = sum(task.boq_line_ids.mapped("quantity"))
            amount = sum(task.boq_line_ids.mapped("amount"))
            task.boq_quantity_total = qty
            task.boq_amount_total = amount
            task.boq_uom_id = task.boq_line_ids[:1].uom_id.id if task.boq_line_ids else False

    @api.depends("project_id", "work_id", "sc_state")
    def _compute_readiness(self):
        for task in self:
            missing_fields, blockers = task._get_readiness_state()
            if blockers:
                task.readiness_status = "blocked"
            elif missing_fields:
                task.readiness_status = "missing"
            else:
                task.readiness_status = "ready"
            task.readiness_missing_fields = json.dumps(missing_fields, ensure_ascii=False)
            task.readiness_blockers = json.dumps(blockers, ensure_ascii=False)

    def _get_readiness_state(self):
        missing_fields = []
        blockers = []

        if not self.project_id:
            missing_fields.append("project_id")

        if "work_id" in self._fields and self.project_id:
            if "wbs_ready" in self.project_id._fields and self.project_id.wbs_ready:
                if not self.work_id:
                    missing_fields.append("work_id")

        if self.project_id and "lifecycle_state" in self.project_id._fields:
            if self.project_id.lifecycle_state in ("paused", "closed"):
                blockers.append("project.lifecycle_state")

        return missing_fields, blockers

    def _get_progress_ratio(self):
        if "progress_rate" in self._fields:
            return self.progress_rate or 0.0
        if "progress" in self._fields:
            return self.progress or 0.0
        return None

    def _audit_transition(self, event_code, action, before_state, after_state, reason=None):
        Audit = self.env["sc.audit.log"]
        for task in self:
            Audit.write_event(
                event_code=event_code,
                model=task._name,
                res_id=task.id,
                action=action,
                before={"sc_state": before_state},
                after={"sc_state": after_state},
                reason=reason,
                require_reason=(event_code == "task_cancelled"),
                project_id=task.project_id.id if task.project_id else False,
                company_id=task.project_id.company_id.id if task.project_id else False,
            )

    def _ensure_manager_role(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_project_manager"):
            raise_guard(
                "TASK_GUARD_ROLE_REQUIRED",
                "Task",
                "Cancel",
                reasons=["manager role required"],
            )

    def _ensure_no_direct_state_write(self, vals):
        if "sc_state" in vals and not self.env.context.get("allow_transition"):
            raise_guard(
                "TASK_GUARD_DIRECT_STATE_WRITE",
                "Task",
                "Write",
                reasons=["sc_state change must use transition methods"],
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._ensure_no_direct_state_write(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._ensure_no_direct_state_write(vals)
        return super().write(vals)

    def action_prepare_task(self):
        for task in self:
            if task.sc_state != "draft":
                raise_guard(
                    "TASK_GUARD_MISSING_FIELDS",
                    task.display_name,
                    "Prepare",
                    reasons=["sc_state must be draft"],
                )
            missing_fields, blockers = task._get_readiness_state()
            if blockers:
                raise_guard(
                    "TASK_GUARD_PROJECT_BLOCKED",
                    task.display_name,
                    "Prepare",
                    reasons=blockers,
                )
            if missing_fields:
                raise_guard(
                    "TASK_GUARD_MISSING_FIELDS",
                    task.display_name,
                    "Prepare",
                    reasons=missing_fields,
                )
            before_state = task.sc_state
            task.with_context(allow_transition=True).write({"sc_state": "ready"})
            task._audit_transition("task_ready", "action_prepare_task", before_state, "ready")
        return True

    def action_start_task(self):
        for task in self:
            if task.sc_state != "ready":
                raise_guard(
                    "TASK_GUARD_PROJECT_BLOCKED",
                    task.display_name,
                    "Start",
                    reasons=["sc_state must be ready"],
                )
            if task.project_id and "lifecycle_state" in task.project_id._fields:
                if task.project_id.lifecycle_state in ("paused", "closed"):
                    raise_guard(
                        "TASK_GUARD_PROJECT_BLOCKED",
                        task.display_name,
                        "Start",
                        reasons=["project is paused/closed"],
                    )
            before_state = task.sc_state
            task.with_context(allow_transition=True).write({"sc_state": "in_progress"})
            task._audit_transition("task_started", "action_start_task", before_state, "in_progress")
        return True

    def action_mark_done(self):
        for task in self:
            if task.sc_state != "in_progress":
                raise_guard(
                    "TASK_GUARD_NOT_COMPLETE",
                    task.display_name,
                    "Complete",
                    reasons=["sc_state must be in_progress"],
                )
            progress = task._get_progress_ratio()
            if progress is not None and progress < 1.0:
                raise_guard(
                    "TASK_GUARD_NOT_COMPLETE",
                    task.display_name,
                    "Complete",
                    reasons=["progress not complete"],
                )
            before_state = task.sc_state
            task.with_context(allow_transition=True).write({"sc_state": "done"})
            task._audit_transition("task_done", "action_mark_done", before_state, "done")
        return True

    def action_cancel_task(self, reason=None):
        self._ensure_manager_role()
        for task in self:
            before_state = task.sc_state
            task.with_context(allow_transition=True).write({"sc_state": "cancelled"})
            task._audit_transition(
                "task_cancelled",
                "action_cancel_task",
                before_state,
                "cancelled",
                reason=reason,
            )
        return True
