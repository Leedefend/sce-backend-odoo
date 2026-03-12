<template>
  <article class="block block-record-summary" :class="summaryClass">
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

const summaryClass = computed(() => {
  const zone = String(props.zoneKey || '');
  if (zone.includes('header')) return 'summary-zone-header';
  if (zone.includes('cost')) return 'summary-zone-cost';
  return 'summary-zone-default';
});
</script>

<style scoped>
.block { border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; padding: 10px; height: 100%; }
.block-header h4 { margin: 0 0 8px; font-size: 14px; }
.summary-grid { display: grid; gap: 8px; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
.summary-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px; background: #f9fafb; }
.summary-label { margin: 0; font-size: 12px; color: #6b7280; }
.summary-value { margin: 4px 0 0; font-size: 14px; font-weight: 600; color: #111827; }

.summary-zone-header {
  border-color: #dbeafe;
  background: #f8fbff;
}
.summary-zone-header .summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
}
.summary-zone-header .summary-item {
  background: #ffffff;
  min-height: 78px;
}
.summary-zone-header .summary-value {
  font-size: 15px;
}

.summary-zone-cost .summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.summary-zone-cost .summary-item {
  background: #fffbeb;
  border-color: #fde68a;
  min-height: 82px;
}

@media (max-width: 1200px) {
  .summary-zone-cost .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
