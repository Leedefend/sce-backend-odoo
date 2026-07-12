import { computed, ref, type ComputedRef, type Ref } from 'vue';
import {
  loadApprovalPolicyConfig,
  saveApprovalPolicyConfig,
  saveApprovalPolicySteps,
  type ApprovalPolicyConfigPayload,
} from '../../api/businessConfig';

export type ApprovalStepDraft = {
  key: string;
  id: number;
  name: string;
  approval_scope_key: string;
  active: boolean;
  amount_min: string;
  amount_max: string;
  condition_note: string;
  note: string;
};

type UseBusinessConfigApprovalEditorOptions = {
  currentModel: ComputedRef<string>;
  selectedPageLabel: Ref<string>;
  error: Ref<string>;
  setMessage: (text: string, detail?: string) => void;
  clearMessage: () => void;
  loadSurface: () => Promise<void>;
  focusActiveEditorPanel: () => Promise<void>;
  onOpenPanel: () => void;
};

export function useBusinessConfigApprovalEditor(options: UseBusinessConfigApprovalEditorOptions) {
  const approvalLoading = ref(false);
  const approvalAudit = ref<ApprovalPolicyConfigPayload | null>(null);
  const approvalPanelOpen = ref(false);
  const approvalForm = ref({ approval_required: false, mode: 'none', manager_scope_key: '' });
  const approvalBase = ref({ approval_required: false, mode: 'none', manager_scope_key: '' });
  const approvalSteps = ref<ApprovalStepDraft[]>([]);
  const approvalStepsBaseJson = ref('[]');
  const approvalStepDragIndex = ref<number | null>(null);
  const approvalStepDropIndex = ref<number | null>(null);
  let approvalStepTempId = 0;

  const approvalModeOptions = computed(() => approvalAudit.value?.mode_options?.length
    ? approvalAudit.value.mode_options
    : [
        { value: 'none', label: '无需审核' },
        { value: 'single', label: '单级审核' },
        { value: 'linear', label: '多级顺序审核' },
      ]);
  const approvalScopeOptions = computed(() => approvalAudit.value?.scope_options || []);
  const approvalPolicyLabel = computed(() => {
    const policy = approvalAudit.value?.policy;
    const target = policy?.target_model_label || options.selectedPageLabel.value || options.currentModel.value || '当前业务';
    return policy?.exists ? `${target}：${policy.name || '已配置规则'}` : `${target}：尚未建立审批规则，保存后自动创建。`;
  });
  const approvalRuntimeText = computed(() => {
    if (!approvalAudit.value) return '未读取';
    return approvalAudit.value.runtime_approval_required ? '当前需要审批' : '当前无需审批';
  });
  const approvalEffectGuideText = computed(() => {
    const target = approvalAudit.value?.policy?.target_model_label || options.selectedPageLabel.value || '当前业务';
    return `保存后立即影响${target}的办理审批判断；未保存调整可用“放弃调整”撤销。`;
  });
  const approvalImpactSummaryText = computed(() => {
    if (!approvalForm.value.approval_required) {
      return '保存后当前业务不再要求审批。';
    }
    const modeLabel = approvalModeOptions.value.find((option) => option.value === approvalForm.value.mode)?.label || '审批';
    const scopeLabel = approvalScopeOptions.value.find((option) => option.value === approvalForm.value.manager_scope_key)?.label || '未指定默认审批岗位';
    const activeSteps = approvalSteps.value.filter((step) => step.active);
    const stepPreview = activeSteps
      .slice(0, 3)
      .map((step) => String(step.name || '').trim())
      .filter(Boolean)
      .join('、');
    const suffix = activeSteps.length > 3 ? `等 ${activeSteps.length} 个步骤` : `${activeSteps.length} 个步骤`;
    return `${modeLabel}，默认岗位：${scopeLabel}，${suffix}${stepPreview ? `：${stepPreview}` : ''}。`;
  });
  const approvalStepsJson = computed(() => JSON.stringify(approvalSteps.value.map((step) => ({
    id: Number(step.id || 0),
    name: String(step.name || '').trim(),
    approval_scope_key: String(step.approval_scope_key || '').trim(),
    active: Boolean(step.active),
    amount_min: normalizeAmountText(step.amount_min),
    amount_max: normalizeAmountText(step.amount_max),
    condition_note: String(step.condition_note || '').trim(),
    note: String(step.note || '').trim(),
  }))));
  const hasApprovalDraftChanges = computed(() => (
    approvalForm.value.approval_required !== approvalBase.value.approval_required
    || String(approvalForm.value.mode || 'none') !== approvalBase.value.mode
    || String(approvalForm.value.manager_scope_key || '') !== approvalBase.value.manager_scope_key
    || approvalStepsJson.value !== approvalStepsBaseJson.value
  ));
  const activeApprovalStepCount = computed(() => approvalSteps.value.filter((step) => step.active).length);
  const approvalValidationMessage = computed(() => {
    if (!approvalForm.value.approval_required) return '';
    if (!approvalSteps.value.length) return '启用审批后至少需要配置一个审批步骤。';
    const invalidNameIndex = approvalSteps.value.findIndex((step) => !String(step.name || '').trim());
    if (invalidNameIndex >= 0) return `第 ${invalidNameIndex + 1} 步需要填写步骤名称。`;
    const invalidScopeIndex = approvalSteps.value.findIndex((step) => !String(step.approval_scope_key || '').trim());
    if (invalidScopeIndex >= 0) return `第 ${invalidScopeIndex + 1} 步需要选择审批岗位。`;
    const invalidAmountIndex = approvalSteps.value.findIndex((step) => {
      const minText = normalizeAmountText(step.amount_min);
      const maxText = normalizeAmountText(step.amount_max);
      if (!minText || !maxText) return false;
      const min = Number(minText);
      const max = Number(maxText);
      return Number.isFinite(min) && Number.isFinite(max) && min > max;
    });
    if (invalidAmountIndex >= 0) return `第 ${invalidAmountIndex + 1} 步金额下限不能大于上限。`;
    return '';
  });
  const canSaveApprovalDraft = computed(() => hasApprovalDraftChanges.value && !approvalValidationMessage.value);

  function applyApprovalAudit(result: ApprovalPolicyConfigPayload) {
    approvalAudit.value = result;
    const policy = result.policy;
    const form = {
      approval_required: Boolean(policy.approval_required),
      mode: String(policy.mode || 'none'),
      manager_scope_key: String(policy.manager_scope_key || ''),
    };
    approvalForm.value = { ...form };
    approvalBase.value = { ...form };
    approvalSteps.value = (policy.steps || [])
      .filter((step) => step.active !== false)
      .map((step) => approvalStepFromPayload(step));
    approvalStepsBaseJson.value = approvalStepsJson.value;
  }

  function resetApprovalDraft() {
    approvalForm.value = { ...approvalBase.value };
    const steps = approvalAudit.value?.policy.steps || [];
    approvalSteps.value = steps.filter((step) => step.active !== false).map((step) => approvalStepFromPayload(step));
    approvalStepsBaseJson.value = approvalStepsJson.value;
    options.setMessage('已放弃审批设置调整');
  }

  function updateApprovalFormField(field: keyof typeof approvalForm.value, value: string | boolean) {
    if (field === 'approval_required') {
      approvalForm.value.approval_required = Boolean(value);
      return;
    }
    approvalForm.value[field] = String(value || '');
  }

  function onApprovalRequiredChange() {
    if (!approvalForm.value.approval_required) {
      approvalForm.value.mode = 'none';
      return;
    }
    if (!approvalForm.value.mode || approvalForm.value.mode === 'none') {
      approvalForm.value.mode = 'single';
    }
    if (!approvalSteps.value.length) {
      addApprovalStep();
    }
  }

  function enableApprovalWithDefaultStep() {
    approvalForm.value.approval_required = true;
    onApprovalRequiredChange();
  }

  async function loadApprovalConfig() {
    if (!options.currentModel.value) return;
    approvalLoading.value = true;
    options.error.value = '';
    options.clearMessage();
    try {
      const result = await loadApprovalPolicyConfig({ model: options.currentModel.value });
      applyApprovalAudit(result);
      options.onOpenPanel();
      approvalPanelOpen.value = true;
      await options.focusActiveEditorPanel();
    } catch (err) {
      options.error.value = err instanceof Error ? err.message : '审批设置读取失败';
    } finally {
      approvalLoading.value = false;
    }
  }

  async function saveApprovalConfig() {
    if (!options.currentModel.value || !hasApprovalDraftChanges.value) return false;
    if (approvalValidationMessage.value) {
      options.error.value = approvalValidationMessage.value;
      return false;
    }
    approvalLoading.value = true;
    options.error.value = '';
    options.clearMessage();
    try {
      const stepDraftChanged = approvalStepsJson.value !== approvalStepsBaseJson.value;
      const stepPayload: Parameters<typeof saveApprovalPolicySteps>[0]['steps'] = approvalSteps.value.map((step) => ({
        id: step.id > 0 ? step.id : undefined,
        name: String(step.name || '').trim(),
        approval_scope_key: String(step.approval_scope_key || '').trim(),
        active: true,
        amount_min: normalizeAmountText(step.amount_min) || false,
        amount_max: normalizeAmountText(step.amount_max) || false,
        condition_note: String(step.condition_note || '').trim(),
        note: String(step.note || '').trim(),
      }));
      const nextMode = approvalForm.value.approval_required
        ? String(approvalForm.value.mode || 'single')
        : 'none';
      let result = await saveApprovalPolicyConfig({
        model: options.currentModel.value,
        approval_required: approvalForm.value.approval_required,
        mode: nextMode,
        manager_scope_key: approvalForm.value.manager_scope_key || '',
      });
      if (stepDraftChanged) {
        result = await saveApprovalPolicySteps({
          model: options.currentModel.value,
          steps: approvalForm.value.approval_required ? stepPayload : [],
        });
      }
      applyApprovalAudit(result);
      await options.loadSurface();
      options.setMessage('审批设置已保存', result.runtime_approval_required ? '当前业务提交后会进入审批。' : '当前业务提交后无需审批。');
      return true;
    } catch (err) {
      options.error.value = err instanceof Error ? err.message : '审批设置保存失败';
      return false;
    } finally {
      approvalLoading.value = false;
    }
  }

  function normalizeAmountText(value: unknown): string {
    const text = String(value ?? '').trim();
    if (!text) return '';
    const parsed = Number(text);
    if (!Number.isFinite(parsed) || parsed < 0) return text;
    return String(parsed);
  }

  function approvalStepFromPayload(step: ApprovalPolicyConfigPayload['policy']['steps'][number]): ApprovalStepDraft {
    return {
      key: `step-${step.id || `tmp-${approvalStepTempId += 1}`}`,
      id: Number(step.id || 0),
      name: String(step.name || ''),
      approval_scope_key: String(step.approval_scope_key || ''),
      active: step.active !== false,
      amount_min: step.amount_min ? String(step.amount_min) : '',
      amount_max: step.amount_max ? String(step.amount_max) : '',
      condition_note: String(step.condition_note || ''),
      note: String(step.note || ''),
    };
  }

  function defaultApprovalScopeKey() {
    return approvalForm.value.manager_scope_key || approvalScopeOptions.value[0]?.value || '';
  }

  function addApprovalStep() {
    approvalSteps.value.push({
      key: `new-step-${approvalStepTempId += 1}`,
      id: 0,
      name: `审批步骤${approvalSteps.value.length + 1}`,
      approval_scope_key: defaultApprovalScopeKey(),
      active: true,
      amount_min: '',
      amount_max: '',
      condition_note: '',
      note: '',
    });
  }

  function removeApprovalStep(index: number) {
    approvalSteps.value.splice(index, 1);
  }

  function moveApprovalStep(index: number, delta: number) {
    const targetIndex = index + delta;
    if (targetIndex < 0 || targetIndex >= approvalSteps.value.length) return;
    const next = [...approvalSteps.value];
    const [item] = next.splice(index, 1);
    next.splice(targetIndex, 0, item);
    approvalSteps.value = next;
  }

  function startApprovalStepDrag(index: number, event: DragEvent) {
    approvalStepDragIndex.value = index;
    approvalStepDropIndex.value = index;
    event.dataTransfer?.setData('text/plain', String(index));
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
    }
  }

  function dropApprovalStep(index: number) {
    const from = approvalStepDragIndex.value;
    if (from === null || from === index) {
      clearApprovalStepDrag();
      return;
    }
    const next = [...approvalSteps.value];
    const [item] = next.splice(from, 1);
    next.splice(index, 0, item);
    approvalSteps.value = next;
    clearApprovalStepDrag();
  }

  function clearApprovalStepDrag() {
    approvalStepDragIndex.value = null;
    approvalStepDropIndex.value = null;
  }

  return {
    approvalLoading,
    approvalAudit,
    approvalPanelOpen,
    approvalForm,
    approvalSteps,
    approvalStepDragIndex,
    approvalStepDropIndex,
    approvalModeOptions,
    approvalScopeOptions,
    approvalPolicyLabel,
    approvalRuntimeText,
    approvalEffectGuideText,
    approvalImpactSummaryText,
    hasApprovalDraftChanges,
    activeApprovalStepCount,
    approvalValidationMessage,
    canSaveApprovalDraft,
    resetApprovalDraft,
    updateApprovalFormField,
    onApprovalRequiredChange,
    enableApprovalWithDefaultStep,
    loadApprovalConfig,
    saveApprovalConfig,
    addApprovalStep,
    removeApprovalStep,
    moveApprovalStep,
    startApprovalStepDrag,
    dropApprovalStep,
    clearApprovalStepDrag,
  };
}
