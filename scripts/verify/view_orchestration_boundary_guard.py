#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard business view orchestration boundaries."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "addons/smart_core/core/view_orchestration_contract.py"
NATIVE_PARSE = ROOT / "addons/smart_core/app_config_engine/services/native_parse_service.py"
FALLBACK_PARSE = ROOT / "addons/smart_core/app_config_engine/services/parse_fallback_service.py"
ODOO_PARSER = ROOT / "addons/smart_core/app_config_engine/services/view_Parser/contract_Parser.py"
APP_VIEW_CONFIG = ROOT / "addons/smart_core/app_config_engine/models/app_view_config.py"
PAGE_ASSEMBLER = ROOT / "addons/smart_core/app_config_engine/services/assemblers/page_assembler.py"
V2_ASSEMBLER = ROOT / "addons/smart_core/core/unified_page_contract_v2_assembler.py"
VIEW_ORCHESTRATOR = ROOT / "addons/smart_core/core/view_orchestrator.py"
FIELD_HANDLER = ROOT / "addons/smart_core/handlers/form_field_configuration.py"
FIELD_POLICY = ROOT / "addons/smart_core/model/ui_form_field_policy.py"
BUSINESS_CONFIG = ROOT / "addons/smart_core/model/ui_business_config_contract.py"
DOC = ROOT / "docs/audit/native/view_orchestration_boundary_20260515.md"
ORCHESTRATOR_TEST = ROOT / "addons/smart_core/tests/test_view_orchestrator.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _function_body(source: str, name: str) -> str:
    marker = f"def {name}"
    start = source.find(marker)
    if start < 0:
        return ""
    next_def = source.find("\ndef ", start + len(marker))
    next_class = source.find("\nclass ", start + len(marker))
    stops = [idx for idx in (next_def, next_class) if idx > start]
    end = min(stops) if stops else len(source)
    return source[start:end]


def main() -> int:
    errors: list[str] = []
    contract = _read(CONTRACT)
    native_parse = _read(NATIVE_PARSE)
    fallback_parse = _read(FALLBACK_PARSE)
    odoo_parser = _read(ODOO_PARSER)
    app_view_config = _read(APP_VIEW_CONFIG)
    page_assembler = _read(PAGE_ASSEMBLER)
    v2 = _read(V2_ASSEMBLER)
    orchestrator = _read(VIEW_ORCHESTRATOR) if VIEW_ORCHESTRATOR.exists() else ""
    field_handler = _read(FIELD_HANDLER)
    field_policy = _read(FIELD_POLICY)
    business_config = _read(BUSINESS_CONFIG)
    doc = _read(DOC)
    orchestrator_test = _read(ORCHESTRATOR_TEST)

    for label, source in (
        ("NativeParseService", native_parse),
        ("ParseFallbackService", fallback_parse),
        ("OdooViewParser", odoo_parser),
    ):
        _assert(
            "NO_BUSINESS_FACT_AUTHORITY = True" in source and '"no_business_fact_authority"' in source,
            f"{label} must remain parse/projection only",
            errors,
        )

    _assert(
        "business_view_orchestration" in contract
        and "PARSER_FORBIDDEN_RESPONSIBILITIES" in contract
        and "VIEW_ORCHESTRATOR_INPUTS" in contract
        and "VIEW_TYPE_OUTPUT_SURFACES" in contract,
        "view orchestration boundary contract must name inputs, outputs, and forbidden parser responsibilities",
        errors,
    )
    _assert(
        '"ui.business.config.contract"' in contract
        and '"ui.business.config.contract.version"' in contract
        and "business_config_contract" in contract,
        "orchestration boundary must use business config contract authorities",
        errors,
    )
    _assert(
        "industry_view_template" not in contract
        and "customer_view_profile" not in contract
        and "ui.view.profile" not in doc
        and "ui.view.template" not in doc,
        "view orchestration boundary must not introduce parallel template/profile concepts",
        errors,
    )
    for view_type in (
        "form",
        "tree",
        "list",
        "kanban",
        "search",
        "pivot",
        "graph",
        "calendar",
        "gantt",
        "activity",
        "dashboard",
    ):
        _assert(f'"{view_type}"' in contract, f"contract missing view type: {view_type}", errors)
        _assert(view_type in doc, f"boundary audit doc missing view type: {view_type}", errors)

    semantic_body = _function_body(v2, "_apply_semantic_container_annotation")
    _assert(
        "semanticTitle" in semantic_body and "semanticAnchor" in semantic_body,
        "semantic standardizer must write semantic annotations",
        errors,
    )
    _assert(
        'node["title"]' not in semantic_body
        and 'node["label"]' not in semantic_body
        and 'node["string"]' not in semantic_body,
        "semantic standardizer must not write user-visible container labels",
        errors,
    )

    _assert(
        '"action_id"' in field_handler
        and '"view_id"' in field_handler
        and '"company_id"' in field_handler,
        "low-code field handlers must keep action/view/company field policy scope",
        errors,
    )
    _assert(
        "_upsert_view_orchestration_field_rows" in field_handler
        and "view_orchestration" in field_handler
        and "business_config_mirrored_count" in field_handler,
        "low-code field handlers must mirror edits into business config orchestration contracts",
        errors,
    )
    _assert(
        field_handler.count("_upsert_view_orchestration_field_rows(") >= 4,
        "field visibility, order, batch, and custom-field handlers must all mirror to business config",
        errors,
    )
    _assert(
        "user_id" not in field_policy,
        "ui.form.field.policy must not introduce user-specific structural scope",
        errors,
    )
    _assert(
        "view_type" in business_config
        and "action_id" in business_config
        and "view_id" in business_config
        and "_effective_view_orchestration_contracts" in business_config,
        "ui.business.config.contract must expose view orchestration runtime scope",
        errors,
    )
    for schema_token in (
        '"group_by"',
        '"groupBys"',
        '"dimensions"',
        '"defaults"',
        '"slots"',
        '"chart_policy"',
        "list_keys",
        "dict_keys",
    ):
        _assert(schema_token in business_config, f"business config view orchestration schema missing: {schema_token}", errors)
    _assert(
        "class ViewOrchestrator" in orchestrator
        and "def compose" in orchestrator
        and "ui.business.config.contract" in orchestrator
        and "business_view_orchestration" in orchestrator,
        "ViewOrchestrator must consume business config contracts",
        errors,
    )
    for required in (
        "test_search_view_uses_business_config_filters_and_group_by",
        "test_pivot_view_uses_business_config_measures_dimensions_and_defaults",
        "test_generic_view_uses_business_config_slots_and_actions",
    ):
        _assert(required in orchestrator_test, f"ViewOrchestrator non-form runtime test missing: {required}", errors)
    _assert(
        "ViewOrchestrator(self.env).compose" in app_view_config
        and 'self.env["ui.form.field.policy"].apply_to_view_contract' not in app_view_config,
        "app.view.config must route final view composition through ViewOrchestrator",
        errors,
    )
    _assert(
        "_current_view_orchestration_config_summary" in page_assembler
        and '"config_source": "ui.business.config.contract"' in page_assembler
        and '"owner_layer": "business_view_orchestration"' in page_assembler
        and '"ui.business.config.contract"' in page_assembler,
        "low-code contract surface must expose business config orchestration ownership",
        errors,
    )

    for phrase in (
        "缺失的是一个独立的业务视图编排层",
        "表单只是最容易暴露问题的视图类型，不是边界本身",
        "原生视图解析层",
        "业务视图编排层",
        "契约投影层",
        "ui.business.config.contract",
        "配置合同",
        "ViewOrchestrator.compose",
        "business_view_orchestration",
    ):
        _assert(phrase in doc, f"boundary audit doc missing phrase: {phrase}", errors)

    legacy_form_doc = ROOT / "docs/audit/native/form_view_orchestration_boundary_20260515.md"
    legacy_form_contract = ROOT / "addons/smart_core/core/form_view_orchestration_contract.py"
    _assert(not legacy_form_doc.exists(), "legacy form-only orchestration audit doc must not remain authoritative", errors)
    _assert(not legacy_form_contract.exists(), "legacy form-only orchestration contract must not remain authoritative", errors)

    if errors:
        print("[view_orchestration_boundary_guard] FAIL")
        for error in errors:
            print(f" - {error}")
        return 1
    print("[view_orchestration_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
