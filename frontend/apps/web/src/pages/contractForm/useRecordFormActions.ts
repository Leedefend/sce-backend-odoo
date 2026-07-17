/* eslint-disable @typescript-eslint/no-explicit-any */
import type { FormSectionFieldActionPayload, FormSectionFieldSchema } from '../../components/template/formSection.types';
import type { ContractAction, LayoutNode } from './types';

type ActionDependencies = Record<string, any>;

/** Owns save, conflict recovery, form configuration, and projection refresh actions. */
export function useRecordFormActions(dependencies: ActionDependencies) {
  const { ApiError, BUSINESS_CONFIG_ACTION_KEYS, BUSINESS_CONFIG_MODES, BUSINESS_CONFIG_ROUTE_FLAGS, PROJECT_CONTEXT_CHANGED_EVENT, actionId, activeContractMode, activeContractModeFieldRows, appendFormConfigOperation, buildLowCodeApplyBaseParams, buildLowCodePreviewQuery, buildLowCodeReturnQuery, buildSaveRecordPayload, busy, busyKind, canSave, clearIntakeAutosave, closeContractPromptAction, collectPolicyValidationErrors, collectSceneValidationPrecheckErrors, collectWritableValues, comparableFieldValue, contract, contractActionRuleKey, contractFieldSequenceFromOrder, contractModeFeedback, contractV2ActionRules, createContractFormRecord, currentFormDesignFieldKeys, currentFormOrderedFieldKeys, dirtyFieldSet, draggingFieldLabel, effectiveFieldGroupTitleForDraft, ensureFormInitialReload, executeProjectionRefresh, fieldGroupTitleMatches, fieldOrderDraft, fieldVisibilityBase, fieldVisibilityDirtyKeys, fieldVisibilityDraft, focusFirstValidationError, formConfigAuditResult, formConflict, formCreateContextFromState, formData, formDesignFieldLabel, formDesignerGroupNavigatorItems, formRouteIdentity, formSettingsActiveTab, formUiLabel, handleProjectContextChanged, hasChanges, hasCurrentFormFieldDraftChanges, instanceRouteIdentity, intentConfirmationRef, isBusinessConfigMode, isBusinessConfigRuntimeModel, isComponentActive, isContractFieldOrderEditable, isFormPageRouteOwner, isProjectStandardIntakeMode, isTierValidationActionHiddenFromState, isWritableFieldVisible, layoutNodes, model, moveFieldOrder, navigateCreatedRecord, normalizeFieldGroupTitle, normalizeFieldValue, onContractInlineGroupRename, onErrorCaptured, onFieldOrderDragEnd, onFieldOrderDragLeave, onFieldOrderDragOver, onFieldOrderDragStart, onFieldOrderDrop, onFieldOrderGroupDrop, onFieldOrderWindowDragOver, onFieldOrderWindowDragStop, onRelationDialogDocumentKeydown, one2manyValidation, originalValues, parseMaybeJsonRecord, policyContext, recordId, recordVersionPolicy, recordVersionToken, reload, rememberFormConfigFieldLabel, renderErrorMessage, resolvePendingInlineRelationCreates, resolvePendingMany2manyTagCreates, retainedRouteIdentity, route, router, runContractRuleAction, sanitizeUiErrorMessage, saveContractFieldOrder, sceneReadyFormSurface, scopedCreateContext, selectedFormSettingsFieldGroupTitle, selectedFormSettingsFieldGroupTitleDraft, selectedFormSettingsFieldGroupTitleEdit, selectedFormSettingsFieldKey, selectedFormSettingsFieldLabel, selectedFormSettingsFieldRow, session, setInlineFieldPolicy, showOne2manyErrors, status, submissionFeedback, uploadPendingNativeAttachments, useFormPageLifecycleRuntime, v2ContractStore, validateBeforeSaveRecord, validateContractFormData, validationErrors, writeContractFormRecord } = dependencies;
  async function discardChanges() {
    if (!hasChanges.value || busy.value) return;
    await reload();
  }

  onErrorCaptured((err) => {
    const message = err instanceof Error ? err.message : String(err || '系统处理问题');
    renderErrorMessage.value = `表单页面打开失败：${message}`;
    return false;
  });

  async function confirmActionSafety(action: ContractAction) {
    const safety = action.actionSafety;
    if (!safety || safety.classification !== 'danger' || !safety.requiresConfirm) return true;
    return intentConfirmationRef.value?.confirm({ actionLabel: String(action.label || '操作'),
      message: String(safety.confirmMessage || action.hint || '该操作执行后将立即生效，请确认是否继续。') }) ?? false;
  }

  async function ensureSavedBeforeRecordAction() {
    if (!hasChanges.value) return true;
    return Boolean(await saveRecord({ on_success: ['scene_projection'] }));
  }

  function applyClientMode(mode: string, toggle = true) {
    const next = String(mode || '').trim();
    if (!next) return false;
    activeContractMode.value = toggle && activeContractMode.value === next ? '' : next;
    contractModeFeedback.value = '';
    if (!activeContractMode.value) closeContractPromptAction();
    return true;
  }

  function applyRouteConfigMode(rawMode: unknown) {
    const mode = String(rawMode || '').trim();
    if (isBusinessConfigRuntimeModel(model.value)) {
      if (activeContractMode.value === BUSINESS_CONFIG_MODES.formFieldConfiguration || activeContractMode.value === BUSINESS_CONFIG_MODES.lowCode) {
        activeContractMode.value = '';
      }
      return;
    }
    if (isBusinessConfigMode(mode)) {
      applyClientMode(mode, false);
    }
  }

  async function onContractFieldAction(payload: FormSectionFieldActionPayload) {
    const fieldKey = String(payload.field.name || '').trim();
    const actionValue = String(payload.action.value || '').trim();
    if (isContractFieldOrderEditable.value && fieldKey && ['show', 'hide'].includes(actionValue)) {
      fieldVisibilityDraft[fieldKey] = actionValue === 'show';
      fieldVisibilityDirtyKeys[fieldKey] = true;
      formConfigAuditResult.value = null;
      appendFormConfigOperation(actionValue === 'show' ? '显示字段' : '隐藏字段', `${formDesignFieldLabel(fieldKey)} 设置为${actionValue === 'show' ? '显示' : '隐藏'}`);
      contractModeFeedback.value = '字段显示设置已调整，保存后生效';
      return;
    }
    const raw = payload.action.raw;
    if (!raw) return;
    await runContractRuleAction(raw);
  }

  function onFormSettingsFieldSelect(payload: { field: FormSectionFieldSchema; groupTitle: string }) {
    if (!isContractFieldOrderEditable.value) return;
    const fieldKey = String(payload.field.name || payload.field.key || '').trim();
    if (!fieldKey) return;
    rememberFormConfigFieldLabel(fieldKey, payload.field.label);
    if (!Object.prototype.hasOwnProperty.call(fieldVisibilityBase.value, fieldKey)) {
      const row = activeContractModeFieldRows.value.find((item) => item.fieldKey === fieldKey);
      const checkedAction = row?.actions.find((action) => Boolean(action.checked));
      fieldVisibilityBase.value = {
        ...fieldVisibilityBase.value,
        [fieldKey]: checkedAction ? checkedAction.value === 'show' : true,
      };
      if (!Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)) {
        fieldVisibilityDraft[fieldKey] = checkedAction ? checkedAction.value === 'show' : true;
      }
    }
    selectedFormSettingsFieldKey.value = fieldKey;
    selectedFormSettingsFieldLabel.value = String(payload.field.label || fieldKey).trim();
    selectedFormSettingsFieldGroupTitleDraft.value = (
      effectiveFieldGroupTitleForDraft(fieldKey)
      || normalizeFieldGroupTitle(payload.groupTitle)
    );
    selectedFormSettingsFieldGroupTitleEdit.value = selectedFormSettingsFieldGroupTitleDraft.value;
    formSettingsActiveTab.value = 'fields';
  }

  function selectFormDesignerGroup(title: string) {
    const normalizedTitle = normalizeFieldGroupTitle(title);
    if (!normalizedTitle) return;
    const group = formDesignerGroupNavigatorItems.value.find((item) => fieldGroupTitleMatches(item.title, normalizedTitle));
    const orderedKeys = currentFormOrderedFieldKeys.value.length ? currentFormOrderedFieldKeys.value : currentFormDesignFieldKeys.value;
    const fieldKey = orderedKeys.find((key) => group?.fieldKeys.includes(key)) || group?.fieldKeys[0] || '';
    if (!fieldKey) return;
    onFormSettingsFieldSelect({
      field: {
        name: fieldKey,
        key: fieldKey,
        label: formDesignFieldLabel(fieldKey),
      } as FormSectionFieldSchema,
      groupTitle: normalizedTitle,
    });
  }

  function selectFormDesignerField(fieldKey: string) {
    const key = String(fieldKey || '').trim();
    if (!key) return;
    onFormSettingsFieldSelect({
      field: {
        name: key,
        key,
        label: formDesignFieldLabel(key),
      } as FormSectionFieldSchema,
      groupTitle: effectiveFieldGroupTitleForDraft(key) || '业务配置字段',
    });
  }

  async function onSelectedFormSettingsGroupTitleChange(event: Event) {
    const oldTitle = selectedFormSettingsFieldGroupTitle.value;
    const target = event.target as HTMLInputElement | null;
    const newTitle = String(selectedFormSettingsFieldGroupTitleEdit.value || target?.value || '').trim();
    if (!oldTitle || !newTitle || oldTitle === newTitle) {
      selectedFormSettingsFieldGroupTitleEdit.value = oldTitle;
      return;
    }
    await onContractInlineGroupRename({ oldTitle, newTitle });
  }

  async function onSelectedFormSettingsFieldLabelChange(event: Event) {
    const fieldKey = selectedFormSettingsFieldKey.value;
    const target = event.target as HTMLInputElement | null;
    const label = String(target?.value || '').trim();
    if (!fieldKey || !label || label === selectedFormSettingsFieldRow.value?.label) return;
    selectedFormSettingsFieldLabel.value = label;
    await setInlineFieldPolicy(fieldKey, { label });
  }

  function contractInlineFieldOrderIndex(field: FormSectionFieldSchema) {
    const fieldKey = String(field.name || '').trim();
    if (!fieldKey) return -1;
    return fieldOrderDraft.value.indexOf(fieldKey);
  }

  function onContractInlineFieldOrderMove(payload: { field: FormSectionFieldSchema; delta: number }) {
    const fieldKey = String(payload.field.name || '').trim();
    if (!fieldKey) return;
    moveFieldOrder(fieldKey, payload.delta);
  }

  function onContractInlineFieldOrderDragStart(payload: { field: FormSectionFieldSchema; event: DragEvent }) {
    const fieldKey = String(payload.field.name || '').trim();
    if (!fieldKey) return;
    rememberFormConfigFieldLabel(fieldKey, payload.field.label);
    const fieldLabel = String(payload.field.label || '').trim();
    draggingFieldLabel.value = fieldLabel && fieldLabel !== fieldKey ? fieldLabel : formDesignFieldLabel(fieldKey);
    onFieldOrderDragStart(fieldKey, payload.event);
  }

  function onContractInlineFieldOrderDragOver(payload: { field: FormSectionFieldSchema; groupTitle?: string; placement?: 'before' | 'after' | '' }) {
    const fieldKey = String(payload.field.name || '').trim();
    if (!fieldKey) return;
    rememberFormConfigFieldLabel(fieldKey, payload.field.label);
    onFieldOrderDragOver(fieldKey, payload.placement);
  }

  function onContractInlineFieldOrderDragLeave(payload: { field: FormSectionFieldSchema; groupTitle?: string }) {
    const fieldKey = String(payload.field.name || '').trim();
    if (!fieldKey) return;
    onFieldOrderDragLeave(fieldKey);
  }

  function onContractInlineFieldOrderDrop(payload: { field: FormSectionFieldSchema; groupTitle?: string; placement?: 'before' | 'after' | '' }) {
    const fieldKey = String(payload.field.name || '').trim();
    if (!fieldKey) return;
    rememberFormConfigFieldLabel(fieldKey, payload.field.label);
    onFieldOrderDrop(fieldKey, payload.groupTitle, payload.placement);
  }

  function onContractInlineFieldOrderGroupDrop(payload: { groupTitle: string; groupIndex?: number }) {
    onFieldOrderGroupDrop(payload.groupTitle);
  }

  function onContractInlineFieldOrderDragEnd() {
    onFieldOrderDragEnd();
  }

  function lowCodeApplyBaseParams() {
    const configAction = contractV2ActionRules.value.find((rule) => contractActionRuleKey(rule) === BUSINESS_CONFIG_ACTION_KEYS.currentFormFieldOrderSave);
    const target = parseMaybeJsonRecord(configAction?.target);
    return buildLowCodeApplyBaseParams({
      actionId: actionId.value || route.query.action_id,
      viewId: routeQueryText('view_id') || routeQueryText('viewId'),
      targetParams: parseMaybeJsonRecord(target.params),
      modelName: String(model.value || ''),
    });
  }

  function contractFieldSequence(fieldKey: string, fallback = 100) {
    return contractFieldSequenceFromOrder(fieldOrderDraft.value, fieldKey, fallback);
  }

  function fieldGroupTitleForDraft(fieldKey: string) {
    return effectiveFieldGroupTitleForDraft(fieldKey);
  }

  function routeQueryText(key: string) {
    const value = route.query[key];
    if (Array.isArray(value)) return String(value[0] || '').trim();
    return String(value || '').trim();
  }

  function lowCodeReturnQuery() {
    return buildLowCodeReturnQuery({
      routeQuery: route.query as Record<string, unknown>,
      modelName: model.value,
      actionId: actionId.value,
      openPagesFlag: BUSINESS_CONFIG_ROUTE_FLAGS.openPages,
    });
  }

  function previewLowCodeConfiguredPage() {
    const query = buildLowCodePreviewQuery({
      routeQuery: route.query as Record<string, unknown>,
      returnToBusinessConfigFlag: BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig,
      openPagesFlag: BUSINESS_CONFIG_ROUTE_FLAGS.openPages,
    });
    router.push({ path: route.path, query });
  }

  async function previewCurrentFormConfiguration() {
    if (hasCurrentFormFieldDraftChanges.value) {
      const saved = await saveContractFieldOrder();
      if (!saved) return;
    }
    previewLowCodeConfiguredPage();
  }

  function returnToBusinessConfigDesigner() {
    router.push({
      path: '/admin/business-config',
      query: lowCodeReturnQuery(),
    });
  }

  function isTierValidationActionHidden(methodName: string): boolean {
    return isTierValidationActionHiddenFromState({
      methodName,
      validationStatus: formData.validation_status,
      canReview: formData.can_review,
    });
  }

  async function applyProjectionRefreshPolicy(policy?: ContractAction['refreshPolicy']) {
    if (!policy || !Array.isArray(policy.on_success) || !policy.on_success.length) {
      return;
    }
    await executeProjectionRefresh({
      policy,
      refreshScene: async () => {
        await reload();
      },
      refreshWorkbench: async () => {
        await session.loadAppInit();
      },
      refreshRoleSurface: async () => {
        await session.loadAppInit();
      },
      recordTrace: ({ intent, writeMode, latencyMs }) => {
        session.recordIntentTrace({ intent, writeMode, latencyMs });
      },
    });
  }

  async function saveRecord(refreshPolicy?: ContractAction['refreshPolicy']): Promise<boolean | number> {
    if (!canSave.value || !model.value) return false;
    submissionFeedback.value = null;
    validationErrors.value = [];
    formConflict.value = false;
    const validation = await validateBeforeSaveRecord({
      collectPolicyValidationErrors: (submittedFields) => [
        ...collectPolicyValidationErrors(contract.value, policyContext.value),
        ...collectPolicyValidationErrors(contract.value, {
          ...policyContext.value,
          submittedFields,
        }),
      ],
      collectSceneValidationPrecheckErrors: (fieldLabels) => collectSceneValidationPrecheckErrors(fieldLabels),
      collectWritableValues: () => collectWritableValues(),
      formData,
      isProjectStandardIntakeMode: isProjectStandardIntakeMode.value,
      isWritableFieldVisible: (name) => isWritableFieldVisible(name),
      layoutNodes: layoutNodes.value,
      layoutFieldLabels: () => (layoutNodes.value as LayoutNode[]).reduce<Record<string, string>>((acc, node) => {
        if (node.kind === 'field') acc[node.name] = node.label || node.name;
        return acc;
      }, {}),
      normalizeFieldValue: (name, value) => normalizeFieldValue(name, value),
      one2manyIssues: one2manyValidation.value.issues,
      projectManagerId: formData.manager_id,
      projectName: formData.name,
      recordId: recordId.value,
      resolvePendingInlineRelationCreates: () => resolvePendingInlineRelationCreates(),
      resolvePendingMany2manyTagCreates: () => resolvePendingMany2manyTagCreates(),
      validateContractFormData: (fieldLabels, values) => validateContractFormData({
        contract: contract.value,
        fieldLabels,
        values,
      }).map((item) => item.message),
    });
    showOne2manyErrors.value = Boolean(validation.showOne2manyErrors);
    if (!validation.ok || !validation.editableMap) {
      validationErrors.value = validation.validationErrors || [];
      submissionFeedback.value = validation.submissionFeedback || null;
      await focusFirstValidationError();
      return false;
    }
    const editableMap = validation.editableMap;
    busyKind.value = 'save';
    try {
      const values = buildSaveRecordPayload({
        comparableFieldValue: (name, value) => comparableFieldValue(name, value),
        contract: contract.value,
        dirtyFieldSet,
        editableMap,
        formData,
        originalValues: originalValues.value,
        recordId: recordId.value,
      });
      if (recordId.value && !Object.keys(values).length) {
        busyKind.value = null;
        dirtyFieldSet.clear();
        return true;
      }
      if (recordId.value) {
        await writeContractFormRecord({
          model: model.value,
          ids: [recordId.value],
          vals: values,
          ifMatch: recordVersionPolicy() ? recordVersionToken.value : undefined,
        });
        submissionFeedback.value = { kind: 'success', message: formUiLabel('save_success') };
        formConflict.value = false;
        dirtyFieldSet.clear();
        await applyProjectionRefreshPolicy(refreshPolicy || { on_success: ['scene_projection'] });
        return true;
      }
      const context = scopedCreateContext(route.query, formCreateContextFromState({ contract: contract.value, v2ContractStore: v2ContractStore.value }), formData.project_id);
      const created = await createContractFormRecord({ model: model.value, vals: values, context });
      if (created?.id) {
        const attachmentsUploaded = await uploadPendingNativeAttachments(Number(created.id));
        if (!attachmentsUploaded) {
          return false;
        }
        const title = String(contract.value?.head?.title || '').trim();
        submissionFeedback.value = { kind: 'success', message: `${title || '记录'}已创建` };
        clearIntakeAutosave();
        return await navigateCreatedRecord({
          createdId: created.id,
          nextSceneKey: String(sceneReadyFormSurface.value.nextSceneKey || '').trim(),
          nextSceneRoute: String(sceneReadyFormSurface.value.nextSceneRoute || '').trim(),
          refreshPolicy,
        });
      }
    } catch (err) {
      const fallback = recordId.value ? '保存失败，请检查填写内容' : '创建失败，请检查填写内容';
      if (err instanceof ApiError && err.status === 401) {
        await session.logout();
        await router.replace('/login');
        return false;
      }
      if (err instanceof ApiError && err.status === 403) {
        await router.replace({ name: 'access-denied' });
        return false;
      }
      if (err instanceof ApiError && err.status === 409) {
        formConflict.value = true;
        validationErrors.value = ['当前记录已发生变化，请加载最新数据后重新核对本次修改。'];
        submissionFeedback.value = { kind: 'error', message: '记录已被其他操作更新，当前输入尚未写入。' };
        await focusFirstValidationError();
        return false;
      }
      const message = sanitizeUiErrorMessage(err instanceof Error ? err.message : err, fallback);
      validationErrors.value = [message];
      submissionFeedback.value = { kind: 'error', message: message && message !== fallback ? message : fallback };
      await focusFirstValidationError();
      return false;
    } finally {
      busyKind.value = null;
    }
    return false;
  }

  useFormPageLifecycleRuntime({
    contract,
    formRouteIdentity: () => formRouteIdentity(),
    handleProjectContextChanged,
    instanceRouteIdentity,
    isComponentActive,
    onFieldOrderDragEnd,
    onFieldOrderWindowDragOver,
    onFieldOrderWindowDragStop,
    onRelationDialogDocumentKeydown,
    projectContextChangedEvent: PROJECT_CONTEXT_CHANGED_EVENT,
    routeIsOwned: () => isFormPageRouteOwner(route.name),
    reload: () => reload(),
    retainedRouteIdentity,
    status,
    ensureFormInitialReload: () => ensureFormInitialReload(),
  });

  return {
    discardChanges,
    confirmActionSafety,
    ensureSavedBeforeRecordAction,
    applyClientMode,
    applyRouteConfigMode,
    onContractFieldAction,
    onFormSettingsFieldSelect,
    selectFormDesignerGroup,
    selectFormDesignerField,
    onSelectedFormSettingsGroupTitleChange,
    onSelectedFormSettingsFieldLabelChange,
    contractInlineFieldOrderIndex,
    onContractInlineFieldOrderMove,
    onContractInlineFieldOrderDragStart,
    onContractInlineFieldOrderDragOver,
    onContractInlineFieldOrderDragLeave,
    onContractInlineFieldOrderDrop,
    onContractInlineFieldOrderGroupDrop,
    onContractInlineFieldOrderDragEnd,
    lowCodeApplyBaseParams,
    contractFieldSequence,
    fieldGroupTitleForDraft,
    routeQueryText,
    lowCodeReturnQuery,
    previewLowCodeConfiguredPage,
    previewCurrentFormConfiguration,
    returnToBusinessConfigDesigner,
    isTierValidationActionHidden,
    applyProjectionRefreshPolicy,
    saveRecord,
  };
}
