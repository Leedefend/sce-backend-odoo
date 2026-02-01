<template>
  <main class="page">
    <header class="header">
      <div>
        <h1>{{ title }}</h1>
        <p class="meta">Model: {{ model }}</p>
      </div>
      <button @click="reload">Reload</button>
    </header>

    <section class="table" v-if="records.length">
      <table>
        <thead>
          <tr>
            <th v-for="col in columns" :key="col">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in records" :key="String(row.id ?? index)" @click="openRecord(row.id)">
            <td v-for="col in columns" :key="col">
              {{ formatValue(row[col]) }}
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <p v-else class="empty">No data loaded.</p>

    <p v-if="error" class="error">{{ error }}</p>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { listRecords } from '../api/data';
import { loadActionContract } from '../api/contract';
import { useSessionStore } from '../stores/session';
import { findActionMeta } from '../app/menu';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const error = ref('');
const records = ref<Array<Record<string, unknown>>>([]);
const columns = ref<string[]>([]);

const actionId = computed(() => Number(route.params.actionId));
const actionMeta = computed(() => {
  return session.currentAction ?? findActionMeta(session.menuTree, actionId.value);
});

const model = computed(() => actionMeta.value?.model ?? '');
const title = computed(() => actionMeta.value?.action_id ? `Action ${actionMeta.value?.action_id}` : 'Action');
const menuId = computed(() => Number(route.query.menu_id ?? 0));

function mergeContext(base: Record<string, unknown> | string | undefined) {
  if (!base || typeof base === 'string') {
    return menuId.value ? { menu_id: menuId.value } : {};
  }
  if (!menuId.value) {
    return base;
  }
  return { ...base, menu_id: menuId.value };
}

function normalizeDomain(domain: unknown) {
  if (!domain) {
    return [];
  }
  return domain;
}

function pickColumns(rows: Array<Record<string, unknown>>) {
  if (!rows.length) {
    return ['id', 'name'];
  }
  const first = rows[0];
  const keys = Object.keys(first);
  return keys.slice(0, 6);
}

function formatValue(value: unknown) {
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  if (value && typeof value === 'object') {
    return JSON.stringify(value);
  }
  return value ?? '';
}

function extractColumnsFromContract(contract: Awaited<ReturnType<typeof loadActionContract>>) {
  const columns = contract?.ui_contract?.columns;
  if (Array.isArray(columns) && columns.length) {
    return columns;
  }
  const schema = contract?.ui_contract?.columnsSchema;
  if (Array.isArray(schema) && schema.length) {
    return schema.map((col) => col.name).filter(Boolean);
  }
  const rawFields = contract?.ui_contract_raw?.fields;
  if (rawFields && typeof rawFields === 'object') {
    return Object.keys(rawFields);
  }
  return [];
}

async function load() {
  error.value = '';
  records.value = [];
  columns.value = [];

  if (!model.value) {
    error.value = 'Action has no model';
    return;
  }

  try {
    const contract = await loadActionContract(actionId.value);
    const contractColumns = extractColumnsFromContract(contract);
    const result = await listRecords({
      model: model.value,
      fields: contractColumns.length ? contractColumns : ['id', 'name'],
      domain: normalizeDomain(actionMeta.value?.domain),
      context: mergeContext(actionMeta.value?.context),
      limit: 40,
      offset: 0,
    });
    records.value = result.records ?? [];
    columns.value = contractColumns.length ? contractColumns : pickColumns(records.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'failed to load list';
  }
}

function openRecord(id: unknown) {
  if (!model.value) {
    return;
  }
  if (typeof id === 'number') {
    router.push(`/r/${model.value}/${id}`);
  } else if (typeof id === 'string' && id) {
    router.push(`/r/${model.value}/${id}`);
  }
}

function reload() {
  load();
}

onMounted(load);
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 32px;
  background: #f8fafc;
  font-family: "IBM Plex Sans", system-ui, sans-serif;
  color: #0f172a;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.meta {
  color: #64748b;
  font-size: 14px;
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

button {
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
  background: #111827;
  color: white;
  cursor: pointer;
}

.error {
  margin-top: 16px;
  color: #dc2626;
}

.empty {
  color: #64748b;
}
</style>
