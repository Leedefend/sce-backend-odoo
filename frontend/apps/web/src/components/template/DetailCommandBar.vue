<template>
  <section v-if="steps.length || actions.length" class="page-command-bar" data-component="DetailCommandBar">
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
}>();

defineEmits<{
  (e: 'run-action', action: DetailActionItem): void;
}>();
</script>

<style scoped>
.page-command-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 14px;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.page-statusbar-strip,
.page-action-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 0;
}

.page-statusbar-chip {
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #475569;
}

.page-statusbar-chip--active {
  border-color: #111827;
  background: #111827;
  color: #fff;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.12);
}

.page-action-strip {
  padding-bottom: 0;
  justify-content: flex-end;
}

.ghost,
.primary {
  border-radius: 6px;
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  font-weight: 500;
}

.primary {
  background: #111827;
  color: #fff;
  border-color: #111827;
}

.ghost {
  color: #6b7280;
}
</style>
