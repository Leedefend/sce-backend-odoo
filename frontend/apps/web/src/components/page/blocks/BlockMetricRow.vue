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
      label: key,
      value: typeof value === 'object' ? JSON.stringify(value) : String(value ?? '--'),
      tone: 'neutral',
    }));
});

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
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
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
  border: 1px solid #e5e7eb;
  padding: 12px;
  min-height: 110px;
  text-align: left;
  color: inherit;
}
button.metric-item { cursor: pointer; }
button.metric-item:hover {
  border-color: #60a5fa;
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.12);
}
.metric-label {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
}
.metric-value {
  margin: 8px 0 0;
  font-size: 26px;
  font-weight: 700;
}
.metric-meta {
  margin: 8px 0 0;
  font-size: 12px;
  color: #6b7280;
}
.tone-success { background: #ecfdf5; }
.tone-warning { background: #fffbeb; }
.tone-danger { background: #fef2f2; }
.tone-info { background: #eff6ff; }
.tone-neutral { background: #f9fafb; }
</style>
