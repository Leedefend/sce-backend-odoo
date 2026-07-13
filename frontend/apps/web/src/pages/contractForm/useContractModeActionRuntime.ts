import { computed, reactive, ref, type Ref } from 'vue';
import { intentRequest } from '../../api/intents';
import { parseMaybeJsonRecord } from '../../app/contractRuntime';
import {
  contractActionRuleClientMode,
  contractPromptFieldsFromRule,
  contractPromptParamsFromRule,
} from './actionContract';
import { applyFormRuntimeStatusEvent } from './runtimeStateApplier';
import type { BusyKind, UiStatus } from './types';

export function useContractModeActionRuntime(params: {
  busyKind: Ref<BusyKind>;
  errorMessage: Ref<string>;
  status: Ref<UiStatus>;
  contractModeFeedback: Ref<string>;
  applyClientMode: (mode: string, toggle?: boolean) => boolean | void;
  reload: () => Promise<void>;
}) {
  const contractPromptRule = ref<Record<string, unknown> | null>(null);
  const contractPromptValues = reactive<Record<string, string>>({});
  const contractPromptFields = computed(() => (
    contractPromptRule.value ? contractPromptFieldsFromRule(contractPromptRule.value) : []
  ));

  function closeContractPromptAction() {
    contractPromptRule.value = null;
    Object.keys(contractPromptValues).forEach((key) => {
      delete contractPromptValues[key];
    });
  }

  async function runContractRuleAction(rule: Record<string, unknown>, providedParams?: Record<string, unknown>) {
    const target = parseMaybeJsonRecord(rule.target);
    const mode = contractActionRuleClientMode(rule);
    const intent = String(rule.intent || target.intent || '').trim();
    if (intent === 'ui.local_mode' || intent === 'ui.mode' || (!intent && mode)) {
      params.applyClientMode(mode, target.toggle !== false);
      return;
    }
    if (!intent) return;
    if (!providedParams && contractPromptFieldsFromRule(rule).length) {
      openContractModeAction(rule);
      return;
    }
    const actionParams = providedParams || contractPromptParamsFromRule(rule);
    if (actionParams === null) return;
    params.busyKind.value = 'action';
    try {
      await intentRequest({
        intent,
        params: actionParams,
        context: parseMaybeJsonRecord(target.context),
      });
      params.contractModeFeedback.value = String(target.success_message || '已更新').trim();
      await params.reload();
    } catch (err) {
      applyFormRuntimeStatusEvent(params, {
        kind: 'status',
        transaction: 'contractMode',
        status: 'error',
        errorMessage: err instanceof Error ? err.message : '表单配置操作失败',
      });
    } finally {
      params.busyKind.value = null;
    }
  }

  function openContractModeAction(rule: Record<string, unknown>) {
    const promptFields = contractPromptFieldsFromRule(rule);
    if (!promptFields.length) {
      void runContractRuleAction(rule);
      return;
    }
    Object.keys(contractPromptValues).forEach((key) => {
      delete contractPromptValues[key];
    });
    promptFields.forEach((field) => {
      contractPromptValues[field.name] = field.defaultValue;
    });
    contractPromptRule.value = rule;
    params.contractModeFeedback.value = '';
  }

  async function submitContractPromptAction() {
    const rule = contractPromptRule.value;
    if (!rule) return;
    const actionParams = contractPromptParamsFromRule(rule, contractPromptValues);
    if (actionParams === null) return;
    await runContractRuleAction(rule, actionParams);
    closeContractPromptAction();
  }

  function setContractPromptValue(fieldName: string, value: string) {
    contractPromptValues[fieldName] = value;
  }

  return {
    closeContractPromptAction,
    contractPromptFields,
    contractPromptRule,
    contractPromptValues,
    openContractModeAction,
    runContractRuleAction,
    setContractPromptValue,
    submitContractPromptAction,
  };
}
