/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed } from 'vue';
import type { ActionContract } from '@sc/schema';
import type { FormRecordHydrationTarget } from './recordHydration';

type LifecycleDependencies = Record<string, any>;

/** Owns authoritative contract loading, record hydration, and stale-response isolation. */
export function useRecordPageLifecycle(dependencies: LifecycleDependencies) {
  const { ApiError, ContractAccessPolicyError, ContractV2DecodeError, ErrorCodes, actionId, advancedExpanded, analyzeFormContractReadiness, applyIncomingFormFieldValue, applyPageStatusEvent, applyRouteRelationLabel, buildRouteContractContext, changedFieldCount, changedFieldSet, chatterLoading, clearNativeAttachmentError, clearNativeChatterForRecordLoad, clearOne2manyRows, clearPendingNativeAttachments, closeNativeChatterComposer, contract, contractAccessPolicy, contractActions, contractMeta, contractModelName, contractReadiness, coreFieldNames, createContractV2Store, decodeContractV2Snapshot, dirtyFieldSet, fieldType, financialWorkspace, formData, formDataFieldNames, formRouteIdentity, hydrateSelectedRelationOptions, hydrateVisibleOne2manyRows, initOne2manyRows, isProjectScopeExempt, layoutNodes, loadActionContractRaw, loadError, loadModelContractRaw, loadNativeChatterTimeline, loadRelationOptions, menuId, mergeNativeLayoutFieldDescriptorsIntoContract, model, nativeAttachments, nativeChatterActions, nativeChatterAutoLoadKey, nativeLayoutVisibilityRevision, onchangeLinePatches, onchangeModifiersPatch, getOnchangeTimer, setOnchangeTimer, onchangeWarnings, originalValues, pickContractNavQuery, readContractFormRecord, recordId, recordIdDisplay, recordMissing, recordVersionPolicy, recordVersionToken, relationKeywords, relationOptions, renderErrorMessage, renderProfile, requestedSourceMode, requestedSurface, resolveContractV2MainData, resolveCreateDefaultsFromState, resolveNavigationUrlFromOrigin, resolveUnifiedPageContractV2, resolveUnifiedPageContractV2MainData, restoreIntakeAutosave, retainedRouteIdentity, rights, route, router, session, setStatusbarValue, showHud, showOne2manyErrors, snapshotOriginalFormValues, status, toPositiveInt, upsertRelationOption, v2ContractDecodeError, v2ContractStore, v2ShadowActionCount, v2ShadowButtonStatusCount, v2ShadowFieldCodeCount, v2ShadowGlobalSourceKind, v2ShadowLayoutSourceKind, v2ShadowLegacyFieldMissingPreview, v2ShadowLegacyFieldOverlapCount, v2ShadowMainDataFieldCount, v2ShadowReadonlyValueCount, v2ShadowSourceContextKind, v2ShadowStatusFieldCount, v2ShadowStoreReady, v2ShadowValueFieldCount, v2ShadowValueSourceKind, v2ShadowWidgetCount, validateSurfaceMarkers, validationErrors, writableFieldCount } = dependencies;
  let activeReloadToken = 0;
  let activeReloadIdentity = '';
  let activeReloadPromise: Promise<void> | null = null;

  function resolveNavigationUrl(url: string) {
    return resolveNavigationUrlFromOrigin(url, window.location.origin);
  }

  function syncContractV2ShadowStore(rawContract: unknown) {
    v2ContractStore.value = null;
    v2ContractDecodeError.value = '';
    try {
      const snapshot = decodeContractV2Snapshot(resolveUnifiedPageContractV2(rawContract) || rawContract);
      v2ContractStore.value = createContractV2Store(snapshot);
    } catch (err) {
      if (err instanceof ContractV2DecodeError) {
        v2ContractDecodeError.value = err.issues.slice(0, 4).map((issue) => `${issue.path} ${issue.message}`).join(' | ');
        return;
      }
      v2ContractDecodeError.value = err instanceof Error ? err.message : '表单配置解析失败';
    }
  }

  const viewOrchestrationHudSummary = computed(() => {
    const rootGovernance = contract.value && typeof contract.value === 'object'
      ? (contract.value as Record<string, unknown>).governance
      : undefined;
    const governance = rootGovernance && typeof rootGovernance === 'object' && !Array.isArray(rootGovernance)
      ? rootGovernance as Record<string, unknown>
      : {};
    const orchestration = governance.view_orchestration && typeof governance.view_orchestration === 'object' && !Array.isArray(governance.view_orchestration)
      ? governance.view_orchestration as Record<string, unknown>
      : {};
    const views = orchestration.views && typeof orchestration.views === 'object' && !Array.isArray(orchestration.views)
      ? orchestration.views as Record<string, unknown>
      : {};
    const current = (views.form || {}) as Record<string, unknown>;
    const contracts = Array.isArray(current.business_config_contracts)
      ? current.business_config_contracts as Array<Record<string, unknown>>
      : [];
    const businessConfigFormFields = Array.isArray(current.business_config_form_fields)
      ? current.business_config_form_fields.map((item) => String(item || '').trim()).filter(Boolean)
      : [];
    const skippedLegacyPolicyFields = Array.isArray(current.skipped_legacy_policy_fields)
      ? current.skipped_legacy_policy_fields.map((item) => String(item || '').trim()).filter(Boolean)
      : [];
    return {
      applied: Boolean(orchestration.applied || current.applied || contracts.length),
      owner: String(orchestration.owner_layer || current.owner_layer || '-'),
      contractCount: contracts.length,
      contractNames: contracts.map((row) => String(row.name || row.id || '').trim()).filter(Boolean).join(',') || '-',
      legacyOverlay: Boolean(current.legacy_field_policy_overlay),
      businessConfigFieldCount: businessConfigFormFields.length,
      skippedLegacyPolicyFields: skippedLegacyPolicyFields.join(',') || '-',
    };
  });

  const hudEntries = computed(() => [
    { label: '业务对象', value: model.value || '-' },
    { label: '操作编号', value: actionId.value || '-' },
    { label: '记录编号', value: recordIdDisplay.value },
    { label: '配置已加载', value: Boolean(contract.value) },
    { label: '配置可用', value: contractReadiness.value.usable },
    { label: '配置问题数', value: contractReadiness.value.issues.length },
    { label: '新版配置暂存可用', value: v2ShadowStoreReady.value },
    { label: '新版配置组件数', value: v2ShadowWidgetCount.value },
    { label: '新版配置操作数', value: v2ShadowActionCount.value },
    { label: '新版配置按钮状态数', value: v2ShadowButtonStatusCount.value },
    { label: '新版配置字段编码数', value: v2ShadowFieldCodeCount.value },
    { label: '新版配置字段重叠数', value: v2ShadowLegacyFieldOverlapCount.value },
    { label: '新版配置缺失字段', value: v2ShadowLegacyFieldMissingPreview.value },
    { label: '新版配置布局来源', value: v2ShadowLayoutSourceKind.value },
    { label: '新版配置全局来源', value: v2ShadowGlobalSourceKind.value },
    { label: '新版配置上下文来源', value: v2ShadowSourceContextKind.value },
    { label: '新版配置状态字段数', value: v2ShadowStatusFieldCount.value },
    { label: '新版配置值字段数', value: v2ShadowValueFieldCount.value },
    { label: '新版配置主数据字段数', value: v2ShadowMainDataFieldCount.value },
    { label: '新版配置只读值数', value: v2ShadowReadonlyValueCount.value },
    { label: '新版配置值来源', value: v2ShadowValueSourceKind.value },
    { label: '配置解析问题', value: v2ContractDecodeError.value || '-' },
    { label: '配置视图类型', value: contract.value?.head?.view_type || contract.value?.view_type || '-' },
    { label: '页面编排已应用', value: viewOrchestrationHudSummary.value.applied },
    { label: '页面编排责任层', value: viewOrchestrationHudSummary.value.owner },
    { label: '页面编排配置数', value: viewOrchestrationHudSummary.value.contractCount },
    { label: '页面编排名称', value: viewOrchestrationHudSummary.value.contractNames },
    { label: '表单配置字段数', value: viewOrchestrationHudSummary.value.businessConfigFieldCount },
    { label: '跳过策略字段', value: viewOrchestrationHudSummary.value.skippedLegacyPolicyFields },
    { label: '历史策略覆盖', value: viewOrchestrationHudSummary.value.legacyOverlay },
    { label: '渲染档位', value: renderProfile.value },
    { label: '字段数', value: Object.keys(contract.value?.fields || {}).length },
    { label: '布局节点数', value: layoutNodes.value.length },
    { label: '可写字段数', value: writableFieldCount.value },
    { label: '已变更字段数', value: changedFieldCount.value },
    { label: '操作数', value: contractActions.value.length },
    { label: '权限', value: `${rights.value.read ? 'R' : '-'}${rights.value.write ? 'W' : '-'}${rights.value.create ? 'C' : '-'}${rights.value.unlink ? 'D' : '-'}` },
    { label: '联动提醒数', value: onchangeWarnings.value.length },
    { label: '明细联动补丁数', value: onchangeLinePatches.value.length },
  ]);
  async function loadContract() {
    contract.value = null;
    v2ContractStore.value = null;
    v2ContractDecodeError.value = '';
    const profile = recordId.value ? 'edit' : 'create';
    const currentModel = String(model.value || '').trim();
    const contractContext = buildRouteContractContext(route.query as Record<string, unknown>);
    const contextRaw = String(route.query.context_raw || '').trim();
    const requestedViewId = toPositiveInt(route.query.view_id) || toPositiveInt(route.query.viewId) || 0;
    let response: Awaited<ReturnType<typeof loadActionContractRaw>> | null = null;
    if (actionId.value) {
      try {
        response = await loadActionContractRaw(actionId.value, {
          menuId: menuId.value || undefined,
          viewId: requestedViewId || undefined,
          recordId: recordId.value,
          renderProfile: profile,
          surface: requestedSurface.value,
          sourceMode: requestedSourceMode.value,
          context: contractContext,
          contextRaw,
        });
        const actionReadiness = analyzeFormContractReadiness(response?.data, { requirePureFormViewType: true });
        const actionModel = contractModelName(response?.data);
        if (!actionReadiness.usable || (currentModel && actionModel && actionModel !== currentModel)) {
          response = null;
        }
      } catch {
        response = null;
      }
    }
    if (!response && currentModel) {
      response = await loadModelContractRaw(currentModel, {
        viewType: 'form',
        viewId: requestedViewId || undefined,
        recordId: recordId.value,
        renderProfile: profile,
        surface: requestedSurface.value,
        sourceMode: requestedSourceMode.value,
        context: contractContext,
        contextRaw,
      });
    }
    if (!response?.data || typeof response.data !== 'object') {
      throw new Error('表单配置返回为空');
    }
    const markerCheck = validateSurfaceMarkers(
      response.data,
      (response.meta as Record<string, unknown> | null) || null,
      requestedSurface.value,
    );
    if (!markerCheck.ok) {
      throw new Error(`表单配置标记不完整：${markerCheck.issues.slice(0, 4).join(' | ')}`);
    }
    const readiness = analyzeFormContractReadiness(response.data, { requirePureFormViewType: false });
    if (!readiness.usable) {
      throw new Error(`表单配置暂不可渲染：${readiness.issues.slice(0, 4).join(' | ')}`);
    }
    contract.value = response.data as ActionContract;
    contractMeta.value = response.meta || null;
    syncContractV2ShadowStore(response.data);
    mergeNativeLayoutFieldDescriptorsIntoContract();
    const policy = contractAccessPolicy.value;
    if (policy.mode === 'block') {
      const message = policy.message || 'contract access policy blocked this page';
      throw new ContractAccessPolicyError(message, policy.reasonCode || 'CONTRACT_ACCESS_BLOCKED');
    }
    const hasCore = coreFieldNames.value.length > 0;
    advancedExpanded.value = renderProfile.value !== 'create' || !hasCore;
  }

  async function loadRecord() {
    const versionPolicy = recordVersionPolicy();
    const fieldNames = formDataFieldNames();
    if (!fieldNames.includes('display_name')) fieldNames.push('display_name');
    if (versionPolicy?.tokenField && !fieldNames.includes(versionPolicy.tokenField)) {
      fieldNames.push(versionPolicy.tokenField);
    }
    recordVersionToken.value = '';
    closeNativeChatterComposer();
    clearNativeChatterForRecordLoad();
    clearNativeAttachmentError();
    if (!recordId.value) {
      clearPendingNativeAttachments();
      nativeChatterAutoLoadKey.value = '';
    }
    Object.keys(formData).forEach((key) => {
      delete formData[key];
    });
    Object.keys(relationKeywords).forEach((key) => {
      delete relationKeywords[key];
    });
    relationOptions.value = {};
    clearOne2manyRows();
    onchangeModifiersPatch.value = {};
    onchangeWarnings.value = [];
    onchangeLinePatches.value = [];
    changedFieldSet.clear();
    dirtyFieldSet.clear();
    const pendingOnchangeTimer = getOnchangeTimer();
    if (pendingOnchangeTimer) {
      clearTimeout(pendingOnchangeTimer);
      setOnchangeTimer(null);
    }
    const hydrationTarget: FormRecordHydrationTarget = {
      formData,
      relationOptions: relationOptions.value,
      relationKeywords,
      upsertRelationOption,
      initOne2manyRows,
    };
    if (!recordId.value) {
      const defaults = resolveCreateDefaultsFromState({ contract: contract.value, routeQuery: route.query as Record<string, unknown>, selectedProject: session.projectContext?.selected || null, v2ContractStore: v2ContractStore.value });
      fieldNames.forEach((name) => {
        const descriptor = contract.value?.fields?.[name];
        applyIncomingFormFieldValue({
          fieldName: name,
          descriptor,
          incoming: name in defaults ? defaults[name] : '',
          target: hydrationTarget,
        });
        if (fieldType(descriptor) === 'many2one') applyRouteRelationLabel(route.query, name, Number(formData[name] || 0), (label) => { upsertRelationOption(name, { id: Number(formData[name]), label }); relationKeywords[name] = label; });
      });
      originalValues.value = snapshotOriginalFormValues(fieldNames, formData);
      nativeLayoutVisibilityRevision.value += 1;
      restoreIntakeAutosave();
      return;
    }
    const read = await readContractFormRecord({
      model: model.value,
      ids: [recordId.value],
      fields: fieldNames.length ? fieldNames : '*',
    });
    const row = read.records?.[0];
    if (!row) {
      recordMissing.value = true;
      return;
    }
    recordMissing.value = false;
    const storeMainData = resolveContractV2MainData(v2ContractStore.value);
    const contractMainData = Object.keys(storeMainData).length ? storeMainData : resolveUnifiedPageContractV2MainData(contract.value);
    if (versionPolicy?.tokenField) {
      recordVersionToken.value = String((row as Record<string, unknown>)[versionPolicy.tokenField] || '').trim();
    }
    fieldNames.forEach((name) => {
      if (name === versionPolicy?.tokenField && !contract.value?.fields?.[name]) return;
      const incoming = Object.prototype.hasOwnProperty.call(row, name)
        ? (row as Record<string, unknown>)[name]
        : (contractMainData[name] ?? '');
      applyIncomingFormFieldValue({
        fieldName: name,
        descriptor: contract.value?.fields?.[name],
        incoming,
        target: hydrationTarget,
      });
    });
    originalValues.value = snapshotOriginalFormValues(fieldNames, formData);
    nativeLayoutVisibilityRevision.value += 1;
    if (recordId.value && (nativeChatterActions.value.length || nativeAttachments.value)) {
      if (nativeChatterAutoLoadKey.value !== `${model.value}:${recordId.value}` && !chatterLoading.value) {
        nativeChatterAutoLoadKey.value = `${model.value}:${recordId.value}`;
        await loadNativeChatterTimeline(recordId.value, model.value);
      }
    }
  }
  function handleSceneBlockAction(payload: { action?: { target?: Record<string, unknown> } }) {
    const target = payload?.action?.target && typeof payload.action.target === 'object'
      ? payload.action.target
      : {};
    const targetKind = String(target.kind || '').trim();
    if (targetKind === 'statusbar_value') {
      const value = String(target.value || '').trim();
      if (value) {
        setStatusbarValue(value);
        return;
      }
    }
    const route = String(target.route || '').trim();
    if (route) {
      void router.push(route);
      return;
    }
    const sceneKey = String(target.scene_key || '').trim();
    if (sceneKey) {
      void router.push({ name: 'scene', params: { sceneKey } });
    }
  }
  async function reload() {
    const reloadIdentity = formRouteIdentity();
    if (activeReloadPromise && reloadIdentity && reloadIdentity === activeReloadIdentity) {
      return activeReloadPromise;
    }
    const run = (async () => {
      const reloadToken = activeReloadToken + 1;
      activeReloadToken = reloadToken;
      renderErrorMessage.value = '';
      Object.assign(loadError, { status: null, reason: '', trace: '' });
      recordMissing.value = false;
      applyPageStatusEvent({ kind: 'status', transaction: 'formReload', status: 'loading' });
      validationErrors.value = [];
      showOne2manyErrors.value = false;
      try {
        await loadContract();
        if (reloadToken !== activeReloadToken) return;
        await loadRecord();
        if (reloadToken !== activeReloadToken) return;
        applyPageStatusEvent({ kind: 'status', transaction: 'formReload', status: 'ok' });
        retainedRouteIdentity.value = formRouteIdentity();
        if (!financialWorkspace.value && !isProjectScopeExempt(route.query)) {
          void preloadFormAuxiliaryData(reloadToken);
        }
      } catch (err) {
        if (reloadToken !== activeReloadToken) return;
        if (err instanceof ApiError) {
          Object.assign(loadError, { status: err.status, reason: String(err.reasonCode || ''), trace: String(err.traceId || '') });
        }
        if (err instanceof ApiError && err.status === 403) {
          await router.replace({
            name: 'access-denied',
            query: { from: route.fullPath, reason: err.reasonCode || 'PERMISSION_DENIED' },
          });
          return;
        }
        if (err instanceof ApiError && err.status === 404) {
          recordMissing.value = true;
          renderErrorMessage.value = '';
          // The status protocol clears any prior loading error without a direct ref write.
          applyPageStatusEvent({ kind: 'status', transaction: 'formReload', status: 'ok' });
          return;
        }
        if (err instanceof ContractAccessPolicyError) {
          await router.push({
            name: 'workbench',
            query: pickContractNavQuery(route.query as Record<string, unknown>, {
              reason: ErrorCodes.CAPABILITY_MISSING,
              action_id: actionId.value || undefined,
              menu_id: Number(route.query.menu_id || 0) || undefined,
              diag: showHud.value ? (err.reasonCode || 'CONTRACT_ACCESS_BLOCKED') : undefined,
            }),
          });
          return;
        }
        applyPageStatusEvent({ kind: 'status', transaction: 'formReload', status: 'error', errorMessage: err instanceof Error ? err.message : '表单加载失败' });
      } finally {
        if (activeReloadIdentity === reloadIdentity) {
          activeReloadPromise = null;
          activeReloadIdentity = '';
        }
      }
    })();
    activeReloadIdentity = reloadIdentity;
    activeReloadPromise = run;
    return run;
  }

  function ensureFormInitialReload() {
    const identity = formRouteIdentity();
    if (!identity) return;
    if (identity === retainedRouteIdentity.value && status.value === 'ok') return;
    if (status.value === 'loading' || !contract.value) {
      void reload();
    }
  }

  async function preloadFormAuxiliaryData(reloadToken: number) {
    try {
      await loadRelationOptions();
      if (reloadToken !== activeReloadToken) return;
      await hydrateSelectedRelationOptions();
      if (reloadToken !== activeReloadToken) return;
      await hydrateVisibleOne2manyRows();
    } catch {
      // Auxiliary data can be completed by explicit field interactions after the form renders.
    }
  }


  return {
    resolveNavigationUrl,
    syncContractV2ShadowStore,
    viewOrchestrationHudSummary,
    hudEntries,
    loadContract,
    loadRecord,
    handleSceneBlockAction,
    reload,
    ensureFormInitialReload,
    preloadFormAuxiliaryData,
  };
}
