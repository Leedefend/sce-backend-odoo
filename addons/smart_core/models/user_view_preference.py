# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ScUserViewPreference(models.Model):
    _name = "sc.user.view.preference"
    _description = "Smart Core UI-only User View Preference"

    UI_ONLY_SCOPE_PREFIX = "ui:"
    SUPPORTED_PREFERENCE_KEYS = {"list_columns"}
    SOURCE_KIND = "ui_only_user_preference"
    SOURCE_AUTHORITIES = ("res.users", "ir.actions.actions")
    NO_BUSINESS_FACT_AUTHORITY = True

    @api.model
    def source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": self._name,
        }

    user_id = fields.Many2one("res.users", required=True, index=True, ondelete="cascade")
    scope_key = fields.Char(required=True, index=True)
    action_id = fields.Many2one("ir.actions.actions", index=True, ondelete="cascade")
    model_name = fields.Char(index=True)
    view_type = fields.Char(default="list", index=True)
    preference_key = fields.Char(required=True, default="list_columns", index=True)
    value_json = fields.Json(default=dict)

    _sql_constraints = [
        (
            "sc_user_view_preference_scope_user_uniq",
            "unique(user_id, scope_key)",
            "A user view preference already exists for this scope.",
        ),
    ]

    @api.model
    def normalize_preference_key(self, value):
        key = str(value or "list_columns").strip() or "list_columns"
        return key if key in self.SUPPORTED_PREFERENCE_KEYS else "list_columns"

    @api.model
    def build_scope_key(self, *, preference_key="", view_type="", action_id=0, model_name=""):
        key = self.normalize_preference_key(preference_key)
        view = str(view_type or "list").strip() or "list"
        try:
            action = int(action_id or 0)
        except (TypeError, ValueError):
            action = 0
        model = str(model_name or "").strip()
        target = f"action:{action}" if action > 0 else f"model:{model or 'unknown'}"
        return f"{self.UI_ONLY_SCOPE_PREFIX}{key}:{view}:{target}"
