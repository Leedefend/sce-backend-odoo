<template>
  <section class="project-dashboard-page">
    <section v-if="pageStatus === 'loading'" class="status-wrap">
      <StatusPanel :title="loadingTitle" variant="info" />
    </section>
    <section v-else-if="pageStatus === 'error'" class="status-wrap">
      <StatusPanel :title="errorTitle" :message="errorMessage" variant="error" />
    </section>
    <section v-else class="dashboard-shell">
      <header class="hero-card">
        <div>
          <p class="eyebrow">{{ currentSceneLabel }}</p>
          <h1>{{ dashboardHeadline.title || '项目生命周期工作台' }}</h1>
          <p class="hero-subtitle">项目 ID {{ entry?.project_id || '-' }}</p>
          <p class="hero-state">{{ currentStateText }}</p>
          <p class="hero-next">{{ nextStepText }}</p>
        </div>
        <div class="hero-actions">
          <label v-if="isDashboardSurface && projectSwitcherOptions.length" class="project-switcher">
            <span>切换项目</span>
            <select :value="String(currentProjectId || 0)" @change="handleProjectSwitch">
              <option v-for="item in projectSwitcherOptions" :key="item.project_id" :value="String(item.project_id)">
                {{ item.project_name }} · {{ item.stage_label || '未设阶段' }}
              </option>
            </select>
          </label>
          <button type="button" class="ghost-button" @click="refreshAllBlocks">刷新区块</button>
        </div>
      </header>

      <section v-if="isDashboardSurface" class="state-explain-card">
        <article class="state-explain-item">
          <span class="state-explain-label">阶段说明</span>
          <strong>{{ stateExplain.stageExplain }}</strong>
        </article>
        <article class="state-explain-item">
          <span class="state-explain-label">里程碑说明</span>
          <strong>{{ stateExplain.milestoneExplain }}</strong>
        </article>
        <article class="state-explain-item">
          <span class="state-explain-label">当前状态说明</span>
          <strong>{{ stateExplain.statusExplain }}</strong>
        </article>
      </section>

      <section v-if="isDashboardSurface" class="flow-map-card">
        <div class="flow-map-header">
          <div>
            <span class="state-explain-label">流程地图</span>
            <strong>当前主线位置：{{ currentFlowLabel }}</strong>
          </div>
          <div class="completion-pill">
            <strong>{{ completion.percent }}%</strong>
            <span>下一目标：{{ completion.nextTarget }}</span>
          </div>
        </div>
        <div class="flow-map-track">
          <div v-for="item in flowMapItems" :key="item.key" class="flow-map-step" :data-status="item.status">
            <span class="flow-map-dot">{{ item.dot }}</span>
            <strong>{{ item.label }}</strong>
          </div>
        </div>
      </section>

      <section v-if="transitionFeedback" class="feedback-banner" :data-variant="transitionFeedback.variant">
        <strong>{{ transitionFeedback.title }}</strong>
        <p>{{ transitionFeedback.message }}</p>
      </section>

      <section class="summary-card">
        <div v-if="isDashboardSurface" class="summary-item summary-item-highlight">
          <span class="summary-label">当前项目概览</span>
          <strong class="summary-value">{{ dashboardHeadline.title }}</strong>
          <p class="summary-copy">{{ dashboardHeadline.subtitle }}</p>
        </div>
        <div v-for="item in summaryRows" :key="item.key" class="summary-item">
          <span class="summary-label">{{ item.label }}</span>
          <strong class="summary-value">{{ item.value }}</strong>
          <p v-if="item.copy" class="summary-copy">{{ item.copy }}</p>
        </div>
      </section>

      <section class="blocks-grid">
        <article v-for="descriptor in blockDescriptors" :key="descriptor.key" class="block-card">
          <header class="block-header">
            <div>
              <h2>{{ descriptor.title }}</h2>
              <p>{{ blockCaption(descriptor.key) }}</p>
            </div>
            <button type="button" class="ghost-button" @click="refreshBlock(descriptor.key)">刷新</button>
          </header>

          <div v-if="blockState(descriptor.key).loading" class="block-status">正在加载...</div>
          <div v-else-if="blockState(descriptor.key).error" class="block-status block-status-error">
            {{ blockState(descriptor.key).error }}
          </div>
          <div v-else-if="blockData(descriptor.key)?.state === 'forbidden'" class="block-status block-status-warning">
            当前账号无权限查看该区块。
          </div>
          <div v-else-if="blockData(descriptor.key)?.state === 'empty'" class="block-status">
            {{ blockEmptyText(descriptor.key) }}
          </div>
          <template v-else>
            <section v-if="descriptor.key === 'progress'" class="metric-list">
              <div v-for="item in progressRows" :key="item.key" class="metric-row">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </section>

            <section v-else-if="descriptor.key === 'risks'" class="risk-list">
              <div class="risk-summary">
                <span>风险评分 {{ riskSummary.score }}</span>
                <span>等级 {{ riskSummary.level }}</span>
                <span>未闭环 {{ riskSummary.openCount }}</span>
              </div>
              <div v-for="item in riskAlerts" :key="item.code" class="risk-alert">
                <div>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.description }}</p>
                  <p class="risk-impact">影响：{{ item.impact }}</p>
                  <p v-if="item.affectsAction" class="risk-action-copy">关联动作：{{ item.affectsAction }}</p>
                  <p class="risk-action-copy">建议动作：{{ item.recommendedAction }}</p>
                </div>
                <span class="action-state" :data-tone="item.levelTone">{{ item.levelLabel }}</span>
              </div>
            </section>

            <section v-else-if="descriptor.key === 'plan_summary_detail'" class="metric-list">
              <div v-for="item in planSummaryRows" :key="item.key" class="metric-row">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </section>

            <section v-else-if="descriptor.key === 'plan_tasks' || descriptor.key === 'execution_tasks'" class="task-list">
              <div v-for="item in taskRows(descriptor.key)" :key="item.key" class="task-row">
                <div>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.subtitle }}</p>
                </div>
                <span class="action-state" :data-tone="item.stateTone">{{ item.stateLabel }}</span>
              </div>
            </section>

            <section v-else-if="descriptor.key === 'pilot_precheck'" class="risk-list">
              <div class="risk-summary">
                <span>检查结果 {{ pilotPrecheckSummary.stateLabel }}</span>
                <span>通过 {{ pilotPrecheckSummary.passedCount }}</span>
                <span>阻断 {{ pilotPrecheckSummary.failedCount }}</span>
              </div>
              <div v-for="item in pilotPrecheckRows" :key="item.key" class="risk-alert">
                <strong>{{ item.title }}</strong>
                <p>{{ item.description }}</p>
              </div>
            </section>

            <section v-else-if="descriptor.key === 'cost_entry'" class="cost-form-card">
              <label class="cost-form-field">
                <span>发生日期</span>
                <input v-model="costEntryForm.date" type="date" class="cost-input" />
              </label>
              <label class="cost-form-field">
                <span>金额</span>
                <input v-model="costEntryForm.amount" type="number" min="0" step="0.01" class="cost-input" />
              </label>
              <label class="cost-form-field">
                <span>说明</span>
                <input v-model="costEntryForm.description" type="text" class="cost-input" placeholder="例如：材料进场" />
              </label>
              <label class="cost-form-field">
                <span>成本类别</span>
                <select v-model="costEntryForm.cost_code_id" class="cost-input">
                  <option :value="0">未指定</option>
                  <option v-for="item in costCategoryOptions" :key="item.value" :value="item.value">
                    {{ item.label }}
                  </option>
                </select>
              </label>
              <div class="cost-form-actions">
                <button type="button" class="primary-button" :disabled="costEntrySubmitting" @click="submitCostEntry">
                  {{ costEntrySubmitting ? '录入中...' : costEntrySubmitLabel }}
                </button>
                <span class="cost-form-hint">{{ costEntryHint }}</span>
              </div>
            </section>

            <section v-else-if="descriptor.key === 'cost_list'" class="task-list">
              <div v-for="item in costListRows" :key="item.key" class="task-row">
                <div>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.subtitle }}</p>
                </div>
                <span class="action-state" :data-tone="item.stateTone">{{ item.stateLabel }}</span>
              </div>
            </section>

            <section v-else-if="descriptor.key === 'cost_summary'" class="metric-list">
              <div v-for="item in costSummaryRows" :key="item.key" class="metric-row">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </section>

            <section v-else-if="descriptor.key === 'payment_entry'" class="payment-form-card">
              <label class="cost-form-field">
                <span>付款日期</span>
                <input v-model="paymentEntryForm.date" type="date" class="cost-input" />
              </label>
              <label class="cost-form-field">
                <span>金额</span>
                <input v-model="paymentEntryForm.amount" type="number" min="0" step="0.01" class="cost-input" />
              </label>
              <label class="cost-form-field">
                <span>说明</span>
                <input v-model="paymentEntryForm.description" type="text" class="cost-input" placeholder="例如：材料款支付" />
              </label>
              <div class="cost-form-actions">
                <button type="button" class="primary-button" :disabled="paymentEntrySubmitting" @click="submitPaymentEntry">
                  {{ paymentEntrySubmitting ? '录入中...' : paymentEntrySubmitLabel }}
                </button>
                <span class="cost-form-hint">{{ paymentEntryHint }}</span>
              </div>
            </section>

            <section v-else-if="descriptor.key === 'payment_list'" class="task-list">
              <div v-for="item in paymentListRows" :key="item.key" class="task-row">
                <div>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.subtitle }}</p>
                </div>
                <span class="action-state" :data-tone="item.stateTone">{{ item.stateLabel }}</span>
              </div>
            </section>

            <section v-else-if="descriptor.key === 'payment_summary'" class="metric-list">
              <div v-for="item in paymentSummaryRows" :key="item.key" class="metric-row">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </section>

            <section v-else-if="descriptor.key === 'settlement_summary'" class="metric-list">
              <div v-for="item in settlementSummaryRows" :key="item.key" class="metric-row">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </section>

            <section v-else-if="descriptor.key === 'next_actions'" class="action-list">
              <div v-if="primaryAction" class="action-card action-card-primary">
                <div>
                  <div class="action-title-row">
                    <strong>{{ primaryAction.label }}</strong>
                    <span class="recommended-badge">主推荐</span>
                  </div>
                  <p>{{ primaryAction.hint }}</p>
                  <p v-if="primaryAction.reason" class="action-reason">{{ primaryAction.reason }}</p>
                </div>
                <div class="action-side">
                  <span class="action-state" :data-tone="primaryAction.stateTone">{{ primaryAction.stateLabel }}</span>
                  <button
                    type="button"
                    class="primary-button"
                    :disabled="primaryAction.disabled"
                    @click="runAction(primaryAction)"
                  >
                    {{ primaryAction.buttonLabel }}
                  </button>
                </div>
              </div>
              <div v-for="item in secondaryActions" :key="item.key" class="action-card">
                <div>
                  <div class="action-title-row">
                    <strong>{{ item.label }}</strong>
                    <span v-if="item.recommended" class="recommended-badge">推荐</span>
                  </div>
                  <p>{{ item.hint }}</p>
                  <p v-if="item.reason" class="action-reason">{{ item.reason }}</p>
                </div>
                <div class="action-side">
                  <span class="action-state" :data-tone="item.stateTone">{{ item.stateLabel }}</span>
                  <button
                    type="button"
                    class="primary-button"
                    :disabled="item.disabled"
                    @click="runAction(item)"
                  >
                    {{ item.buttonLabel }}
                  </button>
                </div>
              </div>
            </section>

            <section v-else class="block-status">暂未支持的区块。</section>
          </template>
        </article>
      </section>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { intentRequest } from '../api/intents';
import {
  consumePendingProjectContext,
  PROJECT_DASHBOARD_ENTRY_INTENT,
  PROJECT_EXECUTION_ENTRY_INTENT,
} from '../app/projectCreationBaseline';
import { useSessionStore } from '../stores/session';

type RuntimeHint = {
  intent?: string;
  params?: Record<string, unknown>;
  reason_code?: string;
  key?: string;
};

type GenericEntry = {
  project_id?: number;
  scene_key?: string;
  scene_label?: string;
  state_fallback_text?: string;
  title?: string;
  project_context?: Record<string, unknown>;
  flow_map?: Record<string, unknown>;
  completion?: Record<string, unknown>;
  metrics_explain?: Array<Record<string, unknown>>;
  state_explain?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  blocks?: Array<{ key?: string; title?: string; state?: string; caption?: string; empty_hint?: string }>;
  suggested_action?: RuntimeHint;
  runtime_fetch_hints?: {
    blocks?: Record<string, RuntimeHint>;
  };
};

type RuntimeBlockEnvelope = {
  block_key?: string;
  block_type?: string;
  title?: string;
  state?: string;
  data?: Record<string, unknown>;
  error?: { code?: string; message?: string };
};

type RuntimeBlockResponse = {
  project_id?: number;
  block_key?: string;
  block?: RuntimeBlockEnvelope;
  degraded?: boolean;
};

type BlockRuntimeState = {
  loading: boolean;
  error: string;
  payload: RuntimeBlockEnvelope | null;
};

type ActionFeedback = {
  variant: 'success' | 'warning';
  title: string;
  message: string;
};

type CostCategoryOption = {
  value: number;
  label: string;
};

type ActionCard = {
  key: string;
  label: string;
  hint: string;
  reason: string;
  advancesToStage: string;
  intent: string;
  params: Record<string, unknown>;
  state: string;
  stateLabel: string;
  stateTone: string;
  buttonLabel: string;
  disabled: boolean;
  recommended: boolean;
};

type SummaryItem = {
  key: string;
  label: string;
  value: string;
  copy?: string;
};

type ProjectSwitchOption = {
  project_id: number;
  project_name: string;
  execution_stage_label?: string;
  stage_label: string;
  milestone_label: string;
  project_condition?: string;
  status: string;
  active?: boolean;
  project_context?: Record<string, unknown>;
};

type DashboardActionRow = Record<string, unknown> & {
  state_label?: unknown;
  state_tone?: unknown;
  button_label?: unknown;
  hint?: unknown;
  message?: unknown;
  title?: unknown;
  subtitle?: unknown;
  empty_hint?: unknown;
};

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const pageStatus = ref<'loading' | 'error' | 'ready'>('loading');
const errorTitle = ref('产品生命周期工作台加载失败');
const errorMessage = ref('');
const loadingTitle = ref('正在加载场景...');
const currentSceneKey = ref('project.dashboard');
const entry = ref<GenericEntry | null>(null);
const runtimeBlocks = ref<Record<string, BlockRuntimeState>>({});
const transitionFeedback = ref<ActionFeedback | null>(null);
const costEntryForm = ref({
  date: '',
  amount: '',
  description: '',
  cost_code_id: 0,
});
const costEntrySubmitting = ref(false);
const paymentEntryForm = ref({
  date: '',
  amount: '',
  description: '',
});
const paymentEntrySubmitting = ref(false);
const projectSwitcherOptions = ref<ProjectSwitchOption[]>([]);

const SCENE_ENTRY_INTENTS: Record<string, string> = {
  'project.dashboard': PROJECT_DASHBOARD_ENTRY_INTENT,
  'project.execution': PROJECT_EXECUTION_ENTRY_INTENT,
  'cost.tracking': 'cost.tracking.enter',
  payment: 'payment.enter',
  settlement: 'settlement.enter',
};

function asText(value: unknown) {
  return String(value || '').trim();
}

function asNumber(value: unknown) {
  const num = Number(value || 0);
  return Number.isFinite(num) ? num : 0;
}

const currentProjectContext = computed<Record<string, unknown>>(() => {
  const raw = entry.value?.project_context;
  return raw && typeof raw === 'object' ? raw as Record<string, unknown> : {};
});

const flowMap = computed<Record<string, unknown>>(() => {
  const raw = entry.value?.flow_map;
  return raw && typeof raw === 'object' ? raw as Record<string, unknown> : {};
});

const flowMapItems = computed(() => {
  const rows = Array.isArray(flowMap.value.items) ? flowMap.value.items : [];
  return rows.map((item) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    const status = asText(row.status || 'todo') || 'todo';
    return {
      key: asText(row.key || ''),
      label: asText(row.label || row.key || ''),
      status,
      dot: status === 'done' ? '✔' : status === 'current' ? '●' : '○',
    };
  });
});

const currentFlowLabel = computed(() => {
  return flowMapItems.value.find((item) => item.status === 'current')?.label || '未识别';
});

const completion = computed(() => {
  const raw = entry.value?.completion;
  const data = raw && typeof raw === 'object' ? raw as Record<string, unknown> : {};
  return {
    percent: asNumber(data.percent || 0),
    nextTarget: asText(data.next_target || '') || '继续推进主线',
  };
});

const metricsExplainMap = computed<Record<string, { status: string; explain: string }>>(() => {
  const raw = Array.isArray(entry.value?.metrics_explain) ? entry.value?.metrics_explain : [];
  return raw.reduce<Record<string, { status: string; explain: string }>>((acc, item) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    const key = asText(row.key || '');
    if (!key) return acc;
    acc[key] = {
      status: asText(row.status || 'normal') || 'normal',
      explain: asText(row.explain || '') || '',
    };
    return acc;
  }, {});
});

const currentProjectId = computed(() => asNumber(currentProjectContext.value.project_id || entry.value?.project_id || 0));
const isDashboardSurface = computed(() => {
  return route.path === '/s/project.management'
    || currentSceneKey.value === 'project.dashboard'
    || currentSceneKey.value === 'project.management';
});

const currentSceneLabel = computed(() => {
  return asText(entry.value?.scene_label || '') || '项目场景';
});

const blockDescriptors = computed(() => entry.value?.blocks || []);
const backendSummaryRows = computed<SummaryItem[]>(() => {
  const raw = Array.isArray(entry.value?.summary_rows) ? entry.value?.summary_rows : [];
  return raw
    .map((item) => {
      const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
      const key = asText(row.key || '');
      if (!key) return null;
      return {
        key,
        label: asText(row.label || key) || key,
        value: asText(row.value || '--') || '--',
        copy: asText(row.copy || '') || undefined,
      } satisfies SummaryItem;
    })
    .filter((item): item is SummaryItem => Boolean(item));
});

const summaryRows = computed<SummaryItem[]>(() => {
  if (backendSummaryRows.value.length) return backendSummaryRows.value;
  return [];
});

const dashboardHeadline = computed(() => {
  const projectName = asText(currentProjectContext.value.project_name || entry.value?.title || '--') || '--';
  const stageLabel = asText(currentProjectContext.value.execution_stage_label || '--') || '--';
  const milestoneLabel = asText(currentProjectContext.value.milestone_label || '--') || '--';
  return {
    title: projectName,
    subtitle: [stageLabel !== '--' ? `stage=${stageLabel}` : '', milestoneLabel !== '--' ? `milestone=${milestoneLabel}` : ''].filter(Boolean).join(' · ')
      || '',
  };
});

const stateExplain = computed(() => {
  const raw = entry.value?.state_explain;
  const data = raw && typeof raw === 'object' ? raw as Record<string, unknown> : {};
  const statusExplain = asText(data.status_explain || '') || asText(data.project_condition_explain || '') || '';
  return {
    stageExplain: asText(data.execution_stage_explain || '') || '--',
    milestoneExplain: asText(data.milestone_explain || '') || '--',
    projectConditionExplain: asText(data.project_condition_explain || '') || '--',
    statusExplain: statusExplain || '--',
  };
});

function blockState(blockKey: string): BlockRuntimeState {
  return runtimeBlocks.value[blockKey] || { loading: false, error: '', payload: null };
}

function blockData(blockKey: string) {
  return blockState(blockKey).payload;
}

function blockCaption(blockKey: string) {
  const descriptor = blockDescriptors.value.find((row) => asText(row.key || '') === blockKey);
  const contractCaption = asText(descriptor?.caption || '');
  if (contractCaption) return contractCaption;
  return '--';
}

const progressRows = computed(() => {
  const payload = blockData('progress');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  return [
    { key: 'completion_percent', label: '总体完成率', value: `${asNumber(data.completion_percent)}%` },
    { key: 'task_open', label: '未完成任务', value: `${asNumber(data.task_open)} 项` },
    { key: 'task_blocked', label: '阻塞任务', value: `${asNumber(data.task_blocked)} 项` },
    { key: 'task_overdue', label: '延期任务', value: `${asNumber(data.task_overdue)} 项` },
    { key: 'milestone_progress', label: '里程碑完成率', value: `${asNumber(data.milestone_progress)}%` },
    { key: 'critical_path_health', label: '关键路径', value: asText(data.critical_path_health || '--') || '--' },
  ];
});

const planSummaryRows = computed(() => {
  const payload = blockData('plan_summary_detail');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  return [
    { key: 'task_total', label: '计划任务总数', value: `${asNumber(data.task_total)} 项` },
    { key: 'task_open', label: '待完成任务', value: `${asNumber(data.task_open)} 项` },
    { key: 'task_overdue', label: '延期任务', value: `${asNumber(data.task_overdue)} 项` },
    { key: 'milestone_total', label: '里程碑总数', value: `${asNumber(data.milestone_total)} 项` },
    { key: 'milestone_done', label: '已完成里程碑', value: `${asNumber(data.milestone_done)} 项` },
    { key: 'planning_health', label: '计划状态', value: asText(data.planning_health || '--') || '--' },
  ];
});

const riskSummary = computed(() => {
  const payload = blockData('risks');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  return {
    score: asNumber(summary.risk_score),
    level: asText(summary.risk_level || '--') || '--',
    openCount: asNumber(summary.risk_open),
  };
});

const riskAlerts = computed(() => {
  const payload = blockData('risks');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const alerts = Array.isArray(data.alerts) ? data.alerts : [];
  return alerts.map((item, index) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    const hint = asText(row.hint || '');
    const level = asText(row.level || 'info');
    return {
      code: asText(row.code || `risk_${index + 1}`),
      title: asText(row.title || row.code || '风险提醒'),
      description: hint || `当前值 ${asNumber(row.value)}`,
      impact: asText(row.impact || '') || '当前问题会影响主线推进，请优先关注。',
      affectsAction: asText(row.action_key || '') || '',
      recommendedAction: asText(row.recommended_action || '') || '按驾驶舱推荐动作继续推进。',
      levelLabel: level === 'danger' ? '阻断' : level === 'warning' ? '预警' : '提示',
      levelTone: level === 'danger' ? 'warning' : level === 'warning' ? 'info' : 'success',
      sortWeight: level === 'danger' ? 0 : level === 'warning' ? 1 : 2,
    };
  }).sort((left, right) => left.sortWeight - right.sortWeight);
});

function taskRows(blockKey: string) {
  const payload = blockData(blockKey);
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const items = Array.isArray(data.items) ? data.items : [];
  return items.map((item, index) => {
    const row = item && typeof item === 'object' ? item as DashboardActionRow : {};
    const state = asText(row.state || 'open') || 'open';
    const stateLabel = asText(row.state_label || '');
    const stateTone = asText(row.state_tone || '');
    return {
      key: asText(row.task_id || row.id || row.key || `${blockKey}_${index + 1}`),
      title: asText(row.title || row.name || '未命名记录'),
      subtitle: asText(row.subtitle || '') || [asText(row.stage_name || ''), asText(row.deadline || '')].filter(Boolean).join(' · ') || '暂无补充信息',
      stateLabel: stateLabel || state || '--',
      stateTone: stateTone || 'info',
    };
  });
}

function blockEmptyText(blockKey: string) {
  const descriptor = blockDescriptors.value.find((row) => asText(row.key || '') === blockKey);
  const descriptorHint = asText(descriptor?.empty_hint || '');
  if (descriptorHint) return descriptorHint;
  const payload = blockData(blockKey);
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  const hint = asText(summary.empty_hint || '');
  if (hint) return hint;
  return '--';
}

function actionStateLabel(state: string) {
  return asText(state || '') || '--';
}

function actionButtonLabel(row: Record<string, unknown>, state: string) {
  const explicit = asText(row.button_label || '');
  if (explicit) return explicit;
  const actionKind = asText(row.action_kind || '');
  if (actionKind === 'transition') return '推进';
  if (actionKind === 'guidance') return '进入';
  return state === 'blocked' ? '受阻' : '执行';
}

function actionHint(row: Record<string, unknown>) {
  const rawHint = asText(row.hint || row.message || '');
  return rawHint || '查看该动作的当前执行提示';
}

const pilotPrecheckSummary = computed(() => {
  const payload = blockData('pilot_precheck');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  const overall = asText(summary.overall_state || '');
  return {
    stateLabel: overall === 'ready' ? '通过' : '受阻',
    passedCount: asNumber(summary.passed_count),
    failedCount: asNumber(summary.failed_count),
  };
});

const pilotPrecheckRows = computed(() => {
  const payload = blockData('pilot_precheck');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const checks = Array.isArray(data.checks) ? data.checks : [];
  return checks.map((item, index) => {
    const row = item && typeof item === 'object' ? item as DashboardActionRow : {};
    const status = asText(row.status || 'fail');
    return {
      key: asText(row.key || `pilot_check_${index + 1}`),
      title: `${asText(row.label || row.key || '试点检查')} · ${status === 'pass' ? '通过' : '受阻'}`,
      description: asText(row.message || row.hint || row.reason_code || '') || '检查结果待确认',
    };
  });
});

const costEntryPayload = computed(() => {
  const payload = blockData('cost_entry');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  return (data.form && typeof data.form === 'object') ? data.form as Record<string, unknown> : {};
});

const costCategoryOptions = computed<CostCategoryOption[]>(() => {
  const options = costEntryPayload.value.options;
  const costCodeOptions = options && typeof options === 'object' ? (options as Record<string, unknown>).cost_code_id : [];
  const rows = Array.isArray(costCodeOptions) ? costCodeOptions : [];
  return rows.map((item) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    return {
      value: asNumber(row.value),
      label: asText(row.label || '未命名类别'),
    };
  });
});

const costEntrySubmitLabel = computed(() => {
  return asText(costEntryPayload.value.submit_label || '') || '记录成本';
});

const costEntryHint = computed(() => {
  const payload = blockData('cost_entry');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  return asText(summary.state_fallback_text || '') || '--';
});

const costListRows = computed(() => {
  const payload = blockData('cost_list');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const records = Array.isArray(data.records) ? data.records : [];
  return records.map((item, index) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    const amount = asNumber(row.amount);
    const currency = asText(row.currency_name || '');
    const category = asText(row.category_name || row.category_type || '');
    return {
      key: asText(row.move_id || row.id || `cost_${index + 1}`),
      title: asText(row.description || row.name || '成本记录'),
      subtitle: [asText(row.date || ''), category, asText(row.project_name || '')].filter(Boolean).join(' · ') || '暂无补充信息',
      stateLabel: currency ? `${amount} ${currency}` : `${amount}`,
      stateTone: asText(row.state || '') === 'posted' ? 'success' : 'warning',
    };
  });
});

const costSummaryRows = computed(() => {
  const payload = blockData('cost_summary');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  const currency = asText(summary.currency_name || '');
  const total = asNumber(summary.total_cost_amount);
  return [
    { key: 'total_cost_amount', label: '项目成本合计', value: currency ? `${total} ${currency}` : `${total}` },
    { key: 'record_count', label: '记录数量', value: `${asNumber(summary.record_count)} 条` },
    { key: 'draft_record_count', label: '草稿记录', value: `${asNumber(summary.draft_record_count)} 条` },
    { key: 'posted_record_count', label: '已过账记录', value: `${asNumber(summary.posted_record_count)} 条` },
  ];
});

const paymentEntryPayload = computed(() => {
  const payload = blockData('payment_entry');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  return (data.form && typeof data.form === 'object') ? data.form as Record<string, unknown> : {};
});

const paymentEntrySubmitLabel = computed(() => {
  return asText(paymentEntryPayload.value.submit_label || '') || '记录付款';
});

const paymentEntryHint = computed(() => {
  const payload = blockData('payment_entry');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  return asText(summary.state_fallback_text || '') || '--';
});

const paymentListRows = computed(() => {
  const payload = blockData('payment_list');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const records = Array.isArray(data.records) ? data.records : [];
  return records.map((item, index) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    const amount = asNumber(row.amount);
    const currency = asText(row.currency_name || '');
    return {
      key: asText(row.payment_request_id || row.id || `payment_${index + 1}`),
      title: asText(row.description || row.name || '付款记录'),
      subtitle: [asText(row.date || ''), asText(row.partner_name || ''), asText(row.project_name || '')].filter(Boolean).join(' · ') || '暂无补充信息',
      stateLabel: currency ? `${amount} ${currency}` : `${amount}`,
      stateTone: asText(row.state || '') === 'draft' ? 'warning' : 'success',
    };
  });
});

const paymentSummaryRows = computed(() => {
  const payload = blockData('payment_summary');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  const currency = asText(summary.currency_name || '');
  const total = asNumber(summary.total_payment_amount);
  return [
    { key: 'total_payment_amount', label: '项目付款合计', value: currency ? `${total} ${currency}` : `${total}` },
    { key: 'record_count', label: '记录数量', value: `${asNumber(summary.record_count)} 条` },
    { key: 'draft_record_count', label: '草稿记录', value: `${asNumber(summary.draft_record_count)} 条` },
    { key: 'approved_record_count', label: '已完成/批准', value: `${asNumber(summary.approved_record_count)} 条` },
    { key: 'executed_record_count', label: '已支付台账', value: `${asNumber(summary.executed_record_count)} 条` },
    { key: 'executed_payment_amount', label: '已支付证据金额', value: currency ? `${asNumber(summary.executed_payment_amount)} ${currency}` : `${asNumber(summary.executed_payment_amount)}` },
  ];
});

const settlementSummaryRows = computed(() => {
  const payload = blockData('settlement_summary');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  const currency = asText(summary.currency_name || '');
  const totalCost = asNumber(summary.total_cost);
  const totalPayment = asNumber(summary.total_payment);
  const delta = asNumber(summary.delta);
  const costCount = asNumber(summary.cost_record_count);
  const paymentCount = asNumber(summary.payment_record_count);
  const executedPayment = asNumber(summary.executed_payment_amount);
  const executedPaymentCount = asNumber(summary.executed_payment_record_count);
  const display = (value: number) => currency ? `${value} ${currency}` : `${value}`;
  return [
    { key: 'total_cost', label: '总成本', value: display(totalCost) },
    { key: 'total_payment', label: '总付款', value: display(totalPayment) },
    { key: 'executed_payment_amount', label: '已支付证据', value: display(executedPayment) },
    { key: 'delta', label: '差额', value: display(delta) },
    { key: 'cost_record_count', label: '成本记录', value: `${costCount} 条` },
    { key: 'payment_record_count', label: '付款记录', value: `${paymentCount} 条` },
    { key: 'executed_payment_record_count', label: '支付台账', value: `${executedPaymentCount} 条` },
  ];
});

const nextActions = computed<ActionCard[]>(() => {
  const payload = blockData('next_actions');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const actions = Array.isArray(data.actions) ? data.actions : [];
  return actions.map((item, index) => {
    const row = item && typeof item === 'object' ? item as DashboardActionRow : {};
    const state = asText(row.state || 'available') || 'available';
    const intent = asText(row.intent || '');
    const stateLabel = asText(row.state_label || '');
    const stateTone = asText(row.state_tone || '');
    const buttonLabel = asText(row.button_label || '');
    const reason = asText(row.reason || '');
    const recommended = Boolean(row.recommended);
    return {
      key: asText(row.key || `action_${index + 1}`),
      label: asText(row.label || row.key || '下一步动作'),
      hint: actionHint(row),
      reason,
      advancesToStage: asText(row.advances_to_stage || ''),
      intent,
      params: (row.params && typeof row.params === 'object') ? row.params as Record<string, unknown> : {},
      state,
      stateLabel: stateLabel || actionStateLabel(state),
      stateTone: stateTone || (state === 'blocked' ? 'warning' : 'success'),
      buttonLabel: actionButtonLabel(row, state) || buttonLabel || '执行',
      disabled: !intent || state === 'blocked' && intent !== 'project.execution.advance',
      recommended,
    };
  }).sort((left, right) => {
    if (left.recommended !== right.recommended) return left.recommended ? -1 : 1;
    return 0;
  });
});

const primaryAction = computed<ActionCard | null>(() => {
  return nextActions.value.find((item) => item.recommended) || nextActions.value[0] || null;
});

const secondaryActions = computed<ActionCard[]>(() => {
  const primaryKey = primaryAction.value?.key || '';
  return nextActions.value.filter((item) => item.key !== primaryKey);
});

const currentStateText = computed(() => {
  const payload = blockData('next_actions');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  const stateLabel = asText(summary.current_state_label || '');
  const pilotState = asText(summary.pilot_precheck_state || '');
  if (pilotState === 'blocked') {
    return stateLabel || '--';
  }
  if (stateLabel) {
    return stateLabel;
  }
  return asText(entry.value?.state_fallback_text || '') || '--';
});

const nextStepText = computed(() => {
  const payload = blockData('next_actions');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  const pilotState = asText(summary.pilot_precheck_state || '');
  const pilotMessage = asText(summary.pilot_primary_message || '');
  if (pilotState === 'blocked' && pilotMessage) {
    return pilotMessage;
  }
  const nextStepLabel = asText(summary.next_step_label || '');
  if (nextStepLabel) {
    return nextStepLabel;
  }
  const firstAction = nextActions.value[0];
  return firstAction ? firstAction.label : '--';
});

function resetRuntimeBlocks() {
  const nextState: Record<string, BlockRuntimeState> = {};
  (entry.value?.blocks || []).forEach((row) => {
    const key = asText(row.key || '');
    if (!key) return;
    nextState[key] = { loading: false, error: '', payload: null };
  });
  runtimeBlocks.value = nextState;
}

function resetCostEntryForm() {
  const defaults = costEntryPayload.value.defaults && typeof costEntryPayload.value.defaults === 'object'
    ? costEntryPayload.value.defaults as Record<string, unknown>
    : {};
  costEntryForm.value = {
    date: asText(defaults.date || ''),
    amount: asText(defaults.amount || ''),
    description: asText(defaults.description || ''),
    cost_code_id: asNumber(defaults.cost_code_id || 0),
  };
}

function resetPaymentEntryForm() {
  const defaults = paymentEntryPayload.value.defaults && typeof paymentEntryPayload.value.defaults === 'object'
    ? paymentEntryPayload.value.defaults as Record<string, unknown>
    : {};
  paymentEntryForm.value = {
    date: asText(defaults.date || ''),
    amount: asText(defaults.amount || ''),
    description: asText(defaults.description || ''),
  };
}

function shouldHydrateCostEntryDefaults() {
  return !asText(costEntryForm.value.date)
    && !asText(costEntryForm.value.amount)
    && !asText(costEntryForm.value.description)
    && asNumber(costEntryForm.value.cost_code_id) <= 0;
}

function shouldHydratePaymentEntryDefaults() {
  return !asText(paymentEntryForm.value.date)
    && !asText(paymentEntryForm.value.amount)
    && !asText(paymentEntryForm.value.description);
}

async function refreshBlock(blockKey: string) {
  const key = asText(blockKey);
  if (!key) return;
  const hints = entry.value?.runtime_fetch_hints?.blocks || {};
  const hint = hints[key];
  if (!hint?.intent) {
    runtimeBlocks.value[key] = { loading: false, error: '缺少 runtime fetch hint', payload: null };
    return;
  }
  runtimeBlocks.value = {
    ...runtimeBlocks.value,
    [key]: {
      loading: true,
      error: '',
      payload: runtimeBlocks.value[key]?.payload || null,
    },
  };
  try {
    const data = await intentRequest<RuntimeBlockResponse>({
      intent: hint.intent,
      params: hint.params || {},
      context: {
        scene_key: currentSceneKey.value,
        page_key: 'project.management.dashboard',
        project_id: currentProjectId.value,
      },
    });
    runtimeBlocks.value = {
      ...runtimeBlocks.value,
      [key]: {
        loading: false,
        error: '',
        payload: (data?.block && typeof data.block === 'object') ? data.block : null,
      },
    };
  } catch (err) {
    runtimeBlocks.value = {
      ...runtimeBlocks.value,
      [key]: {
        loading: false,
        error: err instanceof Error ? err.message : 'runtime block load failed',
        payload: runtimeBlocks.value[key]?.payload || null,
      },
    };
  }
}

async function refreshAllBlocks() {
  const keys = blockDescriptors.value.map((row) => asText(row.key || '')).filter(Boolean);
  if (currentSceneKey.value === 'cost.tracking') {
    const ordered = ['cost_entry', 'cost_summary', 'cost_list', 'next_actions'];
    const seen = new Set<string>();
    for (const key of ordered) {
      if (!keys.includes(key)) continue;
      seen.add(key);
      await refreshBlock(key);
    }
    for (const key of keys) {
      if (seen.has(key)) continue;
      await refreshBlock(key);
    }
  } else if (currentSceneKey.value === 'payment') {
    const ordered = ['payment_entry', 'payment_summary', 'payment_list', 'next_actions'];
    const seen = new Set<string>();
    for (const key of ordered) {
      if (!keys.includes(key)) continue;
      seen.add(key);
      await refreshBlock(key);
    }
    for (const key of keys) {
      if (seen.has(key)) continue;
      await refreshBlock(key);
    }
  } else if (currentSceneKey.value === 'settlement') {
    const ordered = ['settlement_summary'];
    const seen = new Set<string>();
    for (const key of ordered) {
      if (!keys.includes(key)) continue;
      seen.add(key);
      await refreshBlock(key);
    }
    for (const key of keys) {
      if (seen.has(key)) continue;
      await refreshBlock(key);
    }
  } else {
    const tasks = keys.map((key) => refreshBlock(key));
    await Promise.allSettled(tasks);
  }
  if (currentSceneKey.value === 'cost.tracking' && shouldHydrateCostEntryDefaults()) {
    resetCostEntryForm();
  }
  if (currentSceneKey.value === 'payment' && shouldHydratePaymentEntryDefaults()) {
    resetPaymentEntryForm();
  }
}

function currentEntryIntent() {
  return SCENE_ENTRY_INTENTS[currentSceneKey.value] || PROJECT_DASHBOARD_ENTRY_INTENT;
}

function reloadCurrentScene() {
  return loadEntry(currentEntryIntent(), { project_context: currentProjectContext.value });
}

async function loadEntry(intent: string, params: Record<string, unknown>) {
  loadingTitle.value = '正在加载场景...';
  pageStatus.value = 'loading';
  try {
    const data = await intentRequest<GenericEntry>({
      intent,
      params,
      context: {
        scene_key: currentSceneKey.value || intent.replace('.enter', ''),
        page_key: 'project.management.dashboard',
        project_id: currentProjectId.value,
      },
    });
    entry.value = (data && typeof data === 'object') ? data : {};
    currentSceneKey.value = asText(entry.value?.scene_key || '') || intent.replace('.enter', '');
    session.setActiveProjectContext(currentProjectContext.value);
    resetRuntimeBlocks();
    pageStatus.value = 'ready';
    await refreshAllBlocks();
    if (isDashboardSurface.value) {
      await loadProjectSwitcherOptions();
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : 'unknown error';
    if (intent === PROJECT_DASHBOARD_ENTRY_INTENT && message.includes('PROJECT_NOT_FOUND')) {
      session.clearActiveProjectContext();
      await router.replace('/my-work');
      return;
    }
    pageStatus.value = 'error';
    errorTitle.value = '产品生命周期工作台加载失败';
    errorMessage.value = message;
  }
}

async function loadProjectSwitcherOptions() {
  const fallbackContext = currentProjectContext.value;
  const fallbackProjectId = asNumber(fallbackContext.project_id || 0);
  const fallbackOption = fallbackProjectId > 0
    ? {
      project_id: fallbackProjectId,
      project_name: asText(fallbackContext.project_name || `项目 ${fallbackProjectId}`),
      execution_stage_label: asText(fallbackContext.execution_stage_label || ''),
      stage_label: asText(fallbackContext.stage_label || ''),
      milestone_label: asText(fallbackContext.milestone_label || ''),
      project_condition: asText(fallbackContext.project_condition || ''),
      status: asText(fallbackContext.status || ''),
      active: true,
      project_context: fallbackContext,
    }
    : null;
  try {
    const result = await intentRequest<{ options?: ProjectSwitchOption[] }>({
      intent: 'project.entry.context.options',
      params: {
        project_context: currentProjectContext.value,
      },
      context: {
        scene_key: currentSceneKey.value,
        page_key: 'project.management.dashboard',
        project_id: currentProjectId.value,
      },
    });
    const remoteOptions = Array.isArray(result?.options) ? result.options : [];
    const merged = new Map<number, ProjectSwitchOption>();
    for (const item of remoteOptions) {
      const projectId = asNumber(item?.project_id || 0);
      if (projectId <= 0) continue;
      merged.set(projectId, {
        ...item,
        active: projectId === currentProjectId.value || Boolean(item?.active),
      });
    }
    if (fallbackOption && !merged.has(fallbackOption.project_id)) {
      merged.set(fallbackOption.project_id, fallbackOption);
    }
    projectSwitcherOptions.value = Array.from(merged.values());
  } catch {
    projectSwitcherOptions.value = fallbackOption ? [fallbackOption] : [];
  }
}

async function handleProjectSwitch(event: Event) {
  const target = event.target as HTMLSelectElement | null;
  const nextProjectId = Number(target?.value || 0);
  if (nextProjectId <= 0 || nextProjectId === currentProjectId.value) return;
  const option = projectSwitcherOptions.value.find((item) => Number(item.project_id || 0) === nextProjectId);
  const nextContext = option?.project_context && typeof option.project_context === 'object'
    ? option.project_context as Record<string, unknown>
    : { project_id: nextProjectId };
  transitionFeedback.value = {
    variant: 'success',
    title: '项目已切换',
    message: `当前已切换到 ${option?.project_name || `项目 ${nextProjectId}` }。`,
  };
  await loadEntry(PROJECT_DASHBOARD_ENTRY_INTENT, { project_context: nextContext });
}

async function runAction(action: ActionCard) {
  if (!action.intent || action.disabled) return;
  try {
    if (action.intent.endsWith('.enter')) {
      transitionFeedback.value = null;
      await loadEntry(action.intent, action.params);
      return;
    }
    if (action.intent.endsWith('.block.fetch')) {
      const blockKey = asText(action.params.block_key || '');
      if (blockKey) {
        await refreshBlock(blockKey);
        transitionFeedback.value = {
          variant: 'success',
          title: '区块已刷新',
          message: `已刷新 ${blockKey}。`,
        };
        return;
      }
    }
    const result = await intentRequest<Record<string, unknown>>({
      intent: action.intent,
      params: action.params,
      context: {
        scene_key: currentSceneKey.value,
        page_key: 'project.management.dashboard',
        project_id: currentProjectId.value,
      },
    });
    const fromState = asText(result.from_state || '');
    const toState = asText(result.to_state || '');
    const blocked = asText(result.result || '') === 'blocked';
    const message = asText(result.message || '');
    transitionFeedback.value = {
      variant: blocked ? 'warning' : 'success',
      title: blocked ? '动作执行受阻' : '动作执行完成',
      message: action.advancesToStage
        ? `已推进到${action.advancesToStage}阶段。${message || '请继续按驾驶舱推荐动作推进。'}`
        : fromState && toState
          ? `状态变化：${fromState} → ${toState}。${message || '已返回结果'}`
          : `执行结果：${message || '已返回结果'}。`,
    };
    if (asText(action.intent) === 'project.connection.transition' || asText(result.to_state || '')) {
      await loadEntry(PROJECT_DASHBOARD_ENTRY_INTENT, { project_context: currentProjectContext.value });
      return;
    }
    await reloadCurrentScene();
  } catch (err) {
    transitionFeedback.value = {
      variant: 'warning',
      title: '动作执行失败',
      message: err instanceof Error ? err.message : 'unknown error',
    };
  }
}

async function submitCostEntry() {
  if (costEntrySubmitting.value) return;
  const formIntent = asText(costEntryPayload.value.intent || '');
  if (!formIntent) return;
  costEntrySubmitting.value = true;
  try {
    const result = await intentRequest<Record<string, unknown>>({
      intent: formIntent,
      params: {
        project_id: currentProjectId.value,
        project_context: currentProjectContext.value,
        date: costEntryForm.value.date,
        amount: costEntryForm.value.amount,
        description: costEntryForm.value.description,
        cost_code_id: costEntryForm.value.cost_code_id || 0,
      },
      context: {
        scene_key: currentSceneKey.value,
        page_key: 'project.management.dashboard',
        project_id: currentProjectId.value,
      },
    });
    transitionFeedback.value = {
      variant: 'success',
      title: '成本记录已创建',
      message: asText(result.summary_hint || '') || '已创建成本记录，并刷新成本记录与成本汇总。',
    };
    await loadEntry(PROJECT_DASHBOARD_ENTRY_INTENT, { project_context: currentProjectContext.value });
    resetCostEntryForm();
  } catch (err) {
    transitionFeedback.value = {
      variant: 'warning',
      title: '成本录入失败',
      message: err instanceof Error ? err.message : 'unknown error',
    };
  } finally {
    costEntrySubmitting.value = false;
  }
}

async function submitPaymentEntry() {
  if (paymentEntrySubmitting.value) return;
  const formIntent = asText(paymentEntryPayload.value.intent || '');
  if (!formIntent) return;
  paymentEntrySubmitting.value = true;
  try {
    const result = await intentRequest<Record<string, unknown>>({
      intent: formIntent,
      params: {
        project_id: currentProjectId.value,
        project_context: currentProjectContext.value,
        date: paymentEntryForm.value.date,
        amount: paymentEntryForm.value.amount,
        description: paymentEntryForm.value.description,
      },
      context: {
        scene_key: currentSceneKey.value,
        page_key: 'project.management.dashboard',
        project_id: currentProjectId.value,
      },
    });
    transitionFeedback.value = {
      variant: 'success',
      title: '付款记录已创建',
      message: asText(result.summary_hint || '') || '已创建付款记录，并刷新付款记录与付款汇总。',
    };
    await loadEntry(PROJECT_DASHBOARD_ENTRY_INTENT, { project_context: currentProjectContext.value });
    resetPaymentEntryForm();
  } catch (err) {
    transitionFeedback.value = {
      variant: 'warning',
      title: '付款录入失败',
      message: err instanceof Error ? err.message : 'unknown error',
    };
  } finally {
    paymentEntrySubmitting.value = false;
  }
}

async function loadLifecycleEntry() {
  const pendingProjectContext = consumePendingProjectContext();
  const activeProjectContext = currentProjectId.value > 0 ? currentProjectContext.value : session.activeProjectContext;
  await loadEntry(
    PROJECT_DASHBOARD_ENTRY_INTENT,
    pendingProjectContext
      ? { project_context: pendingProjectContext }
      : (activeProjectContext && typeof activeProjectContext === 'object' ? { project_context: activeProjectContext } : {}),
  );
}

watch(
  () => route.fullPath,
  () => {
    void loadLifecycleEntry();
  },
  { immediate: true },
);
</script>

<style scoped>
.project-dashboard-page {
  display: grid;
  gap: 16px;
  padding: 18px;
  background:
    radial-gradient(circle at top left, rgba(196, 220, 255, 0.9), transparent 32%),
    linear-gradient(180deg, #eef4f8 0%, #f9fbfc 100%);
  min-height: 100%;
}

.dashboard-shell {
  display: grid;
  gap: 16px;
}

.status-wrap {
  padding: 4px;
}

.hero-card,
.state-explain-card,
.summary-card,
.block-card,
.feedback-banner {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(22, 55, 89, 0.08);
  border-radius: 18px;
  box-shadow: 0 18px 40px rgba(33, 56, 82, 0.08);
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding: 20px 22px;
}

.hero-actions {
  display: grid;
  gap: 10px;
  justify-items: end;
}

.project-switcher {
  display: grid;
  gap: 6px;
  color: #486581;
  font-size: 12px;
}

.project-switcher select {
  min-width: 240px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(22, 55, 89, 0.12);
  background: rgba(255, 255, 255, 0.96);
  color: #102a43;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #486581;
}

.hero-card h1,
.block-header h2 {
  margin: 0;
  color: #102a43;
}

.hero-subtitle,
.block-header p,
.hero-state,
.hero-next {
  margin: 8px 0 0;
  color: #627d98;
}

.hero-state {
  color: #102a43;
  font-weight: 600;
}

.hero-next {
  color: #0b6e4f;
}

.feedback-banner {
  padding: 16px 18px;
}

.feedback-banner[data-variant='success'] {
  border-color: rgba(12, 126, 89, 0.22);
}

.feedback-banner[data-variant='warning'] {
  border-color: rgba(180, 83, 9, 0.22);
}

.feedback-banner strong {
  display: block;
  color: #102a43;
}

.feedback-banner p {
  margin: 8px 0 0;
  color: #486581;
}

.summary-card {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  padding: 16px;
}

.state-explain-card {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  padding: 16px;
}

.flow-map-card {
  display: grid;
  gap: 14px;
  padding: 16px;
}

.flow-map-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.completion-pill {
  display: grid;
  gap: 2px;
  padding: 10px 14px;
  border-radius: 14px;
  background: rgba(11, 110, 79, 0.08);
  color: #0b6e4f;
}

.flow-map-track {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.flow-map-step {
  display: grid;
  gap: 6px;
  justify-items: center;
  padding: 12px 10px;
  border-radius: 14px;
  background: rgba(240, 244, 248, 0.72);
  color: #627d98;
}

.flow-map-step[data-status='done'] {
  background: rgba(11, 110, 79, 0.12);
  color: #0b6e4f;
}

.flow-map-step[data-status='current'] {
  background: rgba(24, 144, 255, 0.12);
  color: #1f4b99;
}

.flow-map-dot {
  font-size: 18px;
  line-height: 1;
}

.state-explain-item {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(240, 244, 248, 0.72);
}

.state-explain-label {
  font-size: 12px;
  color: #7b8794;
}

.summary-item {
  display: grid;
  gap: 6px;
}

.summary-item-highlight {
  grid-column: 1 / -1;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(16, 42, 67, 0.08);
}

.summary-label {
  font-size: 12px;
  color: #7b8794;
}

.summary-value {
  color: #102a43;
}

.summary-copy {
  margin: 0;
  color: #627d98;
  font-size: 13px;
}

.blocks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.block-card {
  display: grid;
  gap: 14px;
  padding: 18px;
}

.block-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.ghost-button,
.primary-button {
  border-radius: 999px;
  border: 1px solid rgba(16, 42, 67, 0.12);
  background: #fff;
  color: #102a43;
  padding: 8px 14px;
  font-size: 13px;
  cursor: pointer;
}

.primary-button {
  background: #102a43;
  color: #fff;
}

.primary-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.block-status {
  padding: 18px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.04);
  color: #52606d;
}

.block-status-error {
  background: rgba(190, 24, 93, 0.08);
  color: #9d174d;
}

.block-status-warning {
  background: rgba(180, 83, 9, 0.08);
  color: #9a3412;
}

.metric-list,
.task-list,
.action-list,
.risk-list,
.cost-form-card {
  display: grid;
  gap: 12px;
}

.cost-form-field {
  display: grid;
  gap: 6px;
  color: #345067;
  font-size: 13px;
}

.cost-input {
  width: 100%;
  border: 1px solid rgba(49, 83, 114, 0.18);
  border-radius: 12px;
  padding: 10px 12px;
  font: inherit;
  background: rgba(255, 255, 255, 0.94);
  color: #163047;
}

.cost-form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.cost-form-hint {
  color: #567185;
  font-size: 13px;
}

.metric-row,
.task-row,
.action-card,
.risk-alert {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(240, 244, 248, 0.72);
}

.action-title-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.recommended-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(12, 126, 89, 0.14);
  color: #0b6e4f;
  font-size: 12px;
  font-weight: 700;
}

.action-reason {
  margin: 6px 0 0;
  color: #486581;
  font-size: 13px;
}

.action-card-primary {
  border: 1px solid rgba(12, 126, 89, 0.22);
  background: rgba(240, 255, 248, 0.92);
}

.risk-summary {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  color: #334e68;
}

.risk-impact,
.risk-action-copy {
  margin: 6px 0 0;
  color: #486581;
  font-size: 13px;
}

.action-side {
  display: grid;
  gap: 8px;
  justify-items: end;
}

.action-state {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 72px;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  background: rgba(16, 42, 67, 0.08);
  color: #102a43;
}

.action-state[data-tone='warning'] {
  background: rgba(180, 83, 9, 0.12);
  color: #9a3412;
}

.action-state[data-tone='success'] {
  background: rgba(12, 126, 89, 0.14);
  color: #0b6e4f;
}

.action-state[data-tone='info'] {
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
}

@media (max-width: 900px) {
  .hero-card,
  .block-header,
  .metric-row,
  .task-row,
  .action-card,
  .risk-alert {
    grid-template-columns: 1fr;
    display: grid;
  }

  .action-side {
    justify-items: start;
  }
}
</style>
