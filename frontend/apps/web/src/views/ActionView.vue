<template>
  <section class="page">
    <header class="header">
      <div>
        <h2>{{ title }}</h2>
        <p class="meta">Model: {{ model || 'N/A' }}</p>
      </div>
      <button @click="reload">Reload</button>
    </header>

    <section class="summary">
      <div>
        <p class="label">Action ID</p>
        <p class="value">{{ actionId || 'N/A' }}</p>
      </div>
      <div>
        <p class="label">View Mode</p>
        <p class="value">{{ viewMode }}</p>
      </div>
      <div>
        <p class="label">Menu ID</p>
        <p class="value">{{ menuId || 'N/A' }}</p>
      </div>
    </section>

    <ListPage
      :title="listTitle"
      :model="model"
      :status="status"
      :loading="status === 'loading'"
      :error-message="errorMessage"
      :trace-id="traceId"
      :columns="columns"
      :records="records"
      :sort-label="sortLabel"
      :on-reload="reload"
      :on-row-click="handleRowClick"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { listRecords } from '../api/data';
import { ApiError } from '../api/client';
import { resolveAction } from '../app/resolvers/actionResolver';
import { loadActionContract } from '../api/contract';
import { useSessionStore } from '../stores/session';
import ListPage from '../pages/ListPage.vue';
import { deriveListStatus } from '../app/view_state';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const status = ref<'idle' | 'loading' | 'ok' | 'empty' | 'error'>('idle');
const error = ref('');
const errorCode = ref<number | null>(null);
const traceId = ref('');
const records = ref<Array<Record<string, unknown>>>([]);
const columns = ref<string[]>([]);

const actionId = computed(() => Number(route.params.actionId));
const actionMeta = computed(() => session.currentAction);

const model = computed(() => actionMeta.value?.model ?? '');
const title = computed(() => actionMeta.value?.action_id ? `Action ${actionMeta.value?.action_id}` : 'Action');
const menuId = computed(() => Number(route.query.menu_id ?? 0));
const viewMode = computed(() => (actionMeta.value?.view_modes?.[0] ?? 'tree').toString());
const listTitle = computed(() => actionMeta.value?.name || title.value);
const errorMessage = computed(() => {
  if (!error.value) {
    return '';
  }
  return errorCode.value ? `code=${errorCode.value} · ${error.value}` : error.value;
});
const sortLabel = computed(() => {
  const order = (actionMeta.value as any)?.order;
  if (typeof order === 'string' && order.trim()) {
    return order;
  }
  return 'id asc';
});

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
  if (Array.isArray(domain)) {
    return domain;
  }
  return [];
}

function pickColumns(rows: Array<Record<string, unknown>>) {
  if (!rows.length) {
    return ['id', 'name'];
  }
  const first = rows[0];
  const keys = Object.keys(first);
  return keys.slice(0, 6);
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
  status.value = 'loading';
  error.value = '';
  errorCode.value = null;
  traceId.value = '';
  records.value = [];
  columns.value = [];

  if (!model.value) {
    error.value = 'Action has no model';
    status.value = deriveListStatus({ error: error.value, recordsLength: 0 });
    return;
  }

  try {
    const { contract } = await resolveAction(session.menuTree, actionId.value, actionMeta.value);
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
    status.value = deriveListStatus({ error: '', recordsLength: records.value.length });
  } catch (err) {
    if (err instanceof ApiError) {
      traceId.value = err.traceId ?? '';
      error.value = err.message;
      errorCode.value = err.status ?? null;
    } else {
      error.value = err instanceof Error ? err.message : 'failed to load list';
    }
    status.value = deriveListStatus({ error: error.value, recordsLength: 0 });
  }
}

function handleRowClick(row: Record<string, unknown>) {
  const id = row.id;
  if (!model.value) {
    return;
  }
  if (typeof id === 'number') {
    router.push({
      path: `/r/${model.value}/${id}`,
      query: { menu_id: menuId.value || undefined, action_id: actionId.value || undefined },
    });
  } else if (typeof id === 'string' && id) {
    router.push({
      path: `/r/${model.value}/${id}`,
      query: { menu_id: menuId.value || undefined, action_id: actionId.value || undefined },
    });
  }
}

function reload() {
  load();
}

onMounted(load);
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

button {
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
  background: #111827;
  color: white;
  cursor: pointer;
}
</style>
