<template>
  <section class="page">
    <header class="header">
      <div>
        <h2>{{ title }}</h2>
        <p class="meta">{{ subtitle }}</p>
      </div>
      <div class="actions">
        <button
          v-for="btn in headerButtons"
          :key="btn.name ?? btn.string"
          :disabled="status !== 'ok' || !recordId || executing === btn.name || buttonState(btn).state !== 'enabled'"
          class="ghost"
          :title="buttonTooltip(btn)"
          @click="runHeaderButton(btn)"
        >
          {{ buttonLabel(btn) }}
        </button>
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
      :message="error?.code ? `code=${error.code} · ${error.message}` : error?.message"
      :trace-id="error?.traceId || traceId"
      :error-code="error?.code"
      :hint="error?.hint"
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
    <StatusPanel
      v-else-if="renderBlocked"
      title="View node unsupported"
      message="Layout nodes are present but renderer support is incomplete."
      error-code="VIEW_NODE_UNSUPPORTED"
      variant="error"
      :on-retry="reload"
    />

    <section v-else class="card" :class="{ editing: status === 'editing' }">
      <div v-if="status === 'ok' && lastAction === 'save'" class="banner success">
        Saved. Changes have been applied.
      </div>
      <div v-if="ribbon" class="ribbon">{{ ribbon.title || 'Ribbon' }}</div>
      <div v-if="statButtons.length" class="stat-buttons">
        <button
          v-for="btn in statButtons"
          :key="btn.name ?? btn.string"
          class="stat-button"
          :disabled="!recordId || executing === btn.name || buttonState(btn).state !== 'enabled'"
          :title="buttonTooltip(btn)"
          @click="runStatButton(btn)"
        >
          <span class="stat-label">{{ buttonLabel(btn) }}</span>
          <span v-if="btn.field" class="stat-value">{{ recordData?.[btn.field] ?? '-' }}</span>
        </button>
      </div>
      <ViewLayoutRenderer
        v-if="renderMode === 'layout_tree'"
        :layout="viewContract?.layout || {}"
        :fields="viewContract?.fields"
        :record="recordData"
        :parent-id="recordId"
        :editing="status === 'editing'"
        :draft-name="draftName"
        :edit-mode="status === 'editing' ? 'name' : 'none'"
        @update:field="handleFieldUpdate"
      />
      <div v-else>
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
      </div>
      <section v-if="hasChatter" class="chatter">
        <h3>Chatter</h3>
        <p v-if="chatterError" class="meta">{{ chatterError }}</p>
        <div v-else class="chatter-grid">
          <div class="chatter-block">
            <h4>Messages</h4>
            <p v-if="!chatterMessages.length" class="meta">No messages yet.</p>
            <ul v-else class="chatter-list">
              <li v-for="msg in chatterMessages" :key="String(msg.id)" class="chatter-item">
                <div class="chatter-title">{{ msg.subject || 'Message' }}</div>
                <div class="chatter-meta">{{ msg.author_id?.[1] || 'Unknown' }} · {{ msg.date || '-' }}</div>
                <div class="chatter-body">{{ stripHtml(String(msg.body || '')) }}</div>
              </li>
            </ul>
            <div class="chatter-compose">
              <textarea v-model="chatterDraft" placeholder="Write a message..." />
              <button :disabled="chatterPosting || !chatterDraft.trim()" @click="sendChatter">
                {{ chatterPosting ? 'Posting...' : 'Post message' }}
              </button>
            </div>
          </div>
          <div class="chatter-block">
            <h4>Attachments</h4>
            <p v-if="!chatterAttachments.length" class="meta">No attachments yet.</p>
            <div class="chatter-upload">
              <input type="file" @change="onAttachmentSelected" />
              <span v-if="chatterUploading" class="meta">Uploading…</span>
              <span v-if="chatterUploadError" class="meta">{{ chatterUploadError }}</span>
            </div>
            <ul v-if="chatterAttachments.length" class="chatter-list">
              <li v-for="att in chatterAttachments" :key="String(att.id)" class="chatter-item">
                <div class="chatter-title">{{ att.name || 'Attachment' }}</div>
                <div class="chatter-meta">{{ att.mimetype || 'unknown' }} · {{ att.file_size || '-' }}</div>
                <button class="ghost" type="button" @click="downloadAttachment(att)">Download</button>
              </li>
            </ul>
          </div>
        </div>
      </section>
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
import { listRecords, readRecordRaw, writeRecordV6Raw } from '../api/data';
import { executeButton } from '../api/executeButton';
import { postChatterMessage } from '../api/chatter';
import { downloadFile, fileToBase64, uploadFile } from '../api/files';
import { extractFieldNames, resolveView } from '../app/resolvers/viewResolver';
import { deriveRecordStatus } from '../app/view_state';
import type { ViewButton, ViewContract } from '@sc/schema';
import FieldValue from '../components/FieldValue.vue';
import ViewLayoutRenderer from '../components/view/ViewLayoutRenderer.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import StatusPanel from '../components/StatusPanel.vue';
import { isHudEnabled } from '../config/debug';
import { useStatus } from '../composables/useStatus';
import { useSessionStore } from '../stores/session';
import { capabilityTooltip, evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { ErrorCodes } from '../app/error_codes';

const route = useRoute();
const router = useRouter();
const traceId = ref('');
const lastTraceId = ref('');
const { error, clearError, setError } = useStatus();
const status = ref<'idle' | 'loading' | 'ok' | 'empty' | 'error' | 'editing' | 'saving'>('idle');
const fields = ref<Array<{ name: string; label: string; value: unknown; descriptor?: ViewContract['fields'][string] }>>([]);
const viewContract = ref<ViewContract | null>(null);
const recordData = ref<Record<string, unknown> | null>(null);
const chatterMessages = ref<Array<Record<string, unknown>>>([]);
const chatterAttachments = ref<Array<Record<string, unknown>>>([]);
const chatterError = ref('');
const chatterDraft = ref('');
const chatterPosting = ref(false);
const chatterUploading = ref(false);
const chatterUploadError = ref('');
const draftName = ref('');
const lastIntent = ref('');
const lastWriteMode = ref('');
const lastLatencyMs = ref<number | null>(null);
const lastAction = ref<'save' | 'load' | 'execute' | ''>('');
const executing = ref<string | null>(null);
const layoutStats = ref({ field: 0, group: 0, notebook: 0, page: 0, unsupported: 0 });

const model = computed(() => String(route.params.model || ''));
const recordId = computed(() => Number(route.params.id));
const recordTitle = ref<string | null>(null);
const title = computed(() => recordTitle.value || `Record ${recordId.value}`);
const subtitle = computed(() => (status.value === 'editing' ? 'Editing name' : 'Record details'));
const canEdit = computed(() => model.value === 'project.project');
const showHud = computed(() => isHudEnabled(route));
const session = useSessionStore();
const userGroups = computed(() => session.user?.groups_xmlids ?? []);
const statusLabel = computed(() => {
  if (status.value === 'editing') return 'Editing';
  if (status.value === 'saving') return 'Saving';
  if (status.value === 'loading') return 'Loading';
  if (status.value === 'error') return 'Error';
  if (status.value === 'empty') return 'Empty';
  return 'Ready';
});
const statusTone = computed(() => {
  if (status.value === 'error') return 'danger';
  if (status.value === 'editing' || status.value === 'saving') return 'warn';
  return 'ok';
});
const renderMode = computed(() => (viewContract.value?.layout ? 'layout_tree' : 'fallback_fields'));
const headerButtons = computed(() => normalizeButtons(viewContract.value?.layout?.headerButtons ?? []));
const statButtons = computed(() => normalizeButtons(viewContract.value?.layout?.statButtons ?? []));
const ribbon = computed(() => {
  const value = viewContract.value?.layout?.ribbon;
  if (!value || typeof value !== 'object') return null;
  const invisible = (value as { invisible?: { type?: string; value?: boolean } }).invisible;
  if (typeof invisible === 'object' && invisible?.type === 'boolean' && invisible.value) {
    return null;
  }
  return value as { title?: string };
});
const hasChatter = computed(() => Boolean(viewContract.value?.layout?.chatter));
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
const hudEntries = computed(() => [
  { label: 'model', value: model.value },
  { label: 'record_id', value: recordId.value },
  { label: 'status', value: status.value },
  { label: 'render_mode', value: renderMode.value },
  { label: 'layout_present', value: Boolean(viewContract.value?.layout) },
  { label: 'layout_nodes', value: JSON.stringify(layoutStats.value) },
  { label: 'unsupported_nodes', value: missingNodes.value.join(',') || '-' },
  { label: 'coverage_supported', value: supportedNodes.join(',') },
  { label: 'last_intent', value: lastIntent.value || '-' },
  { label: 'write_mode', value: lastWriteMode.value || '-' },
  { label: 'trace_id', value: traceId.value || lastTraceId.value || '-' },
  { label: 'latency_ms', value: lastLatencyMs.value ?? '-' },
  { label: 'route', value: route.fullPath },
]);

function buttonState(btn: ViewButton) {
  return evaluateCapabilityPolicy({
    source: btn,
    available: session.capabilities,
    groups: Array.isArray(btn.groups) ? btn.groups : [],
    userGroups: userGroups.value,
  });
}

function buttonTooltip(btn: ViewButton) {
  return capabilityTooltip(buttonState(btn));
}

function stripHtml(input: string) {
  return input.replace(/<[^>]*>/g, '').trim();
}

async function load() {
  clearError();
  traceId.value = '';
  fields.value = [];
  viewContract.value = null;
  recordData.value = null;
  chatterMessages.value = [];
  chatterAttachments.value = [];
  chatterError.value = '';
  chatterUploadError.value = '';
  layoutStats.value = { field: 0, group: 0, notebook: 0, page: 0, unsupported: 0 };
  status.value = 'loading';
  lastIntent.value = 'api.data.read';
  lastWriteMode.value = 'read';
  lastAction.value = 'load';
  const startedAt = Date.now();

  if (!model.value || !recordId.value) {
    setError(new Error('Missing model or id'), 'Missing model or id');
    status.value = deriveRecordStatus({ error: error.value?.message || '', fieldsLength: 0 });
    return;
  }

  try {
    const view = await resolveView(model.value, 'form');
    viewContract.value = view || null;
    const layout = view?.layout;
    if (!layout) {
      setError(new Error('Missing view layout'), 'Missing view layout');
      status.value = 'empty';
      lastLatencyMs.value = Date.now() - startedAt;
      return;
    }
    layoutStats.value = analyzeLayout(layout);

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
    recordData.value = record as Record<string, unknown>;
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

    if (hasChatter.value) {
      await loadChatter();
    }
  } catch (err) {
    setError(err, 'failed to load record');
    traceId.value = error.value?.traceId || '';
    lastTraceId.value = error.value?.traceId || '';
    status.value = deriveRecordStatus({ error: error.value?.message || '', fieldsLength: 0 });
    lastLatencyMs.value = Date.now() - startedAt;
  }
}

async function loadChatter() {
  chatterError.value = '';
  try {
    const [messages, attachments] = await Promise.all([
      listRecords({
        model: 'mail.message',
        fields: ['id', 'author_id', 'date', 'body', 'subject'],
        domain: [
          ['res_id', '=', recordId.value],
          ['model', '=', model.value],
        ],
        order: 'date desc',
        limit: 20,
      }),
      listRecords({
        model: 'ir.attachment',
        fields: ['id', 'name', 'mimetype', 'file_size'],
        domain: [
          ['res_id', '=', recordId.value],
          ['res_model', '=', model.value],
        ],
        order: 'id desc',
        limit: 20,
      }),
    ]);
    chatterMessages.value = messages.records ?? [];
    chatterAttachments.value = attachments.records ?? [];
  } catch (err) {
    chatterError.value = err instanceof Error ? err.message : 'Failed to load chatter';
  }
}

async function sendChatter() {
  if (!model.value || !recordId.value || !chatterDraft.value.trim()) {
    return;
  }
  chatterPosting.value = true;
  try {
    await postChatterMessage({
      model: model.value,
      res_id: recordId.value,
      body: chatterDraft.value.trim(),
    });
    chatterDraft.value = '';
    await loadChatter();
  } catch (err) {
    chatterError.value = err instanceof Error ? err.message : 'Failed to post chatter message';
  } finally {
    chatterPosting.value = false;
  }
}

async function onAttachmentSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file || !model.value || !recordId.value) {
    return;
  }
  chatterUploading.value = true;
  chatterUploadError.value = '';
  try {
    const { data, mimetype } = await fileToBase64(file);
    await uploadFile({
      model: model.value,
      res_id: recordId.value,
      name: file.name,
      mimetype,
      data,
    });
    await loadChatter();
  } catch (err) {
    chatterUploadError.value = err instanceof Error ? err.message : 'Failed to upload file';
  } finally {
    chatterUploading.value = false;
    input.value = '';
  }
}

async function downloadAttachment(att: { id?: number; name?: string; mimetype?: string }) {
  if (!att?.id) return;
  try {
    const payload = await downloadFile({ id: Number(att.id) });
    const binary = atob(payload.datas || '');
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: payload.mimetype || att.mimetype || 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = payload.name || att.name || 'download';
    link.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    chatterUploadError.value = err instanceof Error ? err.message : 'Failed to download file';
  }
}

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

function reload() {
  load();
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

function handleFieldUpdate(payload: { name: string; value: string }) {
  if (payload.name === 'name') {
    draftName.value = payload.value;
  }
}

async function runHeaderButton(btn: ViewButton) {
  const state = buttonState(btn);
  if (state.state === 'disabled_capability') {
    await router.push({ name: 'workbench', query: { reason: ErrorCodes.CAPABILITY_MISSING } });
    return;
  }
  if (state.state === 'disabled_permission') {
    error.value = { message: 'Permission denied', code: 403, hint: 'Check access rights.' };
    status.value = 'error';
    return;
  }
  if (!model.value || !recordId.value || !btn.name) {
    return;
  }
  lastIntent.value = 'execute_button';
  lastWriteMode.value = 'execute';
  lastAction.value = 'execute';
  const startedAt = Date.now();
  executing.value = btn.name;
  try {
    const response = await executeButton({
      model: model.value,
      res_id: recordId.value,
      button: { name: btn.name, type: btn.type ?? 'object' },
      context: btn.context ?? {},
      meta: { view_id: viewContract.value?.view_id },
    });
    lastLatencyMs.value = Date.now() - startedAt;
    if (response?.effect) {
      await applyButtonEffect(response.effect);
    } else if (response?.result?.type === 'refresh') {
      await load();
    } else if (response?.result?.action_id) {
      await router.push({ name: 'action', params: { actionId: response.result.action_id } });
    }
  } catch (err) {
    setError(err, 'failed to execute button');
    status.value = 'error';
    lastLatencyMs.value = Date.now() - startedAt;
  } finally {
    executing.value = null;
  }
}

async function runStatButton(btn: ViewButton) {
  await runHeaderButton(btn);
}

async function applyButtonEffect(effect: { type: string; target?: Record<string, unknown>; message?: string }) {
  if (!effect || typeof effect !== 'object') {
    return;
  }
  if (effect.type === 'reload_record') {
    await load();
    return;
  }
  if (effect.type === 'reload_action') {
    await load();
    return;
  }
  if (effect.type === 'navigate' && effect.target) {
    const target = effect.target as { kind?: string; model?: string; id?: number; action_id?: number; url?: string };
    if (target.kind === 'record' && target.model && target.id) {
      await router.push({ name: 'record', params: { model: target.model, id: target.id } });
      return;
    }
    if (target.kind === 'action' && target.action_id) {
      await router.push({ name: 'action', params: { actionId: target.action_id } });
      return;
    }
    if (target.kind === 'url' && target.url) {
      window.open(target.url, '_blank');
    }
    return;
  }
  if (effect.type === 'toast' && effect.message) {
    // eslint-disable-next-line no-console
    console.info(`[toast] ${effect.message}`);
  }
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
  clearError();
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
    setError(err, 'failed to save record');
    traceId.value = error.value?.traceId || '';
    lastTraceId.value = error.value?.traceId || '';
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

.ribbon {
  align-self: start;
  padding: 6px 12px;
  border-radius: 999px;
  background: #fee2e2;
  color: #991b1b;
  font-size: 12px;
  font-weight: 600;
  width: fit-content;
}

.stat-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.stat-button {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: #f8fafc;
  color: #0f172a;
  cursor: pointer;
}

.stat-label {
  font-weight: 600;
}

.stat-value {
  font-size: 18px;
}

.chatter {
  margin-top: 16px;
  padding: 16px;
  border-radius: 12px;
  border: 1px dashed rgba(148, 163, 184, 0.5);
  background: #f8fafc;
}

.chatter-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.chatter-block {
  display: grid;
  gap: 8px;
}

.chatter-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 8px;
}

.chatter-item {
  padding: 10px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: #fff;
  display: grid;
  gap: 4px;
}

.chatter-title {
  font-weight: 600;
}

.chatter-meta {
  font-size: 12px;
  color: #64748b;
}

.chatter-body {
  font-size: 13px;
  color: #1f2937;
}

.chatter-compose {
  display: grid;
  gap: 8px;
  margin-top: 8px;
}

.chatter-compose textarea {
  min-height: 80px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  padding: 10px;
  font-size: 13px;
}
.chatter-upload {
  display: grid;
  gap: 6px;
  margin-bottom: 10px;
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
