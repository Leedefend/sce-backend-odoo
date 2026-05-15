#!/usr/bin/env python3
"""Audit action-scoped form-view projection facts.

Run inside ``odoo shell``.  The audit samples runtime-visible menu actions and
checks that the action-selected form view is the same scope used by
``app.view.config`` projection identity and readonly projection generation.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(os.environ.get("SC_REPO_ROOT") or Path.cwd()).resolve()
DEFAULT_OUTPUT_DIR = ROOT / "docs/audit/native/form_view_scope_action_projection"
DEFAULT_AUDIT_LOGIN = os.environ.get("FORM_VIEW_SCOPE_AUDIT_LOGIN") or os.environ.get("E2E_LOGIN") or "wutao"

BUSINESS_MODEL_PREFIXES = (
    "construction.",
    "payment.",
    "project.",
    "purchase.",
    "quota.",
    "sc.",
    "tender.",
)
BUSINESS_MODEL_EXACT = {
    "hr.department",
    "res.partner",
    "res.users",
}
TECHNICAL_MODEL_PREFIXES = (
    "base.",
    "bus.",
    "ir.",
    "mail.",
    "portal.",
    "res.config",
    "web.",
)
TECHNICAL_MODEL_TOKENS = (
    ".wizard",
    ".settings",
    ".installer",
)


@dataclass
class ActionProjectionRow:
    status: str
    menu_id: int
    menu_name: str
    action_id: int
    action_name: str
    model: str
    view_mode: str
    action_views: str
    expected_projection_scope: str
    expected_source_view_id: int
    identity_projection_scope: str
    identity_action_id: int
    identity_source_view_id: int
    transient_projection_scope: str
    transient_action_id: int
    transient_source_view_id: int
    persistent_scope_count: int
    field_policy_count: int
    issues: str


def text(value: Any) -> str:
    return str(value or "").strip()


def is_business_model(model: str) -> bool:
    if not model:
        return False
    if model.startswith(TECHNICAL_MODEL_PREFIXES):
        return False
    if any(token in model for token in TECHNICAL_MODEL_TOKENS):
        return False
    return model in BUSINESS_MODEL_EXACT or model.startswith(BUSINESS_MODEL_PREFIXES)


def action_views_json(action: Any) -> str:
    try:
        return json.dumps(list(action.views or []), ensure_ascii=False, default=str)
    except Exception:
        return "[]"


def action_source_view_id(action: Any, view_type: str = "form") -> int:
    for view_spec in action.views or []:
        if view_spec and len(view_spec) >= 2 and view_spec[1] == view_type:
            try:
                return int(view_spec[0] or 0)
            except Exception:
                return 0
    return 0


def collect_menu_actions(user_env: Any, limit: int) -> list[tuple[Any, Any]]:
    by_action = {}
    Menu = user_env["ir.ui.menu"]
    for menu in Menu.search([]):
        try:
            action = menu.action
        except Exception:
            continue
        if not action or getattr(action, "_name", "") != "ir.actions.act_window":
            continue
        model = text(getattr(action, "res_model", ""))
        view_mode = text(getattr(action, "view_mode", ""))
        if "form" not in {item.strip() for item in view_mode.split(",") if item.strip()}:
            continue
        if not is_business_model(model):
            continue
        if model not in user_env:
            continue
        by_action.setdefault(int(action.id), (menu, action))
    rows = list(by_action.values())
    rows.sort(
        key=lambda item: (
            0 if action_source_view_id(item[1].sudo(), "form") else 1,
            text(item[1].res_model),
            int(item[1].id),
            int(item[0].id),
        )
    )
    return rows[:limit] if limit > 0 else rows


def int_id(value: Any) -> int:
    try:
        return int(getattr(value, "id", value) or 0)
    except Exception:
        return 0


def audit_action(user_env: Any, menu: Any, action: Any) -> ActionProjectionRow:
    issues: list[str] = []
    action_meta = action.sudo()
    model = text(action.res_model)
    view_type = "form"
    expected_view_id = action_source_view_id(action_meta, view_type)
    expected_scope = f"action:{int(action.id)}:{model}:{view_type}:view:{expected_view_id}"
    identity = {}
    transient = None
    persistent_count = 0
    policy_count = 0

    Config = user_env["app.view.config"].with_context(contract_action_id=int(action.id))
    try:
        identity = Config._projection_identity(model, view_type)
    except Exception as exc:
        issues.append(f"identity_error:{text(exc)[:180]}")

    if identity.get("projection_scope") != expected_scope:
        issues.append("projection_identity_scope_mismatch")
    if int_id(identity.get("action_id")) != int(action.id):
        issues.append("projection_identity_action_mismatch")
    if int_id(identity.get("source_view_id")) != expected_view_id:
        issues.append("projection_identity_view_mismatch")

    try:
        transient = (
            user_env["app.view.config"]
            .with_context(contract_action_id=int(action.id), contract_projection_readonly=True)
            ._generate_from_fields_view_get(model, view_type)
        )
    except Exception as exc:
        issues.append(f"readonly_projection_error:{text(exc)[:180]}")

    if transient:
        if text(transient.projection_scope) != expected_scope:
            issues.append("readonly_projection_scope_mismatch")
        if int_id(transient.action_id) != int(action.id):
            issues.append("readonly_projection_action_mismatch")
        if int_id(transient.source_view_id) != expected_view_id:
            issues.append("readonly_projection_view_mismatch")

    try:
        persistent_count = user_env["app.view.config"].sudo().search_count([("projection_scope", "=", expected_scope)])
    except Exception as exc:
        issues.append(f"persistent_scope_count_error:{text(exc)[:120]}")

    try:
        policy_domain = [("model", "=", model)]
        if expected_view_id:
            policy_domain = [
                ("model", "=", model),
                "|",
                ("action_id", "=", int(action.id)),
                ("view_id", "=", expected_view_id),
            ]
        else:
            policy_domain = [("model", "=", model), ("action_id", "=", int(action.id))]
        policy_count = user_env["ui.form.field.policy"].sudo().search_count(policy_domain)
    except Exception as exc:
        issues.append(f"field_policy_count_error:{text(exc)[:120]}")

    return ActionProjectionRow(
        status="fail" if issues else "pass",
        menu_id=int(menu.id),
        menu_name=text(menu.complete_name or menu.name),
        action_id=int(action.id),
        action_name=text(action.name),
        model=model,
        view_mode=text(action.view_mode),
        action_views=action_views_json(action_meta),
        expected_projection_scope=expected_scope,
        expected_source_view_id=expected_view_id,
        identity_projection_scope=text(identity.get("projection_scope")),
        identity_action_id=int_id(identity.get("action_id")),
        identity_source_view_id=int_id(identity.get("source_view_id")),
        transient_projection_scope=text(getattr(transient, "projection_scope", "")) if transient else "",
        transient_action_id=int_id(getattr(transient, "action_id", 0)) if transient else 0,
        transient_source_view_id=int_id(getattr(transient, "source_view_id", 0)) if transient else 0,
        persistent_scope_count=int(persistent_count or 0),
        field_policy_count=int(policy_count or 0),
        issues=", ".join(issues),
    )


def write_reports(out_dir: Path, audit_login: str, rows: list[ActionProjectionRow]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    row_dicts = [asdict(row) for row in rows]
    status_counts = Counter(row.status for row in rows)
    payload = {
        "ok": not any(row.status == "fail" for row in rows),
        "scope": "runtime visible action form-view projection identity",
        "audit_login": audit_login,
        "summary": {
            "sample_count": len(rows),
            "pass_count": status_counts.get("pass", 0),
            "fail_count": status_counts.get("fail", 0),
            "action_scoped_count": sum(1 for row in rows if row.expected_projection_scope.startswith("action:")),
            "explicit_source_view_count": sum(1 for row in rows if row.expected_source_view_id > 0),
            "field_policy_scope_count": sum(row.field_policy_count for row in rows),
        },
        "rows": row_dicts,
    }
    (out_dir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with (out_dir / "rows.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(ActionProjectionRow.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(row_dicts)

    lines = [
        "# Form View Scope Action Projection Audit",
        "",
        f"- audit_login: {audit_login}",
        f"- sample_count: {payload['summary']['sample_count']}",
        f"- pass_count: {payload['summary']['pass_count']}",
        f"- fail_count: {payload['summary']['fail_count']}",
        f"- explicit_source_view_count: {payload['summary']['explicit_source_view_count']}",
        f"- field_policy_scope_count: {payload['summary']['field_policy_scope_count']}",
        "",
        "| status | model | action | source_view | projection_scope | policies | issues |",
        "|---|---|---|---:|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {status} | `{model}` | `{action}` | {view_id} | `{scope}` | {policies} | {issues} |".format(
                status=row.status,
                model=row.model,
                action=f"{row.action_id}:{row.action_name}",
                view_id=row.expected_source_view_id,
                scope=row.expected_projection_scope,
                policies=row.field_policy_count,
                issues=row.issues or "",
            )
        )
    (out_dir / "README.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--limit", type=int, default=int(os.environ.get("FORM_VIEW_SCOPE_ACTION_LIMIT", "30") or "30"))
    parser.add_argument("--audit-login", default=DEFAULT_AUDIT_LOGIN)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or []))
    base_env = globals().get("env")
    if base_env is None:
        raise RuntimeError("This audit must run inside odoo shell with global env.")
    user = base_env["res.users"].sudo().search([("login", "=", args.audit_login)], limit=1)
    if not user:
        raise RuntimeError(f"audit user not found: {args.audit_login}")
    user_env = base_env(user=user)
    samples = collect_menu_actions(user_env, args.limit)
    rows = [audit_action(user_env, menu, action) for menu, action in samples]
    write_reports(Path(args.out_dir), args.audit_login, rows)
    fail_count = sum(1 for row in rows if row.status == "fail")
    print(f"[form_view_scope_action_projection_audit] out_dir={args.out_dir}")
    print(f"[form_view_scope_action_projection_audit] sample_count={len(rows)} fail_count={fail_count}")
    if fail_count:
        return 1
    print("[form_view_scope_action_projection_audit] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
