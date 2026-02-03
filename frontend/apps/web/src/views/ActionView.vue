<template>
  <section class="page">
    <header class="header">
      <div>
        <h2>{{ title }}</h2>
        <p class="meta">{{ subtitle }}</p>
      </div>
      <div class="actions">
        <span class="status-dot" :class="status"></span>
        <span class="status-text">{{ statusLabel }}</span>
        <button class="ghost" @click="reload">Reload</button>
      </div>
    </header>

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

    <DevContextPanel
      :visible="showHud"
      title="Action Context"
      :entries="hudEntries"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { listRecordsRaw } from '../api/data';
import { ApiError } from '../api/client';
import { resolveAction } from '../app/resolvers/actionResolver';
import { loadActionContract } from '../api/contract';
import { useSessionStore } from '../stores/session';
import ListPage from '../pages/ListPage.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import { deriveListStatus } from '../app/view_state';
import { isHudEnabled } from '../config/debug';
import type { NavNode } from '@sc/schema';

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
const title = computed(() => {
  const menuLabel = findMenuName(session.menuTree, menuId.value);
  return menuLabel || actionMeta.value?.name || 'List';
});
const menuId = computed(() => Number(route.query.menu_id ?? 0));
const viewMode = computed(() => (actionMeta.value?.view_modes?.[0] ?? 'tree').toString());
const listTitle = computed(() => actionMeta.value?.name || title.value);
const sortLabel = computed(() => {
  const order = (actionMeta.value as any)?.order;
  if (typeof order === 'string' && order.trim()) {
    return order;
  }
  return 'id asc';
});
const subtitle = computed(() => `${records.value.length} records · sorted by ${sortLabel.value}`);
const statusLabel = computed(() => {
  if (status.value === 'loading') return 'Loading';
  if (status.value === 'error') return 'Error';
  if (status.value === 'empty') return 'Empty';
  return 'Ready';
});
const showHud = computed(() => isHudEnabled(route));
const errorMessage = computed(() => {
  if (!error.value) {
    return '';
  }
  return errorCode.value ? `code=${errorCode.value} · ${error.value}` : error.value;
});

function findMenuName(nodes: NavNode[], menuId?: number): string {
  if (!menuId) {
    return '';
  }
  const walk = (items: NavNode[]): string | null => {
    for (const node of items) {
      if (node.menu_id === menuId || node.id === menuId) {
        return node.title || node.name || node.label || '';
      }
      if (node.children?.length) {
        const found = walk(node.children);
        if (found) return found;
      }
    }
    return null;
  };
  return walk(nodes) || '';
}
const hudEntries = computed(() => [
  { label: 'action_id', value: actionId.value || '-' },
  { label: 'menu_id', value: menuId.value || '-' },
  { label: 'model', value: model.value || '-' },
  { label: 'view_mode', value: viewMode.value || '-' },
  { label: 'route', value: route.fullPath },
  { label: 'trace_id', value: traceId.value || '-' },
]);

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
    const result = await listRecordsRaw({
      model: model.value,
      fields: contractColumns.length ? contractColumns : ['id', 'name'],
      domain: normalizeDomain(actionMeta.value?.domain),
      context: mergeContext(actionMeta.value?.context),
      limit: 40,
      offset: 0,
    });
    records.value = result.data?.records ?? [];
    columns.value = contractColumns.length ? contractColumns : pickColumns(records.value);
    status.value = deriveListStatus({ error: '', recordsLength: records.value.length });
    if (result.meta?.trace_id) {
      traceId.value = String(result.meta.trace_id);
    }
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

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #94a3b8;
}

.status-dot.loading {
  background: #38bdf8;
}

.status-dot.error {
  background: #ef4444;
}

.status-dot.empty {
  background: #f59e0b;
}

.status-dot.ok {
  background: #22c55e;
}

.status-text {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #64748b;
}

.meta {
  color: #64748b;
  font-size: 14px;
}

button {
  padding: 10px 14px;
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
</style>
