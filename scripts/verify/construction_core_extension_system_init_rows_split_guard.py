#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
ROWS = ROOT / "addons/smart_construction_core/core_extension_system_init_rows.py"
CI = ROOT / "make/ci.mk"

MAX_CORE_EXTENSION_LINES = 3351


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    if "odoo" not in sys.modules:
        odoo = types.ModuleType("odoo")
        fields_module = types.SimpleNamespace(Datetime=types.SimpleNamespace(now=lambda: "2026-07-14 00:00:00"))
        odoo.fields = fields_module
        exceptions = types.ModuleType("odoo.exceptions")
        exceptions.AccessError = type("AccessError", (Exception,), {})
        sys.modules["odoo"] = odoo
        sys.modules["odoo.exceptions"] = exceptions
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeCompany:
    id = 7
    name = "示例企业"


class _FakeUser:
    id = 11
    company_id = _FakeCompany()


class _FakeModel:
    def __init__(self, fields: set[str], rows: list[dict]):
        self._fields = fields
        self._rows = rows

    def search_read(self, domain, fields, limit=6, order=None):
        del order
        rows = list(self._rows)
        for item in domain or []:
            if not isinstance(item, tuple) or len(item) != 3:
                continue
            field_name, operator, expected = item
            if operator == "=":
                rows = [row for row in rows if row.get(field_name) == expected]
        return [
            {field: row.get(field) for field in fields if field in row}
            for row in rows[:limit]
        ]


class _FakeEnv(dict):
    pass


def main() -> int:
    errors: list[str] = []
    core_text = _read(CORE_EXTENSION)
    rows_text = _read(ROWS)
    ci_text = _read(CI)

    if not core_text:
        errors.append(f"missing core extension file: {CORE_EXTENSION.relative_to(ROOT)}")
    if not rows_text:
        errors.append(f"missing system init rows module: {ROWS.relative_to(ROOT)}")

    if core_text:
        line_count = len(core_text.splitlines())
        if line_count > MAX_CORE_EXTENSION_LINES:
            errors.append(f"core_extension.py line budget exceeded: {line_count} > {MAX_CORE_EXTENSION_LINES}")
        for token in [
            "core_extension_system_init_rows as _system_init_rows",
            "return _system_init_rows.as_text(value)",
            "return _system_init_rows.safe_search_read(env, model_name, domain, fields, limit=limit)",
            "return _system_init_rows.model_has_field(env, model_name, field_name)",
            "return _system_init_rows.build_enterprise_enablement_contract(env, user)",
            "return _system_init_rows.build_task_action_rows(env, user)",
            "return _system_init_rows.build_payment_action_rows(env)",
            "return _system_init_rows.build_risk_action_rows(env)",
            "return _system_init_rows.build_project_action_rows(env, user)",
            "return _system_init_rows.dictionary_fields(env)",
            "return _system_init_rows.build_role_entry_contract_rows(env)",
            "return _system_init_rows.build_home_block_contract_rows(env)",
        ]:
            if token not in core_text:
                errors.append(f"core_extension.py missing system-init row split token: {token}")
        for forbidden in ("from odoo import fields", "from odoo.exceptions import AccessError"):
            if forbidden in core_text:
                errors.append(f"core_extension.py must not keep row-builder implementation import: {forbidden}")

    if rows_text:
        for token in [
            "def as_text(",
            "def safe_search_read(",
            "def model_has_field(",
            "def step_status_label(",
            "def build_enterprise_enablement_contract(",
            "def build_task_action_rows(",
            "def build_payment_action_rows(",
            "def build_risk_action_rows(",
            "def build_project_action_rows(",
            "def dictionary_fields(",
            "def build_role_entry_contract_rows(",
            "def build_home_block_contract_rows(",
            "model.search_read(",
            "fields.Datetime.now()",
        ]:
            if token not in rows_text:
                errors.append(f"system init rows module missing token: {token}")
        for forbidden in (".write(", ".create(", ".unlink(", "requests.", "register_", "env.cr", "commit("):
            if forbidden in rows_text:
                errors.append(f"system init rows module must remain read-side row assembly; forbidden token: {forbidden}")

    if "python3 scripts/verify/construction_core_extension_system_init_rows_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run construction_core_extension_system_init_rows_split_guard.py")

    if not errors:
        rows = _load(ROWS, "construction_core_extension_system_init_rows_under_guard")
        if rows.as_text({"zh_CN": " 项目 "}) != "项目":
            errors.append("as_text must preserve localized text normalization")
        enterprise = rows.build_enterprise_enablement_contract(_FakeEnv(), _FakeUser())
        if enterprise.get("mainline", {}).get("current_company_id") != 7:
            errors.append("enterprise enablement rows must preserve company id")
        env = _FakeEnv({
            "sc.dictionary": _FakeModel(
                {"code", "name", "value_json", "sequence", "scope_type", "scope_ref"},
                [
                    {"type": "role_entry", "active": True, "code": "role.menu", "scope_type": "role", "scope_ref": "pm", "value_json": {"entry_type": "menu"}, "sequence": 2},
                    {"type": "home_block", "active": True, "code": "home.block", "scope_type": "global", "value_json": {"is_enabled": True}, "sequence": 1},
                ],
            ),
            "project.task": _FakeModel(
                {"id", "name", "project_id", "sc_state", "date_deadline", "write_date", "user_id"},
                [{"id": 3, "name": "跟进", "project_id": [9, "项目A"], "sc_state": "in_progress"}],
            ),
            "payment.request": _FakeModel(
                {"id", "name", "project_id", "state", "amount", "date_request", "write_date"},
                [{"id": 4, "name": "付款", "project_id": [9, "项目A"], "amount": 12}],
            ),
            "project.project": _FakeModel(
                {"id", "name", "health_state", "lifecycle_state", "write_date", "user_id", "manager_id"},
                [{"id": 5, "name": "项目A", "health_state": "risk", "lifecycle_state": "draft", "active": True}],
            ),
        })
        if not rows.build_task_action_rows(env, _FakeUser()):
            errors.append("task action rows must be built from read-side rows")
        if rows.build_payment_action_rows(env)[0].get("amount") != 12:
            errors.append("payment action rows must preserve amount")
        if rows.build_project_action_rows(env, _FakeUser())[0].get("status") != "urgent":
            errors.append("project action rows must preserve risk status")
        if rows.build_role_entry_contract_rows(env)[0].get("role_code") != "pm":
            errors.append("role entry rows must preserve role-scoped dictionary entries")
        if rows.build_home_block_contract_rows(env)[0].get("blocks") != ["home.block"]:
            errors.append("home block rows must preserve enabled global blocks")

    if errors:
        print("[construction_core_extension_system_init_rows_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[construction_core_extension_system_init_rows_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
