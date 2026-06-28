#!/usr/bin/env python3
"""Guard frontend consumers prefer formal V2 policy projections."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_SCHEMA = ROOT / "docs/architecture/unified_page_contract_v2/unified_page_contract_v2.schema.json"
ENUM_REGISTRY = ROOT / "docs/architecture/unified_page_contract_v2/enum_registry.json"
CONTRACT_HELPERS = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractV2.ts"
STRICT_SCHEMA = ROOT / "frontend/apps/web/src/app/contracts/v2/schema.ts"
STRICT_TYPES = ROOT / "frontend/apps/web/src/app/contracts/v2/types.ts"
STRICT_STORE = ROOT / "frontend/apps/web/src/app/contracts/v2/store.ts"
CONSUMER_FILES = [
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewPageDisplayStateRuntime.ts",
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewActionPresentationRuntime.ts",
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewSurfaceDisplayRuntime.ts",
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewSurfaceIntentRuntime.ts",
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewFilterComputedRuntime.ts",
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewContractShapeRuntime.ts",
    ROOT / "frontend/apps/web/src/views/ActionView.vue",
    ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue",
    ROOT / "frontend/apps/web/src/app/runtime/unifiedPageContractV2CompatProjection.ts",
    ROOT / "frontend/apps/web/scripts/low_code_global_stability_acceptance.mjs",
]

REQUIRED_HELPERS = (
    "resolveUnifiedPageContractV2DeletePolicy",
    "resolveUnifiedPageContractV2SurfacePolicies",
    "resolveUnifiedPageContractV2ListProfile",
    "resolveUnifiedPageContractV2BusinessOperationProfile",
    "resolveUnifiedPageContractV2FieldGroups",
    "resolveUnifiedPageContractV2FormStructureContract",
    "resolveUnifiedPageContractV2VisibleFields",
)

FORBIDDEN_DIRECT_READS = (
    ".delete_policy",
    ".surface_policies",
    ".list_profile",
    ".business_operation_profile",
    ".field_groups",
    ".form_structure_contract",
    ".visible_fields",
)

ALLOWED_DIRECT_READS = {
    "frontend/apps/web/src/app/runtime/unifiedPageContractV2CompatProjection.ts": {
        ".delete_policy": {"const candidate = asDict(node.delete_policy);"},
        ".list_profile": {"const legacyListProfile = asDict(legacyProjection.list_profile);"},
    },
    "frontend/apps/web/src/pages/ContractFormPage.vue": {
        ".field_groups": {"applyParams.field_groups = changedGroups;"},
    },
}

FORBIDDEN_STRICT_SCHEMA_COMPAT_ALIASES = (
    "['delete_policy']",
    "['surface_policies']",
    "['list_profile']",
    "['business_operation_profile']",
    "row.visible_fields",
    "row.field_groups",
    "row.source_authority",
    "root.form_structure_contract",
    "root.searchContract",
    "root.data",
    "root.rawBody",
    "['page_info']",
    "['layout_contract']",
    "['status_contract']",
    "['action_contract']",
    "['data_contract']",
    "['runtime_contract']",
    "unified_page_contract_v2",
    "__unified_page_contract_v2",
    "legacyContractProjection",
    "legacy_contract_projection",
)

FORBIDDEN_STRICT_TYPE_COMPAT_ALIASES = (
    "delete_policy",
    "surface_policies",
    "list_profile",
    "business_operation_profile",
    "visible_fields",
    "field_groups",
    "form_structure_contract",
    "searchContract",
    "legacyContractProjection",
    "legacy_contract_projection",
)

REQUIRED_STRICT_ENUM_TYPE_TOKENS = (
    "export type ContractV2ViewType = 'form' | 'list' | 'table' | 'kanban' | 'tree' | 'gantt' | 'combine'",
    "export type ContractV2LayoutType = 'form' | 'table' | 'kanban' | 'tree' | 'gantt' | 'combine'",
    "export type ContractV2AdaptMode = 'pc' | 'mobile'",
    "export type ContractV2TriggerType = 'change' | 'click' | 'select' | 'refresh' | 'add' | 'delete' | 'confirm' | 'submit' | 'blur' | 'focus'",
    "export type ContractV2DispatchMode = 'local' | 'server' | 'serverDebounced' | 'serverBlocking'",
    "export type ContractV2TargetScope = 'widget' | 'container' | 'page' | 'dataSource' | 'runtime'",
    "export type ContractV2RefreshMode = 'none' | 'partial' | 'full'",
    "export type ContractV2Auth = 'none' | 'read' | 'edit' | 'admin'",
    "export type ContractV2PatchStrategy = 'incremental' | 'full'",
    "export type ContractV2CachePolicy = 'none' | 'etag' | 'snapshot'",
    "export type ContractV2RenderStrategy = 'sync' | 'scheduled' | 'virtualized'",
    "export type ContractV2PatchOperation = 'replace' | 'merge' | 'append' | 'remove' | 'reorder' | 'invalidate'",
    "export type ContractV2PageRenderMode = 'governed'",
    "export interface ContractV2Meta",
    "viewType: ContractV2ViewType",
    "layoutType: ContractV2LayoutType",
    "renderMode: ContractV2PageRenderMode",
    "adaptMode: ContractV2AdaptMode",
    "triggerType: ContractV2TriggerType",
    "dispatchMode: ContractV2DispatchMode",
    "targetScope: ContractV2TargetScope",
    "refreshMode: ContractV2RefreshMode",
    "auth?: ContractV2Auth",
    "pageId: string",
    "layoutHints: ContractV2Dictionary",
    "submitPolicy?: ContractV2Dictionary",
    "tracePolicy?: ContractV2Dictionary",
    "dependencyGraph: Record<string, string[]>",
    "runtimeContract: ContractV2RuntimeContract",
    "patchStrategy: ContractV2PatchStrategy",
    "cachePolicy: ContractV2CachePolicy",
    "renderStrategy?: ContractV2RenderStrategy",
    "patchOperations?: ContractV2PatchOperation[]",
    "meta: ContractV2Meta",
)

REQUIRED_STRICT_ENUM_DECODER_TOKENS = (
    "function decodeViewType(",
    "function decodeLayoutType(",
    "function decodeAdaptMode(",
    "function decodeTriggerType(",
    "function decodeDispatchMode(",
    "function decodeTargetScope(",
    "function decodeRefreshMode(",
    "function decodeAuth(",
    "function decodePatchStrategy(",
    "function decodeCachePolicy(",
    "function decodeRenderStrategy(",
    "function decodePatchOperation(",
    "function decodePageRenderMode(",
    "function decodeRuntimeContract(",
    "function decodeMeta(",
    "viewType: decodeViewType(",
    "layoutType: decodeLayoutType(",
    "renderMode: decodePageRenderMode(",
    "const contractVersion = requiredString(source, 'contractVersion', 'pageInfo', issues)",
    "pageId: requiredString(source, 'pageId', 'pageInfo', issues)",
    "sceneKey: requiredString(source, 'sceneKey', 'pageInfo', issues)",
    "pageName: requiredString(source, 'pageName', 'pageInfo', issues)",
    "viewType: decodeViewType(requiredString(source, 'viewType', 'pageInfo', issues)",
    "layoutType: decodeLayoutType(requiredString(source, 'layoutType', 'pageInfo', issues)",
    "clientType: decodeClientType(requiredString(source, 'clientType', 'pageInfo', issues)",
    "adaptMode: decodeAdaptMode(",
    "triggerType: decodeTriggerType(",
    "dispatchMode: decodeDispatchMode(",
    "targetScope: decodeTargetScope(",
    "refreshMode: decodeRefreshMode(",
    "const auth = decodeAuth(",
    "pageId: requiredString(source, 'pageId', 'layoutContract', issues)",
    "layoutHints: requiredRecord(source, 'layoutHints', 'layoutContract', issues)",
    "dependencyGraph,",
    "submitPolicy }",
    "tracePolicy }",
    "patchStrategy: decodePatchStrategy(",
    "cachePolicy: decodeCachePolicy(",
    "const runtimeContract = decodeRuntimeContract(",
    "const meta = decodeMeta(",
)

FORBIDDEN_STRICT_STORE_META_EXTENSION_TOKENS = (
    "meta.requiredCapabilities",
    "requiredCapabilities",
)

ALLOWED_STRICT_STORE_SNAKE_CASE_TOKENS = {
    # ContractV2ValueSource.kind; not a payload field read.
    "main_data",
    # Native form shadow widget synthesis compatibility.
    "component_config",
    "component_key",
    "field_info",
    "field_type",
    "relation_entry",
    "widget_id",
    "widget_options",
    # Source context compatibility owned by resolveContractV2SourceContext.
    "context_raw",
    "domain_raw",
    "render_profile",
    "source_context",
}

ALLOWED_STRICT_SCHEMA_SNAKE_CASE_TOKENS = {
    # Formal enum values.
    "harmony_h5",
    "web_pc",
    "wx_mini",
    # Explicit dataMeta forbidden-key rejection.
    "business_operation_profile",
    "field_groups",
    "legacy_contract",
    "visible_fields",
    # Native form container extension compatibility.
    "button_type",
    "field_info",
    "form_structure",
    "form_structure_role",
}

FORBIDDEN_STRICT_ALIAS_HELPERS = (
    "function requiredAliasedString(",
    "function optionalAliasedString(",
    "function aliasedRecord(",
    "function aliasedArray(",
)

FORBIDDEN_STRICT_PAGE_INFO_ALIASES = (
    "['contract_version']",
    "['page_id']",
    "['scene_key']",
    "['page_name', 'title']",
    "['view_type']",
    "['layout_type']",
    "['client_type']",
)

FORBIDDEN_STRICT_LAYOUT_CONTRACT_ALIASES = (
    "['container_tree', 'containerList', 'container_list']",
    "source.container_tree",
    "['layout_type']",
    "['adapt_mode']",
    "['component_registry']",
)

FORBIDDEN_STRICT_ACTION_CONTRACT_ALIASES = (
    "['action_rule_list', 'actions']",
    "source.action_rule_list",
    "['dependency_graph']",
)

FORBIDDEN_STRICT_ACTION_RULE_ALIASES = (
    "['action_id', 'id', 'key']",
    "['trigger_type']",
    "['source_widget_id']",
    "raw.target_ids",
    "['dispatch_mode']",
    "['target_scope']",
    "['refresh_mode']",
    "['action_key', 'key']",
)

FORBIDDEN_STRICT_DATA_CONTRACT_ALIASES = (
    "source.tree_data",
    "source.gantt_data",
    "['main_data']",
    "source.table_rows",
    "source.relation_rows",
    "['dict_data']",
    "source.data_source",
    "source.data_meta",
)

FORBIDDEN_STRICT_DATA_META_ALIASES = (
    "row.fieldNames",
    "row.field_names",
    "Array.isArray(value)",
    "Array.isArray(row.items)",
    "visible_fields",
    "field_groups",
    "business_operation_profile",
    "'legacy' + 'ContractProjection'",
    "'legacy_contract' + '_projection'",
)

FORBIDDEN_STRICT_WIDGET_ALIASES = (
    "raw.fieldInfo",
    "raw.field_info",
    "raw.component_config",
    "fieldInfo.componentConfig",
    "fieldInfo.component_config",
    "fieldInfo.relationEntry",
    "fieldInfo.relation_entry",
    "componentConfig.relationEntry",
    "componentConfig.relation_entry",
    "fieldInfo.widgetOptions",
    "fieldInfo.widget_options",
    "fieldInfo.options",
    "componentConfig.widgetOptions",
    "componentConfig.widget_options",
    "['field_code', 'name', 'field']",
    "['widget_id', 'id']",
    "['widget_type', 'widget', 'type']",
    "['component_key']",
    "fieldInfo.componentKey",
    "fieldInfo.component_key",
    "['string', 'title']",
    "fieldInfo.label",
    "fieldInfo.string",
    "['field_type', 'ttype']",
    "fieldInfo.type",
    "fieldInfo.ttype",
    "fieldInfo.relation",
)

FORBIDDEN_STRICT_CONTAINER_FORMAL_FIELD_ALIASES = (
    "['container_id', 'id', 'name']",
    "['container_type', 'type']",
    "raw.widget_list",
    "raw.widgets",
    "raw.string) || asString(raw.label)",
)

FORBIDDEN_STRICT_STATUS_CONTRACT_ALIASES = (
    "['global_status']",
    "['widget_status']",
    "['button_status']",
    "['container_status']",
    "['selector_status']",
    "source.page_visible",
    "['page_auth']",
    "reason_code",
    "raw.widget_id",
    "raw.btn_id",
    "raw.container_id",
)

ALLOWED_STRICT_SCHEMA_EXTENSION_FIELDS = {
    # Native form shadow rendering still consumes these container presentation
    # fields while formal V2 fields remain containerId/containerType/title/etc.
    "ContractV2Container": {
        "action",
        "attributes",
        "buttonType",
        "cols",
        "columns",
        "fieldInfo",
        "field_info",
        "formStructure",
        "formStructureRole",
        "invisible",
        "items",
        "label",
        "modifiers",
        "name",
        "nodes",
        "pages",
        "readonly",
        "required",
        "string",
        "tabs",
        "type",
        "widget",
    },
    # These are display/runtime conveniences for current native-field widgets.
    "ContractV2Widget": {"fieldType", "relation"},
    # Action presentation keeps UI/navigation metadata outside the formal rule
    # execution contract.
    "ContractV2ActionRule": {"actionKey", "button", "intent", "label", "target"},
}

STRICT_TYPE_ENUM_REGISTRY_MAP = {
    "ContractV2ClientType": ("clientType", "stable"),
    "ContractV2ViewType": ("viewType",),
    "ContractV2LayoutType": ("layoutType",),
    "ContractV2AdaptMode": ("adaptMode",),
    "ContractV2TriggerType": ("triggerType",),
    "ContractV2DispatchMode": ("dispatchMode",),
    "ContractV2TargetScope": ("targetScope",),
    "ContractV2RefreshMode": ("refreshMode",),
    "ContractV2Auth": ("authLevel",),
    "ContractV2PatchStrategy": ("patchStrategy",),
    "ContractV2CachePolicy": ("cachePolicy",),
    "ContractV2RenderStrategy": ("renderStrategy",),
    "ContractV2PatchOperation": ("patchOperation",),
    "ContractV2PageRenderMode": ("renderMode",),
}

STRICT_DECODER_ENUM_REGISTRY_MAP = {
    "decodeClientType": ("clientType", "stable"),
    "decodeViewType": ("viewType",),
    "decodeLayoutType": ("layoutType",),
    "decodeAdaptMode": ("adaptMode",),
    "decodeTriggerType": ("triggerType",),
    "decodeDispatchMode": ("dispatchMode",),
    "decodeTargetScope": ("targetScope",),
    "decodeRefreshMode": ("refreshMode",),
    "decodeAuth": ("authLevel",),
    "decodePageRenderMode": ("renderMode",),
    "decodePatchStrategy": ("patchStrategy",),
    "decodeCachePolicy": ("cachePolicy",),
    "decodeRenderStrategy": ("renderStrategy",),
    "decodePatchOperation": ("patchOperation",),
}


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _has_helper_call(source: str, helper: str) -> bool:
    return bool(re.search(rf"\b{re.escape(helper)}\s*\(", source))


def _strict_snapshot_fields(source: str) -> set[str]:
    match = re.search(r"export\s+interface\s+ContractV2Snapshot\s*\{(?P<body>.*?)\n\}", source, re.DOTALL)
    if not match:
        return set()
    fields: set[str] = set()
    for line in match.group("body").splitlines():
        field = re.match(r"\s*([A-Za-z_$][\w$]*)\??:", line)
        if field:
            fields.add(field.group(1))
    return fields


def _interface_fields(source: str, interface_name: str) -> set[str]:
    match = re.search(
        rf"export\s+interface\s+{re.escape(interface_name)}(?:\s+extends\s+[^\{{]+)?\s*\{{(?P<body>.*?)\n\}}",
        source,
        re.DOTALL,
    )
    if not match:
        return set()
    fields: set[str] = set()
    for line in match.group("body").splitlines():
        field = re.match(r"\s*([A-Za-z_$][\w$]*)\??:", line)
        if field:
            fields.add(field.group(1))
    return fields


def _strict_required_object_reads(source: str) -> set[str]:
    return set(re.findall(r"readAliasedObject\(root, '([^']+)', \[\], '\$', issues\)", source))


def _function_body(source: str, function_name: str) -> str:
    match = re.search(rf"function\s+{re.escape(function_name)}\s*\([^)]*\)\s*:[^{{]+\{{(?P<body>.*?)\n\}}", source, re.DOTALL)
    return match.group("body") if match else ""


def _snake_case_tokens(source: str) -> set[str]:
    return set(re.findall(r"\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]*\b", source))


def _registry_path(value: dict[str, object], path: tuple[str, ...]) -> object:
    node: object = value
    for item in path:
        if not isinstance(node, dict):
            return None
        node = node.get(item)
    return node


def _strict_type_enum_literals(source: str, type_name: str) -> list[str] | None:
    match = re.search(rf"export\s+type\s+{re.escape(type_name)}\s*=\s*(?P<body>[^;]+);", source)
    if not match:
        return None
    return re.findall(r"'([^']+)'", match.group("body"))


def _decoder_enum_literals(source: str, function_name: str) -> list[str] | None:
    body = _function_body(source, function_name)
    if not body:
        return None
    return re.findall(r"\bvalue\s*===\s*'([^']+)'", body)


def main() -> int:
    violations: list[str] = []
    helper_source = CONTRACT_HELPERS.read_text(encoding="utf-8")
    for helper in REQUIRED_HELPERS:
        if f"export function {helper}(" not in helper_source:
            violations.append(f"{_relative(CONTRACT_HELPERS)}: missing exported helper {helper}")
    strict_schema_source = STRICT_SCHEMA.read_text(encoding="utf-8")
    strict_schema_snake_tokens = _snake_case_tokens(strict_schema_source)
    if strict_schema_snake_tokens != ALLOWED_STRICT_SCHEMA_SNAKE_CASE_TOKENS:
        violations.append(
            f"{_relative(STRICT_SCHEMA)}: strict V2 decoder snake_case tokens must match whitelist; "
            f"extra={sorted(strict_schema_snake_tokens - ALLOWED_STRICT_SCHEMA_SNAKE_CASE_TOKENS)} "
            f"missing={sorted(ALLOWED_STRICT_SCHEMA_SNAKE_CASE_TOKENS - strict_schema_snake_tokens)}"
        )
    for token in FORBIDDEN_STRICT_SCHEMA_COMPAT_ALIASES:
        if token in strict_schema_source:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: strict V2 decoder must not accept compatibility alias {token}"
            )
    strict_type_source = STRICT_TYPES.read_text(encoding="utf-8")
    enum_registry = json.loads(ENUM_REGISTRY.read_text(encoding="utf-8"))
    for function_name, registry_key_path in sorted(STRICT_DECODER_ENUM_REGISTRY_MAP.items()):
        decoder_literals = _decoder_enum_literals(strict_schema_source, function_name)
        registry_literals = _registry_path(enum_registry, registry_key_path)
        if decoder_literals is None:
            violations.append(f"{_relative(STRICT_SCHEMA)}: missing strict V2 enum decoder {function_name}")
            continue
        if decoder_literals != registry_literals:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: {function_name} literals must match enum_registry.{'.'.join(registry_key_path)}; "
                f"decoder={decoder_literals} registry={registry_literals}"
            )
    for type_name, registry_key_path in sorted(STRICT_TYPE_ENUM_REGISTRY_MAP.items()):
        type_literals = _strict_type_enum_literals(strict_type_source, type_name)
        registry_literals = _registry_path(enum_registry, registry_key_path)
        if type_literals is None:
            violations.append(f"{_relative(STRICT_TYPES)}: missing strict V2 enum type {type_name}")
            continue
        if type_literals != registry_literals:
            violations.append(
                f"{_relative(STRICT_TYPES)}: {type_name} literals must match enum_registry.{'.'.join(registry_key_path)}; "
                f"type={type_literals} registry={registry_literals}"
            )
    for token in FORBIDDEN_STRICT_TYPE_COMPAT_ALIASES:
        if token in strict_type_source:
            violations.append(
                f"{_relative(STRICT_TYPES)}: strict V2 types must not declare compatibility alias {token}"
            )
    for token in REQUIRED_STRICT_ENUM_TYPE_TOKENS:
        if token not in strict_type_source:
            violations.append(f"{_relative(STRICT_TYPES)}: strict V2 type enum token missing: {token}")
    for token in REQUIRED_STRICT_ENUM_DECODER_TOKENS:
        if token not in strict_schema_source:
            violations.append(f"{_relative(STRICT_SCHEMA)}: strict V2 enum decoder token missing: {token}")
    for token in FORBIDDEN_STRICT_ALIAS_HELPERS:
        if token in strict_schema_source:
            violations.append(f"{_relative(STRICT_SCHEMA)}: strict V2 decoder must not define alias helper {token}")
    page_info_decoder = _function_body(strict_schema_source, "decodePageInfo")
    for token in FORBIDDEN_STRICT_PAGE_INFO_ALIASES:
        if token in page_info_decoder:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: strict V2 pageInfo decoder must not accept compatibility alias {token}"
            )
    layout_contract_decoder = _function_body(strict_schema_source, "decodeLayoutContract")
    for token in FORBIDDEN_STRICT_LAYOUT_CONTRACT_ALIASES:
        if token in layout_contract_decoder:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: strict V2 layoutContract decoder must not accept compatibility alias {token}"
            )
    action_contract_decoder = _function_body(strict_schema_source, "decodeActionContract")
    for token in FORBIDDEN_STRICT_ACTION_CONTRACT_ALIASES:
        if token in action_contract_decoder:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: strict V2 actionContract decoder must not accept compatibility alias {token}"
            )
    action_rule_decoder = _function_body(strict_schema_source, "decodeActionRule")
    for token in FORBIDDEN_STRICT_ACTION_RULE_ALIASES:
        if token in action_rule_decoder:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: strict V2 actionRule decoder must not accept compatibility alias {token}"
            )
    data_contract_decoder = _function_body(strict_schema_source, "decodeDataContract")
    for token in FORBIDDEN_STRICT_DATA_CONTRACT_ALIASES:
        if token in data_contract_decoder:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: strict V2 dataContract decoder must not accept compatibility alias {token}"
            )
    data_meta_decoder_source = "\n".join(
        _function_body(strict_schema_source, name)
        for name in ("decodeVisibleFields", "decodeFieldGroups")
    )
    for token in FORBIDDEN_STRICT_DATA_META_ALIASES[:4]:
        if token in data_meta_decoder_source:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: strict V2 dataMeta decoder must not accept compatibility alias {token}"
            )
    data_meta_decoder = _function_body(strict_schema_source, "decodeDataMeta")
    for token in FORBIDDEN_STRICT_DATA_META_ALIASES[4:]:
        if token not in data_meta_decoder:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: strict V2 dataMeta decoder must reject forbidden key {token}"
            )
    widget_decoder = _function_body(strict_schema_source, "decodeWidget")
    for token in FORBIDDEN_STRICT_WIDGET_ALIASES:
        if token in widget_decoder:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: strict V2 widget decoder must not accept compatibility alias {token}"
            )
    container_decoder = _function_body(strict_schema_source, "decodeContainer")
    for token in FORBIDDEN_STRICT_CONTAINER_FORMAL_FIELD_ALIASES:
        if token in container_decoder:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: strict V2 container formal fields must not accept compatibility alias {token}"
            )
    status_decoder_source = "\n".join(
        _function_body(strict_schema_source, name)
        for name in (
            "decodeGlobalStatus",
            "decodeWidgetStatus",
            "decodeButtonStatus",
            "decodeContainerStatus",
            "decodeSelectorStatus",
            "decodeStatusContract",
        )
    )
    for token in FORBIDDEN_STRICT_STATUS_CONTRACT_ALIASES:
        if token in status_decoder_source:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: strict V2 status decoder must not accept compatibility alias {token}"
            )
    strict_store_source = STRICT_STORE.read_text(encoding="utf-8")
    for token in FORBIDDEN_STRICT_STORE_META_EXTENSION_TOKENS:
        if token in strict_store_source:
            violations.append(
                f"{_relative(STRICT_STORE)}: strict V2 store must not read schema-external meta extension {token}"
            )
    strict_store_snake_tokens = _snake_case_tokens(strict_store_source)
    if strict_store_snake_tokens != ALLOWED_STRICT_STORE_SNAKE_CASE_TOKENS:
        violations.append(
            f"{_relative(STRICT_STORE)}: strict V2 store snake_case compatibility tokens must match whitelist; "
            f"extra={sorted(strict_store_snake_tokens - ALLOWED_STRICT_STORE_SNAKE_CASE_TOKENS)} "
            f"missing={sorted(ALLOWED_STRICT_STORE_SNAKE_CASE_TOKENS - strict_store_snake_tokens)}"
        )
    schema_payload = json.loads(BACKEND_SCHEMA.read_text(encoding="utf-8"))
    schema_top_level = set((schema_payload.get("properties") or {}).keys())
    schema_required = set(schema_payload.get("required") or [])
    strict_snapshot_fields = _strict_snapshot_fields(strict_type_source)
    if not strict_snapshot_fields:
        violations.append(f"{_relative(STRICT_TYPES)}: missing ContractV2Snapshot interface")
    elif strict_snapshot_fields != schema_top_level:
        violations.append(
            f"{_relative(STRICT_TYPES)}: ContractV2Snapshot fields must match schema top-level properties; "
            f"extra={sorted(strict_snapshot_fields - schema_top_level)} missing={sorted(schema_top_level - strict_snapshot_fields)}"
        )
    strict_required_reads = _strict_required_object_reads(strict_schema_source)
    if strict_required_reads != schema_required:
        violations.append(
            f"{_relative(STRICT_SCHEMA)}: strict V2 decoder required object reads must match schema.required; "
            f"extra={sorted(strict_required_reads - schema_required)} missing={sorted(schema_required - strict_required_reads)}"
        )
    status_type_map = {
        "widgetStatus": "ContractV2WidgetStatus",
        "buttonStatus": "ContractV2ButtonStatus",
        "containerStatus": "ContractV2ContainerStatus",
        "selectorStatus": "ContractV2SelectorStatus",
    }
    schema_defs = schema_payload.get("$defs") or {}
    for schema_name, interface_name in status_type_map.items():
        schema_fields = set(((schema_defs.get(schema_name) or {}).get("properties") or {}).keys())
        type_fields = _interface_fields(strict_type_source, interface_name)
        if not type_fields:
            violations.append(f"{_relative(STRICT_TYPES)}: missing {interface_name} interface")
            continue
        if type_fields != schema_fields:
            violations.append(
                f"{_relative(STRICT_TYPES)}: {interface_name} fields must match schema $defs.{schema_name}; "
                f"extra={sorted(type_fields - schema_fields)} missing={sorted(schema_fields - type_fields)}"
            )
    schema_interface_map = {
        "pageInfo": "ContractV2PageInfo",
        "layoutContract": "ContractV2LayoutContract",
        "actionContract": "ContractV2ActionContract",
        "actionRule": "ContractV2ActionRule",
        "runtimeContract": "ContractV2RuntimeContract",
        "container": "ContractV2Container",
        "widget": "ContractV2Widget",
        "dataContract": "ContractV2DataContract",
        "dataMeta": "ContractV2DataMeta",
        "meta": "ContractV2Meta",
        "visibleFields": "ContractV2VisibleFields",
        "fieldGroups": "ContractV2FieldGroups",
    }
    for schema_name, interface_name in schema_interface_map.items():
        schema_def = schema_defs.get(schema_name)
        if schema_name in schema_top_level:
            schema_def = schema_payload.get("properties", {}).get(schema_name)
            if isinstance(schema_def, dict) and "$ref" in schema_def:
                schema_def = schema_defs.get(str(schema_def["$ref"]).rsplit("/", 1)[-1])
        schema_fields = set(((schema_def or {}).get("properties") or {}).keys())
        type_fields = _interface_fields(strict_type_source, interface_name)
        if not schema_fields:
            violations.append(f"{_relative(BACKEND_SCHEMA)}: missing schema properties for {schema_name}")
            continue
        if not type_fields:
            violations.append(f"{_relative(STRICT_TYPES)}: missing {interface_name} interface")
            continue
        missing = schema_fields - type_fields
        if missing:
            violations.append(
                f"{_relative(STRICT_TYPES)}: {interface_name} must cover schema {schema_name} fields; "
                f"missing={sorted(missing)}"
            )
        allowed_extra = ALLOWED_STRICT_SCHEMA_EXTENSION_FIELDS.get(interface_name, set())
        extra = type_fields - schema_fields
        unexpected_extra = extra - allowed_extra
        if unexpected_extra:
            violations.append(
                f"{_relative(STRICT_TYPES)}: {interface_name} declares schema-external fields outside the strict V2 whitelist; "
                f"extra={sorted(unexpected_extra)}"
            )
        if interface_name in ALLOWED_STRICT_SCHEMA_EXTENSION_FIELDS and extra != allowed_extra:
            violations.append(
                f"{_relative(STRICT_TYPES)}: {interface_name} schema-extension whitelist drift; "
                f"extra={sorted(extra)} expected={sorted(allowed_extra)}"
            )

    for path in CONSUMER_FILES:
        source = path.read_text(encoding="utf-8")
        rel = _relative(path)
        if "legacyContractProjection" in source or "legacy_contract_projection" in source:
            violations.append(f"{rel}: stable V2 consumers must not read legacyContractProjection")
        if rel != _relative(CONTRACT_HELPERS):
            if "surface_policies" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2SurfacePolicies"):
                violations.append(f"{rel}: surface_policies consumers must use resolveUnifiedPageContractV2SurfacePolicies")
            if "list_profile" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2ListProfile"):
                violations.append(f"{rel}: list_profile consumers must use resolveUnifiedPageContractV2ListProfile")
            if "delete_policy" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2DeletePolicy"):
                violations.append(f"{rel}: delete_policy consumers must use resolveUnifiedPageContractV2DeletePolicy")
            if "business_operation_profile" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2BusinessOperationProfile"):
                violations.append(f"{rel}: business_operation_profile consumers must use resolveUnifiedPageContractV2BusinessOperationProfile")
            if "field_groups" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2FieldGroups"):
                violations.append(f"{rel}: field_groups consumers must use resolveUnifiedPageContractV2FieldGroups")
            if "form_structure_contract" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2FormStructureContract"):
                violations.append(f"{rel}: form_structure_contract consumers must use resolveUnifiedPageContractV2FormStructureContract")
            if "visible_fields" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2VisibleFields"):
                violations.append(f"{rel}: visible_fields consumers must use resolveUnifiedPageContractV2VisibleFields")

        allowed = ALLOWED_DIRECT_READS.get(rel, {})
        for index, line in enumerate(source.splitlines(), start=1):
            stripped = line.strip()
            for token in FORBIDDEN_DIRECT_READS:
                if token not in stripped:
                    continue
                if stripped in allowed.get(token, set()):
                    continue
                violations.append(f"{rel}:{index}: direct read of legacy root field {token}")

    if violations:
        print("[frontend_v2_policy_projection_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[frontend_v2_policy_projection_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
