<template>
  <article class="block block-progress-summary">
    <header class="block-header">
      <h4>{{ block.title || '进展' }}</h4>
    </header>
    <div class="progress-list">
      <article v-for="item in rows" :key="item.key" class="progress-item">
        <div class="progress-line">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}%</strong>
        </div>
        <div class="progress-track"><div class="progress-fill" :style="{ width: `${item.value}%` }" /></div>
      </article>
    </div>
    <p v-if="!rows.length" class="empty-text">当前暂无可计算的进度数据，请先补齐任务计划。</p>
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

function clampPercent(raw: unknown) {
  const num = Number(raw || 0);
  if (!Number.isFinite(num)) return 0;
  return Math.max(0, Math.min(100, Math.round(num)));
}

const rows = computed(() => {
  if (Array.isArray(props.dataset)) {
    return props.dataset.map((item, index) => {
      const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
      return {
        key: String(row.key || `progress-${index + 1}`),
        label: String(row.label || `进展 ${index + 1}`),
        value: clampPercent(row.value),
      };
    });
  }
  const source = props.dataset && typeof props.dataset === 'object' ? props.dataset as Record<string, unknown> : {};
  const bars = source.bars && typeof source.bars === 'object' ? source.bars as Record<string, unknown> : {};
  const kpi = source.kpi && typeof source.kpi === 'object' ? source.kpi as Record<string, unknown> : {};
  const rowsLocal = [
    { key: 'contract', label: 'contract', value: clampPercent((bars as Record<string, unknown>).contract) },
    { key: 'output', label: 'output', value: clampPercent((bars as Record<string, unknown>).output) },
    { key: 'cost_rate', label: 'cost_rate', value: clampPercent((kpi as Record<string, unknown>).costRate || (kpi as Record<string, unknown>).cost_rate) },
    { key: 'payment_rate', label: 'payment_rate', value: clampPercent((kpi as Record<string, unknown>).paymentRate || (kpi as Record<string, unknown>).payment_rate) },
  ];
  return rowsLocal.filter((row) => row.value > 0);
});
</script>

<style scoped>
.block { border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; padding: 10px; }
.block-header h4 { margin: 0 0 8px; font-size: 14px; }
.progress-list { display: grid; gap: 8px; }
.progress-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px; background: #f9fafb; }
.progress-line { display: flex; justify-content: space-between; font-size: 12px; }
.progress-track { margin-top: 6px; width: 100%; height: 8px; background: #e5e7eb; border-radius: 999px; overflow: hidden; }
.progress-fill { height: 100%; background: #2563eb; }
.empty-text { margin: 6px 0 0; color: #6b7280; font-size: 13px; }
</style>
