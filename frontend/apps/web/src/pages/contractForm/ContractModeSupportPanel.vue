<template>
  <section v-if="activeActions.length" class="contract-mode-actions">
    <button
      v-for="action in activeActions"
      :key="`mode-${action.key}`"
      type="button"
      class="chip-btn"
      :disabled="busy"
      @click="$emit('open-mode-action', action.raw)"
    >
      {{ action.label }}
    </button>
    <p v-if="modeFeedback" class="contract-mode-feedback">{{ modeFeedback }}</p>
  </section>
  <ContractPromptActionForm
    :busy="busy"
    :fields="promptFields"
    :values="promptValues"
    :visible="promptVisible"
    @cancel="$emit('cancel-prompt')"
    @submit="$emit('submit-prompt')"
    @value-change="$emit('prompt-value-change', $event)"
  />
  <LowCodeFieldCreateDialog
    :busy="busy"
    :dialog="lowCodeFieldCreateDialog"
    @close="$emit('close-field-create')"
    @submit="$emit('submit-field-create')"
    @update:label="$emit('field-create-label-change', $event)"
    @update:ttype="$emit('field-create-type-change', $event)"
  />
  <ul v-if="lowCodePrecheckWarnings.length" class="contract-lowcode-warnings">
    <li v-for="(warning, index) in lowCodePrecheckWarnings" :key="`lowcode-warning-${index}`">{{ warning }}</li>
  </ul>
  <div v-if="showAdvancedToggle" class="layout-divider advanced-toggle">
    <button class="chip-btn" :disabled="busy" @click="$emit('toggle-advanced')">
      {{ advancedExpanded ? '收起高级信息' : '展开高级信息' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import ContractPromptActionForm from './ContractPromptActionForm.vue';
import LowCodeFieldCreateDialog, { type LowCodeFieldCreateDialogState } from './LowCodeFieldCreateDialog.vue';
import type { ContractPromptField } from './types';

type ContractModeAction = {
  key: string;
  label: string;
  raw: Record<string, unknown>;
};

defineProps<{
  activeActions: ContractModeAction[];
  advancedExpanded: boolean;
  busy: boolean;
  lowCodeFieldCreateDialog: LowCodeFieldCreateDialogState;
  lowCodePrecheckWarnings: string[];
  modeFeedback: string;
  promptFields: ContractPromptField[];
  promptValues: Record<string, string>;
  promptVisible: boolean;
  showAdvancedToggle: boolean;
}>();

defineEmits<{
  'open-mode-action': [raw: Record<string, unknown>];
  'cancel-prompt': [];
  'submit-prompt': [];
  'prompt-value-change': [payload: { fieldName: string; value: string }];
  'close-field-create': [];
  'submit-field-create': [];
  'field-create-label-change': [value: string];
  'field-create-type-change': [value: string];
  'toggle-advanced': [];
}>();
</script>
