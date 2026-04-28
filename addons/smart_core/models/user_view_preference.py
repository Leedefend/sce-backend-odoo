# -*- coding: utf-8 -*-
from odoo import fields, models


class ScUserViewPreference(models.Model):
    _name = "sc.user.view.preference"
    _description = "Smart Core User View Preference"

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
