<template>
  <article class="block block-record-table">
    <header class="block-header">
      <h4>{{ block.title || '表格' }}</h4>
    </header>

    <div v-if="rows.length" class="table-wrap">
      <table class="mini-table">
        <thead>
          <tr>
            <th v-for="(col, index) in columns" :key="`col-${col}`">{{ columnLabel(col, index) }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in rows" :key="`row-${idx}`">
            <td v-for="col in columns" :key="`cell-${idx}-${col}`">{{ stringify(row[col]) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-else class="empty-text">{{ emptyMessage }}</p>
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

const emptyMessage = computed(() => String(source.value.empty_message || '暂无数据'));

function columnLabel(col: string, index: number) {
  const labels = source.value.column_labels && typeof source.value.column_labels === 'object'
    ? source.value.column_labels as Record<string, string>
    : {};
  return labels[col] || `字段 ${index + 1}`;
}

function stringify(value: unknown) {
  if (value === null || value === undefined) return '--';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
</script>

<style scoped>
.block { border: 1px solid var(--sc-app-border); border-radius: 8px; background: var(--sc-app-panel); padding: 10px; min-height: 170px; }
.block-header h4 { margin: 0 0 8px; font-size: 15px; font-weight: 700; }
.table-wrap { max-width: 100%; overflow: auto; }
.mini-table { width: max(100%, 560px); min-width: 560px; border-collapse: collapse; font-size: 13px; }
.mini-table th,
.mini-table td { border: 1px solid var(--sc-app-border); padding: 8px 10px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
.mini-table th { border: 1px solid var(--sc-app-border); background: var(--sc-app-muted-bg); font-weight: 700; color: var(--sc-app-text-primary); padding: 8px 10px; }
.mini-table tbody tr:nth-child(2n) td { background: var(--sc-app-muted-bg); }
.empty-text { margin: 6px 0 0; color: var(--sc-app-text-secondary); font-size: 13px; }

</style>
