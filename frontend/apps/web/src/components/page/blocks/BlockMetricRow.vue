<template>
  <article class="block block-metric-row">
    <header v-if="block.title" class="block-header">
      <h4>{{ block.title }}</h4>
    </header>

    <div class="metric-grid">
      <component
        :is="item.actionKey ? 'button' : 'article'"
        v-for="item in metrics"
        :key="item.key"
        class="metric-item"
        :class="`tone-${item.tone || 'neutral'}`"
        type="button"
        @click="item.actionKey ? emitAction(item) : undefined"
      >
        <p class="metric-label">{{ item.label }}</p>
        <p class="metric-value">{{ item.value }}</p>
        <p v-if="item.delta || item.hint" class="metric-meta">{{ item.delta || item.hint }}</p>
      </component>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { PageBlockActionEvent, PageOrchestrationBlock } from '../../../app/pageOrchestration';

type MetricItem = {
  key: string;
  label: string;
  value: string | number;
  delta?: string;
  hint?: string;
  tone?: string;
  actionKey?: string;
  raw?: Record<string, unknown>;
};

const props = defineProps<{
  block: PageOrchestrationBlock;
  zoneKey: string;
  dataset: unknown;
}>();

const emit = defineEmits<{
  (event: 'action', payload: PageBlockActionEvent): void;
}>();

const metrics = computed<MetricItem[]>(() => {
  if (Array.isArray(props.dataset)) {
    return props.dataset.map((item, index) => {
      const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
      return {
        key: String(row.key || `metric-${index + 1}`),
        label: String(row.label || `指标 ${index + 1}`),
        value: String(row.value ?? '--'),
        delta: String(row.delta || ''),
        hint: String(row.hint || ''),
        tone: String(row.tone || 'neutral').toLowerCase(),
        actionKey: String(row.action_key || ''),
        raw: row,
      };
    });
  }
  if (!props.dataset || typeof props.dataset !== 'object') return [];
  const row = props.dataset as Record<string, unknown>;
  return Object.entries(row)
    .filter(([key]) => !['title', 'subtitle', 'message', 'hint'].includes(key))
    .slice(0, 8)
    .map(([key, value]) => ({
      key,
      label: humanizeKey(key),
      value: typeof value === 'object' ? '多项内容' : String(value ?? '--'),
      tone: 'neutral',
    }));
});

function humanizeKey(value: string) {
  return String(value || '')
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim() || '未命名';
}

function emitAction(item: MetricItem) {
  const actionKey = String(item.actionKey || '').trim();
  if (!actionKey) return;
  emit('action', {
    actionKey,
    blockKey: props.block.key,
    zoneKey: props.zoneKey,
    item: item.raw || {},
  });
}
</script>

<style scoped>
.block {
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  padding: 12px;
  height: 100%;
}
.block-header h4 {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 600;
}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}
.metric-item {
  border-radius: 10px;
  border: 1px solid var(--sc-app-border);
  padding: 12px;
  min-height: 110px;
  text-align: left;
  color: inherit;
}
button.metric-item { cursor: pointer; }
button.metric-item:hover {
  border-color: var(--sc-semantic-surface-interactive);
  box-shadow: 0 10px 20px var(--sc-app-focus-ring);
}
.metric-label {
  margin: 0;
  font-size: 13px;
  color: var(--sc-app-text-secondary);
}
.metric-value {
  margin: 8px 0 0;
  font-size: 26px;
  font-weight: 700;
}
.metric-meta {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}
.tone-success { background: var(--sc-app-success-bg); }
.tone-warning { background: var(--sc-app-warning-bg); }
.tone-danger { background: var(--sc-app-danger-bg); }
.tone-info { background: var(--sc-app-info-bg); }
.tone-neutral { background: var(--sc-app-muted-bg); }
</style>
