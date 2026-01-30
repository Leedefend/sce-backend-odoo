# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, fields, models


class ScSubscriptionPlan(models.Model):
    _name = "sc.subscription.plan"
    _description = "SC Subscription Plan"
    _order = "sequence, id"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    description = fields.Text()
    feature_flags_json = fields.Json()
    limits_json = fields.Json()

    _sql_constraints = [
        ("sc_subscription_plan_code_uniq", "unique(code)", "Plan code must be unique."),
    ]


class ScSubscription(models.Model):
    _name = "sc.subscription"
    _description = "SC Subscription"
    _order = "start_date desc, id desc"

    company_id = fields.Many2one("res.company", required=True, ondelete="cascade")
    plan_id = fields.Many2one("sc.subscription.plan", required=True, ondelete="restrict")
    state = fields.Selection(
        [("trial", "Trial"), ("active", "Active"), ("paused", "Paused"), ("canceled", "Canceled")],
        default="trial",
        required=True,
    )
    start_date = fields.Date(default=fields.Date.context_today)
    end_date = fields.Date()
    is_trial = fields.Boolean(default=True)
    note = fields.Char()


class ScEntitlement(models.Model):
    _name = "sc.entitlement"
    _description = "SC Entitlement"
    _order = "updated_at desc, id desc"

    company_id = fields.Many2one("res.company", required=True, ondelete="cascade")
    plan_id = fields.Many2one("sc.subscription.plan", ondelete="set null")
    effective_flags_json = fields.Json()
    effective_limits_json = fields.Json()
    updated_at = fields.Datetime()

    _sql_constraints = [
        ("sc_entitlement_company_uniq", "unique(company_id)", "Entitlement per company must be unique."),
    ]

    @api.model
    def _default_plan(self):
        code = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sc.subscription.default_plan_code", "default")
        )
        plan = self.env["sc.subscription.plan"].sudo().search([("code", "=", code)], limit=1)
        if not plan:
            plan = self.env["sc.subscription.plan"].sudo().search([("active", "=", True)], limit=1)
        return plan

    @api.model
    def _resolve_plan(self, company):
        today = fields.Date.context_today(self)
        sub = self.env["sc.subscription"].sudo().search([
            ("company_id", "=", company.id),
            ("state", "in", ("trial", "active")),
            "|",
            ("end_date", "=", False),
            ("end_date", ">=", today),
        ], order="start_date desc, id desc", limit=1)
        return sub.plan_id if sub else self._default_plan()

    @api.model
    def get_effective(self, company):
        plan = self._resolve_plan(company)
        flags = dict(plan.feature_flags_json or {}) if plan else {}
        limits = dict(plan.limits_json or {}) if plan else {}
        ent = self.search([("company_id", "=", company.id)], limit=1)
        vals = {
            "company_id": company.id,
            "plan_id": plan.id if plan else False,
            "effective_flags_json": flags,
            "effective_limits_json": limits,
            "updated_at": fields.Datetime.now(),
        }
        if ent:
            ent.write(vals)
        else:
            ent = self.create(vals)
        return ent

    @api.model
    def _flag_enabled(self, flags, flag):
        if not flag:
            return True
        val = (flags or {}).get(flag)
        if isinstance(val, bool):
            return val is True
        if isinstance(val, (int, float)):
            return val == 1
        if isinstance(val, str):
            return val.strip().lower() in {"1", "true", "yes", "y", "on"}
        return False

    @api.model
    def evaluate_intent(self, user, intent, params):
        if not user:
            return True, "", {}
        company = user.company_id
        ent = self.get_effective(company)
        flags = ent.effective_flags_json or {}
        cap_key = (params or {}).get("capability_key") or (params or {}).get("capability") or (params or {}).get("key")
        cap = None
        if cap_key:
            cap = self.env["sc.capability"].sudo().search([("key", "=", cap_key)], limit=1)
        elif intent:
            caps = self.env["sc.capability"].sudo().search([("intent", "=", intent)])
            if len(caps) == 1:
                cap = caps[0]
        if cap and cap.required_flag:
            if not self._flag_enabled(flags, cap.required_flag):
                return False, "FEATURE_DISABLED", {"required_flag": cap.required_flag, "capability_key": cap.key}
        return True, "", {}

    @api.model
    def get_payload(self, user):
        if not user:
            return {}
        ent = self.get_effective(user.company_id)
        return {
            "plan_code": ent.plan_id.code if ent.plan_id else None,
            "flags": ent.effective_flags_json or {},
            "limits": ent.effective_limits_json or {},
        }


class ScUsageCounter(models.Model):
    _name = "sc.usage.counter"
    _description = "SC Usage Counter"
    _order = "updated_at desc, id desc"

    company_id = fields.Many2one("res.company", required=True, ondelete="cascade")
    key = fields.Char(required=True, index=True)
    value = fields.Integer(default=0)
    updated_at = fields.Datetime()

    _sql_constraints = [
        ("sc_usage_counter_company_key_uniq", "unique(company_id, key)", "Usage counter must be unique per company."),
    ]

    @api.model
    def bump(self, company, key, delta=1):
        counter = self.search([("company_id", "=", company.id), ("key", "=", key)], limit=1)
        if counter:
            counter.write({"value": counter.value + delta, "updated_at": fields.Datetime.now()})
        else:
            self.create({
                "company_id": company.id,
                "key": key,
                "value": delta,
                "updated_at": fields.Datetime.now(),
            })

    @api.model
    def get_usage_map(self, company):
        counters = self.search([("company_id", "=", company.id)])
        return {rec.key: rec.value for rec in counters}


class ScOpsJob(models.Model):
    _name = "sc.ops.job"
    _description = "SC Ops Job"
    _order = "started_at desc, id desc"

    name = fields.Char(required=True)
    job_type = fields.Char(required=True)
    status = fields.Selection(
        [("running", "Running"), ("done", "Done"), ("failed", "Failed"), ("canceled", "Canceled")],
        default="running",
        required=True,
    )
    started_at = fields.Datetime()
    finished_at = fields.Datetime()
    payload_json = fields.Json()
    result_json = fields.Json()
    error_message = fields.Char()
    trace_id = fields.Char()
