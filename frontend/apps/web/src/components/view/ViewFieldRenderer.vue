<template>
  <div v-if="!isHidden" class="view-field">
    <label class="view-label">{{ label }}</label>
    <div class="view-value">
      <input
        v-if="canEdit && !isSelection"
        class="view-input"
        :type="inputType"
        :value="inputValue"
        @input="onInput"
      />
      <select v-else-if="canEdit && isSelection" class="view-select" :value="inputValue" @change="onInput">
        <option v-for="opt in selectionOptions" :key="opt[0]" :value="opt[0]">
          {{ opt[1] }}
        </option>
      </select>
      <FieldValue v-else :value="value" :field="descriptor" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import FieldValue from '../FieldValue.vue';
import type { ViewContract } from '@sc/schema';

interface ViewFieldNode {
  name?: string;
  string?: string;
  invisible?: { type?: string; value?: boolean } | boolean;
  visible?: boolean;
  editable?: boolean;
}

const props = defineProps<{
  field: ViewFieldNode;
  descriptor?: ViewContract['fields'][string];
  value: unknown;
  editing: boolean;
  draftName: string;
  editMode: 'none' | 'name' | 'all';
}>();

const emit = defineEmits<{ (event: 'update:field', payload: { name: string; value: string }): void }>();

const label = computed(() => props.field.string || props.descriptor?.string || props.field.name || 'Field');
const isNameField = computed(() => props.field.name === 'name');
const canEdit = computed(() => {
  if (!props.editing) return false;
  if (props.editMode === 'none') return false;
  if (props.editMode === 'name') return isNameField.value;
  return true;
});
const isSelection = computed(() => props.descriptor?.ttype === 'selection');
const selectionOptions = computed(() => (Array.isArray(props.descriptor?.selection) ? props.descriptor?.selection : []));
const inputValue = computed(() => {
  if (canEdit.value && isNameField.value) {
    return props.draftName;
  }
  return String(props.value ?? '');
});
const inputType = computed(() => {
  switch (props.descriptor?.ttype) {
    case 'integer':
    case 'float':
      return 'number';
    case 'date':
      return 'date';
    case 'datetime':
      return 'datetime-local';
    default:
      return 'text';
  }
});
const isHidden = computed(() => {
  const invisible = props.field.invisible;
  if (typeof invisible === 'boolean') {
    return invisible;
  }
  if (invisible && typeof invisible === 'object' && 'value' in invisible) {
    return Boolean(invisible.value);
  }
  if (props.field.visible === false) {
    return true;
  }
  return false;
});

function onInput(event: Event) {
  const name = props.field.name || '';
  emit('update:field', { name, value: (event.target as HTMLInputElement).value });
}
</script>

<style scoped>
.view-field {
  display: grid;
  gap: 6px;
}

.view-label {
  font-weight: 600;
  color: #334155;
}

.view-value {
  color: #0f172a;
}

.view-input {
  width: 100%;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid #cbd5f5;
  font-size: 14px;
}

.view-select {
  width: 100%;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid #cbd5f5;
  font-size: 14px;
  background: white;
}
</style>
