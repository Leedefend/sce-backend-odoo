<template>
  <main class="page">
    <header class="header">
      <div>
        <h1>{{ title }}</h1>
        <p class="meta">Model: {{ model }} · ID: {{ recordId }}</p>
      </div>
      <button @click="reload">Reload</button>
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

    <section v-else-if="fields.length" class="card">
      <div v-for="field in fields" :key="field.name" class="field">
        <span class="label">{{ field.label }}</span>
        <span class="value"><FieldValue :value="field.value" :field="field.descriptor" /></span>
      </div>
    </section>

    <p v-else class="empty">No fields loaded.</p>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { ApiError } from '../api/client';
import { readRecord } from '../api/data';
import { extractFieldNames, resolveView } from '../app/resolvers/viewResolver';
import type { ViewContract } from '@sc/schema';
import FieldValue from '../components/FieldValue.vue';
import StatusPanel from '../components/StatusPanel.vue';

const route = useRoute();
const error = ref('');
const traceId = ref('');
const loading = ref(false);
const fields = ref<Array<{ name: string; label: string; value: unknown; descriptor?: ViewContract['fields'][string] }>>([]);

const model = computed(() => String(route.params.model || ''));
const recordId = computed(() => Number(route.params.id));
const title = computed(() => `Record ${recordId.value}`);

async function load() {
  error.value = '';
  traceId.value = '';
  fields.value = [];
  loading.value = true;

  if (!model.value || !recordId.value) {
    error.value = 'Missing model or id';
    loading.value = false;
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
