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
          :disabled="!recordId || saving || loading || executing === btn.name || buttonState(btn).state !== 'enabled'"
          class="action secondary"
          :title="buttonTooltip(btn)"
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
    <StatusPanel
      v-else-if="renderBlocked"
      title="View node unsupported"
      message="Layout nodes are present but renderer support is incomplete."
      error-code="VIEW_NODE_UNSUPPORTED"
      variant="error"
      :on-retry="reload"
    />

    <section v-else class="card">
      <ViewLayoutRenderer
        v-if="renderMode === 'layout_tree'"
        :layout="viewContract?.layout || {}"
        :fields="viewContract?.fields"
        :record="formData"
        :editing="true"
        :draft-name="draftName"
        :edit-mode="'all'"
        @update:field="handleFieldUpdate"
      />
      <div v-else>
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
      </div>
    </section>
    <DevContextPanel :visible="showHud" title="Form Context" :entries="hudEntries" />
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
import ViewLayoutRenderer from '../components/view/ViewLayoutRenderer.vue';
import type { ViewButton, ViewContract } from '@sc/schema';
import { recordTrace, createTraceId } from '../services/trace';
import { useStatus } from '../composables/useStatus';
import DevContextPanel from '../components/DevContextPanel.vue';
import { isHudEnabled } from '../config/debug';
import { useSessionStore } from '../stores/session';
import { checkCapabilities, getRequiredCapabilities } from '../app/capability';
import { ErrorCodes } from '../app/error_codes';

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
const draftName = ref('');
const layoutStats = ref({ field: 0, group: 0, notebook: 0, page: 0, unsupported: 0 });

const headerButtons = computed(() => {
  const raw =
    viewContract.value?.layout?.headerButtons ??
    (viewContract.value as { layout?: { header_buttons?: ViewButton[] } } | null)?.layout?.header_buttons ??
    [];
  return normalizeButtons(raw);
});
const renderMode = computed(() => (viewContract.value?.layout ? 'layout_tree' : 'fallback_fields'));
const supportedNodes = ['field', 'group', 'notebook', 'page', 'headerButtons', 'statButtons', 'ribbon', 'chatter'];
const missingNodes = computed(() => {
  const layout = viewContract.value?.layout;
  if (!layout) return [];
  const present = new Set<string>();
  if (Array.isArray(layout.groups) && layout.groups.length) present.add('group');
  const groupFields = Array.isArray(layout.groups)
    ? layout.groups.some((group: any) => (Array.isArray(group.fields) && group.fields.length) || (Array.isArray(group.sub_groups) && group.sub_groups.length))
    : false;
  if (groupFields) present.add('field');
  if (Array.isArray(layout.notebooks) && layout.notebooks.length) present.add('notebook');
  const hasPages = Array.isArray(layout.notebooks)
    ? layout.notebooks.some((notebook: any) => Array.isArray(notebook.pages) && notebook.pages.length)
    : false;
  if (hasPages) present.add('page');
  if (Array.isArray(layout.headerButtons) && layout.headerButtons.length) present.add('headerButtons');
  if (Array.isArray(layout.statButtons) && layout.statButtons.length) present.add('statButtons');
  if (layout.ribbon) present.add('ribbon');
  if (layout.chatter) present.add('chatter');
  return Array.from(present).filter((node) => !supportedNodes.includes(node));
});
const renderBlocked = computed(() => showHud.value && renderMode.value === 'layout_tree' && missingNodes.value.length > 0);
const showHud = computed(() => isHudEnabled(route));
const session = useSessionStore();
const userGroups = computed(() => session.user?.groups_xmlids ?? []);
const hudEntries = computed(() => [
  { label: 'model', value: model.value },
  { label: 'record_id', value: recordIdDisplay.value },
  { label: 'render_mode', value: renderMode.value },
  { label: 'layout_present', value: Boolean(viewContract.value?.layout) },
  { label: 'layout_nodes', value: JSON.stringify(layoutStats.value) },
  { label: 'unsupported_nodes', value: missingNodes.value.join(',') || '-' },
  { label: 'coverage_supported', value: supportedNodes.join(',') },
]);

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
  layoutStats.value = { field: 0, group: 0, notebook: 0, page: 0, unsupported: 0 };

  if (!model.value) {
    setError(new Error('Missing model'), 'Missing model');
    loading.value = false;
    return;
  }

  try {
    const view = await resolveView(model.value, 'form');
    viewContract.value = view;
    if (view.layout) {
      layoutStats.value = analyzeLayout(view.layout);
    }
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
    draftName.value = String(record?.name ?? '');
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

function buttonState(btn: ViewButton) {
  const requiredCaps = getRequiredCapabilities(btn);
  const capCheck = checkCapabilities(requiredCaps, session.capabilities);
  if (!capCheck.ok) {
    return { state: 'disabled_capability', missing: capCheck.missing };
  }
  const groups = Array.isArray(btn.groups) ? btn.groups : [];
  if (groups.length && !groups.some((g) => userGroups.value.includes(g))) {
    return { state: 'disabled_permission', missing: [] };
  }
  return { state: 'enabled', missing: [] };
}

function buttonTooltip(btn: ViewButton) {
  const state = buttonState(btn);
  if (state.state === 'disabled_capability') {
    return `Missing capabilities: ${state.missing.join(', ')}`;
  }
  if (state.state === 'disabled_permission') {
    return 'Permission required';
  }
  return '';
}

function handleFieldUpdate(payload: { name: string; value: string }) {
  if (!payload.name) {
    return;
  }
  formData[payload.name] = payload.value;
  if (payload.name === 'name') {
    draftName.value = payload.value;
  }
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
  const state = buttonState(btn);
  if (state.state === 'disabled_capability') {
    await router.push({ name: 'workbench', query: { reason: ErrorCodes.CAPABILITY_MISSING } });
    return;
  }
  if (state.state === 'disabled_permission') {
    error.value = { message: 'Permission denied', code: 403, hint: 'Check access rights.' };
    return;
  }
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

function analyzeLayout(layout: ViewContract['layout']) {
  const stats = { field: 0, group: 0, notebook: 0, page: 0, unsupported: 0 };
  const countGroup = (group: any) => {
    stats.group += 1;
    const fields = Array.isArray(group.fields) ? group.fields : [];
    stats.field += fields.length;
    const subGroups = Array.isArray(group.sub_groups) ? group.sub_groups : [];
    subGroups.forEach((sub) => countGroup(sub));
  };
  const groups = Array.isArray(layout.groups) ? layout.groups : [];
  groups.forEach((group) => countGroup(group));
  const notebooks = Array.isArray(layout.notebooks) ? layout.notebooks : [];
  stats.notebook += notebooks.length;
  notebooks.forEach((notebook) => {
    const pages = Array.isArray(notebook.pages) ? notebook.pages : [];
    stats.page += pages.length;
    pages.forEach((page) => {
      const pageGroups = Array.isArray(page.groups) ? page.groups : [];
      pageGroups.forEach((group) => countGroup(group));
    });
  });
  const unsupported = [
    Array.isArray(layout.headerButtons) ? layout.headerButtons.length : 0,
    Array.isArray(layout.statButtons) ? layout.statButtons.length : 0,
    layout.ribbon ? 1 : 0,
    layout.chatter ? 1 : 0,
  ].reduce((sum, value) => sum + value, 0);
  stats.unsupported = unsupported;
  return stats;
}
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
