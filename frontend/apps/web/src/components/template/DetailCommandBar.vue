<template>
  <section
    v-if="steps.length || actions.length"
    :class="['page-command-bar', { 'page-command-bar--native': nativeLike }]"
    data-component="DetailCommandBar"
  >
    <section v-if="steps.length" class="page-statusbar-strip">
      <span
        v-for="step in steps"
        :key="step.key"
        :class="['page-statusbar-chip', { 'page-statusbar-chip--active': step.active }]"
      >
        {{ step.label }}
      </span>
    </section>
    <section v-if="actions.length" class="page-action-strip">
      <button
        v-for="action in actions"
        :key="`strip-${action.key}`"
        :class="action.semantic === 'primary_action' ? 'primary' : 'ghost'"
        :disabled="busy || !action.enabled"
        :title="action.hint"
        @click="$emit('run-action', action)"
      >
        {{ action.label }}
      </button>
    </section>
  </section>
</template>

<script setup lang="ts">
import type { DetailActionItem, DetailStatusbarStep } from './detailLayout.types';

defineProps<{
  steps: DetailStatusbarStep[];
  actions: DetailActionItem[];
  busy: boolean;
  nativeLike?: boolean;
}>();

defineEmits<{
  (e: 'run-action', action: DetailActionItem): void;
}>();
</script>

<style scoped>
.page-command-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
  padding: 6px 8px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}

.page-statusbar-strip,
.page-action-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 0;
}

.page-statusbar-chip {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: #fff;
  color: #4b5563;
}

.page-statusbar-chip--active {
  border-color: #9ca3af;
  background: #f3f4f6;
  color: #fff;
  color: #111827;
  box-shadow: none;
}

.page-action-strip {
  padding-bottom: 0;
  justify-content: flex-end;
}

.page-command-bar--native {
  margin-bottom: 6px;
  padding: 2px 0 6px;
  border: 0;
  border-bottom: 1px solid #e5e7eb;
  border-radius: 0;
  background: transparent;
}

.page-command-bar--native .page-statusbar-chip {
  border-radius: 999px;
  padding: 4px 10px;
}

.ghost,
.primary {
  border-radius: 6px;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  background: #fff;
  font-size: 12px;
  font-weight: 500;
}

.primary {
  background: #1f2937;
  color: #fff;
  border-color: #1f2937;
}

.ghost {
  color: #374151;
}
</style>
