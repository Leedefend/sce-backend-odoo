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
          <h1>{{ entry?.title || '项目生命周期工作台' }}</h1>
          <p class="hero-subtitle">项目 ID {{ entry?.project_id || '-' }}</p>
          <p class="hero-state">{{ currentStateText }}</p>
          <p class="hero-next">{{ nextStepText }}</p>
        </div>
        <button type="button" class="ghost-button" @click="refreshAllBlocks">刷新区块</button>
      </header>

      <section v-if="transitionFeedback" class="feedback-banner" :data-variant="transitionFeedback.variant">
        <strong>{{ transitionFeedback.title }}</strong>
        <p>{{ transitionFeedback.message }}</p>
      </section>

      <section class="summary-card">
        <div v-for="item in summaryRows" :key="item.key" class="summary-item">
          <span class="summary-label">{{ item.label }}</span>
          <strong class="summary-value">{{ item.value }}</strong>
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
                <strong>{{ item.title }}</strong>
                <p>{{ item.description }}</p>
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
              <div v-for="item in nextActions" :key="item.key" class="action-card">
                <div>
                  <strong>{{ item.label }}</strong>
                  <p>{{ item.hint }}</p>
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
import { useRoute } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { intentRequest } from '../api/intents';
import { consumePendingProjectContext, PROJECT_DASHBOARD_ENTRY_INTENT } from '../app/projectCreationBaseline';

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
  intent: string;
  params: Record<string, unknown>;
  state: string;
  stateLabel: string;
  stateTone: string;
  buttonLabel: string;
  disabled: boolean;
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

const SCENE_ENTRY_INTENTS: Record<string, string> = {
  'project.dashboard': 'project.dashboard.enter',
  'project.execution': 'project.execution.enter',
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

const currentProjectId = computed(() => asNumber(currentProjectContext.value.project_id || entry.value?.project_id || 0));

const currentSceneLabel = computed(() => {
  return asText(entry.value?.scene_label || '') || '项目场景';
});

const blockDescriptors = computed(() => entry.value?.blocks || []);

const summaryRows = computed(() => {
  const summary = (entry.value?.summary && typeof entry.value.summary === 'object') ? entry.value.summary : {};
  if (currentSceneKey.value === 'cost.tracking') {
    const total = asNumber(summary.cost_total_amount);
    const currency = asText(summary.currency_name || '');
    return [
      { key: 'project_code', label: '项目编码', value: asText(summary.project_code || '--') || '--' },
      { key: 'manager_name', label: '项目经理', value: asText(summary.manager_name || '--') || '--' },
      { key: 'stage_name', label: '当前阶段', value: asText(summary.stage_name || '--') || '--' },
      { key: 'cost_record_count', label: '成本记录数', value: `${asNumber(summary.cost_record_count)} 条` },
      { key: 'cost_total_amount', label: '成本合计', value: currency ? `${total} ${currency}` : `${total}` },
      { key: 'draft_cost_amount', label: '草稿金额', value: currency ? `${asNumber(summary.draft_cost_amount)} ${currency}` : `${asNumber(summary.draft_cost_amount)}` },
    ];
  }
  if (currentSceneKey.value === 'payment') {
    const total = asNumber(summary.payment_total_amount);
    const currency = asText(summary.currency_name || '');
    return [
      { key: 'project_code', label: '项目编码', value: asText(summary.project_code || '--') || '--' },
      { key: 'manager_name', label: '项目经理', value: asText(summary.manager_name || '--') || '--' },
      { key: 'stage_name', label: '当前阶段', value: asText(summary.stage_name || '--') || '--' },
      { key: 'payment_record_count', label: '付款记录数', value: `${asNumber(summary.payment_record_count)} 条` },
      { key: 'payment_total_amount', label: '付款合计', value: currency ? `${total} ${currency}` : `${total}` },
      { key: 'draft_payment_amount', label: '草稿金额', value: currency ? `${asNumber(summary.draft_payment_amount)} ${currency}` : `${asNumber(summary.draft_payment_amount)}` },
    ];
  }
  if (currentSceneKey.value === 'project.dashboard') {
    return [
      { key: 'project_name', label: '项目名称', value: asText(currentProjectContext.value.project_name || entry.value?.title || '--') || '--' },
      { key: 'stage_label', label: '当前阶段', value: asText(currentProjectContext.value.stage_label || summary.stage_name || '--') || '--' },
      { key: 'milestone_label', label: '当前里程碑', value: asText(currentProjectContext.value.milestone_label || '--') || '--' },
      { key: 'status', label: '当前状态', value: asText(currentProjectContext.value.status || summary.status || '--') || '--' },
      { key: 'progress_percent', label: '执行进度', value: `${asNumber(summary.progress_percent)}%` },
      { key: 'cost_total', label: '成本合计', value: `${asNumber(summary.cost_total)}` },
      { key: 'payment_total', label: '付款合计', value: `${asNumber(summary.payment_total)}` },
    ];
  }
  return [
    { key: 'project_code', label: '项目编码', value: asText(summary.project_code || '--') || '--' },
    { key: 'manager_name', label: '项目经理', value: asText(summary.manager_name || '--') || '--' },
    { key: 'partner_name', label: '建设单位', value: asText(summary.partner_name || '--') || '--' },
    { key: 'stage_name', label: '当前阶段', value: asText(summary.stage_name || '--') || '--' },
    { key: 'health_state', label: '健康度', value: asText(summary.health_state || '--') || '--' },
    { key: 'date_start', label: '计划开始', value: asText(summary.date_start || '--') || '--' },
    { key: 'date_end', label: '计划结束', value: asText(summary.date_end || '--') || '--' },
  ];
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
  return '区块按需加载。';
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
    const value = asNumber(row.value);
    const hint = asText(row.hint || '');
    return {
      code: asText(row.code || `risk_${index + 1}`),
      title: asText(row.title || row.code || '风险提醒'),
      description: hint ? `${hint} 当前值 ${value}` : `当前值 ${value}`,
    };
  });
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
      stateLabel: stateLabel || state || '待处理',
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
  if (blockKey === 'plan_tasks') return '当前项目还没有计划任务。';
  if (blockKey === 'execution_tasks') return '当前项目还没有执行任务。';
  if (blockKey === 'pilot_precheck') return '当前项目还没有试点前检查结果。';
  if (blockKey === 'cost_list') return '当前项目还没有成本记录。';
  if (blockKey === 'payment_list') return '当前项目还没有付款记录。';
  return '当前区块暂无数据。';
}

function actionStateLabel(state: string) {
  return asText(state || '') || '待处理';
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
  return rawHint || '等待后续场景接入';
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
  return asText(summary.state_fallback_text || '') || '录入后会刷新成本记录与成本汇总。';
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
  return asText(summary.state_fallback_text || '') || '录入后会刷新付款记录与付款汇总。';
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
  const display = (value: number) => currency ? `${value} ${currency}` : `${value}`;
  return [
    { key: 'total_cost', label: '总成本', value: display(totalCost) },
    { key: 'total_payment', label: '总付款', value: display(totalPayment) },
    { key: 'delta', label: '差额', value: display(delta) },
    { key: 'cost_record_count', label: '成本记录', value: `${costCount} 条` },
    { key: 'payment_record_count', label: '付款记录', value: `${paymentCount} 条` },
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
    return {
      key: asText(row.key || `action_${index + 1}`),
      label: asText(row.label || row.key || '下一步动作'),
      hint: actionHint(row),
      intent,
      params: (row.params && typeof row.params === 'object') ? row.params as Record<string, unknown> : {},
      state,
      stateLabel: stateLabel || actionStateLabel(state),
      stateTone: stateTone || (state === 'blocked' ? 'warning' : 'success'),
      buttonLabel: actionButtonLabel(row, state) || buttonLabel || '执行',
      disabled: !intent || state === 'blocked' && intent !== 'project.execution.advance',
    };
  });
});

const currentStateText = computed(() => {
  const payload = blockData('next_actions');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  const stateLabel = asText(summary.current_state_label || '');
  const pilotState = asText(summary.pilot_precheck_state || '');
  if (pilotState === 'blocked') {
    return stateLabel ? `当前状态：${stateLabel}` : '当前状态：未通过首轮试点检查';
  }
  if (stateLabel) {
    return `当前状态：${stateLabel}`;
  }
  return asText(entry.value?.state_fallback_text || '') || '当前状态：正在查看场景状态。';
});

const nextStepText = computed(() => {
  const payload = blockData('next_actions');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  const pilotState = asText(summary.pilot_precheck_state || '');
  const pilotMessage = asText(summary.pilot_primary_message || '');
  if (pilotState === 'blocked' && pilotMessage) {
    return `下一步：${pilotMessage}`;
  }
  const nextStepLabel = asText(summary.next_step_label || '');
  if (nextStepLabel) {
    return `下一步：${nextStepLabel}`;
  }
  const firstAction = nextActions.value[0];
  return firstAction ? `下一步：${firstAction.label}` : '下一步：刷新区块并继续查看建议动作。';
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
    resetRuntimeBlocks();
    pageStatus.value = 'ready';
    await refreshAllBlocks();
  } catch (err) {
    pageStatus.value = 'error';
    errorTitle.value = '产品生命周期工作台加载失败';
    errorMessage.value = err instanceof Error ? err.message : 'unknown error';
  }
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
      message: fromState && toState
        ? `状态变化：${fromState} → ${toState}。${message || '已返回结果'}`
        : `执行结果：${message || '已返回结果'}。`,
    };
    if (asText(action.intent) === 'project.connection.transition' || asText(result.to_state || '')) {
      await loadEntry(currentEntryIntent(), { project_context: currentProjectContext.value });
      return;
    }
    await refreshAllBlocks();
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
    await loadEntry(currentEntryIntent(), { project_context: currentProjectContext.value });
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
    await loadEntry(currentEntryIntent(), { project_context: currentProjectContext.value });
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
  await loadEntry(
    PROJECT_DASHBOARD_ENTRY_INTENT,
    pendingProjectContext ? { project_context: pendingProjectContext } : {},
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

.summary-item {
  display: grid;
  gap: 6px;
}

.summary-label {
  font-size: 12px;
  color: #7b8794;
}

.summary-value {
  color: #102a43;
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

.risk-summary {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  color: #334e68;
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
