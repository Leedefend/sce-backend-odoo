<template>
  <section class="page sc-page sc-product-workspace-stack" data-product-page-mode="detail">
    <!-- Page intent: surface record status, risks, metrics, and next actions. -->
    <header class="header sc-product-page-header">
      <div>
        <h2>{{ title }}</h2>
        <p class="meta">{{ subtitle }}</p>
        <p v-if="readonlyHint" class="meta readonly-hint">{{ readonlyHint }}</p>
        <p v-if="actionFeedback" class="meta action-feedback" :class="{ error: !actionFeedback.success }">
          {{ actionFeedback.message }} <span v-if="!actionFeedback.success && actionFeedback.reasonCode" class="code">({{ actionFeedbackReasonLabel(actionFeedback.reasonCode) }})</span>
        </p>
      </div>
      <div class="actions sc-product-primary-actions">
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
        <button class="ghost" @click="goBack">{{ pageText('action_back', '返回') }}</button>
        <button v-if="status === 'ok' && canEdit" @click="startEdit">{{ pageText('action_edit', '编辑') }}</button>
        <button v-if="status === 'editing'" :disabled="isSaveDisabled" @click="save">{{ pageText('action_save', '保存') }}</button>
        <button v-if="status === 'editing'" class="ghost" @click="cancelEdit">{{ pageText('action_cancel', '取消') }}</button>
        <button class="ghost" :disabled="status === 'loading' || status === 'saving'" @click="reload">{{ pageText('action_reload', '刷新') }}</button>
      </div>
    </header>

    <StatusPanel v-if="status === 'loading'" :title="pageText('loading_title', '正在加载记录')" variant="info" />
    <StatusPanel v-else-if="status === 'saving'" :title="pageText('saving_title', '正在保存记录')" variant="info" />
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
      :title="pageText('view_node_unsupported_title', '页面结构暂不支持')"
      :message="pageText('view_node_unsupported_message', '当前页面结构包含暂不支持的展示节点，请联系管理员完善页面配置。')"
      error-code="VIEW_NODE_UNSUPPORTED"
      variant="error"
      :on-retry="reload"
    />

    <section v-else class="card sc-product-main-surface" :class="{ editing: status === 'editing' }">
      <div v-if="pageSectionEnabled('save_banner', true) && pageSectionTagIs('save_banner', 'div') && editTxState === 'saved'" class="banner success" :style="pageSectionStyle('save_banner')">
        {{ pageText('banner_saved', '已保存，变更已生效。') }}
      </div>
      <section v-if="pageSectionEnabled('project_summary', true) && pageSectionTagIs('project_summary', 'section') && showProjectSummary" class="record-l1" :style="pageSectionStyle('project_summary')">
        <article class="l1-card">
          <p class="l1-label">{{ pageText('summary_status_stage', '记录状态与阶段') }}</p>
          <p class="l1-value">{{ projectStatusSummary }}</p>
        </article>
        <article class="l1-card">
          <p class="l1-label">{{ pageText('summary_risk', '关键风险摘要') }}</p>
          <p class="l1-value">{{ projectRiskSummary }}</p>
        </article>
        <article class="l1-card">
          <p class="l1-label">{{ pageText('summary_finance', '关键指标摘要') }}</p>
          <p class="l1-value">{{ projectFinanceSummary }}</p>
        </article>
      </section>
      <section v-if="pageSectionEnabled('next_actions', true) && pageSectionTagIs('next_actions', 'section') && showProjectSummary" class="record-next" :style="pageSectionStyle('next_actions')">
        <p class="next-label">{{ pageText('next_actions_title', '下一步动作') }}</p>
        <div class="next-actions">
          <button class="ghost" @click="openProjectAction('/my-work', { section: 'todo', search: '待办' })">{{ pageText('next_action_todo', '查看待办') }}</button>
          <button class="ghost" @click="openProjectAction('/my-work', { section: 'todo', search: '风险' })">{{ pageText('next_action_risk', '查看风险') }}</button>
          <button class="ghost" @click="openProjectAction('/my-work', { section: 'todo', search: '业务' })">{{ pageText('next_action_contract', '查看业务记录') }}</button>
          <button class="ghost" @click="openProjectAction('/my-work', { section: 'todo', search: '执行' })">{{ pageText('next_action_cost', '查看执行分析') }}</button>
        </div>
      </section>
      <div v-if="ribbon" class="ribbon">{{ ribbon.title || pageText('ribbon_fallback', '状态标记') }}</div>
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
        <h3>{{ pageText('fallback_details_title', '记录详情') }}</h3>
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
                @click="openAttachment(entry.attachment)"
              >
                {{ pageText('action_view_attachment', '查看') }}
              </button>
            </div>
          </li>
        </ul>
      </section>
    </section>

    <DevContextPanel
      :visible="showHud && pageSectionEnabled('dev_context', true) && pageSectionTagIs('dev_context', 'div')"
      :style="pageSectionStyle('dev_context')"
      :title="pageText('dev_context_title', '记录上下文')"
      :entries="hudEntries"
    />
    <AttachmentViewer ref="attachmentViewerRef" />
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ApiError } from '../api/client';
import { executeButton } from '../api/executeButton';
import { fetchChatterTimeline, postChatterMessage, type ChatterTimelineEntry } from '../api/chatter';
import { fileToBase64, uploadFile } from '../api/files';
import { loadActionContractRaw } from '../api/contract';
import { buildRecordRuntimeFromContract } from '../app/contractRecordRuntime';
import { readRecordDiagnosticsRaw, writeRecordDiagnosticsRaw } from '../app/runtime/recordDiagnosticsDataRuntime';
import { deriveRecordStatus } from '../app/view_state';
import type { ButtonEffect, ButtonEffectTarget, ViewButton, ViewContract } from '@sc/schema';
import ViewLayoutRenderer from '../components/view/ViewLayoutRenderer.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import StatusPanel from '../components/StatusPanel.vue';
import AttachmentViewer from '../components/attachment/AttachmentViewer.vue';
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
import { buildEntryTargetRouteTarget } from '../app/routeQuery';
import { findActionMetaByMenu } from '../app/menu';

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
const attachmentViewerRef = ref<InstanceType<typeof AttachmentViewer> | null>(null);
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
const title = computed(() => recordTitle.value || `记录 ${recordId.value}`);
const subtitle = computed(() => (
  status.value === 'editing'
    ? pageText('subtitle_editing', '正在编辑记录字段')
    : pageText('subtitle_ready', '记录详情')
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
    ? `${pageText('project_output_prefix', '指标 ')}${output}`
    : pageText('project_output_unset', '指标未配置');
  const payText = Number.isFinite(pay) && pay > 0
    ? `${pageText('project_pay_prefix', '完成比 ')}${pay}${pageText('project_pay_suffix', '%')}`
    : pageText('project_pay_unset', '完成比未配置');
  return `${outputText} · ${payText}`;
});
const canEdit = computed(() => contractWriteAllowed.value);
const readonlyHint = computed(() => {
  if (canEdit.value) return '';
  const level = String(session.productFacts.license?.level || '').trim();
  const bundle = String(session.productFacts.bundle?.name || '').trim();
  if (level && level !== 'enterprise') {
    const bundleSegment = bundle ? `${pageText('readonly_hint_license_bundle_sep', '，套餐：')}${bundle}` : '';
    return `${pageText('readonly_hint_license_prefix', '当前为只读模式（授权级别：')}${level}${bundleSegment}${pageText('readonly_hint_license_suffix', '）。如需编辑权限请联系管理员。')}`;
  }
  return pageText('readonly_hint_default', '当前记录处于只读模式，请联系管理员开通写权限。');
});
const actionContext = computed(() => {
  const fromQuery = Number(route.query.action_id || 0);
  if (Number.isFinite(fromQuery) && fromQuery > 0) return { id: fromQuery, source: 'query' as const };
  const menuId = toPositiveInt(route.query.menu_id);
  const menuAction = menuId ? findActionMetaByMenu(session.menuTree, menuId) : null;
  const fromMenu = Number(menuAction?.action_id || 0);
  if (Number.isFinite(fromMenu) && fromMenu > 0) {
    const menuModel = String(menuAction?.model || '').trim();
    if (!menuModel || menuModel === model.value) {
      return { id: fromMenu, source: 'menu' as const };
    }
  }
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
function toPositiveInt(value: unknown): number {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
}
const requestedViewId = computed(() => (
  toPositiveInt(route.query.view_id) || toPositiveInt(route.query.viewId) || 0
));
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
const PROJECT_CONTEXT_CHANGED_EVENT = 'sc:project-context-changed';
const pageContract = usePageContract('record');
const pageText = pageContract.text;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const statusLabel = computed(() => {
  if (status.value === 'editing') return pageText('status_editing', '编辑中');
  if (status.value === 'saving') return pageText('status_saving', '保存中');
  if (status.value === 'loading') return pageText('status_loading', '加载中');
  if (status.value === 'error') return pageText('status_error', '异常');
  if (status.value === 'empty') return pageText('status_empty', '无数据');
  return pageText('status_ready', '就绪');
});
const headerActions = computed(() => pageGlobalActions.value);
const statusTone = computed(() => {
  if (status.value === 'error') return 'danger';
  if (status.value === 'editing' || status.value === 'saving') return 'warn';
  return 'ok';
});
const errorCopy = computed(() => resolveErrorCopy(error.value, pageText('error_fallback', '记录加载失败')));
const emptyCopy = computed(() => resolveEmptyCopy('record'));
const renderMode = computed(() => 'layout_tree');

function actionFeedbackReasonLabel(reason: unknown) {
  const raw = String(reason || '').trim();
  const key = raw.toUpperCase();
  const mapping: Record<string, string> = {
    ACTION_UNSUPPORTED: pageText('reason_action_unsupported', '暂不支持此操作'),
    EXECUTE_FAILED: pageText('reason_execute_failed', '操作未完成'),
    PERMISSION_DENIED: pageText('reason_permission_denied', '权限不足'),
    NOT_FOUND: pageText('reason_not_found', '记录不存在'),
    BUSINESS_RULE_FAILED: pageText('reason_business_rule_failed', '业务规则限制'),
    MISSING_PARAMS: pageText('reason_missing_params', '参数不完整'),
    NETWORK_ERROR: pageText('reason_network_error', '网络异常'),
    SYSTEM_ERROR: pageText('reason_system_error', '系统异常'),
  };
  if (!raw) return pageText('reason_unknown', '待确认');
  return mapping[key] || raw.replace(/[_-]+/g, ' ').toLowerCase().replace(/(^|\s)\S/g, (s) => s.toUpperCase());
}

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
  { label: '业务对象', value: model.value },
  { label: '记录编号', value: recordId.value },
  { label: '页面状态', value: status.value },
  { label: '入口来源', value: actionContext.value.source },
  { label: '渲染模式', value: renderMode.value },
  { label: '布局已加载', value: Boolean(viewContract.value?.layout) },
  { label: '布局节点', value: layoutStatsText.value },
  { label: '未支持节点', value: missingNodes.value.join('、') || '-' },
  { label: '已覆盖能力', value: supportedNodes.join('、') },
  { label: '最近意图', value: lastIntent.value || '-' },
  { label: '写入模式', value: lastWriteMode.value || '-' },
  { label: '处理编号', value: traceId.value || lastTraceId.value || '-' },
  { label: '配置模式', value: contractMode.value || '-' },
  { label: '请求界面', value: requestedSurface.value },
  { label: '来源模式', value: requestedSourceMode.value },
  { label: '允许写入', value: contractWriteAllowed.value },
  { label: '耗时', value: lastLatencyMs.value ?? '-' },
  { label: '当前路由', value: route.fullPath },
]);
const layoutStatsText = computed(() => {
  const stats = layoutStats.value;
  return [
    `分组 ${stats.group}`,
    `字段 ${stats.field}`,
    `页签 ${stats.notebook + stats.page}`,
    `未支持 ${stats.unsupported}`,
  ].join('；');
});

function resolveCarryQuery(extra?: Record<string, unknown>) {
  return pickContractNavQuery(route.query as Record<string, unknown>, extra);
}

function resolveButtonActionQuery(result: object | null | undefined, extra?: Record<string, unknown>) {
  const payload = (result && typeof result === 'object' && !Array.isArray(result))
    ? result as Record<string, unknown>
    : {};
  return resolveCarryQuery({
    action_id: payload.action_id,
    domain_raw: payload.domain_raw,
    context_raw: payload.context_raw,
    ...(extra || {}),
  });
}

function openProjectAction(path: string, query?: Record<string, string>) {
  router.push({ path, query: query || undefined }).catch(() => {});
}

function buttonState(btn: ViewButton) {
  const raw = btn as ViewButton & { disabled?: boolean };
  if (raw.disabled === true) {
    return { state: 'disabled_permission' as const, missing: [] };
  }
  return evaluateCapabilityPolicy({
    source: btn,
    available: session.capabilities,
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
      ? `${pageText('missing_capability_license_prefix', '；当前授权级别：')}${level}`
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
    setError(new Error(pageText('error_missing_record_context', '缺少记录上下文')), pageText('error_missing_record_context', '缺少记录上下文'));
    status.value = deriveRecordStatus({ error: error.value?.message || '', fieldsLength: 0 });
    return;
  }

  try {
    if (!actionId.value) {
      throw new Error(pageText('error_missing_action_context', '缺少页面动作上下文'));
    }
    const actionContract = await loadActionContractRaw(actionId.value, {
      viewId: requestedViewId.value || undefined,
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
        throw new Error(`${pageText('error_surface_marker_invalid', '页面契约标记不一致')}：${markerCheck.issues.slice(0, 4).join(' | ')}`);
      }
      const runtime = buildRecordRuntimeFromContract(actionContract.data);
      view = runtime.view;
      contractFieldNames = runtime.fieldNames;
      contractWriteAllowed.value = runtime.rights.write;
    }
    contractMode.value = String(actionContract?.meta?.contract_mode || '');
    if (!view) {
      throw new Error(pageText('error_missing_form_contract', '缺少表单页面契约'));
    }
    viewContract.value = view || null;
    const layout = view?.layout;
    if (!layout) {
      setError(new Error(pageText('error_missing_view_layout', '缺少页面布局配置')), pageText('error_missing_view_layout', '缺少页面布局配置'));
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
    const read = await readRecordDiagnosticsRaw({
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
    setError(err, pageText('error_load_record', '记录加载失败'));
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
    chatterError.value = err instanceof Error ? err.message : pageText('chatter_load_failed', '协作记录加载失败');
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
    chatterError.value = err instanceof Error ? err.message : pageText('chatter_post_failed', '评论发布失败');
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
    chatterUploadError.value = err instanceof Error ? err.message : pageText('chatter_upload_failed', '附件上传失败');
  } finally {
    chatterUploading.value = false;
    input.value = '';
  }
}

async function openAttachment(att: { id?: number; name?: string; mimetype?: string }) {
  if (!att?.id) return;
  try {
    await attachmentViewerRef.value?.open({ id: Number(att.id) }, att.name);
  } catch (err) {
    chatterUploadError.value = err instanceof Error ? err.message : pageText('chatter_download_failed', '附件下载失败');
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
  return raw.filter((btn) => {
    if (!btn || typeof btn !== 'object') return false;
    return (btn as { visible?: unknown }).visible !== false;
  }) as ViewButton[];
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
    return '多项内容';
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
      message: '权限不足',
      code: 403,
      hint: '请核对当前角色的访问权限。',
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
    } else if (response?.result?.entry_target) {
      await router.push(buildEntryTargetRouteTarget(response.result.entry_target, {
        query: resolveButtonActionQuery(response.result),
        actionId: response.result.action_id,
      }) as never);
    } else if (response?.result?.action_id) {
      await router.push({
        name: 'action',
        params: { actionId: response.result.action_id },
        query: resolveButtonActionQuery(response.result, { action_id: response.result.action_id }),
      });
    }
    actionFeedback.value = parseExecuteResult(response);
  } catch (err) {
    setError(err, pageText('error_execute_button', '操作执行失败'));
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
    if (target.kind === 'entry_target' && target.entry_target) {
      await router.push(buildEntryTargetRouteTarget(target.entry_target, {
        query: resolveButtonActionQuery(target),
      }) as never);
      return;
    }
    if (target.kind === 'action' && target.action_id) {
      await router.push({
        name: 'action',
        params: { actionId: target.action_id },
        query: resolveButtonActionQuery(target, { action_id: target.action_id }),
      });
      return;
    }
    if (target.kind === 'url' && target.url) {
      window.open(target.url, '_blank');
    }
    return;
  }
  if (effect.type === 'toast' && effect.message) {
    actionFeedback.value = {
      message: String(effect.message),
      reasonCode: 'ACTION_COMPLETED',
      success: true,
    };
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
      return writeRecordDiagnosticsRaw({
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
      setError(err, pageText('error_record_changed', '记录已被更新，请刷新后重试'));
    } else {
      setError(err, pageText('error_save_record', '记录保存失败'));
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
        await router.push({ path: '/my-work', query: resolveCarryQuery({ section: 'todo', search: '风险' }) });
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
      message: pageText('error_fallback', '记录加载失败'),
      reasonCode: 'ACTION_UNSUPPORTED',
      success: false,
    };
  }
}

onMounted(() => {
  void load();
  if (typeof window !== 'undefined') {
    window.addEventListener(PROJECT_CONTEXT_CHANGED_EVENT, handleProjectContextChanged);
  }
});

watch(
  () => `${String(route.params.model || '')}|${String(route.params.id || '')}|${String(route.query.action_id || '')}|${String(route.query.view_id || '')}|${String(route.query.viewId || '')}`,
  () => {
    void load();
  },
);

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener(PROJECT_CONTEXT_CHANGED_EVENT, handleProjectContextChanged);
  }
});

function handleProjectContextChanged(): void {
  void load();
}
</script>

<style scoped>
.page {
  display: grid;
  gap: var(--sc-product-workspace-stack-gap);
  color: var(--sc-app-text-primary);
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
  color: var(--sc-semantic-text-muted);
  font-size: 14px;
}

.readonly-hint {
  margin-top: 6px;
  color: var(--sc-app-warning-text);
  background: var(--sc-app-warning-bg);
  border: 1px solid var(--sc-app-warning-border);
  border-radius: var(--sc-component-panel-radius);
  padding: 6px 10px;
}

.action-feedback {
  margin-top: 6px;
  color: var(--sc-app-success-text);
}

.action-feedback.error {
  color: var(--sc-app-danger-text);
}

.action-feedback .code {
  color: var(--sc-semantic-text-muted);
}

.pill {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  background: var(--sc-app-subtle-bg);
  color: var(--sc-app-text-secondary);
}

.pill.ok {
  background: var(--sc-app-success-bg);
  color: var(--sc-app-success-text);
}

.pill.warn {
  background: var(--sc-app-warning-bg);
  color: var(--sc-app-warning-text);
}

.pill.danger {
  background: var(--sc-app-danger-bg);
  color: var(--sc-app-danger-text);
}

.card {
  background: var(--sc-app-panel);
  border-radius: var(--sc-component-panel-radius);
  padding: 24px;
  box-shadow: var(--sc-app-shadow);
  display: grid;
  gap: 12px;
}

.card.editing {
  border: 1px dashed var(--sc-app-border-strong);
  box-shadow: var(--sc-semantic-shadow-modal);
}

.record-l1 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.l1-card {
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-panel-radius);
  padding: 10px;
  background: var(--sc-app-muted-bg);
}

.l1-label {
  margin: 0;
  color: var(--sc-semantic-text-muted);
  font-size: 12px;
}

.l1-value {
  margin: 6px 0 0;
  color: var(--sc-app-text-primary);
  font-size: 13px;
  font-weight: 600;
}

.record-next {
  border: 1px dashed var(--sc-app-border-strong);
  border-radius: var(--sc-component-panel-radius);
  padding: 10px;
  background: var(--sc-app-panel);
}

.next-label {
  margin: 0;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
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
  border-bottom: 1px solid var(--sc-app-border);
}

.label {
  font-weight: 600;
  color: var(--sc-app-text-secondary);
}

.value {
  color: var(--sc-app-text-primary);
}

.input {
  width: 100%;
  padding: 8px 10px;
  border-radius: var(--sc-component-input-radius);
  border: 1px solid var(--sc-app-border-strong);
  font-size: 14px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
}

.banner {
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
}

.banner.success {
  background: var(--sc-app-info-bg);
  border: 1px solid var(--sc-app-info-border);
  color: var(--sc-app-info-text);
}

.ribbon {
  align-self: start;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--sc-app-danger-bg);
  color: var(--sc-app-danger-text);
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
  border-radius: var(--sc-component-panel-radius);
  border: 1px solid var(--sc-app-border);
  background: var(--sc-app-muted-bg);
  color: var(--sc-app-text-primary);
  cursor: pointer;
}

.stat-label {
  font-weight: 600;
}

.stat-value {
  font-size: 18px;
}

.fallback-fields {
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-panel-radius);
  padding: 12px;
  background: var(--sc-app-muted-bg);
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
  color: var(--sc-app-text-secondary);
  font-weight: 600;
}

.fallback-value {
  color: var(--sc-app-text-primary);
  text-align: right;
}

.chatter {
  margin-top: 16px;
  padding: 16px;
  border-radius: var(--sc-component-panel-radius);
  border: 1px dashed var(--sc-app-border-strong);
  background: var(--sc-app-muted-bg);
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
  border-radius: var(--sc-component-panel-radius);
  border: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
  display: grid;
  gap: 4px;
}

.chatter-title {
  font-weight: 600;
}

.chatter-meta {
  font-size: 12px;
  color: var(--sc-semantic-text-muted);
}

.chatter-body {
  font-size: 13px;
  color: var(--sc-app-text-primary);
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
  border-radius: var(--sc-component-input-radius);
  border: 1px solid var(--sc-app-border-strong);
  padding: 10px;
  font-size: 13px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
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
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-panel);
  padding: 10px;
}

.timeline-type {
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 999px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 6px;
  align-self: start;
}

.timeline-type.type-message {
  color: var(--sc-app-info-text);
  background: var(--sc-app-info-bg);
  border-color: var(--sc-app-info-border);
}

.timeline-type.type-attachment {
  color: var(--sc-app-success-text);
  background: var(--sc-app-success-bg);
  border-color: var(--sc-app-success-border);
}

.timeline-type.type-audit {
  color: var(--sc-app-warning-text);
  background: var(--sc-app-warning-bg);
  border-color: var(--sc-app-warning-border);
}

.timeline-main {
  min-width: 0;
}
button {
  padding: 10px 14px;
  border: none;
  border-radius: var(--sc-component-button-radius);
  background: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
  cursor: pointer;
}

.ghost {
  background: transparent;
  color: var(--sc-app-text-primary);
  border: 1px solid var(--sc-app-border);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
