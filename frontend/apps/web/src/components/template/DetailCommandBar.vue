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
  gap: var(--ui-space-3);
  margin-bottom: var(--ui-space-3);
  padding: var(--ui-space-3) var(--ui-space-4);
  border: 1px solid var(--ui-color-border-strong);
  border-radius: var(--ui-radius-md);
  background:
    linear-gradient(180deg, rgba(240, 246, 250, 0.62), rgba(255, 255, 255, 0) 84px),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 245, 239, 0.94));
  box-shadow: var(--ui-shadow-sm);
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
  gap: var(--ui-space-3);
}

.page-command-group__eyebrow {
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-bold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ui-color-ink-soft);
}

.page-command-group__count {
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-soft);
}

.page-statusbar-strip,
.page-action-strip {
  display: flex;
  flex-wrap: wrap;
  gap: var(--ui-space-2);
  margin-bottom: 0;
}

.page-statusbar-chip {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 var(--ui-space-3);
  border-radius: var(--ui-radius-pill);
  border: 1px solid var(--ui-color-border);
  background: rgba(255, 255, 255, 0.88);
  color: var(--ui-color-ink-muted);
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-semibold);
}

.page-statusbar-chip--active {
  border-color: rgba(61, 120, 159, 0.28);
  background: rgba(238, 245, 250, 0.98);
  color: var(--ui-color-primary-700);
  box-shadow:
    inset 0 0 0 1px rgba(61, 120, 159, 0.12),
    var(--ui-shadow-xs);
}

.page-action-strip {
  padding-bottom: 0;
  justify-content: flex-end;
}

.page-action-button {
  min-height: 34px;
  padding: 0 var(--ui-space-3);
  border-radius: var(--ui-radius-sm);
  border: 1px solid var(--ui-color-border);
  background: rgba(255, 255, 255, 0.92);
  color: var(--ui-color-ink);
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-semibold);
  box-shadow: var(--ui-shadow-xs);
}

.page-action-button--primary {
  border-color: var(--ui-color-primary-700);
  background: linear-gradient(135deg, var(--ui-color-primary-700), var(--ui-color-primary-600));
  color: #f8fafc;
  box-shadow: 0 10px 22px rgba(31, 76, 130, 0.18);
}

.page-action-button--ghost {
  color: var(--ui-color-ink);
}

.page-command-bar--native {
  grid-template-columns: 1fr;
  margin-bottom: var(--ui-space-2);
  padding: var(--ui-space-2) 0 var(--ui-space-3);
  border: 0;
  border-bottom: 1px solid var(--ui-color-border);
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.page-command-bar--native .page-statusbar-chip {
  padding: 4px 10px;
  box-shadow: none;
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
