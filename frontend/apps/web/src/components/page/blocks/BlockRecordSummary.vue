<template>
  <article class="block block-record-summary">
    <header class="block-header">
      <h4>{{ block.title || '摘要' }}</h4>
      <div v-if="actions.length" class="summary-actions">
        <button
          v-for="action in actions"
          :key="`summary-action-${action.key}`"
          type="button"
          class="summary-action-btn"
          @click="emitAction(action.key)"
        >
          {{ action.label || action.key }}
        </button>
      </div>
    </header>
    <div class="summary-grid">
      <article v-for="item in rows" :key="item.key" class="summary-item">
        <p class="summary-label">{{ item.label }}</p>
        <p class="summary-value">{{ item.value }}</p>
      </article>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { PageOrchestrationBlock } from '../../../app/pageOrchestration';
import type { PageBlockActionEvent } from '../../../app/pageOrchestration';

const props = defineProps<{
  block: PageOrchestrationBlock;
  zoneKey: string;
  dataset: unknown;
}>();

const emit = defineEmits<{
  (event: 'action', payload: PageBlockActionEvent): void;
}>();

const actions = computed(() => Array.isArray(props.block.actions) ? props.block.actions : []);

const rows = computed(() => {
  const source = props.dataset && typeof props.dataset === 'object' ? props.dataset as Record<string, unknown> : {};
  const rawRows = Array.isArray(props.dataset)
    ? props.dataset
    : (Array.isArray(source.rows) ? source.rows : (Array.isArray(source.items) ? source.items : []));
  return rawRows.map((item, index) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    const rawValue = row.value ?? row.description;
    return {
      key: String(row.key || `summary-${index + 1}`),
      label: String(row.label || row.title || `项 ${index + 1}`),
      value: rawValue === null || rawValue === undefined || typeof rawValue === 'object' ? '--' : String(rawValue),
    };
  });
});

function emitAction(actionKey: string) {
  const key = String(actionKey || '').trim();
  if (!key) return;
  emit('action', {
    actionKey: key,
    blockKey: props.block.key,
    zoneKey: props.zoneKey,
    item: {},
  });
}
</script>

<style scoped>
.block { border: 1px solid var(--sc-app-border); border-radius: 8px; background: var(--sc-app-panel); padding: 10px; height: 100%; }
.block-header h4 { margin: 0 0 8px; font-size: 14px; }
.block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.summary-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.summary-action-btn {
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 8px;
  background: var(--sc-app-input-bg);
  padding: 4px 10px;
  font-size: 12px;
  color: var(--sc-app-text-primary);
  cursor: pointer;
}
.summary-action-btn:hover {
  border-color: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-surface-interactive);
}
.summary-grid { display: grid; gap: 8px; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
.summary-item { border: 1px solid var(--sc-app-border); border-radius: 8px; padding: 8px; background: var(--sc-app-muted-bg); }
.summary-label { margin: 0; font-size: 12px; color: var(--sc-app-text-secondary); }
.summary-value { margin: 4px 0 0; font-size: 14px; font-weight: 600; color: var(--sc-app-text-primary); }

</style>
