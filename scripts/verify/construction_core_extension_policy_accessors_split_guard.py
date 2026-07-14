#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
ACCESSORS = ROOT / "addons/smart_construction_core/core_extension_policy_accessors.py"
POLICY_MAPS = ROOT / "addons/smart_construction_core/core_extension_policy_maps.py"
CI = ROOT / "make/ci.mk"

MAX_CORE_EXTENSION_LINES = 1820


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load_file(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _install_policy_map_stub() -> None:
    policy_maps = _load_file(POLICY_MAPS, "construction_core_policy_maps_for_accessor_guard")
    package_names = [
        "odoo",
        "odoo.addons",
        "odoo.addons.smart_construction_core",
    ]
    for name in package_names:
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["odoo.addons.smart_construction_core.core_extension_policy_maps"] = policy_maps
    sys.modules.setdefault("odoo.addons.smart_construction_core.models", types.ModuleType("odoo.addons.smart_construction_core.models"))
    sys.modules.setdefault("odoo.addons.smart_construction_core.models.support", types.ModuleType("odoo.addons.smart_construction_core.models.support"))
    alias_fields = types.ModuleType("odoo.addons.smart_construction_core.models.support.p1_daily_business_visible_alias_fields")
    alias_fields.P1_ALIAS_LABELS = {"sample.model": ["项目名称", "合同金额"]}
    alias_fields.P1_ALIAS_COMPAT_LABELS = {"sample.model": ["兼容字段"]}
    alias_fields.LABEL_SOURCE_OVERRIDES = {"项目名称": ["project_id"], "合同金额": ["amount_total"], "兼容字段": ["compat_name"]}
    alias_fields.MODEL_LABEL_SOURCE_OVERRIDES = {"sample.model": {"合同金额": ["amount_total", "amount_untaxed"]}}
    confirmed = types.ModuleType("odoo.addons.smart_construction_core.models.support.user_confirmed_formal_visible_fields")
    confirmed.USER_CONFIRMED_FORMAL_VISIBLE_FIELDS = {"sample.model": [{"label": "确认字段"}]}
    alias_fields.LABEL_SOURCE_OVERRIDES["确认字段"] = ["confirmed_name"]
    sys.modules["odoo.addons.smart_construction_core.models.support.p1_daily_business_visible_alias_fields"] = alias_fields
    sys.modules["odoo.addons.smart_construction_core.models.support.user_confirmed_formal_visible_fields"] = confirmed


class _FakeModelRecord:
    def __init__(self, model: str):
        self.model = model


class _FakeModel:
    _transient = False
    _abstract = False

    def __init__(self, rows=None, name="", fields=None):
        self._rows = rows or []
        self.name = name
        self._fields = set(fields or [])

    def sudo(self):
        return self

    def search(self, domain):
        del domain
        return self._rows

    def browse(self, record_id=0):
        del record_id
        return self

    def exists(self):
        return self

    def __bool__(self):
        return bool(self.name or self._rows)


class _FakeEnv(dict):
    pass


def main() -> int:
    errors: list[str] = []
    core_text = _read(CORE_EXTENSION)
    accessors_text = _read(ACCESSORS)
    ci_text = _read(CI)

    if not core_text:
        errors.append(f"missing core extension file: {CORE_EXTENSION.relative_to(ROOT)}")
    if not accessors_text:
        errors.append(f"missing policy accessors module: {ACCESSORS.relative_to(ROOT)}")

    if core_text:
        line_count = len(core_text.splitlines())
        if line_count > MAX_CORE_EXTENSION_LINES:
            errors.append(f"core_extension.py line budget exceeded: {line_count} > {MAX_CORE_EXTENSION_LINES}")
        for token in [
            "core_extension_policy_accessors as _policy_accessors",
            "return _policy_accessors.get_file_upload_allowed_model_contributions(env)",
            "return _policy_accessors.get_api_data_mutation_policy_contribution(env, model_name, op)",
            "return _policy_accessors.is_contract_tax_rate_quick_create(env, vals)",
            "return _policy_accessors.get_api_data_create_execution_policy_contribution(env, model_name, vals, ctx, params)",
            "return _policy_accessors.get_api_data_search_fields(env, model_name)",
        ]:
            if token not in core_text:
                errors.append(f"core_extension.py missing policy accessors split token: {token}")

    if accessors_text:
        for token in [
            "def get_file_upload_allowed_model_contributions(",
            "def business_attachment_allowed_models(",
            "def get_api_data_mutation_policy_contribution(",
            "def is_contract_tax_rate_quick_create(",
            "def get_api_data_create_execution_policy_contribution(",
            "def get_api_data_unlink_allowed_model_contributions(",
            "def get_api_data_search_fields(",
            "USER_CONFIRMED_FORMAL_VISIBLE_FIELDS",
            "_policy_maps.API_DATA_UNLINK_POLICIES",
        ]:
            if token not in accessors_text:
                errors.append(f"policy accessors module missing token: {token}")
        for forbidden in (".write(", ".create(", ".unlink(", "requests.", "register_", "commit("):
            if forbidden in accessors_text:
                errors.append(f"policy accessors module must remain read-side policy accessors; forbidden token: {forbidden}")

    if "python3 scripts/verify/construction_core_extension_policy_accessors_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run construction_core_extension_policy_accessors_split_guard.py")

    if not errors:
        _install_policy_map_stub()
        accessors = _load_file(ACCESSORS, "construction_core_extension_policy_accessors_under_guard")
        env = _FakeEnv({
            "ir.model": _FakeModel([
                _FakeModelRecord("project.project"),
                _FakeModelRecord("sc.legacy.invoice.tax.fact"),
                _FakeModelRecord("sc.scene.internal"),
            ]),
            "project.project": _FakeModel(),
            "sc.legacy.invoice.tax.fact": _FakeModel(),
            "account.tax.group": _FakeModel(name="合同税率"),
            "sample.model": _FakeModel(fields={"project_id", "amount_total", "confirmed_name"}),
        })
        upload_models = accessors.get_file_upload_allowed_model_contributions(env)
        if "project.project" not in upload_models:
            errors.append("policy accessors must preserve project upload model contribution")
        if "sc.scene.internal" in upload_models:
            errors.append("policy accessors must keep scene/internal models excluded")
        mutation = accessors.get_api_data_mutation_policy_contribution(env, "sc.legacy.receipt.income.fact", "create")
        if mutation.get("allowed") is not False:
            errors.append("policy accessors must preserve readonly mutation denial")
        quick_vals = {"type_tax_use": "none", "amount_type": "percent", "price_include": False, "tax_group_id": 1}
        if not accessors.is_contract_tax_rate_quick_create(env, quick_vals):
            errors.append("policy accessors must preserve contract tax quick-create recognition")
        create_policy = accessors.get_api_data_create_execution_policy_contribution(env, "account.tax", quick_vals, {}, {})
        if create_policy.get("sudo") is not True:
            errors.append("policy accessors must preserve contract tax quick-create sudo policy")
        unfiltered_names = accessors.get_api_data_search_fields(None, "sample.model")
        if "amount_untaxed" not in unfiltered_names or "confirmed_name" not in unfiltered_names:
            errors.append("policy accessors must merge alias, model override, and confirmed formal search fields")
        filtered_names = accessors.get_api_data_search_fields(env, "sample.model")
        if filtered_names != ["project_id", "amount_total", "confirmed_name"]:
            errors.append("policy accessors must filter search fields against model _fields")

    if errors:
        print("[construction_core_extension_policy_accessors_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[construction_core_extension_policy_accessors_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
