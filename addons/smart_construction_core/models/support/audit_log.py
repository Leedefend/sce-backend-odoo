# -*- coding: utf-8 -*-
import json
import uuid

from odoo import api, fields, models

from .state_guard import raise_guard


class ScAuditLog(models.Model):
    _name = "sc.audit.log"
    _description = "SC Audit Log"

    event_code = fields.Char(string="Event Code", required=True, index=True)
    action = fields.Char(string="Action")
    model = fields.Char(string="Model", required=True, index=True)
    res_id = fields.Integer(string="Record ID", required=True, index=True)
    actor_uid = fields.Many2one("res.users", string="Actor", required=True, index=True)
    actor_login = fields.Char(string="Actor Login")
    ts = fields.Datetime(string="Timestamp", default=fields.Datetime.now, index=True)
    before_json = fields.Text(string="Before (JSON)")
    after_json = fields.Text(string="After (JSON)")
    reason = fields.Text(string="Reason")
    trace_id = fields.Char(string="Trace ID", index=True)
    company_id = fields.Many2one("res.company", string="Company", index=True)
    project_id = fields.Many2one("project.project", string="Project", index=True)

    @api.model
    def write_event(
        self,
        event_code,
        model,
        res_id,
        action=None,
        before=None,
        after=None,
        reason=None,
        require_reason=False,
        trace_id=None,
        company_id=None,
        project_id=None,
        actor_uid=None,
        actor_login=None,
    ):
        if require_reason and not reason:
            raise_guard(
                "AUDIT_REASON_REQUIRED",
                "Audit",
                "Write",
                reasons=["reason is required"],
            )

        def _to_json(value):
            if value is None:
                return False
            if isinstance(value, str):
                return value
            try:
                return json.dumps(value, ensure_ascii=True)
            except TypeError:
                return json.dumps({"value": str(value)}, ensure_ascii=True)

        actor = actor_uid or self.env.user
        payload = {
            "event_code": event_code,
            "action": action,
            "model": model,
            "res_id": int(res_id) if res_id is not None else 0,
            "actor_uid": actor.id,
            "actor_login": actor_login or actor.login,
            "ts": fields.Datetime.now(),
            "before_json": _to_json(before),
            "after_json": _to_json(after),
            "reason": reason,
            "trace_id": trace_id or uuid.uuid4().hex,
            "company_id": company_id.id if isinstance(company_id, models.BaseModel) else company_id,
            "project_id": project_id.id if isinstance(project_id, models.BaseModel) else project_id,
        }
        return self.sudo().create(payload)
