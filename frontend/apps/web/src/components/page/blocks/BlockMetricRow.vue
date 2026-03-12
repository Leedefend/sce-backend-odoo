<template>
  <article class="block block-metric-row">
    <header v-if="block.title" class="block-header">
      <h4>{{ block.title }}</h4>
    </header>

    <div class="metric-grid">
      <article
        v-for="item in metrics"
        :key="item.key"
        class="metric-item"
        :class="`tone-${item.tone || 'neutral'}`"
      >
        <p class="metric-label">{{ item.label }}</p>
        <p class="metric-value">{{ item.value }}</p>
        <p v-if="item.delta || item.hint" class="metric-meta">{{ item.delta || item.hint }}</p>
      </article>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { PageOrchestrationBlock } from '../../../app/pageOrchestration';

type MetricItem = {
  key: string;
  label: string;
  value: string | number;
  delta?: string;
  hint?: string;
  tone?: string;
};

const props = defineProps<{
  block: PageOrchestrationBlock;
  zoneKey: string;
  dataset: unknown;
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
  padding: 10px;
  min-height: 96px;
}
.metric-label {
  margin: 0;
  font-size: 12px;
  color: #6b7280;
}
.metric-value {
  margin: 8px 0 0;
  font-size: 24px;
  font-weight: 600;
}
.metric-meta {
  margin: 6px 0 0;
  font-size: 12px;
  color: #6b7280;
}
.tone-success { background: #ecfdf5; }
.tone-warning { background: #fffbeb; }
.tone-danger { background: #fef2f2; }
.tone-info { background: #eff6ff; }
.tone-neutral { background: #f9fafb; }
</style>
