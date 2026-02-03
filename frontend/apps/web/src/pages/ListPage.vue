<template>
  <section class="page">
    <header class="header">
      <div>
        <h2>{{ title }}</h2>
        <p class="meta">Model: {{ model || 'N/A' }}</p>
      </div>
      <div class="actions">
        <span class="pill" :class="status">{{ statusLabel }}</span>
        <button @click="onReload" :disabled="loading">Reload</button>
      </div>
    </header>

    <section class="summary">
      <div>
        <p class="label">Columns</p>
        <p class="value">{{ columns.length || 'N/A' }}</p>
      </div>
      <div>
        <p class="label">Records</p>
        <p class="value">{{ records.length || '0' }}</p>
      </div>
      <div>
        <p class="label">Sort</p>
        <p class="value">{{ sortLabel || 'default' }}</p>
      </div>
    </section>

    <StatusPanel v-if="loading" title="Loading list..." variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
      title="Request failed"
      :message="errorMessage"
      :trace-id="traceId"
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

const props = defineProps<{
  title: string;
  model: string;
  status: 'loading' | 'ok' | 'empty' | 'error';
  loading: boolean;
  errorMessage?: string;
  traceId?: string;
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

.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.08);
}

.summary .label {
  margin: 0;
  font-size: 12px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.summary .value {
  margin: 4px 0 0;
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
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
  background: #111827;
  color: white;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
