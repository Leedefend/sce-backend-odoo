# -*- coding: utf-8 -*-
from odoo import fields, models

from ..support.state_guard import raise_guard


class ProjectCostPeriod(models.Model):
    _name = "project.cost.period"
    _description = "项目成本期间"
    _order = "period desc, id desc"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
    )
    period = fields.Char("期间(YYYY-MM)", required=True, index=True)

    locked = fields.Boolean("已锁定", default=False, index=True)
    locked_by = fields.Many2one("res.users", string="锁定人", index=True)
    locked_at = fields.Datetime("锁定时间", index=True)
    lock_reason = fields.Text("锁定说明")

    _sql_constraints = [
        ("uniq_project_period", "unique(project_id, period)", "期间已存在"),
    ]

    def _audit_period(self, event_code, before_locked, after_locked, reason=None, require_reason=False):
        Audit = self.env["sc.audit.log"]
        for rec in self:
            Audit.write_event(
                event_code=event_code,
                model=rec._name,
                res_id=rec.id,
                action=event_code,
                before={"locked": before_locked},
                after={"locked": after_locked},
                reason=reason,
                require_reason=require_reason,
                project_id=rec.project_id.id if rec.project_id else False,
                company_id=rec.project_id.company_id.id if rec.project_id else False,
            )

    def action_lock_period(self, reason=None):
        for rec in self:
            before_locked = rec.locked
            rec.write(
                {
                    "locked": True,
                    "locked_by": self.env.user.id,
                    "locked_at": fields.Datetime.now(),
                    "lock_reason": reason or False,
                }
            )
            rec._audit_period(
                "period_locked",
                before_locked=before_locked,
                after_locked=True,
                reason=reason,
                require_reason=False,
            )
        return True

    def action_unlock_period(self, reason=None):
        for rec in self:
            if not reason:
                raise_guard(
                    "AUDIT_REASON_REQUIRED",
                    "Audit",
                    "Write",
                    reasons=["reason is required"],
                )
            before_locked = rec.locked
            rec.write(
                {
                    "locked": False,
                    "locked_by": False,
                    "locked_at": False,
                    "lock_reason": False,
                }
            )
            rec._audit_period(
                "period_unlocked",
                before_locked=before_locked,
                after_locked=False,
                reason=reason,
                require_reason=True,
            )
        return True
