<template>
  <form
    v-if="visible"
    class="contract-mode-prompt"
    @submit.prevent="$emit('submit')"
  >
    <label
      v-for="field in fields"
      :key="`contract-prompt-${field.name}`"
      class="contract-mode-prompt-field"
    >
      <span>{{ field.label }}</span>
      <select
        v-if="field.options.length"
        :value="String(values[field.name] || '')"
        :required="field.required"
        :disabled="busy"
        @change="$emit('value-change', { fieldName: field.name, value: inputValue($event) })"
      >
        <option value=""></option>
        <option v-for="option in field.options" :key="option.value" :value="option.value">{{ option.label }}</option>
      </select>
      <input
        v-else
        :value="String(values[field.name] || '')"
        :required="field.required"
        :disabled="busy"
        @input="$emit('value-change', { fieldName: field.name, value: inputValue($event) })"
      />
    </label>
    <button type="submit" class="chip-btn" :disabled="busy">确定</button>
    <button type="button" class="ghost" :disabled="busy" @click="$emit('cancel')">取消</button>
  </form>
</template>

<script setup lang="ts">
import type { ContractPromptField } from './types';

defineProps<{
  visible: boolean;
  fields: ContractPromptField[];
  values: Record<string, string>;
  busy: boolean;
}>();

defineEmits<{
  submit: [];
  cancel: [];
  'value-change': [payload: { fieldName: string; value: string }];
}>();

function inputValue(event: Event) {
  return String((event.target as HTMLInputElement | HTMLSelectElement).value || '');
}
</script>

<style scoped src="./ContractPromptActionForm.css"></style>
