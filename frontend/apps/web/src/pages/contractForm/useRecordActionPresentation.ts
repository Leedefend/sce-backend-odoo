/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed } from 'vue';
import type { FormSectionFieldChange } from '../../components/template/formSection.types';
import type { RelationFieldAdapter } from '../../components/template/relationField.types';
import type { NativeFormLayoutNode } from '../../components/template/NativeFormTreeRenderer.vue';
import type { ContractAction } from './types';

type PresentationDependencies = Record<string, any>;

/** Owns authoritative action presentation and field interaction adapters. */
export function useRecordActionPresentation(dependencies: PresentationDependencies) {
  const { ErrorCodes, actionId, activeChatterLabel, activeChatterMode, activityAssigneeId, activityDeadline, activityNote, activitySummary, activityUpdatingIds, addOne2manyRow, advancedExpanded, applyPageStatusEvent, applyWorkflowAvailability, attachmentError, attachmentUploading, buildContractFormActions, busy, busyKind, canOpenRelationRecordForm, changedFieldGroupDraft, chatterDraft, chatterError, chatterPosting, chatterTimeline, closeNativeChatterComposer, collaborationUserChoices, collaborationUserOptions, collaborationUserQuery, collaborationUsersLoading, collectContractV2ButtonStatusById, collectSceneValidationPrecheckErrorsFromRules, collectUnifiedPageContractV2ButtonStatus, commitMany2oneInline, confirmActionSafety, contract, detectObjectMethodFromActionKey, dispatchTemplateFieldChange, effectiveFieldSize, effectiveGroupVisible, ensureSavedBeforeRecordAction, executeButton, fieldGroupBase, fieldGroupDraft, fieldInputType, fieldMoveTargetDraft, fieldOrderDraft, fieldOrderPreviewActive, fieldVisibilityDraft, filteredRelationOptions, focusProductFormValidationError, formConflict, formData, formLayoutColumnsDraft, inputFieldValue, intentConfirmationRef, isContractFieldOrderEditable, isMissingRequiredValue, isProjectIntakeCreateMode, isProjectQuickIntakeMode, isTierValidationActionHidden, layoutContainsType, loadCollaborationUsers, lowCodeFormLayoutBase, many2oneValue, markFieldChanged, model, nativeFormDesignFieldKeys, nativeFormDesignFieldLabels, nativeLayoutVisibilityRevision, navigateActionResponseResult, normalizeActionKind, normalizeActionSafety, normalizeRequiredParams, normalizeWorkflowActionRows, normalizeWorkflowEvidenceGateRows, onNativeAttachmentSelected, onchangeModifiersPatch, one2manyCanCreate, one2manyColumnDisplayValue, one2manyColumnInputType, one2manyColumns, one2manyCreateLabel, one2manyRowErrors, one2manyRowHints, one2manyRowLabel, one2manyRowStateLabel, one2manySummary, openNativeAttachment, openNativeChatterAction, openRelationCreateForm, parseMaybeJsonRecord, pendingNativeAttachments, policyContext, queryMany2oneInline, recordId, relationCreateMode, relationIds, relationInlineCreate, relationKeyword, relationOptionsForField, relationUiLabel, reload, rememberFormConfigFieldLabel, removeMentionUser, removeOne2manyRow, removePendingNativeAttachment, removedOne2manyRows, renderProfile, resolveContractFormFieldLabels, resolveInputPlaceholder, resolvePrimaryCreateFooterAction, resolveSelectPlaceholder, resolveUnifiedPageContractV2, resolveWorkflowContractFromSources, restoreOne2manyRow, rights, route, runAction, runtimeRoleCode, selectMentionUser, selectedMentionUsers, selectedRelationOptions, sendNativeChatter, session, setBooleanField, setMany2oneField, setOne2manyRowField, setRelationIds, setRelationKeyword, setRelationMultiField, setSelectionField, setTextField, shouldShowWorkflowAction, showHud, showOne2manyErrors, toDateInputValue, toDatetimeInputValue, toPositiveInt, updateNativeActivity, useRecordCollaborationPresentation, useRecordContractSemantics, useRecordFormFieldSchemas, useRecordFormLayout, v2ContractStore, validationErrors, visibleOne2manyRows } = dependencies;
  function currentWorkflowContract(): Record<string, unknown> {
    return resolveWorkflowContractFromSources(contract.value, v2ContractStore.value?.snapshot);
  }

  function workflowContractActionRows(): Array<Record<string, unknown>> {
    if (!recordId.value) return [];
    return normalizeWorkflowActionRows(currentWorkflowContract(), model.value);
  }

  function blockingWorkflowEvidenceMessage() {
    const row = workflowEvidenceGateRows.value.find((item) => item.blocking);
    return row?.message || '';
  }

  function applyWorkflowContractToAction(action: ContractAction): ContractAction {
    return applyWorkflowAvailability({ action, workflow: currentWorkflowContract(), recordId: recordId.value, blockingMessage: blockingWorkflowEvidenceMessage() });
  }

  function shouldShowWorkflowNativeAction(methodName: string) {
    return shouldShowWorkflowAction(currentWorkflowContract(), recordId.value, methodName);
  }

  const workflowEvidenceGateRows = computed(() => normalizeWorkflowEvidenceGateRows(currentWorkflowContract()));

  const contractActions = computed<ContractAction[]>(() => {
    const sceneReadyActions = useSceneFormAugmentations.value && Array.isArray(sceneReadyFormSurface.value.actions)
      ? sceneReadyFormSurface.value.actions as Array<Record<string, unknown>>
      : [];
    const storeButtonStatus = collectContractV2ButtonStatusById(v2ContractStore.value);
    const v2ButtonStatus = Object.keys(storeButtonStatus).length
      ? storeButtonStatus
      : collectUnifiedPageContractV2ButtonStatus(contract.value);
    return buildContractFormActions({
      contract: contract.value,
      model: model.value,
      recordId: recordId.value,
      renderProfile: renderProfile.value,
      sceneReadyActions,
      v2ButtonStatus,
      workflowActionRows: workflowContractActionRows(),
      policyContext: policyContext.value,
      evaluateNativeActionVisibility,
      isTierValidationActionHidden,
    });
  });

  const headerActions = computed(() => contractActions.value.filter((item) => item.level === 'header' || item.level === 'toolbar'));
  const bodyActions = computed(() => contractActions.value.filter((item) => item.level !== 'header' && item.level !== 'toolbar'));

  const contractFieldLabels = computed<Record<string, string>>(() => resolveContractFormFieldLabels(contract.value, v2ContractStore.value?.snapshot));

  function contractFieldLabel(name: string) {
    return contractFieldLabels.value[String(name || '').trim()] || '';
  }
  const {
    activeActivityAction,
    nativeAttachmentMaxBytes,
    nativeChatterActions,
    nativeAttachments,
    nativeCollaborationPanelProps,
    nativeCollaborationPanelListeners,
    resolveNativeAttachmentLabel,
  } = useRecordCollaborationPresentation({
    contract, v2ContractStore, recordId, model, renderProfile, busy,
    activeChatterMode, activeChatterLabel, chatterDraft, activitySummary, activityDeadline, activityNote,
    collaborationUserQuery, collaborationUserOptions, collaborationUserChoices, collaborationUsersLoading,
    selectedMentionUsers, activityAssigneeId, chatterPosting, chatterError, chatterTimeline, activityUpdatingIds,
    attachmentError, attachmentUploading, pendingNativeAttachments, onNativeAttachmentSelected,
    closeNativeChatterComposer, loadCollaborationUsers, openNativeChatterAction, openNativeAttachment,
    removeMentionUser, removePendingNativeAttachment, selectMentionUser, sendNativeChatter, updateNativeActivity,
  });

  const hasNativeChatterNode = computed(() => nativeLayoutContainsType(nativeFormLayoutNodes.value, 'chatter'));

  function nativeLayoutContainsType(nodes: NativeFormLayoutNode[], type: string): boolean {
    return layoutContainsType(nodes as Array<Record<string, unknown>>, type);
  }

  function contractActionFromNativeRow(row: Record<string, unknown>): ContractAction | null {
    const nativeAction = row.action && typeof row.action === 'object' && !Array.isArray(row.action)
      ? row.action as Record<string, unknown>
      : {};
    const payload = parseMaybeJsonRecord(nativeAction.payload || row.payload);
    const rowName = String(nativeAction.name || row.name || payload.method || payload.ref || '').trim();
    const rowLabel = String(nativeAction.label || row.label || '').trim();
    const key = String(nativeAction.key || row.key || rowName || rowLabel || '').trim();
    if (!key) return null;
    const kind = normalizeActionKind(
      nativeAction.kind || row.kind || row.buttonType || payload.type || row.type || (rowName ? 'object' : ''),
    );
    const level = String(nativeAction.level || row.level || 'body').trim().toLowerCase();
    const actionId = toPositiveInt(payload.action_id) ?? toPositiveInt(payload.ref) ?? toPositiveInt(row.action_id) ?? toPositiveInt(row.ref);
    const methodName = detectObjectMethodFromActionKey(
      key,
      String(payload.method || row.method || (kind === 'object' || kind === 'server' ? rowName : '') || '').trim(),
    );
    if (!shouldShowWorkflowNativeAction(methodName)) return null;
    const needRecord = kind === 'object' || kind === 'server' || level === 'row' || level === 'smart';
    return applyWorkflowContractToAction({
      key,
      label: rowLabel || key,
      kind,
      level,
      selection: 'none',
      actionId,
      methodName,
      targetModel: String(row.target_model || row.model || payload.model || model.value || '').trim(),
      context: parseMaybeJsonRecord(payload.context_raw || row.context),
      domainRaw: String(payload.domain_raw || row.domain_raw || '').trim(),
      target: String(payload.target || row.target || '').trim(),
      url: String(payload.url || row.url || '').trim(),
      enabled: !needRecord || Boolean(recordId.value),
      hint: needRecord && !recordId.value ? 'requires record id' : '',
      intent: String(nativeAction.intent || row.intent || '').trim(),
      semantic: '',
      sourceWidgetId: String(row.sourceWidgetId || row.source_widget_id || '').trim(),
      clientMode: '',
      visibleProfiles: ['create', 'edit', 'readonly'],
      requiredParams: normalizeRequiredParams(nativeAction.required_params || row.required_params),
      requiresReason: nativeAction.requires_reason === true || row.requires_reason === true,
      actionSafety: normalizeActionSafety(nativeAction.action_safety || row.action_safety),
    });
  }

  function resolveNativeActionState(row: Record<string, unknown>) {
    const action = contractActionFromNativeRow(row);
    if (!action) return {};
    return {
      disabled: busy.value || !action.enabled,
      title: action.hint || '',
    };
  }

  function isUnifiedSubmitMethod(methodName: string) {
    const method = String(methodName || '').trim();
    return method === 'action_submit'
      || method === 'action_submit_progress'
      || method === 'action_confirm'
      || method === 'button_confirm';
  }

  function isUnifiedSubmitAction(action: ContractAction | null | undefined) {
    return Boolean(action && isUnifiedSubmitMethod(action.methodName));
  }

  function nativeHeaderSubmitActionForCreate(): ContractAction | null {
    const nativeFormContract = contract.value?.views?.form as Record<string, unknown> | undefined;
    const rows = Array.isArray(nativeFormContract?.header_buttons)
      ? nativeFormContract.header_buttons as Array<Record<string, unknown>>
      : [];
    for (const row of rows) {
      const action = contractActionFromNativeRow(row);
      if (!isUnifiedSubmitAction(action)) continue;
      return {
        ...action,
        enabled: true,
        hint: '',
      };
    }
    return null;
  }

  const primarySubmitAction = computed<ContractAction | null>(() => {
    if (isProjectIntakeCreateMode.value) return null;
    if (!model.value) return null;
    if (!recordId.value) return nativeHeaderSubmitActionForCreate();
    const visibleAction = headerActions.value.find((action) => isUnifiedSubmitAction(action) && action.enabled);
    return visibleAction || null;
  });

  const primaryCreateFooterAction = computed<ContractAction | null>(() => {
    if (isProjectIntakeCreateMode.value) return null;
    if (!model.value || recordId.value) return null;
    if (primarySubmitAction.value) return null;
    const v2 = resolveUnifiedPageContractV2(contract.value);
    return resolvePrimaryCreateFooterAction({
      actions: contractActions.value,
      fallbackRules: parseMaybeJsonRecord(v2?.actionContract).actionRuleList,
      targetModel: model.value,
    });
  });

  async function runNativeLayoutAction(row: Record<string, unknown>) {
    const action = contractActionFromNativeRow(row);
    if (!action) return;
    if ((action.kind === 'object' || action.kind === 'server') && action.methodName && recordId.value) {
      if (!action.enabled || !await confirmActionSafety(action)) return;
      if (!await ensureSavedBeforeRecordAction()) return;
      busyKind.value = 'action';
      try {
        const response = await executeButton({
          model: action.targetModel || model.value,
          res_id: recordId.value,
          button: { name: action.methodName, type: action.kind === 'server' ? 'server' : 'object' },
          context: action.context,
          meta: {
            menu_id: Number(route.query.menu_id || 0) || undefined,
            action_id: actionId.value || undefined,
          },
        });
        const result = response?.result;
        if (await navigateActionResponseResult(result)) {
          return;
        }
        await reload();
        return;
      } catch (err) {
        applyPageStatusEvent({ kind: 'status', transaction: 'runAction', status: 'error', errorMessage: err instanceof Error ? err.message : '操作执行失败' });
        return;
      } finally {
        busyKind.value = null;
      }
    }
    await runAction(action);
  }

  const {
    advancedFieldNames, contractVisibleFields, coreFieldNames, fieldSemanticMeta, focusFirstValidationError,
    focusValidationError, hasAdvancedFields, nonSceneValidationErrors, policyRequiredFields, reloadLatestRecord, sceneReadyFormSurface,
    sceneValidationPanel, sceneValidationRequiredFields, strictContractDefaultsSummary, strictContractGuard,
    strictContractMissingSummary, strictContractMode, useSceneFormAugmentations, validationRequiredFields,
  } = useRecordContractSemantics({
    contract, v2ContractStore, route, session, actionId, recordId, model, renderProfile, runtimeRoleCode,
    validationErrors, isProjectIntakeCreateMode, intentConfirmationRef, formConflict,
    layoutNodes: () => layoutNodes.value,
    reload: () => reload(),
    focusValidationError: focusProductFormValidationError,
  });

  const {
    baseNativeFormLayoutNodes, currentNativeFieldOrder, ensureFieldOrderDraftStartsFromCurrentLayout,
    evaluateNativeActionVisibility, evaluateNativeModifierValue, fieldModifierMap, formDataFieldNames, isFieldVisible,
    isNativeFavoriteField, isNativeFieldVisible, isNativeLayoutNodeVisible, isWritableFieldVisible,
    nativeFormLayoutNodes, nativeFormRootColumns, nativeGroupCount, nativeNotebookPageCount, nativeStatusbar,
    nativeVisibleFieldNames, nativeVisibleSectionTitles, rawNativeFormLayoutNodes, resolveNativeButtonLabel,
    runtimeFieldStates, runtimeNativeFormLayoutNodes, runtimeState, setStatusbarValue, showNativeDefaultSectionTitle, useNativeFormTree,
  } = useRecordFormLayout({
    contract, v2ContractStore, contractVisibleFields, onchangeModifiersPatch, formData,
    isProjectQuickIntakeMode, contractFieldLabel, fieldSemanticMeta, showHud, advancedExpanded,
    coreFieldNames, advancedFieldNames, renderProfile, recordId, isContractFieldOrderEditable,
    fieldOrderDraft, fieldOrderPreviewActive, changedFieldGroupDraft, fieldMoveTargetDraft,
    fieldGroupBase, fieldGroupDraft, effectiveGroupVisible, lowCodeFormLayoutBase,
    nativeLayoutVisibilityRevision, nativeFormDesignFieldKeys, nativeFormDesignFieldLabels,
    formLayoutColumnsDraft, fieldVisibilityDraft, contractActionFromNativeRow, policyContext, rights,
    currentWorkflowContract, markFieldChanged, layoutNodes: () => layoutNodes.value,
  });

  const { layoutNodes, nativeFieldSchemasForNodes } = useRecordFormFieldSchemas({
    contract, v2ContractStore, nativeFormLayoutNodes, isNativeFieldVisible, isNativeLayoutNodeVisible,
    runtimeState, recordId, rights, contractFieldLabel, isContractFieldOrderEditable, effectiveFieldSize,
    rememberFormConfigFieldLabel, fieldOrderPreviewActive, fieldOrderDraft, formData, isFieldVisible,
    contractVisibleFields, coreFieldNames, advancedFieldNames, evaluatePolicyContext: policyContext,
    runtimeFieldStates, validationErrors,
    relationOptionsForField, relationCreateMode, relationInlineCreate, relationKeyword,
    canOpenRelationRecordForm, relationUiLabel, inputFieldValue, many2oneValue,
    toDateInputValue, toDatetimeInputValue,
  });

  function collectSceneValidationPrecheckErrors(fieldLabels: Record<string, string>): string[] {
    return collectSceneValidationPrecheckErrorsFromRules({
      requiredFields: sceneValidationRequiredFields.value,
      fieldLabels,
      isFieldVisible,
      fieldValue: (field) => formData[field],
      isMissingValue: isMissingRequiredValue,
      errorCode: ErrorCodes.SCENE_VALIDATION_REQUIRED,
    });
  }

  function onTemplateFieldChange(payload: FormSectionFieldChange) {
    if (String(payload.type || '').trim().toLowerCase() === 'many2one' && payload.action === 'query') {
      queryMany2oneInline(payload.name, payload.descriptor, String(payload.value ?? ''));
      return;
    }
    if (String(payload.type || '').trim().toLowerCase() === 'many2one' && payload.action === 'commit') {
      void commitMany2oneInline(payload.name, payload.descriptor, String(payload.value ?? ''));
      return;
    }
    dispatchTemplateFieldChange(payload, {
      onBoolean: (name, value) => setBooleanField(name, value),
      onSelection: (name, value) => setSelectionField(name, value),
      onMany2one: (name, descriptor, value) => setMany2oneField(name, descriptor, value),
      onText: (name, value) => setTextField(name, value),
    });
  }

  const relationFieldAdapter = computed<RelationFieldAdapter>(() => ({
    busy: busy.value,
    showOne2manyErrors: showOne2manyErrors.value,
    relationKeyword,
    setRelationKeyword,
    relationIds,
    selectedRelationOptions,
    filteredRelationOptions,
    setRelationMultiField,
    setRelationIds,
    relationCreateMode: (fieldName: string) => relationCreateMode(contract.value?.fields?.[fieldName]),
    relationCreateLabel: (fieldName: string) => {
      const descriptor = contract.value?.fields?.[fieldName];
      const mode = relationCreateMode(descriptor);
      if (mode === 'page') return relationUiLabel(descriptor, 'create_and_edit');
      if (mode === 'quick') return relationUiLabel(descriptor, 'quick_create');
      return '';
    },
    relationInlineCreateLabel: (fieldName: string) => {
      const descriptor = contract.value?.fields?.[fieldName];
      const template = relationUiLabel(descriptor, 'inline_create');
      const label = relationKeyword(fieldName).trim();
      return template.includes('%s') ? template.replace('%s', label) : template || label;
    },
    canInlineCreateRelation: (fieldName: string) => {
      const descriptor = contract.value?.fields?.[fieldName];
      const inline = relationInlineCreate(descriptor);
      const keyword = relationKeyword(fieldName).trim();
      if (!keyword || !inline.enabled || !inline.createOnNoMatch) return false;
      return !relationOptionsForField(fieldName).some((option) => option.label.trim().toLowerCase() === keyword.toLowerCase());
    },
    openRelationCreate: (fieldName: string) => {
      const descriptor = contract.value?.fields?.[fieldName];
      if (!descriptor) return;
      void openRelationCreateForm(fieldName, descriptor);
    },
    one2manyCanCreate,
    one2manyCreateLabel,
    addOne2manyRow,
    one2manySummary,
    visibleOne2manyRows,
    one2manyRowStateLabel,
    one2manyColumns,
    setOne2manyRowField,
    removeOne2manyRow,
    one2manyRowErrors,
    one2manyRowHints,
    removedOne2manyRows,
    restoreOne2manyRow,
    one2manyRowLabel,
    selectPlaceholder: resolveSelectPlaceholder,
    one2manyColumnInputType,
    one2manyColumnDisplayValue,
    inputFieldValue,
    fieldInputType,
    inputPlaceholder: resolveInputPlaceholder,
    setTextField,
  }));


  return {
    currentWorkflowContract,
    workflowContractActionRows,
    blockingWorkflowEvidenceMessage,
    applyWorkflowContractToAction,
    shouldShowWorkflowNativeAction,
    workflowEvidenceGateRows,
    contractActions,
    headerActions,
    bodyActions,
    contractFieldLabels,
    contractFieldLabel,
    activeActivityAction,
    nativeAttachmentMaxBytes,
    nativeChatterActions,
    nativeAttachments,
    nativeCollaborationPanelProps,
    nativeCollaborationPanelListeners,
    resolveNativeAttachmentLabel,
    hasNativeChatterNode,
    nativeLayoutContainsType,
    contractActionFromNativeRow,
    resolveNativeActionState,
    isUnifiedSubmitMethod,
    isUnifiedSubmitAction,
    nativeHeaderSubmitActionForCreate,
    primarySubmitAction,
    primaryCreateFooterAction,
    runNativeLayoutAction,
    advancedFieldNames,
    contractVisibleFields,
    coreFieldNames,
    fieldSemanticMeta,
    focusFirstValidationError,
    focusValidationError,
    hasAdvancedFields,
    nonSceneValidationErrors,
    policyRequiredFields,
    reloadLatestRecord,
    sceneReadyFormSurface,
    sceneValidationPanel,
    sceneValidationRequiredFields,
    strictContractDefaultsSummary,
    strictContractGuard,
    strictContractMissingSummary,
    strictContractMode,
    useSceneFormAugmentations,
    validationRequiredFields,
    baseNativeFormLayoutNodes,
    currentNativeFieldOrder,
    ensureFieldOrderDraftStartsFromCurrentLayout,
    evaluateNativeActionVisibility,
    evaluateNativeModifierValue,
    fieldModifierMap,
    formDataFieldNames,
    isFieldVisible,
    isNativeFavoriteField,
    isNativeFieldVisible,
    isNativeLayoutNodeVisible,
    isWritableFieldVisible,
    nativeFormLayoutNodes,
    nativeFormRootColumns,
    nativeGroupCount,
    nativeNotebookPageCount,
    nativeStatusbar,
    nativeVisibleFieldNames,
    nativeVisibleSectionTitles,
    rawNativeFormLayoutNodes,
    resolveNativeButtonLabel,
    runtimeFieldStates,
    runtimeNativeFormLayoutNodes,
    runtimeState,
    setStatusbarValue,
    showNativeDefaultSectionTitle,
    useNativeFormTree,
    layoutNodes,
    nativeFieldSchemasForNodes,
    collectSceneValidationPrecheckErrors,
    onTemplateFieldChange,
    relationFieldAdapter,
  };
}
