<template>
  <article class="block block-record-table" :class="tableClass">
    <header class="block-header">
      <div>
        <h4>{{ block.title || '表格' }}</h4>
        <p class="block-subtitle">{{ rows.length }} 条记录</p>
      </div>
    </header>

    <div v-if="rows.length" class="table-wrap">
      <table class="mini-table">
        <thead>
          <tr>
            <th v-for="col in columns" :key="`col-${col}`">{{ columnLabel(col) }}</th>
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

const tableClass = computed(() => {
  const zone = String(props.zoneKey || '');
  if (zone.includes('contract')) return 'table-zone-contract';
  if (zone.includes('finance')) return 'table-zone-finance';
  return 'table-zone-default';
});

function columnLabel(col: string) {
  const labels = source.value.column_labels && typeof source.value.column_labels === 'object'
    ? source.value.column_labels as Record<string, string>
    : {};
  return labels[col] || col;
}

function stringify(value: unknown) {
  if (value === null || value === undefined) return '--';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
</script>

<style scoped>
.block {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #fff;
  padding: 12px;
  min-height: 170px;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.block-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.block-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.block-subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: #64748b;
}

.table-wrap { overflow: auto; }
.mini-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.mini-table th,
.mini-table td { border: 1px solid #e5e7eb; padding: 9px 10px; text-align: left; }
.mini-table th { border: 1px solid #e5e7eb; background: #f8fafc; font-weight: 700; color: #334155; padding: 9px 10px; }
.mini-table tbody tr:nth-child(2n) td { background: #fcfdff; }
.mini-table tbody tr:hover td { background: #f8fafc; }
.empty-text { margin: 6px 0 0; color: #6b7280; font-size: 13px; }

.table-zone-contract {
  border-color: #dbeafe;
  background: #f8fbff;
}

.table-zone-finance {
  border-color: #dcfce7;
  background: #f6fff9;
}
</style>
