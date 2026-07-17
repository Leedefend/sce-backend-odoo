/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed, watch } from 'vue';
import type { FieldDescriptor } from '@sc/schema';
import type { NativeFormLayoutNode } from '../../components/template/NativeFormTreeRenderer.vue';
import type { NativeLayoutLikeNode } from './nativeLayoutUtils';
import type { LowCodeFieldSize } from './types';

type PersistenceDependencies = Record<string, any>;

export function useRecordFormDesignerPersistence(dependencies: PersistenceDependencies) {
  const { BUSINESS_CONFIG_INTENTS, BUSINESS_CONFIG_MODES, activeContractMode, activeContractModeFieldRows, applyPageStatusEvent, buildCurrentFormGroupOptions, buildFormDesignerGroupNavigatorItems, buildFormDesignerSearchableFieldRows, buildFormFieldConfigScope, buildLowCodeViewOrchestrationFromDraft, busy, busyKind, collectLowCodeLayoutFromViewOrchestration, collectNativeFieldStructureGroups, collectNativeLayoutGroupTitles, contract, contractFieldLabel, contractModeFeedback, currentBusinessCategoryLabel, currentFormDesignFieldKeys, currentFormOrderedFieldKeys, effectiveFieldGroupTitleForDraft, effectiveFieldSize, effectiveGroupColumns, effectiveGroupVisible, extractLowCodeFormFieldDraftState, extractLowCodeLayoutDraftState, fieldGroupBase, fieldGroupDraft, fieldGroupSavedBase, fieldLayoutDirtyKeys, fieldOrderDraft, fieldSizeBase, fieldSizeDraft, fieldVisibilityBase, fieldVisibilityDraft, filterFormDesignerFieldRows, formConfigAuditBusy, formConfigAuditResult, formDesignFieldLabel, formDesignerFieldSearchText, formLayoutColumnsBase, formLayoutColumnsConfigured, formLayoutColumnsDraft, formLayoutDirty, formatFormConfigAuditSummary, groupColumnsBase, groupColumnsDraft, groupLayoutDirtyKeys, groupVisibilityBase, groupVisibilityDraft, inferLowCodeLayoutColumns, intentRequest, isContractFieldOrderEditable, isReadableFieldGroupTitle, layoutHasReadableFieldGroups, lowCodeApplyBaseParams, lowCodeContractHydrating, lowCodeContractList, lowCodeContractLoaded, lowCodeFormLayoutBase, lowCodeFormSpecFromViews, lowCodeLayoutDraft, lowCodeLayoutFieldLabelFromNodes, lowCodeLayoutFromFormSpec, lowCodeScopedContractName, lowCodeSelectedContractName, lowCodeViewsFromContractResponse, mergeLowCodeLayoutWithRuntimeGroupShells, model, normalizeConfigPageLabel, normalizeContractV2ContainersForNativeFormFromTree, normalizeFieldGroupTitle, normalizeFormConfigAuditResult, normalizeLowCodeContractListRows, pageDisplayTitle, rawNativeFormLayoutNodes, readableFallbackFieldLabel, requestIntent, resolveContractV2ContainerTree, resolveSelectedFormSettingsFieldGroupTitle, resolveUnifiedPageContractV2, routeQueryText, runtimeNativeFormLayoutNodes, selectedFormSettingsFieldGroupTitleDraft, selectedFormSettingsFieldGroupTitleEdit, selectedFormSettingsFieldKey, selectedFormSettingsFieldLabel, showHud, v2ContractStore } = dependencies;
  const typedRequestIntent = requestIntent as <T = unknown>(payload: Record<string, unknown>) => Promise<T>;
  async function auditCurrentFormConfiguration() {
    if (formConfigAuditBusy.value || busy.value) return;
    const params = lowCodeApplyBaseParams();
    const modelName = String(params.model || model.value || '').trim();
    if (!modelName) return;
    formConfigAuditBusy.value = true;
    try {
      const result = await typedRequestIntent<{
        business_config_form_fields?: unknown[];
        business_config_form_layout_fields?: unknown[];
        has_business_config_form_layout?: boolean;
        layout_matches_fields?: boolean;
        legacy_policy_fields?: unknown[];
        skipped_legacy_policy_fields?: unknown[];
        active_legacy_policy_fields?: unknown[];
        has_conflict?: boolean;
      }>({
        intent: BUSINESS_CONFIG_INTENTS.formAudit,
        params: {
          ...params,
          model: modelName,
          view_type: 'form',
        },
        context: { view: 'form' },
      });
      formConfigAuditResult.value = normalizeFormConfigAuditResult(result);
    } catch (err) {
      applyPageStatusEvent({ kind: 'status', transaction: 'formConfig', status: 'error', errorMessage: err instanceof Error ? err.message : '表单配置检查失败' });
    } finally {
      formConfigAuditBusy.value = false;
    }
  }

  const showCurrentFormFieldConfigScope = computed(() => isContractFieldOrderEditable.value);
  const showLowCodeTechnicalDetails = computed(() => {
    if (activeContractMode.value !== BUSINESS_CONFIG_MODES.lowCode) return showHud.value;
    const hudFlag = routeQueryText('hud').toLowerCase();
    const surface = routeQueryText('surface').toLowerCase();
    return hudFlag === '1' || hudFlag === 'true' || surface === 'hud';
  });

  const currentFormConfigPageLabel = computed(() => normalizeConfigPageLabel(
    routeQueryText('page_label')
    || routeQueryText('pageLabel')
    || currentBusinessCategoryLabel.value
    || pageDisplayTitle.value
    || '当前表单',
  ));

  const formFieldConfigScope = computed(() => buildFormFieldConfigScope(currentFormConfigPageLabel.value));

  const formConfigAuditSummary = computed(() => {
    return formatFormConfigAuditSummary(formConfigAuditResult.value, showLowCodeTechnicalDetails.value);
  });

  const selectedFormSettingsFieldRow = computed(() => {
    const fieldKey = selectedFormSettingsFieldKey.value;
    if (!fieldKey) return undefined;
    const row = activeContractModeFieldRows.value.find((item) => item.fieldKey === fieldKey);
    if (!row) {
      const label = selectedFormSettingsFieldLabel.value || fieldKey;
      const visible = Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)
        ? fieldVisibilityDraft[fieldKey]
        : true;
      return {
        fieldKey,
        label,
        actions: [
          {
            key: `${fieldKey}:show`,
            label: '显示',
            value: 'show',
            checked: visible,
            disabled: busy.value,
            title: '在当前页面显示这个字段',
            raw: {},
          },
          {
            key: `${fieldKey}:hide`,
            label: '隐藏',
            value: 'hide',
            checked: !visible,
            disabled: busy.value,
            title: '在当前页面隐藏这个字段',
            raw: {},
          },
        ],
      };
    }
    return {
      ...row,
      label: selectedFormSettingsFieldLabel.value || row.label || fieldKey,
    };
  });

  const nativeFieldStructureGroups = computed<Array<{ key: string; title: string; fieldKeys: string[] }>>(() => {
    const lowCodeLayout = lowCodeFormLayoutBase.value;
    const useLowCodeLayout = isContractFieldOrderEditable.value && layoutHasReadableFieldGroups(lowCodeLayout);
    const legacyLayout = Array.isArray(contract.value?.views?.form?.layout)
      ? contract.value?.views?.form?.layout as unknown as NativeFormLayoutNode[]
      : [];
    const storeContainers = resolveContractV2ContainerTree(v2ContractStore.value);
    const v2 = storeContainers.length ? null : resolveUnifiedPageContractV2(contract.value);
    const containers = storeContainers.length
      ? storeContainers
      : (Array.isArray(v2?.layoutContract?.containerTree) ? v2.layoutContract.containerTree : []);
    const baseLayout = useLowCodeLayout
      ? mergeLowCodeLayoutWithRuntimeGroupShells(lowCodeLayout, runtimeNativeFormLayoutNodes())
      : (isContractFieldOrderEditable.value && legacyLayout.length
        ? legacyLayout
        : (containers.length
          ? normalizeContractV2ContainersForNativeFormFromTree(containers as unknown as NativeLayoutLikeNode[]) as NativeFormLayoutNode[]
          : legacyLayout));
    return collectNativeFieldStructureGroups(baseLayout as NativeLayoutLikeNode[]);
  });

  watch(nativeFieldStructureGroups, (groups) => {
    const nextBase: Record<string, string> = {};
    groups.forEach((group) => {
      const title = normalizeFieldGroupTitle(group.title || '主表区域');
      group.fieldKeys.forEach((fieldKey) => {
        if (fieldKey && !nextBase[fieldKey]) nextBase[fieldKey] = title;
      });
    });
    const preservedBase = Object.entries(fieldGroupBase.value).reduce<Record<string, string>>((acc, [fieldKey, title]) => {
      const key = String(fieldKey || '').trim();
      const normalized = normalizeFieldGroupTitle(title);
      if (key && isReadableFieldGroupTitle(normalized)) acc[key] = normalized;
      return acc;
    }, {});
    fieldGroupBase.value = { ...nextBase, ...preservedBase };
    currentFormDesignFieldKeys.value.forEach((fieldKey) => {
      if (!fieldKey) return;
      const title = fieldGroupBase.value[fieldKey];
      if (title && (!Object.prototype.hasOwnProperty.call(fieldGroupDraft, fieldKey) || !isReadableFieldGroupTitle(fieldGroupDraft[fieldKey]))) {
        fieldGroupDraft[fieldKey] = title;
      }
    });
  }, { immediate: true });

  const currentFormDesignFieldCount = computed(() => {
    if (activeContractModeFieldRows.value.length) return activeContractModeFieldRows.value.length;
    return nativeFieldStructureGroups.value.reduce((total, group) => total + group.fieldKeys.length, 0);
  });

  const currentFormGroupOptions = computed(() => {
    return buildCurrentFormGroupOptions({
      nativeGroups: nativeFieldStructureGroups.value,
      runtimeGroupTitles: collectNativeLayoutGroupTitles(runtimeNativeFormLayoutNodes()),
      fieldKeys: currentFormDesignFieldKeys.value,
      resolveDraftGroupTitle: effectiveFieldGroupTitleForDraft,
    });
  });

  const formDesignerGroupNavigatorItems = computed(() => {
    return buildFormDesignerGroupNavigatorItems({
      nativeGroups: nativeFieldStructureGroups.value,
      fieldKeys: currentFormDesignFieldKeys.value,
      selectedGroupTitle: selectedFormSettingsFieldGroupTitle.value,
      resolveDraftGroupTitle: effectiveFieldGroupTitleForDraft,
    });
  });

  const formDesignerFieldSearchQuery = computed(() => String(formDesignerFieldSearchText.value || '').trim().toLowerCase());

  const formDesignerSearchableFieldRows = computed(() => {
    return buildFormDesignerSearchableFieldRows({
      orderedFieldKeys: currentFormOrderedFieldKeys.value,
      fallbackFieldKeys: currentFormDesignFieldKeys.value,
      nativeGroups: nativeFieldStructureGroups.value,
      resolveDraftGroupTitle: effectiveFieldGroupTitleForDraft,
      resolveFieldLabel: formDesignFieldLabel,
    });
  });

  const formDesignerFilteredFieldRows = computed(() => {
    return filterFormDesignerFieldRows(formDesignerSearchableFieldRows.value, formDesignerFieldSearchQuery.value);
  });

  const selectedFormSettingsFieldGroupTitle = computed(() => {
    return resolveSelectedFormSettingsFieldGroupTitle({
      fieldKey: selectedFormSettingsFieldKey.value,
      draftGroupTitle: effectiveFieldGroupTitleForDraft(selectedFormSettingsFieldKey.value),
      nativeGroups: nativeFieldStructureGroups.value,
      fallbackDraftTitle: selectedFormSettingsFieldGroupTitleDraft.value,
    });
  });

  const selectedFormSettingsGroupVisible = computed(() => effectiveGroupVisible(selectedFormSettingsFieldGroupTitle.value));
  const selectedFormSettingsGroupColumns = computed(() => effectiveGroupColumns(selectedFormSettingsFieldGroupTitle.value));
  const selectedFormSettingsFieldSize = computed(() => effectiveFieldSize(selectedFormSettingsFieldKey.value));

  watch(selectedFormSettingsFieldGroupTitle, (title) => {
    selectedFormSettingsFieldGroupTitleEdit.value = title;
  });

  function syncLayoutDraftFromFormSpec(formSpec: Record<string, unknown>) {
    const runtimeColumns = inferLowCodeLayoutColumns(runtimeNativeFormLayoutNodes()) || inferLowCodeLayoutColumns(rawNativeFormLayoutNodes.value) || 3;
    const next = extractLowCodeLayoutDraftState(formSpec, runtimeColumns) as {
      columnsConfigured: boolean;
      columns: 1 | 2 | 3;
      groupVisible: Record<string, boolean>;
      groupColumns: Record<string, 1 | 2 | 3>;
      fieldSize: Record<string, LowCodeFieldSize>;
    };
    formLayoutColumnsConfigured.value = next.columnsConfigured;
    formLayoutColumnsBase.value = next.columns;
    if (!formLayoutDirty.value) {
      formLayoutColumnsDraft.value = next.columns;
    }
    groupVisibilityBase.value = next.groupVisible;
    if (!Object.keys(groupLayoutDirtyKeys).length) {
      Object.keys(groupVisibilityDraft).forEach((key) => delete groupVisibilityDraft[key]);
      Object.entries(next.groupVisible).forEach(([key, value]) => {
        groupVisibilityDraft[key] = value;
      });
    }
    groupColumnsBase.value = next.groupColumns;
    if (!Object.keys(groupLayoutDirtyKeys).length) {
      Object.keys(groupColumnsDraft).forEach((key) => delete groupColumnsDraft[key]);
      Object.entries(next.groupColumns).forEach(([key, value]) => {
        groupColumnsDraft[key] = value;
      });
    }
    fieldSizeBase.value = next.fieldSize;
    if (!Object.keys(fieldLayoutDirtyKeys).length) {
      Object.keys(fieldSizeDraft).forEach((key) => delete fieldSizeDraft[key]);
      Object.entries(next.fieldSize).forEach(([key, value]) => {
        fieldSizeDraft[key] = value;
      });
    }
  }

  function syncFieldDraftFromFormSpec(
    formSpec: Record<string, unknown>,
    options: { overwriteDraftGroups?: boolean; syncOrder?: boolean; syncVisibility?: boolean } = {},
  ) {
    const state = extractLowCodeFormFieldDraftState(formSpec) as {
      orderedFieldNames: string[];
      visibility: Record<string, boolean>;
      groups: Record<string, string>;
    };
    if (options.syncOrder !== false && state.orderedFieldNames.length) fieldOrderDraft.value = state.orderedFieldNames;
    if (options.syncVisibility !== false) {
      Object.entries(state.visibility).forEach(([key, visible]) => {
        fieldVisibilityBase.value = { ...fieldVisibilityBase.value, [key]: visible };
        fieldVisibilityDraft[key] = visible;
      });
    }
    Object.entries(state.groups).forEach(([key, groupTitle]) => {
      const previousDraft = normalizeFieldGroupTitle(fieldGroupDraft[key]);
      const previousBase = normalizeFieldGroupTitle(fieldGroupBase.value[key]);
      const shouldSyncDraft = options.overwriteDraftGroups
        || !previousDraft
        || previousDraft === previousBase
        || previousDraft.startsWith('默认分组');
      fieldGroupSavedBase.value = { ...fieldGroupSavedBase.value, [key]: groupTitle };
      fieldGroupBase.value = { ...fieldGroupBase.value, [key]: groupTitle };
      if (shouldSyncDraft) fieldGroupDraft[key] = groupTitle;
    });
  }

  function applyRuntimeInferredFormColumns() {
    if (!isContractFieldOrderEditable.value || formLayoutColumnsConfigured.value || formLayoutDirty.value) return;
    const runtimeColumns = inferLowCodeLayoutColumns(runtimeNativeFormLayoutNodes());
    if (!runtimeColumns || runtimeColumns === formLayoutColumnsBase.value) return;
    formLayoutColumnsBase.value = runtimeColumns;
    formLayoutColumnsDraft.value = runtimeColumns;
    Object.keys(groupColumnsDraft).forEach((key) => delete groupColumnsDraft[key]);
    groupColumnsBase.value = {};
  }

  async function hydrateLowCodeDraftFromContract() {
    if (!isContractFieldOrderEditable.value || lowCodeContractLoaded.value || lowCodeContractHydrating.value) return;
    const modelName = String(model.value || '').trim();
    if (!modelName) return;
    let hydrated = false;
    lowCodeContractHydrating.value = true;
    try {
      const base = lowCodeApplyBaseParams();
      const scopedName = lowCodeScopedContractName(modelName, base);
      const listResult = await typedRequestIntent<{
        items?: Array<{ name?: string }>;
      }>({
        intent: BUSINESS_CONFIG_INTENTS.contractList,
        params: { ...base, model: modelName, view_type: 'form' },
      }).catch(() => null);
      const availableNames = new Set((Array.isArray(listResult?.items) ? listResult?.items || [] : [])
        .map((row) => String(row?.name || '').trim())
        .filter(Boolean));
      const contractName = availableNames.has(scopedName) ? scopedName : '';
      if (!contractName) return;
      const res = await typedRequestIntent<{
        contract_json?: {
          objects?: Array<{ name?: string; fields?: Array<{ name?: string; visible?: boolean; order?: number }> }>;
        }
      }>({
        intent: BUSINESS_CONFIG_INTENTS.contractGet,
        params: { ...base, model: modelName, name: contractName, view_type: 'form' },
      }).catch(() => null);
      if (!res) return;
      const orchestrationViews = lowCodeViewsFromContractResponse(res);
      const formSpec = lowCodeFormSpecFromViews(orchestrationViews);
      lowCodeFormLayoutBase.value = lowCodeLayoutFromFormSpec(formSpec) as NativeFormLayoutNode[];
      syncLayoutDraftFromFormSpec(formSpec);
      syncFieldDraftFromFormSpec(formSpec, { overwriteDraftGroups: true });
      lowCodeLayoutDraft.value = collectLowCodeLayoutFromViewOrchestration(orchestrationViews, modelName);
      hydrated = true;
    } catch {
      // ignore low-code contract hydrate failure in form runtime
    } finally {
      if (hydrated) lowCodeContractLoaded.value = true;
      lowCodeContractHydrating.value = false;
    }
  }

  async function refreshLowCodeFormLayoutBase() {
    if (!isContractFieldOrderEditable.value || lowCodeContractHydrating.value) return;
    const modelName = String(model.value || '').trim();
    if (!modelName) return;
    try {
      const base = lowCodeApplyBaseParams();
      const scopedName = lowCodeScopedContractName(modelName, base);
      const res = await typedRequestIntent<{
        contract_json?: { view_orchestration?: Record<string, unknown> }
      }>({
        intent: BUSINESS_CONFIG_INTENTS.contractGet,
        params: { ...base, model: modelName, name: scopedName, view_type: 'form' },
      }).catch(() => null);
      const orchestrationViews = lowCodeViewsFromContractResponse(res);
      const formSpec = lowCodeFormSpecFromViews(orchestrationViews);
      lowCodeFormLayoutBase.value = lowCodeLayoutFromFormSpec(formSpec) as NativeFormLayoutNode[];
      syncLayoutDraftFromFormSpec(formSpec);
      syncFieldDraftFromFormSpec(formSpec, { syncOrder: false, syncVisibility: false });
    } catch {
      // Form config still works from runtime layout if the saved contract cannot be read.
    }
  }

  async function loadLowCodeContractList() {
    if (!isContractFieldOrderEditable.value) return;
    const modelName = String(model.value || '').trim();
    if (!modelName) return;
    try {
      const base = lowCodeApplyBaseParams();
      const result = await typedRequestIntent<{
        items?: Array<{ id?: number; name?: string; model?: string; status?: string; version_no?: number }>;
      }>({
        intent: BUSINESS_CONFIG_INTENTS.contractList,
        params: { ...base, model: modelName, view_type: 'form' },
      });
      lowCodeContractList.value = normalizeLowCodeContractListRows(result?.items);
      if (lowCodeSelectedContractName.value && !lowCodeContractList.value.some((row) => row.name === lowCodeSelectedContractName.value)) {
        lowCodeSelectedContractName.value = '';
      }
      if (!lowCodeSelectedContractName.value && lowCodeContractList.value.length) {
        lowCodeSelectedContractName.value = lowCodeContractList.value[0].name;
      }
    } catch {
      lowCodeContractList.value = [];
    }
  }

  async function switchLowCodeContractByName() {
    const name = String(lowCodeSelectedContractName.value || '').trim();
    const modelName = String(model.value || '').trim();
    if (!name || !modelName) return;
    try {
      const base = lowCodeApplyBaseParams();
      const res = await typedRequestIntent<{
        contract_json?: {
          view_orchestration?: Record<string, unknown>;
        }
      }>({
        intent: BUSINESS_CONFIG_INTENTS.contractGet,
        params: { ...base, model: modelName, name, view_type: 'form' },
      });
      lowCodeContractLoaded.value = false;
      const orchestrationViews = lowCodeViewsFromContractResponse(res);
      const formSpec = lowCodeFormSpecFromViews(orchestrationViews);
      lowCodeFormLayoutBase.value = lowCodeLayoutFromFormSpec(formSpec) as NativeFormLayoutNode[];
      syncLayoutDraftFromFormSpec(formSpec);
      syncFieldDraftFromFormSpec(formSpec, { overwriteDraftGroups: true });
      lowCodeLayoutDraft.value = collectLowCodeLayoutFromViewOrchestration(orchestrationViews, modelName);
    } catch {
      // ignore
    }
  }

  async function publishSelectedLowCodeContract() {
    const name = String(lowCodeSelectedContractName.value || '').trim();
    const modelName = String(model.value || '').trim();
    if (!name || !modelName || busy.value) return;
    busyKind.value = 'action';
    try {
      const base = lowCodeApplyBaseParams();
      await intentRequest({
        intent: BUSINESS_CONFIG_INTENTS.contractPublish,
        params: { ...base, name, model: modelName, view_type: 'form' },
      });
      contractModeFeedback.value = '配置版本已发布，刷新页面后按新配置生效';
      await loadLowCodeContractList();
    } catch (err) {
      applyPageStatusEvent({ kind: 'status', transaction: 'contractMode', status: 'error', errorMessage: err instanceof Error ? err.message : '配置版本发布失败' });
    } finally {
      busyKind.value = null;
    }
  }

  async function rollbackSelectedLowCodeContract() {
    const name = String(lowCodeSelectedContractName.value || '').trim();
    const modelName = String(model.value || '').trim();
    if (!name || !modelName || busy.value) return;
    busyKind.value = 'action';
    try {
      const base = lowCodeApplyBaseParams();
      await intentRequest({
        intent: BUSINESS_CONFIG_INTENTS.contractRollback,
        params: { ...base, name, model: modelName, view_type: 'form' },
      });
      contractModeFeedback.value = '配置版本已回滚到上一版并发布生效';
      await loadLowCodeContractList();
      await switchLowCodeContractByName();
    } catch (err) {
      applyPageStatusEvent({ kind: 'status', transaction: 'contractMode', status: 'error', errorMessage: err instanceof Error ? err.message : '配置版本回滚失败' });
    } finally {
      busyKind.value = null;
    }
  }

  function buildLowCodeViewOrchestration() {
    const availableFields = contract.value?.fields || {};
    return buildLowCodeViewOrchestrationFromDraft({
      availableFieldNames: Object.keys(availableFields),
      layoutDraft: lowCodeLayoutDraft.value,
      formOrderDraft: fieldOrderDraft.value,
      formOrderEditable: isContractFieldOrderEditable.value,
      formColumns: formLayoutColumnsDraft.value,
      resolveFieldLabel: (name) => effectiveLowCodeFieldLabel(name, availableFields[name]),
      resolveFieldGroupTitle: effectiveFieldGroupTitleForDraft,
      resolveFieldVisible: (name, groupTitle) => fieldVisibilityDraft[name] !== false && effectiveGroupVisible(groupTitle),
      resolveGroupVisible: effectiveGroupVisible,
      resolveGroupColumns: effectiveGroupColumns,
      resolveFieldSize: effectiveFieldSize,
    });
  }

  function lowCodeLayoutFieldLabel(name: string) {
    return lowCodeLayoutFieldLabelFromNodes(name, rawNativeFormLayoutNodes.value, lowCodeFormLayoutBase.value);
  }

  function effectiveLowCodeFieldLabel(name: string, descriptor?: FieldDescriptor) {
    const fieldName = String(name || '').trim();
    return String(
      contractFieldLabel(fieldName)
      || lowCodeLayoutFieldLabel(fieldName)
      || descriptor?.string
      || readableFallbackFieldLabel(fieldName),
    ).trim() || readableFallbackFieldLabel(fieldName);
  }


  return {
    auditCurrentFormConfiguration, showCurrentFormFieldConfigScope, showLowCodeTechnicalDetails, currentFormConfigPageLabel, formFieldConfigScope,
    formConfigAuditSummary, selectedFormSettingsFieldRow, nativeFieldStructureGroups, currentFormDesignFieldCount, currentFormGroupOptions,
    formDesignerGroupNavigatorItems, formDesignerFieldSearchQuery, formDesignerSearchableFieldRows, formDesignerFilteredFieldRows, selectedFormSettingsFieldGroupTitle,
    selectedFormSettingsGroupVisible, selectedFormSettingsGroupColumns, selectedFormSettingsFieldSize, syncLayoutDraftFromFormSpec, syncFieldDraftFromFormSpec,
    applyRuntimeInferredFormColumns, hydrateLowCodeDraftFromContract, refreshLowCodeFormLayoutBase, loadLowCodeContractList, switchLowCodeContractByName,
    publishSelectedLowCodeContract, rollbackSelectedLowCodeContract, buildLowCodeViewOrchestration, lowCodeLayoutFieldLabel, effectiveLowCodeFieldLabel,
  };
}
