<template>
  <main class="page">
    <header class="header">
      <div>
        <h1>{{ title }}</h1>
        <p class="meta">Model: {{ model }} · ID: {{ recordIdDisplay }}</p>
      </div>
      <div class="actions">
        <button
          v-for="btn in headerButtons"
          :key="btn.name ?? btn.string"
          :disabled="!recordId || saving || loading || executing === btn.name"
          class="action secondary"
          @click="runButton(btn)"
        >
          {{ buttonLabel(btn) }}
        </button>
        <button :disabled="saving" @click="save">{{ saving ? 'Saving...' : 'Save' }}</button>
        <button @click="reload">Reload</button>
      </div>
    </header>

    <StatusPanel v-if="loading" title="Loading record..." variant="info" />
    <StatusPanel
      v-else-if="error"
      title="Request failed"
      :message="error?.message"
      :trace-id="error?.traceId"
      :error-code="error?.code"
      :hint="error?.hint"
      variant="error"
      :on-retry="reload"
    />

    <section v-else class="card">
      <div v-for="field in fields" :key="field.name" class="field">
        <label class="label">{{ field.label }}</label>
        <template v-if="field.readonly">
          <FieldValue :value="formData[field.name]" :field="field.descriptor" />
        </template>
        <template v-else>
          <input
            v-if="isTextField(field)"
            v-model="formData[field.name]"
            :type="fieldInputType(field)"
          />
          <select v-else-if="field.descriptor?.ttype === 'selection'" v-model="formData[field.name]">
            <option v-for="opt in field.descriptor?.selection || []" :key="opt[0]" :value="opt[0]">
              {{ opt[1] }}
            </option>
          </select>
          <input v-else v-model="formData[field.name]" />
        </template>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createRecord, readRecord, writeRecord } from '../api/data';
import { executeButton } from '../api/executeButton';
import { extractFieldNames, resolveView } from '../app/resolvers/viewResolver';
import FieldValue from '../components/FieldValue.vue';
import StatusPanel from '../components/StatusPanel.vue';
import type { ViewButton, ViewContract } from '@sc/schema';
import { recordTrace, createTraceId } from '../services/trace';
import { useStatus } from '../composables/useStatus';

const route = useRoute();
const router = useRouter();

const { error, clearError, setError } = useStatus();
const loading = ref(false);
const saving = ref(false);
const executing = ref<string | null>(null);

const model = computed(() => String(route.params.model || ''));
const recordId = computed(() => (route.params.id === 'new' ? null : Number(route.params.id)));
const recordIdDisplay = computed(() => (recordId.value ? recordId.value : 'new'));
const title = computed(() => `Form: ${model.value}`);

const viewContract = ref<ViewContract | null>(null);
const fields = ref<
  Array<{ name: string; label: string; descriptor?: ViewContract['fields'][string]; readonly?: boolean }>
>([]);
const formData = reactive<Record<string, unknown>>({});

const headerButtons = computed(() => {
  const raw =
    viewContract.value?.layout?.headerButtons ??
    (viewContract.value as { layout?: { header_buttons?: ViewButton[] } } | null)?.layout?.header_buttons ??
    [];
  return normalizeButtons(raw);
});

function isTextField(field: (typeof fields.value)[number]) {
  const ttype = field.descriptor?.ttype;
  return ['char', 'text', 'float', 'integer', 'date', 'datetime', 'boolean', undefined].includes(ttype as string);
}

function fieldInputType(field: (typeof fields.value)[number]) {
  switch (field.descriptor?.ttype) {
    case 'integer':
    case 'float':
      return 'number';
    case 'date':
      return 'date';
    case 'datetime':
      return 'datetime-local';
    default:
      return 'text';
  }
}

async function load() {
  clearError();
  loading.value = true;

  if (!model.value) {
    setError(new Error('Missing model'), 'Missing model');
    loading.value = false;
    return;
  }

  try {
    const view = await resolveView(model.value, 'form');
    viewContract.value = view;
    const fieldNames = extractFieldNames(view.layout).filter(Boolean);
    const read = recordId.value
      ? await readRecord({
          model: model.value,
          ids: [recordId.value],
          fields: fieldNames.length ? fieldNames : '*',
        })
      : { records: [{}] };

    const record = read.records?.[0] ?? {};
    fields.value = (fieldNames.length ? fieldNames : Object.keys(record)).map((name) => ({
      name,
      label: view.fields?.[name]?.string ?? name,
      descriptor: view.fields?.[name],
      readonly: view.fields?.[name]?.readonly,
    }));

    fields.value.forEach((field) => {
      formData[field.name] = record[field.name] ?? '';
    });
    recordTrace({
      ts: Date.now(),
      trace_id: createTraceId(),
      intent: 'api.data.read',
      status: 'ok',
      model: model.value,
      view_mode: 'form',
      params_digest: JSON.stringify({ id: recordId.value }),
    });
  } catch (err) {
    setError(err, 'failed to load record');
  } finally {
    loading.value = false;
  }
}

async function save() {
  if (!model.value) {
    return;
  }
  saving.value = true;
  try {
    if (recordId.value) {
      await writeRecord({ model: model.value, ids: [recordId.value], vals: formData });
      recordTrace({
        ts: Date.now(),
        trace_id: createTraceId(),
        intent: 'api.data.write',
        status: 'ok',
        model: model.value,
        view_mode: 'form',
        params_digest: JSON.stringify({ id: recordId.value }),
      });
    } else {
      const created = await createRecord({ model: model.value, vals: formData });
      if (created.id) {
        recordTrace({
          ts: Date.now(),
          trace_id: createTraceId(),
          intent: 'api.data.create',
          status: 'ok',
          model: model.value,
          view_mode: 'form',
          params_digest: JSON.stringify({ id: created.id }),
        });
        router.replace(`/r/${model.value}/${created.id}?view_mode=form`);
      }
    }
  } catch (err) {
    setError(err, 'failed to save');
  } finally {
    saving.value = false;
  }
}

function normalizeButtons(raw: unknown): ViewButton[] {
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw.filter((btn) => btn && typeof btn === 'object') as ViewButton[];
}

function buttonLabel(btn: ViewButton) {
  return btn.string || btn.name || 'Action';
}

function getQueryNumber(key: string) {
  const val = route.query[key];
  if (Array.isArray(val)) {
    const n = Number(val[0]);
    return Number.isNaN(n) ? undefined : n;
  }
  if (typeof val === 'string') {
    const n = Number(val);
    return Number.isNaN(n) ? undefined : n;
  }
  return undefined;
}

async function runButton(btn: ViewButton) {
  if (!model.value || !recordId.value || !btn.name) {
    return;
  }
  executing.value = btn.name;
  try {
    const response = await executeButton({
      model: model.value,
      res_id: recordId.value,
      button: { name: btn.name, type: btn.type ?? 'object' },
      context: btn.context ?? {},
      meta: {
        menu_id: getQueryNumber('menu_id'),
        action_id: getQueryNumber('action_id'),
        view_id: viewContract.value?.view_id,
      },
    });
    recordTrace({
      ts: Date.now(),
      trace_id: createTraceId(),
      intent: 'execute_button',
      status: 'ok',
      model: model.value,
      view_mode: 'form',
      params_digest: JSON.stringify({ id: recordId.value, name: btn.name }),
    });
    if (response?.result?.type === 'refresh') {
      await load();
    }
  } catch (err) {
    setError(err, 'failed to execute button');
  } finally {
    executing.value = null;
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
  background: #f1f5f9;
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

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 12px;
}

.field {
  display: grid;
  gap: 6px;
}

.label {
  font-weight: 600;
  color: #334155;
}

input,
select {
  padding: 10px 12px;
  border: 1px solid #cbd5f5;
  border-radius: 8px;
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
