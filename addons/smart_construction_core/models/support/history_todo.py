# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class ScHistoryTodo(models.Model):
    _name = "sc.history.todo"
    _description = "Historical Workflow Todo"
    _order = "state, priority desc, received_at desc, approved_at desc, id desc"

    name = fields.Char(required=True, index=True)
    state = fields.Selection(
        [
            ("todo", "待处理"),
            ("acknowledged", "已确认"),
            ("resolved", "已处理"),
            ("archived", "已归档"),
        ],
        default="todo",
        required=True,
        index=True,
    )
    priority = fields.Integer(default=10, index=True)
    workflow_audit_id = fields.Many2one("sc.legacy.workflow.audit", required=True, index=True, ondelete="cascade")
    legacy_workflow_id = fields.Char(index=True)
    legacy_source_table = fields.Char(index=True)
    target_lane = fields.Char(index=True)
    target_model = fields.Char(index=True)
    target_external_id = fields.Char(index=True)
    target_res_model = fields.Char(index=True)
    target_res_id = fields.Integer(index=True)
    actor_legacy_user_id = fields.Char(index=True)
    actor_name = fields.Char(index=True)
    legacy_step_name = fields.Char(index=True)
    legacy_template_name = fields.Char(index=True)
    action_classification = fields.Char(index=True)
    legacy_status = fields.Char(index=True)
    legacy_approval_type = fields.Char(index=True)
    received_at = fields.Datetime(index=True)
    approved_at = fields.Datetime(index=True)
    approval_note = fields.Text()
    resolution_note = fields.Text()
    acknowledged_by_id = fields.Many2one("res.users", index=True, ondelete="set null")
    acknowledged_at = fields.Datetime(index=True)
    resolved_by_id = fields.Many2one("res.users", index=True, ondelete="set null")
    resolved_at = fields.Datetime(index=True)
    source_table = fields.Char(default="sc.legacy.workflow.audit", required=True, index=True)

    _sql_constraints = [
        ("history_todo_workflow_audit_unique", "unique(workflow_audit_id)", "Historical workflow todo already exists."),
    ]

    def _require_finance_user(self):
        if not (
            self.env.user.has_group("smart_construction_core.group_sc_cap_finance_user")
            or self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager")
            or self.env.user.has_group("smart_construction_core.group_sc_cap_config_admin")
        ):
            raise UserError(_("You do not have permission to update historical workflow todos."))

    def action_acknowledge(self):
        self._require_finance_user()
        now = fields.Datetime.now()
        self.filtered(lambda rec: rec.state == "todo").write(
            {"state": "acknowledged", "acknowledged_by_id": self.env.user.id, "acknowledged_at": now}
        )

    def action_resolve(self):
        self._require_finance_user()
        now = fields.Datetime.now()
        self.write({"state": "resolved", "resolved_by_id": self.env.user.id, "resolved_at": now})

    def action_archive(self):
        self._require_finance_user()
        self.write({"state": "archived"})

    def action_reset_todo(self):
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager"):
            raise UserError(_("Only finance managers can reopen historical workflow todos."))
        self.write({"state": "todo", "resolved_by_id": False, "resolved_at": False})

    def action_open_source_audit(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("历史审批审计"),
            "res_model": "sc.legacy.workflow.audit",
            "res_id": self.workflow_audit_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_open_target_record(self):
        self.ensure_one()
        if not self.target_res_model or not self.target_res_id:
            raise UserError(_("This historical todo has no resolved target record."))
        return {
            "type": "ir.actions.act_window",
            "name": _("目标业务记录"),
            "res_model": self.target_res_model,
            "res_id": self.target_res_id,
            "view_mode": "form",
            "target": "current",
        }
