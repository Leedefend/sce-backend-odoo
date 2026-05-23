#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit action context default-group projection.

Run through ``scripts/ops/odoo_shell_exec.sh`` so Odoo provides the global
``env``.  The audit checks every ``ir.actions.act_window`` that carries a
``search_default_group_*`` context key and verifies that the custom page
contract projects at most one matching default group.
"""

from __future__ import annotations

import json
from typing import Any

from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import (
    ActionDispatcher,
)
from odoo.tools.safe_eval import safe_eval


ALLOWED_UNMATCHED = {
    ("account.analytic.line", "search_default_group_by_analytic_account"),
}
KEY_ACTION_NAMES = {
    "发票总台账",
    "发票分类汇总表",
    "发票分析报表",
    "收款申请",
    "支付申请",
    "项目预算",
    "施工方案",
    "风险项",
}


def _context_tokens(action: Any) -> list[str]:
    try:
        context = safe_eval(action.context or "{}") or {}
    except Exception:
        context = {}
    return [
        str(key)
        for key, value in context.items()
        if str(key).startswith("search_default_group_") and value
    ]


def _group_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    search = payload.get("search") or {}
    group_by = search.get("group_by") or []
    return [row for row in group_by if isinstance(row, dict)]


def _default_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in _group_rows(payload) if bool(row.get("default"))]


def _row_identity(row: dict[str, Any]) -> list[str]:
    return [
        str(row.get("field") or ""),
        str(row.get("key") or ""),
    ]


def main() -> int:
    dispatcher = ActionDispatcher(env, env["ir.model"].sudo().env)  # noqa: F821
    Action = env["ir.actions.act_window"].sudo()  # noqa: F821
    actions = Action.search([("context", "ilike", "search_default_group_")], order="id")

    checked = 0
    errors: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    multi_default: list[dict[str, Any]] = []
    defaults: list[dict[str, Any]] = []

    for action in actions:
        tokens = _context_tokens(action)
        if not tokens:
            continue
        checked += 1
        try:
            payload, _versions = dispatcher.dispatch(
                {
                    "subject": "action",
                    "action_id": action.id,
                    "view_type": action.view_mode or "tree,form",
                    "context": {},
                }
            )
        except Exception as exc:
            errors.append(
                {
                    "id": action.id,
                    "name": action.name,
                    "model": action.res_model,
                    "tokens": tokens,
                    "error": str(exc),
                }
            )
            continue

        default_rows = _default_rows(payload)
        if len(default_rows) > 1:
            multi_default.append(
                {
                    "id": action.id,
                    "name": action.name,
                    "model": action.res_model,
                    "tokens": tokens,
                    "defaults": [_row_identity(row) for row in default_rows],
                }
            )
        elif len(default_rows) == 1:
            row = default_rows[0]
            defaults.append(
                {
                    "id": action.id,
                    "name": action.name,
                    "model": action.res_model,
                    "tokens": tokens,
                    "default": _row_identity(row),
                }
            )
        else:
            unmatched.append(
                {
                    "id": action.id,
                    "name": action.name,
                    "model": action.res_model,
                    "tokens": tokens,
                }
            )

    unexpected_unmatched = [
        row
        for row in unmatched
        if not all((row["model"], token) in ALLOWED_UNMATCHED for token in row["tokens"])
    ]
    sample_defaults = [
        row
        for row in defaults
        if row["name"] in KEY_ACTION_NAMES or len(row["tokens"]) > 1
    ]
    result = {
        "action_count": len(actions),
        "checked": checked,
        "default_count": len(defaults),
        "allowed_unmatched": unmatched,
        "unexpected_unmatched": unexpected_unmatched,
        "multi_default": multi_default,
        "errors": errors,
        "sample_defaults": sample_defaults,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if errors or multi_default or unexpected_unmatched:
        print("[verify.action_default_group.contract_audit] FAIL")
        return 1
    print("[verify.action_default_group.contract_audit] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
