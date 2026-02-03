<template>
  <section class="page">
    <header class="header">
      <div>
        <h2>{{ title }}</h2>
        <p class="meta">Model: {{ model }} · ID: {{ recordId }}</p>
      </div>
      <div class="actions">
        <button class="ghost" @click="goBack">Back</button>
        <button v-if="status === 'ok' && canEdit" @click="startEdit">Edit</button>
        <button v-if="status === 'editing'" @click="save" :disabled="isSaveDisabled">Save</button>
        <button v-if="status === 'editing'" class="ghost" @click="cancelEdit">Cancel</button>
        <button @click="reload" :disabled="status === 'loading' || status === 'saving'">Reload</button>
      </div>
    </header>

    <StatusPanel v-if="status === 'loading'" title="Loading record..." variant="info" />
    <StatusPanel v-else-if="status === 'saving'" title="Saving record..." variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
      title="Request failed"
      :message="error"
      :trace-id="traceId"
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

    <section v-else class="card">
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
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ApiError } from '../api/client';
import { readRecord, writeRecordV6 } from '../api/data';
import { extractFieldNames, resolveView } from '../app/resolvers/viewResolver';
import { deriveRecordStatus } from '../app/view_state';
import type { ViewContract } from '@sc/schema';
import FieldValue from '../components/FieldValue.vue';
import StatusPanel from '../components/StatusPanel.vue';

const route = useRoute();
const router = useRouter();
const error = ref('');
const traceId = ref('');
const status = ref<'idle' | 'loading' | 'ok' | 'empty' | 'error' | 'editing' | 'saving'>('idle');
const fields = ref<Array<{ name: string; label: string; value: unknown; descriptor?: ViewContract['fields'][string] }>>([]);
const draftName = ref('');

const model = computed(() => String(route.params.model || ''));
const recordId = computed(() => Number(route.params.id));
const title = computed(() => `Record ${recordId.value}`);
const canEdit = computed(() => model.value === 'project.project');

async function load() {
  error.value = '';
  traceId.value = '';
  fields.value = [];
  status.value = 'loading';

  if (!model.value || !recordId.value) {
    error.value = 'Missing model or id';
    status.value = deriveRecordStatus({ error: error.value, fieldsLength: 0 });
    return;
  }

  try {
    const view = await resolveView(model.value, 'form');

    const fieldNames = extractFieldNames(view.layout).filter(Boolean);
    const read = await readRecord({
      model: model.value,
      ids: [recordId.value],
      fields: fieldNames.length ? fieldNames : '*',
    });

    const record = read.records?.[0] ?? {};
    fields.value = (fieldNames.length ? fieldNames : Object.keys(record)).map((name) => ({
      name,
      label: view.fields?.[name]?.string ?? name,
      value: record[name],
      descriptor: view.fields?.[name],
    }));
    status.value = deriveRecordStatus({ error: '', fieldsLength: fields.value.length });
    draftName.value = String(record?.name ?? '');
  } catch (err) {
    if (err instanceof ApiError) {
      traceId.value = err.traceId ?? '';
      error.value = err.message;
    } else {
      error.value = err instanceof Error ? err.message : 'failed to load record';
    }
    status.value = deriveRecordStatus({ error: error.value, fieldsLength: 0 });
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
  traceId.value = '';
  status.value = 'saving';

  try {
    await writeRecordV6({
      model: model.value,
      id: recordId.value,
      values: { name: draftName.value.trim() },
    });
    status.value = 'ok';
    await load();
  } catch (err) {
    if (err instanceof ApiError) {
      traceId.value = err.traceId ?? '';
      error.value = err.message;
    } else {
      error.value = err instanceof Error ? err.message : 'failed to save record';
    }
    status.value = 'error';
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

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 12px;
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
