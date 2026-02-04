<template>
  <section class="page">
    <header class="header">
      <div>
        <h2>{{ title }}</h2>
        <p class="meta">{{ subtitle }}</p>
      </div>
      <div class="actions">
        <span class="pill" :class="status">{{ statusLabel }}</span>
        <button class="ghost" @click="onReload" :disabled="loading">Reload</button>
      </div>
    </header>

    <section class="toolbar">
      <div class="search">
        <input type="search" placeholder="Search" disabled />
      </div>
      <div class="filters">
        <span class="filter">All</span>
        <span class="filter">Active</span>
        <span class="filter">Archived</span>
      </div>
      <div class="sort">
        <span class="label">Sort</span>
        <span class="value">{{ sortLabel || 'default' }}</span>
      </div>
    </section>

    <StatusPanel v-if="loading" title="Loading list..." variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
      title="Request failed"
      :message="error?.message || errorMessage"
      :trace-id="error?.traceId || traceId"
      :error-code="error?.code || errorCode"
      :hint="error?.hint || errorHint"
      variant="error"
      :on-retry="onReload"
    />
    <StatusPanel
      v-else-if="status === 'empty'"
      title="No data"
      message="No records returned for this action."
      variant="info"
      :on-retry="onReload"
    />

    <section v-else class="table">
      <table>
        <thead>
          <tr>
            <th v-for="col in columns" :key="col">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in records" :key="String(row.id ?? index)" @click="handleRow(row)">
            <td v-for="col in columns" :key="col">
              {{ formatValue(row[col]) }}
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import StatusPanel from '../components/StatusPanel.vue';
import type { StatusError } from '../composables/useStatus';

const props = defineProps<{
  title: string;
  model: string;
  status: 'loading' | 'ok' | 'empty' | 'error';
  loading: boolean;
  errorMessage?: string;
  traceId?: string;
  errorCode?: number | null;
  errorHint?: string;
  error?: StatusError | null;
  columns: string[];
  records: Array<Record<string, unknown>>;
  onReload: () => void;
  onRowClick: (row: Record<string, unknown>) => void;
  sortLabel?: string;
}>();

const statusLabel = computed(() => {
  if (props.status === 'loading') return 'Loading';
  if (props.status === 'error') return 'Error';
  if (props.status === 'empty') return 'Empty';
  return 'Ready';
});

const subtitle = computed(() => {
  return `${props.records.length} records · ${props.columns.length} columns`;
});
function formatValue(value: unknown) {
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  if (value && typeof value === 'object') {
    return JSON.stringify(value);
  }
  return value ?? '';
}

function handleRow(row: Record<string, unknown>) {
  props.onRowClick(row);
}
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.meta {
  color: #64748b;
  font-size: 14px;
}

.toolbar {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 12px;
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.08);
  align-items: center;
}

.search input {
  width: 100%;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: #f8fafc;
}

.filters {
  display: flex;
  gap: 8px;
}

.filter {
  padding: 6px 10px;
  border-radius: 999px;
  background: #f1f5f9;
  font-size: 12px;
  color: #475569;
}

.sort {
  display: grid;
  justify-items: end;
  gap: 4px;
}

.sort .label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #94a3b8;
}

.sort .value {
  font-weight: 600;
}

.table {
  overflow: auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
  font-size: 14px;
}

thead th {
  position: sticky;
  top: 0;
  background: white;
  z-index: 1;
}

tr:hover {
  background: #f1f5f9;
  cursor: pointer;
}

.pill {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  background: #e2e8f0;
  color: #1e293b;
}

.pill.ok {
  background: #dcfce7;
  color: #14532d;
}

.pill.error {
  background: #fee2e2;
  color: #991b1b;
}

.pill.loading {
  background: #e0f2fe;
  color: #075985;
}

.pill.empty {
  background: #fef3c7;
  color: #92400e;
}

button {
  padding: 8px 12px;
  border: none;
  border-radius: 10px;
  background: #111827;
  color: white;
  cursor: pointer;
}

.ghost {
  background: transparent;
  color: #111827;
  border: 1px solid rgba(15, 23, 42, 0.12);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
