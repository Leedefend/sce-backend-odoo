/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed, reactive, ref } from 'vue';
import type { FieldDescriptor } from '@sc/schema';
import type { NativeFormLayoutNode } from '../../components/template/NativeFormTreeRenderer.vue';
import type {
  FormConfigAuditResult,
  LowCodeFieldSize,
} from './types';
import type { LowCodeLayoutDraftRow } from './formConfigHelpers';
import { useRecordFormDesignerPresentation } from './useRecordFormDesignerPresentation';
import { useRecordFormDesignerPersistence } from './useRecordFormDesignerPersistence';

type DesignerDependencies = Record<string, any>;

/** Owns the administrator-only form design state and operations. */
export function useRecordFormDesigner(dependencies: DesignerDependencies) {
  const { BUSINESS_CONFIG_INTENTS, BUSINESS_CONFIG_MODES, BUSINESS_CONFIG_ROUTE_FLAGS, FORM_FIELD_CONFIG_INTENTS, actionId, activeContractMode, applyClientMode, applyPageStatusEvent, buildCurrentFormGroupOptions, buildFormConfigFieldLabelReplacementEntries, buildFormDesignerGroupNavigatorItems, buildFormDesignerSearchableFieldRows, buildFormFieldConfigScope, buildLowCodeViewOrchestrationFromDraft, busy, busyKind, changedFieldGroupFromDrafts, changedFieldVisibilityFromDrafts, collectLowCodeLayoutFromViewOrchestration, collectNativeFieldStructureGroups, collectNativeLayoutGroupTitles, contract, contractActionRuleClientMode, contractActionRuleControl, contractActionRuleKey, contractFieldLabel, contractFieldSequence, contractModeFeedback, contractV2ActionRules, currentBusinessCategoryLabel, effectiveFieldGroupTitleFromDrafts, ensureFieldOrderDraftStartsFromCurrentLayout, errorMessage, extractLowCodeFormFieldDraftState, extractLowCodeLayoutDraftState, filterFormDesignerFieldRows, formSettingsActiveTab, formatFormConfigAuditSummary, formatFormConfigOperationSummaryText, inferLowCodeLayoutColumns, intentRequest, isBusinessConfigRuntimeModel, isReadableFieldGroupTitle, isSuggestedInternalFormField, layoutHasReadableFieldGroups, lowCodeApplyBaseParams, lowCodeFormSpecFromViews, lowCodeLayoutFieldLabelFromNodes, lowCodeLayoutFromFormSpec, lowCodeScopedContractName, lowCodeViewsFromContractResponse, mergeLowCodeLayoutWithRuntimeGroupShells, model, nativeFormLayoutNodes, normalizeConfigPageLabel, normalizeContractV2ContainersForNativeFormFromTree, normalizeFieldGroupTitle, normalizeFormConfigAuditResult, normalizeLowCodeContractListRows, pageDisplayTitle, parseMaybeJsonRecord, rawNativeFormLayoutNodes, readableFallbackFieldLabel, reload, resolveContractV2ContainerTree, resolveFormDesignFieldLabel, resolveSelectedFormSettingsFieldGroupTitle, resolveUnifiedPageContractV2, route, routeQueryText, runtimeNativeFormLayoutNodes, session, showHud, status, useContractModeActionRuntime, useFieldOrderDragRuntime, useFieldOrderMutationRuntime, useFieldVisibilityDraftRuntime, useFormConfigOperationLog, useFormConfigSaveRuntime, useFormSettingsGroupRuntime, useFormSettingsLayoutRuntime, useInlineFieldPolicyRuntime, useLowCodeFieldCreateRuntime, v2ContractStore } = dependencies;
  const requestIntent = intentRequest as <T = unknown>(payload: Record<string, unknown>) => Promise<T>;
  const fieldOrderDraft = ref<string[]>([]);
  const fieldOrderPreviewActive = ref(false);
  const nativeFormDesignFieldKeys = ref<string[]>([]);
  const nativeFormDesignFieldLabels = ref<Record<string, string>>({});
  const formConfigFieldLabelCache = reactive<Record<string, string>>({});
  const fieldGroupBase = ref<Record<string, string>>({});
  const fieldGroupSavedBase = ref<Record<string, string>>({});
  const fieldGroupDraft = reactive<Record<string, string>>({});
  const formLayoutColumnsBase = ref<1 | 2 | 3>(3);
  const formLayoutColumnsDraft = ref<1 | 2 | 3>(3);
  const formLayoutColumnsConfigured = ref(false);
  const groupVisibilityBase = ref<Record<string, boolean>>({});
  const groupVisibilityDraft = reactive<Record<string, boolean>>({});
  const groupColumnsBase = ref<Record<string, 1 | 2 | 3>>({});
  const groupColumnsDraft = reactive<Record<string, 1 | 2 | 3>>({});
  const fieldSizeBase = ref<Record<string, LowCodeFieldSize>>({});
  const fieldSizeDraft = reactive<Record<string, LowCodeFieldSize>>({});
  const formLayoutDirty = ref(false);
  const groupLayoutDirtyKeys = reactive<Record<string, boolean>>({});
  const fieldLayoutDirtyKeys = reactive<Record<string, boolean>>({});
  const fieldMoveTargetDraft = reactive<Record<string, string>>({});
  const {
    draggingFieldKey,
    draggingFieldLabel,
    dropTargetFieldKey,
    dropTargetPlacement,
    dragStart: onFieldOrderDragStart,
    dragOver: onFieldOrderDragOver,
    dragLeave: onFieldOrderDragLeave,
    dragEnd: onFieldOrderDragEnd,
    windowDragOver: onFieldOrderWindowDragOver,
    windowDragStop: onFieldOrderWindowDragStop,
    resetDropTarget: resetFieldOrderDropTarget,
  } = useFieldOrderDragRuntime({
    enabled: () => isContractFieldOrderEditable.value,
    resolveFieldLabel: (fieldKey) => formDesignFieldLabel(fieldKey),
  });
  const selectedFormSettingsFieldKey = ref('');
  const selectedFormSettingsFieldLabel = ref('');
  const selectedFormSettingsFieldGroupTitleDraft = ref('');
  const selectedFormSettingsFieldGroupTitleEdit = ref('');
  const formDesignerFieldSearchText = ref('');
  const selectedFormSettingsOrderTargetKey = ref('');
  const selectedFormSettingsOrderPlacement = ref<'before' | 'after'>('before');
  const isContractFieldOrderEditable = computed(() => (
    !isBusinessConfigRuntimeModel(model.value)
    && (
      activeContractMode.value === BUSINESS_CONFIG_MODES.formFieldConfiguration
      || activeContractMode.value === BUSINESS_CONFIG_MODES.lowCode
    )
  ));
  const showReturnToBusinessConfigAction = computed(() => (
    routeQueryText(BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig) === '1'
    || activeContractMode.value === BUSINESS_CONFIG_MODES.lowCode
  ));
  const fieldVisibilityBase = ref<Record<string, boolean>>({});
  const fieldVisibilityDirty = ref(false);
  const fieldVisibilityDraft = reactive<Record<string, boolean>>({});
  const fieldVisibilityDirtyKeys = reactive<Record<string, boolean>>({});
  const formConfigAuditBusy = ref(false);
  const formConfigAuditResult = ref<FormConfigAuditResult | null>(null);
  const {
    operationLog: formConfigOperationLog,
    operatorName: formConfigOperatorName,
    appendOperation: appendFormConfigOperation,
    markPendingOperations: markPendingFormConfigOperations,
    clearOperationLog: clearFormConfigOperationLog,
  } = useFormConfigOperationLog({
    user: () => session.user as Record<string, unknown> | null,
    db: () => route.query.db,
    modelName: () => model.value || route.params.model,
    actionId: () => actionId.value || route.query.action_id,
    viewId: () => routeQueryText('view_id') || routeQueryText('viewId'),
    page: () => routeQueryText('page_label') || routeQueryText('pageLabel') || route.fullPath,
  });
  const {
    onFormLayoutColumnsChange,
    onSelectedFormSettingsGroupVisibilityChange,
    onSelectedFormSettingsGroupColumnsChange,
    onSelectedFormSettingsFieldSizeChange,
    resetContractFieldOrder,
  } = useFormSettingsLayoutRuntime({
    formLayoutColumnsBase,
    formLayoutColumnsDraft,
    formLayoutDirty,
    formConfigAuditResult,
    groupVisibilityBase,
    groupVisibilityDraft,
    groupColumnsBase,
    groupColumnsDraft,
    groupLayoutDirtyKeys,
    fieldSizeBase,
    fieldSizeDraft,
    fieldLayoutDirtyKeys,
    fieldOrderDraft,
    fieldOrderPreviewActive,
    fieldGroupBase,
    fieldGroupSavedBase,
    fieldGroupDraft,
    fieldMoveTargetDraft,
    fieldVisibilityBase,
    fieldVisibilityDraft,
    fieldVisibilityDirty,
    fieldVisibilityDirtyKeys,
    contractModeFeedback,
    currentDesignFieldKeys: () => currentFormDesignFieldKeys.value,
    visibilityDraftFieldKeys: () => formVisibilityDraftFieldKeys.value,
    baseFieldRows: () => contractModeBaseFieldRows.value,
    currentGroupOptions: () => currentFormGroupOptions.value,
    groupNavigatorItems: () => formDesignerGroupNavigatorItems.value,
    selectedGroupTitle: () => selectedFormSettingsFieldGroupTitle.value,
    selectedFieldKey: () => selectedFormSettingsFieldKey.value,
    effectiveGroupVisible: (key) => effectiveGroupVisible(key),
    effectiveGroupColumns: (key) => effectiveGroupColumns(key),
    effectiveFieldSize: (fieldKey) => effectiveFieldSize(fieldKey),
    formDesignFieldLabel: (fieldKey) => formDesignFieldLabel(fieldKey),
    appendOperation: appendFormConfigOperation,
    markPendingOperations: markPendingFormConfigOperations,
  });
  const {
    onContractInlineGroupRename,
  } = useFormSettingsGroupRuntime({
    busy: () => busy.value,
    nativeFormLayoutNodes: () => nativeFormLayoutNodes.value,
    contractFields: () => (contract.value?.fields || {}) as Record<string, FieldDescriptor>,
    currentOrderedFieldKeys: () => currentFormOrderedFieldKeys.value,
    effectiveFieldGroupTitle: (fieldKey) => effectiveFieldGroupTitleForDraft(fieldKey),
    formDesignFieldLabel: (fieldKey) => formDesignFieldLabel(fieldKey),
    contractFieldLabel: (fieldKey) => contractFieldLabel(fieldKey),
    fieldGroupDraft,
    selectedGroupTitleDraft: selectedFormSettingsFieldGroupTitleDraft,
    selectedGroupTitleEdit: selectedFormSettingsFieldGroupTitleEdit,
    formConfigAuditResult,
    contractModeFeedback,
    appendOperation: appendFormConfigOperation,
  });
  const {
    moveFieldOrder,
    moveSelectedFormSettingsFieldToOrderTarget,
    onSelectedFormSettingsFieldGroupMoveChange,
    onFieldOrderDrop,
    onFieldOrderGroupDrop,
  } = useFieldOrderMutationRuntime({
    isEditable: () => isContractFieldOrderEditable.value,
    ensureDraftStartsFromCurrentLayout: () => ensureFieldOrderDraftStartsFromCurrentLayout(),
    fieldOrderDraft,
    fieldOrderPreviewActive,
    currentOrderedFieldKeys: () => currentFormOrderedFieldKeys.value,
    fieldGroupBase,
    fieldGroupDraft,
    fieldMoveTargetDraft,
    selectedFieldKey: selectedFormSettingsFieldKey,
    selectedFieldLabel: selectedFormSettingsFieldLabel,
    selectedGroupTitleDraft: selectedFormSettingsFieldGroupTitleDraft,
    selectedGroupTitleEdit: selectedFormSettingsFieldGroupTitleEdit,
    selectedOrderTargetKey: selectedFormSettingsOrderTargetKey,
    selectedOrderPlacement: selectedFormSettingsOrderPlacement,
    draggingFieldKey,
    draggingFieldLabel,
    formConfigAuditResult,
    formDesignFieldLabel: (fieldKey) => formDesignFieldLabel(fieldKey),
    appendOperation: appendFormConfigOperation,
    resetDropTarget: resetFieldOrderDropTarget,
  });
  const {
    hideSuggestedInternalFields,
    onFieldVisibilityDraftChange,
    onSelectedFormSettingsFieldVisibilityChange,
  } = useFieldVisibilityDraftRuntime({
    fieldVisibilityDraft,
    fieldVisibilityDirty,
    fieldVisibilityDirtyKeys,
    formConfigAuditResult,
    contractModeFeedback,
    selectedFieldKey: () => selectedFormSettingsFieldKey.value,
    suggestedHiddenRows: () => suggestedHiddenFieldRows.value,
    formDesignFieldLabel: (fieldKey) => formDesignFieldLabel(fieldKey),
    appendOperation: appendFormConfigOperation,
  });
  const {
    onContractInlineFieldLabelChange,
    setInlineFieldPolicy,
  } = useInlineFieldPolicyRuntime({
    busy: () => busy.value,
    busyKind,
    errorMessage,
    status,
    contractModeFeedback,
    lowCodeApplyBaseParams: () => lowCodeApplyBaseParams(),
    contractFieldSequence: (fieldKey) => contractFieldSequence(fieldKey),
    formDesignFieldLabel: (fieldKey) => formDesignFieldLabel(fieldKey),
    appendOperation: appendFormConfigOperation,
    reload: () => reload(),
  });
  const {
    closeContractPromptAction,
    contractPromptFields,
    contractPromptRule,
    contractPromptValues,
    openContractModeAction,
    runContractRuleAction,
    setContractPromptValue,
    submitContractPromptAction,
  } = useContractModeActionRuntime({
    busyKind,
    errorMessage,
    status,
    contractModeFeedback,
    applyClientMode: (mode, toggle) => applyClientMode(mode, toggle),
    reload: () => reload(),
  });
  const {
    lowCodeFieldCreateDialog,
    openCentralCustomFieldCreate,
    onContractInlineFieldAddAfter,
    onContractInlineGroupAddField,
    closeInlineCustomFieldCreate,
    setFieldCreateLabel,
    setFieldCreateType,
    submitInlineCustomFieldCreate,
  } = useLowCodeFieldCreateRuntime({
    busy: () => busy.value,
    selectedFieldKey: () => selectedFormSettingsFieldKey.value,
    selectedGroupTitle: () => selectedFormSettingsFieldGroupTitle.value,
    firstGroupTitle: () => currentFormGroupOptions.value[0] || '',
    fieldOrderLength: () => fieldOrderDraft.value.length,
    fieldSequence: (fieldKey, fallback) => contractFieldSequence(fieldKey, fallback),
    submit: async ({ label, ttype, groupTitle, sequence }) => {
      busyKind.value = 'action';
      try {
        await intentRequest({
          intent: FORM_FIELD_CONFIG_INTENTS.customFieldCreate,
          params: {
            ...lowCodeApplyBaseParams(),
            label,
            ttype,
            group_title: groupTitle,
            sequence,
          },
          context: { view: 'form' },
        });
        contractModeFeedback.value = '字段已添加';
        appendFormConfigOperation('新增字段', `${label} 添加到 ${groupTitle}`, 'done');
        await reload();
        return true;
      } catch (err) {
        applyPageStatusEvent({ kind: 'status', transaction: 'formConfig', status: 'error', errorMessage: err instanceof Error ? err.message : '自定义字段创建失败' });
        return false;
      } finally {
        busyKind.value = null;
      }
    },
  });
  const lowCodeContractLoaded = ref(false);
  const lowCodeContractHydrating = ref(false);
  const lowCodePrecheckWarnings = ref<string[]>([]);
  const lowCodeContractList = ref<Array<{ id: number; name: string; model: string; status: string; version_no: number }>>([]);
  const lowCodeSelectedContractName = ref('');
  const lowCodeFormLayoutBase = ref<NativeFormLayoutNode[]>([]);
  const lowCodeLayoutDraft = ref<LowCodeLayoutDraftRow[]>([]);
  const {
    saveContractFieldOrder,
  } = useFormConfigSaveRuntime({
    appendOperation: appendFormConfigOperation,
    buildLowCodeViewOrchestration: () => buildLowCodeViewOrchestration(),
    busyKind,
    changedFieldGroupDraft: () => changedFieldGroupDraft(),
    changedFieldVisibilityDraft: () => changedFieldVisibilityDraft(),
    contractModeFeedback,
    contractV2ActionRules: () => contractV2ActionRules.value,
    errorMessage,
    fieldGroupBase,
    fieldGroupSavedBase,
    fieldLayoutDirtyKeys,
    fieldOrderDraft,
    fieldSizeBase,
    fieldSizeDraft,
    fieldVisibilityBase,
    fieldVisibilityDirty,
    fieldVisibilityDirtyKeys,
    formConfigAuditResult,
    formLayoutColumnsBase,
    formLayoutColumnsDraft,
    formLayoutDirty,
    groupColumnsBase,
    groupColumnsDraft,
    groupLayoutDirtyKeys,
    groupVisibilityBase,
    groupVisibilityDraft,
    hasCurrentFormFieldDraftChanges: () => hasCurrentFormFieldDraftChanges.value,
    hasFieldLayoutChanges: () => hasFieldLayoutChanges.value,
    hasFieldOrderChanges: () => hasFieldOrderChanges.value,
    hasFormLayoutChanges: () => hasFormLayoutChanges.value,
    hasGroupLayoutChanges: () => hasGroupLayoutChanges.value,
    hydrateLowCodeDraftFromContract: () => hydrateLowCodeDraftFromContract(),
    lowCodeContractLoaded,
    lowCodePrecheckWarnings,
    markPendingOperations: markPendingFormConfigOperations,
    modelName: () => model.value,
    changeSetToken: () => String(route.query.change_set_token || '').trim(),
    reload: () => reload(),
    status,
  });

  const {
    contractModeBaseFieldRows, activeContractModeFieldRows, currentFormDesignFieldKeys, currentFormOrderedFieldKeys, selectedFormSettingsOrderTargetOptions,
    syncFieldOrderDraftWithDesignKeys, hasFieldOrderChanges, formVisibilityDraftFieldKeys, hasFieldVisibilityChanges, hasFieldGroupChanges,
    effectiveGroupVisible, effectiveGroupColumns, effectiveFieldSize, hasFormLayoutChanges, hasGroupLayoutChanges,
    hasFieldLayoutChanges, hasCurrentFormFieldDraftChanges, formConfigFieldLabelReplacementEntries, formatFormConfigOperationSummary, formDesignFieldLabel,
    rememberFormConfigFieldLabel, suggestedHiddenFieldRows, changedFieldVisibilityDraft, changedFieldGroupDraft, effectiveFieldGroupTitleForDraft,
  } = useRecordFormDesignerPresentation({
    activeContractMode, applyRuntimeInferredFormColumns: () => applyRuntimeInferredFormColumns(), buildFormConfigFieldLabelReplacementEntries, busy,
    changedFieldGroupFromDrafts, changedFieldVisibilityFromDrafts, contract, contractActionRuleClientMode,
    contractActionRuleControl, contractActionRuleKey, contractFieldLabel, contractV2ActionRules,
    effectiveFieldGroupTitleFromDrafts, fieldGroupBase, fieldGroupDraft, fieldGroupSavedBase,
    fieldLayoutDirtyKeys, fieldMoveTargetDraft, fieldOrderDraft, fieldOrderPreviewActive,
    fieldSizeBase, fieldSizeDraft, fieldVisibilityBase, fieldVisibilityDirty,
    fieldVisibilityDirtyKeys, fieldVisibilityDraft, formConfigAuditResult, formConfigFieldLabelCache,
    formLayoutColumnsBase, formLayoutColumnsConfigured, formLayoutColumnsDraft, formLayoutDirty,
    formSettingsActiveTab, formatFormConfigOperationSummaryText, groupColumnsBase, groupColumnsDraft,
    groupLayoutDirtyKeys, groupVisibilityBase, groupVisibilityDraft, hydrateLowCodeDraftFromContract: () => hydrateLowCodeDraftFromContract(),
    isContractFieldOrderEditable, isSuggestedInternalFormField, loadLowCodeContractList: () => loadLowCodeContractList(), lowCodeContractLoaded,
    lowCodeFormLayoutBase, nativeFormDesignFieldKeys, nativeFormDesignFieldLabels, normalizeFieldGroupTitle,
    parseMaybeJsonRecord, refreshLowCodeFormLayoutBase: () => refreshLowCodeFormLayoutBase(), resolveFormDesignFieldLabel, selectedFormSettingsFieldGroupTitleDraft,
    selectedFormSettingsFieldKey, selectedFormSettingsFieldLabel, selectedFormSettingsOrderTargetKey, v2ContractStore,
  });
  const {
    auditCurrentFormConfiguration, showCurrentFormFieldConfigScope, showLowCodeTechnicalDetails, currentFormConfigPageLabel,
    formFieldConfigScope, formConfigAuditSummary, selectedFormSettingsFieldRow, nativeFieldStructureGroups,
    currentFormDesignFieldCount, currentFormGroupOptions, formDesignerGroupNavigatorItems, formDesignerFieldSearchQuery,
    formDesignerSearchableFieldRows, formDesignerFilteredFieldRows, selectedFormSettingsFieldGroupTitle, selectedFormSettingsGroupVisible,
    selectedFormSettingsGroupColumns, selectedFormSettingsFieldSize, syncLayoutDraftFromFormSpec, syncFieldDraftFromFormSpec,
    applyRuntimeInferredFormColumns, hydrateLowCodeDraftFromContract, refreshLowCodeFormLayoutBase, loadLowCodeContractList,
    switchLowCodeContractByName, publishSelectedLowCodeContract, rollbackSelectedLowCodeContract, buildLowCodeViewOrchestration,
    lowCodeLayoutFieldLabel, effectiveLowCodeFieldLabel,
  } = useRecordFormDesignerPersistence({
    BUSINESS_CONFIG_INTENTS, BUSINESS_CONFIG_MODES, activeContractMode, activeContractModeFieldRows,
    applyPageStatusEvent, buildCurrentFormGroupOptions, buildFormDesignerGroupNavigatorItems, buildFormDesignerSearchableFieldRows,
    buildFormFieldConfigScope, buildLowCodeViewOrchestrationFromDraft, busy, busyKind,
    collectLowCodeLayoutFromViewOrchestration, collectNativeFieldStructureGroups, collectNativeLayoutGroupTitles, contract,
    contractFieldLabel, contractModeFeedback, currentBusinessCategoryLabel, currentFormDesignFieldKeys,
    currentFormOrderedFieldKeys, effectiveFieldGroupTitleForDraft, effectiveFieldSize, effectiveGroupColumns,
    effectiveGroupVisible, extractLowCodeFormFieldDraftState, extractLowCodeLayoutDraftState, fieldGroupBase,
    fieldGroupDraft, fieldGroupSavedBase, fieldLayoutDirtyKeys, fieldOrderDraft,
    fieldSizeBase, fieldSizeDraft, fieldVisibilityBase, fieldVisibilityDraft,
    filterFormDesignerFieldRows, formConfigAuditBusy, formConfigAuditResult, formDesignFieldLabel,
    formDesignerFieldSearchText, formLayoutColumnsBase, formLayoutColumnsConfigured, formLayoutColumnsDraft,
    formLayoutDirty, formatFormConfigAuditSummary, groupColumnsBase, groupColumnsDraft,
    groupLayoutDirtyKeys, groupVisibilityBase, groupVisibilityDraft, inferLowCodeLayoutColumns,
    intentRequest, isContractFieldOrderEditable, isReadableFieldGroupTitle, layoutHasReadableFieldGroups,
    lowCodeApplyBaseParams, lowCodeContractHydrating, lowCodeContractList, lowCodeContractLoaded,
    lowCodeFormLayoutBase, lowCodeFormSpecFromViews, lowCodeLayoutDraft, lowCodeLayoutFieldLabelFromNodes,
    lowCodeLayoutFromFormSpec, lowCodeScopedContractName, lowCodeSelectedContractName, lowCodeViewsFromContractResponse,
    mergeLowCodeLayoutWithRuntimeGroupShells, model, normalizeConfigPageLabel, normalizeContractV2ContainersForNativeFormFromTree,
    normalizeFieldGroupTitle, normalizeFormConfigAuditResult, normalizeLowCodeContractListRows, pageDisplayTitle,
    rawNativeFormLayoutNodes, readableFallbackFieldLabel, requestIntent, resolveContractV2ContainerTree,
    resolveSelectedFormSettingsFieldGroupTitle, resolveUnifiedPageContractV2, routeQueryText, runtimeNativeFormLayoutNodes,
    selectedFormSettingsFieldGroupTitleDraft, selectedFormSettingsFieldGroupTitleEdit, selectedFormSettingsFieldKey, selectedFormSettingsFieldLabel,
    showHud, v2ContractStore,
  });

  return {
    fieldOrderDraft, fieldOrderPreviewActive, nativeFormDesignFieldKeys, nativeFormDesignFieldLabels, formConfigFieldLabelCache,
    fieldGroupBase, fieldGroupSavedBase, fieldGroupDraft, formLayoutColumnsBase, formLayoutColumnsDraft,
    formLayoutColumnsConfigured, groupVisibilityBase, groupVisibilityDraft, groupColumnsBase, groupColumnsDraft,
    fieldSizeBase, fieldSizeDraft, formLayoutDirty, groupLayoutDirtyKeys, fieldLayoutDirtyKeys,
    fieldMoveTargetDraft, draggingFieldKey, draggingFieldLabel, dropTargetFieldKey, dropTargetPlacement,
    onFieldOrderDragStart, onFieldOrderDragOver, onFieldOrderDragLeave, onFieldOrderDragEnd, onFieldOrderWindowDragOver,
    onFieldOrderWindowDragStop, resetFieldOrderDropTarget, selectedFormSettingsFieldKey, selectedFormSettingsFieldLabel, selectedFormSettingsFieldGroupTitleDraft,
    selectedFormSettingsFieldGroupTitleEdit, formDesignerFieldSearchText, selectedFormSettingsOrderTargetKey, selectedFormSettingsOrderPlacement, isContractFieldOrderEditable,
    showReturnToBusinessConfigAction, fieldVisibilityBase, fieldVisibilityDirty, fieldVisibilityDraft, fieldVisibilityDirtyKeys,
    formConfigAuditBusy, formConfigAuditResult, formConfigOperationLog, formConfigOperatorName, appendFormConfigOperation,
    markPendingFormConfigOperations, clearFormConfigOperationLog, onFormLayoutColumnsChange, onSelectedFormSettingsGroupVisibilityChange, onSelectedFormSettingsGroupColumnsChange,
    onSelectedFormSettingsFieldSizeChange, resetContractFieldOrder, onContractInlineGroupRename, moveFieldOrder, moveSelectedFormSettingsFieldToOrderTarget,
    onSelectedFormSettingsFieldGroupMoveChange, onFieldOrderDrop, onFieldOrderGroupDrop, hideSuggestedInternalFields, onFieldVisibilityDraftChange,
    onSelectedFormSettingsFieldVisibilityChange, onContractInlineFieldLabelChange, setInlineFieldPolicy, closeContractPromptAction, contractPromptFields,
    contractPromptRule, contractPromptValues, openContractModeAction, runContractRuleAction, setContractPromptValue,
    submitContractPromptAction, lowCodeFieldCreateDialog, openCentralCustomFieldCreate, onContractInlineFieldAddAfter, onContractInlineGroupAddField,
    closeInlineCustomFieldCreate, setFieldCreateLabel, setFieldCreateType, submitInlineCustomFieldCreate, lowCodeContractLoaded,
    lowCodeContractHydrating, lowCodePrecheckWarnings, lowCodeContractList, lowCodeSelectedContractName, lowCodeFormLayoutBase,
    lowCodeLayoutDraft, saveContractFieldOrder, contractModeBaseFieldRows, activeContractModeFieldRows, currentFormDesignFieldKeys,
    currentFormOrderedFieldKeys, selectedFormSettingsOrderTargetOptions, syncFieldOrderDraftWithDesignKeys, hasFieldOrderChanges, formVisibilityDraftFieldKeys,
    hasFieldVisibilityChanges, hasFieldGroupChanges, effectiveGroupVisible, effectiveGroupColumns, effectiveFieldSize,
    hasFormLayoutChanges, hasGroupLayoutChanges, hasFieldLayoutChanges, hasCurrentFormFieldDraftChanges, formConfigFieldLabelReplacementEntries,
    formatFormConfigOperationSummary, formDesignFieldLabel, rememberFormConfigFieldLabel, suggestedHiddenFieldRows, changedFieldVisibilityDraft,
    changedFieldGroupDraft, effectiveFieldGroupTitleForDraft, auditCurrentFormConfiguration, showCurrentFormFieldConfigScope, showLowCodeTechnicalDetails,
    currentFormConfigPageLabel, formFieldConfigScope, formConfigAuditSummary, selectedFormSettingsFieldRow, nativeFieldStructureGroups,
    currentFormDesignFieldCount, currentFormGroupOptions, formDesignerGroupNavigatorItems, formDesignerFieldSearchQuery, formDesignerSearchableFieldRows,
    formDesignerFilteredFieldRows, selectedFormSettingsFieldGroupTitle, selectedFormSettingsGroupVisible, selectedFormSettingsGroupColumns, selectedFormSettingsFieldSize,
    syncLayoutDraftFromFormSpec, syncFieldDraftFromFormSpec, applyRuntimeInferredFormColumns, hydrateLowCodeDraftFromContract, refreshLowCodeFormLayoutBase,
    loadLowCodeContractList, switchLowCodeContractByName, publishSelectedLowCodeContract, rollbackSelectedLowCodeContract, buildLowCodeViewOrchestration,
    lowCodeLayoutFieldLabel, effectiveLowCodeFieldLabel,
  };
}
