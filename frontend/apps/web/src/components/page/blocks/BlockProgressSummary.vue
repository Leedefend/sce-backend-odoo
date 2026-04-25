<template>
  <article class="block block-progress-summary">
    <header class="block-header">
      <h4>{{ block.title || '进展' }}</h4>
    </header>
    <p v-if="summaryText" class="summary-text">{{ summaryText }}</p>
    <div class="progress-list">
      <article v-for="item in rows" :key="item.key" class="progress-item" :class="`kind-${item.kind}`">
        <div class="progress-line">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}{{ item.unit }}</strong>
        </div>
        <div v-if="item.kind === 'rate'" class="progress-track"><div class="progress-fill" :style="{ width: `${item.value}%` }" /></div>
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

function normalizeCount(raw: unknown) {
  const num = Number(raw || 0);
  if (!Number.isFinite(num)) return 0;
  return Math.max(0, Math.round(num));
}

const rows = computed(() => {
  if (Array.isArray(props.dataset)) {
    return props.dataset.map((item, index) => {
      const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
      return {
        key: String(row.key || `progress-${index + 1}`),
        label: String(row.label || `进展 ${index + 1}`),
        value: String(row.unit || '%') === '%' ? clampPercent(row.value) : normalizeCount(row.value),
        unit: String(row.unit || '%'),
        kind: String(row.unit || '%') === '%' ? 'rate' : 'count',
      };
    });
  }
  const source = props.dataset && typeof props.dataset === 'object' ? props.dataset as Record<string, unknown> : {};
  const bars = source.bars && typeof source.bars === 'object' ? source.bars as Record<string, unknown> : {};
  const kpi = source.kpi && typeof source.kpi === 'object' ? source.kpi as Record<string, unknown> : {};
  const rowsLocal = [
    { key: 'contract', label: '合同履约率', value: clampPercent((bars as Record<string, unknown>).contract), unit: '%', kind: 'rate' },
    { key: 'output', label: '产值完成率', value: clampPercent((bars as Record<string, unknown>).output), unit: '%', kind: 'rate' },
    { key: 'cost_rate', label: '成本控制率', value: clampPercent((kpi as Record<string, unknown>).costRate || (kpi as Record<string, unknown>).cost_rate), unit: '%', kind: 'rate' },
    { key: 'payment_rate', label: '资金支付率', value: clampPercent((kpi as Record<string, unknown>).paymentRate || (kpi as Record<string, unknown>).payment_rate), unit: '%', kind: 'rate' },
  ];
  return rowsLocal.filter((row) => row.value > 0);
});

const summaryText = computed(() => {
  const source = props.dataset && typeof props.dataset === 'object' ? props.dataset as Record<string, unknown> : {};
  return String(source.summary || '').trim();
});
</script>

<style scoped>
.block { border: 1px solid #e5e7eb; border-radius: 12px; background: #fff; padding: 12px; height: 100%; }
.block-header h4 { margin: 0 0 10px; font-size: 15px; font-weight: 600; }
.summary-text { margin: 0 0 10px; color: #475569; font-size: 13px; line-height: 1.5; }
.progress-list { display: grid; gap: 10px; }
.progress-item { border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px; background: #f8fbff; min-height: 66px; }
.progress-item.kind-count { background: #fff7ed; border-color: #fed7aa; }
.progress-line { display: flex; justify-content: space-between; font-size: 13px; }
.progress-track { margin-top: 8px; width: 100%; height: 9px; background: #dbeafe; border-radius: 999px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #60a5fa 0%, #2563eb 100%); }
.empty-text { margin: 6px 0 0; color: #6b7280; font-size: 13px; }
</style>
