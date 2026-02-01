<template>
  <main class="page">
    <header class="header">
      <div>
        <h1>{{ title }}</h1>
        <p class="meta">Model: {{ model }} · ID: {{ recordIdDisplay }}</p>
      </div>
      <div class="actions">
        <button @click="save" :disabled="saving">{{ saving ? 'Saving...' : 'Save' }}</button>
        <button @click="reload">Reload</button>
      </div>
    </header>

    <StatusPanel v-if="loading" title="Loading record..." variant="info" />
    <StatusPanel
      v-else-if="error"
      title="Request failed"
      :message="error"
      :trace-id="traceId"
      variant="error"
      :on-retry="reload"
    />

    <section v-else class="card">
      <div class="field" v-for="field in fields" :key="field.name">
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
import { ApiError } from '../api/client';
import { createRecord, readRecord, writeRecord } from '../api/data';
import { extractFieldNames, resolveView } from '../app/resolvers/viewResolver';
import FieldValue from '../components/FieldValue.vue';
import StatusPanel from '../components/StatusPanel.vue';
import type { ViewContract } from '@sc/schema';
import { recordTrace, createTraceId } from '../services/trace';

const route = useRoute();
const router = useRouter();

const error = ref('');
const traceId = ref('');
const loading = ref(false);
const saving = ref(false);

const model = computed(() => String(route.params.model || ''));
const recordId = computed(() => (route.params.id === 'new' ? null : Number(route.params.id)));
const recordIdDisplay = computed(() => (recordId.value ? recordId.value : 'new'));
const title = computed(() => `Form: ${model.value}`);

const fields = ref<
  Array<{ name: string; label: string; descriptor?: ViewContract['fields'][string]; readonly?: boolean }>
>([]);
const formData = reactive<Record<string, any>>({});

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
  error.value = '';
  traceId.value = '';
  loading.value = true;

  if (!model.value) {
    error.value = 'Missing model';
    loading.value = false;
    return;
  }

  try {
    const view = await resolveView(model.value, 'form');
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
    if (err instanceof ApiError) {
      traceId.value = err.traceId ?? '';
      error.value = err.message;
    } else {
      error.value = err instanceof Error ? err.message : 'failed to load record';
    }
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
        router.replace(`/m/${model.value}/${created.id}?view_mode=form`);
      }
    }
  } catch (err) {
    if (err instanceof ApiError) {
      traceId.value = err.traceId ?? '';
      error.value = err.message;
    } else {
      error.value = err instanceof Error ? err.message : 'failed to save';
    }
  } finally {
    saving.value = false;
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
