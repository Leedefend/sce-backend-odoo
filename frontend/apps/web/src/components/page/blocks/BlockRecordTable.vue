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
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-sm);
  background: rgba(255, 255, 255, 0.94);
  padding: var(--ui-space-3);
  min-height: 170px;
  box-shadow: var(--ui-shadow-xs);
}

.block-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--ui-space-3);
  margin-bottom: var(--ui-space-3);
}

.block-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: var(--ui-font-weight-bold);
  color: var(--ui-color-ink-strong);
}

.block-subtitle {
  margin: 4px 0 0;
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-muted);
}

.table-wrap { overflow: auto; }
.mini-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.mini-table th,
.mini-table td { border: 1px solid var(--ui-color-border); padding: 9px 10px; text-align: left; }
.mini-table th {
  border: 1px solid var(--ui-color-border);
  background: rgba(240, 246, 250, 0.72);
  color: var(--ui-color-ink);
  font-weight: var(--ui-font-weight-bold);
  padding: 9px 10px;
}
.mini-table tbody tr:nth-child(2n) td { background: rgba(248, 245, 239, 0.52); }
.mini-table tbody tr:hover td { background: rgba(240, 246, 250, 0.62); }
.empty-text { margin: 6px 0 0; color: var(--ui-color-ink-muted); font-size: 13px; }

.table-zone-contract {
  border-color: rgba(61, 120, 159, 0.18);
  background: linear-gradient(180deg, rgba(240, 246, 250, 0.58), rgba(255, 255, 255, 0.92));
}

.table-zone-finance {
  border-color: rgba(31, 122, 91, 0.18);
  background: linear-gradient(180deg, rgba(235, 248, 242, 0.72), rgba(255, 255, 255, 0.92));
}
</style>
