<template>
  <section class="edit-panel config-editor-panel approval-panel">
    <div class="edit-panel-head">
      <div>
        <h2>审批规则</h2>
        <p>{{ policyLabel }}</p>
      </div>
      <button type="button" class="ghost small" :disabled="loading" @click="$emit('close')">
        返回工作台
      </button>
    </div>
    <aside class="approval-rule-panel" aria-label="审批规则设置">
      <div class="approval-guide">
        <strong>审批配置怎么生效</strong>
        <span>{{ effectGuideText }}</span>
      </div>
      <div class="approval-rule-head">
        <strong>规则开关</strong>
        <span>{{ runtimeText }}</span>
      </div>
      <div class="approval-config-grid">
        <label class="approval-toggle">
          <input
            :checked="form.approval_required"
            type="checkbox"
            @change="$emit('updateFormField', 'approval_required', ($event.target as HTMLInputElement).checked); $emit('approvalRequiredChange')"
          />
          <span>启用审批</span>
        </label>
        <label>
          <span>审批方式</span>
          <select
            :value="form.mode"
            :disabled="!form.approval_required"
            @change="$emit('updateFormField', 'mode', ($event.target as HTMLSelectElement).value)"
          >
            <option
              v-for="option in modeOptions"
              :key="option.value"
              :value="option.value"
              :disabled="form.approval_required && option.value === 'none'"
            >
              {{ option.label }}
            </option>
          </select>
        </label>
        <label>
          <span>默认审批岗位</span>
          <select
            :value="form.manager_scope_key"
            :disabled="!form.approval_required"
            @change="$emit('updateFormField', 'manager_scope_key', ($event.target as HTMLSelectElement).value)"
          >
            <option value="">暂不指定</option>
            <option v-for="option in scopeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
      </div>
      <div class="edit-meta approval-rule-summary">
        <span>当前步骤：{{ activeStepCount }} 个</span>
        <span>保存状态：{{ hasDraftChanges ? '有未保存调整' : '已同步' }}</span>
        <span v-if="advancedPanelOpen">生效来源：{{ boundaryText }}</span>
        <span v-if="hasDraftChanges" class="edit-dirty">配置已调整，可保存</span>
      </div>
      <div class="approval-impact-summary">
        <strong>{{ hasDraftChanges ? '本次调整' : '当前规则' }}</strong>
        <span>{{ impactSummaryText }}</span>
      </div>
    </aside>
    <section class="approval-steps" :class="{ 'approval-steps--disabled': !form.approval_required }">
      <header>
        <div>
          <strong>审批步骤编排</strong>
          <span>{{ form.approval_required ? `${activeStepCount} 个启用步骤，拖动整行调整顺序` : '启用审批后配置办理节点' }}</span>
          <em v-if="form.approval_required" class="approval-step-action-hint">也可以用上移、下移精确调整步骤顺序。</em>
        </div>
        <button type="button" class="ghost small" :disabled="loading || !form.approval_required" @click="$emit('addStep')">
          添加步骤
        </button>
      </header>
      <div v-if="steps.length" class="approval-step-table" role="table" aria-label="审批步骤">
        <div class="approval-step-table-head" role="row">
          <span>序号</span>
          <span>步骤名称</span>
          <span>审批岗位</span>
          <span>金额下限</span>
          <span>金额上限</span>
          <span>操作</span>
        </div>
        <div
          v-for="(step, index) in steps"
          :key="step.key"
          class="approval-step-row"
          :class="{
            'approval-step-row--dragging': dragIndex === index,
            'approval-step-row--drop-target': dropIndex === index && dragIndex !== index,
          }"
          role="row"
          :draggable="form.approval_required"
          :aria-label="`拖动第${index + 1}步调整顺序`"
          @dragstart="$emit('startStepDrag', index, $event)"
          @dragover.prevent
          @dragenter.prevent="$emit('setStepDropIndex', index)"
          @drop.prevent="$emit('dropStep', index)"
          @dragend="$emit('clearStepDrag')"
        >
          <span class="approval-step-seq">{{ index + 1 }}</span>
          <div class="approval-step-cell">
            <input v-model="step.name" type="text" placeholder="例如：合同中心审核" :disabled="!form.approval_required" :aria-label="`第${index + 1}步名称`" />
          </div>
          <div class="approval-step-cell">
            <select v-model="step.approval_scope_key" :disabled="!form.approval_required" :aria-label="`第${index + 1}步审批岗位`">
              <option value="">请选择</option>
              <option v-for="option in scopeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          <div class="approval-step-cell">
            <input v-model="step.amount_min" type="number" min="0" step="0.01" placeholder="不限制" :disabled="!form.approval_required" :aria-label="`第${index + 1}步金额下限`" />
          </div>
          <div class="approval-step-cell">
            <input v-model="step.amount_max" type="number" min="0" step="0.01" placeholder="不限制" :disabled="!form.approval_required" :aria-label="`第${index + 1}步金额上限`" />
          </div>
          <div class="approval-step-actions">
            <button type="button" title="上移" :aria-label="`上移第${index + 1}步`" :disabled="loading || !form.approval_required || index === 0" @click="$emit('moveStep', index, -1)">↑</button>
            <button type="button" title="下移" :aria-label="`下移第${index + 1}步`" :disabled="loading || !form.approval_required || index === steps.length - 1" @click="$emit('moveStep', index, 1)">↓</button>
            <button type="button" title="移除" :aria-label="`移除第${index + 1}步`" :disabled="loading || !form.approval_required" @click="$emit('removeStep', index)">×</button>
          </div>
        </div>
      </div>
      <div v-else class="approval-step-empty">
        当前没有审批步骤，启用审批后可添加办理节点。
        <button type="button" class="ghost small" :disabled="loading" @click="$emit('enableWithDefaultStep')">启用并添加步骤</button>
      </div>
      <div v-if="validationMessage" class="approval-validation">{{ validationMessage }}</div>
    </section>
    <div class="edit-panel-actions">
      <button type="button" class="ghost small primary" :disabled="loading || !canSaveDraft" @click="$emit('save')">
        {{ loading ? '保存中...' : '保存审批设置' }}
      </button>
      <button type="button" class="ghost small" :disabled="loading || !hasDraftChanges" @click="$emit('reset')">
        放弃调整
      </button>
      <button type="button" class="ghost small" :disabled="!canOpenFullRule" @click="$emit('openFullRule')">
        打开完整规则
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
type ApprovalForm = {
  approval_required: boolean;
  mode: string;
  manager_scope_key: string;
};

type ApprovalStepDraft = {
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

type Option = { value: string; label: string };

defineProps<{
  policyLabel: string;
  effectGuideText: string;
  runtimeText: string;
  impactSummaryText: string;
  boundaryText: string;
  form: ApprovalForm;
  steps: ApprovalStepDraft[];
  modeOptions: Option[];
  scopeOptions: Option[];
  activeStepCount: number;
  hasDraftChanges: boolean;
  canSaveDraft: boolean;
  canOpenFullRule: boolean;
  validationMessage: string;
  loading: boolean;
  advancedPanelOpen: boolean;
  dragIndex: number | null;
  dropIndex: number | null;
}>();

defineEmits<{
  close: [];
  updateFormField: [field: keyof ApprovalForm, value: string | boolean];
  approvalRequiredChange: [];
  addStep: [];
  enableWithDefaultStep: [];
  removeStep: [index: number];
  moveStep: [index: number, delta: number];
  startStepDrag: [index: number, event: DragEvent];
  setStepDropIndex: [index: number];
  dropStep: [index: number];
  clearStepDrag: [];
  save: [];
  reset: [];
  openFullRule: [];
}>();
</script>
