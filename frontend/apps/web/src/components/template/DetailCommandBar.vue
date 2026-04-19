<template>
  <section
    v-if="steps.length || actions.length"
    :class="['page-command-bar', { 'page-command-bar--native': nativeLike }]"
    data-component="DetailCommandBar"
  >
    <section v-if="steps.length" class="page-command-group page-command-group--status">
      <div class="page-command-group__head">
        <span class="page-command-group__eyebrow">流程阶段</span>
        <span class="page-command-group__count">{{ steps.length }} 步</span>
      </div>
      <div class="page-statusbar-strip">
        <span
          v-for="step in steps"
          :key="step.key"
          :class="['page-statusbar-chip', { 'page-statusbar-chip--active': step.active }]"
        >
          {{ step.label }}
        </span>
      </div>
    </section>
    <section v-if="actions.length" class="page-command-group page-command-group--actions">
      <div class="page-command-group__head">
        <span class="page-command-group__eyebrow">下一步动作</span>
        <span class="page-command-group__count">{{ actions.length }} 项</span>
      </div>
      <div class="page-action-strip">
        <button
          v-for="action in actions"
          :key="`strip-${action.key}`"
          :class="[
            'page-action-button',
            action.semantic === 'primary_action' ? 'page-action-button--primary' : 'page-action-button--ghost',
          ]"
          :disabled="busy || !action.enabled"
          :title="action.hint"
          @click="$emit('run-action', action)"
        >
          {{ action.label }}
        </button>
      </div>
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
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  gap: 14px;
  margin-bottom: 14px;
  padding: 12px 14px;
  border: 1px solid rgba(203, 213, 225, 0.92);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94));
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
}

.page-command-group {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.page-command-group__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.page-command-group__eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

.page-command-group__count {
  font-size: 11px;
  color: #94a3b8;
}

.page-statusbar-strip,
.page-action-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 0;
}

.page-statusbar-chip {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  font-size: 12px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #475569;
  font-weight: 600;
}

.page-statusbar-chip--active {
  border-color: #1d4ed8;
  background: #eff6ff;
  color: #1d4ed8;
  box-shadow: inset 0 0 0 1px rgba(29, 78, 216, 0.12);
}

.page-action-strip {
  padding-bottom: 0;
  justify-content: flex-end;
}

.page-action-button {
  min-height: 34px;
  border-radius: 10px;
  padding: 0 12px;
  border: 1px solid #cbd5e1;
  background: #fff;
  font-size: 12px;
  font-weight: 600;
}

.page-action-button--primary {
  background: #0f172a;
  color: #fff;
  border-color: #0f172a;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.14);
}

.page-action-button--ghost {
  color: #334155;
}

.page-command-bar--native {
  grid-template-columns: 1fr;
  margin-bottom: 8px;
  padding: 8px 0 10px;
  border: 0;
  border-bottom: 1px solid #e5e7eb;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.page-command-bar--native .page-statusbar-chip {
  border-radius: 999px;
  padding: 4px 10px;
}

@media (max-width: 920px) {
  .page-command-bar {
    grid-template-columns: 1fr;
  }

  .page-action-strip {
    justify-content: flex-start;
  }
}
</style>
