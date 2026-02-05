<template>
  <section class="page">
    <KanbanPage
      v-if="viewMode === 'kanban'"
      :title="pageTitle"
      :status="status"
      :loading="status === 'loading'"
      :error-message="errorMessage"
      :trace-id="traceId"
      :error="error"
      :records="records"
      :fields="kanbanFields"
      :title-field="kanbanTitleField"
      :subtitle="subtitle"
      :status-label="statusLabel"
      :on-reload="reload"
      :on-card-click="handleRowClick"
    />
    <ListPage
      v-else
      :title="pageTitle"
      :model="model"
      :status="status"
      :loading="status === 'loading'"
      :error-message="errorMessage"
      :trace-id="traceId"
      :error="error"
      :columns="columns"
      :records="records"
      :sort-label="sortLabel"
      :sort-options="sortOptions"
      :sort-value="sortValue"
      :search-term="searchTerm"
      :subtitle="subtitle"
      :status-label="statusLabel"
      :on-reload="reload"
      :on-search="handleSearch"
      :on-sort="handleSort"
      :on-row-click="handleRowClick"
    />

    <DevContextPanel
      :visible="showHud"
      title="View Context"
      :entries="hudEntries"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { listRecordsRaw } from '../api/data';
import { resolveAction } from '../app/resolvers/actionResolver';
import { loadActionContract } from '../api/contract';
import { useSessionStore } from '../stores/session';
import ListPage from '../pages/ListPage.vue';
import KanbanPage from '../pages/KanbanPage.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import { deriveListStatus } from '../app/view_state';
import { isHudEnabled } from '../config/debug';
import { ErrorCodes } from '../app/error_codes';
import { evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { useStatus } from '../composables/useStatus';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const status = ref<'idle' | 'loading' | 'ok' | 'empty' | 'error'>('idle');
const traceId = ref('');
const lastTraceId = ref('');
const records = ref<Array<Record<string, unknown>>>([]);
const searchTerm = ref('');
const sortValue = ref('');
const columns = ref<string[]>([]);
const kanbanFields = ref<string[]>([]);
const lastIntent = ref('');
const lastWriteMode = ref('');
const lastLatencyMs = ref<number | null>(null);
const { error, clearError, setError } = useStatus();

const actionId = computed(() => Number(route.params.actionId));
const actionMeta = computed(() => session.currentAction);

const model = computed(() => actionMeta.value?.model ?? '');
const injectedTitle = inject('pageTitle', computed(() => ''));
const menuId = computed(() => Number(route.query.menu_id ?? 0));
const viewMode = computed(() => (actionMeta.value?.view_modes?.[0] ?? 'tree').toString());
const sortLabel = computed(() => sortValue.value || 'id asc');
const sortOptions = computed(() => [
  { label: 'Name ↑', value: 'name asc' },
  { label: 'Name ↓', value: 'name desc' },
  { label: 'Updated ↓', value: 'write_date desc' },
  { label: 'Updated ↑', value: 'write_date asc' },
]);
const subtitle = computed(() => `${records.value.length} records · sorted by ${sortLabel.value}`);
const kanbanTitleField = computed(() => {
  const candidates = ['display_name', 'name'];
  const found = candidates.find((field) => kanbanFields.value.includes(field));
  return found || kanbanFields.value[0] || 'id';
});
const statusLabel = computed(() => {
  if (status.value === 'loading') return 'Loading';
  if (status.value === 'error') return 'Error';
  if (status.value === 'empty') return 'Empty';
  return 'Ready';
});
const pageTitle = computed(() => injectedTitle?.value || actionMeta.value?.name || 'Workspace');
const showHud = computed(() => isHudEnabled(route));
const errorMessage = computed(() => (error.value?.code ? `code=${error.value.code} · ${error.value.message}` : error.value?.message || ''));
const hudEntries = computed(() => [
  { label: 'action_id', value: actionId.value || '-' },
  { label: 'menu_id', value: menuId.value || '-' },
  { label: 'model', value: model.value || '-' },
  { label: 'view_mode', value: viewMode.value || '-' },
  { label: 'order', value: sortLabel.value || '-' },
  { label: 'last_intent', value: lastIntent.value || '-' },
  { label: 'write_mode', value: lastWriteMode.value || '-' },
  { label: 'trace_id', value: traceId.value || lastTraceId.value || '-' },
  { label: 'latency_ms', value: lastLatencyMs.value ?? '-' },
  { label: 'route', value: route.fullPath },
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
  const directViews = (contract as any)?.views || (contract as any)?.ui_contract?.views;
  if (directViews) {
    const treeBlock = directViews.tree || directViews.list;
    const treeColumns = treeBlock?.columns;
    if (Array.isArray(treeColumns) && treeColumns.length) {
      return treeColumns;
    }
    const treeSchema = treeBlock?.columnsSchema || treeBlock?.columns_schema;
    if (Array.isArray(treeSchema) && treeSchema.length) {
      return treeSchema.map((col: { name?: string }) => col.name).filter(Boolean);
    }
  }

  const columns = (contract as any)?.ui_contract?.columns;
  if (Array.isArray(columns) && columns.length) {
    return columns;
  }
  const schema = (contract as any)?.ui_contract?.columnsSchema;
  if (Array.isArray(schema) && schema.length) {
    return schema.map((col: { name?: string }) => col.name).filter(Boolean);
  }
  const rawFields = contract?.ui_contract_raw?.fields;
  if (rawFields && typeof rawFields === 'object') {
    return Object.keys(rawFields);
  }
  return [];
}

function extractKanbanFields(contract: Awaited<ReturnType<typeof loadActionContract>>) {
  const directViews = (contract as any)?.views || (contract as any)?.ui_contract?.views;
  if (directViews) {
    const kanbanBlock = directViews.kanban;
    if (Array.isArray(kanbanBlock?.fields) && kanbanBlock.fields.length) {
      return kanbanBlock.fields;
    }
  }
  const fieldsMap = (contract as any)?.fields || (contract as any)?.ui_contract_raw?.fields;
  if (fieldsMap && typeof fieldsMap === 'object') {
    const preferred = ['display_name', 'name', 'stage_id', 'user_id', 'partner_id', 'write_date', 'create_date'];
    const available = Object.keys(fieldsMap);
    const picked = preferred.filter((field) => available.includes(field));
    if (picked.length) {
      return picked;
    }
    return available.slice(0, 6);
  }
  return ['name', 'id'];
}

function getActionType(meta: unknown) {
  const raw = (meta as { type?: string; action_type?: string }) || {};
  return String(raw.type || raw.action_type || '').toLowerCase();
}

function isClientAction(meta: unknown) {
  const raw = meta as { tag?: string; type?: string; action_type?: string };
  const tag = String(raw?.tag || '').toLowerCase();
  const actionType = getActionType(meta);
  return actionType.includes('client') || tag.length > 0;
}

function isWindowAction(meta: unknown) {
  const actionType = getActionType(meta);
  return actionType.includes('act_window') || actionType.includes('window') || actionType === '';
}

async function load() {
  status.value = 'loading';
  clearError();
  traceId.value = '';
  lastIntent.value = 'api.data.list';
  lastWriteMode.value = 'read';
  lastLatencyMs.value = null;
  records.value = [];
  columns.value = [];
  kanbanFields.value = [];
  const startedAt = Date.now();

  if (!actionId.value) {
    setError(new Error('Action id missing'), 'Action id missing');
    status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
    return;
  }

  try {
    const { contract, meta } = await resolveAction(session.menuTree, actionId.value, actionMeta.value);
    if (meta) {
      session.setActionMeta(meta);
    }
    if (!sortValue.value) {
      const viewOrder = (contract as any)?.views?.tree?.order || (contract as any)?.ui_contract?.views?.tree?.order;
      const order = viewOrder || (meta as any)?.order;
      if (typeof order === 'string' && order.trim()) {
        sortValue.value = order;
      } else {
        sortValue.value = 'id asc';
      }
    }
    const policy = evaluateCapabilityPolicy({ source: meta, available: session.capabilities });
    if (policy.state !== 'enabled') {
      await router.replace({
        name: 'workbench',
        query: {
          menu_id: menuId.value || undefined,
          action_id: actionId.value || undefined,
          reason: ErrorCodes.CAPABILITY_MISSING,
          missing: policy.missing.join(','),
        },
      });
      return;
    }
    const resolvedModel = meta?.model ?? model.value;
    if (!resolvedModel) {
      if (isClientAction(meta)) {
        await router.replace({
          name: 'workbench',
          query: {
            menu_id: menuId.value || undefined,
            action_id: actionId.value || undefined,
            reason: ErrorCodes.ACT_NO_MODEL,
          },
        });
        return;
      }
      if (!isWindowAction(meta)) {
        await router.replace({
          name: 'workbench',
          query: {
            menu_id: menuId.value || undefined,
            action_id: actionId.value || undefined,
            reason: ErrorCodes.ACT_UNSUPPORTED_TYPE,
          },
        });
        return;
      }
      setError(new Error('Action has no model'), 'Action has no model');
      status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
      return;
    }
    const contractColumns = extractColumnsFromContract(contract);
    const kanbanContractFields = extractKanbanFields(contract);
    kanbanFields.value = kanbanContractFields;
    const requestedFields = viewMode.value === 'kanban' ? kanbanContractFields : contractColumns;
    const result = await listRecordsRaw({
      model: resolvedModel,
      fields: requestedFields.length ? requestedFields : ['id', 'name'],
      domain: normalizeDomain(meta?.domain),
      context: mergeContext(meta?.context),
      limit: 40,
      offset: 0,
      search_term: searchTerm.value.trim() || undefined,
      order: sortLabel.value,
    });
    records.value = result.data?.records ?? [];
    columns.value = contractColumns.length ? contractColumns : pickColumns(records.value);
    status.value = deriveListStatus({ error: '', recordsLength: records.value.length });
    if (result.meta?.trace_id) {
      traceId.value = String(result.meta.trace_id);
      lastTraceId.value = String(result.meta.trace_id);
    } else if (result.traceId) {
      traceId.value = String(result.traceId);
      lastTraceId.value = String(result.traceId);
    }
    lastLatencyMs.value = Date.now() - startedAt;
  } catch (err) {
    setError(err, 'failed to load list');
    traceId.value = error.value?.traceId || '';
    lastTraceId.value = error.value?.traceId || '';
    status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
    lastLatencyMs.value = Date.now() - startedAt;
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

function handleSearch(value: string) {
  searchTerm.value = value;
  load();
}

function handleSort(value: string) {
  sortValue.value = value;
  load();
}

onMounted(load);
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
}
</style>
