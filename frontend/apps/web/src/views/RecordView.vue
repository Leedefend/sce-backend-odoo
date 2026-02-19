<template>
  <section class="page">
    <header class="header">
      <div>
        <h2>{{ title }}</h2>
        <p class="meta">{{ subtitle }}</p>
        <p v-if="actionFeedback" class="meta action-feedback" :class="{ error: !actionFeedback.success }">
          {{ actionFeedback.message }} <span class="code">({{ actionFeedback.reasonCode }})</span>
        </p>
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
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="error?.traceId || traceId"
      :error-code="error?.code"
      :reason-code="error?.reasonCode"
      :error-category="error?.errorCategory"
      :retryable="error?.retryable"
      :hint="errorCopy.hint"
      :suggested-action="error?.suggestedAction"
      variant="error"
      :on-retry="reload"
      :on-suggested-action="handleSuggestedAction"
    />
    <StatusPanel
      v-else-if="status === 'empty'"
      :title="emptyCopy.title"
      :message="emptyCopy.message"
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
      <div v-if="editTx.state === 'saved'" class="banner success">
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
        :record="renderRecord"
        :parent-id="recordId"
        :editing="status === 'editing'"
        :draft-name="draftName"
        :edit-mode="status === 'editing' ? 'all' : 'none'"
        @update:field="handleFieldUpdate"
      />
      <div v-else>
        <div v-for="field in fields" :key="field.name" class="field">
          <span class="label">{{ field.label }}</span>
          <span class="value">
            <template v-if="status === 'editing' && canEditField(field.name)">
              <select
                v-if="isSelectionField(field.name)"
                :value="String(resolveDraftValue(field.name))"
                class="input"
                @change="updateDraftField(field.name, ($event.target as HTMLSelectElement).value)"
              >
                <option v-for="opt in selectionOptions(field.name)" :key="opt[0]" :value="opt[0]">
                  {{ opt[1] }}
                </option>
              </select>
              <input
                v-else
                :value="String(resolveDraftValue(field.name) ?? '')"
                class="input"
                :type="fieldInputType(field.name)"
                @input="updateDraftField(field.name, ($event.target as HTMLInputElement).value)"
              />
            </template>
            <FieldValue v-else :value="field.value" :field="field.descriptor" />
          </span>
        </div>
      </div>
      <section v-if="hasChatter" class="chatter">
        <h3>协作时间线</h3>
        <p v-if="chatterError" class="meta">{{ chatterError }}</p>
        <div class="chatter-compose">
          <textarea v-model="chatterDraft" placeholder="输入评论，支持 @同事 ..." />
          <div class="chatter-compose-actions">
            <button :disabled="chatterPosting || !chatterDraft.trim()" @click="sendChatter">
              {{ chatterPosting ? '发布中...' : '发布评论' }}
            </button>
            <input type="file" @change="onAttachmentSelected" />
            <span v-if="chatterUploading" class="meta">上传中…</span>
            <span v-if="chatterUploadError" class="meta">{{ chatterUploadError }}</span>
          </div>
        </div>
        <p v-if="!timelineEntries.length" class="meta">暂无协作记录。</p>
        <ul v-else class="timeline-list">
          <li v-for="entry in timelineEntries" :key="entry.key" class="timeline-item">
            <div class="timeline-type" :class="`type-${entry.type}`">{{ entry.typeLabel }}</div>
            <div class="timeline-main">
              <div class="chatter-title">{{ entry.title }}</div>
              <div class="chatter-meta">{{ entry.meta }}</div>
              <div v-if="entry.body" class="chatter-body">{{ entry.body }}</div>
              <button
                v-if="entry.type === 'attachment' && entry.attachment"
                class="ghost"
                type="button"
                @click="downloadAttachment(entry.attachment)"
              >
                Download
              </button>
            </div>
          </li>
        </ul>
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
import { readRecordRaw, writeRecordV6Raw } from '../api/data';
import { ApiError } from '../api/client';
import { executeButton } from '../api/executeButton';
import { fetchChatterTimeline, postChatterMessage, type ChatterTimelineEntry } from '../api/chatter';
import { downloadFile, fileToBase64, uploadFile } from '../api/files';
import { loadActionContractRaw } from '../api/contract';
import { buildRecordRuntimeFromContract } from '../app/contractRecordRuntime';
import { deriveRecordStatus } from '../app/view_state';
import type { ViewButton, ViewContract } from '@sc/schema';
import FieldValue from '../components/FieldValue.vue';
import ViewLayoutRenderer from '../components/view/ViewLayoutRenderer.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import StatusPanel from '../components/StatusPanel.vue';
import { isHudEnabled } from '../config/debug';
import { resolveEmptyCopy, resolveErrorCopy, useStatus } from '../composables/useStatus';
import { useEditTx } from '../composables/useEditTx';
import { useSessionStore } from '../stores/session';
import { capabilityTooltip, evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { ErrorCodes } from '../app/error_codes';
import { parseExecuteResult, semanticButtonLabel } from '../app/action_semantics';
import { pickContractNavQuery } from '../app/navigationContext';
import { resolveActionIdFromContext } from '../app/actionContext';

const route = useRoute();
const router = useRouter();
const traceId = ref('');
const lastTraceId = ref('');
const contractMode = ref('');
const contractWriteAllowed = ref(true);
const { error, clearError, setError } = useStatus();
const status = ref<'idle' | 'loading' | 'ok' | 'empty' | 'error' | 'editing' | 'saving'>('idle');
const fields = ref<Array<{ name: string; label: string; value: unknown; descriptor?: ViewContract['fields'][string] }>>([]);
const viewContract = ref<ViewContract | null>(null);
const recordData = ref<Record<string, unknown> | null>(null);
const timelineEntries = ref<ChatterTimelineEntry[]>([]);
const chatterError = ref('');
const chatterDraft = ref('');
const chatterPosting = ref(false);
const chatterUploading = ref(false);
const chatterUploadError = ref('');
const actionFeedback = ref<{ message: string; reasonCode: string; success: boolean } | null>(null);
const draftName = ref('');
const draftValues = ref<Record<string, unknown>>({});
const lastIntent = ref('');
const lastWriteMode = ref('');
const lastLatencyMs = ref<number | null>(null);
const lastAction = ref<'save' | 'load' | 'execute' | ''>('');
const executing = ref<string | null>(null);
const layoutStats = ref({ field: 0, group: 0, notebook: 0, page: 0, unsupported: 0 });
type LayoutGroupLike = {
  fields?: unknown[];
  sub_groups?: LayoutGroupLike[];
};
type LayoutNotebookLike = {
  pages?: unknown[];
};
const editTx = useEditTx();

const model = computed(() => String(route.params.model || ''));
const recordId = computed(() => Number(route.params.id));
const recordTitle = ref<string | null>(null);
const title = computed(() => recordTitle.value || `Record ${recordId.value}`);
const subtitle = computed(() => (status.value === 'editing' ? 'Editing contract fields' : 'Record details'));
const canEdit = computed(() => contractWriteAllowed.value);
const actionContext = computed(() => {
  const fromQuery = Number(route.query.action_id || 0);
  if (Number.isFinite(fromQuery) && fromQuery > 0) return { id: fromQuery, source: 'query' as const };
  const fromCurrent = Number(session.currentAction?.action_id || 0);
  if (Number.isFinite(fromCurrent) && fromCurrent > 0) {
    const currentModel = String(session.currentAction?.model || '').trim();
    if (!currentModel || currentModel === model.value) {
      return { id: fromCurrent, source: 'current_action' as const };
    }
  }
  const resolved = resolveActionIdFromContext({
    routeQuery: route.query as Record<string, unknown>,
    currentActionId: session.currentAction?.action_id,
    currentActionModel: session.currentAction?.model,
    menuTree: session.menuTree,
    model: model.value,
    preferredMode: 'form',
  });
  if (resolved) return { id: resolved, source: 'menu_tree' as const };
  return { id: null, source: 'none' as const };
});
const actionId = computed(() => actionContext.value.id);
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
const errorCopy = computed(() => resolveErrorCopy(error.value, 'Record load failed'));
const emptyCopy = computed(() => resolveEmptyCopy('record'));
const renderMode = computed(() => (viewContract.value?.layout ? 'layout_tree' : 'fallback_fields'));
const renderRecord = computed(() => {
  if (status.value !== 'editing') return recordData.value;
  return { ...(recordData.value || {}), ...draftValues.value };
});
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
    ? layout.groups.some((group) => {
        const g = group as LayoutGroupLike;
        return (Array.isArray(g.fields) && g.fields.length > 0) || (Array.isArray(g.sub_groups) && g.sub_groups.length > 0);
      })
    : false;
  if (groupFields) present.add('field');
  if (Array.isArray(layout.notebooks) && layout.notebooks.length) present.add('notebook');
  const hasPages = Array.isArray(layout.notebooks)
    ? layout.notebooks.some((notebook) => {
        const n = notebook as LayoutNotebookLike;
        return Array.isArray(n.pages) && n.pages.length > 0;
      })
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
  { label: 'action_source', value: actionContext.value.source },
  { label: 'render_mode', value: renderMode.value },
  { label: 'layout_present', value: Boolean(viewContract.value?.layout) },
  { label: 'layout_nodes', value: JSON.stringify(layoutStats.value) },
  { label: 'unsupported_nodes', value: missingNodes.value.join(',') || '-' },
  { label: 'coverage_supported', value: supportedNodes.join(',') },
  { label: 'last_intent', value: lastIntent.value || '-' },
  { label: 'write_mode', value: lastWriteMode.value || '-' },
  { label: 'trace_id', value: traceId.value || lastTraceId.value || '-' },
  { label: 'contract_mode', value: contractMode.value || '-' },
  { label: 'contract_write', value: contractWriteAllowed.value },
  { label: 'latency_ms', value: lastLatencyMs.value ?? '-' },
  { label: 'route', value: route.fullPath },
]);

function resolveCarryQuery(extra?: Record<string, unknown>) {
  return pickContractNavQuery(route.query as Record<string, unknown>, extra);
}

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

async function load() {
  clearError();
  traceId.value = '';
  fields.value = [];
  viewContract.value = null;
  recordData.value = null;
  draftValues.value = {};
  timelineEntries.value = [];
  chatterError.value = '';
  chatterUploadError.value = '';
  layoutStats.value = { field: 0, group: 0, notebook: 0, page: 0, unsupported: 0 };
  contractMode.value = '';
  contractWriteAllowed.value = true;
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
    if (!actionId.value) {
      throw new Error('missing action_id for contract-driven record view');
    }
    const actionContract = await loadActionContractRaw(actionId.value);
    let view: ViewContract | null = null;
    let contractFieldNames: string[] = [];
    if (actionContract?.data && typeof actionContract.data === 'object') {
      const runtime = buildRecordRuntimeFromContract(actionContract.data);
      view = runtime.view;
      contractFieldNames = runtime.fieldNames;
      contractWriteAllowed.value = runtime.rights.write;
    }
    contractMode.value = String(actionContract?.meta?.contract_mode || '');
    if (!view) {
      throw new Error('missing ui.contract form payload');
    }
    viewContract.value = view || null;
    const layout = view?.layout;
    if (!layout) {
      setError(new Error('Missing view layout'), 'Missing view layout');
      status.value = 'empty';
      lastLatencyMs.value = Date.now() - startedAt;
      return;
    }
    layoutStats.value = analyzeLayout(layout);

    const fieldNames = contractFieldNames.length ? contractFieldNames : Object.keys(view?.fields || {}).filter(Boolean);
    const readFields = fieldNames.length ? [...fieldNames] : ['*'];
    if (readFields.length && readFields[0] !== '*' && !readFields.includes('write_date')) {
      readFields.push('write_date');
    }
    const read = await readRecordRaw({
      model: model.value,
      ids: [recordId.value],
      fields: readFields,
    });

    const record = read?.data?.records?.[0] ?? null;
    if (!record) {
      status.value = 'empty';
      lastLatencyMs.value = Date.now() - startedAt;
      return;
    }
    recordData.value = record as Record<string, unknown>;
    const displayFields = (fieldNames.length ? fieldNames : Object.keys(record as Record<string, unknown>)).filter(
      (name) => name !== 'write_date',
    );
    fields.value = displayFields.map((name) => ({
      name,
      label: view?.fields?.[name]?.string ?? name,
      value: (record as Record<string, unknown>)[name],
      descriptor: view?.fields?.[name],
    }));
    draftValues.value = displayFields.reduce<Record<string, unknown>>((acc, name) => {
      acc[name] = (record as Record<string, unknown>)[name];
      return acc;
    }, {});
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
    const timeline = await fetchChatterTimeline({
      model: model.value,
      res_id: recordId.value,
      limit: 40,
      include_audit: true,
    });
    timelineEntries.value = Array.isArray(timeline.items) ? timeline.items : [];
  } catch (err) {
    chatterError.value = err instanceof Error ? err.message : 'Failed to load chatter';
    timelineEntries.value = [];
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
  type LayoutPageLike = { groups?: LayoutGroupLike[] };
  const countGroup = (group: LayoutGroupLike) => {
    stats.group += 1;
    const fields = Array.isArray(group.fields) ? group.fields : [];
    stats.field += fields.length;
    const subGroups = Array.isArray(group.sub_groups) ? group.sub_groups : ([] as LayoutGroupLike[]);
    subGroups.forEach((sub) => countGroup(sub));
  };
  const groups = Array.isArray(layout.groups) ? layout.groups : [];
  groups.forEach((group) => countGroup(group as LayoutGroupLike));
  const notebooks = Array.isArray(layout.notebooks) ? layout.notebooks : [];
  stats.notebook += notebooks.length;
  notebooks.forEach((notebook) => {
    const nb = notebook as LayoutNotebookLike;
    const pages = Array.isArray(nb.pages) ? (nb.pages as LayoutPageLike[]) : [];
    stats.page += pages.length;
    pages.forEach((page) => {
      const pageGroups = Array.isArray(page.groups) ? page.groups : [];
      pageGroups.forEach((group) => countGroup(group as LayoutGroupLike));
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

function handleSuggestedAction(action: string): boolean {
  if (action !== 'open_record') return false;
  if (!model.value || !recordId.value) return false;
  router
    .push({ name: 'record', params: { model: model.value, id: recordId.value }, query: resolveCarryQuery() })
    .catch(() => {});
  return true;
}

function normalizeButtons(raw: unknown): ViewButton[] {
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw.filter((btn) => btn && typeof btn === 'object') as ViewButton[];
}

function buttonLabel(btn: ViewButton) {
  return semanticButtonLabel(btn);
}

function canEditField(fieldName: string) {
  if (!canEdit.value) return false;
  const descriptor = viewContract.value?.fields?.[fieldName];
  if (!descriptor) return false;
  return !descriptor.readonly;
}

function isSelectionField(fieldName: string) {
  const descriptor = viewContract.value?.fields?.[fieldName];
  const ttype = descriptor?.ttype || descriptor?.type;
  return ttype === 'selection';
}

function selectionOptions(fieldName: string) {
  const descriptor = viewContract.value?.fields?.[fieldName];
  return Array.isArray(descriptor?.selection) ? descriptor.selection : [];
}

function fieldInputType(fieldName: string) {
  const descriptor = viewContract.value?.fields?.[fieldName];
  const ttype = descriptor?.ttype || descriptor?.type;
  switch (ttype) {
    case 'integer':
    case 'float':
    case 'monetary':
      return 'number';
    case 'date':
      return 'date';
    case 'datetime':
      return 'datetime-local';
    default:
      return 'text';
  }
}

function resolveDraftValue(fieldName: string) {
  if (fieldName in draftValues.value) {
    return draftValues.value[fieldName];
  }
  return recordData.value?.[fieldName];
}

function updateDraftField(fieldName: string, value: unknown) {
  draftValues.value = { ...draftValues.value, [fieldName]: value };
  if (fieldName === 'name') {
    draftName.value = String(value ?? '');
  }
}

function handleFieldUpdate(payload: { name: string; value: string }) {
  if (!payload.name) return;
  updateDraftField(payload.name, payload.value);
}

async function runHeaderButton(btn: ViewButton) {
  actionFeedback.value = null;
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
  if (btn.type === 'action_open' || String(btn.name).startsWith('__open__')) {
    const rawAction = String(btn.name).replace('__open__', '');
    const openActionId = Number(rawAction || 0);
    if (Number.isFinite(openActionId) && openActionId > 0) {
      const enriched = btn as ViewButton & {
        buttonContext?: Record<string, unknown>;
        domainRaw?: string;
        actionTarget?: string;
      };
      await router.push({
        name: 'action',
        params: { actionId: openActionId },
        query: resolveCarryQuery({
          action_id: openActionId,
          target: enriched.actionTarget || undefined,
          domain_raw: enriched.domainRaw || undefined,
          context_raw:
            enriched.buttonContext && Object.keys(enriched.buttonContext).length
              ? JSON.stringify(enriched.buttonContext)
              : undefined,
        }),
      });
    }
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
      button: { name: btn.name, type: btn.type === 'server' ? 'server' : btn.type ?? 'object' },
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
    actionFeedback.value = parseExecuteResult(response);
  } catch (err) {
    setError(err, 'failed to execute button');
    status.value = 'error';
    lastLatencyMs.value = Date.now() - startedAt;
    actionFeedback.value = { message: '操作失败', reasonCode: 'EXECUTE_FAILED', success: false };
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
      await router.push({
        name: 'record',
        params: { model: target.model, id: target.id },
        query: resolveCarryQuery(),
      });
      return;
    }
    if (target.kind === 'action' && target.action_id) {
      await router.push({
        name: 'action',
        params: { actionId: target.action_id },
        query: resolveCarryQuery({ action_id: target.action_id }),
      });
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
  draftValues.value = fields.value.reduce<Record<string, unknown>>((acc, field) => {
    acc[field.name] = field.value;
    return acc;
  }, {});
  draftName.value = String(draftValues.value.name ?? '');
  status.value = 'editing';
  editTx.beginEdit();
}

function cancelEdit() {
  if (status.value !== 'editing') {
    return;
  }
  draftValues.value = fields.value.reduce<Record<string, unknown>>((acc, field) => {
    acc[field.name] = field.value;
    return acc;
  }, {});
  draftName.value = String(draftValues.value.name ?? '');
  status.value = 'ok';
  editTx.cancelEdit();
}

const hasDraftChanges = computed(() => {
  const current = recordData.value || {};
  return Object.keys(draftValues.value).some((key) => {
    if (!canEditField(key)) return false;
    return String(current[key] ?? '') !== String(draftValues.value[key] ?? '');
  });
});
const isSaveDisabled = computed(() => status.value === 'saving' || !hasDraftChanges.value);

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
    const current = recordData.value || {};
    const payload = Object.keys(draftValues.value).reduce<Record<string, unknown>>((acc, key) => {
      if (!canEditField(key)) return acc;
      const before = current[key];
      const after = draftValues.value[key];
      if (String(before ?? '') === String(after ?? '')) return acc;
      acc[key] = after;
      return acc;
    }, {});
    if (!Object.keys(payload).length) {
      status.value = 'ok';
      editTx.cancelEdit();
      return;
    }
    const result = await editTx.save(async () => {
      return writeRecordV6Raw({
        model: model.value,
        id: recordId.value,
        values: payload,
        ifMatch: recordData.value?.write_date ? String(recordData.value?.write_date) : undefined,
      });
    });
    if (result?.meta?.trace_id) {
      lastTraceId.value = String(result.meta.trace_id);
      editTx.markSaved(String(result.meta.trace_id));
    } else if (result?.traceId) {
      lastTraceId.value = String(result.traceId);
      editTx.markSaved(String(result.traceId));
    } else {
      editTx.markSaved();
    }
    status.value = 'ok';
    lastLatencyMs.value = Date.now() - startedAt;
    await load();
  } catch (err) {
    if (err instanceof ApiError && err.status === 409) {
      setError(err, 'Record changed, reload and retry');
    } else {
      setError(err, 'failed to save record');
    }
    traceId.value = error.value?.traceId || '';
    lastTraceId.value = error.value?.traceId || '';
    status.value = 'error';
    lastLatencyMs.value = Date.now() - startedAt;
    editTx.markError(error.value?.code ? String(error.value?.code) : '');
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

.action-feedback {
  margin-top: 6px;
  color: #166534;
}

.action-feedback.error {
  color: #b91c1c;
}

.action-feedback .code {
  color: #64748b;
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

.chatter-compose-actions {
  display: flex;
  align-items: center;
  gap: 8px;
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

.timeline-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}

.timeline-item {
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: 10px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 10px;
  background: #fff;
  padding: 10px;
}

.timeline-type {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 6px;
  align-self: start;
}

.timeline-type.type-message {
  color: #1d4ed8;
  background: #eff6ff;
  border-color: #bfdbfe;
}

.timeline-type.type-attachment {
  color: #166534;
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.timeline-type.type-audit {
  color: #7c2d12;
  background: #fff7ed;
  border-color: #fdba74;
}

.timeline-main {
  min-width: 0;
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
