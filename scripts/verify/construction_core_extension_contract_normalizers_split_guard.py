#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
NORMALIZERS = ROOT / "addons/smart_construction_core/core_extension_contract_normalizers.py"
HELPERS = ROOT / "addons/smart_construction_core/core_extension_contract_helpers.py"
CI = ROOT / "make/ci.mk"

MAX_CORE_EXTENSION_LINES = 1809
MAX_NORMALIZER_LINES = 383


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_normalizers():
    helper_module = _load(HELPERS, "construction_core_extension_contract_helpers_for_normalizer_guard")
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    sys.modules.setdefault("odoo.addons.smart_construction_core", types.ModuleType("odoo.addons.smart_construction_core"))
    sys.modules["odoo.addons.smart_construction_core.core_extension_contract_helpers"] = helper_module
    return _load(NORMALIZERS, "construction_core_extension_contract_normalizers_under_guard")


def _field(name: str, ttype: str = "char", **extra):
    return {"name": name, "string": extra.pop("string", name), "type": ttype, **extra}


def main() -> int:
    errors: list[str] = []
    core_text = _read(CORE_EXTENSION)
    normalizer_text = _read(NORMALIZERS)
    ci_text = _read(CI)

    if not core_text:
        errors.append(f"missing core extension file: {CORE_EXTENSION.relative_to(ROOT)}")
    if not normalizer_text:
        errors.append(f"missing contract normalizer module: {NORMALIZERS.relative_to(ROOT)}")

    if core_text:
        line_count = len(core_text.splitlines())
        if line_count > MAX_CORE_EXTENSION_LINES:
            errors.append(f"core_extension.py line budget exceeded: {line_count} > {MAX_CORE_EXTENSION_LINES}")
        for token in [
            "core_extension_contract_normalizers as _contract_normalizers",
            "_contract_normalizers.normalize_construction_diary_form(contract, source_contract, model=model, view_type=view_type)",
            "_contract_normalizers.general_contract_tax_contract(contract, source_contract=source_contract)",
            "_contract_normalizers.normalize_general_contract_company_form(contract, source_contract=source_contract)",
            "return _contract_normalizers.model_specific_form_contract_policy(payload)",
            "return _contract_normalizers.form_field_aliases(payload)",
            "def _sc_inject_workflow_contract(env, contract, source, *, model, view_type):",
        ]:
            if token not in core_text:
                errors.append(f"core_extension.py missing contract normalizer split token: {token}")

    if normalizer_text:
        line_count = len(normalizer_text.splitlines())
        if line_count > MAX_NORMALIZER_LINES:
            errors.append(f"contract normalizer line budget exceeded: {line_count} > {MAX_NORMALIZER_LINES}")
        for token in [
            "def normalize_construction_diary_form(",
            "def general_contract_tax_contract(",
            "def normalize_general_contract_company_form(",
            "def model_specific_form_contract_policy(",
            "def form_field_aliases(",
            "_sc_collect_field_nodes = _contract_helpers.sc_collect_field_nodes",
            "_sc_set_v2_container_tree = _contract_helpers.sc_set_v2_container_tree",
            "_sc_set_v2_widget_status = _contract_helpers.sc_set_v2_widget_status",
            "_sc_set_v2_governance_patch = _contract_helpers.sc_set_v2_governance_patch",
            "_sc_replace_contract_content = _contract_helpers.sc_replace_contract_content",
            "_sc_form_layout_governance = _contract_helpers.sc_form_layout_governance",
            "_sc_apply_form_layout_governance_to_group = _contract_helpers.sc_apply_form_layout_governance_to_group",
        ]:
            if token not in normalizer_text:
                errors.append(f"contract normalizer module missing token: {token}")
        for forbidden in (
            "env[",
            ".search(",
            ".write(",
            ".create(",
            ".unlink(",
            "requests.",
            "register_",
            "AccessError",
            "from odoo import fields",
            " odoo.fields",
        ):
            if forbidden in normalizer_text:
                errors.append(f"contract normalizer module must remain projection-only; forbidden token: {forbidden}")

    if "python3 scripts/verify/construction_core_extension_contract_normalizers_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run construction_core_extension_contract_normalizers_split_guard.py")

    if not errors:
        normalizers = _load_normalizers()

        diary_contract = {"model": "sc.construction.diary", "layoutContract": {"containerTree": []}}
        diary_source = {
            "fields": {
                "project_id": _field("project_id", "many2one", relation="project.project"),
                "date_diary": _field("date_diary", "date"),
                "diary_type": _field("diary_type", "selection", selection=[("daily", "Daily")]),
                "title": _field("title"),
                "state": _field("state", "selection"),
            }
        }
        normalizers.normalize_construction_diary_form(diary_contract, diary_source, model="sc.construction.diary", view_type="form")
        diary_patches = diary_contract.get("runtimeContract", {}).get("governancePatches", {})
        if "construction_diary_form" not in diary_patches:
            errors.append("construction diary normalizer must record governance patch")
        if not diary_contract.get("layoutContract", {}).get("containerTree"):
            errors.append("construction diary normalizer must write v2 container tree")

        tax_contract = {
            "model": "sc.general.contract",
            "fields": {"tax_id": _field("tax_id", "many2one", relation="account.tax")},
            "layoutContract": {
                "containerTree": [
                    {"type": "group", "children": [{"type": "field", "name": "amount_total", "widgetId": "field.amount_total"}]}
                ]
            },
            "statusContract": {"widgetStatus": [{"widgetId": "field.tax_rate", "visible": True}]},
        }
        normalizers.general_contract_tax_contract(tax_contract)
        widget_ids = [row.get("widgetId") for row in tax_contract.get("statusContract", {}).get("widgetStatus", []) if isinstance(row, dict)]
        if "field.tax_id" not in widget_ids or "field.tax_rate" in widget_ids:
            errors.append("general contract tax normalizer must replace tax_rate status with tax_id")

        company_contract = {"model": "sc.general.contract", "viewType": "form", "layoutContract": {"containerTree": []}}
        company_source = {
            "model": "sc.general.contract",
            "view_type": "form",
            "business_operation_profile": {"form_structure_governance": {"form_columns": 2}},
            "fields": {
                "contract_name": _field("contract_name"),
                "amount_total": _field("amount_total", "float", string="最终合同价"),
            },
        }
        normalizers.normalize_general_contract_company_form(company_contract, company_source)
        company_patches = company_contract.get("runtimeContract", {}).get("governancePatches", {})
        if "general_contract_company_form" not in company_patches:
            errors.append("general contract company normalizer must record governance patch")
        if "最终合同价" in repr(company_contract):
            errors.append("general contract company normalizer must replace legacy amount label")
        if "合同金额" not in repr(company_contract):
            errors.append("general contract company normalizer must expose company amount label")
        form_policy = normalizers.model_specific_form_contract_policy({
            "model": "sc.general.contract",
            "fields": {"tax_id": {}, "tax_rate": {}},
        })
        if form_policy != {"remove_fields": ["tax_rate"]}:
            errors.append("contract normalizer must preserve tax_rate removal form policy")
        aliases = normalizers.form_field_aliases({
            "model": "sc.general.contract",
            "source_contract": {"fields": {"tax_id": {}}},
        })
        if aliases != {"tax_rate": "tax_id"}:
            errors.append("contract normalizer must preserve tax_rate field alias")

    if errors:
        print("[construction_core_extension_contract_normalizers_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[construction_core_extension_contract_normalizers_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
