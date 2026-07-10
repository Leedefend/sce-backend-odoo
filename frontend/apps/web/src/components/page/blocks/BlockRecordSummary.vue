<template>
  <article class="block block-record-summary" :class="summaryClass">
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
  if (Array.isArray(props.dataset)) {
    return props.dataset.map((item, index) => {
      const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
      return {
        key: String(row.key || `summary-${index + 1}`),
        label: String(row.label || row.title || `项 ${index + 1}`),
        value: String(row.value ?? row.description ?? '--'),
      };
    });
  }
  if (!props.dataset || typeof props.dataset !== 'object') return [];
  return Object.entries(props.dataset as Record<string, unknown>).slice(0, 10).map(([key, value]) => ({
    key,
    label: humanizeKey(key),
    value: typeof value === 'object' ? '多项内容' : String(value ?? '--'),
  }));
});

function humanizeKey(value: string) {
  return String(value || '')
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim() || '未命名';
}

const summaryClass = computed(() => {
  const zone = String(props.zoneKey || '');
  if (zone.includes('header')) return 'summary-zone-header';
  if (zone.includes('cost')) return 'summary-zone-cost';
  return 'summary-zone-default';
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

.summary-zone-header {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
}
.summary-zone-header .summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
}
.summary-zone-header .summary-item {
  background: var(--sc-app-panel);
  min-height: 78px;
}
.summary-zone-header .summary-value {
  font-size: 15px;
}

.summary-zone-cost .summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.summary-zone-cost .summary-item {
  background: var(--sc-app-warning-bg);
  border-color: var(--sc-app-warning-border);
  min-height: 82px;
}

@media (max-width: 1200px) {
  .summary-zone-cost .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
