<template>
  <section class="page">
    <PageHeader
      :title="title"
      :subtitle="subtitle"
      :status="status"
      :status-label="statusLabel"
      :loading="loading"
      :on-reload="onReload"
    />

    <PageToolbar
      :loading="loading"
      :search-term="searchTerm || ''"
      :sort-options="sortOptions || []"
      :sort-value="sortValue || ''"
      :on-search="onSearch"
      :on-sort="onSort"
    />

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
import StatusPanel from '../components/StatusPanel.vue';
import PageHeader from '../components/page/PageHeader.vue';
import PageToolbar from '../components/page/PageToolbar.vue';
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
  onSearch: (value: string) => void;
  onSort: (value: string) => void;
  sortLabel?: string;
  searchTerm?: string;
  sortOptions?: Array<{ label: string; value: string }>;
  sortValue?: string;
  subtitle: string;
  statusLabel: string;
}>();
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

</style>
