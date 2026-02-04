<template>
  <section class="page">
    <header class="header">
      <div>
        <h2>{{ title }}</h2>
        <p class="meta">{{ subtitle }}</p>
      </div>
      <div class="actions">
        <span class="pill" :class="statusTone">{{ statusLabel }}</span>
        <button class="ghost" @click="goBack">Back</button>
        <button v-if="status === 'ok' && canEdit" @click="startEdit">Edit</button>
        <button v-if="status === 'editing'" @click="save" :disabled="isSaveDisabled">Save</button>
        <button v-if="status === 'editing'" class="ghost" @click="cancelEdit">Cancel</button>
        <button class="ghost" @click="reload" :disabled="status === 'loading' || status === 'saving'">Reload</button>
      </div>
    </header>

    <StatusPanel v-if="status === 'loading'" title="Loading record..." variant="info" />
    <StatusPanel v-else-if="status === 'saving'" title="Saving record..." variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
      title="Request failed"
      :message="errorCode ? `code=${errorCode} · ${error}` : error"
      :trace-id="traceId"
      :error-code="errorCode"
      :hint="errorHint"
      variant="error"
      :on-retry="reload"
    />
    <StatusPanel
      v-else-if="status === 'empty'"
      title="No data"
      message="Record not found or not readable."
      variant="info"
      :on-retry="reload"
    />

    <section v-else class="card" :class="{ editing: status === 'editing' }">
      <div v-if="status === 'ok' && lastAction === 'save'" class="banner success">
        Saved. Changes have been applied.
      </div>
      <div v-for="field in fields" :key="field.name" class="field">
        <span class="label">{{ field.label }}</span>
        <span class="value">
          <input
            v-if="status === 'editing' && field.name === 'name'"
            v-model="draftName"
            class="input"
            type="text"
          />
          <FieldValue v-else :value="field.value" :field="field.descriptor" />
        </span>
      </div>
    </section>

    <DevContextPanel
      :visible="showHud"
      title="Record Context"
      :entries="hudEntries"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ApiError } from '../api/client';
import { readRecordRaw, writeRecordV6Raw } from '../api/data';
import { extractFieldNames, resolveView } from '../app/resolvers/viewResolver';
import { deriveRecordStatus } from '../app/view_state';
import type { ViewContract } from '@sc/schema';
import FieldValue from '../components/FieldValue.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import StatusPanel from '../components/StatusPanel.vue';
import { isHudEnabled } from '../config/debug';

const route = useRoute();
const router = useRouter();
const error = ref('');
const errorCode = ref<number | null>(null);
const traceId = ref('');
const lastTraceId = ref('');
const status = ref<'idle' | 'loading' | 'ok' | 'empty' | 'error' | 'editing' | 'saving'>('idle');
const fields = ref<Array<{ name: string; label: string; value: unknown; descriptor?: ViewContract['fields'][string] }>>([]);
const draftName = ref('');
const lastIntent = ref('');
const lastWriteMode = ref('');
const lastLatencyMs = ref<number | null>(null);
const lastAction = ref<'save' | 'load' | ''>('');

const model = computed(() => String(route.params.model || ''));
const recordId = computed(() => Number(route.params.id));
const recordTitle = ref<string | null>(null);
const title = computed(() => recordTitle.value || `Record ${recordId.value}`);
const subtitle = computed(() => (status.value === 'editing' ? 'Editing name' : 'Record details'));
const canEdit = computed(() => model.value === 'project.project');
const showHud = computed(() => isHudEnabled(route));
const statusLabel = computed(() => {
  if (status.value === 'editing') return 'Editing';
  if (status.value === 'saving') return 'Saving';
  if (status.value === 'loading') return 'Loading';
  if (status.value === 'error') return 'Error';
  if (status.value === 'empty') return 'Empty';
  return 'Ready';
});
const errorHint = computed(() => {
  if (errorCode.value === 401) return 'Check login session and token.';
  if (errorCode.value === 403) return 'Check access rights for this record.';
  if (errorCode.value === 404) return 'Record not found.';
  return '';
});
const statusTone = computed(() => {
  if (status.value === 'error') return 'danger';
  if (status.value === 'editing' || status.value === 'saving') return 'warn';
  return 'ok';
});
const hudEntries = computed(() => [
  { label: 'model', value: model.value },
  { label: 'record_id', value: recordId.value },
  { label: 'status', value: status.value },
  { label: 'last_intent', value: lastIntent.value || '-' },
  { label: 'write_mode', value: lastWriteMode.value || '-' },
  { label: 'trace_id', value: traceId.value || lastTraceId.value || '-' },
  { label: 'latency_ms', value: lastLatencyMs.value ?? '-' },
  { label: 'route', value: route.fullPath },
]);

async function load() {
  error.value = '';
  errorCode.value = null;
  traceId.value = '';
  fields.value = [];
  status.value = 'loading';
  lastIntent.value = 'api.data.read';
  lastWriteMode.value = 'read';
  lastAction.value = 'load';
  const startedAt = Date.now();

  if (!model.value || !recordId.value) {
    error.value = 'Missing model or id';
    status.value = deriveRecordStatus({ error: error.value, fieldsLength: 0 });
    return;
  }

  try {
    const view = await resolveView(model.value, 'form');
    const layout = view?.layout;
    if (!layout) {
      error.value = 'Missing view layout';
      status.value = 'empty';
      lastLatencyMs.value = Date.now() - startedAt;
      return;
    }

    const fieldNames = extractFieldNames(layout).filter(Boolean);
    const read = await readRecordRaw({
      model: model.value,
      ids: [recordId.value],
      fields: fieldNames.length ? fieldNames : '*',
    });

    const record = read?.data?.records?.[0] ?? null;
    if (!record) {
      status.value = 'empty';
      lastLatencyMs.value = Date.now() - startedAt;
      return;
    }
    fields.value = (fieldNames.length ? fieldNames : Object.keys(record as Record<string, unknown>)).map((name) => ({
      name,
      label: view?.fields?.[name]?.string ?? name,
      value: (record as Record<string, unknown>)[name],
      descriptor: view?.fields?.[name],
    }));
    status.value = deriveRecordStatus({ error: '', fieldsLength: fields.value.length });
    draftName.value = String(record?.name ?? '');
    recordTitle.value = String(record?.name ?? '') || null;
    if (read.meta?.trace_id) {
      traceId.value = String(read.meta.trace_id);
      lastTraceId.value = String(read.meta.trace_id);
    } else if (read.traceId) {
      traceId.value = String(read.traceId);
      lastTraceId.value = String(read.traceId);
    }
    lastLatencyMs.value = Date.now() - startedAt;
  } catch (err) {
    if (err instanceof ApiError) {
      traceId.value = err.traceId ?? '';
      lastTraceId.value = err.traceId ?? '';
      errorCode.value = err.status ?? null;
      error.value = err.message;
    } else {
      error.value = err instanceof Error ? err.message : 'failed to load record';
    }
    status.value = deriveRecordStatus({ error: error.value, fieldsLength: 0 });
    lastLatencyMs.value = Date.now() - startedAt;
  }
}

function reload() {
  load();
}

function startEdit() {
  if (status.value !== 'ok') {
    return;
  }
  const nameField = fields.value.find((field) => field.name === 'name');
  draftName.value = String(nameField?.value ?? '');
  status.value = 'editing';
}

function cancelEdit() {
  if (status.value !== 'editing') {
    return;
  }
  const nameField = fields.value.find((field) => field.name === 'name');
  draftName.value = String(nameField?.value ?? '');
  status.value = 'ok';
}

const isSaveDisabled = computed(() => status.value === 'saving' || !draftName.value.trim());

async function save() {
  if (status.value !== 'editing') {
    return;
  }
  error.value = '';
  errorCode.value = null;
  traceId.value = '';
  status.value = 'saving';
  lastIntent.value = 'api.data.write';
  lastWriteMode.value = 'update';
  lastAction.value = 'save';
  const startedAt = Date.now();

  try {
    const result = await writeRecordV6Raw({
      model: model.value,
      id: recordId.value,
      values: { name: draftName.value.trim() },
    });
    if (result?.meta?.trace_id) {
      lastTraceId.value = String(result.meta.trace_id);
    } else if (result?.traceId) {
      lastTraceId.value = String(result.traceId);
    }
    status.value = 'ok';
    lastLatencyMs.value = Date.now() - startedAt;
    await load();
  } catch (err) {
    if (err instanceof ApiError) {
      traceId.value = err.traceId ?? '';
      lastTraceId.value = err.traceId ?? '';
      errorCode.value = err.status ?? null;
      error.value = err.message;
    } else {
      error.value = err instanceof Error ? err.message : 'failed to save record';
    }
    status.value = 'error';
    lastLatencyMs.value = Date.now() - startedAt;
  }
}

function goBack() {
  router.back();
}

onMounted(load);
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
  color: #0f172a;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions {
  display: flex;
  gap: 8px;
}

.meta {
  color: #64748b;
  font-size: 14px;
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

.pill.warn {
  background: #fef9c3;
  color: #713f12;
}

.pill.danger {
  background: #fee2e2;
  color: #991b1b;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 12px;
}

.card.editing {
  border: 1px dashed #94a3b8;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
}

.field {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.label {
  font-weight: 600;
  color: #334155;
}

.value {
  color: #0f172a;
}

.input {
  width: 100%;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid #cbd5f5;
  font-size: 14px;
}

.banner {
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
}

.banner.success {
  background: #ecfeff;
  border: 1px solid #a5f3fc;
  color: #155e75;
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

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
