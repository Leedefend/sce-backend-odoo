#!/usr/bin/env python3
"""Guard the platform-level Unified Page Contract v2 intent."""

from __future__ import annotations

import ast
import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORE_DIR = ROOT / "addons/smart_core/core"
HANDLER_PATH = ROOT / "addons/smart_core/handlers/ui_contract_v2.py"
ONCHANGE_HANDLER_PATH = ROOT / "addons/smart_core/handlers/api_onchange.py"
ASSEMBLER_PATH = ROOT / "addons/smart_core/core/unified_page_contract_v2_assembler.py"
CLIENT_PATH = ROOT / "addons/smart_core/core/unified_page_contract_v2_client.py"
MOBILE_CONTRACT_PAGE = ROOT / "frontend/apps/mobile/src/pages/contract/index.vue"
FORBIDDEN_INDUSTRY_PATH = ROOT / "addons/smart_construction_core/handlers/mobile_contract.py"


def _load(path: Path, name: str):
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    core_pkg.__path__ = [str(CORE_DIR)]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _literal_assignments(tree: ast.AST) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            out[node.targets[0].id] = node.value.value
    return out


def main() -> int:
    errors: list[str] = []
    if not HANDLER_PATH.exists():
        _fail(errors, "smart_core must expose ui_contract_v2 handler")
    if FORBIDDEN_INDUSTRY_PATH.exists():
        _fail(errors, "mobile contract protocol must not live in smart_construction_core")

    source = HANDLER_PATH.read_text(encoding="utf-8") if HANDLER_PATH.exists() else ""
    onchange_source = ONCHANGE_HANDLER_PATH.read_text(encoding="utf-8") if ONCHANGE_HANDLER_PATH.exists() else ""
    mobile_source = MOBILE_CONTRACT_PAGE.read_text(encoding="utf-8") if MOBILE_CONTRACT_PAGE.exists() else ""
    tree = ast.parse(source or "\n")
    assignments = _literal_assignments(tree)
    if assignments.get("INTENT_TYPE") != "ui.contract.v2":
        _fail(errors, "handler INTENT_TYPE must be ui.contract.v2")
    if "UiContractHandler" not in source:
        _fail(errors, "v2 intent must use ui.contract as source authority")
    if "assemble_unified_page_contract_v2" not in source:
        _fail(errors, "v2 intent must assemble Unified Page Contract v2")
    if "trim_unified_page_contract_v2" not in source:
        _fail(errors, "v2 intent must apply terminal client trimming")
    if "resolve_delivery_profile" not in source:
        _fail(errors, "v2 intent must resolve terminal delivery profile")
    for forbidden in ("mobile_contract", "mobileContract", "deviceContract", "construction.contract.mobile"):
        if forbidden in source:
            _fail(errors, f"handler must not introduce mobile private schema: {forbidden}")
    for token in ("statusContract", "globalStatus", "containerStatus", "widgetStatus", "buttonStatus", "collectGlobalStatus", "collectContainerStatus", "collectWidgetStatus", "collectButtonStatus"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must consume v2 status contract token: {token}")
    for token in ("selectorStatus", "collectSelectorStatus", "resolveSelectorStatus", "matchesSelector", "pattern.endsWith('.*')", "selector.startsWith(pattern.slice(0, -1))"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must consume v2 selectorStatus token: {token}")
    for token in ("isPageReadable", "isPageReadonly", "pageAuth", "pageVisible"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must honor v2 globalStatus token: {token}")
    for token in ("containerVisible", "containerDisabled", "walkContainers(asList(row.children), nextState)"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must inherit v2 containerStatus token: {token}")
    for token in ("assemble_unified_page_patch_v2", "unified_page_patch_v2", "include_v2_patch"):
        if token not in onchange_source:
            _fail(errors, f"api.onchange must expose opt-in v2 patch token: {token}")
    for token in ("applyUnifiedPagePatchV2", "dataPatch", "statusPatch", "mergeStatusRows"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must be able to apply v2 patch token: {token}")
    for token in ("layoutPatch", "runtimePatch", "hasLayoutPatch", "hasRuntimePatch", "layoutContract: nextLayout", "runtimeContract: nextRuntime"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must preserve v2 layout/runtime patch token: {token}")
    for token in ("runtimeContract", "contractMeta", "traceLabel", "runtimeLabel", "contractMeta.value.traceId || contractMeta.value.requestId || contractMeta.value.etag || contractMeta.value.snapshotId", "runtimeContract.value.cachePolicy", "retryPolicy.maxRetries"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must expose v2 meta/runtime observability token: {token}")
    for token in ("requestIntentWithRetry", "requestIntentOnce", "currentRuntimeRetryPolicy", "shouldRetryIntentError", "retryDelayMs", "function delay", "retryPolicy.maxRetries || retryPolicy.max_retries", "retryPolicy.timeoutMs || retryPolicy.timeout_ms || retryPolicy.requestTimeoutMs || retryPolicy.request_timeout_ms", "code === 408 || code === 429 || code >= 500", "message.includes('network') || message.includes('timeout')", "setTimeout(resolve, ms)"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must execute v2 runtime retry policy token: {token}")
    for token in ("contractTraceParams", "contractTraceContext", "...contractTraceParams(nextContract)", "...contractTraceParams(contract.value)", "...contractTraceContext(contract.value)", "out.trace_id = traceId", "out.request_id = requestId", "out.contract_etag = meta.etag", "out.snapshot_id = meta.snapshotId || meta.snapshot_id"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must propagate v2 trace context token: {token}")
    for token in ("intentError", "errorDiagnosticLabel", "appendErrorDiagnostic", "bodyError.reason_code || bodyError.reasonCode || bodyError.code", "bodyError.trace_id || bodyError.traceId || asDict(body.meta).trace_id", "normalizeError(err, '业务数据读取失败')", "normalizeError(err, '子表加载失败')", "normalizeError(err, '动作执行失败').slice(0, 48)"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must surface v2 diagnostic errors token: {token}")
    for token in ("tableRowsPatch", "relationRowsPatch", "treeDataPatch", "ganttDataPatch", "dictDataPatch", "paginationPatch", "hasDataContractPatch", "dataContract: nextData"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must merge v2 dataPatch token: {token}")
    for token in ("mergeRowsByDataKey", "extractPatchRows", "isReplaceDataPatch", "syncRecordsFromDataPatch(nextData)", "patch.updateType === 'full'", "rowOperation === 'replace'", "mergeRowsById(asList(baseRowsByKey[key])"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must preserve v2 row patch merge semantics token: {token}")
    for token in ("key === 'line_patches'", "applyLinePatches", "applyLinePatchRows", "linePatch.dataKey || linePatch.data_key || linePatch.field", "row_state || linePatch.state", "command_hint || linePatch.command", "baseRows.filter((row) => !matches(row))"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must apply v2 relation line_patches token: {token}")
    for token in ("removeRelationRow", "confirmRelationRowRemove", "relation-block__remove", "row_state: 'delete'", "command_hint: ['unlink']", "pushWarningMessages([`${block.label} 行已标记移除，保存后生效`])", "currentRelationRows", "params.relationRows = currentRelationRows()", "params.relation_rows = currentRelationRows()", "relationRowKey"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must provide bounded v2 relation row removal token: {token}")
    for token in ("RelationEditorState", "relationEditor", "relationEditorFields", "relation-block__add", "relation-block__edit", "openCreateRelationRow", "editRelationRow", "saveRelationEditor", "relationEditorInitialValues", "handleRelationEditorInput", "row_state: mode === 'create' ? 'create' : 'update'", "command_hint: [mode === 'create' ? 'create' : 'update']", "patch: { ...relationEditor.value.values }", "pushWarningMessages([`${block.label} 行已${mode === 'create' ? '新增' : '更新'}，保存后生效`])"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must provide bounded v2 relation row add/edit token: {token}")
    for token in ("hydrateInlineRecords", "hasInlineData", "hasInlineRows", "firstInlineRows", "firstRecordList", "dataContract.mainData", "dataContract.tableRows", "dataContract.treeData"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must render v2 inline dataContract rows token: {token}")
    for token in ("InlineRecordSet", "firstInlineRecordSet", "activeRecordDataKey", "dataSources[inlineSet.key]", "syncRecordDataContractRows", "requestParams.data_key = recordDataKey", "[rowSection]:", "pagination[inlineSet.key]"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must keep v2 tableRows/treeData pagination source aligned token: {token}")
    for token in ("dictKey", "formatFieldValue", "resolveDictLabel", "dictData[dictKey]", "row.label || row.name || row.display_name"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must map v2 dictData labels token: {token}")
    for token in ("RelationBlock", "relationBlocks", "collectRelationBlocks", "isRelationWidget", "formatRelationRow", "currentDataContract.relationRows", "widget.dataKey"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must render v2 relationRows token: {token}")
    for token in ("summaryFields", "collectSummaryFields", "resolveRelationSummaryFields", "fieldNamesFromList", "currentDataContract.dataMeta", "meta.summaryFields || meta.summary_fields"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must use v2 relation summary metadata token: {token}")
    for token in ("currentDataContract.pagination", "moreCount", "Math.max(0, total - visibleRows.length)", "relation-block__more"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must expose v2 relation pagination token: {token}")
    for token in ("resolveRelationDataSource", "block.canLoadMore", "loadMoreRelationRows", "mergeRelationRowsResponse", "extractRelationResponseRows", "mergeRowsById", "dataSources[dataKey] || dataSources[widget.fieldCode] || dataSources[widget.widgetId]", "relationRows: {"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must load v2 relationRows from dataSource token: {token}")
    for token in ("globalPatch", "containerPatchRows", "mergeStatusRows(asList(currentStatus.containerStatus), containerPatchRows, 'containerId')", "...asDict(currentStatus.globalStatus), ...globalPatch"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must merge v2 statusPatch token: {token}")
    for token in ("selectorPatchRows", "mergeStatusRows(asList(currentStatus.selectorStatus), selectorPatchRows, 'selector')"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must merge v2 selectorStatus patch token: {token}")
    for token in ("refreshMode", "normalizeRefreshMode", "applyActionRefreshMode", "mode === 'none'", "mode === 'full'", "loadRecords(endpoint, token, contract.value, false)"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must honor v2 action refreshMode token: {token}")
    for token in ("targetIds", "dependencyTargets", "collectActionDependencyTargets", "action.dependencyGraph", "actionRefreshTargets", "needsFullContractRefresh", "target.startsWith('relationrows.')", "applyActionRefreshMode(action.refreshMode, runtime.endpoint, runtime.token, action)", "applyActionRefreshMode(action.refreshMode, endpoint, token, action)"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must honor v2 action target dependencies token: {token}")
    for token in ("targetScope", "normalizeActionTargetScope", "row.targetScope || row.target_scope", "targetScope === 'runtime' || targetScope === 'contract'", "targetScope === 'dataSource' || targetScope === 'data_source'", "await loadContract()", "await loadRecords(endpoint, token, contract.value, false)", "scope === 'datasource'"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must honor v2 targetScope refresh token: {token}")
    for token in ("commandActions", "isEditableField", "handleFieldInput", "scheduleFieldAction", "runFieldAction", "resolveFieldAction", "intent: 'api.onchange'", "include_v2_patch: true", "contract_version: contractVersion.value", "changed_fields: [field.fieldCode]", "applyOnchangeDataPatch", "fieldActionTimer", "submitPolicy", "resolveActionDebounceMs", "action.dispatchMode !== 'serverDebounced'", "action.submitPolicy.debounceMs || action.submitPolicy.debounce_ms"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must trigger v2 field onchange token: {token}")
    for token in ("valueType", "editableInputType", ":type=\"editableInputType(field)\"", "['input', 'number', 'date', 'datetime'].includes(type)", "type.includes('number') || type.includes('integer') || type.includes('float') || type.includes('monetary')", "normalizeEditableValue", "setEditableFieldValue(field, normalizeEditableValue(field, detail.value))", "Number.isFinite(numberValue) ? numberValue : value"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must preserve v2 editable value types token: {token}")
    for token in ("isDateField", "isDateTimeField", "mode=\"date\"", "mode=\"time\"", "handleDateChange", "handleDateTimeDateChange", "handleDateTimeTimeChange", "datePickerValue", "timePickerValue", "combineDateTimeValue", "field-row__datetime", "`${datePart} ${timePart}:00`"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must map v2 date/datetime controls token: {token}")
    for token in ("isBooleanField", "isSelectionField", "handleBooleanChange", "handleSelectionChange", "setEditableFieldValue", "selectionOptions", "selectionIndex", "<switch", "<picker", "range-key=\"label\"", "dictData[dictKey]", "row.value ?? row.key ?? row.id"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must map v2 compact field controls token: {token}")
    for token in ("isRemoteSelectionField", "loadFieldOptions", "mergeFieldOptions", "clearFieldOptionsByFieldCodes", "type.includes('select') || type.includes('selection') || type.includes('radio')", "v-else-if=\"isRemoteSelectionField(field)\"", "@click=\"loadFieldOptions(field)\"", "mergeFieldOptions(field, asDict(response.data))"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must load v2 remote selection options token: {token}")
    for token in ("isMany2OneField", "handleMany2OneChange", "many2OneOptions", "many2OneIndex", "type.includes('many2one') || type.includes('select.remote')", "setEditableFieldValue(field, [option.value, option.label])"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must map v2 local many2one controls token: {token}")
    for token in ("isRemoteSearchableMany2OneField", "optionSearchText", "handleOptionSearchInput", "optionSearchValue", "fieldOptionSearchParams", "name_search: keyword", "search: keyword", "query: keyword", "confirm-type=\"search\"", "@confirm=\"loadFieldOptions(field)\"", "field-row__remote", "field-row__search"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must provide v2 many2one remote search token: {token}")
    for token in ("isRemoteMany2OneField", "fieldOptionKey", "resolveFieldOptionDataSource", "loadMany2OneOptions", "mergeMany2OneOptions", "many2OneLoadingKey", "dataSources[key] || dataSources[field.fieldCode] || dataSources[field.widgetId]", "intent: sourceIntent", "dataKey: key", "asDict(data.dictData)[key]", "[key]: rows", "normalizeError(err, '选项加载失败').slice(0, 48)"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must load v2 remote many2one options token: {token}")
    for token in ("optionDomain", "optionDomainRaw", "optionContextRaw", "fieldOptionDomainParams", "params.domain_raw = domainRaw", "params.context_raw = contextRaw", "params.domain = field.optionDomain", "clearFieldOptionsByFieldCodes", "delete dictData[key]", "domainChangedFields", "status.domain = row.domain", "status.domain_raw = row.domain_raw || row.domainRaw"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must refetch v2 field options with domain token: {token}")
    for token in ("isExecutableCommandAction", "hasContractTarget", "action.intent === 'execute_button'", "action.intent === 'api.data'", "action.intent === 'ui.contract'", "Boolean(asText(action.button.name || action.actionKey))", "target.scene_key || target.sceneKey"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must filter executable v2 command actions token: {token}")
    for token in ("STANDARD_FORM_ACTIONS", "'form.save', 'form.validate', 'record.delete'", "isStandardFormAction", "executeStandardFormAction", "standardFormActionParams", "currentRecordValues", "confirmDestructiveAction", "intent: action.intent", "params.values = currentRecordValues()", "params.record_id = resId", "action.intent === 'record.delete'"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must dispatch standard v2 form commands token: {token}")
    for token in ("tracePolicy", "onchangeRequestId", "action.tracePolicy.required === true", "`mobile.${action.actionId}.${Date.now()}`", "action_id: action.actionId", "source_widget_id: action.sourceWidgetId", "trigger_type: action.triggerType", "request_id: requestId"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must honor v2 onchange tracePolicy token: {token}")
    for token in ("applyOnchangeModifiersPatch", "data.modifiers_patch || data.modifiersPatch", "Object.entries(asDict(raw))", "widgetId: `field.${fieldCode}`", "status.readonly = Boolean(row.readonly)", "status.required = Boolean(row.required)", "status.visible = !row.invisible", "applyUnifiedPagePatchV2({ statusPatch: { widgetStatus: rows } })"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must fallback onchange modifiers_patch token: {token}")
    for token in ("applyOnchangeLinePatches", "data.line_patches || data.linePatches", "asList(raw).map((item) => asDict(item))", "applyUnifiedPagePatchV2({ dataPatch: { relationRows: { line_patches: rows } } })"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must fallback onchange line_patches token: {token}")
    for token in ("applyResponseUnifiedPagePatch", "response.unified_page_patch_v2", "data.unified_page_patch_v2 || data.unifiedPagePatchV2", "applyUnifiedPagePatchV2(patch)", "appliedPatch && normalizeRefreshMode(action.refreshMode) === 'none'"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must consume v2 action response patch token: {token}")
    for token in ("showActionResponseFeedback", "firstResponseWarning", "response.warnings", "data.warnings", "effect.message || result.message || data.message", "type === 'toast'", "uni.showToast({ title: message.slice(0, 48)"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must expose v2 action feedback token: {token}")
    for token in ("warningMessages", "warningTimer", "warning-stack", "collectResponseWarnings", "pushWarningMessages", "clearWarningMessages", "warningMessages.value = next", "setTimeout(() => {", "warningMessages.value = []", "slice(0, 4)"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must keep durable v2 warning feedback token: {token}")
    for token in ("parseMaybeJsonRecord", "actionTargetModel", "actionExecutionContext", "target.target_model", "target.view_mode", "context,"):
        if token not in mobile_source:
            _fail(errors, f"mobile terminal renderer must preserve v2 action target/button metadata token: {token}")

    assembler = _load(ASSEMBLER_PATH, "odoo.addons.smart_core.core.upc_v2_intent_guard_assembler")
    client = _load(CLIENT_PATH, "odoo.addons.smart_core.core.upc_v2_intent_guard_client")
    sample = {
        "title": "契约运行",
        "model": "construction.contract",
        "view_type": "tree",
        "fields": {
            "name": {"string": "名称", "type": "char"},
            "partner_id": {"string": "供应商", "type": "many2one"},
        },
        "buttons": [{"name": "action_confirm", "string": "确认", "type": "object"}],
        "domain_raw": "[('state','=','draft')]",
        "context_raw": "{'search_default_my': 1}",
    }
    contract = assembler.assemble_unified_page_contract_v2(sample, source_type="ui.contract", client_type="harmony_h5")
    contract = client.trim_unified_page_contract_v2(
        contract,
        client_type="harmony_h5",
        delivery_profile="mobile_compact",
        max_widgets=1,
        max_actions=1,
    )
    expected_keys = {
        "pageInfo",
        "layoutContract",
        "statusContract",
        "actionContract",
        "dataContract",
        "runtimeContract",
        "meta",
    }
    if set(contract.keys()) != expected_keys:
        _fail(errors, "v2 contract top-level keys drifted")
    if contract.get("pageInfo", {}).get("contractVersion") != "2.1.0":
        _fail(errors, "v2 contract version must stay 2.1.0")
    if contract.get("pageInfo", {}).get("clientType") != "harmony_h5":
        _fail(errors, "harmony_h5 client type must survive v2 assembly and trimming")
    if contract.get("layoutContract", {}).get("adaptMode") != "mobile":
        _fail(errors, "harmony_h5 must use mobile adapt mode")
    primary_source = (((contract.get("dataContract") or {}).get("dataSource") or {}).get("primary") or {})
    if primary_source.get("intent") != "api.data":
        _fail(errors, "list/tree v2 contracts must declare primary api.data dataSource")
    primary_params = primary_source.get("params") if isinstance(primary_source.get("params"), dict) else {}
    if primary_params.get("model") != "construction.contract":
        _fail(errors, "primary dataSource must carry model from contract source")
    if "fields" not in primary_params:
        _fail(errors, "primary dataSource must carry explicit fields")
    if primary_params.get("domain_raw") != "[('state','=','draft')]":
        _fail(errors, "primary dataSource must inherit domain_raw from v2 source")
    if primary_params.get("context_raw") != "{'search_default_my': 1}":
        _fail(errors, "primary dataSource must inherit context_raw from v2 source")
    actions = (contract.get("actionContract", {}) or {}).get("actionRuleList") or []
    if not actions or actions[0].get("label") != "确认" or actions[0].get("intent") != "execute_button":
        _fail(errors, "v2 action rules must carry renderable label and intent from source contract")
    if (actions[0].get("button") or {}).get("name") != "action_confirm":
        _fail(errors, "v2 execute_button action rules must carry original button name")
    widgets = ((contract.get("layoutContract", {}).get("containerTree") or [{}])[0].get("widgetList") or [])
    if len(widgets) != 1:
        _fail(errors, "mobile_compact must trim delivered widgets")
    meta = contract.get("meta", {}) if isinstance(contract.get("meta"), dict) else {}
    if meta.get("sourceType") != "ui.contract":
        _fail(errors, "mobile_compact must keep sourceType as ui.contract")
    if "compat" in meta:
        _fail(errors, "mobile_compact contract meta.compat must be removed")
    delivery_trim = contract.get("meta", {}).get("deliveryTrim") or {}
    if delivery_trim.get("omitted", {}).get("widgets", 0) < 1:
        _fail(errors, "mobile_compact must report omitted widgets")

    form_sample = {
        "title": "合同表单",
        "model": "construction.contract",
        "view_type": "form",
        "fields": {
            "name": {"string": "名称", "type": "char"},
            "amount_final": {"string": "金额", "type": "monetary"},
        },
        "record_id": 42,
    }
    form_contract = assembler.assemble_unified_page_contract_v2(form_sample, source_type="ui.contract", client_type="harmony_h5")
    form_primary = (((form_contract.get("dataContract") or {}).get("dataSource") or {}).get("primary") or {})
    form_params = form_primary.get("params") if isinstance(form_primary.get("params"), dict) else {}
    if form_params.get("op") != "read" or form_params.get("ids") != [42]:
        _fail(errors, "form v2 contracts with record_id must declare primary api.data read dataSource")
    action_sample = {
        "title": "合同表单",
        "model": "construction.contract",
        "view_type": "form",
        "fields": {"name": {"string": "名称", "type": "char"}},
        "buttons": [
            {
                "key": "module.action_contract",
                "kind": "open",
                "label": "打开合同",
                "intent": "open",
                "payload": {"action_id": 99, "view_mode": "tree,form"},
                "target_model": "construction.contract",
            },
            {
                "key": "module.server_action_contract",
                "kind": "server",
                "label": "服务端动作",
                "intent": "execute",
                "payload": {"server_action_id": 77, "xml_id": "module.server_action_contract"},
            },
        ],
        "record_id": 42,
    }
    action_contract = assembler.assemble_unified_page_contract_v2(action_sample, source_type="ui.contract", client_type="harmony_h5")
    action_rules = (action_contract.get("actionContract") or {}).get("actionRuleList") or []
    open_rule = next((row for row in action_rules if row.get("label") == "打开合同"), {})
    server_rule = next((row for row in action_rules if row.get("label") == "服务端动作"), {})
    if open_rule.get("intent") != "ui.contract" or (open_rule.get("target") or {}).get("action_id") != 99:
        _fail(errors, "v2 open actions must become ui.contract targets")
    if (server_rule.get("button") or {}).get("type") != "server_action" or (server_rule.get("button") or {}).get("server_action_id") != 77:
        _fail(errors, "v2 server actions must preserve server_action button metadata")

    if errors:
        print("Unified Page Contract v2 intent guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Unified Page Contract v2 intent guard passed: platform ui.contract.v2 is the only terminal entry")
    return 0


if __name__ == "__main__":
    sys.exit(main())
