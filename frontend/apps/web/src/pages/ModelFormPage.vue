<template>
  <main class="page">
    <header class="header">
      <div>
        <h1>{{ title }}</h1>
        <p class="meta">Model: {{ model }} · ID: {{ recordIdDisplay }}</p>
        <p v-if="actionFeedback" class="action-feedback" :class="{ error: !actionFeedback.success }">
          {{ actionFeedback.message }} <span class="code">({{ actionFeedback.reasonCode }})</span>
        </p>
      </div>
      <div class="actions">
        <button
          v-for="btn in nativeHeaderButtons"
          :key="btn.name ?? btn.string"
          :disabled="!recordId || saving || loading || executing === btn.name || buttonState(btn).state !== 'enabled'"
          class="action secondary"
          :title="buttonTooltip(btn)"
          @click="runButton(btn)"
        >
          {{ buttonLabel(btn) }}
        </button>
        <button
          v-for="action in semanticActionButtons"
          :key="`semantic-${action.key}`"
          :disabled="!recordId || saving || loading || actionBusy || !action.allowed"
          class="action secondary"
          :title="semanticActionTooltip(action)"
          @click="runSemanticAction(action)"
        >
          {{ action.label }}
        </button>
        <button :disabled="saving" @click="save">{{ saving ? 'Saving...' : 'Save' }}</button>
        <button @click="reload">Reload</button>
      </div>
    </header>

    <StatusPanel v-if="loading" title="Loading record..." variant="info" />
    <StatusPanel
      v-else-if="error"
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="error?.traceId"
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
      v-else-if="renderBlocked"
      title="View node unsupported"
      message="Layout nodes are present but renderer support is incomplete."
      error-code="VIEW_NODE_UNSUPPORTED"
      variant="error"
      :on-retry="reload"
    />

    <section v-else class="card">
      <section v-if="semanticActionButtons.length" class="semantic-action-hints">
        <div
          v-for="action in semanticActionButtons"
          :key="`semantic-hint-${action.key}`"
          class="semantic-action-hint"
          :class="{ blocked: !action.allowed }"
        >
          <strong>{{ action.label }}</strong>
          <span>
            {{ action.currentState || '-' }} → {{ action.nextStateHint || '-' }}
          </span>
          <span v-if="!action.allowed">{{ action.blockedMessage || action.reasonCode || '当前状态不可执行' }}</span>
        </div>
      </section>
      <ViewLayoutRenderer
        v-if="renderMode === 'layout_tree'"
        :layout="viewContract?.layout || {}"
        :fields="viewContract?.fields"
        :record="formData"
        :parent-id="recordId || undefined"
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
import {
  executePaymentRequestAction,
  fetchPaymentRequestAvailableActions,
  type PaymentRequestActionSurfaceItem,
} from '../api/paymentRequest';
import { extractFieldNames, resolveView } from '../app/resolvers/viewResolver';
import FieldValue from '../components/FieldValue.vue';
import StatusPanel from '../components/StatusPanel.vue';
import ViewLayoutRenderer from '../components/view/ViewLayoutRenderer.vue';
import type { ViewButton, ViewContract } from '@sc/schema';
import { recordTrace, createTraceId } from '../services/trace';
import { resolveErrorCopy, useStatus } from '../composables/useStatus';
import DevContextPanel from '../components/DevContextPanel.vue';
import { isHudEnabled } from '../config/debug';
import { useSessionStore } from '../stores/session';
import { capabilityTooltip, evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { ErrorCodes } from '../app/error_codes';
import { parseExecuteResult, semanticButtonLabel } from '../app/action_semantics';

const route = useRoute();
const router = useRouter();

const { error, clearError, setError } = useStatus();
const loading = ref(false);
const saving = ref(false);
const executing = ref<string | null>(null);
const actionBusy = ref(false);
const actionFeedback = ref<{ message: string; reasonCode: string; success: boolean } | null>(null);

const model = computed(() => String(route.params.model || ''));
const recordId = computed(() => (route.params.id === 'new' ? null : Number(route.params.id)));
const recordIdDisplay = computed(() => (recordId.value ? recordId.value : 'new'));
const title = computed(() => `Form: ${model.value}`);
const errorCopy = computed(() => resolveErrorCopy(error.value, 'failed to load record'));

const viewContract = ref<ViewContract | null>(null);
const fields = ref<
  Array<{ name: string; label: string; descriptor?: ViewContract['fields'][string]; readonly?: boolean }>
>([]);
const formData = reactive<Record<string, unknown>>({});
const draftName = ref('');
const layoutStats = ref({ field: 0, group: 0, notebook: 0, page: 0, unsupported: 0 });
type LayoutGroupLike = {
  fields?: unknown[];
  sub_groups?: LayoutGroupLike[];
};
type LayoutNotebookLike = {
  pages?: unknown[];
};

const headerButtons = computed(() => {
  const raw =
    viewContract.value?.layout?.headerButtons ??
    (viewContract.value as { layout?: { header_buttons?: ViewButton[] } } | null)?.layout?.header_buttons ??
    [];
  return normalizeButtons(raw);
});
type SemanticActionButton = {
  key: string;
  label: string;
  allowed: boolean;
  reasonCode: string;
  blockedMessage: string;
  currentState: string;
  nextStateHint: string;
  requiresReason: boolean;
  executeIntent: string;
};
const paymentActionSurface = ref<PaymentRequestActionSurfaceItem[]>([]);
const isPaymentRequestModel = computed(() => model.value === 'payment.request');
const semanticActionButtons = computed<SemanticActionButton[]>(() => {
  if (!isPaymentRequestModel.value) return [];
  return paymentActionSurface.value.map((item) => ({
    key: String(item.key || '').trim(),
    label: String(item.label || item.key || '操作').trim(),
    allowed: Boolean(item.allowed),
    reasonCode: String(item.reason_code || ''),
    blockedMessage: String(item.blocked_message || ''),
    currentState: String(item.current_state || ''),
    nextStateHint: String(item.next_state_hint || ''),
    requiresReason: Boolean(item.requires_reason),
    executeIntent: String(item.execute_intent || 'payment.request.execute'),
  }));
});
const nativeHeaderButtons = computed(() => {
  if (isPaymentRequestModel.value && semanticActionButtons.value.length > 0) {
    return [];
  }
  return headerButtons.value;
});
const renderMode = computed(() => (viewContract.value?.layout ? 'layout_tree' : 'fallback_fields'));
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
  { label: 'semantic_actions', value: semanticActionButtons.value.map((item) => `${item.key}:${item.allowed}`).join(',') || '-' },
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
    await loadPaymentActionSurface();
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

async function loadPaymentActionSurface() {
  paymentActionSurface.value = [];
  if (!isPaymentRequestModel.value || !recordId.value) {
    return;
  }
  try {
    const response = await fetchPaymentRequestAvailableActions(recordId.value);
    paymentActionSurface.value = Array.isArray(response.data?.actions) ? response.data.actions : [];
    if (response.traceId) {
      lastTraceId.value = response.traceId;
    }
  } catch (err) {
    setError(err, 'failed to load payment request actions');
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
  return semanticButtonLabel(btn);
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
  actionFeedback.value = null;
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
    actionFeedback.value = parseExecuteResult(response);
  } catch (err) {
    setError(err, 'failed to execute button');
    actionFeedback.value = { message: '操作失败', reasonCode: 'EXECUTE_FAILED', success: false };
  } finally {
    executing.value = null;
  }
}

function semanticActionTooltip(action: SemanticActionButton) {
  if (action.allowed) return '';
  if (action.blockedMessage) return `不可执行：${action.blockedMessage}`;
  if (action.reasonCode) return `不可执行：${action.reasonCode}`;
  return '当前状态不可执行';
}

function parseIntentActionResult(data: Record<string, unknown> | null | undefined) {
  const reasonCode = String(data?.reason_code || 'OK');
  const success =
    typeof data?.success === 'boolean'
      ? Boolean(data.success)
      : reasonCode === 'OK' || reasonCode === 'DRY_RUN';
  const message = String(data?.message || (success ? '操作成功' : '操作失败'));
  return { message, reasonCode, success };
}

async function runSemanticAction(action: SemanticActionButton) {
  actionFeedback.value = null;
  if (!model.value || !recordId.value || !action.allowed) {
    return;
  }
  let reason = '';
  if (action.requiresReason) {
    reason = String(window.prompt('请输入驳回原因', '') || '').trim();
    if (!reason) {
      actionFeedback.value = { message: '已取消：缺少原因', reasonCode: 'MISSING_PARAMS', success: false };
      return;
    }
  }
  actionBusy.value = true;
  try {
    const response = await executePaymentRequestAction({
      paymentRequestId: recordId.value,
      action: action.key,
      reason,
    });
    lastTraceId.value = response.traceId || lastTraceId.value;
    actionFeedback.value = parseIntentActionResult(response.data as Record<string, unknown>);
    recordTrace({
      ts: Date.now(),
      trace_id: response.traceId || createTraceId(),
      intent: action.executeIntent || 'payment.request.execute',
      status: actionFeedback.value.success ? 'ok' : 'error',
      model: model.value,
      view_mode: 'form',
      params_digest: JSON.stringify({ id: recordId.value, action: action.key }),
    });
    await load();
  } catch (err) {
    setError(err, 'failed to execute semantic action');
    actionFeedback.value = { message: '操作失败', reasonCode: 'EXECUTE_FAILED', success: false };
  } finally {
    actionBusy.value = false;
  }
}

function reload() {
  load();
}

function handleSuggestedAction(action: string): boolean {
  if (action !== 'open_record') return false;
  if (!model.value || !recordId.value) return false;
  router.push(`/r/${model.value}/${recordId.value}?view_mode=form`).catch(() => {});
  return true;
}

onMounted(load);

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

.action-feedback {
  margin: 8px 0 0;
  color: #166534;
  font-size: 13px;
}

.action-feedback.error {
  color: #b91c1c;
}

.action-feedback .code {
  color: #64748b;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 12px;
}

.semantic-action-hints {
  display: grid;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.semantic-action-hint {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 12px;
  color: #334155;
}

.semantic-action-hint.blocked {
  color: #b91c1c;
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
