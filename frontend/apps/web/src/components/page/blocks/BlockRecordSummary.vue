<template>
  <article class="block block-record-summary">
    <header class="block-header">
      <h4>{{ block.title || '摘要' }}</h4>
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

const props = defineProps<{
  block: PageOrchestrationBlock;
  zoneKey: string;
  dataset: unknown;
}>();

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
    label: key,
    value: typeof value === 'object' ? JSON.stringify(value) : String(value ?? '--'),
  }));
});
</script>

<style scoped>
.block { border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; padding: 10px; height: 100%; }
.block-header h4 { margin: 0 0 8px; font-size: 14px; }
.summary-grid { display: grid; gap: 8px; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
.summary-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px; background: #f9fafb; }
.summary-label { margin: 0; font-size: 12px; color: #6b7280; }
.summary-value { margin: 4px 0 0; font-size: 14px; font-weight: 600; color: #111827; }
</style>
