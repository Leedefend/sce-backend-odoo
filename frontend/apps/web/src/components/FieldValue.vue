<template>
  <span>{{ display }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { FieldDescriptor } from '@sc/schema';
import { formatDisplayValue } from '../utils/display';

const props = defineProps<{ value: unknown; field?: FieldDescriptor }>();

const display = computed(() => {
  return formatDisplayValue(props.value, props.field);
});
</script>
