<template>
  <span>{{ display }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { FieldDescriptor } from '@sc/schema';

const props = defineProps<{ value: unknown; field?: FieldDescriptor }>();

const display = computed(() => {
  const field = props.field;
  const value = props.value;

  const fieldType = field?.ttype || field?.type;

  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }

  if (fieldType === 'boolean') {
    return value ? 'Yes' : 'No';
  }

  if (fieldType === 'selection' && Array.isArray(field.selection)) {
    const match = field.selection.find((item) => item[0] === value);
    return match ? match[1] : value ?? '';
  }

  if (fieldType === 'many2one') {
    if (Array.isArray(value)) {
      return value[1] ?? value[0];
    }
  }

  if (Array.isArray(value)) {
    return value.join(', ');
  }

  if (value && typeof value === 'object') {
    return JSON.stringify(value);
  }

  return value ?? '';
});
</script>
