import type { Ref } from 'vue';
import { intentRequest } from '../../api/intents';
import { stageBusinessConfigChangeSetItem } from '../../api/businessConfig';
import {
  BUSINESS_CONFIG_ACTION_KEYS,
  BUSINESS_CONFIG_INTENTS,
} from '../../app/businessConfigBoundaries';
import { parseMaybeJsonRecord } from '../../app/contractRuntime';
import { contractActionRuleKey } from './actionContract';
import {
  formConfigSaveOperationSummary as formConfigSaveOperationSummaryFromDraft,
  lowCodeScopedContractName,
  normalizeLowCodeApplyParams,
} from './formConfigHelpers';
import { applyFormRuntimeBusyEvent, applyFormRuntimeStatusEvent } from './runtimeStateApplier';
import type { BusyKind, FormConfigAuditResult, LowCodeFieldSize, UiStatus } from './types';
import { saveStandaloneFormConfig } from './saveStandaloneFormConfig';

type LowCodeColumns = 1 | 2 | 3;

export function useFormConfigSaveRuntime(params: {
  appendOperation: (action: string, summary: string, status?: 'pending' | 'saved' | 'reverted' | 'done') => void;
  buildLowCodeViewOrchestration: () => unknown;
  busyKind: Ref<BusyKind>;
  changedFieldGroupDraft: () => Record<string, string>;
  changedFieldVisibilityDraft: () => Record<string, boolean>;
  contractModeFeedback: Ref<string>;
  contractV2ActionRules: () => Record<string, unknown>[];
  errorMessage: Ref<string>;
  fieldGroupBase: Ref<Record<string, string>>;
  fieldGroupSavedBase: Ref<Record<string, string>>;
  fieldLayoutDirtyKeys: Record<string, boolean>;
  fieldOrderDraft: Ref<string[]>;
  fieldSizeBase: Ref<Record<string, LowCodeFieldSize>>;
  fieldSizeDraft: Record<string, LowCodeFieldSize>;
  fieldVisibilityBase: Ref<Record<string, boolean>>;
  fieldVisibilityDirty: Ref<boolean>;
  fieldVisibilityDirtyKeys: Record<string, boolean>;
  formConfigAuditResult: Ref<FormConfigAuditResult | null>;
  formLayoutColumnsBase: Ref<LowCodeColumns>;
  formLayoutColumnsDraft: Ref<LowCodeColumns>;
  formLayoutDirty: Ref<boolean>;
  groupColumnsBase: Ref<Record<string, LowCodeColumns>>;
  groupColumnsDraft: Record<string, LowCodeColumns>;
  groupLayoutDirtyKeys: Record<string, boolean>;
  groupVisibilityBase: Ref<Record<string, boolean>>;
  groupVisibilityDraft: Record<string, boolean>;
  hasCurrentFormFieldDraftChanges: () => boolean;
  hasFieldLayoutChanges: () => boolean;
  hasFieldOrderChanges: () => boolean;
  hasFormLayoutChanges: () => boolean;
  hasGroupLayoutChanges: () => boolean;
  hydrateLowCodeDraftFromContract: () => Promise<void>;
  lowCodeContractLoaded: Ref<boolean>;
  lowCodePrecheckWarnings: Ref<string[]>;
  markPendingOperations: (status: 'saved' | 'reverted') => void;
  modelName: () => string;
  changeSetToken: () => string;
  reload: () => Promise<void>;
  status: Ref<UiStatus>;
}) {
  function formConfigSaveOperationSummary(changedVisibility: Record<string, boolean>, changedGroups: Record<string, string>) {
    return formConfigSaveOperationSummaryFromDraft({
      hasFieldOrderChanges: params.hasFieldOrderChanges(),
      changedVisibility,
      changedGroups,
      hasFormLayoutChanges: params.hasFormLayoutChanges(),
      hasGroupLayoutChanges: params.hasGroupLayoutChanges(),
      hasFieldLayoutChanges: params.hasFieldLayoutChanges(),
    });
  }

  async function saveContractFieldOrder() {
    if (!params.hasCurrentFormFieldDraftChanges()) return true;
    const configAction = params.contractV2ActionRules().find((rule) => contractActionRuleKey(rule) === BUSINESS_CONFIG_ACTION_KEYS.currentFormFieldOrderSave);
    const target = parseMaybeJsonRecord(configAction?.target);
    const baseParams = normalizeLowCodeApplyParams(parseMaybeJsonRecord(target.params));
    const changedVisibility = params.changedFieldVisibilityDraft();
    const changedGroups = params.changedFieldGroupDraft();
    const saveOperationSummary = formConfigSaveOperationSummary(changedVisibility, changedGroups);
    const applyParams: Record<string, unknown> = { ...baseParams };
    if (params.hasFieldOrderChanges()) {
      applyParams.field_order = [...params.fieldOrderDraft.value];
    }
    if (Object.keys(changedGroups).length) {
      applyParams.field_groups = changedGroups;
    }
    if (Object.keys(changedVisibility).length) {
      applyParams.field_visibility = changedVisibility;
    }
    const hasFieldApplyParams = 'field_order' in applyParams || 'field_visibility' in applyParams || 'field_groups' in applyParams;
    if (!hasFieldApplyParams && !params.hasFormLayoutChanges() && !params.hasGroupLayoutChanges() && !params.hasFieldLayoutChanges()) {
      params.fieldVisibilityDirty.value = false;
      params.contractModeFeedback.value = '';
      return true;
    }
    applyFormRuntimeBusyEvent(params, {
      kind: 'begin',
      transaction: 'formConfig',
      busyKind: 'action',
    });
    try {
      const changeSetToken = params.changeSetToken();
      if (hasFieldApplyParams && !changeSetToken) {
        await intentRequest({
          intent: BUSINESS_CONFIG_INTENTS.lowCodeApply,
          params: applyParams,
          context: { view: 'form' },
        });
      }
      const modelName = String(params.modelName() || '');
      const contractName = lowCodeScopedContractName(modelName || 'unknown', baseParams);
      const contractPayload = {
        view_orchestration: params.buildLowCodeViewOrchestration(),
      };
      const saveResult = changeSetToken
        ? await stageBusinessConfigChangeSetItem({
          change_set_token: changeSetToken,
          config_type: 'form',
          target_key: contractName,
          contract_name: contractName,
          model: modelName,
          view_type: 'form',
          action_id: Number(baseParams.action_id || 0) || undefined,
          view_id: Number(baseParams.view_id || 0) || undefined,
          role_key: String(baseParams.role_key || '') || undefined,
          draft_payload: contractPayload,
          diff_summary: { summary: saveOperationSummary },
        })
        : await saveStandaloneFormConfig({ baseParams, name: contractName, model: modelName, contractPayload });
      const warnings = Array.isArray(saveResult?.precheck?.warnings) ? saveResult.precheck?.warnings || [] : [];
      params.lowCodePrecheckWarnings.value = warnings.map((item) => String(item || '').trim()).filter(Boolean);
      if (Object.keys(changedVisibility).length) {
        params.fieldVisibilityBase.value = {
          ...params.fieldVisibilityBase.value,
          ...changedVisibility,
        };
        Object.keys(changedVisibility).forEach((key) => {
          delete params.fieldVisibilityDirtyKeys[key];
        });
      }
      if (Object.keys(changedGroups).length) {
        params.fieldGroupSavedBase.value = {
          ...params.fieldGroupSavedBase.value,
          ...changedGroups,
        };
        params.fieldGroupBase.value = {
          ...params.fieldGroupBase.value,
          ...changedGroups,
        };
      }
      params.formLayoutColumnsBase.value = params.formLayoutColumnsDraft.value;
      params.groupVisibilityBase.value = { ...params.groupVisibilityDraft };
      params.groupColumnsBase.value = { ...params.groupColumnsDraft };
      params.fieldSizeBase.value = { ...params.fieldSizeDraft };
      params.formLayoutDirty.value = false;
      Object.keys(params.groupLayoutDirtyKeys).forEach((key) => delete params.groupLayoutDirtyKeys[key]);
      Object.keys(params.fieldLayoutDirtyKeys).forEach((key) => delete params.fieldLayoutDirtyKeys[key]);
      params.fieldVisibilityDirty.value = false;
      params.lowCodeContractLoaded.value = false;
      params.formConfigAuditResult.value = null;
      params.contractModeFeedback.value = changeSetToken
        ? '表单设置已加入待发布变更，可返回工作台检查和预览'
        : '表单设置已保存并发布，刷新页面后按新配置生效';
      params.markPendingOperations('saved');
      params.appendOperation(changeSetToken ? '加入待发布变更' : '保存发布', saveOperationSummary, 'done');
      if (!changeSetToken) {
        await params.reload();
        await params.hydrateLowCodeDraftFromContract();
      }
      return true;
    } catch (err) {
      applyFormRuntimeStatusEvent(params, {
        kind: 'status',
        transaction: 'formConfig',
        status: 'error',
        errorMessage: err instanceof Error ? err.message : '表单字段顺序更新失败',
      });
      return false;
    } finally {
      applyFormRuntimeBusyEvent(params, {
        kind: 'end',
        transaction: 'formConfig',
      });
    }
  }

  return {
    formConfigSaveOperationSummary,
    saveContractFieldOrder,
  };
}
