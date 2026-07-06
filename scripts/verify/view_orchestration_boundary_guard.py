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
CALENDAR_GANTT_ACTIVITY_PARSER = ROOT / "addons/smart_core/app_config_engine/services/view_Parser/parsers_Calendar_Gantt Activity.py"
APP_VIEW_CONFIG = ROOT / "addons/smart_core/app_config_engine/models/app_view_config.py"
CONTRACT_MIXIN = ROOT / "addons/smart_core/app_config_engine/models/contract_mixin.py"
PAGE_ASSEMBLER = ROOT / "addons/smart_core/app_config_engine/services/assemblers/page_assembler.py"
LOAD_CONTRACT = ROOT / "addons/smart_core/handlers/load_contract.py"
V2_ASSEMBLER = ROOT / "addons/smart_core/core/unified_page_contract_v2_assembler.py"
VIEW_ORCHESTRATOR = ROOT / "addons/smart_core/core/view_orchestrator.py"
FIELD_HANDLER = ROOT / "addons/smart_core/handlers/form_field_configuration.py"
FIELD_POLICY = ROOT / "addons/smart_core/model/ui_form_field_policy.py"
BUSINESS_CONFIG = ROOT / "addons/smart_core/model/ui_business_config_contract.py"
DOC = ROOT / "docs/audit/native/view_orchestration_boundary_20260515.md"
ORCHESTRATOR_TEST = ROOT / "addons/smart_core/tests/test_view_orchestrator.py"
FIELD_HANDLER_TEST = ROOT / "addons/smart_core/tests/test_form_field_configuration_params.py"
NATIVE_PARSER_TEST = ROOT / "addons/smart_core/tests/test_native_view_parser_surfaces.py"
BUSINESS_CONFIG_TEST = ROOT / "addons/smart_core/tests/test_business_config_contract_schema.py"
PAGE_ASSEMBLER_TEST = ROOT / "addons/smart_core/tests/test_page_assembler_view_orchestration_versions.py"
CONTRACT_MIXIN_TEST = ROOT / "addons/smart_core/tests/test_contract_mixin_view_surfaces.py"
ACTION_VIEW_RUNTIME = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewContractShapeRuntime.ts"
ACTION_VIEW_SHAPE_SMOKE = ROOT / "scripts/verify/action_view_orchestration_contract_shape_smoke.js"
CONTRACT_FORM_PAGE = ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue"
CONTRACT_FORM_LOWCODING_SMOKE = ROOT / "scripts/verify/contract_form_lowcode_orchestration_smoke.js"
CONTRACT_FORM_ORCHESTRATION_HUD_SMOKE = ROOT / "scripts/verify/contract_form_view_orchestration_hud_smoke.js"


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
    calendar_parser = _read(CALENDAR_GANTT_ACTIVITY_PARSER)
    app_view_config = _read(APP_VIEW_CONFIG)
    contract_mixin = _read(CONTRACT_MIXIN)
    page_assembler = _read(PAGE_ASSEMBLER)
    load_contract = _read(LOAD_CONTRACT)
    v2 = _read(V2_ASSEMBLER)
    orchestrator = _read(VIEW_ORCHESTRATOR) if VIEW_ORCHESTRATOR.exists() else ""
    field_handler = _read(FIELD_HANDLER)
    field_policy = _read(FIELD_POLICY)
    business_config = _read(BUSINESS_CONFIG)
    doc = _read(DOC)
    orchestrator_test = _read(ORCHESTRATOR_TEST)
    field_handler_test = _read(FIELD_HANDLER_TEST)
    native_parser_test = _read(NATIVE_PARSER_TEST)
    business_config_test = _read(BUSINESS_CONFIG_TEST)
    page_assembler_test = _read(PAGE_ASSEMBLER_TEST)
    contract_mixin_test = _read(CONTRACT_MIXIN_TEST)
    action_view_runtime = _read(ACTION_VIEW_RUNTIME)
    action_view_shape_smoke = _read(ACTION_VIEW_SHAPE_SMOKE)
    contract_form_page = _read(CONTRACT_FORM_PAGE)
    contract_form_lowcode_smoke = _read(CONTRACT_FORM_LOWCODING_SMOKE)
    contract_form_hud_smoke = _read(CONTRACT_FORM_ORCHESTRATION_HUD_SMOKE)

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
    for parser_token in (
        '"date_slots"',
        '"resource_slots"',
        '"dependency_slots"',
        '"activity_type_slots"',
        '"group_by_fields"',
        '"search_fields"',
        "_parse_view_field_nodes",
    ):
        _assert(parser_token in calendar_parser, f"native parser surface missing: {parser_token}", errors)
    for parser_test in (
        "test_calendar_parser_preserves_native_slots_and_fields",
        "test_gantt_parser_preserves_dependency_and_resource_slots",
        "test_search_parser_preserves_search_fields_and_group_by_metadata",
    ):
        _assert(parser_test in native_parser_test, f"native parser surface test missing: {parser_test}", errors)
    _assert(
        "_fallback_view_field_nodes" in app_view_config
        and "view_type == 'search'" in app_view_config
        and "view_type == 'calendar'" in app_view_config
        and "view_type == 'gantt'" in app_view_config
        and "view_type == 'activity'" in app_view_config
        and "'group_by_fields'" in app_view_config,
        "app.view.config fallback parser must preserve non-form native view surfaces",
        errors,
    )
    _assert(
        "'search': {'search'}" in contract_mixin
        and "'activity': {'activity'}" in contract_mixin
        and "'dashboard': {'dashboard'}" in contract_mixin
        and '"search": {"search"}' in app_view_config
        and '"activity": {"activity"}' in app_view_config
        and '"dashboard": {"dashboard"}' in app_view_config
        and "test_governed_sanitize_keeps_non_form_view_surface_blocks" in contract_mixin_test,
        "contract sanitizer must preserve native search/activity/dashboard view surface blocks",
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
        field_handler.count('"ui.business.config.contract"') >= 4
        and field_handler.count('"ui.business.config.contract.version"') >= 4
        and "test_low_code_write_intents_declare_business_config_authority" in field_handler_test,
        "low-code write intents must declare business config contract authority",
        errors,
    )
    _assert(
        "_append_business_config_scope_domain" in field_handler
        and "_normalize_view_type_scope" in field_handler
        and "test_business_config_contract_list_uses_full_view_scope_domain" in field_handler_test
        and "test_business_config_contract_publish_rejects_invalid_scope_id" in field_handler_test,
        "business config contract handlers must share view/action/view/role/status scope rules",
        errors,
    )
    _assert(
        "test_business_config_contract_save_uses_full_scope_domain" in field_handler_test
        and '("view_type", "=", view_type or False)' in field_handler
        and '("action_id", "=", action_id or False)' in field_handler
        and '("view_id", "=", view_id or False)' in field_handler
        and '("role_key", "=", role_key)' in field_handler,
        "business config contract save must search existing records by full orchestration scope",
        errors,
    )
    _assert(
        "test_business_config_contract_save_normalizes_empty_role_scope" in field_handler_test
        and '("role_key", "=", role_key or False)' in field_handler
        and '"role_key": role_key or False' in field_handler,
        "business config contract save must normalize empty role scope to False",
        errors,
    )
    _assert(
        "_contract_reload_hint" in field_handler
        and '"view_orchestration_config_changed"' in field_handler
        and '"contract_reload":' in field_handler
        and "test_contract_reload_hint_normalizes_scope" in field_handler_test,
        "business config writes must return contract reload hints",
        errors,
    )
    _assert(
        "_upsert_view_orchestration_field_rows(" in field_handler
        and "business_config_mirrored_count" in field_handler
        and "business_config_group_mirrored_count" in field_handler
        and "business_config_visibility_mirrored_count" in field_handler
        and "business_config_layout_mirrored_count" in field_handler,
        "field visibility, order, batch, and custom-field handlers must all mirror to business config",
        errors,
    )
    _assert(
        "test_batch_config_rejects_unknown_visibility_field_before_order_write" in field_handler_test
        and "field_visibility" in field_handler
        and "字段不存在：%s.%s" in field_handler,
        "batch low-code form configuration must reject unknown visibility fields before writing orchestration config",
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
        and "_normalize_view_orchestration_view_type" in business_config
        and "_effective_view_orchestration_contracts" in business_config,
        "ui.business.config.contract must expose view orchestration runtime scope",
        errors,
    )
    _assert(
        'return "tree" if normalized == "list" else normalized' in business_config
        and "rec.view_id.type" in business_config
        and "contract.view_type" in business_config,
        "ui.business.config.contract must normalize tree/list consistently for scope checks",
        errors,
    )
    for schema_token in (
        '"group_by"',
        '"groupBys"',
        '"dimensions"',
        '"defaults"',
        '"slots"',
        '"action_slots"',
        '"context"',
        '"domain"',
        '"row_classes"',
        '"cards"',
        '"kpis"',
        '"chart_policy"',
        '"dependency_slots"',
        '"metric_slots"',
        '"navigation_slots"',
        '"quick_actions"',
        "list_keys",
        "dict_keys",
    ):
        _assert(schema_token in business_config, f"business config view orchestration schema missing: {schema_token}", errors)
    _assert(
        "_unknown_view_orchestration_fields" in business_config
        and "rec.model in self.env" in business_config
        and "view_orchestration 引用了不存在字段" in business_config
        and "test_unknown_view_orchestration_fields_are_reported" in business_config_test
        and "test_business_semantic_ids_are_not_treated_as_model_fields" in business_config_test,
        "business config view orchestration schema must reject unknown model fields without blocking semantic ids",
        errors,
    )
    _assert(
        "class ViewOrchestrator" in orchestrator
        and "def compose" in orchestrator
        and "ui.business.config.contract" in orchestrator
        and "business_view_orchestration" in orchestrator,
        "ViewOrchestrator must consume business config contracts",
        errors,
    )
    _assert(
        "source_trace" in orchestrator
        and '"view_orchestration"' in orchestrator
        and '"business_config_contracts"' in orchestrator,
        "ViewOrchestrator must expose source_trace for orchestration results",
        errors,
    )
    _assert(
        'result["source_trace"]["view_orchestration"]' in orchestrator_test
        and 'trace["action_id"]' in orchestrator_test
        and 'trace["view_id"]' in orchestrator_test,
        "ViewOrchestrator tests must cover source_trace orchestration scope",
        errors,
    )
    for required in (
        "test_search_view_uses_business_config_filters_and_group_by",
        "test_pivot_view_uses_business_config_measures_dimensions_and_defaults",
        "test_generic_view_uses_business_config_slots_and_actions",
        "test_graph_view_uses_business_config_scalar_and_display_rows",
        "test_calendar_view_uses_business_config_date_resource_and_color_slots",
        "test_dashboard_view_uses_business_config_metric_chart_and_navigation_slots",
        "test_list_view_uses_business_config_row_actions",
        "test_form_view_uses_business_config_action_slots_without_field_rows",
        "test_form_view_uses_business_config_field_display_policy",
        "test_form_view_uses_business_config_field_order_in_native_layout",
        "test_list_view_uses_business_config_column_display_policy",
        "test_list_view_uses_business_config_view_options",
        "test_dashboard_view_uses_business_config_cards_and_kpis",
    ):
        _assert(required in orchestrator_test, f"ViewOrchestrator non-form runtime test missing: {required}", errors)
    for orchestration_token in (
        '"date_slots"',
        '"resource_slots"',
        '"dependency_slots"',
        '"metric_slots"',
        '"navigation_slots"',
        '"quick_actions"',
    ):
        _assert(orchestration_token in orchestrator, f"ViewOrchestrator generic surface missing: {orchestration_token}", errors)
    _assert(
        "ViewOrchestrator(self.env).compose" in app_view_config
        and 'self.env["ui.form.field.policy"].apply_to_view_contract' not in app_view_config,
        "app.view.config must route final view composition through ViewOrchestrator",
        errors,
    )
    _assert(
        "_apply_action_slots" in orchestrator
        and '"row_actions"' in orchestrator
        and '"header_buttons"' in orchestrator
        and '"action_slots"' in orchestrator,
        "ViewOrchestrator must apply business action slots across view types",
        errors,
    )
    _assert(
        "_apply_field_display_policy" in orchestrator
        and "_apply_column_display_policy" in orchestrator
        and "_sort_form_field_nodes" in orchestrator
        and "_ordered_display_rows" in orchestrator
        and "_order_slot_fields" in orchestrator
        and '"readonly"' in orchestrator
        and '"widget"' in orchestrator
        and '"width"' in orchestrator,
        "ViewOrchestrator must apply field order plus field and column display policies across view types",
        errors,
    )
    _assert(
        "_apply_view_options" in orchestrator
        and '"page_size"' in orchestrator
        and '"row_classes"' in orchestrator
        and '"cards"' in orchestrator
        and '"kpis"' in orchestrator,
        "ViewOrchestrator must apply view-level display and content options",
        errors,
    )
    _assert(
        "_sanitize_spec_field_refs" in orchestrator
        and "test_runtime_orchestration_drops_unknown_field_refs_from_existing_configs" in orchestrator_test,
        "ViewOrchestrator must defensively drop unknown field references from existing orchestration configs",
        errors,
    )
    _assert(
        "'source_trace': vp.get('source_trace', {})" in app_view_config,
        "app.view.config get_contract_api must expose orchestrator source_trace",
        errors,
    )
    _assert(
        "_view_orchestration_version_token" in app_view_config
        and "'orchestration_version': orchestration_version" in app_view_config
        and "'effective_version':" in app_view_config
        and 'v_contract.get("effective_version")' in page_assembler,
        "view contract versions must include orchestration config versions",
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
    _assert(
        '"role_key": str(rec.role_key or "")' in page_assembler
        and "viewOrchestrationHudSummary" in contract_form_page
        and "view_orchestration_contracts" in contract_form_page
        and "contract_form_view_orchestration_hud_smoke" in contract_form_hud_smoke,
        "form UI diagnostics must expose applied view orchestration contract summary",
        errors,
    )
    _assert(
        "_inject_view_orchestration_summary" in page_assembler
        and 'governance["view_orchestration"]' in page_assembler
        and '"views": view_rows' in page_assembler,
        "page assembler must summarize per-view orchestration governance",
        errors,
    )
    _assert(
        "_inject_search_view_orchestration" in page_assembler
        and 'data["views"]["search"]' in page_assembler
        and 'data["search"] = merged' in page_assembler,
        "page assembler must route top-level search through view orchestration",
        errors,
    )
    _assert(
        "_append_view_version_token" in page_assembler
        and "versions=versions" in page_assembler
        and 'search_contract.get("effective_version")' in page_assembler
        and "test_append_view_version_token_adds_search_orchestration_version" in page_assembler_test,
        "page assembler must include search view orchestration effective_version in page view versions",
        errors,
    )
    _assert(
        "test_coerce_calendar_preserves_orchestrated_slot_semantics" in page_assembler_test
        and "test_coerce_dashboard_preserves_orchestrated_slots" in page_assembler_test
        and '"date_slots"' in page_assembler
        and '"metric_slots"' in page_assembler
        and '"navigation_slots"' in page_assembler,
        "page assembler must expose orchestrated advanced-view slots on user-facing view contracts",
        errors,
    )
    _assert(
        "extractKanbanFieldsFromContract" in action_view_runtime
        and "extractAdvancedViewFieldsFromContract" in action_view_runtime
        and "collectDisplayRowLabels" in action_view_runtime
        and "collectDisplayRowLabels(block.measures" in action_view_runtime
        and "collectDisplayRowLabels(block.cards" in action_view_runtime
        and "collectSlotFieldNames" in action_view_runtime
        and "kanban nested fields and slots" in action_view_shape_smoke
        and "calendar advanced fields" in action_view_shape_smoke
        and "dashboard advanced fields" in action_view_shape_smoke,
        "frontend action view runtime must consume orchestrated kanban and advanced-view slots",
        errors,
    )
    _assert(
        "buildLowCodeViewOrchestration" in contract_form_page
        and "view_orchestration: buildLowCodeViewOrchestration()" in contract_form_page
        and "collectLowCodeLayoutFromViewOrchestration" in contract_form_page
        and "contract_form_lowcode_orchestration_smoke" in contract_form_lowcode_smoke,
        "frontend low-code form authoring must persist and hydrate view_orchestration contracts",
        errors,
    )
    relation_dialog_body = _function_body(page_assembler, "_build_relation_search_dialog_contract")
    _assert(
        '"governance": governance' in relation_dialog_body
        and '"source_trace": source_trace' in relation_dialog_body
        and 'view_contract.get("source_trace")' in relation_dialog_body,
        "relation search dialogs must expose target view orchestration trace",
        errors,
    )
    _assert(
        '"governance": data.get("governance")' in load_contract
        and '"source_trace": data.get("source_trace")' in load_contract,
        "semantic_page must expose page governance and source_trace",
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
