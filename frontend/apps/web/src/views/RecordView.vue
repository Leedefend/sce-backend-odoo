<template>
  <main class="page">
    <header class="header">
      <div>
        <h1>{{ title }}</h1>
        <p class="meta">Model: {{ model }} · ID: {{ recordId }}</p>
      </div>
      <button @click="reload">Reload</button>
    </header>

    <section class="card" v-if="fields.length">
      <div class="field" v-for="field in fields" :key="field.name">
        <span class="label">{{ field.label }}</span>
        <span class="value">{{ formatValue(field.value) }}</span>
      </div>
    </section>

    <p v-else class="empty">No fields loaded.</p>
    <p v-if="error" class="error">{{ error }}</p>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { intentRequest } from '../api/intents';
import { readRecord } from '../api/data';
import type { ViewContract, FormField, LoadViewRequest } from '@sc/schema';

const route = useRoute();
const error = ref('');
const fields = ref<Array<{ name: string; label: string; value: unknown }>>([]);

const model = computed(() => String(route.params.model || ''));
const recordId = computed(() => Number(route.params.id));
const title = computed(() => `Record ${recordId.value}`);

function extractFieldNames(layout: ViewContract['layout']) {
  const names: string[] = [];
  const pushField = (field?: FormField) => {
    if (field?.name && !names.includes(field.name)) {
      names.push(field.name);
    }
  };

  layout.groups?.forEach((group) => {
    group.fields?.forEach((field) => pushField(field));
    group.sub_groups?.forEach((sub) => sub.fields?.forEach((field) => pushField(field)));
  });

  layout.notebooks?.forEach((notebook) => {
    notebook.pages?.forEach((page) => {
      page.groups?.forEach((group) => {
        group.fields?.forEach((field) => pushField(field));
      });
    });
  });

  if (layout.titleField) {
    pushField({ name: layout.titleField });
  }

  return names;
}

async function load() {
  error.value = '';
  fields.value = [];

  if (!model.value || !recordId.value) {
    error.value = 'Missing model or id';
    return;
  }

  try {
    const view = await intentRequest<ViewContract>({
      intent: 'load_view',
      params: { model: model.value, view_type: 'form' } as Record<string, unknown>,
    });

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
    }));
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'failed to load record';
  }
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
