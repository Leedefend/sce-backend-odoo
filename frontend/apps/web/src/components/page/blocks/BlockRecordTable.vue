<template>
  <article class="block block-record-table">
    <header class="block-header">
      <h4>{{ block.title || '表格' }}</h4>
    </header>

    <div v-if="rows.length" class="table-wrap">
      <table class="mini-table">
        <thead>
          <tr>
            <th v-for="col in columns" :key="`col-${col}`">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in rows" :key="`row-${idx}`">
            <td v-for="col in columns" :key="`cell-${idx}-${col}`">{{ stringify(row[col]) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-else class="empty-text">暂无数据</p>
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

type DataRow = Record<string, unknown>;

const source = computed(() => (
  props.dataset && typeof props.dataset === 'object' ? props.dataset as Record<string, unknown> : {}
));

const columns = computed<string[]>(() => {
  const raw = source.value.columns;
  if (!Array.isArray(raw)) return [];
  return raw.map((item) => String(item || '').trim()).filter(Boolean);
});

const rows = computed<DataRow[]>(() => {
  const raw = source.value.rows;
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((item) => item && typeof item === 'object' && !Array.isArray(item))
    .map((item) => item as DataRow);
});

function stringify(value: unknown) {
  if (value === null || value === undefined) return '--';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
</script>

<style scoped>
.block { border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; padding: 10px; }
.block-header h4 { margin: 0 0 8px; font-size: 14px; }
.table-wrap { overflow: auto; }
.mini-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.mini-table th,
.mini-table td { border: 1px solid #e5e7eb; padding: 6px 8px; text-align: left; }
.mini-table th { background: #f9fafb; font-weight: 600; }
.empty-text { margin: 6px 0 0; color: #6b7280; font-size: 13px; }
</style>
