# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, models


class ExecuteButtonService(models.AbstractModel):
    _name = "sc.execute_button.service"
    _description = "Execute button actions with a unified response"

    @api.model
    def execute(self, model, res_id, method, context=None):
        if not model or model not in self.env:
            raise ValueError("invalid model")
        if not res_id or not method:
            raise ValueError("missing res_id or method")

        record = self.env[model].browse(int(res_id)).exists()
        if not record:
            raise ValueError("record not found")

        record.check_access_rights("write")
        record.check_access_rule("write")

        fn = getattr(record, method, None)
        if fn is None or not callable(fn):
            raise ValueError("method not callable")

        ctx = dict(self.env.context or {})
        if isinstance(context, dict):
            ctx.update(context)

        result = record.with_context(ctx)
        result = getattr(result, method)()
        ui_effect = _extract_ui_effect(result)
        next_action = _extract_action(result)
        reload_flag = bool(result is None or result is True)

        return {
            "reload": reload_flag,
            "ui_effect": ui_effect,
            "next_action": next_action,
        }


def _extract_ui_effect(result):
    if isinstance(result, dict) and "effect" in result:
        return result.get("effect")
    return None


def _extract_action(result):
    if not isinstance(result, dict):
        return None
    if any(key in result for key in ("type", "res_model", "views", "tag")):
        return result
    return None
