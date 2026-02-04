<template>
  <div v-if="!isHidden" class="view-field">
    <label class="view-label">{{ label }}</label>
    <div class="view-value">
      <ViewRelationalRenderer
        v-if="isRelational"
        :ids="relationIds"
        :model="relationModel"
        :relation-field="relationField"
        :parent-id="parentId"
        :editable="relationalEditable"
      />
      <input
        v-else-if="canEdit && !isSelection"
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
import ViewRelationalRenderer from './ViewRelationalRenderer.vue';
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
  parentId?: number;
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
const fieldType = computed(() => props.descriptor?.ttype || props.descriptor?.type || '');
const isSelection = computed(() => fieldType.value === 'selection');
const selectionOptions = computed(() => (Array.isArray(props.descriptor?.selection) ? props.descriptor?.selection : []));
const isRelational = computed(() => ['one2many', 'many2many'].includes(String(fieldType.value)));
const relationIds = computed(() => {
  if (!Array.isArray(props.value)) return [];
  const ids = [];
  for (const item of props.value) {
    if (typeof item === 'number') {
      ids.push(item);
      continue;
    }
    if (Array.isArray(item) && typeof item[0] === 'number') {
      ids.push(item[0]);
      continue;
    }
    if (item && typeof item === 'object' && 'id' in item && typeof item.id === 'number') {
      ids.push(item.id);
    }
  }
  return ids;
});
const relationField = computed(() => props.descriptor?.relation_field || '');
const relationModel = computed(() => props.descriptor?.relation || '');
const relationalEditable = computed(() => {
  if (!props.editing) return false;
  if (props.descriptor?.readonly) return false;
  return Boolean(props.descriptor?.editable ?? true);
});
const inputValue = computed(() => {
  if (canEdit.value && isNameField.value) {
    return props.draftName;
  }
  return String(props.value ?? '');
});
const inputType = computed(() => {
  switch (fieldType.value) {
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
