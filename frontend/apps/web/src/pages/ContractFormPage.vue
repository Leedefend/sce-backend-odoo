<template>
  <LayoutShell :flow="layoutShellFlow">
    <header v-if="effectiveCompactMode" class="form-compact-topbar">
      <div class="form-compact-title">
        <strong>{{ pageDisplayTitle }}</strong>
        <span v-if="pageDisplaySubtitle">{{ pageDisplaySubtitle }}</span>
      </div>
      <div class="form-compact-actions">
        <button
          v-if="!isProjectCreatePage"
          class="ghost"
          :disabled="busy"
          @click="goBackFromDetail"
        >
          返回
        </button>
        <button
          v-if="!isProjectCreatePage && !hasPrimaryHeaderAction"
          class="primary"
          :disabled="isQuickSubmitDisabled"
          :title="sceneWriteDisabledReason"
          @click="() => saveRecord()"
        >
          {{ submitButtonLabel }}
        </button>
      </div>
    </header>

    <PageHeaderTemplate
      v-else
      :title="pageDisplayTitle"
      :subtitle="pageDisplaySubtitle || undefined"
      :compact="nativeLikeFormSurface"
    >
      <template #meta>
        <p v-if="showHud" class="meta">model={{ model }} · id={{ recordIdDisplay }} · action={{ actionId || '-' }}</p>
        <p v-if="showHud && contractMetaLine" class="meta">{{ contractMetaLine }}</p>
      </template>
      <template #status>
        <template v-if="isProjectCreatePage">
          <p class="header-status-item">当前进度：{{ intakeRequiredSummary }}</p>
          <p class="header-status-item" :class="{ 'header-status-item--danger': intakeMissingSummary !== '无' }">缺少：{{ intakeMissingSummary }}</p>
        </template>
      </template>
      <template #actions>
        <button
          v-if="!isProjectCreatePage"
          class="ghost"
          :disabled="busy"
          @click="goBackFromDetail"
        >
          返回
        </button>
        <button
          v-if="!isProjectCreatePage && !hasPrimaryHeaderAction"
          class="primary"
          :disabled="isQuickSubmitDisabled"
          :title="sceneWriteDisabledReason"
          @click="() => saveRecord()"
        >
          {{ submitButtonLabel }}
        </button>
        <button
          v-if="enterpriseNextActionVisible"
          class="ghost"
          :disabled="busy || !enterpriseNextActionTarget"
          @click="openEnterpriseNextAction"
        >
          {{ enterpriseNextActionLabel }}
        </button>
        <button v-if="showDebugActionsVisible && !isProjectCreatePage" class="ghost" :disabled="busy || !contract" @click="copyContractJson">复制契约</button>
        <button v-if="showDebugActionsVisible && !isProjectCreatePage" class="ghost" :disabled="busy || !contract" @click="exportContractJson">导出契约</button>
        <button v-if="showDebugActionsVisible && !isProjectCreatePage" class="ghost" :disabled="busy" @click="reload">重新加载</button>
      </template>
    </PageHeaderTemplate>

    <StatusPanel v-if="status === 'loading'" title="正在加载页面..." variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
      title="页面加载失败"
      :message="errorMessage"
      hint="请稍后重试；若持续失败请联系管理员。"
      variant="error"
      :on-retry="reload"
      retry-label="重新加载"
    />
    <section v-else-if="showFormNativeFallback" class="card">
      <StatusPanel title="当前表单建议使用原生页面" :message="formNativeFallbackMessage" variant="info" />
      <button class="primary" @click="openFormNativeFallback">打开原生页面</button>
    </section>

    <section
      v-else
      :class="['card', {
        'card--flow': isProjectCreatePage,
        'card--compact': effectiveCompactMode,
        'card--project-align': nativeLikeFormSurface,
      }]"
    >
      <section v-if="showPageOverviewStrip" class="page-overview-strip">
        <div v-for="item in pageOverviewItems" :key="item.label" class="page-overview-pill">
          <span class="page-overview-pill__label">{{ item.label }}</span>
          <strong class="page-overview-pill__value">{{ item.value }}</strong>
        </div>
      </section>
      <DetailCommandBar
        v-if="showCommandBar"
        :steps="statusbarSteps"
        :actions="contractActionStrip"
        :busy="busy"
        :native-like="nativeLikeFormSurface"
        @run-action="runAction"
      />
      <StatusPanel
        v-if="sceneRuntimeStatusPanel"
        :title="sceneRuntimeStatusPanel.title"
        :message="sceneRuntimeStatusPanel.message"
        :hint="sceneRuntimeStatusPanel.hint"
        variant="info"
      />
      <section v-if="showContractWarnings" class="block warn">
        <h3>提示信息</h3>
        <ul>
          <li v-for="item in warnings" :key="item">{{ item }}</li>
        </ul>
      </section>
      <section v-if="showStrictContractGuard" class="block contract-missing-block">
        <h3>契约缺口提示</h3>
        <p class="contract-missing-summary">{{ strictContractMissingSummary }}</p>
        <p v-if="strictContractDefaultsSummary" class="contract-missing-defaults">{{ strictContractDefaultsSummary }}</p>
      </section>

      <section v-if="showWorkflowTransitions" class="block">
        <h3>流程操作</h3>
        <div class="chips">
          <button
            v-for="item in workflowTransitions"
            :key="item.key"
            class="chip-btn"
            :disabled="busy || !item.action"
            :title="item.notes || ''"
            @click="item.action && runAction(item.action)"
          >
            {{ item.label }}
          </button>
        </div>
      </section>

      <section v-if="showInlineSearchFilters" class="block">
        <h3>快捷筛选</h3>
        <div class="chips">
          <button
            v-for="item in searchFilters"
            :key="`flt-${item.key}`"
            class="chip-btn"
            :class="{ active: activeFilterKey === item.key }"
            :disabled="busy || !item.key"
            @click="openFilter(item.key)"
          >
            {{ item.label }}
          </button>
        </div>
      </section>

      <section :class="['form-grid', { 'form-grid--project-align': nativeLikeFormSurface }]">
        <section v-if="showStructureProjectionSummary" class="block zone-block structure-projection-block">
          <h3>结构投影摘要</h3>
          <p class="zone-collaboration-line">shell 数：{{ structureProjectionSummary.shellCount }}，section 数：{{ structureProjectionSummary.sectionCount }}，tab 数：{{ structureProjectionSummary.tabCount }}</p>
          <p class="zone-collaboration-line">shell 标题：{{ structureProjectionSummary.shellTitles || '（空）' }}</p>
          <p class="zone-collaboration-line">contract 输入（views.form.layout）：notebook={{ contractTabAuditSummary.source_layout.notebook }}，page={{ contractTabAuditSummary.source_layout.page }}</p>
          <p class="zone-collaboration-line">contract 输入（semantic layout）：notebook={{ contractTabAuditSummary.semantic_layout.notebook }}，page={{ contractTabAuditSummary.semantic_layout.page }}</p>
          <p class="zone-collaboration-line">pipeline(layout_tree)：notebook={{ contractTabAuditSummary.layout_tree.notebook }}，page={{ contractTabAuditSummary.layout_tree.page }}</p>
          <p class="zone-collaboration-line">pipeline(detail_shell_raw)：shell={{ contractTabAuditSummary.detail_shell_raw.shell }}，tab={{ contractTabAuditSummary.detail_shell_raw.tab }}</p>
          <p class="zone-collaboration-line">消费真值源：{{ contractTabAuditSummary.single_source }}（semantic 仅观测，不参与投影）</p>
          <p class="zone-collaboration-line">投影对账：projected tabs={{ contractTabAuditSummary.projected_tabs }}，delta(layout-page - projected)={{ contractTabAuditSummary.delta_from_layout_page }}</p>
        </section>
        <div v-if="isProjectCreatePage" class="form-flow-guide">
          <p class="form-flow-guide-main">只需完成核心信息即可创建项目</p>
        </div>
        <StatusPanel
          v-if="sceneValidationPanel"
          title="表单校验失败"
          :message="sceneValidationPanel.message"
          :error-code="sceneValidationPanel.code"
          :reason-code="sceneValidationPanel.code"
          :hint="sceneValidationPanel.hint"
          :suggested-action="sceneValidationPanel.suggestedAction"
          variant="error"
        />
        <p v-if="nonSceneValidationErrors.length" class="validation-error">
          {{ nonSceneValidationErrors.join('；') }}
        </p>
        <p v-if="onchangeWarnings.length" class="validation-warn">
          {{ onchangeWarnings.map((item) => item.message || item.title || '').filter(Boolean).join('；') }}
        </p>
        <p v-if="submissionFeedback" class="submission-feedback" :class="`submission-feedback--${submissionFeedback.kind}`">
          {{ submissionFeedback.message }}
        </p>
        <p v-if="visibleFieldNodeCount === 0" class="validation-warn">
          当前页面暂无可显示字段，请检查契约可见字段与角色权限配置。
        </p>
        <DetailShellLayout
          v-if="showDetailShellZone"
          :shells="normalizedDetailShells"
          :busy="busy"
          :is-project-create-page="isProjectCreatePage"
          :native-like="nativeLikeFormSurface"
          :advanced-expanded="advancedExpanded"
          :relation-fallback-adapter="relationFallbackAdapter"
          @field-change="onTemplateFieldChange"
          @toggle-advanced="advancedExpanded = !advancedExpanded"
        />
        <StatusPanel
          v-else
          title="当前表单语义未开放详情区"
          message="semantic_page 未声明 detail_zone，已按契约隐藏详情布局。"
          variant="info"
        />
        <section v-if="showRelationZoneBlock" class="block zone-block">
          <h3>关联数据</h3>
          <div class="zone-chip-list">
            <span v-for="item in semanticRelationZoneItems" :key="item.field" class="zone-chip">
              {{ item.label }} · {{ item.viewType }} · {{ item.editableLabel }}
            </span>
          </div>
        </section>
        <section v-if="showCollaborationZoneBlock" class="block zone-block">
          <h3>协作区</h3>
          <p class="zone-collaboration-line">讨论区：{{ semanticHasChatter ? '已启用' : '未启用' }}</p>
          <p class="zone-collaboration-line">附件区：{{ semanticHasAttachments ? '已启用' : '未启用' }}</p>
        </section>
        <div v-if="hasAdvancedFields && !isProjectCreatePage && !nativeLikeFormSurface" class="layout-divider advanced-toggle">
          <button class="chip-btn" :disabled="busy" @click="advancedExpanded = !advancedExpanded">
            {{ advancedExpanded ? '收起高级信息' : '展开高级信息' }}
          </button>
        </div>

      </section>

      <PageFooterTemplate v-if="isProjectCreatePage" hint="填写完成后点击“创建项目”">
        <template #default>
          <button class="ghost" :disabled="busy" @click="cancelIntake">取消</button>
          <button class="primary" :disabled="isIntakeCreateDisabled" :title="sceneWriteDisabledReason" @click="() => saveRecord()">
            {{ intakeCreateButtonLabel }}
          </button>
        </template>
      </PageFooterTemplate>

      <section v-if="showBodyActionStrip" class="block">
        <h3>可执行操作</h3>
        <div class="chips">
          <button
            v-for="action in bodyActions"
            :key="`body-${action.key}`"
            class="chip-btn"
            :disabled="busy || !action.enabled"
            :title="action.hint"
            @click="runAction(action)"
          >
            {{ action.label }}<template v-if="showHud"> · {{ action.kind }}</template>
          </button>
        </div>
      </section>
    </section>

    <DevContextPanel
      :visible="showHud"
      title="表单上下文"
      :entries="hudEntries"
    />
  </LayoutShell>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch, watchEffect } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import FieldValue from '../components/FieldValue.vue';
import StatusPanel from '../components/StatusPanel.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import LayoutShell from '../components/template/LayoutShell.vue';
import PageHeaderTemplate from '../components/template/PageHeader.vue';
import PageFooterTemplate from '../components/template/PageFooter.vue';
import DetailCommandBar from '../components/template/DetailCommandBar.vue';
import DetailShellLayout from '../components/template/DetailShellLayout.vue';
import type { FormSectionFieldSchema, FormSectionFieldChange } from '../components/template/formSection.types';
import type { RelationFallbackAdapter } from '../components/template/relationFallback.types';
import type { DetailShellView, DetailStatusbarStep, DetailSectionView } from '../components/template/detailLayout.types';
import { createFormSectionFieldSchemaBuilder } from '../components/template/formSection.adapter';
import { resolveInputPlaceholder, resolveSelectPlaceholder } from '../components/template/placeholder.mapper';
import { resolveFieldSpanClass } from '../components/template/fieldSpan.mapper';
import { mapDescriptorSelectionOptions, mapRelationOptions } from '../components/template/option.mapper';
import { createRelationFallbackAdapter } from '../components/template/relationFallback.adapter';
import { dispatchTemplateFieldChange } from '../components/template/fieldChange.dispatcher';
import { isHudEnabled } from '../config/debug';
import { loadActionContractRaw, loadModelContractRaw } from '../api/contract';
import { createRecord, listRecords, readRecord, writeRecord } from '../api/data';
import { ApiError } from '../api/client';
import { executeButton } from '../api/executeButton';
import { triggerOnchange } from '../api/onchange';
import type { OnchangeLinePatch } from '../api/onchange';
import type { ActionContract, FieldDescriptor } from '@sc/schema';
import { useSessionStore } from '../stores/session';
import { ErrorCodes } from '../app/error_codes';
import {
  detectObjectMethodFromActionKey,
  normalizeActionKind,
  parseMaybeJsonRecord,
  toPositiveInt,
} from '../app/contractRuntime';
import { validateContractFormData } from '../app/contractValidation';
import { resolveActionIdFromContext } from '../app/actionContext';
import { pickContractNavQuery } from '../app/navigationContext';
import { readWorkspaceContext } from '../app/workspaceContext';
import { collectPolicyValidationErrors, evaluateActionPolicy, evaluateFieldPolicy } from '../app/contractPolicies';
import { buildRuntimeFieldStates } from '../app/modifierEngine';
import { buildOne2ManyInlineCommands, buildX2ManyCommands, extractX2ManyIds } from '../app/x2manyCommands';
import { resolveSceneValidationSuggestedAction } from '../app/sceneValidationRecoveryStrategy';
import { findSceneReadyEntry, resolveFormSceneReady } from '../app/resolvers/sceneReadyResolver';
import { normalizeSceneActionProtocol } from '../app/sceneActionProtocol';
import { executeProjectionRefresh } from '../app/projectionRefreshRuntime';
import { normalizeRenderProfile } from '../app/pageContract';
import {
  buildDetailShellViewsFromTree,
  type LayoutNodeView,
  type LayoutTreeSectionView,
} from '../app/runtime/detailLayoutRuntime';
import { executeSceneMutation } from '../app/sceneMutationRuntime';
import { isCoreSceneStrictMode } from '../app/contractStrictMode';
import { buildNativeFallbackUrl, resolveContractViewRenderPolicy } from '../app/contractTakeover';
import { PROJECT_INTAKE_SCENE_KEY, setPendingProjectContext } from '../app/projectCreationBaseline';

type UiStatus = 'loading' | 'ok' | 'error';
type BusyKind = 'save' | 'action' | null;
const MANY2ONE_CREATE_OPTION = '__create__';

type ContractAction = {
  key: string;
  label: string;
  kind: string;
  level: string;
  actionId: number | null;
  methodName: string;
  targetModel: string;
  context: Record<string, unknown>;
  domainRaw: string;
  target: string;
  url: string;
  enabled: boolean;
  hint: string;
  semantic: string;
  buttonType?: string;
  order?: number;
  visibleProfiles: Array<'create' | 'edit' | 'readonly'>;
  mutation?: {
    type: string;
    model: string;
    operation: string;
    payload_schema?: Record<string, unknown>;
  };
  refreshPolicy?: {
    on_success: string[];
    on_failure?: string[];
    mode?: string;
    scope?: string;
    debounce_ms?: number;
  };
};

type LayoutNode = LayoutNodeView & {
  descriptor?: FieldDescriptor;
  groupsXmlids?: string[];
};

type LayoutTreeSection = LayoutTreeSectionView & {
  groupsXmlids?: string[];
};

type RelationOption = {
  id: number;
  label: string;
};

type One2ManyInlineRow = {
  key: string;
  id: number | null;
  isNew: boolean;
  removed: boolean;
  dirty: boolean;
  values: Record<string, unknown>;
};

type One2ManyColumn = {
  name: string;
  label: string;
  ttype: string;
  required: boolean;
  selection?: Array<[string, string]>;
};

type ContractAccessPolicy = {
  mode: 'allow' | 'degrade' | 'block';
  reasonCode: string;
  message: string;
  blockedFields: Array<{ field: string; model: string; reasonCode: string }>;
  degradedFields: Array<{ field: string; model: string; reasonCode: string }>;
};

class ContractAccessPolicyError extends Error {
  reasonCode: string;

  constructor(message: string, reasonCode: string) {
    super(message);
    this.name = 'ContractAccessPolicyError';
    this.reasonCode = reasonCode;
  }
}

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

function asText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
}

const status = ref<UiStatus>('loading');
const loadStage = ref('idle');
const errorMessage = ref('');
const validationErrors = ref<string[]>([]);
const submissionFeedback = ref<{ kind: 'success' | 'warn' | 'error'; message: string } | null>(null);
const showOne2manyErrors = ref(false);
const busyKind = ref<BusyKind>(null);
const contract = ref<ActionContract | null>(null);
const contractMeta = ref<Record<string, unknown> | null>(null);
const activeFilterKey = ref('');
const originalValues = ref<Record<string, unknown>>({});
const formData = reactive<Record<string, unknown>>({});
const advancedExpanded = ref(false);
const relationOptions = ref<Record<string, RelationOption[]>>({});
const relationFieldDescriptors = ref<Record<string, Record<string, FieldDescriptor>>>({});
const relationKeywords = reactive<Record<string, string>>({});
const deniedRelationModels = new Set<string>();
const one2manyRows = reactive<Record<string, One2ManyInlineRow[]>>({});
const relationQueryTimers: Record<string, ReturnType<typeof setTimeout>> = {};
const onchangeModifiersPatch = ref<Record<string, Record<string, unknown>>>({});
const onchangeWarnings = ref<Array<{ title?: string; message?: string; reason_code?: string }>>([]);
const onchangeLinePatches = ref<OnchangeLinePatch[]>([]);
const changedFieldSet = new Set<string>();
let onchangeTimer: ReturnType<typeof setTimeout> | null = null;
const applyingOnchangePatch = ref(false);

const model = computed(() => String(route.params.model || contract.value?.head?.model || contract.value?.model || ''));
const isProjectFormPage = computed(() => String(model.value || '').trim() === 'project.project');
const isWorkBreakdownFormPage = computed(() => String(model.value || '').trim() === 'construction.work.breakdown');
const actionId = computed(() => {
  return resolveActionIdFromContext({
    routeQuery: route.query as Record<string, unknown>,
    currentActionId: session.currentAction?.action_id,
    currentActionModel: session.currentAction?.model,
    model: model.value,
  });
});
const recordId = computed(() => {
  const raw = String(route.params.id || '').trim();
  if (!raw || raw === 'new') return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
});
const recordIdDisplay = computed(() => (recordId.value ? String(recordId.value) : 'new'));
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
const busy = computed(() => busyKind.value !== null);
const isInteractionLocked = computed(() => status.value === 'loading' || busy.value);
const formRenderPolicy = computed(() => resolveContractViewRenderPolicy(contract.value, 'form'));
const formNativeFallbackUrl = computed(() => {
  const action = formRenderPolicy.value.fallbackAction;
  return Object.keys(action || {}).length ? buildNativeFallbackUrl(action) : '';
});
const showFormNativeFallback = computed(() => formRenderPolicy.value.recommendedRuntime === 'native' && Boolean(formNativeFallbackUrl.value));
const formNativeFallbackMessage = computed(() => (
  formRenderPolicy.value.notes[0] || '当前表单命中了原生兜底条件，请使用原生页面完成操作。'
));
const sceneContractV1 = computed<Record<string, unknown>>(() => asRecord((contract.value as Record<string, unknown> | null)?.scene_contract_v1));
const sceneContractPermissions = computed<Record<string, unknown>>(() => asRecord(sceneContractV1.value.permissions));
const semanticPage = computed<Record<string, unknown>>(() => asRecord((contract.value as Record<string, unknown> | null)?.semantic_page));
const semanticFormSemantics = computed<Record<string, unknown>>(() => asRecord(semanticPage.value.form_semantics));
const semanticFormLayout = computed<unknown[]>(() => (Array.isArray(semanticFormSemantics.value.layout) ? semanticFormSemantics.value.layout : []));
const semanticZoneKeySet = computed(() => {
  const zones = Array.isArray(semanticPage.value.zones) ? semanticPage.value.zones : [];
  const keys = zones
    .map((item) => {
      const row = asRecord(item);
      return asText(row.key);
    })
    .filter(Boolean);
  return new Set(keys);
});
const semanticHasSummaryZone = computed(() => semanticZoneKeySet.value.size === 0 || semanticZoneKeySet.value.has('summary_zone'));
const semanticHasDetailZone = computed(() => semanticZoneKeySet.value.size === 0 || semanticZoneKeySet.value.has('detail_zone'));
const semanticHasActionZone = computed(() => semanticZoneKeySet.value.size === 0 || semanticZoneKeySet.value.has('action_zone'));
const semanticHasRelationZone = computed(() => semanticZoneKeySet.value.size === 0 || semanticZoneKeySet.value.has('relation_zone'));
const semanticHasCollaborationZone = computed(() => semanticZoneKeySet.value.size === 0 || semanticZoneKeySet.value.has('collaboration_zone'));
const semanticRelationZoneItems = computed<Array<{ field: string; label: string; viewType: string; editableLabel: string }>>(() => {
  const rows = Array.isArray(semanticFormSemantics.value.relation_fields) ? semanticFormSemantics.value.relation_fields : [];
  return rows
    .map((item) => {
      const row = asRecord(item);
      const field = asText(row.field);
      if (!field) return null;
      const fieldDescriptor = contract.value?.fields?.[field] as Record<string, unknown> | undefined;
      const label = String(fieldDescriptor?.string || field).trim();
      const viewType = asText(row.preferred_view_type) || 'tree';
      const editable = asRecord(row.editable);
      const editableLabel = editable.inline_edit === true ? '可行内编辑' : '只读关系';
      return { field, label, viewType, editableLabel };
    })
    .filter((item): item is { field: string; label: string; viewType: string; editableLabel: string } => Boolean(item));
});
const semanticHasChatter = computed(() => {
  if (semanticFormSemantics.value.has_chatter === true) return true;
  const chatter = asRecord(asRecord(asRecord(contract.value).views).form).chatter;
  return Boolean(chatter && typeof chatter === 'object' && (chatter as Record<string, unknown>).enabled === true);
});
const semanticHasAttachments = computed(() => {
  if (semanticFormSemantics.value.has_attachments === true) return true;
  const attachments = asRecord(asRecord(asRecord(contract.value).views).form).attachments;
  return Boolean(attachments && typeof attachments === 'object' && (attachments as Record<string, unknown>).enabled === true);
});
const semanticPermissionVerdicts = computed<Record<string, unknown>>(() => asRecord(semanticPage.value.permission_verdicts));
const semanticActionGating = computed<Record<string, unknown>>(() => asRecord(semanticPage.value.action_gating));
const semanticActionGatingVerdict = computed<Record<string, unknown>>(() => asRecord(semanticActionGating.value.verdict));
function resolveSurfaceActionRows(kind: 'header_buttons' | 'button_box' | 'stat_buttons') {
  const profile = normalizeRenderProfile(contract.value?.render_profile, recordId.value ? 'edit' : 'create');
  const renderSurfaces = asRecord((contract.value as Record<string, unknown> | null)?.render_surfaces);
  const activeSurface = asRecord(renderSurfaces[profile]);
  const actions = asRecord(activeSurface.actions);
  const rows = actions[kind];
  if (Array.isArray(rows)) return rows;
  const formView = asRecord(asRecord(asRecord(contract.value).views).form);
  const fallback = formView[kind];
  return Array.isArray(fallback) ? fallback : [];
}
const formViewSurfaceActions = computed<Array<Record<string, unknown>>>(() => {
  const buckets = [
    { rows: resolveSurfaceActionRows('header_buttons'), level: 'header' },
    { rows: resolveSurfaceActionRows('button_box'), level: 'smart' },
    { rows: resolveSurfaceActionRows('stat_buttons'), level: 'smart' },
  ];
  const out: Array<Record<string, unknown>> = [];
  const dedup = new Set<string>();
  for (const bucket of buckets) {
    if (!Array.isArray(bucket.rows)) continue;
    for (const item of bucket.rows) {
      const row = asRecord(item);
      const payload = parseMaybeJsonRecord(row.payload);
      const key = asText(row.key)
        || asText(row.name)
        || asText(payload.method)
        || asText(payload.ref)
        || asText(row.label);
      if (!key || dedup.has(key)) continue;
      dedup.add(key);
      out.push({
        ...row,
        key,
        level: asText(row.level) || bucket.level,
      });
    }
  }
  return out;
});
const semanticActionStateByKey = computed<Record<string, { enabled: boolean; reason: string }>>(() => {
  const out: Record<string, { enabled: boolean; reason: string }> = {};
  const actions = asRecord(semanticPage.value.actions);
  const buckets = [actions.header_actions, actions.record_actions, actions.toolbar_actions];
  for (const bucket of buckets) {
    if (!Array.isArray(bucket)) continue;
    for (const item of bucket) {
      const row = asRecord(item);
      const key = asText(row.key);
      if (!key) continue;
      const enabled = row.enabled === true;
      const reason = asText(row.reason) || asText(row.reason_code);
      out[key] = { enabled, reason };
    }
  }
  for (const row of formViewSurfaceActions.value) {
    const key = asText(row.key);
    if (!key || out[key]) continue;
    out[key] = { enabled: true, reason: '' };
  }
  return out;
});
const sceneConsumerRuntime = computed<Record<string, unknown>>(() => {
  const diagnostics = asRecord(sceneContractV1.value.diagnostics);
  return asRecord(diagnostics.consumer_runtime);
});
const sceneDisabledActions = computed<Record<string, string>>(() => {
  const out: Record<string, string> = {};
  Object.entries(asRecord(sceneContractPermissions.value.disabled_actions)).forEach(([key, value]) => {
    const reason = asText(value);
    if (!key || !reason) return;
    out[key] = reason;
  });
  return out;
});
const sceneRuntimePageStatus = computed(() => (
  asText(sceneConsumerRuntime.value.runtime_page_status) || asText(sceneConsumerRuntime.value.page_status)
));
const sceneWriteDisabledReason = computed(() => {
  const disabled = sceneDisabledActions.value;
  const statusKey = sceneRuntimePageStatus.value;
  const currentState = asText(sceneConsumerRuntime.value.current_state);
  if (recordId.value) {
    if (disabled.edit) return disabled.edit;
    if (disabled.submit) return disabled.submit;
    if (sceneContractPermissions.value.can_edit === false) {
      return currentState
        ? `当前记录状态 ${currentState} 不允许编辑`
        : (statusKey === 'readonly' ? '当前页面为只读状态' : '当前页面不允许编辑');
    }
  } else {
    if (disabled.create) return disabled.create;
    if (disabled.submit) return disabled.submit;
    if (sceneContractPermissions.value.can_create === false) {
      return statusKey === 'restricted' ? '当前页面不允许新建' : '当前页面暂不可创建';
    }
  }
  if (statusKey === 'restricted') return '当前页面访问受限';
  return '';
});
const sceneRuntimeStatusPanel = computed(() => {
  const statusKey = sceneRuntimePageStatus.value;
  const reason = sceneWriteDisabledReason.value;
  if (!statusKey && !reason) return null;
  const currentState = asText(sceneConsumerRuntime.value.current_state);
  const missingRequiredCount = Number(sceneConsumerRuntime.value.missing_required_count || 0);
  const activeTransitionCount = Number(sceneConsumerRuntime.value.active_transition_count || 0);
  const parts: string[] = [];
  if (reason) parts.push(reason);
  if (currentState) parts.push(`当前状态：${currentState}`);
  if (missingRequiredCount > 0) parts.push(`缺失必填项：${missingRequiredCount}`);
  if (activeTransitionCount > 0) parts.push(`可用流转数：${activeTransitionCount}`);
  return {
    title: statusKey === 'readonly'
      ? '当前表单为只读状态'
      : statusKey === 'restricted'
        ? '当前表单访问受限'
        : '当前表单运行态提示',
    message: parts.join('；') || '当前页面的可写能力受 scene contract runtime 限制。',
    hint: '当前交互状态来自后端 scene contract runtime。',
  };
});

const renderProfile = computed<'create' | 'edit' | 'readonly'>(() => {
  const profile = normalizeRenderProfile(contract.value?.render_profile, 'edit');
  if (profile === 'readonly') return 'readonly';
  if (profile === 'edit') return 'edit';
  if (profile === 'create') return 'create';
  if (!canSave.value) return 'readonly';
  return recordId.value ? 'edit' : 'create';
});
const activeRenderSurface = computed<Record<string, unknown>>(() => {
  const renderSurfaces = asRecord((contract.value as Record<string, unknown> | null)?.render_surfaces);
  return asRecord(renderSurfaces[renderProfile.value]);
});

const rights = computed(() => {
  const head = contract.value?.head?.permissions;
  const effective = contract.value?.permissions?.effective?.rights;
  const resolve = (key: 'read' | 'write' | 'create' | 'unlink') => {
    const semanticVerdict = asRecord(semanticPermissionVerdicts.value[key]);
    if (typeof semanticVerdict.allowed === 'boolean') return semanticVerdict.allowed;
    const a = head?.[key];
    if (typeof a === 'boolean') return a;
    const b = effective?.[key];
    if (typeof b === 'boolean') return b;
    return true;
  };
  return {
    read: resolve('read'),
    write: resolve('write'),
    create: resolve('create'),
    unlink: resolve('unlink'),
  };
});

const canPersistBySceneRuntime = computed(() => {
  if (recordId.value) {
    if (sceneContractPermissions.value.can_edit === false) return false;
  } else if (sceneContractPermissions.value.can_create === false) {
    return false;
  }
  if (sceneRuntimePageStatus.value === 'restricted') return false;
  return true;
});
const isSemanticStateWriteBlocked = computed(() => Boolean(semanticActionGatingVerdict.value.is_closed_state) && Boolean(recordId.value));
const canSave = computed(() => (
  (recordId.value ? rights.value.write : rights.value.create)
  && canPersistBySceneRuntime.value
  && !isSemanticStateWriteBlocked.value
));
const isProjectQuickIntakeMode = computed(() => {
  if (String(model.value || '').trim() !== 'project.project') return false;
  if (recordId.value) return false;
  return String(route.query.intake_mode || '').trim().toLowerCase() === 'quick';
});
const isProjectStandardIntakeMode = computed(() => {
  if (String(model.value || '').trim() !== 'project.project') return false;
  if (recordId.value) return false;
  if (isProjectQuickIntakeMode.value) return false;
  return String(route.query.scene_key || '').trim() === PROJECT_INTAKE_SCENE_KEY;
});
const isProjectCreatePage = computed(() => {
  const routeModel = String(route.params.model || '').trim();
  const routeId = String(route.params.id || '').trim().toLowerCase();
  return routeModel === 'project.project' && routeId === 'new';
});
const isProjectIntakeCreateMode = computed(() => isProjectQuickIntakeMode.value || isProjectStandardIntakeMode.value);
const intakeAutosaveKey = computed(() => {
  if (!isProjectCreatePage.value) return '';
  const mode = isProjectQuickIntakeMode.value ? 'quick' : 'standard';
  const userId = Number(session.user?.id || 0) || 0;
  return `sc:intake:autosave:project.project:${mode}:u${userId}`;
});
const quickRequiredReady = computed(() => {
  if (!isProjectQuickIntakeMode.value) return true;
  const projectName = String(formData.name || '').trim();
  const managerId = Number(formData.manager_id || 0);
  return Boolean(projectName) && Number.isFinite(managerId) && managerId > 0;
});
const standardCreateReady = computed(() => {
  if (!isProjectStandardIntakeMode.value) return true;
  const projectName = String(formData.name || '').trim();
  const managerId = Number(formData.manager_id || 0);
  return Boolean(projectName) && Number.isFinite(managerId) && managerId > 0;
});
const hasChanges = computed(() => {
  const keys = Object.keys(formData);
  return keys.some((key) => {
    if (!isFieldWritable(key)) return false;
    return comparableFieldValue(key, formData[key]) !== comparableFieldValue(key, originalValues.value[key]);
  });
});
const writableFieldCount = computed(() =>
  layoutNodes.value.filter((node) => node.kind === 'field' && !node.readonly).length,
);
const visibleFieldNodeCount = computed(() =>
  layoutNodes.value.filter((node) => node.kind === 'field' && isFieldVisible(node.name)).length,
);
const changedFieldCount = computed(() =>
  Object.keys(formData).filter((key) => isFieldWritable(key) && comparableFieldValue(key, formData[key]) !== comparableFieldValue(key, originalValues.value[key])).length,
);

const hasExplicitPasswordChange = computed(() => {
  if (String(model.value || '').trim() !== 'res.users') return false;
  return String(formData.password || '').trim().length > 0;
});

const intakeRequiredFields = computed(() => {
  if (!isProjectCreatePage.value) return [];
  return layoutNodes.value
    .filter((node) => node.kind === 'field' && node.required && isFieldVisible(node.name))
    .map((node) => ({ name: node.name, label: node.label || node.name }));
});

const intakeRequiredReadyCount = computed(() => {
  if (!isProjectCreatePage.value) return 0;
  return intakeRequiredFields.value.filter((field) => {
    const value = formData[field.name];
    if (value === null || value === undefined) return false;
    if (typeof value === 'string') return value.trim().length > 0;
    if (typeof value === 'number') return Number.isFinite(value) && value > 0;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === 'boolean') return true;
    return Boolean(value);
  }).length;
});

const intakeMissingRequiredLabels = computed(() => {
  if (!isProjectCreatePage.value) return [];
  return intakeRequiredFields.value
    .filter((field) => {
      const value = formData[field.name];
      if (value === null || value === undefined) return true;
      if (typeof value === 'string') return value.trim().length === 0;
      if (typeof value === 'number') return !Number.isFinite(value) || value <= 0;
      if (Array.isArray(value)) return value.length === 0;
      return false;
    })
    .map((field) => {
      const label = String(field.label || '').trim();
      if (label === '名称') return '项目名称';
      return label;
    })
    .slice(0, 5);
});

const intakeRequiredSummary = computed(() => {
  if (!isProjectCreatePage.value) return '';
  const total = intakeRequiredFields.value.length;
  const done = intakeRequiredReadyCount.value;
  if (total <= 0) return '当前契约未提供必填字段约束。';
  return `${done}/${total}`;
});

const intakeMissingSummary = computed(() => {
  if (!isProjectCreatePage.value) return '';
  if (!intakeMissingRequiredLabels.value.length) return '无';
  return intakeMissingRequiredLabels.value.join('、');
});

const one2manyValidation = computed(() => collectOne2manyDraftValidation());

const pageTitle = computed(() => {
  if (isWorkBreakdownFormPage.value) {
    return '工程结构详情';
  }
  if (isProjectFormPage.value) {
    const recordName = String(formData.name || '').trim();
    if (recordName) return recordName;
    if (recordId.value) return `项目详情 #${recordId.value}`;
    return '项目详情';
  }
  const title = String(contract.value?.head?.title || '').trim();
  if (title) return title;
  const actionName = String(session.currentAction?.name || '').trim();
  if (actionName) return actionName;
  return model.value ? `业务表单 · ${model.value}` : '业务表单';
});

const pageDisplayTitle = computed(() => {
  if (isProjectCreatePage.value) return '创建项目';
  return pageTitle.value;
});

const pageDisplaySubtitle = computed(() => {
  if (isProjectCreatePage.value) {
    return '填写核心信息即可完成项目立项';
  }
  if (isWorkBreakdownFormPage.value) {
    return '查看或编辑工程结构节点信息';
  }
  if (isProjectFormPage.value) {
    const statusLabel = activeStatusbarLabel.value;
    return statusLabel ? `项目详情页 · 当前阶段：${statusLabel}` : '项目详情页';
  }
  if (enterpriseFormSurface.value === 'enterprise_enablement' && isEnterpriseCompanyFormPage.value) {
    return '这里只维护企业启用所需的基础信息。保存后请继续进入组织架构。';
  }
  if (enterpriseFormSurface.value === 'enterprise_enablement' && isEnterpriseDepartmentFormPage.value) {
    return '先搭建部门层级，再进入用户设置，把执行主体挂到部门下。';
  }
  if (enterpriseFormSurface.value === 'enterprise_enablement' && isEnterpriseUserFormPage.value) {
    return '这里只维护用户主数据。角色、安全策略和高级权限治理继续保留在原生页面。';
  }
  return '';
});

const isEnterpriseCompanyFormPage = computed(() => String(model.value || '').trim() === 'res.company');
const isEnterpriseDepartmentFormPage = computed(() => String(model.value || '').trim() === 'hr.department');
const isEnterpriseUserFormPage = computed(() => String(model.value || '').trim() === 'res.users');
const formGovernance = computed<Record<string, unknown>>(() => {
  const raw = (contract.value as Record<string, unknown> | null)?.form_governance;
  return raw && typeof raw === 'object' && !Array.isArray(raw) ? raw as Record<string, unknown> : {};
});
const enterpriseFormSurface = computed(() => String(formGovernance.value.surface || '').trim());
const isEnterpriseBootstrapFormPage = computed(() => enterpriseFormSurface.value === 'enterprise_enablement');

const isEnterpriseUserEnablementCreatePage = computed(() => {
  const enterprisePrimaryActionId = Number(session.enterpriseEnablement?.primary_action?.action_id || 0);
  if (recordId.value) return false;
  if (String(model.value || '').trim() !== 'res.users') return false;
  return enterprisePrimaryActionId > 0 && actionId.value === enterprisePrimaryActionId;
});
const enterpriseCurrentCompanyId = computed(() => {
  const fromEnablement = Number(session.enterpriseEnablement?.current_company_id || 0);
  if (fromEnablement > 0) return fromEnablement;
  const userRecord = (session.user && typeof session.user === 'object')
    ? (session.user as Record<string, unknown>)
    : {};
  const fromCompanyId = Number(userRecord.company_id || 0);
  if (fromCompanyId > 0) return fromCompanyId;
  const companyRaw = userRecord.company;
  if (companyRaw && typeof companyRaw === 'object' && !Array.isArray(companyRaw)) {
    const fromCompanyObject = Number((companyRaw as Record<string, unknown>).id || 0);
    if (fromCompanyObject > 0) return fromCompanyObject;
  }
  return 0;
});

const intakeCreateButtonLabel = computed(() => {
  if (!isProjectCreatePage.value) return '创建项目';
  return busy.value && busyKind.value === 'save' ? '创建中…' : '创建项目';
});

const submitButtonLabel = computed(() => {
  if (busy.value && busyKind.value === 'save') {
    return isProjectQuickIntakeMode.value ? '创建中...' : '保存中...';
  }
  if (isProjectQuickIntakeMode.value && !recordId.value) {
    return '创建并进入项目驾驶舱';
  }
  return '保存';
});
const normalCreateButtonLabel = computed(() => (busy.value && busyKind.value === 'save' ? '创建中...' : '创建项目'));

const headerActionsVisible = computed(() => {
  if (isProjectIntakeCreateMode.value) return [];
  if (Boolean(formGovernance.value.suppress_contract_header_actions)) return [];
  return headerActions.value;
});
const contractActionStrip = computed(() => {
  const source = headerActionsVisible.value;
  const dedup = new Set<string>();
  const isTechnicalLabel = (labelRaw: unknown): boolean => {
    const label = String(labelRaw || '').trim();
    if (!label) return true;
    if (label.includes('_')) return true;
    return /^[a-z0-9.:-]+$/i.test(label);
  };
  const out = source.filter((action) => {
    const key = String(action.key || '').trim();
    if (!key || dedup.has(key)) return false;
    dedup.add(key);
    if ((projectDetailStructureAlignMode.value || nativeLikeFormSurface.value) && isTechnicalLabel(action.label)) return false;
    return true;
  });
  return out;
});
const statusbarFieldName = computed(() => String(asRecord(asRecord(contract.value?.views?.form).statusbar).field || '').trim());
const statusbarSteps = computed<DetailStatusbarStep[]>(() => {
  const fieldName = statusbarFieldName.value;
  if (!fieldName) return [];
  const descriptor = contract.value?.fields?.[fieldName];
  const rows = Array.isArray(descriptor?.selection) ? descriptor.selection : [];
  const current = String(formData[fieldName] || '').trim();
  return rows
    .map((item) => {
      const tuple = Array.isArray(item) ? item : [];
      const key = String(tuple[0] || '').trim();
      const label = String(tuple[1] || tuple[0] || '').trim();
      if (!key || !label) return null;
      return {
        key,
        label,
        active: key === current,
      };
    })
    .filter((item): item is DetailStatusbarStep => Boolean(item));
});
const activeStatusbarLabel = computed(() => statusbarSteps.value.find((item) => item.active)?.label || '');
const formCompactMode = computed(() => String(import.meta.env.VITE_FORM_COMPACT || '1').trim() !== '0');
const projectDetailStructureAlignMode = computed(() => isProjectFormPage.value && !isProjectCreatePage.value);
const structureAuditMode = computed(() => {
  if (showHud.value) return true;
  const querySwitchRaw = route.query.structure_audit ?? route.query.audit_structure ?? route.query.debug_structure ?? '';
  const querySwitch = String(querySwitchRaw || '').trim().toLowerCase();
  if (['1', 'true', 'yes', 'on'].includes(querySwitch)) return true;
  return String(import.meta.env.VITE_FORM_STRUCTURE_AUDIT || '0').trim() === '1';
});
const forceStructureVisibilityMode = computed(() => projectDetailStructureAlignMode.value && structureAuditMode.value);
const effectiveCompactMode = computed(() => formCompactMode.value && !nativeLikeFormSurface.value);
const layoutShellFlow = computed(() => isProjectCreatePage.value && !effectiveCompactMode.value);
const pageOverviewItems = computed(() => {
  const items: Array<{ label: string; value: string }> = [];
  if (recordId.value) items.push({ label: '记录ID', value: String(recordId.value) });
  const manager = many2oneLabel('manager_id');
  if (manager) items.push({ label: '项目经理', value: manager });
  const owner = many2oneLabel('owner_id');
  if (owner) items.push({ label: '业主单位', value: owner });
  const startDate = String(formData.start_date || '').trim();
  if (startDate) items.push({ label: '开工日期', value: startDate });
  const contractNo = String(formData.contract_no || '').trim();
  if (contractNo) items.push({ label: '项目编号', value: contractNo });
  const statusLabel = activeStatusbarLabel.value;
  if (statusLabel) items.push({ label: '项目状态', value: statusLabel });
  return items.slice(0, 6);
});
const preferNativeFormSurface = computed(() => {
  if (isProjectCreatePage.value) return false;
  if (showFormNativeFallback.value) return false;
  if (isProjectFormPage.value) return true;
  const deliveredViewType = String(contract.value?.view_type || '').trim().toLowerCase();
  const head = asRecord(contract.value?.head);
  const headViewModes = String(head.view_type || head.view_mode || '').trim().toLowerCase();
  const isFormDelivery = deliveredViewType === 'form'
    || (!deliveredViewType && (headViewModes === 'form' || headViewModes.split(',').map((item) => item.trim()).includes('form')));
  if (!isFormDelivery) return false;
  return contractReadiness.value.usable && layoutNodes.value.some((node) => node.kind === 'field');
});
const nativeLikeFormSurface = computed(() => (
  preferNativeFormSurface.value
  && !forceStructureVisibilityMode.value
));
const showPageOverviewStrip = computed(() => {
  if (nativeLikeFormSurface.value) return false;
  return pageOverviewItems.value.length > 0 && !preferNativeFormSurface.value && !effectiveCompactMode.value;
});
const showCommandBar = computed(() => {
  if (effectiveCompactMode.value) return false;
  if (nativeLikeFormSurface.value) {
    return statusbarSteps.value.length > 0 || contractActionStrip.value.length > 0;
  }
  if (!semanticHasSummaryZone.value && !semanticHasActionZone.value) return false;
  return statusbarSteps.value.length > 0 || contractActionStrip.value.length > 0;
});
const showDetailShellZone = computed(() => semanticHasDetailZone.value);
const showRelationZoneBlock = computed(() => {
  if (nativeLikeFormSurface.value) return false;
  if (!semanticHasRelationZone.value) return false;
  return semanticRelationZoneItems.value.length > 0 && !preferNativeFormSurface.value && !effectiveCompactMode.value;
});
const showCollaborationZoneBlock = computed(() => {
  if (nativeLikeFormSurface.value) return false;
  if (!semanticHasCollaborationZone.value) return false;
  return (semanticHasChatter.value || semanticHasAttachments.value) && !effectiveCompactMode.value;
});

const hasPrimaryHeaderAction = computed(() => headerActionsVisible.value.some((item) => item.semantic === 'primary_action'));
const enterpriseStepTargets = computed(() => {
  const steps = Array.isArray(session.enterpriseEnablement?.steps) ? session.enterpriseEnablement?.steps : [];
  const out: Record<string, { actionId: number; menuId: number; label: string }> = {};
  steps.forEach((step) => {
    if (!step || typeof step !== 'object') return;
    const key = String(step.key || '').trim().toLowerCase();
    const target = step.target && typeof step.target === 'object' ? step.target : null;
    const actionId = Number(target?.action_id || 0);
    const menuId = Number(target?.menu_id || 0);
    const label = String(step.label || '').trim();
    if (!key || actionId <= 0) return;
    out[key] = { actionId, menuId, label };
  });
  return out;
});
const enterpriseNextActionTarget = computed(() => {
  const nextAction = formGovernance.value.next_action;
  const stepKey = nextAction && typeof nextAction === 'object'
    ? String((nextAction as Record<string, unknown>).step_key || '').trim().toLowerCase()
    : '';
  if (stepKey) return enterpriseStepTargets.value[stepKey] || null;
  return null;
});
const enterpriseNextActionLabel = computed(() => {
  const nextAction = formGovernance.value.next_action;
  if (!nextAction || typeof nextAction !== 'object') return '';
  return String((nextAction as Record<string, unknown>).label || '').trim();
});
const enterpriseNextActionVisible = computed(() => {
  if (isProjectCreatePage.value) return false;
  if (!enterpriseNextActionTarget.value) return false;
  return Boolean(recordId.value);
});
const hideWorkflowSection = computed(() => Boolean(formGovernance.value.hide_workflow));
const hideSearchFiltersSection = computed(() => Boolean(formGovernance.value.hide_search_filters));
const hideBodyActionsSection = computed(() => Boolean(formGovernance.value.hide_body_actions));
const showContractWarnings = computed(() => warnings.value.length > 0 && !isProjectCreatePage.value && (!preferNativeFormSurface.value || showHud.value));
const showStrictContractGuard = computed(() => Boolean(strictContractMissingSummary.value) && !isProjectCreatePage.value && (!preferNativeFormSurface.value || showHud.value));
const showWorkflowTransitions = computed(() => {
  if (nativeLikeFormSurface.value) return false;
  if (!semanticHasActionZone.value) return false;
  return workflowTransitions.value.length > 0 && !isProjectCreatePage.value && !hideWorkflowSection.value && !preferNativeFormSurface.value && !effectiveCompactMode.value;
});
const showInlineSearchFilters = computed(() => {
  if (nativeLikeFormSurface.value) return false;
  if (!semanticHasActionZone.value) return false;
  return showSearchFilters.value && searchFilters.value.length > 0 && !isProjectCreatePage.value && !hideSearchFiltersSection.value && !preferNativeFormSurface.value && !effectiveCompactMode.value;
});
const showBodyActionStrip = computed(() => {
  if (nativeLikeFormSurface.value) return false;
  if (!semanticHasActionZone.value) return false;
  return bodyActions.value.length > 0 && !isProjectCreatePage.value && !hideBodyActionsSection.value && !preferNativeFormSurface.value && !effectiveCompactMode.value;
});

const isQuickSubmitDisabled = computed(() => {
  if (busy.value) return true;
  if (!canSave.value) return true;
  if (isProjectQuickIntakeMode.value) return !quickRequiredReady.value;
  if (hasExplicitPasswordChange.value) return false;
  return Boolean(recordId.value) && !hasChanges.value;
});
const isStandardCreateDisabled = computed(() => {
  if (busy.value) return true;
  if (!canSave.value) return true;
  if (isProjectStandardIntakeMode.value) return !standardCreateReady.value;
  return false;
});

const isIntakeCreateDisabled = computed(() => {
  if (!isProjectCreatePage.value) return false;
  if (isProjectQuickIntakeMode.value) return isQuickSubmitDisabled.value;
  return isStandardCreateDisabled.value;
});

function persistIntakeAutosave() {
  const key = intakeAutosaveKey.value;
  if (!key || recordId.value) return;
  try {
    const payload = {
      saved_at: Date.now(),
      values: {
        name: formData.name ?? '',
        manager_id: formData.manager_id ?? false,
        owner_id: formData.owner_id ?? false,
        project_type_id: formData.project_type_id ?? false,
        project_category_id: formData.project_category_id ?? false,
        location: formData.location ?? '',
        start_date: formData.start_date ?? '',
        end_date: formData.end_date ?? '',
      },
    };
    window.localStorage.setItem(key, JSON.stringify(payload));
  } catch {
    // ignore storage exceptions
  }
}

function restoreIntakeAutosave() {
  const key = intakeAutosaveKey.value;
  if (!key || recordId.value) return;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return;
    const parsed = JSON.parse(raw) as { values?: Record<string, unknown> };
    const values = parsed?.values;
    if (!values || typeof values !== 'object') return;
    const fields = [
      'name',
      'manager_id',
      'owner_id',
      'project_type_id',
      'project_category_id',
      'location',
      'start_date',
      'end_date',
    ];
    fields.forEach((field) => {
      if (!(field in values)) return;
      const nextValue = values[field];
      if (nextValue === null || nextValue === undefined || nextValue === '') return;
      formData[field] = nextValue as never;
    });
  } catch {
    // ignore malformed storage payload
  }
}

function clearIntakeAutosave() {
  const key = intakeAutosaveKey.value;
  if (!key) return;
  try {
    window.localStorage.removeItem(key);
  } catch {
    // ignore storage exceptions
  }
}

const contractMetaLine = computed(() => {
  if (!contract.value) return '';
  const mode = String(contractMeta.value?.contract_mode || '-');
  const surface = String((contract.value as Record<string, unknown>)?.contract_surface || contractMeta.value?.contract_surface || '-');
  const viewType = String(contract.value.head?.view_type || contract.value.view_type || '-');
  const filters = Array.isArray(contract.value.search?.filters) ? contract.value.search.filters.length : 0;
  const transitions = Array.isArray(contract.value.workflow?.transitions) ? contract.value.workflow.transitions.length : 0;
  return `mode=${mode} · surface=${surface} · view_type=${viewType} · profile=${renderProfile.value} · filters=${filters} · transitions=${transitions} · rights=${rights.value.read ? 'R' : '-'}${rights.value.write ? 'W' : '-'}${rights.value.create ? 'C' : '-'}${rights.value.unlink ? 'D' : '-'}`;
});

const showDebugActions = computed(() => renderProfile.value !== 'create');
const showDebugActionsVisible = computed(() => showHud.value && showDebugActions.value);
const runtimeUserGroups = computed(() => {
  const out = new Set<string>();
  (session.user?.groups_xmlids || []).forEach((group) => {
    const normalized = String(group || '').trim();
    if (normalized) out.add(normalized);
  });
  return out;
});
const runtimeRoleCode = computed(() => String(session.roleSurface?.role_code || '').trim().toLowerCase());
const runtimeCapabilities = computed(() => {
  const out = new Set<string>();
  (session.capabilities || []).forEach((key) => {
    const normalized = String(key || '').trim();
    if (normalized) out.add(normalized);
  });
  const catalog = session.capabilityCatalog || {};
  Object.values(catalog).forEach((meta) => {
    const key = String(meta?.key || '').trim();
    if (!key) return;
    const state = String(meta?.state || '').trim().toUpperCase();
    const capState = String(meta?.capability_state || '').trim().toLowerCase();
    if (state === 'LOCKED' || capState === 'deny') return;
    out.add(key);
  });
  return out;
});
const policyContext = computed(() => ({
  profile: renderProfile.value,
  formData: formData as Record<string, unknown>,
  capabilities: runtimeCapabilities.value,
  userGroups: runtimeUserGroups.value,
  roleCode: runtimeRoleCode.value,
}));

const warnings = computed(() => {
  const rows = contract.value?.warnings;
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => {
      if (typeof row === 'string') return row;
      if (row && typeof row === 'object') return String((row as Record<string, unknown>).message || (row as Record<string, unknown>).code || '');
      return '';
    })
    .map((x) => x.trim())
    .filter(Boolean);
});

const contractAccessPolicy = computed<ContractAccessPolicy>(() => {
  const raw = (contract.value as Record<string, unknown> | null)?.access_policy;
  const row = raw && typeof raw === 'object' && !Array.isArray(raw)
    ? (raw as Record<string, unknown>)
    : {};
  const modeRaw = String(row.mode || '').trim().toLowerCase();
  const mode: 'allow' | 'degrade' | 'block' = modeRaw === 'block' || modeRaw === 'degrade' ? modeRaw : 'allow';
  const normalizeRows = (value: unknown) => {
    if (!Array.isArray(value)) return [];
    return value
      .map((item) => {
        if (!item || typeof item !== 'object' || Array.isArray(item)) return null;
        const v = item as Record<string, unknown>;
        return {
          field: String(v.field || '').trim(),
          model: String(v.model || '').trim(),
          reasonCode: String(v.reason_code || '').trim(),
        };
      })
      .filter((item): item is { field: string; model: string; reasonCode: string } => Boolean(item));
  };
  return {
    mode,
    reasonCode: String(row.reason_code || '').trim(),
    message: String(row.message || '').trim(),
    blockedFields: normalizeRows(row.blocked_fields),
    degradedFields: normalizeRows(row.degraded_fields),
  };
});

const workflowTransitions = computed(() => {
  const rows = contract.value?.workflow?.transitions;
  if (!Array.isArray(rows)) return [];
  // Create profile only keeps primary create action in header; hide workflow transitions to avoid duplicated semantics.
  if (renderProfile.value === 'create') return [];
  if (isProjectFormPage.value) return [];
  const headerActionKeys = new Set(
    contractActions.value
      .filter((item) => item.level === 'header' || item.level === 'toolbar')
      .map((item) => item.key),
  );
  const transitions = rows.map((row, idx) => {
    const triggerLabel = String(row.trigger?.label || '').trim();
    const triggerName = String(row.trigger?.name || '').trim();
    const triggerKind = String(row.trigger?.kind || '').trim().toLowerCase();
    const action = contractActions.value.find((item) => {
      if (triggerKind && item.kind && item.kind !== triggerKind) return false;
      if (triggerName && (item.methodName === triggerName || item.key.includes(triggerName))) return true;
      if (triggerLabel && item.label === triggerLabel) return true;
      return false;
    }) || null;
    return {
      key: `wf_${idx}`,
      label: triggerLabel || triggerName || `transition_${idx + 1}`,
      notes: String(row.notes || ''),
      action,
    };
  });
  if (showHud.value) return transitions;
  return transitions.filter((item) => {
    const label = String(item.label || '').trim();
    if (!item.action) return false;
    if (item.action?.key && headerActionKeys.has(item.action.key)) return false;
    if (/^\d+$/.test(label)) return false;
    return true;
  });
});

const searchFilters = computed(() => {
  const rows = contract.value?.search?.filters;
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => ({
      key: String(row.key || '').trim(),
      label: String(row.label || row.key || '').trim(),
      domainRaw: String(row.domain_raw || '').trim(),
      contextRaw: String(row.context_raw || '').trim(),
    }))
    .filter((row) => row.key && row.label);
});

const showSearchFilters = computed(() => {
  if (!contract.value) return true;
  if (isProjectFormPage.value) return false;
  if (renderProfile.value !== 'create') return true;
  return !contract.value.hide_filters_on_create;
});

function fieldType(descriptor?: FieldDescriptor | null) {
  return String(descriptor?.ttype || descriptor?.type || '').trim().toLowerCase();
}

function toDateInputValue(value: unknown) {
  const raw = String(value ?? '').trim();
  if (!raw) return '';
  if (raw.length >= 10) return raw.slice(0, 10);
  return raw;
}

function toDatetimeInputValue(value: unknown) {
  const raw = String(value ?? '').trim();
  if (!raw) return '';
  const normalized = raw.replace(' ', 'T');
  return normalized.length >= 16 ? normalized.slice(0, 16) : normalized;
}

function fromDatetimeInputValue(value: unknown) {
  const raw = String(value ?? '').trim();
  if (!raw) return false;
  const normalized = raw.replace('T', ' ');
  return normalized.length === 16 ? `${normalized}:00` : normalized;
}

function normalizeRelationIds(value: unknown): number[] {
  return extractX2ManyIds(value);
}

function relationIds(name: string): number[] {
  return normalizeRelationIds(formData[name]);
}

function many2oneValue(name: string) {
  const ids = relationIds(name);
  return ids.length ? String(ids[0]) : '';
}

function many2oneLabel(name: string) {
  const ids = relationIds(name);
  if (!ids.length) return '';
  const matched = relationOptionsForField(name).find((item) => item.id === ids[0]);
  if (matched?.label) return matched.label;
  return relationKeyword(name) || `#${ids[0]}`;
}

function mergeRelationOptions(current: RelationOption[], incoming: RelationOption[]): RelationOption[] {
  const merged = new Map<number, RelationOption>();
  for (const option of current) {
    if (option.id > 0) merged.set(option.id, option);
  }
  for (const option of incoming) {
    if (option.id > 0) merged.set(option.id, option);
  }
  return Array.from(merged.values());
}

function relationOptionsForField(name: string) {
  const rows = relationOptions.value[name];
  if (Array.isArray(rows) && rows.length) return rows;
  const ids = relationIds(name);
  if (!ids.length) return [];
  return ids.map((id) => ({ id, label: `#${id}` }));
}

function parseMany2oneDisplay(value: unknown): RelationOption | null {
  if (Array.isArray(value)) {
    const id = Number(value[0]);
    if (!Number.isFinite(id) || id <= 0) return null;
    const label = String(value[1] || `#${id}`).trim() || `#${id}`;
    return { id: Math.trunc(id), label };
  }
  if (value && typeof value === 'object') {
    const row = value as Record<string, unknown>;
    const id = Number(row.id);
    if (!Number.isFinite(id) || id <= 0) return null;
    const label = String(row.display_name || row.name || `#${id}`).trim() || `#${id}`;
    return { id: Math.trunc(id), label };
  }
  return null;
}

function upsertRelationOption(fieldName: string, option: RelationOption | null) {
  if (!option) return;
  const current = Array.isArray(relationOptions.value[fieldName]) ? relationOptions.value[fieldName] : [];
  if (current.some((item) => item.id === option.id)) return;
  relationOptions.value = {
    ...relationOptions.value,
    [fieldName]: [option, ...current],
  };
}

function relationKeyword(name: string) {
  return String(relationKeywords[name] || '');
}

function one2manyFieldRows(name: string) {
  return Array.isArray(one2manyRows[name]) ? one2manyRows[name] : [];
}

function one2manyRelationModel(name: string) {
  const descriptor = contract.value?.fields?.[name] as Record<string, unknown> | undefined;
  return String(descriptor?.relation || '').trim();
}

function one2manyRelationFieldDescriptor(fieldName: string, column: string) {
  const model = one2manyRelationModel(fieldName);
  if (!model) return null;
  const map = relationFieldDescriptors.value[model] || {};
  const descriptor = map[column];
  return descriptor || null;
}

function one2manyColumns(name: string): One2ManyColumn[] {
  const subviews = (contract.value?.views?.form as Record<string, unknown> | undefined)?.subviews;
  const fieldSubview = subviews && typeof subviews === 'object'
    ? (subviews as Record<string, unknown>)[name]
    : undefined;
  const tree = fieldSubview && typeof fieldSubview === 'object'
    ? (fieldSubview as Record<string, unknown>).tree
    : undefined;
  const columnsRaw = tree && typeof tree === 'object'
    ? (tree as Record<string, unknown>).columns
    : undefined;
  const out: One2ManyColumn[] = [];
  if (Array.isArray(columnsRaw)) {
    columnsRaw.forEach((item) => {
      if (typeof item === 'string') {
        const normalized = item.trim();
        if (!normalized || normalized === 'id') return;
        const descriptor = one2manyRelationFieldDescriptor(name, normalized);
        out.push({
          name: normalized,
          label: String(descriptor?.string || normalized),
          ttype: fieldType(descriptor) || 'char',
          required: Boolean(descriptor?.required),
          selection: Array.isArray(descriptor?.selection) ? descriptor?.selection : undefined,
        });
        return;
      }
      if (!item || typeof item !== 'object') return;
      const row = item as Record<string, unknown>;
      const colName = String(row.name || '').trim();
      if (!colName || colName === 'id') return;
      const descriptor = one2manyRelationFieldDescriptor(name, colName);
      out.push({
        name: colName,
        label: String(row.label || row.string || descriptor?.string || colName).trim() || colName,
        ttype: fieldType(descriptor) || 'char',
        required: Boolean(descriptor?.required),
        selection: Array.isArray(descriptor?.selection) ? descriptor?.selection : undefined,
      });
    });
  }
  if (!out.length) {
    const descriptor = one2manyRelationFieldDescriptor(name, 'name');
    return [{
      name: 'name',
      label: String(descriptor?.string || '名称'),
      ttype: fieldType(descriptor) || 'char',
      required: Boolean(descriptor?.required),
      selection: Array.isArray(descriptor?.selection) ? descriptor?.selection : undefined,
    }];
  }
  return out.slice(0, 4);
}

function one2manyPolicies(name: string) {
  const formSubviews = asRecord((asRecord(contract.value?.views?.form)).subviews);
  const baseSubview = asRecord(formSubviews[name]);
  const basePolicies = asRecord(baseSubview.policies);
  const surfaceSubviews = asRecord(activeRenderSurface.value.subviews);
  const surfaceSubview = asRecord(surfaceSubviews[name]);
  const surfacePolicies = asRecord(surfaceSubview.policies);
  return {
    inlineEdit: surfacePolicies.inline_edit !== undefined
      ? Boolean(surfacePolicies.inline_edit)
      : Boolean(basePolicies.inline_edit !== false),
    canCreate: surfacePolicies.can_create !== undefined
      ? Boolean(surfacePolicies.can_create)
      : Boolean(basePolicies.can_create !== false),
    canUnlink: surfacePolicies.can_unlink !== undefined
      ? Boolean(surfacePolicies.can_unlink)
      : Boolean(basePolicies.can_unlink !== false),
  };
}

function one2manyPrimaryColumn(name: string) {
  const cols = one2manyColumns(name);
  return cols.length ? cols[0].name : 'name';
}

function one2manyRowLabel(fieldName: string, row: One2ManyInlineRow) {
  const primary = one2manyPrimaryColumn(fieldName);
  const value = String(row.values?.[primary] ?? row.values?.name ?? '').trim();
  if (value) return value;
  if (row.id) return `#${row.id}`;
  return '未命名';
}

function one2manyRowStateLabel(row: One2ManyInlineRow) {
  if (row.removed) return '待删除';
  if (row.isNew) return '新增';
  if (row.dirty) return '已修改';
  return '未变更';
}

function one2manySummary(name: string) {
  const rows = one2manyFieldRows(name);
  if (!rows.length) return '';
  let created = 0;
  let updated = 0;
  let removed = 0;
  rows.forEach((row) => {
    if (row.removed) {
      removed += 1;
      return;
    }
    if (row.isNew) {
      created += 1;
      return;
    }
    if (row.dirty) updated += 1;
  });
  const parts: string[] = [];
  if (created) parts.push(`新增 ${created}`);
  if (updated) parts.push(`修改 ${updated}`);
  if (removed) parts.push(`删除 ${removed}`);
  return parts.length ? `待提交：${parts.join(' / ')}` : '待提交：无变更';
}

function visibleOne2manyRows(name: string) {
  return one2manyFieldRows(name).filter((row) => !row.removed);
}

function removedOne2manyRows(name: string) {
  return one2manyFieldRows(name).filter((row) => row.removed);
}

function ensureOne2manyRows(name: string) {
  if (!Array.isArray(one2manyRows[name])) {
    one2manyRows[name] = [];
  }
  return one2manyRows[name];
}

function makeOne2manyKey() {
  return `o2m_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
}

function addOne2manyRow(name: string) {
  if (isInteractionLocked.value) return;
  const policies = one2manyPolicies(name);
  if (!policies.canCreate) return;
  const rows = ensureOne2manyRows(name);
  const primary = one2manyPrimaryColumn(name);
  const columns = one2manyColumns(name);
  const values = columns.reduce<Record<string, unknown>>((acc, column) => {
    acc[column.name] = column.ttype === 'boolean' ? false : '';
    return acc;
  }, {});
  rows.push({
    key: makeOne2manyKey(),
    id: null,
    isNew: true,
    removed: false,
    dirty: true,
    values: { ...values, [primary]: values[primary] ?? '' },
  });
  markFieldChanged(name);
}

function normalizeOne2manyColumnValue(column: One2ManyColumn, value: unknown) {
  const ttype = String(column.ttype || '').trim().toLowerCase();
  if (ttype === 'boolean') return Boolean(value);
  if (ttype === 'integer') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? Math.trunc(parsed) : false;
  }
  if (ttype === 'float' || ttype === 'monetary') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : false;
  }
  if (ttype === 'date') return toDateInputValue(value) || false;
  if (ttype === 'datetime') return fromDatetimeInputValue(value);
  if (ttype === 'selection') return String(value ?? '').trim() || false;
  return String(value ?? '');
}

function setOne2manyRowField(fieldName: string, rowKey: string, column: One2ManyColumn, value: unknown) {
  const policies = one2manyPolicies(fieldName);
  if (!policies.inlineEdit) return;
  const rows = ensureOne2manyRows(fieldName);
  const row = rows.find((item) => item.key === rowKey);
  if (!row) return;
  const normalized = normalizeOne2manyColumnValue(column, value);
  row.values = {
    ...(row.values || {}),
    [column.name]: normalized,
  };
  row.dirty = true;
  markFieldChanged(fieldName);
}

function one2manyColumnInputType(column: One2ManyColumn) {
  const ttype = String(column.ttype || '').trim().toLowerCase();
  if (ttype === 'integer' || ttype === 'float' || ttype === 'monetary') return 'number';
  if (ttype === 'date') return 'date';
  if (ttype === 'datetime') return 'datetime-local';
  return 'text';
}

function one2manyColumnDisplayValue(column: One2ManyColumn, value: unknown) {
  const ttype = String(column.ttype || '').trim().toLowerCase();
  if (ttype === 'date') return toDateInputValue(value);
  if (ttype === 'datetime') return toDatetimeInputValue(value);
  return String(value ?? '');
}

function removeOne2manyRow(fieldName: string, rowKey: string) {
  if (isInteractionLocked.value) return;
  const policies = one2manyPolicies(fieldName);
  if (!policies.canUnlink) return;
  const rows = ensureOne2manyRows(fieldName);
  const index = rows.findIndex((item) => item.key === rowKey);
  if (index < 0) return;
  const row = rows[index];
  if (row.isNew) {
    rows.splice(index, 1);
  } else {
    row.removed = true;
    row.dirty = true;
  }
  markFieldChanged(fieldName);
}

function restoreOne2manyRow(fieldName: string, rowKey: string) {
  if (isInteractionLocked.value) return;
  const rows = ensureOne2manyRows(fieldName);
  const row = rows.find((item) => item.key === rowKey);
  if (!row) return;
  row.removed = false;
  row.dirty = true;
  markFieldChanged(fieldName);
}

function initOne2manyRows(name: string, source: unknown) {
  const ids = normalizeRelationIds(source);
  const options = relationOptionsForField(name);
  const optionMap = new Map(options.map((item) => [item.id, item.label]));
  const primary = one2manyPrimaryColumn(name);
  one2manyRows[name] = ids.map((id) => ({
    key: `o2m_id_${id}`,
    id,
    isNew: false,
    removed: false,
    dirty: false,
    values: {
      [primary]: optionMap.get(id) || `#${id}`,
      name: optionMap.get(id) || `#${id}`,
    },
  }));
}

function buildOne2manyCommandValue(name: string, mode: 'onchange' | 'write') {
  const rows = one2manyFieldRows(name);
  return buildOne2ManyInlineCommands({
    original: originalValues.value[name],
    draftRows: rows.map((row) => ({
      id: row.id,
      isNew: row.isNew,
      removed: row.removed,
      dirty: row.dirty,
      values: row.values || {},
    })),
    mode,
  });
}

function collectOne2manyDraftValidation() {
  const issues: string[] = [];
  const rowErrors: Record<string, string[]> = {};
  Object.entries(one2manyRows).forEach(([fieldName, rows]) => {
    if (!Array.isArray(rows) || !rows.length) return;
    const primary = one2manyPrimaryColumn(fieldName);
    const columns = one2manyColumns(fieldName);
    const requiredColumns = columns.filter((column) => column.required);
    const labels = new Set<string>();
    rows.forEach((row, index) => {
      if (row.removed) return;
      const rowKey = `${fieldName}:${row.key}`;
      const perRow: string[] = [];
      requiredColumns.forEach((column) => {
        const value = row.values?.[column.name];
        if (isOne2manyEmptyValue(column, value)) {
          perRow.push(`${column.label}不能为空`);
          issues.push(`${fieldName} 第${index + 1}行${column.label}不能为空`);
        }
      });
      const label = String(row.values?.[primary] ?? row.values?.name ?? '').trim();
      if (label) {
        const key = label.toLowerCase();
        if (labels.has(key)) {
          perRow.push(`主值重复：${label}`);
          issues.push(`${fieldName} 存在重复行值：${label}`);
        } else {
          labels.add(key);
        }
      }
      if (perRow.length) {
        rowErrors[rowKey] = perRow;
      }
    });
  });
  return { issues, rowErrors };
}

function isOne2manyEmptyValue(column: One2ManyColumn, value: unknown) {
  const ttype = String(column.ttype || '').trim().toLowerCase();
  if (ttype === 'boolean') return value === false || value === null || value === undefined;
  if (ttype === 'integer' || ttype === 'float' || ttype === 'monetary') {
    return value === false || value === null || value === undefined || Number.isNaN(Number(value));
  }
  if (ttype === 'date' || ttype === 'datetime' || ttype === 'selection') {
    return !String(value ?? '').trim() || value === false;
  }
  return !String(value ?? '').trim();
}

function one2manyRowErrors(fieldName: string, rowKey: string) {
  return one2manyValidation.value.rowErrors[`${fieldName}:${rowKey}`] || [];
}

function one2manyRowHints(fieldName: string, row: One2ManyInlineRow) {
  const messages: string[] = [];
  onchangeLinePatches.value.forEach((patch) => {
    if (String(patch.field || '') !== fieldName) return;
    const rowKey = String(patch.row_key || '').trim();
    const rowId = Number(patch.row_id || 0);
    const matched = (rowKey && rowKey === row.key) || (rowId > 0 && Number(row.id || 0) === rowId);
    if (!matched) return;
    const warns = Array.isArray(patch.warnings) ? patch.warnings : [];
    warns.forEach((warn) => {
      const message = String(warn?.message || warn?.title || '').trim();
      if (message) messages.push(message);
      const reasonCode = String(warn?.reason_code || '').trim();
      if (reasonCode) messages.push(`原因码: ${reasonCode}`);
    });
    const rowState = String(patch.row_state || '').trim().toLowerCase();
    if (rowState) {
      messages.push(`联动状态: ${rowState}`);
    }
    if (Array.isArray(patch.command_hint) && patch.command_hint.length) {
      messages.push(`命令提示: ${patch.command_hint.join('/')}`);
    }
  });
  return Array.from(new Set(messages));
}

function applyOnchangeLinePatches(linePatches: OnchangeLinePatch[]) {
  if (!Array.isArray(linePatches) || !linePatches.length) return;
  linePatches.forEach((line) => {
    const fieldName = String(line.field || '').trim();
    if (!fieldName) return;
    const rowKey = String(line.row_key || '').trim();
    const rowId = Number(line.row_id || 0);
    const rows = ensureOne2manyRows(fieldName);
    const row = rows.find((item) => (rowKey && item.key === rowKey) || (rowId > 0 && Number(item.id || 0) === rowId));
    if (!row) return;
    const patch = line.patch;
    if (patch && typeof patch === 'object') {
      row.values = {
        ...(row.values || {}),
        ...(patch as Record<string, unknown>),
      };
    }
  });
}

function setRelationKeyword(name: string, keyword: string) {
  relationKeywords[name] = keyword;
  if (relationQueryTimers[name]) {
    clearTimeout(relationQueryTimers[name]);
  }
  relationQueryTimers[name] = setTimeout(() => {
    void queryRelationOptions(name, relationKeywords[name] || '');
  }, 260);
}

function filteredRelationOptions(name: string) {
  const rows = relationOptionsForField(name);
  const kw = relationKeyword(name).trim().toLowerCase();
  if (!kw) return rows;
  return rows.filter((row) => row.label.toLowerCase().includes(kw) || String(row.id).includes(kw));
}

function relationModel(name: string) {
  const descriptor = contract.value?.fields?.[name] as Record<string, unknown> | undefined;
  return String(descriptor?.relation || '').trim();
}

function sanitizeUiErrorMessage(raw: unknown, fallback: string) {
  const text = String(raw || '').trim();
  if (!text) return fallback;
  // Do not expose raw success envelopes as UI errors.
  if (text.startsWith('{') && text.includes('"ok"') && text.includes('"data"')) {
    if (text.includes('"ok": true') || text.includes('"records"')) {
      return fallback;
    }
  }
  return text;
}

function relationEntry(descriptor?: FieldDescriptor) {
  const entry = (descriptor as Record<string, unknown> | undefined)?.relation_entry;
  if (!entry || typeof entry !== 'object' || Array.isArray(entry)) return null;
  const row = entry as Record<string, unknown>;
  const actionId = toPositiveInt(row.action_id);
  const menuId = toPositiveInt(row.menu_id);
  const createModeRaw = String(row.create_mode || '').trim().toLowerCase();
  const createMode = createModeRaw === 'page' || createModeRaw === 'quick' ? createModeRaw : 'disabled';
  const defaultVals = row.default_vals && typeof row.default_vals === 'object' && !Array.isArray(row.default_vals)
    ? (row.default_vals as Record<string, unknown>)
    : {};
  return {
    model: String(row.model || '').trim(),
    actionId,
    menuId,
    canRead: row.can_read !== false,
    canCreate: Boolean(row.can_create),
    createMode,
    defaultVals,
    reasonCode: String(row.reason_code || '').trim(),
  };
}

function relationCreateMode(_fieldName: string, descriptor?: FieldDescriptor): 'page' | 'quick' | 'none' {
  const entry = relationEntry(descriptor);
  if (!entry) return 'none';
  if (entry.model === 'sc.dictionary' && entry.canCreate) {
    return 'quick';
  }
  if (entry.createMode === 'page' && entry.actionId) return 'page';
  if (entry.createMode === 'quick' && entry.canCreate) return 'quick';
  return 'none';
}

function relationDomain(descriptor?: FieldDescriptor) {
  const entry = relationEntry(descriptor);
  const out: unknown[] = [];
  const type = String(entry?.defaultVals?.type || '').trim();
  if (type) out.push(['type', '=', type]);
  return out.length ? out : undefined;
}

function runtimeRelationDomain(name: string) {
  const raw = (onchangeModifiersPatch.value?.[name] || {}) as Record<string, unknown>;
  const domain = raw.domain;
  if (!Array.isArray(domain)) return [];
  return domain;
}

function mergedRelationDomain(name: string, descriptor?: FieldDescriptor) {
  const base = relationDomain(descriptor);
  const runtime = runtimeRelationDomain(name);
  const out: unknown[] = [];
  if (Array.isArray(base)) out.push(...base);
  if (Array.isArray(runtime)) out.push(...runtime);
  return out.length ? out : undefined;
}

async function queryRelationOptions(name: string, keyword: string) {
  const descriptor = contract.value?.fields?.[name];
  const relation = relationModel(name);
  if (!relation) return;
  const entry = relationEntry(descriptor);
  if (entry && entry.canRead === false) {
    deniedRelationModels.add(relation);
    return;
  }
  if (deniedRelationModels.has(relation)) return;
  const search = String(keyword || '').trim();
  const domain = mergedRelationDomain(name, descriptor);
  try {
    const listed = await listRecords({
      model: relation,
      fields: ['id', 'name', 'display_name'],
      limit: search ? 40 : 80,
      order: 'id desc',
      domain,
      search_term: search || undefined,
      silentErrors: true,
    });
    const records = Array.isArray(listed?.records) ? listed.records : [];
    const mapped = records
      .map((row) => {
        const id = Number((row as Record<string, unknown>).id);
        if (!Number.isFinite(id) || id <= 0) return null;
        const label = String(
          (row as Record<string, unknown>).display_name
          || (row as Record<string, unknown>).name
          || `#${id}`,
        ).trim();
        return { id: Math.trunc(id), label };
      })
      .filter((item): item is RelationOption => Boolean(item));
    relationOptions.value = {
      ...relationOptions.value,
      [name]: mergeRelationOptions(relationOptions.value[name] || [], mapped),
    };
  } catch (err) {
    if (err instanceof ApiError) {
      const denied = err.status === 403 || String(err.reasonCode || '').toUpperCase() === 'PERMISSION_DENIED';
      if (denied) deniedRelationModels.add(relation);
    }
    // keep existing options if remote query fails
  }
}

async function ensureRelationFieldDescriptors(name: string) {
  const relation = one2manyRelationModel(name);
  if (!relation) return;
  if (relationFieldDescriptors.value[relation]) return;
  try {
    const response = await loadModelContractRaw(relation, {
      viewType: 'form',
      renderProfile: 'edit',
    });
    const fields = response?.data?.fields;
    if (fields && typeof fields === 'object') {
      relationFieldDescriptors.value = {
        ...relationFieldDescriptors.value,
        [relation]: fields as Record<string, FieldDescriptor>,
      };
    }
  } catch {
    // best effort; fallback to char fields
  }
}

async function openRelationCreateForm(fieldName: string, descriptor?: FieldDescriptor) {
  if (isInteractionLocked.value) return;
  const relation = String((descriptor as Record<string, unknown> | undefined)?.relation || '').trim();
  if (!relation) return;
  const mode = relationCreateMode(fieldName, descriptor);
  if (mode === 'none') {
    validationErrors.value = [`未找到 ${relation} 的新建入口，请联系管理员配置菜单动作`];
    return;
  }
  const entry = relationEntry(descriptor);
  const relationActionId = entry?.actionId || null;
  const menuId = entry?.menuId || 0;
  const quickCreate = async () => {
    const label = String(window.prompt('当前未配置维护页面，请输入新选项名称（快速新建）') || '').trim();
    if (!label) return;
    try {
      const vals: Record<string, unknown> = { ...(entry?.defaultVals || {}), name: label };
      if (relation === 'sc.dictionary' && typeof vals.type === 'string' && String(vals.type || '').trim()) {
        vals.code = label.toUpperCase().replace(/\\s+/g, '_').slice(0, 60);
      }
      const created = await createRecord({ model: relation, vals });
      const id = Number(created?.id || 0);
      if (Number.isFinite(id) && id > 0) {
        formData[fieldName] = Math.trunc(id);
        markFieldChanged(fieldName);
        relationKeywords[fieldName] = label;
        await queryRelationOptions(fieldName, label);
      }
      return;
    } catch (err) {
      const message = sanitizeUiErrorMessage(err instanceof Error ? err.message : err, '快速新建失败');
      validationErrors.value = [message];
      return;
    }
  };
  if (!relationActionId && mode === 'quick') {
    await quickCreate();
    return;
  }
  if (!relationActionId) {
    validationErrors.value = [`未找到 ${relation} 的维护页面入口，请联系管理员配置 action/menu`];
    return;
  }
  const defaultQuery = Object.entries(entry?.defaultVals || {}).reduce<Record<string, unknown>>((acc, [key, value]) => {
    if (!key) return acc;
    acc[`default_${key}`] = value;
    return acc;
  }, {});
  const nextQuery = pickContractNavQuery(route.query as Record<string, unknown>, {
    action_id: relationActionId,
    menu_id: menuId || undefined,
    view_mode: 'form',
    ...defaultQuery,
  });
  const returnUrl = `${window.location.pathname}${window.location.search}`;
  try {
    await router.push({
      name: 'model-form',
      params: { model: relation, id: 'new' },
      query: {
        ...nextQuery,
        return_url: encodeURIComponent(returnUrl),
        return_field: fieldName,
        return_model: model.value,
        return_action_id: actionId.value || undefined,
        return_menu_id: Number(route.query.menu_id || 0) || undefined,
      },
    });
  } catch (err) {
    if (relation === 'sc.dictionary' && mode === 'page' && entry?.canCreate && Object.keys(entry?.defaultVals || {}).length) {
      await quickCreate();
      return;
    }
    validationErrors.value = [sanitizeUiErrorMessage(err instanceof Error ? err.message : err, '跳转新建页面失败')];
  }
}

async function loadRelationOptions() {
  loadStage.value = 'load_relation_options';
  const fields = contract.value?.fields || {};
  const one2manyNames = Object.entries(fields)
    .filter(([, descriptor]) => fieldType(descriptor) === 'one2many')
    .map(([name]) => name);
  await Promise.all(one2manyNames.map((name) => ensureRelationFieldDescriptors(name)));
  const visibleRelationFields = new Set(
    layoutNodes.value
      .filter((node) => node.kind === 'field' && isFieldVisible(node.name))
      .map((node) => node.name),
  );
  const entries = Object.entries(fields).filter(([name]) => {
    if (!visibleRelationFields.size) return relationIds(name).length > 0;
    if (visibleRelationFields.has(name)) return true;
    return relationIds(name).length > 0;
  });
  const next: Record<string, RelationOption[]> = {};
  await Promise.all(entries.map(async ([name, descriptor]) => {
    if (!descriptor || typeof descriptor !== 'object') return;
    const type = fieldType(descriptor);
    if (!['many2one', 'many2many', 'one2many'].includes(type)) return;
    const relation = String((descriptor as Record<string, unknown>).relation || '').trim();
    if (!relation) return;
    const entry = relationEntry(descriptor as FieldDescriptor);
    if (entry && entry.canRead === false) {
      deniedRelationModels.add(relation);
      next[name] = [];
      return;
    }
    if (deniedRelationModels.has(relation)) {
      next[name] = [];
      return;
    }
    const domain = mergedRelationDomain(name, descriptor as FieldDescriptor);
    try {
      const listed = await listRecords({
        model: relation,
        fields: ['id', 'name', 'display_name'],
        limit: 80,
        order: 'id desc',
        domain,
        silentErrors: true,
      });
      const records = Array.isArray(listed?.records) ? listed.records : [];
      const mapped = records
        .map((row) => {
          const id = Number((row as Record<string, unknown>).id);
          if (!Number.isFinite(id) || id <= 0) return null;
          const label = String(
            (row as Record<string, unknown>).display_name
            || (row as Record<string, unknown>).name
            || `#${id}`,
          ).trim();
          return { id: Math.trunc(id), label };
        })
        .filter((item): item is RelationOption => Boolean(item));
      next[name] = mergeRelationOptions(next[name] || [], mapped);
    } catch (err) {
      if (err instanceof ApiError) {
        const denied = err.status === 403 || String(err.reasonCode || '').toUpperCase() === 'PERMISSION_DENIED';
        if (denied) deniedRelationModels.add(relation);
      }
      next[name] = [];
    }
  }));
  relationOptions.value = next;
}

function hasGroupAccess(groupsXmlids?: string[]) {
  if (!Array.isArray(groupsXmlids) || !groupsXmlids.length) return true;
  const userGroups = session.user?.groups_xmlids || [];
  return groupsXmlids.some((group) => userGroups.includes(group));
}

function toActionId(raw: unknown) {
  return toPositiveInt(raw);
}

function detectMethodName(key: string, payloadMethod: string) {
  return detectObjectMethodFromActionKey(key, payloadMethod);
}

function actionRequiresWritePermission(actionKey: string) {
  const lowered = String(actionKey || '').trim().toLowerCase();
  if (!lowered) return false;
  return ['edit', 'write', 'save', 'create', 'unlink', 'delete', 'archive', 'submit'].some((token) => lowered.includes(token));
}

function resolveSemanticActionGate(actionKey: string, fallbackEnabled: boolean, fallbackHint: string) {
  const key = String(actionKey || '').trim();
  let enabled = Boolean(fallbackEnabled);
  let hint = String(fallbackHint || '').trim();

  const semanticRow = semanticActionStateByKey.value[key];
  if (semanticRow) {
    enabled = enabled && semanticRow.enabled;
    if (!enabled && semanticRow.reason) {
      hint = semanticRow.reason;
    }
  }

  const requiresWrite = actionRequiresWritePermission(key);
  const verdictKey = requiresWrite ? 'write' : 'execute';
  const verdict = asRecord(semanticPermissionVerdicts.value[verdictKey]);
  if (verdict.allowed === false) {
    enabled = false;
    hint = asText(verdict.reason) || asText(verdict.reason_code) || hint || 'permission denied';
  }

  if (requiresWrite && isSemanticStateWriteBlocked.value) {
    enabled = false;
    hint = asText(semanticActionGatingVerdict.value.reason_code) || hint || 'STATE_BLOCKED';
  }

  return { enabled, hint };
}

const contractActions = computed<ContractAction[]>(() => {
  const mapSceneReadyAction = (row: Record<string, unknown>): ContractAction | null => {
    const protocol = normalizeSceneActionProtocol(row);
    const key = String(row.key || '').trim();
    if (!key) return null;
    const target = parseMaybeJsonRecord(row.target);
    const intent = String(row.intent || '').trim().toLowerCase();
    const tier = String(row.tier || '').trim().toLowerCase();
    const placement = String(row.placement || 'header').trim().toLowerCase();
    const actionId = toActionId(target.action_id) ?? toActionId(target.ref);
    const hasOpenTarget = Boolean(actionId || String(target.url || '').trim() || String(target.route || '').trim());
    const kind = hasOpenTarget || intent === 'ui.contract' ? 'open' : 'object';
    const semantic = tier === 'primary'
      ? 'primary_action'
      : tier === 'secondary'
        ? 'secondary_action'
        : '';
    const gated = resolveSemanticActionGate(key, true, '');
    return {
      key,
      label: String(row.label || key),
      kind,
      level: placement,
      actionId,
      methodName: detectMethodName(key, String(target.method || '').trim()),
      targetModel: String(target.model || model.value || '').trim(),
      context: parseMaybeJsonRecord(target.context_raw),
      domainRaw: String(target.domain_raw || '').trim(),
      target: String(target.target || '').trim(),
      url: String(target.url || target.route || '').trim(),
      enabled: gated.enabled,
      hint: gated.hint,
      semantic,
      buttonType: kind === 'object' ? 'object' : '',
      visibleProfiles: ['create', 'edit', 'readonly'],
      mutation: protocol?.mutation,
      refreshPolicy: protocol?.refresh_policy,
    };
  };

  const sceneReadyActions = Array.isArray(sceneReadyFormSurface.value.actions)
    ? sceneReadyFormSurface.value.actions as Array<Record<string, unknown>>
    : [];
  const preferSceneReadyActions = sceneReadyActions.length > 0 && !isProjectFormPage.value;
  const merged: Array<Record<string, unknown>> = [];
  if (preferSceneReadyActions) {
    merged.push(...sceneReadyActions);
  } else if (nativeLikeFormSurface.value) {
    merged.push(...formViewSurfaceActions.value);
    if (Array.isArray(contract.value?.buttons)) merged.push(...(contract.value?.buttons as Array<Record<string, unknown>>));
    if (Array.isArray(contract.value?.toolbar?.header)) merged.push(...(contract.value?.toolbar?.header as Array<Record<string, unknown>>));
    if (Array.isArray(contract.value?.toolbar?.sidebar)) merged.push(...(contract.value?.toolbar?.sidebar as Array<Record<string, unknown>>));
    if (Array.isArray(contract.value?.toolbar?.footer)) merged.push(...(contract.value?.toolbar?.footer as Array<Record<string, unknown>>));
  } else {
    if (Array.isArray(contract.value?.buttons)) merged.push(...(contract.value?.buttons as Array<Record<string, unknown>>));
    merged.push(...formViewSurfaceActions.value);
    if (Array.isArray(contract.value?.toolbar?.header)) merged.push(...(contract.value?.toolbar?.header as Array<Record<string, unknown>>));
    if (Array.isArray(contract.value?.toolbar?.sidebar)) merged.push(...(contract.value?.toolbar?.sidebar as Array<Record<string, unknown>>));
    if (Array.isArray(contract.value?.toolbar?.footer)) merged.push(...(contract.value?.toolbar?.footer as Array<Record<string, unknown>>));
  }

  const dedup = new Set<string>();
  const out: ContractAction[] = [];
  let actionOrder = 0;
  for (const row of merged) {
    if (preferSceneReadyActions) {
      const mapped = mapSceneReadyAction(row);
      if (!mapped || dedup.has(mapped.key)) continue;
      dedup.add(mapped.key);
      mapped.order = actionOrder;
      actionOrder += 1;
      out.push(mapped);
      continue;
    }
    const key = String(row.key || '').trim();
    if (!key || dedup.has(key)) continue;
    dedup.add(key);
    const payload = parseMaybeJsonRecord(row.payload);
    const kind = normalizeActionKind(row.kind);
    const buttonType = (asText(payload.type) || asText(row.type)).toLowerCase();
    const level = String(row.level || 'body').trim().toLowerCase();
    const actionId = toActionId(payload.action_id) ?? toActionId(payload.ref);
    const methodName = detectMethodName(key, String(payload.method || '').trim());
    const targetModel = String(row.target_model || row.model || model.value || '').trim();
    const context = parseMaybeJsonRecord(payload.context_raw);
    const domainRaw = String(payload.domain_raw || '').trim();
    const target = String(payload.target || '').trim();
    const groups = Array.isArray(row.groups_xmlids) ? (row.groups_xmlids as string[]) : [];
    const visibleProfiles = (
      Array.isArray(row.visible_profiles) ? row.visible_profiles : ['create', 'edit']
    )
      .map((item) => String(item || '').trim().toLowerCase())
      .filter((item): item is 'create' | 'edit' | 'readonly' => item === 'create' || item === 'edit' || item === 'readonly');
    const policy = evaluateActionPolicy(contract.value, key, policyContext.value);
    if (!policy.visible) continue;
    const byGroup = hasGroupAccess(groups);
    const needRecord = kind === 'object' || kind === 'server' || level === 'row' || level === 'smart';
    const fallbackEnabled = policy.enabled && byGroup && (!needRecord || Boolean(recordId.value));
    const fallbackHint = byGroup
      ? (needRecord && !recordId.value ? 'requires record id' : policy.reason)
      : 'permission denied';
    const gated = resolveSemanticActionGate(key, fallbackEnabled, fallbackHint);
    out.push({
      key,
      label: String(row.label || key),
      kind,
      level,
      actionId,
      methodName,
      targetModel,
      context,
      domainRaw,
      target,
      url: String(payload.url || '').trim(),
      enabled: gated.enabled,
      hint: gated.hint,
      semantic: policy.semantic,
      buttonType,
      order: actionOrder,
      visibleProfiles,
    });
    actionOrder += 1;
  }
  const levelRank = (level: string): number => {
    if (level === 'header') return 0;
    if (level === 'toolbar') return 1;
    if (level === 'smart') return 2;
    if (level === 'row') return 3;
    if (level === 'footer') return 4;
    return 5;
  };
  return out.sort((a, b) => {
    const levelDelta = levelRank(a.level) - levelRank(b.level);
    if (levelDelta !== 0) return levelDelta;
    const orderDelta = (a.order ?? 0) - (b.order ?? 0);
    if (orderDelta !== 0) return orderDelta;
    return a.key.localeCompare(b.key);
  });
});

const headerActions = computed(() => contractActions.value.filter((item) => {
  if (nativeLikeFormSurface.value) return item.level === 'header';
  return item.level === 'header' || item.level === 'toolbar';
}));
const bodyActions = computed(() => {
  if (isProjectFormPage.value) return [];
  return contractActions.value.filter((item) => item.level !== 'header' && item.level !== 'toolbar');
});

type SemanticFieldGroup = {
  name: string;
  label: string;
  collapsible: boolean;
  fields: string[];
};

const semanticFieldGroups = computed<Record<string, SemanticFieldGroup>>(() => {
  const raw = Array.isArray(contract.value?.field_groups) ? contract.value?.field_groups : [];
  const out: Record<string, SemanticFieldGroup> = {};
  for (const item of raw || []) {
    if (!item || typeof item !== 'object') continue;
    const row = item as Record<string, unknown>;
    const key = String(row.name || '').trim().toLowerCase();
    if (!key) continue;
    const fields = Array.isArray(row.fields) ? row.fields.map((f) => String(f || '').trim()).filter(Boolean) : [];
    out[key] = {
      name: key,
      label: String(row.label || (key === 'core' ? '核心信息' : '高级信息')).trim(),
      collapsible: Boolean(row.collapsible),
      fields,
    };
  }
  if (!Object.keys(out).length) {
    const profile = ((contract.value?.views?.form as Record<string, unknown> | undefined)?.form_profile
      || (contract.value as Record<string, unknown> | undefined)?.form_profile) as Record<string, unknown> | undefined;
    const core = Array.isArray(profile?.core_fields)
      ? profile?.core_fields.map((f) => String(f || '').trim()).filter(Boolean)
      : [];
    const advanced = Array.isArray(profile?.advanced_fields)
      ? profile?.advanced_fields.map((f) => String(f || '').trim()).filter(Boolean)
      : [];
    if (core.length || advanced.length) {
      out.core = {
        name: 'core',
        label: '核心信息',
        collapsible: false,
        fields: core,
      };
      out.advanced = {
        name: 'advanced',
        label: '高级信息',
        collapsible: true,
        fields: advanced,
      };
    }
  }
  return out;
});

const contractFieldSemantics = computed<Record<string, { semantic_type?: string; surface_role?: string; technical?: boolean }>>(() => {
  const out: Record<string, { semantic_type?: string; surface_role?: string; technical?: boolean }> = {};
  const raw = asRecord(contract.value).field_semantics;
  if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
    Object.entries(raw as Record<string, unknown>).forEach(([name, value]) => {
      if (!value || typeof value !== 'object' || Array.isArray(value)) return;
      const row = value as Record<string, unknown>;
      out[name] = {
        semantic_type: String(row.semantic_type || '').trim().toLowerCase(),
        surface_role: String(row.surface_role || '').trim().toLowerCase(),
        technical: Boolean(row.technical),
      };
    });
  }
  return out;
});

function fieldSemanticMeta(name: string) {
  const fromMap = contractFieldSemantics.value[name];
  if (fromMap) return fromMap;
  const descriptor = contract.value?.fields?.[name] as Record<string, unknown> | undefined;
  return {
    semantic_type: String(descriptor?.semantic_type || '').trim().toLowerCase(),
    surface_role: String(descriptor?.surface_role || '').trim().toLowerCase(),
    technical: Boolean(descriptor?.technical),
  };
}

const coreFieldNames = computed<string[]>(() => {
  const fromSemantic = Object.keys(contract.value?.fields || {}).filter((name) => fieldSemanticMeta(name).surface_role === 'core');
  if (fromSemantic.length) return fromSemantic;
  return semanticFieldGroups.value.core?.fields || [];
});
const advancedFieldNames = computed<string[]>(() => {
  const fromSemantic = Object.keys(contract.value?.fields || {}).filter((name) => fieldSemanticMeta(name).surface_role === 'advanced');
  if (fromSemantic.length) return fromSemantic;
  return semanticFieldGroups.value.advanced?.fields || [];
});
const coreFieldsLabel = computed(() => semanticFieldGroups.value.core?.label || '');
const hasAdvancedFields = computed(() => advancedFieldNames.value.length > 0);
const policyRequiredFields = computed(() => {
  const out = new Set<string>();
  const map = (contract.value?.action_policies || {}) as Record<string, { semantic?: string; enabled_when?: { required_fields?: string[] } }>;
  Object.values(map).forEach((policy) => {
    const semantic = String(policy?.semantic || '').trim().toLowerCase();
    if (semantic !== 'primary_action') return;
    const requiredFields = Array.isArray(policy?.enabled_when?.required_fields)
      ? policy.enabled_when?.required_fields
      : [];
    requiredFields.forEach((field) => {
      const normalized = String(field || '').trim();
      if (normalized) out.add(normalized);
    });
  });
  return out;
});
const sceneReadySceneKey = computed(() => String(route.query.scene_key || route.params.sceneKey || '').trim());
const sceneReadyEntry = computed<Record<string, unknown> | null>(() => {
  const key = sceneReadySceneKey.value;
  return key ? findSceneReadyEntry(session.sceneReadyContractV1, key) : null;
});
const strictContractMode = computed(() => isCoreSceneStrictMode(sceneReadySceneKey.value, sceneReadyEntry.value));
const strictContractGuard = computed<Record<string, unknown>>(() => {
  const entry = (sceneReadyEntry.value && typeof sceneReadyEntry.value === 'object')
    ? (sceneReadyEntry.value as Record<string, unknown>)
    : {};
  const direct = entry.contract_guard;
  if (direct && typeof direct === 'object' && !Array.isArray(direct)) return direct as Record<string, unknown>;
  const meta = (entry.meta && typeof entry.meta === 'object' && !Array.isArray(entry.meta))
    ? (entry.meta as Record<string, unknown>)
    : {};
  const nested = meta.contract_guard;
  if (nested && typeof nested === 'object' && !Array.isArray(nested)) return nested as Record<string, unknown>;
  return {};
});
const strictContractMissingSummary = computed(() => {
  if (!strictContractMode.value) return '';
  const raw = strictContractGuard.value.missing;
  if (!Array.isArray(raw) || !raw.length) return '';
  const missing = raw.map((item) => String(item || '').trim()).filter(Boolean);
  if (!missing.length) return '';
  return `严格模式检测到后端契约缺口：${missing.join(', ')}`;
});
const strictContractDefaultsSummary = computed(() => {
  if (!strictContractMode.value) return '';
  const raw = strictContractGuard.value.defaults_applied;
  if (!Array.isArray(raw) || !raw.length) return '';
  const defaults = raw.map((item) => String(item || '').trim()).filter(Boolean);
  if (!defaults.length) return '';
  return `当前由后端兜底补齐：${defaults.join(', ')}`;
});
const sceneValidationRequiredFields = computed<string[]>(() => {
  return resolveFormSceneReady(sceneReadyEntry.value).requiredFields;
});
const sceneReadyFormSurface = computed(() => {
  return resolveFormSceneReady(sceneReadyEntry.value);
});
const validationRequiredFields = computed(() => {
  const out = new Set<string>();
  const rules = Array.isArray(contract.value?.validation_rules) ? contract.value.validation_rules : [];
  rules.forEach((rule) => {
    if (!rule || typeof rule !== 'object') return;
    const item = rule as Record<string, unknown>;
    if (String(item.code || '').trim().toUpperCase() !== 'REQUIRED') return;
    const field = String(item.field || '').trim();
    if (!field) return;
    const profiles = Array.isArray(item.when_profiles)
      ? item.when_profiles.map((p) => String(p || '').trim().toLowerCase())
      : [];
    if (profiles.length && !profiles.includes(renderProfile.value)) return;
    out.add(field);
  });
  sceneValidationRequiredFields.value.forEach((field) => {
    out.add(field);
  });
  return out;
});
const sceneValidationErrorPrefix = `${ErrorCodes.SCENE_VALIDATION_REQUIRED}:`;
const sceneValidationPanel = computed(() => {
  const rows = validationErrors.value
    .map((item) => String(item || '').trim())
    .filter((item) => item.startsWith(sceneValidationErrorPrefix));
  if (!rows.length) return null;
  const normalized = rows
    .map((item) => item.slice(sceneValidationErrorPrefix.length).trim())
    .filter(Boolean);
  const sceneKey = String(route.query.scene_key || route.params.sceneKey || '').trim();
  const modelName = String(model.value || '').trim();
  const suggestedAction = resolveSceneValidationSuggestedAction({
    modelName,
    recordId: recordId.value,
    actionId: actionId.value,
    sceneKey,
    roleCode: runtimeRoleCode.value,
  });
  return {
    code: ErrorCodes.SCENE_VALIDATION_REQUIRED,
    message: normalized.join('；') || '场景约束校验未通过，请补齐必填字段。',
    hint: '请补齐必填字段后重试。',
    suggestedAction,
  };
});
const nonSceneValidationErrors = computed(() => (
  validationErrors.value.filter((item) => !String(item || '').trim().startsWith(sceneValidationErrorPrefix))
));
const contractVisibleFields = computed<string[]>(() => {
  const rows = Array.isArray(contract.value?.visible_fields) ? contract.value?.visible_fields : [];
  return rows.map((name) => String(name || '').trim()).filter(Boolean);
});
const fieldModifierMap = computed<Record<string, Record<string, unknown>>>(() => {
  const semanticFieldBehaviorMapRaw = asRecord(semanticFormSemantics.value.field_behavior_map);
  const semanticFieldBehaviorMap: Record<string, Record<string, unknown>> = {};
  Object.entries(semanticFieldBehaviorMapRaw).forEach(([name, raw]) => {
    const row = asRecord(raw);
    const key = String(name || '').trim();
    if (!key) return;
    semanticFieldBehaviorMap[key] = {
      readonly: row.readonly === true,
      required: row.required === true,
      invisible: row.invisible === true,
      widget: asText(row.widget),
    };
  });
  if (Object.keys(semanticFieldBehaviorMap).length > 0) {
    return semanticFieldBehaviorMap;
  }
  const formView = (contract.value?.views?.form || {}) as { field_modifiers?: Record<string, Record<string, unknown>> };
  return formView.field_modifiers || {};
});
const runtimeFieldStates = computed(() => {
  const names = Object.keys(contract.value?.fields || {});
  return buildRuntimeFieldStates({
    fieldNames: names,
    fieldModifiers: fieldModifierMap.value,
    modifierPatch: onchangeModifiersPatch.value,
    values: formData as Record<string, unknown>,
  });
});

function runtimeState(name: string) {
  return runtimeFieldStates.value[name] || { invisible: false, readonly: false, required: false };
}

function isFieldVisible(name: string) {
  if (isProjectQuickIntakeMode.value) {
    return ['name', 'manager_id', 'owner_id'].includes(String(name || '').trim());
  }
  const state = runtimeState(name);
  if (state.invisible) return false;
  const semantic = fieldSemanticMeta(name);
  if ((semantic.technical || semantic.semantic_type === 'technical') && !showHud.value) return false;
  if (semantic.surface_role === 'hidden' && !showHud.value) return false;
  const visible = contractVisibleFields.value;
  if (visible.length && !visible.includes(name)) return false;
  if (semantic.surface_role === 'core') return true;
  if (semantic.surface_role === 'advanced') return true;
  const core = coreFieldNames.value;
  const advanced = advancedFieldNames.value;
  const hasCore = core.length > 0;
  const hasAdvanced = advanced.length > 0;
  if (!hasCore && !hasAdvanced) return true;
  if (hasCore && core.includes(name)) return true;
  if (hasAdvanced && advanced.includes(name)) return true;
  // Some contracts only tag advanced fields; keep non-tagged fields visible in that case.
  if (!hasCore) return true;
  return renderProfile.value !== 'create';
}

function shouldShowRequiredMark(node: LayoutNode) {
  if (node.kind !== 'field' || node.readonly) return false;
  if (!node.required) return false;
  if (showHud.value) return true;
  if (renderProfile.value !== 'create') return true;
  const policyRequired = policyRequiredFields.value;
  const validationRequired = validationRequiredFields.value;
  if (policyRequired.size || validationRequired.size) {
    return policyRequired.has(node.name) || validationRequired.has(node.name);
  }
  return coreFieldNames.value.includes(node.name);
}

function isMissingRequiredValue(value: unknown) {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim().length === 0;
  if (typeof value === 'number') return !Number.isFinite(value) || value <= 0;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'boolean') return false;
  if (typeof value === 'object') return Object.keys(value as Record<string, unknown>).length === 0;
  return false;
}

function normalizeLayoutNodeKind(rawType: unknown, sourceKey?: string, nodeRaw?: unknown): string {
  const kind = String(rawType || '').trim().toLowerCase();
  const source = String(sourceKey || '').trim().toLowerCase();
  if (kind === 'tab' || source === 'tabs' || source === 'pages') return 'page';
  if (kind === 'notebook' || source === 'notebook') return 'notebook';
  if (kind === 'group' || kind === 'sheet' || kind === 'page' || kind === 'header' || kind === 'field') return kind;
  if (kind === 'container' && nodeRaw && typeof nodeRaw === 'object' && !Array.isArray(nodeRaw)) {
    const node = nodeRaw as Record<string, unknown>;
    const attrs = node.attributes && typeof node.attributes === 'object' && !Array.isArray(node.attributes)
      ? node.attributes as Record<string, unknown>
      : {};
    const attrName = String(attrs.name || '').trim().toLowerCase();
    const attrClass = String(attrs.class || '').trim().toLowerCase();
    if (attrName === 'button_box' || attrClass.includes('oe_button_box')) return 'group';
    if (attrClass.includes('oe_title')) return 'header';
    if (Array.isArray(node.pages) || Array.isArray(node.tabs)) return 'notebook';
    if (Array.isArray(node.children)) {
      const hasCols = Number(node.cols || node.col || attrs.cols || attrs.col) > 0;
      const hasLabel = Boolean(String(node.title || node.string || node.label || attrs.string || '').trim());
      if (hasCols || hasLabel) return 'group';
    }
  }
  if (!kind && nodeRaw && typeof nodeRaw === 'object' && !Array.isArray(nodeRaw)) {
    const node = nodeRaw as Record<string, unknown>;
    const attrs = node.attributes && typeof node.attributes === 'object' && !Array.isArray(node.attributes)
      ? node.attributes as Record<string, unknown>
      : {};
    if (Array.isArray(node.pages) || Array.isArray(node.tabs)) return 'notebook';
    if (Array.isArray(node.children)) {
      const hasCols = Number(node.cols || node.col || attrs.cols || attrs.col) > 0;
      const hasLabel = Boolean(String(node.title || node.string || node.label || attrs.string || '').trim());
      if (hasCols || hasLabel) return 'group';
    }
  }
  return kind;
}

function normalizeLayoutChildNode(childRaw: unknown, sourceKey: string): unknown {
  if (!childRaw || typeof childRaw !== 'object' || Array.isArray(childRaw)) return childRaw;
  const child = childRaw as Record<string, unknown>;
  const normalizedKind = normalizeLayoutNodeKind(child.type, sourceKey, child);
  if (!normalizedKind) return childRaw;
  const currentKind = String(child.type || '').trim().toLowerCase();
  if (currentKind === normalizedKind) return childRaw;
  return {
    ...child,
    type: normalizedKind,
  };
}

function forEachLayoutChildren(
  node: Record<string, unknown>,
  visitor: (child: unknown, sourceKey: string, index: number) => void,
) {
  const pages = Array.isArray(node.pages) ? node.pages : null;
  const tabs = Array.isArray(node.tabs) ? node.tabs : null;
  const primaryTabSource = pages && pages.length ? ['pages', pages] : (tabs && tabs.length ? ['tabs', tabs] : null);
  if (primaryTabSource) {
    const [sourceKey, children] = primaryTabSource as [string, unknown[]];
    children.forEach((child, index) => visitor(child, sourceKey, index));
  }
  ['children', 'nodes', 'items'].forEach((key) => {
    const children = node[key];
    if (!Array.isArray(children)) return;
    children.forEach((child, index) => visitor(child, key, index));
  });
}

function resolveLayoutNodeLabel(node: Record<string, unknown>): string {
  const attrs = node.attributes && typeof node.attributes === 'object' && !Array.isArray(node.attributes)
    ? node.attributes as Record<string, unknown>
    : {};
  const attrName = String(attrs.name || '').trim();
  const safeAttrName = isHumanReadableLayoutLabel(attrName) ? attrName : '';
  return String(
    node.title
    || node.string
    || node.label
    || attrs.string
    || attrs.title
    || safeAttrName
    || (isHumanReadableLayoutLabel(node.name) ? node.name : '')
    || '',
  ).trim();
}

function resolveLayoutNodeGroups(node: Record<string, unknown>): string[] {
  const attrs = node.attributes && typeof node.attributes === 'object' && !Array.isArray(node.attributes)
    ? node.attributes as Record<string, unknown>
    : {};
  const seen = new Set<string>();
  const push = (raw: unknown) => {
    if (Array.isArray(raw)) {
      raw.forEach((item) => push(item));
      return;
    }
    const text = String(raw || '').trim();
    if (!text) return;
    text.split(',').map((item) => item.trim()).filter(Boolean).forEach((group) => {
      seen.add(group);
    });
  };
  [
    node.groups_xmlids,
    node.groupsXmlids,
    node.groups,
    attrs.groups_xmlids,
    attrs.groupsXmlids,
    attrs.groups,
  ].forEach((value) => push(value));
  return Array.from(seen);
}

function mergeLayoutNodeGroups(...groupLists: Array<string[] | undefined | null>): string[] {
  const seen = new Set<string>();
  groupLists.forEach((groups) => {
    if (!Array.isArray(groups)) return;
    groups.forEach((group) => {
      const text = String(group || '').trim();
      if (text) seen.add(text);
    });
  });
  return Array.from(seen);
}

function isHumanReadableLayoutLabel(labelRaw: unknown): boolean {
  const label = String(labelRaw || '').trim();
  if (!label) return false;
  if (label.includes('_')) return false;
  if (/^[a-z0-9.:-]+$/i.test(label)) return false;
  return true;
}

function resolveLayoutNodeColumns(node: Record<string, unknown>): 1 | 2 {
  const attrs = node.attributes && typeof node.attributes === 'object' && !Array.isArray(node.attributes)
    ? node.attributes as Record<string, unknown>
    : {};
  const candidates = [node.cols, node.col, attrs.cols, attrs.col];
  for (const raw of candidates) {
    const numeric = Number(raw);
    if (Number.isFinite(numeric) && numeric === 1) return 1;
  }
  return 2;
}

function collectSceneValidationPrecheckErrors(fieldLabels: Record<string, string>): string[] {
  const out: string[] = [];
  for (const field of sceneValidationRequiredFields.value) {
    if (!isFieldVisible(field)) continue;
    const value = formData[field];
    if (isMissingRequiredValue(value)) {
      out.push(`${ErrorCodes.SCENE_VALIDATION_REQUIRED}: ${fieldLabels[field] || field} 为必填项`);
    }
  }
  return Array.from(new Set(out)).slice(0, 5);
}

const layoutNodes = computed<LayoutNode[]>(() => {
  const fieldMap = contract.value?.fields || {};
  const formLayout = contract.value?.views?.form?.layout;
  const order = Array.isArray(formLayout) && formLayout.length ? formLayout : semanticFormLayout.value;
  const fieldGroups = contract.value?.permissions?.field_groups || {};
  const used = new Set<string>();
  const nodes: LayoutNode[] = [];

  function pushField(nameRaw: unknown, viewLabelRaw?: unknown, inheritedGroups?: string[]) {
    const name = String(nameRaw || '').trim();
    if (!name || used.has(name)) return;
    const groups = mergeLayoutNodeGroups(
      Array.isArray(fieldGroups[name]?.groups_xmlids) ? fieldGroups[name]?.groups_xmlids : [],
      inheritedGroups,
    );
    if (!hasGroupAccess(groups)) return;
    const descriptor = fieldMap[name];
    if (!descriptor) return;
    const resolved = evaluateFieldPolicy(
      contract.value,
      name,
      {
        required: Boolean(descriptor?.required),
        readonly: Boolean(descriptor?.readonly),
      },
      policyContext.value,
    );
    if (!resolved.visible) return;
      used.add(name);
      const state = runtimeState(name);
      const viewLabel = String(viewLabelRaw || '').trim();
      nodes.push({
        key: `field_${name}`,
        kind: 'field',
        name,
        label: viewLabel || String(descriptor?.string || name),
        readonly: Boolean(
          resolved.readonly
          || state.readonly
          || (recordId.value ? !rights.value.write : !rights.value.create)
          || !canPersistBySceneRuntime.value
        ),
        required: Boolean(resolved.required || state.required),
        descriptor,
        groupsXmlids: groups,
      });
  }

  function walkLayout(nodeRaw: unknown, parentKey: string, inheritedGroups: string[] = []) {
    if (!nodeRaw || typeof nodeRaw !== 'object') return;
    const node = nodeRaw as Record<string, unknown>;
    const kind = normalizeLayoutNodeKind(node.type, undefined, node);
    if (!kind) return;
    const label = resolveLayoutNodeLabel(node);
    const groupsXmlids = mergeLayoutNodeGroups(inheritedGroups, resolveLayoutNodeGroups(node));
    if (!hasGroupAccess(groupsXmlids)) return;
    const nodeKey = `${parentKey}_${kind}_${String(node.name || label || nodes.length)}`;

    if (kind === 'header' || kind === 'sheet' || kind === 'group' || kind === 'notebook' || kind === 'page') {
      nodes.push({
        key: `layout_${nodeKey}`,
        kind: kind as LayoutNode['kind'],
        name: String(node.name || '').trim(),
        label,
        readonly: true,
        required: false,
        groupsXmlids,
      });
    }
    if (kind === 'field') {
      const fieldInfo = node.fieldInfo && typeof node.fieldInfo === 'object' && !Array.isArray(node.fieldInfo)
        ? (node.fieldInfo as Record<string, unknown>)
        : null;
      pushField(node.name, node.title || node.string || node.label || fieldInfo?.label, groupsXmlids);
      return;
    }
    forEachLayoutChildren(node, (child, sourceKey, index) => {
      walkLayout(normalizeLayoutChildNode(child, sourceKey), `${nodeKey}_${sourceKey}_${index}`, groupsXmlids);
    });
  }

  if (Array.isArray(order)) {
    order.forEach((item, index) => walkLayout(item, `root_${index}`));
  }
  if (!nodes.some((node) => node.kind === 'field')) {
    const fallback = contractVisibleFields.value.length
      ? contractVisibleFields.value
      : [...coreFieldNames.value, ...advancedFieldNames.value];
    const fallbackFields = fallback.length ? fallback : Object.keys(fieldMap).slice(0, 16);
    fallbackFields.forEach((name) => pushField(name));
  }

  return nodes;
});

function dividerDefaultLabel(kind: LayoutNode['kind']) {
  if (kind === 'header') return '头部';
  if (kind === 'sheet') return '主体';
  if (kind === 'notebook') return '页签';
  if (kind === 'page') return '页面';
  if (kind === 'group') return '分组';
  return '信息';
}

function mapDetailFieldLabel(fieldName: string, fallbackLabel: string): string {
  const label = String(fallbackLabel || '').trim();
  return label || fieldName;
}

function normalizeDetailSectionTree(sections: LayoutTreeSection[]): LayoutTreeSection[] {
  let pageIndex = 0;
  let groupIndex = 0;
  let notebookIndex = 0;

  const normalizeFallbackTitle = (titleRaw: string): string => {
    const title = String(titleRaw || '').trim();
    if (title.toLowerCase() === 'button_box') return '统计动作';
    return title;
  };

  const walk = (node: LayoutTreeSection): LayoutTreeSection => {
    let title = normalizeFallbackTitle(node.title);
    if (node.kind === 'page') {
      if (!title) title = `页面${pageIndex + 1}`;
      pageIndex += 1;
    } else if (node.kind === 'group') {
      if (!title) title = `分组${groupIndex + 1}`;
      groupIndex += 1;
    } else if (node.kind === 'notebook') {
      if (!title) title = `页签${notebookIndex + 1}`;
      notebookIndex += 1;
    }
    return {
      ...node,
      title,
      children: node.children.map((child) => walk(child)),
    };
  };
  return sections.map((section) => walk(section));
}

const layoutTrees = computed<LayoutTreeSection[]>(() => {
  const fieldMap = contract.value?.fields || {};
  const formLayout = contract.value?.views?.form?.layout;
  const order = Array.isArray(formLayout) && formLayout.length ? formLayout : semanticFormLayout.value;
  const fieldGroups = contract.value?.permissions?.field_groups || {};
  const roots: LayoutTreeSection[] = [];
  const rootDefault: LayoutTreeSection = {
    key: 'layout_root_default',
    title: coreFieldsLabel.value || '核心信息',
    kind: 'default',
    columns: 2,
    fields: [],
    children: [],
  };
  const structuralKinds = new Set<LayoutTreeSection['kind']>(['header', 'sheet', 'group', 'notebook', 'page']);

  function buildFieldNode(nameRaw: unknown, viewLabelRaw?: unknown, inheritedGroups?: string[]): LayoutNode | null {
    const name = String(nameRaw || '').trim();
    if (!name) return null;
    const groups = mergeLayoutNodeGroups(
      Array.isArray(fieldGroups[name]?.groups_xmlids) ? fieldGroups[name]?.groups_xmlids : [],
      inheritedGroups,
    );
    if (!hasGroupAccess(groups)) return null;
    const descriptor = fieldMap[name];
    if (!descriptor) return null;
    const resolved = evaluateFieldPolicy(
      contract.value,
      name,
      {
        required: Boolean(descriptor?.required),
        readonly: Boolean(descriptor?.readonly),
      },
      policyContext.value,
    );
    if (!resolved.visible) return null;
    const state = runtimeState(name);
    const viewLabel = String(viewLabelRaw || '').trim();
    return {
      key: `tree_field_${name}`,
      kind: 'field',
      name,
      label: mapDetailFieldLabel(name, viewLabel || String(descriptor?.string || name)),
      readonly: Boolean(
        resolved.readonly
        || state.readonly
        || (recordId.value ? !rights.value.write : !rights.value.create)
        || !canPersistBySceneRuntime.value
      ),
      required: Boolean(resolved.required || state.required),
      descriptor,
      groupsXmlids: groups,
    };
  }

  function appendField(parent: LayoutTreeSection | null, field: LayoutNode | null) {
    if (!field) return;
    if (parent) {
      parent.fields.push(field);
      return;
    }
    rootDefault.fields.push(field);
  }

  function walk(nodeRaw: unknown, parent: LayoutTreeSection | null, parentKey: string, inheritedGroups: string[] = []) {
    if (!nodeRaw || typeof nodeRaw !== 'object') return;
    const node = nodeRaw as Record<string, unknown>;
    const kind = normalizeLayoutNodeKind(node.type, undefined, node);
    if (!kind) return;
    const label = resolveLayoutNodeLabel(node);
    const nodeGroups = mergeLayoutNodeGroups(inheritedGroups, resolveLayoutNodeGroups(node));
    if (!hasGroupAccess(nodeGroups)) return;
    const nodeKey = `${parentKey}_${kind}_${String(node.name || label || roots.length)}`;
    if (kind === 'field') {
      const fieldInfo = node.fieldInfo && typeof node.fieldInfo === 'object' && !Array.isArray(node.fieldInfo)
        ? (node.fieldInfo as Record<string, unknown>)
        : null;
      appendField(parent, buildFieldNode(node.name, node.title || node.string || node.label || fieldInfo?.label, nodeGroups));
      return;
    }
    const nextParent = structuralKinds.has(kind as LayoutTreeSection['kind'])
      ? {
        key: `tree_${nodeKey}`,
        title: label || dividerDefaultLabel(kind as LayoutNode['kind']),
        kind: kind as LayoutTreeSection['kind'],
        columns: resolveLayoutNodeColumns(node),
        fields: [],
        children: [],
        groupsXmlids: nodeGroups,
      }
      : parent;
    if (nextParent && nextParent !== parent) {
      if (parent) parent.children.push(nextParent);
      else roots.push(nextParent);
    }
    forEachLayoutChildren(node, (child, sourceKey, index) => {
      walk(normalizeLayoutChildNode(child, sourceKey), nextParent, `${nodeKey}_${sourceKey}_${index}`, nodeGroups);
    });
  }

  if (Array.isArray(order)) {
    order.forEach((item, index) => walk(item, null, `root_${index}`));
  }

  const hasVisibleField = (nodes: LayoutTreeSection[]): boolean => nodes.some(
    (node) => node.fields.length > 0 || hasVisibleField(node.children),
  );

  if (!hasVisibleField(roots) && rootDefault.fields.length === 0) {
    const fallback = contractVisibleFields.value.length
      ? contractVisibleFields.value
      : [...coreFieldNames.value, ...advancedFieldNames.value];
    const fallbackFields = fallback.length ? fallback : Object.keys(fieldMap).slice(0, 16);
    fallbackFields.forEach((name) => appendField(null, buildFieldNode(name)));
  }

  if (rootDefault.fields.length > 0) roots.push(rootDefault);

  const prune = (section: LayoutTreeSection): LayoutTreeSection | null => {
    if (!hasGroupAccess(section.groupsXmlids)) return null;
    const children = section.children
      .map((child) => prune(child))
      .filter((child): child is LayoutTreeSection => Boolean(child));
    const visibleFieldCount = section.fields.filter((field) => isFieldVisible(field.name)).length;
    if (visibleFieldCount <= 0 && !children.length && section.kind === 'group') return null;
    return {
      ...section,
      groupsXmlids: section.groupsXmlids,
      children,
    };
  };

  const normalizedRoots = roots
    .map((section) => prune(section))
    .filter((section): section is LayoutTreeSection => Boolean(section));

  return normalizeDetailSectionTree(normalizedRoots);
});

async function goBackFromDetail() {
  if (busy.value) return;
  const fallback = session.resolveLandingPath('/');
  if (window.history.length > 1) {
    router.back();
    return;
  }
  await router.push({ path: fallback, query: resolveWorkspaceContextQuery() });
}

function visibleTreeSectionFields(section: LayoutTreeSection) {
  return section.fields.filter((node) => isFieldVisible(node.name));
}

function treeSectionTemplateFields(section: LayoutTreeSection): FormSectionFieldSchema[] {
  return applyFieldDisplayValues(buildSectionFieldSchemas(visibleTreeSectionFields(section)));
}

const buildSectionFieldSchemas = createFormSectionFieldSchemaBuilder({
  resolveFieldType: (descriptor) => fieldType(descriptor) || 'char',
  resolveRequired: (field) => shouldShowRequiredMark(field as LayoutNode),
  resolveSpanClass: (field) => resolveFieldSpanClass({
    fieldName: field.name,
    fieldType: fieldType(field.descriptor),
  }),
  resolveRawValue: (fieldName) => formData[fieldName],
  resolveMany2oneValue: many2oneValue,
  normalizeDateInputValue: toDateInputValue,
  normalizeDatetimeInputValue: toDatetimeInputValue,
  resolveTextInputValue: inputFieldValue,
  resolveInputPlaceholder: (label) => resolveInputPlaceholder(label),
  resolveSelectionOptions: (descriptor) => mapDescriptorSelectionOptions(descriptor),
  resolveRelationOptions: (fieldName) => mapRelationOptions(relationOptionsForField(fieldName)),
  resolveRelationCreateMode: (fieldName, descriptor) => relationCreateMode(fieldName, descriptor),
  many2oneCreateToken: MANY2ONE_CREATE_OPTION,
});

function applyFieldDisplayValues(fields: FormSectionFieldSchema[]): FormSectionFieldSchema[] {
  return fields.map((field) => {
    if (field.type !== 'many2one') return field;
    const label = many2oneLabel(field.name);
    if (!label) return field;
    return {
      ...field,
      value: label,
    };
  });
}

const detailShells = computed<DetailShellView[]>(() => buildDetailShellViewsFromTree({
  layoutTrees: layoutTrees.value,
  visibleSectionFieldCount: (section) => visibleTreeSectionFields(section).length,
  buildSectionFields: treeSectionTemplateFields,
  preferNativeFormSurface: preferNativeFormSurface.value,
  projectCreateMode: isProjectCreatePage.value,
  renderProfile: renderProfile.value,
}));

function tabSignature(tab: NonNullable<DetailShellView['tabs']>[number]): string {
  const label = String(tab.label || '').trim().toLowerCase();
  const sectionKeys = (tab.sections || []).map((section) => String(section.key || '').trim()).filter(Boolean);
  const fieldKeys = (tab.sections || [])
    .flatMap((section) => (section.fields || []).map((field) => String(field.name || '').trim()))
    .filter(Boolean);
  const keys = fieldKeys.length ? fieldKeys : sectionKeys;
  return `${label}::${Array.from(new Set(keys)).join('|')}`;
}

function dedupeTabs(tabs: NonNullable<DetailShellView['tabs']>): NonNullable<DetailShellView['tabs']> {
  const seen = new Set<string>();
  const result: NonNullable<DetailShellView['tabs']> = [];
  for (const tab of tabs) {
    const signature = tabSignature(tab);
    if (seen.has(signature)) continue;
    seen.add(signature);
    result.push(tab);
  }
  return result;
}

function isRenderableSection(section: DetailSectionView): boolean {
  const fields = Array.isArray(section.fields) ? section.fields.length : 0;
  if (fields > 0) return true;
  const title = String(section.title || '').trim();
  const hint = String(section.hint || '').trim();
  if (hint) return true;
  if (!title) return false;
  if (/^信息分组\s*\d*$/.test(title)) return false;
  return true;
}

function dedupeNativeSectionFields(section: DetailSectionView, seenFields: Set<string>): DetailSectionView {
  const fields = section.fields.filter((field) => {
    const name = String(field.name || '').trim();
    if (!name) return true;
    if (seenFields.has(name)) return false;
    seenFields.add(name);
    return true;
  });
  return {
    ...section,
    fields,
  };
}

function dedupeNativeShellFields(shell: DetailShellView, seenFields: Set<string>): DetailShellView {
  const sections = Array.isArray(shell.sections)
    ? shell.sections.map((section) => dedupeNativeSectionFields(section, seenFields))
    : shell.sections;
  const tabs = Array.isArray(shell.tabs)
    ? shell.tabs.map((tab) => ({
      ...tab,
      sections: tab.sections.map((section) => dedupeNativeSectionFields(section, seenFields)),
    }))
    : shell.tabs;
  return {
    ...shell,
    sections,
    tabs,
  };
}

const normalizedDetailShells = computed<DetailShellView[]>(() => {
  const shells = detailShells.value;
  if (!nativeLikeFormSurface.value) return shells;
  const seenFields = new Set<string>();
  return shells
    .filter((shell) => shell.kind !== 'header')
    .map((shell) => dedupeNativeShellFields(shell, seenFields))
    .map((shell) => {
      const normalizedSections = Array.isArray(shell.sections)
        ? shell.sections.filter((section) => isRenderableSection(section))
        : shell.sections;
      if (!Array.isArray(shell.tabs) || shell.tabs.length <= 1) return shell;
      const filteredTabs = shell.tabs
        .filter((tab) => {
          const label = String(tab.label || '').trim();
          const hasSemanticLabel = Boolean(label);
          const hasRenderableSection = Array.isArray(tab.sections) && tab.sections.some((sec) => (
            sec.fields.length > 0 || Boolean(String(sec.title || '').trim()) || Boolean(String(sec.hint || '').trim())
          ));
          return hasSemanticLabel || hasRenderableSection;
        });
      const dedupedTabs = dedupeTabs(filteredTabs.length ? filteredTabs : shell.tabs);
      return {
        ...shell,
        title: '页签',
        sections: normalizedSections,
        tabs: dedupedTabs.length ? dedupedTabs : shell.tabs,
      };
    })
    .map((shell) => {
      if (Array.isArray(shell.tabs) && shell.tabs.length > 0) return shell;
      const normalizedSections = Array.isArray(shell.sections)
        ? shell.sections.filter((section) => isRenderableSection(section))
        : shell.sections;
      return {
        ...shell,
        sections: normalizedSections,
      };
    })
    .filter((shell) => {
      const sectionSize = Array.isArray(shell.sections) ? shell.sections.length : 0;
      const tabSize = Array.isArray(shell.tabs) ? shell.tabs.length : 0;
      return sectionSize > 0 || tabSize > 0;
    });
});

const GENERIC_SHELL_TITLES = new Set(['default', '头部', '页签容器']);

function normalizeShellSummaryTitle(shell: DetailShellView): string {
  const rawTitle = String(shell.title || '').trim();
  if (rawTitle && !GENERIC_SHELL_TITLES.has(rawTitle)) return rawTitle;
  if (Array.isArray(shell.tabs) && shell.tabs.length > 0) return '页签';
  if (shell.kind === 'sheet') return '项目';
  if (shell.kind === 'page') return '页面';
  return '';
}

const structureProjectionSummary = computed(() => {
  const shells = normalizedDetailShells.value;
  const shellCount = shells.length;
  const sectionCount = shells.reduce((acc, shell) => acc + (Array.isArray(shell.sections) ? shell.sections.length : 0), 0);
  const tabCount = shells.reduce((acc, shell) => acc + (Array.isArray(shell.tabs) ? shell.tabs.length : 0), 0);
  const shellTitles = Array.from(new Set(shells
    .map((shell) => normalizeShellSummaryTitle(shell))
    .filter(Boolean)))
    .slice(0, 6)
    .join(' / ');
  return {
    shellCount,
    sectionCount,
    tabCount,
    shellTitles,
  };
});

function countLayoutKinds(layoutRaw: unknown): { notebook: number; page: number } {
  const result = { notebook: 0, page: 0 };
  const walk = (nodeRaw: unknown) => {
    if (!nodeRaw || typeof nodeRaw !== 'object' || Array.isArray(nodeRaw)) return;
    const node = nodeRaw as Record<string, unknown>;
    const kind = normalizeLayoutNodeKind(node.type, undefined, node);
    if (kind === 'notebook') result.notebook += 1;
    if (kind === 'page') result.page += 1;
    forEachLayoutChildren(node, (child, sourceKey) => {
      walk(normalizeLayoutChildNode(child, sourceKey));
    });
  };
  if (Array.isArray(layoutRaw)) {
    layoutRaw.forEach((node) => walk(node));
  }
  return result;
}


function countLayoutTreeKinds(sectionsRaw: unknown): { notebook: number; page: number } {
  const result = { notebook: 0, page: 0 };
  const walk = (sectionRaw: unknown) => {
    if (!sectionRaw || typeof sectionRaw !== 'object' || Array.isArray(sectionRaw)) return;
    const section = sectionRaw as Record<string, unknown>;
    const kind = String(section.kind || '').trim().toLowerCase();
    if (kind === 'notebook') result.notebook += 1;
    if (kind === 'page') result.page += 1;
    const children = section.children;
    if (Array.isArray(children)) {
      children.forEach((child) => walk(child));
    }
  };
  if (Array.isArray(sectionsRaw)) {
    sectionsRaw.forEach((section) => walk(section));
  }
  return result;
}

function countShellTabs(shellsRaw: unknown): { shell: number; tab: number } {
  if (!Array.isArray(shellsRaw)) return { shell: 0, tab: 0 };
  return shellsRaw.reduce((acc, shellRaw) => {
    if (!shellRaw || typeof shellRaw !== 'object' || Array.isArray(shellRaw)) return acc;
    const shell = shellRaw as Record<string, unknown>;
    acc.shell += 1;
    const tabs = shell.tabs;
    if (Array.isArray(tabs)) acc.tab += tabs.length;
    return acc;
  }, { shell: 0, tab: 0 });
}

const contractTabAuditSummary = computed(() => {
  const sourceLayout = countLayoutKinds(contract.value?.views?.form?.layout);
  const semanticLayout = countLayoutKinds(semanticFormLayout.value);
  const layoutTreeKinds = countLayoutTreeKinds(layoutTrees.value as unknown);
  const rawShell = countShellTabs(detailShells.value as unknown);
  const projectedTabs = structureProjectionSummary.value.tabCount;
  const sourcePageCount = sourceLayout.page;
  return {
    source_layout: sourceLayout,
    semantic_layout: semanticLayout,
    layout_tree: layoutTreeKinds,
    detail_shell_raw: rawShell,
    single_source: 'views.form.layout',
    projected_tabs: projectedTabs,
    delta_from_layout_page: sourcePageCount - projectedTabs,
  };
});

const showStructureProjectionSummary = computed(() => structureAuditMode.value && projectDetailStructureAlignMode.value && !isProjectCreatePage.value);

function onTemplateFieldChange(payload: FormSectionFieldChange) {
  dispatchTemplateFieldChange(payload, {
    onBoolean: (name, value) => setBooleanField(name, value),
    onSelection: (name, value) => setSelectionField(name, value),
    onMany2one: (name, descriptor, value) => setMany2oneField(name, descriptor, value),
    onText: (name, value) => setTextField(name, value),
  });
}

const relationFallbackAdapter = computed<RelationFallbackAdapter>(() => createRelationFallbackAdapter({
  busy: busy.value,
  showOne2manyErrors: showOne2manyErrors.value,
  relationKeyword,
  setRelationKeyword,
  relationIds,
  filteredRelationOptions,
  setRelationMultiField,
  addOne2manyRow,
  one2manySummary,
  visibleOne2manyRows,
  one2manyRowStateLabel,
  one2manyColumns,
  setOne2manyRowField,
  removeOne2manyRow,
  one2manyRowErrors,
  one2manyRowHints,
  removedOne2manyRows,
  restoreOne2manyRow,
  one2manyRowLabel,
  selectPlaceholder: resolveSelectPlaceholder,
  one2manyColumnInputType,
  one2manyColumnDisplayValue,
  inputFieldValue,
  fieldInputType,
  inputPlaceholder: resolveInputPlaceholder,
  setTextField,
}));

const contractReadiness = computed<FormContractReadiness>(() => {
  if (!contract.value) {
    return { usable: false, issues: ['contract not loaded'], fieldCount: 0, layoutFieldCount: 0, visibleCandidateCount: 0 };
  }
  return analyzeFormContractReadiness(contract.value, { requirePureFormViewType: false });
});

function normalizeComparable(value: unknown) {
  if (Array.isArray(value) && value.every((item) => typeof item === 'number')) {
    return JSON.stringify([...value].sort((a, b) => a - b));
  }
  if (Array.isArray(value)) return JSON.stringify(value);
  if (value && typeof value === 'object') return JSON.stringify(value);
  return String(value ?? '');
}

function comparableFieldValue(name: string, value: unknown) {
  const descriptor = contract.value?.fields?.[name];
  const ttype = fieldType(descriptor);
  if (ttype === 'many2many') {
    return JSON.stringify(normalizeRelationIds(value).sort((a, b) => a - b));
  }
  if (ttype === 'one2many') {
    const rows = one2manyFieldRows(name).map((row) => ({
      id: row.id || 0,
      isNew: row.isNew,
      removed: row.removed,
      dirty: row.dirty,
      values: row.values || {},
    }));
    return JSON.stringify(rows);
  }
  return normalizeComparable(value);
}

function isFieldWritable(name: string) {
  const node = layoutNodes.value.find((item) => item.kind === 'field' && item.name === name);
  return Boolean(node && !node.readonly);
}

function parseNumeric(text: unknown) {
  const raw = String(text ?? '').trim();
  if (!raw) return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : null;
}

function normalizeFieldValue(name: string, value: unknown) {
  const descriptor = contract.value?.fields?.[name];
  const ttype = fieldType(descriptor);
  if (ttype === 'boolean') {
    return Boolean(value);
  }
  if (ttype === 'integer') {
    const parsed = parseNumeric(value);
    return parsed === null ? false : Math.trunc(parsed);
  }
  if (ttype === 'float' || ttype === 'monetary') {
    const parsed = parseNumeric(value);
    return parsed === null ? false : parsed;
  }
  if (ttype === 'many2one') {
    if (Array.isArray(value) && typeof value[0] === 'number') return value[0];
    if (typeof value === 'number') return value;
    const parsed = parseNumeric(value);
    return parsed === null ? false : Math.trunc(parsed);
  }
  if (ttype === 'many2many') {
    return buildX2ManyCommands({
      kind: 'many2many',
      current: value,
      original: originalValues.value[name],
      mode: 'write',
    });
  }
  if (ttype === 'one2many') {
    return buildOne2manyCommandValue(name, 'write');
  }
  if (ttype === 'date') {
    const normalized = toDateInputValue(value);
    return normalized || false;
  }
  if (ttype === 'datetime') {
    return fromDatetimeInputValue(value);
  }
  if (ttype === 'char' || ttype === 'text' || ttype === 'html') {
    return String(value ?? '');
  }
  return value;
}

function inputFieldValue(name: string) {
  const raw = formData[name];
  if (raw === false || raw === null || raw === undefined) return '';
  return String(raw);
}

function setBooleanField(name: string, checked: boolean) {
  if (isInteractionLocked.value) return;
  formData[name] = checked;
  markFieldChanged(name);
}

function setMany2oneField(name: string, descriptor: FieldDescriptor | undefined, value: string) {
  if (isInteractionLocked.value) return;
  const normalized = String(value || '').trim();
  if (!normalized) {
    formData[name] = false;
    markFieldChanged(name);
    return;
  }
  if (normalized === MANY2ONE_CREATE_OPTION) {
    void openRelationCreateForm(name, descriptor);
    return;
  }
  const id = Number(normalized);
  if (!Number.isFinite(id) || id <= 0) {
    formData[name] = false;
    markFieldChanged(name);
    return;
  }
  formData[name] = Math.trunc(id);
  markFieldChanged(name);
}

function setSelectionField(name: string, value: string) {
  if (isInteractionLocked.value) return;
  formData[name] = value || false;
  markFieldChanged(name);
}

function setRelationMultiField(name: string, target: HTMLSelectElement) {
  if (isInteractionLocked.value) return;
  const ids = Array.from(target.selectedOptions)
    .map((item) => Number(item.value))
    .filter((id) => Number.isFinite(id) && id > 0)
    .map((id) => Math.trunc(id));
  formData[name] = ids;
  markFieldChanged(name);
}

function setTextField(name: string, value: string) {
  if (isInteractionLocked.value) return;
  formData[name] = value;
  markFieldChanged(name);
}

function shouldSkipOnchangeForField(name: string) {
  return String(model.value || '').trim() === 'res.users' && String(name || '').trim() === 'password';
}

function markFieldChanged(name: string) {
  const key = String(name || '').trim();
  if (!key || applyingOnchangePatch.value) return;
  changedFieldSet.add(key);
  if (shouldSkipOnchangeForField(key)) return;
  scheduleOnchange();
}

function scheduleOnchange() {
  if (onchangeTimer) clearTimeout(onchangeTimer);
  onchangeTimer = setTimeout(() => {
    void runOnchangeRoundtrip();
  }, 300);
}

function buildOnchangeValues() {
  const out: Record<string, unknown> = {};
  Object.keys(contract.value?.fields || {}).forEach((name) => {
    const descriptor = contract.value?.fields?.[name];
    const ttype = fieldType(descriptor);
    if (ttype === 'many2many') {
      out[name] = buildX2ManyCommands({
        kind: ttype,
        current: formData[name],
        original: originalValues.value[name],
        mode: 'onchange',
      });
      return;
    }
    if (ttype === 'one2many') {
      out[name] = buildOne2manyCommandValue(name, 'onchange');
      return;
    }
    out[name] = normalizeFieldValue(name, formData[name]);
  });
  if (recordId.value) out.id = recordId.value;
  return out;
}

async function runOnchangeRoundtrip() {
  if (isInteractionLocked.value) {
    scheduleOnchange();
    return;
  }
  if (!model.value) return;
  if (!changedFieldSet.size) return;
  const changed = Array.from(changedFieldSet);
  changedFieldSet.clear();
  try {
    const response = await triggerOnchange({
      model: model.value,
      res_id: recordId.value,
      values: buildOnchangeValues(),
      changed_fields: changed,
      context: pickContractNavQuery(route.query as Record<string, unknown>),
    });
    const patch = response?.patch;
    const modifiersPatch = response?.modifiers_patch;
    const linePatches = Array.isArray(response?.line_patches) ? response.line_patches : [];
    const warnings = Array.isArray(response?.warnings) ? response.warnings : [];
    onchangeWarnings.value = warnings;
    onchangeLinePatches.value = linePatches;
    if (modifiersPatch && typeof modifiersPatch === 'object') {
      onchangeModifiersPatch.value = {
        ...onchangeModifiersPatch.value,
        ...(modifiersPatch as Record<string, Record<string, unknown>>),
      };
      const patchedFields = Object.keys(modifiersPatch as Record<string, Record<string, unknown>>);
      await Promise.all(
        patchedFields.map(async (name) => {
          const descriptor = contract.value?.fields?.[name];
          const ttype = fieldType(descriptor);
          if (!['many2one', 'many2many', 'one2many'].includes(ttype)) return;
          await queryRelationOptions(name, relationKeyword(name));
        }),
      );
    }
    if (patch && typeof patch === 'object') {
      applyingOnchangePatch.value = true;
      Object.entries(patch).forEach(([name, value]) => {
        if (!(name in (contract.value?.fields || {}))) return;
        if (shouldSkipOnchangeForField(name)) return;
        const ttype = fieldType(contract.value?.fields?.[name]);
        if (ttype === 'many2many' || ttype === 'one2many') {
          formData[name] = Array.isArray(value) ? value : [];
          if (ttype === 'one2many') initOne2manyRows(name, formData[name]);
        } else if (ttype === 'many2one') {
          const ids = normalizeRelationIds(value);
          formData[name] = ids.length ? ids[0] : false;
        } else if (ttype === 'date') {
          formData[name] = toDateInputValue(value);
        } else if (ttype === 'datetime') {
          formData[name] = toDatetimeInputValue(value);
        } else {
          formData[name] = value;
        }
      });
      applyingOnchangePatch.value = false;
    }
    if (linePatches.length) {
      applyingOnchangePatch.value = true;
      applyOnchangeLinePatches(linePatches);
      applyingOnchangePatch.value = false;
    }
  } catch {
    // Onchange is best-effort; keep current values when roundtrip fails.
  }
}

function collectWritableValues() {
  return layoutNodes.value
    .filter((node) => node.kind === 'field' && !node.readonly)
    .reduce<Record<string, unknown>>((acc, node) => {
      const value = normalizeFieldValue(node.name, formData[node.name]);
      const ttype = fieldType(node.descriptor);
      if ((ttype === 'many2many' || ttype === 'one2many') && Array.isArray(value) && !value.length) {
        return acc;
      }
      acc[node.name] = value;
      return acc;
    }, {});
}

function fieldInputType(ttype?: string) {
  const type = String(ttype || '').toLowerCase();
  if (type === 'integer' || type === 'float' || type === 'monetary') return 'number';
  if (type === 'date') return 'date';
  if (type === 'datetime') return 'datetime-local';
  return 'text';
}

function normalizeRouteDefault(value: unknown) {
  const raw = Array.isArray(value) ? value[value.length - 1] : value;
  if (typeof raw !== 'string') return raw;
  const normalized = raw.trim();
  if (!normalized) return '';
  if (normalized === 'true') return true;
  if (normalized === 'false') return false;
  if (/^-?\d+(\.\d+)?$/.test(normalized)) return Number(normalized);
  return normalized;
}

function resolveNavigationUrl(url: string) {
  const raw = String(url || '').trim();
  if (!raw) return '';
  if (/^https?:\/\//i.test(raw)) return raw;
  if (raw.startsWith('/')) return `${window.location.origin}${raw}`;
  return raw;
}

const hudEntries = computed(() => [
  { label: 'model', value: model.value || '-' },
  { label: 'action_id', value: actionId.value || '-' },
  { label: 'record_id', value: recordIdDisplay.value },
  { label: 'contract_loaded', value: Boolean(contract.value) },
  { label: 'contract_ready', value: contractReadiness.value.usable },
  { label: 'contract_issues', value: contractReadiness.value.issues.length },
  { label: 'contract_view_type', value: contract.value?.head?.view_type || contract.value?.view_type || '-' },
  { label: 'render_profile', value: renderProfile.value },
  { label: 'fields_count', value: Object.keys(contract.value?.fields || {}).length },
  { label: 'layout_nodes', value: layoutNodes.value.length },
  { label: 'writable_fields', value: writableFieldCount.value },
  { label: 'changed_fields', value: changedFieldCount.value },
  { label: 'actions_count', value: contractActions.value.length },
  { label: 'rights', value: `${rights.value.read ? 'R' : '-'}${rights.value.write ? 'W' : '-'}${rights.value.create ? 'C' : '-'}${rights.value.unlink ? 'D' : '-'}` },
  { label: 'onchange_warnings', value: onchangeWarnings.value.length },
  { label: 'onchange_line_patches', value: onchangeLinePatches.value.length },
]);

type FormContractReadiness = {
  usable: boolean;
  issues: string[];
  fieldCount: number;
  layoutFieldCount: number;
  visibleCandidateCount: number;
};

function analyzeFormContractReadiness(
  data: unknown,
  options?: { requirePureFormViewType?: boolean },
): FormContractReadiness {
  const issues: string[] = [];
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return { usable: false, issues: ['contract payload is not an object'], fieldCount: 0, layoutFieldCount: 0, visibleCandidateCount: 0 };
  }
  const row = data as Record<string, unknown>;
  const requirePureFormViewType = options?.requirePureFormViewType !== false;
  const collectLayoutFieldNames = (layoutRaw: unknown): Set<string> => {
    const names = new Set<string>();
    const walk = (nodeRaw: unknown) => {
      if (Array.isArray(nodeRaw)) {
        nodeRaw.forEach((item) => walk(item));
        return;
      }
      if (!nodeRaw || typeof nodeRaw !== 'object') return;
      const node = nodeRaw as Record<string, unknown>;
      const kind = String(node.type || '').trim().toLowerCase();
      if (kind === 'field') {
        const fieldName = String(node.name || '').trim();
        if (fieldName) names.add(fieldName);
      }
      forEachLayoutChildren(node, (child, sourceKey) => walk(normalizeLayoutChildNode(child, sourceKey)));
    };
    walk(layoutRaw);
    return names;
  };

  const fields = row.fields;
  const fieldMap = fields && typeof fields === 'object' && !Array.isArray(fields)
    ? fields as Record<string, unknown>
    : {};
  const fieldNames = Object.keys(fieldMap);
  if (!fieldNames.length) {
    issues.push('contract.fields is empty');
  }

  const views = row.views;
  const formView = views && typeof views === 'object' && !Array.isArray(views)
    ? (views as Record<string, unknown>).form
    : undefined;
  if (!formView || typeof formView !== 'object' || Array.isArray(formView)) {
    issues.push('contract.views.form is missing');
  }
  const layout = formView && typeof formView === 'object' && !Array.isArray(formView)
    ? (formView as Record<string, unknown>).layout
    : [];
  const semanticPageRaw = row.semantic_page && typeof row.semantic_page === 'object' && !Array.isArray(row.semantic_page)
    ? row.semantic_page as Record<string, unknown>
    : {};
  const semanticFormRaw = semanticPageRaw.form_semantics && typeof semanticPageRaw.form_semantics === 'object' && !Array.isArray(semanticPageRaw.form_semantics)
    ? semanticPageRaw.form_semantics as Record<string, unknown>
    : {};
  const semanticLayout = Array.isArray(semanticFormRaw.layout) ? semanticFormRaw.layout : [];
  const effectiveLayout = Array.isArray(layout) && layout.length ? layout : semanticLayout;
  const layoutFieldNames = collectLayoutFieldNames(effectiveLayout);
  if (!layoutFieldNames.size) {
    issues.push('contract.views.form.layout/semantic_page.form_semantics.layout has no field nodes');
  }

  const head = row.head;
  const headViewType = head && typeof head === 'object' && !Array.isArray(head)
    ? String((head as Record<string, unknown>).view_type || '').trim().toLowerCase()
    : '';
  const viewType = String(row.view_type || '').trim().toLowerCase();
  const normalizeViewModes = (value: string) => value
    .split(',')
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
  const headViewModes = normalizeViewModes(headViewType);
  const rootViewModes = normalizeViewModes(viewType);
  if (requirePureFormViewType) {
    if (headViewModes.length && !headViewModes.includes('form')) {
      issues.push(`head.view_type is ${headViewType}, expected form-compatible`);
    }
    if (rootViewModes.length && !rootViewModes.includes('form')) {
      issues.push(`view_type is ${viewType}, expected form-compatible`);
    }
  }

  const visible = Array.isArray(row.visible_fields)
    ? row.visible_fields.map((x) => String(x || '').trim()).filter(Boolean)
    : [];
  const visibleNameSet = new Set(visible);
  const groupNames = new Set<string>();
  const groups = Array.isArray(row.field_groups) ? row.field_groups : [];
  groups.forEach((item) => {
    if (!item || typeof item !== 'object') return;
    const fieldsRaw = (item as Record<string, unknown>).fields;
    if (!Array.isArray(fieldsRaw)) return;
    fieldsRaw.forEach((name) => {
      const normalized = String(name || '').trim();
      if (normalized) groupNames.add(normalized);
    });
  });
  const visibleCandidates = fieldNames.filter((name) =>
    visibleNameSet.has(name) || groupNames.has(name) || layoutFieldNames.has(name),
  );
  if (fieldNames.length && !visibleCandidates.length) {
    issues.push('no visible field candidate from visible_fields/field_groups/layout');
  }

  return {
    usable: issues.length === 0,
    issues,
    fieldCount: fieldNames.length,
    layoutFieldCount: layoutFieldNames.size,
    visibleCandidateCount: visibleCandidates.length,
  };
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
  const renderMode = String(row.render_mode || '').trim().toLowerCase();
  const sourceMode = String(row.source_mode || '').trim().toLowerCase();
  const governedFromNative = row.governed_from_native;
  const surfaceMapping = row.surface_mapping;
  const metaSurface = String(meta?.contract_surface || '').trim().toLowerCase();

  if (!contractSurface) issues.push('missing contract_surface');
  if (!renderMode) issues.push('missing render_mode');
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

  if (contractSurface === 'native') {
    if (renderMode !== 'native') issues.push(`native surface requires render_mode=native, got ${renderMode || '-'}`);
    if (governedFromNative !== false) issues.push('native surface requires governed_from_native=false');
  } else if (contractSurface === 'user' || contractSurface === 'hud') {
    if (renderMode !== 'governed') issues.push(`governed surface requires render_mode=governed, got ${renderMode || '-'}`);
    if (governedFromNative !== true) issues.push('governed surface requires governed_from_native=true');
  }

  return { ok: issues.length === 0, issues };
}

async function loadContract() {
  loadStage.value = 'load_contract';
  const profile = recordId.value ? 'edit' : 'create';
  const currentModel = String(model.value || '').trim();
  let response: Awaited<ReturnType<typeof loadActionContractRaw>> | null = null;
  if (actionId.value) {
    try {
      response = await loadActionContractRaw(actionId.value, {
        recordId: recordId.value,
        renderProfile: profile,
        surface: requestedSurface.value,
        sourceMode: requestedSourceMode.value,
      });
      const actionReadiness = analyzeFormContractReadiness(response?.data, { requirePureFormViewType: true });
      if (!actionReadiness.usable) {
        response = null;
      }
    } catch {
      response = null;
    }
  }
  if (!response && currentModel) {
    response = await loadModelContractRaw(currentModel, {
      viewType: 'form',
      recordId: recordId.value,
      renderProfile: profile,
      surface: requestedSurface.value,
      sourceMode: requestedSourceMode.value,
    });
  }
  if (!response?.data || typeof response.data !== 'object') {
    throw new Error('empty contract');
  }
  const markerCheck = validateSurfaceMarkers(
    response.data,
    (response.meta as Record<string, unknown> | null) || null,
    requestedSurface.value,
  );
  if (!markerCheck.ok) {
    throw new Error(`contract surface markers invalid: ${markerCheck.issues.slice(0, 4).join(' | ')}`);
  }
  const readiness = analyzeFormContractReadiness(response.data, { requirePureFormViewType: false });
  if (!readiness.usable) {
    throw new Error(`contract not renderable: ${readiness.issues.slice(0, 4).join(' | ')}`);
  }
  contract.value = response.data as ActionContract;
  contractMeta.value = response.meta || null;
  const policy = contractAccessPolicy.value;
  if (policy.mode === 'block') {
    const message = policy.message || 'contract access policy blocked this page';
    throw new ContractAccessPolicyError(message, policy.reasonCode || 'CONTRACT_ACCESS_BLOCKED');
  }
  const hasCore = coreFieldNames.value.length > 0;
  advancedExpanded.value = renderProfile.value !== 'create' || !hasCore;
  if (isEnterpriseUserEnablementCreatePage.value) {
    advancedExpanded.value = true;
  }
}

async function loadRecord() {
  loadStage.value = 'load_record';
  const fieldNames = Object.keys(contract.value?.fields || {});
  Object.keys(formData).forEach((key) => {
    delete formData[key];
  });
  Object.keys(relationKeywords).forEach((key) => {
    delete relationKeywords[key];
  });
  Object.keys(one2manyRows).forEach((key) => {
    delete one2manyRows[key];
  });
  onchangeModifiersPatch.value = {};
  onchangeWarnings.value = [];
  onchangeLinePatches.value = [];
  changedFieldSet.clear();
  if (onchangeTimer) {
    clearTimeout(onchangeTimer);
    onchangeTimer = null;
  }
  if (!recordId.value) {
    const context = contract.value?.head?.context;
    const defaults: Record<string, unknown> = {};
    Object.entries(route.query as Record<string, unknown>).forEach(([key, value]) => {
      if (key.startsWith('default_')) {
        defaults[key.replace(/^default_/, '')] = normalizeRouteDefault(value);
      }
    });
    if (context && typeof context === 'object' && !Array.isArray(context)) {
      Object.entries(context).forEach(([key, value]) => {
        if (key.startsWith('default_') && !(key.replace(/^default_/, '') in defaults)) {
          defaults[key.replace(/^default_/, '')] = value;
        }
      });
    }
    const validator = contract.value?.validator as Record<string, unknown> | undefined;
    const defaultsSample = validator?.defaults_sample;
    if (defaultsSample && typeof defaultsSample === 'object' && !Array.isArray(defaultsSample)) {
      Object.entries(defaultsSample as Record<string, unknown>).forEach(([key, value]) => {
        if (!(key in defaults)) {
          defaults[key] = value === 'dynamic' ? '' : value;
        }
      });
    }
    fieldNames.forEach((name) => {
      const descriptor = contract.value?.fields?.[name];
      const ttype = fieldType(descriptor);
      const incoming = name in defaults ? defaults[name] : '';
      if (ttype === 'many2many' || ttype === 'one2many') {
        formData[name] = Array.isArray(incoming) ? incoming : [];
        if (ttype === 'one2many') initOne2manyRows(name, formData[name]);
      } else if (ttype === 'many2one') {
        const option = parseMany2oneDisplay(incoming);
        upsertRelationOption(name, option);
        const ids = normalizeRelationIds(incoming);
        formData[name] = ids.length ? ids[0] : false;
        const matched = ids.length
          ? (relationOptions.value[name] || []).find((item) => item.id === ids[0])
          : null;
        relationKeywords[name] = matched?.label || option?.label || '';
      } else if (ttype === 'date') {
        formData[name] = toDateInputValue(incoming);
      } else if (ttype === 'datetime') {
        formData[name] = toDatetimeInputValue(incoming);
      } else {
        formData[name] = incoming;
      }
    });
    if (
      isEnterpriseUserEnablementCreatePage.value
      && !normalizeRelationIds(formData.company_id).length
      && enterpriseCurrentCompanyId.value > 0
    ) {
      formData.company_id = enterpriseCurrentCompanyId.value;
    }
    if (isEnterpriseUserEnablementCreatePage.value && formData.active !== true) {
      formData.active = true;
    }
    originalValues.value = fieldNames.reduce<Record<string, unknown>>((acc, name) => {
      const value = formData[name];
      if (Array.isArray(value)) {
        acc[name] = [...value];
      } else if (value && typeof value === 'object') {
        acc[name] = JSON.parse(JSON.stringify(value));
      } else {
        acc[name] = value;
      }
      return acc;
    }, {});
    restoreIntakeAutosave();
    return;
  }
  const read = await readRecord({
    model: model.value,
    ids: [recordId.value],
    fields: fieldNames.length ? fieldNames : '*',
  });
  const row = read.records?.[0] || {};
  fieldNames.forEach((name) => {
    const descriptor = contract.value?.fields?.[name];
    const ttype = fieldType(descriptor);
    const incoming = (row as Record<string, unknown>)[name] ?? '';
    if (ttype === 'many2many' || ttype === 'one2many') {
      formData[name] = Array.isArray(incoming) ? incoming : [];
      if (ttype === 'one2many') initOne2manyRows(name, formData[name]);
    } else if (ttype === 'many2one') {
      const option = parseMany2oneDisplay(incoming);
      upsertRelationOption(name, option);
      const ids = normalizeRelationIds(incoming);
      formData[name] = ids.length ? ids[0] : false;
      const matched = ids.length
        ? (relationOptions.value[name] || []).find((item) => item.id === ids[0])
        : null;
      relationKeywords[name] = matched?.label || option?.label || '';
    } else if (ttype === 'date') {
      formData[name] = toDateInputValue(incoming);
    } else if (ttype === 'datetime') {
      formData[name] = toDatetimeInputValue(incoming);
    } else {
      formData[name] = incoming;
    }
  });
  originalValues.value = fieldNames.reduce<Record<string, unknown>>((acc, name) => {
    const value = formData[name];
    if (Array.isArray(value)) {
      acc[name] = [...value];
    } else if (value && typeof value === 'object') {
      acc[name] = JSON.parse(JSON.stringify(value));
    } else {
      acc[name] = value;
    }
    return acc;
  }, {});
}

async function reload() {
  status.value = 'loading';
  loadStage.value = 'reload_start';
  errorMessage.value = '';
  validationErrors.value = [];
  showOne2manyErrors.value = false;
  try {
    await loadContract();
    await loadRecord();
    await loadRelationOptions();
    loadStage.value = 'reload_done';
    status.value = 'ok';
  } catch (err) {
    loadStage.value = 'reload_error';
    if (err instanceof ContractAccessPolicyError) {
      await router.push({
        name: 'workbench',
        query: pickContractNavQuery(route.query as Record<string, unknown>, {
          reason: ErrorCodes.CAPABILITY_MISSING,
          action_id: actionId.value || undefined,
          menu_id: Number(route.query.menu_id || 0) || undefined,
          diag: showHud.value ? (err.reasonCode || 'CONTRACT_ACCESS_BLOCKED') : undefined,
        }),
      });
      return;
    }
    errorMessage.value = err instanceof Error ? err.message : '页面加载失败，请稍后重试';
    status.value = 'error';
  }
}

watchEffect(() => {
  if (typeof window === 'undefined') return;
  const collectRawContractLayoutFieldOrder = () => {
    const out: Array<{ name: string; label: string }> = [];
    const seen = new Set<string>();
    const walk = (nodeRaw: unknown) => {
      if (Array.isArray(nodeRaw)) {
        nodeRaw.forEach((item) => walk(item));
        return;
      }
      if (!nodeRaw || typeof nodeRaw !== 'object') return;
      const node = nodeRaw as Record<string, unknown>;
      const kind = String(node.type || '').trim().toLowerCase();
      if (kind === 'field') {
        const name = String(node.name || '').trim();
        if (name && !seen.has(name)) {
          seen.add(name);
          out.push({
            name,
            label: String(node.title || node.string || node.label || '').trim(),
          });
        }
      }
      forEachLayoutChildren(node, (child, sourceKey) => walk(normalizeLayoutChildNode(child, sourceKey)));
    };
    walk(contract.value?.views?.form?.layout || []);
    return out;
  };
  const permissionFieldGroups = contract.value?.permissions?.field_groups || {};
  (window as Window & { __scFormDebug?: Record<string, unknown> }).__scFormDebug = {
    status: status.value,
    loadStage: loadStage.value,
    model: model.value,
    actionId: actionId.value,
    recordId: recordId.value,
    preferNativeFormSurface: preferNativeFormSurface.value,
    nativeLikeFormSurface: nativeLikeFormSurface.value,
    deliveredViewType: String(contract.value?.view_type || '').trim(),
    headViewType: String(asRecord(contract.value?.head).view_type || '').trim(),
    contractActionLabels: contractActions.value.map((action) => ({
      key: action.key,
      label: action.label,
      level: action.level,
      kind: action.kind,
      buttonType: action.buttonType,
      order: action.order,
    })),
    headerActionLabels: headerActions.value.map((action) => action.label),
    contractActionStripLabels: contractActionStrip.value.map((action) => action.label),
    contractLoaded: Boolean(contract.value),
    contractHeadTitle: String(contract.value?.head?.title || '').trim(),
    fieldCount: Object.keys(contract.value?.fields || {}).length,
    fieldNames: Object.keys(contract.value?.fields || {}),
    visibleFields: contractVisibleFields.value,
    coreFieldNames: coreFieldNames.value,
    advancedFieldNames: advancedFieldNames.value,
    layoutNodeCount: layoutNodes.value.length,
    rawLayoutFieldOrder: collectRawContractLayoutFieldOrder(),
    layoutFieldLabels: layoutNodes.value
      .filter((node) => node.kind === 'field')
      .map((node) => ({ name: node.name, label: node.label })),
    permissionFieldGroups: Object.entries(permissionFieldGroups).reduce<Record<string, unknown>>((acc, [name, raw]) => {
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return acc;
      const row = raw as Record<string, unknown>;
      acc[name] = {
        groups_xmlids: Array.isArray(row.groups_xmlids) ? row.groups_xmlids : [],
      };
      return acc;
    }, {}),
    coreFieldCount: coreFieldNames.value.length,
    relationFieldCount: Object.entries(contract.value?.fields || {}).filter(([, descriptor]) => {
      const ttype = fieldType(descriptor as FieldDescriptor | undefined);
      return ttype === 'many2one' || ttype === 'many2many' || ttype === 'one2many';
    }).length,
    relationOptionFieldCount: Object.keys(relationOptions.value || {}).length,
    errorMessage: errorMessage.value,
  };
});

function openFormNativeFallback() {
  if (isInteractionLocked.value) return;
  if (!formNativeFallbackUrl.value) return;
  window.location.assign(formNativeFallbackUrl.value);
}

async function runAction(action: ContractAction) {
  if (isInteractionLocked.value) return;
  if (!action.enabled) return;
  const actionKey = String(action.key || '').trim().toLowerCase();
  if (actionKey === 'submit_intake' || actionKey === 'save_draft') {
    await saveRecord(action.refreshPolicy);
    return;
  }
  if (actionKey === 'cancel') {
    await router.push({
      name: 'workbench',
      query: pickContractNavQuery(route.query as Record<string, unknown>, {
        scene: undefined,
      }),
    });
    return;
  }
  if (action.kind === 'open') {
    if (action.actionId) {
      await router.push({
        name: 'action',
        params: { actionId: String(action.actionId) },
        query: pickContractNavQuery(route.query as Record<string, unknown>, {
          action_id: action.actionId,
          target: action.target || undefined,
          domain_raw: action.domainRaw || undefined,
        }),
      });
      return;
    }
    if (action.url) {
      const navUrl = resolveNavigationUrl(action.url);
      window.open(navUrl, action.target === 'self' ? '_self' : '_blank', 'noopener,noreferrer');
      return;
    }
    errorMessage.value = '契约打开动作缺少 action_id';
    status.value = 'error';
    return;
  }
  if (action.mutation) {
    busyKind.value = 'action';
    try {
      const result = await executeSceneMutation({
        mutation: action.mutation,
        actionKey: action.key,
        recordId: recordId.value,
        model: action.targetModel || model.value,
        context: action.context,
      });
      if (showHud.value) {
        // eslint-disable-next-line no-console
        console.info(`[scene-mutation] intent=${result.intent} trace=${result.traceId} action=${action.key}`);
      }
      await applyProjectionRefreshPolicy(action.refreshPolicy);
      return;
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : '场景变更执行失败，请稍后重试';
      status.value = 'error';
      return;
    } finally {
      busyKind.value = null;
    }
  }
  if ((action.kind === 'object' || action.kind === 'server') && action.methodName && recordId.value) {
    busyKind.value = 'action';
    try {
      const executeButtonType = action.buttonType === 'action' ? 'action' : 'object';
      const response = await executeButton({
        model: action.targetModel || model.value,
        res_id: recordId.value,
        button: { name: action.methodName, type: executeButtonType },
        context: action.context,
        meta: {
          menu_id: Number(route.query.menu_id || 0) || undefined,
          action_id: actionId.value || undefined,
        },
      });
      const result = response?.result;
      const refresh = result?.type;
      if (refresh === 'refresh' && !action.refreshPolicy) {
        await reload();
        return;
      }
      const nextActionId = toPositiveInt(result?.action_id);
      if (nextActionId) {
        await router.push({
          name: 'action',
          params: { actionId: String(nextActionId) },
          query: pickContractNavQuery(route.query as Record<string, unknown>, { action_id: nextActionId }),
        });
        if (action.refreshPolicy) {
          await applyProjectionRefreshPolicy(action.refreshPolicy);
        }
        return;
      }
      if (action.refreshPolicy) {
        await applyProjectionRefreshPolicy(action.refreshPolicy);
      }
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : '动作执行失败，请稍后重试';
      status.value = 'error';
    } finally {
      busyKind.value = null;
    }
  }
}

async function openEnterpriseNextAction() {
  if (isInteractionLocked.value) return;
  const target = enterpriseNextActionTarget.value;
  if (!target) return;
  await router.push({
    name: 'action',
    params: { actionId: String(target.actionId) },
    query: pickContractNavQuery(route.query as Record<string, unknown>, {
      action_id: target.actionId,
      menu_id: target.menuId || undefined,
    }),
  });
}

async function applyProjectionRefreshPolicy(policy?: ContractAction['refreshPolicy']) {
  if (!policy || !Array.isArray(policy.on_success) || !policy.on_success.length) {
    return;
  }
  await executeProjectionRefresh({
    policy,
    refreshScene: async () => {
      await reload();
    },
    refreshWorkbench: async () => {
      await session.loadAppInit();
    },
    refreshRoleSurface: async () => {
      await session.loadAppInit();
    },
    recordTrace: ({ intent, writeMode, latencyMs }) => {
      session.recordIntentTrace({ intent, writeMode, latencyMs });
    },
  });
}

async function openFilter(filterKey: string) {
  if (isInteractionLocked.value) return;
  if (!actionId.value) return;
  const selected = searchFilters.value.find((item) => item.key === filterKey);
  activeFilterKey.value = filterKey;
  await router.push({
    name: 'action',
    params: { actionId: String(actionId.value) },
    query: pickContractNavQuery(route.query as Record<string, unknown>, {
      action_id: actionId.value,
      preset_filter: filterKey,
      domain_raw: selected?.domainRaw || undefined,
      context_raw: selected?.contextRaw || undefined,
    }),
  });
}

async function cancelIntake() {
  if (isInteractionLocked.value) return;
  if (!isProjectCreatePage.value) return;
  const target = session.resolveLandingPath('/');
  await router.replace({ path: target, query: resolveWorkspaceContextQuery() });
}

async function saveRecord(refreshPolicy?: ContractAction['refreshPolicy']) {
  if (isInteractionLocked.value) return;
  if (!canSave.value || !model.value) return;
  submissionFeedback.value = null;
  validationErrors.value = [];
  const standardCreateMode = isProjectStandardIntakeMode.value;
  if (standardCreateMode) {
    const draftErrors: string[] = [];
    const projectName = String(formData.name || '').trim();
    const managerId = Number(formData.manager_id || 0);
    if (!projectName) draftErrors.push('请填写项目名称');
    if (!Number.isFinite(managerId) || managerId <= 0) draftErrors.push('请填写项目经理');
    if (draftErrors.length) {
      validationErrors.value = draftErrors;
      submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
      return;
    }
  }
  const one2manyIssues = one2manyValidation.value.issues;
  if (one2manyIssues.length) {
    showOne2manyErrors.value = true;
    validationErrors.value = one2manyIssues.slice(0, 5);
    submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
    return;
  }
  showOne2manyErrors.value = false;
  const editableMap = collectWritableValues();
  const labels = layoutNodes.value.reduce<Record<string, string>>((acc, node) => {
    if (node.kind === 'field') acc[node.name] = node.label || node.name;
    return acc;
  }, {});
  const scenePrecheckIssues = collectSceneValidationPrecheckErrors(labels);
  if (scenePrecheckIssues.length) {
    validationErrors.value = scenePrecheckIssues;
    submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
    return;
  }
  if (!standardCreateMode) {
    const issues = validateContractFormData({
      contract: contract.value,
      fieldLabels: labels,
      values: editableMap,
    });
    const policyIssues = collectPolicyValidationErrors(contract.value, policyContext.value);
    if (policyIssues.length) {
      validationErrors.value = Array.from(new Set(policyIssues)).slice(0, 5);
      submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
      return;
    }
    if (issues.length) {
      validationErrors.value = Array.from(new Set(issues.map((item) => item.message))).slice(0, 5);
      submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
      return;
    }
  }
  busyKind.value = 'save';
  try {
    const values = Object.entries(editableMap).reduce<Record<string, unknown>>((acc, [key, value]) => {
      if (!recordId.value) {
        acc[key] = value;
        return acc;
      }
      if (String(model.value || '').trim() === 'res.users' && key === 'password') {
        const passwordValue = String(formData.password || '').trim();
        if (passwordValue) acc[key] = passwordValue;
        return acc;
      }
      const ttype = fieldType(contract.value?.fields?.[key]);
      if (ttype === 'many2many' || ttype === 'one2many') {
        if (Array.isArray(value) && value.length) {
          acc[key] = value;
        }
        return acc;
      }
      if (comparableFieldValue(key, formData[key]) !== comparableFieldValue(key, originalValues.value[key])) {
        acc[key] = value;
      }
      return acc;
    }, {});
    if (recordId.value && !Object.keys(values).length) {
      submissionFeedback.value = { kind: 'warn', message: '没有检测到可保存的变更。' };
      busyKind.value = null;
      return;
    }
    if (recordId.value) {
      await writeRecord({ model: model.value, ids: [recordId.value], vals: values });
      if (String(model.value || '').trim() === 'res.users' && 'password' in formData) {
        formData.password = '';
        originalValues.value.password = '';
      }
      submissionFeedback.value = { kind: 'success', message: '保存成功，已同步最新表单内容。' };
      await applyProjectionRefreshPolicy(refreshPolicy || { on_success: ['scene_projection'] });
      return;
    }
    const created = await createRecord({ model: model.value, vals: values });
    if (created?.id) {
      submissionFeedback.value = { kind: 'success', message: '保存成功，已创建并进入详情。' };
      clearIntakeAutosave();
      if (model.value === 'project.project') {
        setPendingProjectContext({
          project_id: Number(created.id),
          project_name: String(values.name || formData.name || ''),
          stage: 'initiated',
          stage_label: '已立项',
          milestone: '',
          milestone_label: '',
          status: 'active',
        });
      }
      const nextSceneRoute = String(sceneReadyFormSurface.value.nextSceneRoute || '').trim();
      const nextSceneKey = String(sceneReadyFormSurface.value.nextSceneKey || '').trim();
      const resolvedNextRoute = nextSceneRoute || (nextSceneKey ? `/s/${nextSceneKey}` : '');
      if (isProjectQuickIntakeMode.value && model.value === 'project.project') {
        await applyProjectionRefreshPolicy(refreshPolicy || { on_success: ['scene_projection', 'workbench_projection'] });
        const routePath = resolvedNextRoute || '/s/project.management';
        await router.replace({
          path: routePath,
          query: {
            ...resolveWorkspaceContextQuery(),
          },
        });
        return;
      }
      if (isProjectStandardIntakeMode.value && resolvedNextRoute) {
        await applyProjectionRefreshPolicy(refreshPolicy || { on_success: ['scene_projection', 'workbench_projection'] });
        await router.replace({
          path: resolvedNextRoute,
          query: {
            ...resolveWorkspaceContextQuery(),
          },
        });
        return;
      }
      await router.replace({
        name: 'model-form',
        params: { model: model.value, id: String(created.id) },
        query: pickContractNavQuery(route.query as Record<string, unknown>),
      });
      return;
    }
  } catch (err) {
    const message = sanitizeUiErrorMessage(err instanceof Error ? err.message : err, '创建失败，请检查填写内容');
    validationErrors.value = [message];
    submissionFeedback.value = { kind: 'error', message: '创建失败，请检查填写内容' };
  } finally {
    busyKind.value = null;
  }
}

async function copyContractJson() {
  if (!contract.value) return;
  const payload = JSON.stringify(
    {
      action_id: actionId.value,
      model: model.value,
      contract: contract.value,
      meta: contractMeta.value || {},
    },
    null,
    2,
  );
  try {
    await navigator.clipboard.writeText(payload);
  } catch {
    // ignore clipboard failure in locked environments
  }
}

function exportContractJson() {
  if (!contract.value) return;
  const payload = JSON.stringify(
    {
      action_id: actionId.value,
      model: model.value,
      contract: contract.value,
      meta: contractMeta.value || {},
    },
    null,
    2,
  );
  const blob = new Blob([payload], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `contract_form_${model.value || 'unknown'}_${actionId.value || 'na'}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

watch(
  () => `${String(route.params.model || '')}|${String(route.params.id || '')}|${String(route.query.action_id || '')}`,
  () => {
    void reload();
  },
  { immediate: true },
);

watch(
  () => [
    intakeAutosaveKey.value,
    formData.name,
    formData.manager_id,
    formData.owner_id,
    formData.project_type_id,
    formData.project_category_id,
    formData.location,
    formData.start_date,
    formData.end_date,
  ],
  () => {
    persistIntakeAutosave();
  },
);
</script>

<style scoped>
.page {
  display: grid;
  gap: 6px;
  padding-bottom: 24px;
}

.page--flow {
  max-width: 1080px;
  margin: 0 auto;
  padding: 24px 32px;
}

.header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.header--flow {
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 12px;
  margin-bottom: 16px;
}

.header-main {
  display: grid;
  gap: 0;
}

.page-subtitle {
  margin: 2px 0 0;
  font-size: 12px;
  color: #94a3b8;
}

.page-status-line {
  margin: 2px 0 0;
  font-size: 12px;
  color: #64748b;
}

.header-main h1 {
  margin: 0;
  font-size: 36px;
  line-height: 1.12;
}

.form-compact-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 6px 4px 2px;
}

.form-compact-title {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
}

.form-compact-title strong {
  font-size: 24px;
  line-height: 1.2;
  color: #0f172a;
}

.form-compact-title span {
  font-size: 12px;
  color: #64748b;
}

.form-compact-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.meta {
  margin: 1px 0;
  color: #64748b;
  font-size: 12px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.actions:empty {
  display: none;
}

.header-status {
  display: grid;
  gap: 4px;
  margin-left: auto;
  text-align: right;
  min-width: 240px;
  padding-top: 3px;
}

.header-status-item {
  margin: 0;
  font-size: 12px;
  color: #737b87;
  line-height: 1.3;
}

.header-status-item--danger {
  color: #9a7a3e;
}

.action-hint {
  width: 100%;
  margin: 0;
  font-size: 12px;
  color: #64748b;
  text-align: right;
}

.card {
  border: 1px solid #eef0f2;
  border-radius: 8px;
  padding: 18px;
  background: #fff;
  max-width: 1360px;
  width: 100%;
  margin: 0 auto;
}

.card--compact {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px;
  background: #fff;
  box-shadow: none;
  max-width: none;
  margin: 0;
}

.card--flow {
  max-width: 1280px;
  width: 100%;
  border: 0;
  background: transparent;
  padding: 0;
  box-shadow: none;
}

.card--compact.card--flow {
  max-width: none;
  margin: 0;
}

.card--project-align {
  border: 0;
  border-radius: 0;
  padding: 2px 0 0;
  background: transparent;
  max-width: none;
}

.block {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px;
  margin-bottom: 10px;
  background: #f8fafc;
}

.card--compact .block {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 8px;
  margin-bottom: 8px;
  background: #fff;
}

.block.warn {
  border-color: #fdba74;
  background: #fff7ed;
}

.contract-missing-block {
  border-color: #fca5a5;
  background: #fff5f5;
}

.contract-missing-summary,
.contract-missing-defaults {
  margin: 4px 0 0;
  color: #7a271a;
  font-size: 12px;
}

.block h3 {
  margin: 0 0 8px;
  font-size: 12px;
}

.page-overview-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.page-overview-strip {
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.page-overview-pill {
  min-width: 132px;
  padding: 8px 10px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  display: grid;
  gap: 2px;
}

.page-overview-pill__label {
  font-size: 11px;
  color: #64748b;
}

.page-overview-pill__value {
  font-size: 13px;
  color: #0f172a;
  line-height: 1.3;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
}

.chip-btn {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
  cursor: pointer;
}

.chip-btn.active {
  border-color: #0f766e;
  box-shadow: inset 0 0 0 1px #0f766e;
}

.form-grid {
  display: grid;
  gap: 14px;
}

.form-grid--project-align {
  gap: 8px;
}

.structure-projection-block {
  border-color: #c7d2fe;
  background: #eef2ff;
}

.card--compact .form-grid {
  gap: 10px;
}

.card--flow .form-grid {
  max-width: 100%;
  margin: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.form-flow-guide {
  grid-column: 1 / -1;
  margin: 0;
  padding: 0;
  border: 0;
}

.form-flow-guide-main {
  margin: 0;
  font-size: 12px;
  color: #334155;
}

.validation-error {
  grid-column: 1 / -1;
  margin: 0;
  color: #b91c1c;
  font-size: 12px;
}

.validation-warn {
  grid-column: 1 / -1;
  margin: 0;
  color: #92400e;
  font-size: 12px;
}

.submission-feedback {
  grid-column: 1 / -1;
  margin: 0;
  font-size: 12px;
  border-radius: 8px;
  padding: 8px 10px;
}

.submission-feedback--success {
  color: #065f46;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
}

.submission-feedback--warn {
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fcd34d;
}

.submission-feedback--error {
  color: #991b1b;
  background: #fef2f2;
  border: 1px solid #fca5a5;
}

.layout-divider {
  grid-column: 1 / -1;
  font-size: 12px;
  color: #475569;
  border-bottom: 1px dashed #cbd5e1;
  padding-bottom: 4px;
}

.layout-divider.advanced-toggle {
  display: flex;
  justify-content: flex-start;
  border-bottom: 0;
  padding-bottom: 0;
  margin-top: 2px;
}

.zone-block {
  margin-top: 6px;
}

.zone-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.zone-chip {
  display: inline-flex;
  align-items: center;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  color: #0f172a;
  background: #f8fafc;
}

.zone-collaboration-line {
  margin: 0;
  font-size: 12px;
  color: #334155;
}

@media (max-width: 860px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}

.ghost,
.primary {
  border-radius: 6px;
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  font-weight: 500;
}

.primary {
  background: #111827;
  color: #fff;
  border-color: #111827;
}

.ghost {
  color: #6b7280;
}
</style>
