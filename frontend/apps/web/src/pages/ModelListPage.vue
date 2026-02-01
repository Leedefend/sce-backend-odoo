<template>
  <main class="page">
    <header class="header">
      <div>
        <h1>{{ title }}</h1>
        <p class="meta">Model: {{ model }}</p>
      </div>
      <div class="actions">
        <button @click="toggleSort">Sort: {{ orderLabel }}</button>
        <button @click="reload">Reload</button>
      </div>
    </header>

    <StatusPanel v-if="loading" title="Loading list..." variant="info" />
    <StatusPanel
      v-else-if="error"
      title="Request failed"
      :message="error"
      :trace-id="traceId"
      variant="error"
      :on-retry="reload"
    />

    <section v-else-if="records.length" class="table">
      <table>
        <thead>
          <tr>
            <th v-for="col in columns" :key="col">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in records" :key="String(row.id ?? index)" @click="openRow(row.id)">
            <td v-for="col in columns" :key="col">
              <FieldValue :value="row[col]" />
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <p v-else class="empty">No data loaded.</p>

    <footer class="pager">
      <button :disabled="offset === 0" @click="prevPage">Prev</button>
      <span>Offset: {{ offset }}</span>
      <button :disabled="records.length < limit" @click="nextPage">Next</button>
    </footer>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ApiError } from '../api/client';
import { listRecords } from '../api/data';
import { resolveAction } from '../app/resolvers/actionResolver';
import { openForm } from '../services/action_service';
import { recordTrace, createTraceId } from '../services/trace';
import { useSessionStore } from '../stores/session';
import StatusPanel from '../components/StatusPanel.vue';
import FieldValue from '../components/FieldValue.vue';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const error = ref('');
const traceId = ref('');
const loading = ref(false);
const records = ref<Array<Record<string, unknown>>>([]);
const columns = ref<string[]>([]);

const model = computed(() => String(route.params.model || ''));
const actionId = computed(() => Number(route.query.action_id || 0));
const menuId = computed(() => Number(route.query.menu_id || 0));
const limit = 20;
const offset = ref(0);
const order = ref('id asc');

const title = computed(() => `List: ${model.value}`);
const orderLabel = computed(() => (order.value.includes('desc') ? 'id desc' : 'id asc'));

function pickColumns(rows: Array<Record<string, unknown>>) {
  if (!rows.length) {
    return ['id', 'name'];
  }
  const first = rows[0];
  const keys = Object.keys(first);
  return keys.slice(0, 6);
}

async function load() {
  error.value = '';
  traceId.value = '';
  loading.value = true;

  if (!model.value) {
    error.value = 'Missing model';
    loading.value = false;
    return;
  }

  try {
    let meta = session.currentAction ?? undefined;
    let contractColumns: string[] = [];
    if (actionId.value) {
      const resolved = await resolveAction(session.menuTree, actionId.value, session.currentAction);
      meta = resolved.meta;
      contractColumns = resolved.contract?.ui_contract?.columns ?? [];
    }
    const result = await listRecords({
      model: model.value,
      fields: contractColumns.length ? contractColumns : ['id', 'name'],
      domain: Array.isArray(meta?.domain) ? meta.domain : [],
      context: (meta?.context as Record<string, unknown>) ?? {},
      limit,
      offset: offset.value,
      order: order.value,
    });
    records.value = result.records ?? [];
    columns.value = contractColumns.length ? contractColumns : pickColumns(records.value);
    recordTrace({
      ts: Date.now(),
      trace_id: createTraceId(),
      intent: 'api.data.list',
      status: 'ok',
      menu_id: menuId.value || undefined,
      action_id: actionId.value || undefined,
      model: model.value,
      view_mode: 'tree',
      params_digest: JSON.stringify({ offset: offset.value, order: order.value }),
    });
  } catch (err) {
    if (err instanceof ApiError) {
      traceId.value = err.traceId ?? '';
      error.value = err.message;
    } else {
      error.value = err instanceof Error ? err.message : 'failed to load list';
    }
  } finally {
    loading.value = false;
  }
}

function reload() {
  load();
}

function toggleSort() {
  order.value = order.value.includes('desc') ? 'id asc' : 'id desc';
  load();
}

function nextPage() {
  offset.value += limit;
  load();
}

function prevPage() {
  offset.value = Math.max(0, offset.value - limit);
  load();
}

function openRow(id: unknown) {
  if (typeof id !== 'number' || !model.value) {
    return;
  }
  openForm(router, model.value, id, session.currentAction ?? undefined, menuId.value || undefined);
}

watch(() => route.fullPath, () => {
  offset.value = 0;
  load();
});

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

.actions {
  display: flex;
  gap: 8px;
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

.pager {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  align-items: center;
}

.empty {
  color: #64748b;
}
</style>
