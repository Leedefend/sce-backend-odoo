<template>
  <main class="page">
    <header class="header">
      <div>
        <h1>{{ title }}</h1>
        <p class="meta">Model: {{ model }} · ID: {{ recordIdDisplay }}</p>
        <p v-if="actionFeedback" class="action-feedback" :class="{ error: !actionFeedback.success }">
          {{ actionFeedback.message }} <span class="code">({{ actionFeedback.reasonCode }})</span>
        </p>
        <p v-if="actionFeedback && actionFeedback.traceId" class="action-evidence">
          trace: <code>{{ actionFeedback.traceId }}</code>
          <span v-if="actionFeedback.requestId"> · request: <code>{{ actionFeedback.requestId }}</code></span>
          <span v-if="actionFeedback.replayed"> · replayed</span>
          <button type="button" class="evidence-copy" @click="copyActionEvidence">复制证据</button>
          <button type="button" class="evidence-copy" @click="clearActionFeedback">关闭</button>
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
          v-for="action in displayedSemanticActionButtons"
          :key="`semantic-${action.key}`"
          :disabled="!recordId || saving || loading || actionBusy || !action.allowed"
          class="action secondary"
          :class="{ primary: action.key === primaryActionKey }"
          :title="semanticActionTooltip(action)"
          @click="runSemanticAction(action)"
        >
          {{ actionBusy && actionBusyKey === action.key ? `${action.label} · 执行中...` : action.label }}
        </button>
        <button :disabled="!lastSemanticAction || actionBusy || loading" class="action secondary" @click="rerunLastSemanticAction">
          {{ retryLastActionLabel }}
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
      <section v-if="semanticActionButtons.length" class="semantic-action-filters">
        <button type="button" :class="{ active: actionFilterMode === 'all' }" @click="actionFilterMode = 'all'">
          全部 ({{ semanticActionStats.total }})
        </button>
        <button type="button" :class="{ active: actionFilterMode === 'allowed' }" @click="actionFilterMode = 'allowed'">
          可执行 ({{ semanticActionStats.allowed }})
        </button>
        <button type="button" :class="{ active: actionFilterMode === 'blocked' }" @click="actionFilterMode = 'blocked'">
          阻塞 ({{ semanticActionStats.blocked }})
        </button>
        <button type="button" :class="{ active: hideBlockedHints }" @click="hideBlockedHints = !hideBlockedHints">
          {{ hideBlockedHints ? '显示阻塞' : '隐藏阻塞' }}
        </button>
        <input
          v-model.trim="semanticActionSearch"
          class="semantic-search"
          type="text"
          placeholder="搜索动作/原因码"
        />
      </section>
      <section v-if="semanticActionButtons.length" class="semantic-action-stats">
        <span>主动作: {{ primaryActionKey || '-' }}</span>
        <span>当前筛选: {{ actionFilterMode }}</span>
        <span>显示中: {{ displayedSemanticActionButtons.length }}</span>
        <span :class="{ stale: actionSurfaceIsStale }">刷新: {{ actionSurfaceAgeLabel }}</span>
        <button type="button" class="stats-refresh" @click="loadPaymentActionSurface">刷新动作面</button>
        <button type="button" class="stats-refresh" @click="copyActionSurface">复制动作面</button>
        <button type="button" class="stats-refresh" @click="exportActionSurface">导出动作面</button>
        <label class="auto-refresh-toggle">
          <input v-model="autoRefreshActionSurface" type="checkbox" />
          自动刷新
        </label>
      </section>
      <section v-if="semanticActionButtons.length && actionSurfaceIsStale" class="semantic-action-stale-banner">
        <span>动作面可能过期（超过 60 秒），请先刷新后再执行。</span>
        <button type="button" class="stats-refresh" @click="loadPaymentActionSurface">立即刷新</button>
      </section>
      <section v-if="semanticActionButtons.length" class="semantic-action-shortcuts">
        快捷键: <code>Ctrl+Enter</code> 执行主动作 · <code>Alt+R</code> 重试上次动作
      </section>
      <section v-if="semanticActionButtons.length" class="semantic-action-hints">
        <div
          v-for="action in displayedSemanticActionButtons"
          :key="`semantic-hint-${action.key}`"
          class="semantic-action-hint"
          :class="{ blocked: !action.allowed }"
        >
          <strong>{{ action.label }}</strong>
          <span>
            {{ action.currentState || '-' }} → {{ action.nextStateHint || '-' }}
          </span>
          <span v-if="action.requiredRoleLabel" class="role-hint">
            角色：{{ action.requiredRoleLabel }}
            <em v-if="action.actorMatchesRequiredRole" class="role-match">（当前可执行角色）</em>
            <em v-else class="role-mismatch">（需转交）</em>
          </span>
          <span v-if="action.handoffHint" class="handoff-hint">
            {{ action.handoffHint }}
          </span>
          <span v-if="action.handoffRequired" class="handoff-required">
            请转交给 {{ action.requiredRoleLabel || action.requiredRoleKey || '对应角色' }} 处理
          </span>
          <span v-if="!action.allowed">{{ blockedReasonText(action) }}</span>
          <span v-if="!action.allowed && action.suggestedAction" class="suggestion">
            建议：{{ action.suggestedAction }}
          </span>
          <button
            v-if="!action.allowed && suggestedActionMeta(action).canRun"
            class="hint-action"
            type="button"
            @click="runBlockedSuggestedAction(action)"
          >
            {{ suggestedActionMeta(action).label || '执行建议' }}
          </button>
          <button
            v-if="!action.allowed && action.handoffRequired"
            class="hint-action"
            type="button"
            @click="copyHandoffNote(action)"
          >
            复制转交说明
          </button>
        </div>
      </section>
      <section v-if="actionHistory.length" class="semantic-action-history">
        <div class="history-header">
          <h3>最近操作</h3>
          <div class="history-actions">
            <button type="button" class="history-clear" @click="copyAllHistory">复制全部</button>
            <button type="button" class="history-clear" @click="exportEvidenceBundle">导出证据包</button>
            <button type="button" class="history-clear" @click="clearActionHistory">清空</button>
          </div>
        </div>
        <div class="history-filters">
          <button type="button" :class="{ active: historyReasonFilter === 'ALL' }" @click="historyReasonFilter = 'ALL'">全部</button>
          <button
            v-for="reason in historyReasonCodes"
            :key="`history-reason-${reason}`"
            type="button"
            :class="{ active: historyReasonFilter === reason }"
            @click="historyReasonFilter = reason"
          >
            {{ reason }}
          </button>
        </div>
        <ul>
          <li v-for="entry in filteredActionHistory" :key="entry.key">
            <strong>{{ entry.label }}</strong>
            <span class="history-outcome" :class="{ error: !entry.success }">{{ entry.reasonCode }}</span>
            <span class="history-meta">state: {{ entry.stateBefore || '-' }}</span>
            <span class="history-meta">at: {{ entry.atText }} ({{ historyAgeLabel(entry) }})</span>
            <span v-if="entry.traceId" class="history-meta">trace: {{ entry.traceId }}</span>
            <button type="button" class="history-copy" @click="copyHistoryEntry(entry)">复制</button>
          </li>
        </ul>
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
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
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
import { describeSuggestedAction, runSuggestedAction } from '../composables/useSuggestedAction';

const route = useRoute();
const router = useRouter();

const { error, clearError, setError } = useStatus();
const loading = ref(false);
const saving = ref(false);
const executing = ref<string | null>(null);
const actionBusy = ref(false);
const actionBusyKey = ref('');
type ActionFeedback = {
  message: string;
  reasonCode: string;
  success: boolean;
  traceId?: string;
  requestId?: string;
  replayed?: boolean;
};

type ActionHistoryEntry = {
  key: string;
  label: string;
  reasonCode: string;
  success: boolean;
  stateBefore: string;
  traceId: string;
  at: number;
  atText: string;
};

const actionFeedback = ref<ActionFeedback | null>(null);
const actionHistory = ref<ActionHistoryEntry[]>([]);
const lastSemanticAction = ref<{ action: string; reason: string; label: string } | null>(null);
const historyReasonFilter = ref('ALL');
let actionFeedbackTimer: ReturnType<typeof setTimeout> | null = null;
let actionSurfaceRefreshTimer: ReturnType<typeof setInterval> | null = null;
const actionFilterStorageKey = 'sc.payment.action_filter.v1';
const actionHistoryStoragePrefix = 'sc.payment.action_history.v1';

const model = computed(() => String(route.params.model || ''));
const recordId = computed(() => (route.params.id === 'new' ? null : Number(route.params.id)));
const recordIdDisplay = computed(() => (recordId.value ? recordId.value : 'new'));
const title = computed(() => `Form: ${model.value}`);
const errorCopy = computed(() => resolveErrorCopy(error.value, 'failed to load record'));
const actionHistoryStorageKey = computed(() => `${actionHistoryStoragePrefix}:${model.value}:${recordIdDisplay.value}`);
const PAYMENT_REASON_TEXT: Record<string, string> = {
  PAYMENT_ATTACHMENTS_REQUIRED: "提交前请先上传附件",
  BUSINESS_RULE_FAILED: "当前状态不满足执行条件",
  MISSING_PARAMS: "缺少必要参数",
  NOT_FOUND: "记录不存在或已被删除",
};

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
  suggestedAction: string;
  currentState: string;
  nextStateHint: string;
  requiredRoleLabel: string;
  requiredRoleKey: string;
  handoffHint: string;
  actorMatchesRequiredRole: boolean;
  handoffRequired: boolean;
  deliveryPriority: number;
  requiresReason: boolean;
  executeIntent: string;
};
const paymentActionSurface = ref<PaymentRequestActionSurfaceItem[]>([]);
const paymentActionSurfaceLoadedAt = ref(0);
const autoRefreshActionSurface = ref(false);
const primaryActionKey = ref('');
const isPaymentRequestModel = computed(() => model.value === 'payment.request');
const actionFilterMode = ref<'all' | 'allowed' | 'blocked'>('all');
const hideBlockedHints = ref(false);
const semanticActionSearch = ref('');
try {
  const cachedFilter = String(window.localStorage.getItem(actionFilterStorageKey) || '').trim();
  if (cachedFilter === 'all' || cachedFilter === 'allowed' || cachedFilter === 'blocked') {
    actionFilterMode.value = cachedFilter;
  }
} catch {
  // Ignore storage errors and keep default mode.
}
function semanticActionRank(action: SemanticActionButton) {
  if (action.key === primaryActionKey.value) return 0;
  if (action.allowed) return 1;
  return 2;
}

const semanticActionButtons = computed<SemanticActionButton[]>(() => {
  if (!isPaymentRequestModel.value) return [];
  return paymentActionSurface.value
    .map((item) => ({
      key: String(item.key || '').trim(),
      label: String(item.label || item.key || '操作').trim(),
      allowed: Boolean(item.allowed),
      reasonCode: String(item.reason_code || ''),
      blockedMessage: String(item.blocked_message || ''),
      suggestedAction: String(item.suggested_action || ''),
      currentState: String(item.current_state || ''),
      nextStateHint: String(item.next_state_hint || ''),
      requiredRoleLabel: String(item.required_role_label || ''),
      requiredRoleKey: String(item.required_role_key || ''),
      handoffHint: String(item.handoff_hint || ''),
      actorMatchesRequiredRole: Boolean(item.actor_matches_required_role),
      handoffRequired: Boolean(item.handoff_required),
      deliveryPriority: Number(item.delivery_priority || 100),
      requiresReason: Boolean(item.requires_reason),
      executeIntent: String(item.execute_intent || 'payment.request.execute'),
    }))
    .sort((a, b) => {
      const rankDelta = semanticActionRank(a) - semanticActionRank(b);
      if (rankDelta !== 0) return rankDelta;
      const deliveryDelta = Number(a.deliveryPriority || 100) - Number(b.deliveryPriority || 100);
      if (deliveryDelta !== 0) return deliveryDelta;
      return a.label.localeCompare(b.label, 'zh-CN');
    });
});
const displayedSemanticActionButtons = computed(() => {
  const search = semanticActionSearch.value.toLowerCase();
  if (actionFilterMode.value === 'allowed') {
    return semanticActionButtons.value.filter((item) => item.allowed && `${item.label} ${item.reasonCode}`.toLowerCase().includes(search));
  }
  if (actionFilterMode.value === 'blocked') {
    return semanticActionButtons.value.filter((item) => !item.allowed && `${item.label} ${item.reasonCode}`.toLowerCase().includes(search));
  }
  return semanticActionButtons.value.filter(
    (item) => (hideBlockedHints.value ? item.allowed : true) && `${item.label} ${item.reasonCode}`.toLowerCase().includes(search),
  );
});
const semanticActionStats = computed(() => {
  const total = semanticActionButtons.value.length;
  const allowed = semanticActionButtons.value.filter((item) => item.allowed).length;
  const blocked = total - allowed;
  return { total, allowed, blocked };
});
const actionSurfaceAgeLabel = computed(() => {
  if (!paymentActionSurfaceLoadedAt.value) return '-';
  const deltaSec = Math.max(0, Math.floor((Date.now() - paymentActionSurfaceLoadedAt.value) / 1000));
  if (deltaSec < 60) return `${deltaSec}s`;
  const min = Math.floor(deltaSec / 60);
  const sec = deltaSec % 60;
  return `${min}m${sec}s`;
});
const actionSurfaceIsStale = computed(() => {
  if (!paymentActionSurfaceLoadedAt.value) return true;
  return Date.now() - paymentActionSurfaceLoadedAt.value > 60_000;
});
const primaryAllowedAction = computed(() => {
  const primary = displayedSemanticActionButtons.value.find(
    (item) => item.key === primaryActionKey.value && item.allowed,
  );
  if (primary) return primary;
  return displayedSemanticActionButtons.value.find((item) => item.allowed) || null;
});
const retryLastActionLabel = computed(() => {
  if (!lastSemanticAction.value) return '重试上次动作';
  return `重试：${lastSemanticAction.value.label}`;
});
const historyReasonCodes = computed(() =>
  Array.from(new Set(actionHistory.value.map((item) => item.reasonCode).filter(Boolean))).sort(),
);
const filteredActionHistory = computed(() => {
  if (historyReasonFilter.value === 'ALL') return actionHistory.value;
  return actionHistory.value.filter((item) => item.reasonCode === historyReasonFilter.value);
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
  { label: 'action_filter', value: actionFilterMode.value },
  { label: 'action_history_count', value: String(actionHistory.value.length) },
  { label: 'last_semantic_action', value: lastSemanticAction.value?.action || '-' },
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
  primaryActionKey.value = '';
  if (!isPaymentRequestModel.value || !recordId.value) {
    return;
  }
  try {
    const response = await fetchPaymentRequestAvailableActions(recordId.value);
    paymentActionSurface.value = Array.isArray(response.data?.actions) ? response.data.actions : [];
    paymentActionSurfaceLoadedAt.value = Date.now();
    primaryActionKey.value = String(response.data?.primary_action_key || '').trim();
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
  const roleHint = action.requiredRoleLabel ? `应由${action.requiredRoleLabel}处理` : '';
  const handoffHint = action.handoffRequired ? "；当前角色不匹配，请转交" : "";
  const blockedReason = blockedReasonText(action);
  if (action.allowed) return '';
  if (action.suggestedAction) {
    return `不可执行：${blockedReason}；建议：${action.suggestedAction}${roleHint ? `；${roleHint}` : ''}${handoffHint}`;
  }
  if (blockedReason) return `不可执行：${blockedReason}${roleHint ? `；${roleHint}` : ''}${handoffHint}`;
  return `当前状态不可执行${roleHint ? `；${roleHint}` : ''}${handoffHint}`;
}

function blockedReasonText(action: SemanticActionButton) {
  const message = String(action.blockedMessage || '').trim();
  const reasonCode = String(action.reasonCode || '').trim();
  if (message) return message;
  if (reasonCode) return PAYMENT_REASON_TEXT[reasonCode] || reasonCode;
  return '当前状态不可执行';
}

async function copyHandoffNote(action: SemanticActionButton) {
  const lines = [
    `record=${model.value}:${recordId.value || '-'}`,
    `action=${action.label}(${action.key})`,
    `required_role=${action.requiredRoleLabel || action.requiredRoleKey || '-'}`,
    `reason=${blockedReasonText(action)}`,
    `handoff_hint=${action.handoffHint || '-'}`,
    `trace_id=${lastTraceId.value || '-'}`,
  ];
  try {
    await navigator.clipboard.writeText(lines.join('\n'));
    actionFeedback.value = {
      message: '转交说明已复制',
      reasonCode: 'HANDOFF_NOTE_COPIED',
      success: true,
      traceId: lastTraceId.value,
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: '转交说明复制失败',
      reasonCode: 'HANDOFF_NOTE_COPY_FAILED',
      success: false,
      traceId: lastTraceId.value,
    };
  }
}

async function copyActionSurface() {
  if (!recordId.value || !semanticActionButtons.value.length) return;
  const payload = {
    model: model.value,
    record_id: recordId.value,
    primary_action_key: primaryActionKey.value,
    loaded_at: paymentActionSurfaceLoadedAt.value,
    actions: semanticActionButtons.value,
  };
  try {
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    actionFeedback.value = {
      message: '动作面已复制',
      reasonCode: 'ACTION_SURFACE_COPIED',
      success: true,
      traceId: lastTraceId.value,
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: '动作面复制失败',
      reasonCode: 'ACTION_SURFACE_COPY_FAILED',
      success: false,
      traceId: lastTraceId.value,
    };
  }
}

function exportActionSurface() {
  if (!recordId.value || !semanticActionButtons.value.length) return;
  const payload = {
    model: model.value,
    record_id: recordId.value,
    primary_action_key: primaryActionKey.value,
    loaded_at: paymentActionSurfaceLoadedAt.value,
    exported_at: Date.now(),
    actions: semanticActionButtons.value,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `payment_action_surface_${model.value}_${recordId.value}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function exportEvidenceBundle() {
  if (!recordId.value) return;
  const payload = {
    model: model.value,
    record_id: recordId.value,
    exported_at: Date.now(),
    primary_action_key: primaryActionKey.value,
    action_surface_loaded_at: paymentActionSurfaceLoadedAt.value,
    action_surface_stale: actionSurfaceIsStale.value,
    last_trace_id: lastTraceId.value,
    last_feedback: actionFeedback.value,
    semantic_actions: semanticActionButtons.value,
    action_history: actionHistory.value,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `payment_evidence_bundle_${model.value}_${recordId.value}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
  actionFeedback.value = {
    message: '证据包已导出',
    reasonCode: 'EVIDENCE_BUNDLE_EXPORTED',
    success: true,
    traceId: lastTraceId.value,
  };
  armActionFeedbackAutoClear();
}

function suggestedActionMeta(action: SemanticActionButton) {
  return describeSuggestedAction(action.suggestedAction, {
    traceId: lastTraceId.value || undefined,
    reasonCode: action.reasonCode || undefined,
    message: action.blockedMessage || undefined,
    hasRetryHandler: true,
    hasActionHandler: true,
  });
}

function runBlockedSuggestedAction(action: SemanticActionButton) {
  runSuggestedAction(action.suggestedAction, {
    traceId: lastTraceId.value || undefined,
    reasonCode: action.reasonCode || undefined,
    message: action.blockedMessage || undefined,
    onRetry: load,
    onSuggestedAction: handleSuggestedAction,
    onExecuted: ({ success }) => {
      actionFeedback.value = {
        message: success ? '已执行建议操作' : '建议操作执行失败',
        reasonCode: success ? 'SUGGESTED_ACTION_OK' : 'SUGGESTED_ACTION_FAILED',
        success,
        traceId: lastTraceId.value,
      };
    },
  });
}

function parseIntentActionResult(data: Record<string, unknown> | null | undefined) {
  const reasonCode = String(data?.reason_code || 'OK');
  const success =
    typeof data?.success === 'boolean'
      ? Boolean(data.success)
      : reasonCode === 'OK' || reasonCode === 'DRY_RUN';
  const replayed = Boolean(data?.idempotent_replay);
  let message = String(data?.message || (success ? '操作成功' : '操作失败'));
  if (replayed && success) {
    message = `${message}（复用先前执行结果）`;
  }
  const requestId = String(data?.request_id || '');
  return { message, reasonCode, success, replayed, requestId };
}

async function runSemanticAction(action: SemanticActionButton) {
  actionFeedback.value = null;
  if (!model.value || !recordId.value || !action.allowed) {
    return;
  }
  if (actionSurfaceIsStale.value) {
    const proceed = window.confirm("动作面已过期（超过 60 秒）。建议先刷新。点击“确定”继续执行，点击“取消”将自动刷新。");
    if (!proceed) {
      await loadPaymentActionSurface();
      actionFeedback.value = {
        message: "已取消执行并刷新动作面",
        reasonCode: "ACTION_SURFACE_REFRESH_REQUIRED",
        success: false,
        traceId: lastTraceId.value,
      };
      return;
    }
  }
  if (action.key === 'approve' || action.key === 'done') {
    const confirmed = window.confirm(`确认执行「${action.label}」？`);
    if (!confirmed) {
      actionFeedback.value = { message: '已取消操作', reasonCode: 'CANCELLED', success: false };
      return;
    }
  }
  let reason = '';
  if (action.requiresReason) {
    reason = String(window.prompt('请输入驳回原因（至少 4 个字符）', '') || '').trim();
    if (!reason || reason.length < 4) {
      actionFeedback.value = { message: '已取消：缺少原因', reasonCode: 'MISSING_PARAMS', success: false };
      return;
    }
  }
  actionBusy.value = true;
  actionBusyKey.value = action.key;
  const stateBefore = action.currentState;
  try {
    lastSemanticAction.value = {
      action: action.key,
      reason,
      label: action.label,
    };
    const response = await executePaymentRequestAction({
      paymentRequestId: recordId.value,
      action: action.key,
      reason,
    });
    lastTraceId.value = response.traceId || lastTraceId.value;
    const parsed = parseIntentActionResult(response.data as Record<string, unknown>);
    actionFeedback.value = {
      ...parsed,
      traceId: response.traceId || '',
    };
    actionHistory.value = [
      {
        key: `${action.key}_${Date.now()}`,
        label: action.label,
        reasonCode: parsed.reasonCode,
        success: parsed.success,
        stateBefore,
        traceId: response.traceId || '',
        at: Date.now(),
        atText: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      },
      ...actionHistory.value,
    ].slice(0, 6);
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
    actionFeedback.value = { message: '操作失败', reasonCode: 'EXECUTE_FAILED', success: false, traceId: lastTraceId.value };
  } finally {
    actionBusy.value = false;
    actionBusyKey.value = '';
  }
}

async function rerunLastSemanticAction() {
  if (!lastSemanticAction.value || !recordId.value) return;
  actionBusy.value = true;
  actionBusyKey.value = lastSemanticAction.value.action;
  try {
    const response = await executePaymentRequestAction({
      paymentRequestId: recordId.value,
      action: lastSemanticAction.value.action,
      reason: lastSemanticAction.value.reason,
    });
    lastTraceId.value = response.traceId || lastTraceId.value;
    const parsed = parseIntentActionResult(response.data as Record<string, unknown>);
    actionFeedback.value = {
      ...parsed,
      message: `${lastSemanticAction.value.label} 重试：${parsed.message}`,
      traceId: response.traceId || '',
    };
    await load();
  } catch (err) {
    setError(err, 'failed to retry semantic action');
    actionFeedback.value = { message: '重试失败', reasonCode: 'EXECUTE_FAILED', success: false, traceId: lastTraceId.value };
  } finally {
    actionBusy.value = false;
    actionBusyKey.value = '';
  }
}

function clearActionHistory() {
  actionHistory.value = [];
}

function historyAgeLabel(entry: ActionHistoryEntry) {
  const deltaSec = Math.max(0, Math.floor((Date.now() - Number(entry.at || 0)) / 1000));
  if (deltaSec < 60) return `${deltaSec}s ago`;
  const min = Math.floor(deltaSec / 60);
  const sec = deltaSec % 60;
  return `${min}m${sec}s ago`;
}

function armActionFeedbackAutoClear() {
  if (actionFeedbackTimer) {
    clearTimeout(actionFeedbackTimer);
    actionFeedbackTimer = null;
  }
  if (!actionFeedback.value) return;
  actionFeedbackTimer = setTimeout(() => {
    actionFeedback.value = null;
    actionFeedbackTimer = null;
  }, 6000);
}

async function copyHistoryEntry(entry: ActionHistoryEntry) {
  const payload = [
    `action=${entry.label}`,
    `reason_code=${entry.reasonCode}`,
    `state_before=${entry.stateBefore || '-'}`,
    `trace_id=${entry.traceId || '-'}`,
    `success=${String(entry.success)}`,
  ].join('\n');
  try {
    await navigator.clipboard.writeText(payload);
  } catch {
    // Ignore clipboard failures for this utility action.
  }
}

async function copyAllHistory() {
  if (!actionHistory.value.length) return;
  const lines = actionHistory.value.map((entry) =>
    [
      `action=${entry.label}`,
      `reason_code=${entry.reasonCode}`,
      `state_before=${entry.stateBefore || '-'}`,
      `trace_id=${entry.traceId || '-'}`,
      `at=${entry.atText}`,
      `success=${String(entry.success)}`,
    ].join(' | '),
  );
  try {
    await navigator.clipboard.writeText(lines.join('\n'));
  } catch {
    // Ignore clipboard errors.
  }
}

function onSemanticHotkey(event: KeyboardEvent) {
  if (event.ctrlKey && event.key === 'Enter' && primaryAllowedAction.value && !actionBusy.value && !loading.value) {
    event.preventDefault();
    runSemanticAction(primaryAllowedAction.value);
    return;
  }
  if (event.altKey && (event.key === 'r' || event.key === 'R') && lastSemanticAction.value && !actionBusy.value) {
    event.preventDefault();
    rerunLastSemanticAction();
  }
}

function reload() {
  load();
}

async function copyActionEvidence() {
  if (!actionFeedback.value) return;
  const lines = [
    `reason_code=${actionFeedback.value.reasonCode}`,
    `trace_id=${actionFeedback.value.traceId || '-'}`,
    `request_id=${actionFeedback.value.requestId || '-'}`,
    `replayed=${String(Boolean(actionFeedback.value.replayed))}`,
  ];
  const payload = lines.join('\n');
  try {
    await navigator.clipboard.writeText(payload);
    actionFeedback.value = {
      ...actionFeedback.value,
      message: `${actionFeedback.value.message}（证据已复制）`,
    };
  } catch {
    // Ignore clipboard failures; keep primary action result visible.
  }
}

function clearActionFeedback() {
  actionFeedback.value = null;
}

function handleSuggestedAction(action: string): boolean {
  if (action !== 'open_record') return false;
  if (!model.value || !recordId.value) return false;
  router.push(`/r/${model.value}/${recordId.value}?view_mode=form`).catch(() => {});
  return true;
}

onMounted(() => {
  load();
  window.addEventListener('keydown', onSemanticHotkey);
  actionSurfaceRefreshTimer = window.setInterval(() => {
    if (!autoRefreshActionSurface.value || !recordId.value || !isPaymentRequestModel.value || loading.value || actionBusy.value) return;
    void loadPaymentActionSurface();
  }, 15000);
});
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onSemanticHotkey);
  if (actionFeedbackTimer) {
    clearTimeout(actionFeedbackTimer);
    actionFeedbackTimer = null;
  }
  if (actionSurfaceRefreshTimer) {
    clearInterval(actionSurfaceRefreshTimer);
    actionSurfaceRefreshTimer = null;
  }
});
watch(actionFilterMode, (value) => {
  try {
    window.localStorage.setItem(actionFilterStorageKey, value);
  } catch {
    // Ignore storage errors.
  }
});
watch(
  actionHistory,
  (value) => {
    try {
      window.localStorage.setItem(actionHistoryStorageKey.value, JSON.stringify(value.slice(0, 6)));
    } catch {
      // Ignore storage errors.
    }
  },
  { deep: true },
);
watch(
  actionHistoryStorageKey,
  (key) => {
    try {
      const raw = window.localStorage.getItem(key);
      if (!raw) {
        actionHistory.value = [];
        return;
      }
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        actionHistory.value = parsed.slice(0, 6).map((item) => ({
          key: String(item?.key || `${Date.now()}`),
          label: String(item?.label || '-'),
          reasonCode: String(item?.reasonCode || ''),
          success: Boolean(item?.success),
          stateBefore: String(item?.stateBefore || ''),
          traceId: String(item?.traceId || ''),
          at: Number(item?.at || Date.now()),
          atText: String(item?.atText || ''),
        }));
      }
    } catch {
      actionHistory.value = [];
    }
  },
  { immediate: true },
);
watch(actionFeedback, () => {
  armActionFeedbackAutoClear();
});

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

.actions .primary {
  border-color: #0f766e;
  box-shadow: inset 0 0 0 1px #0f766e;
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

.action-evidence {
  margin: 4px 0 0;
  color: #475569;
  font-size: 12px;
}

.evidence-copy {
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #0f172a;
  font-size: 11px;
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

.semantic-action-filters {
  display: flex;
  gap: 8px;
}

.semantic-action-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #64748b;
}

.semantic-action-stats .stale {
  color: #b45309;
  font-weight: 600;
}

.semantic-action-stale-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid #f59e0b;
  background: #fff7ed;
  color: #9a3412;
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 12px;
}

.stats-refresh {
  padding: 2px 8px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  font-size: 11px;
}

.auto-refresh-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #334155;
}

.semantic-action-shortcuts {
  font-size: 12px;
  color: #475569;
}

.semantic-action-shortcuts code {
  background: #e2e8f0;
  border-radius: 6px;
  padding: 2px 6px;
}

.semantic-action-filters button {
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #0f172a;
  font-size: 12px;
}

.semantic-action-filters button.active {
  border-color: #0f766e;
  box-shadow: inset 0 0 0 1px #0f766e;
}

.semantic-search {
  margin-left: auto;
  min-width: 180px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  font-size: 12px;
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

.semantic-action-hint .suggestion {
  color: #475569;
}

.semantic-action-hint .role-hint {
  color: #0f766e;
}

.semantic-action-hint .role-match {
  font-style: normal;
  color: #0f766e;
}

.semantic-action-hint .role-mismatch {
  font-style: normal;
  color: #b45309;
}

.semantic-action-hint .handoff-hint {
  color: #334155;
}

.semantic-action-hint .handoff-required {
  color: #b45309;
}

.hint-action {
  margin-left: auto;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #0f172a;
  font-size: 12px;
}

.semantic-action-history {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
}

.semantic-action-history h3 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #0f172a;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.history-actions {
  display: flex;
  gap: 6px;
}

.history-filters {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.history-filters button {
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  font-size: 11px;
}

.history-filters button.active {
  border-color: #0f766e;
  box-shadow: inset 0 0 0 1px #0f766e;
}

.history-clear {
  padding: 2px 8px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  font-size: 11px;
}

.semantic-action-history ul {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
}

.history-outcome {
  margin-left: 8px;
  color: #0f766e;
}

.history-outcome.error {
  color: #b91c1c;
}

.history-meta {
  margin-left: 8px;
  color: #64748b;
  font-size: 12px;
}

.history-copy {
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  font-size: 11px;
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
