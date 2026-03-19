<template>
  <section class="page">
    <!-- Page intent: 判断项目是否可控，先看风险与关键指标，再执行下一步动作。 -->
    <header class="header">
      <div>
        <h2>{{ title }}</h2>
        <p class="meta">{{ subtitle }}</p>
        <p v-if="readonlyHint" class="meta readonly-hint">{{ readonlyHint }}</p>
        <p v-if="actionFeedback" class="meta action-feedback" :class="{ error: !actionFeedback.success }">
          {{ actionFeedback.message }} <span class="code">({{ actionFeedback.reasonCode }})</span>
        </p>
      </div>
      <div class="actions">
        <button
          v-for="action in headerActions"
          :key="`header-${action.key}`"
          class="ghost"
          :disabled="status === 'loading' || status === 'saving'"
          @click="executeHeaderAction(action.key)"
        >
          {{ action.label || action.key }}
        </button>
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
        <button class="ghost" @click="goBack">{{ pageText('action_back', 'Back') }}</button>
        <button v-if="status === 'ok' && canEdit" @click="startEdit">{{ pageText('action_edit', 'Edit') }}</button>
        <button v-if="status === 'editing'" :disabled="isSaveDisabled" @click="save">{{ pageText('action_save', 'Save') }}</button>
        <button v-if="status === 'editing'" class="ghost" @click="cancelEdit">{{ pageText('action_cancel', 'Cancel') }}</button>
        <button class="ghost" :disabled="status === 'loading' || status === 'saving'" @click="reload">{{ pageText('action_reload', 'Reload') }}</button>
      </div>
    </header>

    <StatusPanel v-if="status === 'loading'" :title="pageText('loading_title', 'Loading record...')" variant="info" />
    <StatusPanel v-else-if="status === 'saving'" :title="pageText('saving_title', 'Saving record...')" variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="error?.traceId || traceId"
      :error-code="error?.code"
      :reason-code="error?.reasonCode"
      :error-category="error?.errorCategory"
      :error-details="error?.details"
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
      :title="pageText('view_node_unsupported_title', 'View node unsupported')"
      :message="pageText('view_node_unsupported_message', 'Layout nodes are present but renderer support is incomplete.')"
      error-code="VIEW_NODE_UNSUPPORTED"
      variant="error"
      :on-retry="reload"
    />

    <section v-else class="card" :class="{ editing: status === 'editing' }">
      <div v-if="pageSectionEnabled('save_banner', true) && pageSectionTagIs('save_banner', 'div') && editTxState === 'saved'" class="banner success" :style="pageSectionStyle('save_banner')">
        {{ pageText('banner_saved', 'Saved. Changes have been applied.') }}
      </div>
      <section v-if="pageSectionEnabled('project_summary', true) && pageSectionTagIs('project_summary', 'section') && showProjectSummary" class="record-l1" :style="pageSectionStyle('project_summary')">
        <article class="l1-card">
          <p class="l1-label">{{ pageText('summary_status_stage', '项目状态与阶段') }}</p>
          <p class="l1-value">{{ projectStatusSummary }}</p>
        </article>
        <article class="l1-card">
          <p class="l1-label">{{ pageText('summary_risk', '关键风险摘要') }}</p>
          <p class="l1-value">{{ projectRiskSummary }}</p>
        </article>
        <article class="l1-card">
          <p class="l1-label">{{ pageText('summary_finance', '资金/产值指标') }}</p>
          <p class="l1-value">{{ projectFinanceSummary }}</p>
        </article>
      </section>
      <section v-if="pageSectionEnabled('next_actions', true) && pageSectionTagIs('next_actions', 'section') && showProjectSummary" class="record-next" :style="pageSectionStyle('next_actions')">
        <p class="next-label">{{ pageText('next_actions_title', '下一步动作') }}</p>
        <div class="next-actions">
          <button class="ghost" @click="openProjectAction('/my-work', { section: 'todo', search: '项目' })">{{ pageText('next_action_todo', '查看待办') }}</button>
          <button class="ghost" @click="openProjectAction('/s/projects.dashboard')">{{ pageText('next_action_risk', '查看风险') }}</button>
          <button class="ghost" @click="openProjectAction('/my-work', { section: 'todo', search: '合同' })">{{ pageText('next_action_contract', '查看合同') }}</button>
          <button class="ghost" @click="openProjectAction('/my-work', { section: 'todo', search: '成本' })">{{ pageText('next_action_cost', '查看成本') }}</button>
        </div>
      </section>
      <div v-if="ribbon" class="ribbon">{{ ribbon.title || pageText('ribbon_fallback', 'Ribbon') }}</div>
      <div v-if="pageSectionEnabled('stat_buttons', true) && pageSectionTagIs('stat_buttons', 'div') && statButtons.length" class="stat-buttons" :style="pageSectionStyle('stat_buttons')">
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
        v-if="layoutStats.field > 0"
        :layout="viewContract?.layout || {}"
        :fields="viewContract?.fields"
        :record="renderRecord"
        :parent-id="recordId"
        :editing="status === 'editing'"
        :draft-name="draftName"
        :edit-mode="status === 'editing' ? 'all' : 'none'"
        @update:field="handleFieldUpdate"
      />
      <section v-else-if="pageSectionEnabled('details_fallback', true) && pageSectionTagIs('details_fallback', 'section')" class="fallback-fields" :style="pageSectionStyle('details_fallback')">
        <h3>{{ pageText('fallback_details_title', '项目详情') }}</h3>
        <ul>
          <li v-for="field in fields" :key="field.name">
            <span class="fallback-label">{{ field.label }}</span>
            <span class="fallback-value">{{ formatFieldValue(field.value) }}</span>
          </li>
        </ul>
      </section>
      <section v-if="pageSectionEnabled('chatter', true) && pageSectionTagIs('chatter', 'section') && hasChatter" class="chatter" :style="pageSectionStyle('chatter')">
        <h3>{{ pageText('chatter_title', '协作时间线') }}</h3>
        <p v-if="chatterError" class="meta">{{ chatterError }}</p>
        <div class="chatter-compose">
          <textarea v-model="chatterDraft" :placeholder="pageText('chatter_input_placeholder', '输入评论，支持 @同事 ...')" />
          <div class="chatter-compose-actions">
            <button :disabled="chatterPosting || !chatterDraft.trim()" @click="sendChatter">
              {{ chatterPosting ? pageText('chatter_posting', '发布中...') : pageText('chatter_post_action', '发布评论') }}
            </button>
            <input type="file" @change="onAttachmentSelected" />
            <span v-if="chatterUploading" class="meta">{{ pageText('chatter_uploading', '上传中…') }}</span>
            <span v-if="chatterUploadError" class="meta">{{ chatterUploadError }}</span>
          </div>
        </div>
        <p v-if="!timelineEntries.length" class="meta">{{ pageText('chatter_empty', '暂无协作记录。') }}</p>
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
                {{ pageText('action_download', 'Download') }}
              </button>
            </div>
          </li>
        </ul>
      </section>
    </section>

    <DevContextPanel
      :visible="showHud && pageSectionEnabled('dev_context', true) && pageSectionTagIs('dev_context', 'div')"
      :style="pageSectionStyle('dev_context')"
      :title="pageText('dev_context_title', 'Record Context')"
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
import type { ButtonEffect, ButtonEffectTarget, ViewButton, ViewContract } from '@sc/schema';
import ViewLayoutRenderer from '../components/view/ViewLayoutRenderer.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import StatusPanel from '../components/StatusPanel.vue';
import { isHudEnabled } from '../config/debug';
import { resolveEmptyCopy, resolveErrorCopy, useStatus } from '../composables/useStatus';
import { useEditTx } from '../composables/useEditTx';
import { useSessionStore } from '../stores/session';
import { usePageContract } from '../app/pageContract';
import { capabilityTooltip, evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { ErrorCodes } from '../app/error_codes';
import { parseExecuteResult, semanticButtonLabel } from '../app/action_semantics';
import { pickContractNavQuery } from '../app/navigationContext';
import { executePageContractAction } from '../app/pageContractActionRuntime';

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
const editTxState = computed(() => editTx.state.value);

const model = computed(() => String(route.params.model || ''));
const recordId = computed(() => Number(route.params.id));
const recordTitle = ref<string | null>(null);
const title = computed(() => recordTitle.value || `Record ${recordId.value}`);
const subtitle = computed(() => (
  status.value === 'editing'
    ? pageText('subtitle_editing', 'Editing contract fields')
    : pageText('subtitle_ready', 'Record details')
));
const showProjectSummary = computed(() => {
  const payload = recordData.value || {};
  const summarySignals = [
    payload.stage_id,
    payload.stage,
    payload.state,
    payload.status,
    payload.health,
    payload.risk_count,
    payload.warning_count,
    payload.output_value,
    payload.amount_output,
    payload.payment_ratio,
    payload.payment_rate,
  ];
  return summarySignals.some((item) => item !== undefined && item !== null && String(item).trim() !== '');
});
const projectStatusSummary = computed(() => {
  const phase = String(recordData.value?.stage_id || recordData.value?.stage || recordData.value?.state || pageText('project_phase_unset', '未配置阶段'));
  const health = String(recordData.value?.status || recordData.value?.health || '');
  if (health) return `${phase} · ${health}`;
  return phase;
});
const projectRiskSummary = computed(() => {
  const risk = Number(recordData.value?.risk_count || recordData.value?.warning_count || 0);
  if (!Number.isFinite(risk) || risk <= 0) return pageText('project_risk_ok', '正常，暂无高风险告警');
  if (risk >= 3) {
    return `${pageText('project_risk_critical_prefix', '严重，当前高风险 ')}${risk}${pageText('project_risk_critical_suffix', ' 项，需优先闭环')}`;
  }
  return `${pageText('project_risk_attention_prefix', '关注，当前风险 ')}${risk}${pageText('project_risk_attention_suffix', ' 项')}`;
});
const projectFinanceSummary = computed(() => {
  const output = Number(recordData.value?.output_value || recordData.value?.amount_output || 0);
  const pay = Number(recordData.value?.payment_ratio || recordData.value?.payment_rate || 0);
  const outputText = Number.isFinite(output) && output > 0
    ? `${pageText('project_output_prefix', '产值 ')}${output}`
    : pageText('project_output_unset', '产值未配置');
  const payText = Number.isFinite(pay) && pay > 0
    ? `${pageText('project_pay_prefix', '付款比 ')}${pay}${pageText('project_pay_suffix', '%')}`
    : pageText('project_pay_unset', '付款比未配置');
  return `${outputText} · ${payText}`;
});
const canEdit = computed(() => contractWriteAllowed.value);
const readonlyHint = computed(() => {
  if (canEdit.value) return '';
  const level = String(session.productFacts.license?.level || '').trim();
  const bundle = String(session.productFacts.bundle?.name || '').trim();
  if (level && level !== 'enterprise') {
    const bundleSegment = bundle ? `${pageText('readonly_hint_license_bundle_sep', ', Bundle: ')}${bundle}` : '';
    return `${pageText('readonly_hint_license_prefix', '当前为只读模式（License: ')}${level}${bundleSegment}${pageText('readonly_hint_license_suffix', '）。如需编辑权限请联系管理员。')}`;
  }
  return pageText('readonly_hint_default', '当前记录处于只读模式，请联系管理员开通写权限。');
});
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
  return { id: null, source: 'none' as const };
});
const actionId = computed(() => actionContext.value.id);
const showHud = computed(() => isHudEnabled(route));
const requestedSurface = computed<'user' | 'native' | 'hud'>(() => {
  const raw = String(route.query.surface || '').trim().toLowerCase();
  if (raw === 'native' || raw === 'hud' || raw === 'user') return raw;
  if (showHud.value) return 'hud';
  return 'user';
});
const requestedSourceMode = computed(() => (
  requestedSurface.value === 'native' ? 'native_parser' : 'governance_pipeline'
));
const session = useSessionStore();
const pageContract = usePageContract('record');
const pageText = pageContract.text;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const userGroups = computed(() => session.user?.groups_xmlids ?? []);
const statusLabel = computed(() => {
  if (status.value === 'editing') return pageText('status_editing', 'Editing');
  if (status.value === 'saving') return pageText('status_saving', 'Saving');
  if (status.value === 'loading') return pageText('status_loading', 'Loading');
  if (status.value === 'error') return pageText('status_error', 'Error');
  if (status.value === 'empty') return pageText('status_empty', 'Empty');
  return pageText('status_ready', 'Ready');
});
const headerActions = computed(() => pageGlobalActions.value);
const statusTone = computed(() => {
  if (status.value === 'error') return 'danger';
  if (status.value === 'editing' || status.value === 'saving') return 'warn';
  return 'ok';
});
const errorCopy = computed(() => resolveErrorCopy(error.value, pageText('error_fallback', 'Record load failed')));
const emptyCopy = computed(() => resolveEmptyCopy('record'));
const renderMode = computed(() => 'layout_tree');
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
const renderBlocked = computed(() => showHud.value && missingNodes.value.length > 0);
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
  { label: 'surface_requested', value: requestedSurface.value },
  { label: 'source_mode', value: requestedSourceMode.value },
  { label: 'contract_write', value: contractWriteAllowed.value },
  { label: 'latency_ms', value: lastLatencyMs.value ?? '-' },
  { label: 'route', value: route.fullPath },
]);

function resolveCarryQuery(extra?: Record<string, unknown>) {
  return pickContractNavQuery(route.query as Record<string, unknown>, extra);
}

function openProjectAction(path: string, query?: Record<string, string>) {
  router.push({ path, query: query || undefined }).catch(() => {});
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
  const policy = buttonState(btn);
  if (policy.state === 'disabled_capability' && Array.isArray(policy.missing) && policy.missing.length) {
    const details = policy.missing
      .map((key) => {
        const meta = session.capabilityCatalog[key];
        if (!meta) return key;
        const reason = String(meta.reason || '').trim();
        return reason ? `${meta.label || key}（${reason}）` : meta.label || key;
      })
      .slice(0, 4);
    const level = String(session.productFacts.license?.level || '').trim();
    const suffix = level && level !== 'enterprise'
      ? `${pageText('missing_capability_license_prefix', '；当前 License: ')}${level}`
      : '';
    return `${pageText('missing_capability_prefix', '缺少能力：')}${details.join(pageText('missing_capability_sep', '、'))}${suffix}`;
  }
  return capabilityTooltip(policy);
}

function validateSurfaceMarkers(
  data: unknown,
  meta: Record<string, unknown> | null,
  expectedSurface: 'user' | 'native' | 'hud',
) {
  const issues: string[] = [];
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return { ok: false, issues: ['contract payload is not an object'] };
  }
  const row = data as Record<string, unknown>;
  const contractSurface = String(row.contract_surface || '').trim().toLowerCase();
  const renderModeRaw = String(row.render_mode || '').trim().toLowerCase();
  const sourceMode = String(row.source_mode || '').trim().toLowerCase();
  const governedFromNative = row.governed_from_native;
  const surfaceMapping = row.surface_mapping;
  const metaSurface = String(meta?.contract_surface || '').trim().toLowerCase();

  if (!contractSurface) issues.push('missing contract_surface');
  if (!renderModeRaw) issues.push('missing render_mode');
  if (!sourceMode) issues.push('missing source_mode');
  if (typeof governedFromNative !== 'boolean') issues.push('missing governed_from_native');
  if (!surfaceMapping || typeof surfaceMapping !== 'object' || Array.isArray(surfaceMapping)) {
    issues.push('missing surface_mapping');
  }
  if (metaSurface && contractSurface && metaSurface !== contractSurface) {
    issues.push(`meta.contract_surface=${metaSurface} mismatch data.contract_surface=${contractSurface}`);
  }
  if (contractSurface && contractSurface !== expectedSurface) {
    issues.push(`contract_surface=${contractSurface} mismatch expected=${expectedSurface}`);
  }
  return { ok: issues.length === 0, issues };
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
    const actionContract = await loadActionContractRaw(actionId.value, {
      recordId: recordId.value,
      renderProfile: canEdit.value ? 'edit' : 'readonly',
      surface: requestedSurface.value,
      sourceMode: requestedSourceMode.value,
    });
    let view: ViewContract | null = null;
    let contractFieldNames: string[] = [];
    if (actionContract?.data && typeof actionContract.data === 'object') {
      const markerCheck = validateSurfaceMarkers(
        actionContract.data,
        (actionContract.meta as Record<string, unknown> | null) || null,
        requestedSurface.value,
      );
      if (!markerCheck.ok) {
        throw new Error(`contract surface markers invalid: ${markerCheck.issues.slice(0, 4).join(' | ')}`);
      }
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
    setError(err, pageText('error_load_record', 'failed to load record'));
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
    chatterError.value = err instanceof Error ? err.message : pageText('chatter_load_failed', 'Failed to load chatter');
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
    chatterError.value = err instanceof Error ? err.message : pageText('chatter_post_failed', 'Failed to post chatter message');
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
    chatterUploadError.value = err instanceof Error ? err.message : pageText('chatter_upload_failed', 'Failed to upload file');
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
    chatterUploadError.value = err instanceof Error ? err.message : pageText('chatter_download_failed', 'Failed to download file');
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
  // Current renderer supports header buttons, stat buttons, ribbon, and chatter.
  stats.unsupported = 0;
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

function formatFieldValue(value: unknown) {
  if (value === null || value === undefined || value === false) return '-';
  if (Array.isArray(value)) {
    if (value.length === 2 && typeof value[0] === 'number' && typeof value[1] === 'string') {
      return String(value[1] || `#${value[0]}`);
    }
    return value.map((item) => String(item ?? '')).filter(Boolean).join(', ') || '-';
  }
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return '[object]';
    }
  }
  return String(value);
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
    error.value = {
      message: 'Permission denied',
      code: 403,
      hint: 'Check access rights.',
      reasonCode: 'PERMISSION_DENIED',
      errorCategory: 'permission',
      suggestedAction: 'request_access',
      details: {
        intent: 'execute_button',
        model: model.value || '',
        op: 'execute',
      },
    };
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
    setError(err, pageText('error_execute_button', 'failed to execute button'));
    status.value = 'error';
    lastLatencyMs.value = Date.now() - startedAt;
    actionFeedback.value = {
      message: pageText('action_feedback_failed', '操作失败'),
      reasonCode: 'EXECUTE_FAILED',
      success: false,
    };
  } finally {
    executing.value = null;
  }
}

async function runStatButton(btn: ViewButton) {
  await runHeaderButton(btn);
}

async function applyButtonEffect(effect: ButtonEffect) {
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
    const target = effect.target as ButtonEffectTarget;
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
      setError(err, pageText('error_save_record', 'failed to save record'));
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

async function executeHeaderAction(actionKey: string) {
  const handled = await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: resolveCarryQuery(),
    onRefresh: reload,
    onFallback: async (key) => {
      if (key === 'open_my_work') {
        await router.push({ path: '/my-work', query: resolveCarryQuery() });
        return true;
      }
      if (key === 'open_risk_dashboard') {
        await router.push({ path: '/s/projects.dashboard', query: resolveCarryQuery() });
        return true;
      }
      if (key === 'refresh_page' || key === 'refresh') {
        reload();
        return true;
      }
      return false;
    },
  });
  if (!handled) {
    actionFeedback.value = {
      message: pageText('error_fallback', 'Record load failed'),
      reasonCode: 'ACTION_UNSUPPORTED',
      success: false,
    };
  }
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

.readonly-hint {
  margin-top: 6px;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 6px 10px;
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

.record-l1 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.l1-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px;
  background: #f8fafc;
}

.l1-label {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}

.l1-value {
  margin: 6px 0 0;
  color: #0f172a;
  font-size: 13px;
  font-weight: 600;
}

.record-next {
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  padding: 10px;
  background: #fff;
}

.next-label {
  margin: 0;
  font-size: 12px;
  color: #334155;
  font-weight: 700;
}

.next-actions {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
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

.fallback-fields {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px;
  background: #f8fafc;
}

.fallback-fields ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 8px;
}

.fallback-fields li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.fallback-label {
  color: #334155;
  font-weight: 600;
}

.fallback-value {
  color: #0f172a;
  text-align: right;
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
