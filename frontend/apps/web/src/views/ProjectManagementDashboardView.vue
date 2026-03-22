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
import { PROJECT_DASHBOARD_ENTRY_INTENT } from '../app/projectCreationBaseline';

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
  blocks?: Array<{ key?: string; title?: string; state?: string }>;
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

const route = useRoute();
const pageStatus = ref<'loading' | 'error' | 'ready'>('loading');
const errorTitle = ref('产品生命周期工作台加载失败');
const errorMessage = ref('');
const loadingTitle = ref('正在加载场景...');
const currentSceneKey = ref('project.dashboard');
const entry = ref<GenericEntry | null>(null);
const runtimeBlocks = ref<Record<string, BlockRuntimeState>>({});
const transitionFeedback = ref<ActionFeedback | null>(null);

function asText(value: unknown) {
  return String(value || '').trim();
}

function asNumber(value: unknown) {
  const num = Number(value || 0);
  return Number.isFinite(num) ? num : 0;
}

function resolveProjectIdFromQuery() {
  const rawId = route.query.project_id;
  const value = Array.isArray(rawId) ? rawId[0] : rawId;
  const projectId = Number(value || 0);
  return Number.isFinite(projectId) && projectId > 0 ? projectId : 0;
}

const currentSceneLabel = computed(() => {
  return asText(entry.value?.scene_label || '') || '项目场景';
});

const blockDescriptors = computed(() => entry.value?.blocks || []);

const summaryRows = computed(() => {
  const summary = (entry.value?.summary && typeof entry.value.summary === 'object') ? entry.value.summary : {};
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
  if (blockKey === 'progress') return '当前状态：查看项目全局进度。下一步：确认是否进入计划准备。';
  if (blockKey === 'risks') return '当前状态：识别阻塞项。下一步：优先处理高优先级风险。';
  if (blockKey === 'plan_summary_detail') return '当前状态：查看计划准备度。下一步：确认能否进入执行推进。';
  if (blockKey === 'plan_tasks') return '当前状态：核对计划任务。下一步：补齐关键计划输入。';
  if (blockKey === 'execution_tasks') return '当前状态：查看执行任务。下一步：根据执行状态推进。';
  if (blockKey === 'pilot_precheck') return '当前状态：核对首轮试点前提。下一步：先清除阻断项，再执行推进。';
  if (blockKey === 'next_actions') return '当前状态：查看可执行动作。下一步：按建议动作继续推进。';
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
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    const state = asText(row.state || 'open') || 'open';
    return {
      key: asText(row.task_id || row.id || row.key || `${blockKey}_${index + 1}`),
      title: asText(row.name || '未命名记录'),
      subtitle: asText(row.subtitle || '') || [asText(row.stage_name || ''), asText(row.deadline || '')].filter(Boolean).join(' · ') || '暂无补充信息',
      stateLabel:
        state === 'draft' ? '草稿'
          : state === 'ready' ? '就绪'
            : state === 'in_progress' ? '进行中'
              : state === 'done' ? '已完成'
                : state === 'cancelled' ? '已取消'
                  : state === 'blocked' ? '阻塞' : '待处理',
      stateTone:
        state === 'done' ? 'success'
          : state === 'blocked' || state === 'cancelled' ? 'warning'
            : state === 'ready' ? 'success' : 'info',
    };
  });
}

function blockEmptyText(blockKey: string) {
  const payload = blockData(blockKey);
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const summary = (data.summary && typeof data.summary === 'object') ? data.summary as Record<string, unknown> : {};
  const hint = asText(summary.empty_hint || '');
  if (hint) return hint;
  if (blockKey === 'plan_tasks') return '当前项目还没有计划任务。';
  if (blockKey === 'execution_tasks') return '当前项目还没有执行任务。';
  if (blockKey === 'pilot_precheck') return '当前项目还没有试点前检查结果。';
  return '当前区块暂无数据。';
}

function humanReason(reasonCode: string) {
  const code = asText(reasonCode);
  if (code === 'EXECUTION_READY_TO_START') return '当前满足首轮试点前提，可以开始执行。';
  if (code === 'EXECUTION_READY_TO_COMPLETE') return '当前任务正在执行中，可以推进到执行完成。';
  if (code === 'EXECUTION_BLOCKED_REQUIRES_UNBLOCK') return '当前执行处于阻塞态，需要先解除阻塞后再继续。';
  if (code === 'EXECUTION_ALREADY_DONE') return '当前项目执行已完成，无需继续推进。';
  if (code === 'EXECUTION_TASK_MISSING') return '当前项目还没有可推进的任务。';
  if (code === 'EXECUTION_TASK_START_FAILED') return '任务未能成功进入执行中。';
  if (code === 'EXECUTION_TASK_NOT_IN_PROGRESS') return '当前没有处于执行中的任务，无法完成推进。';
  if (code === 'EXECUTION_TASK_COMPLETE_FAILED') return '任务未能成功完成。';
  if (code === 'EXECUTION_TASK_RECOVER_FAILED') return '任务未能恢复到可执行状态。';
  if (code === 'EXECUTION_SCOPE_MULTI_OPEN_TASKS_UNSUPPORTED') return '首轮试点仅允许 1 个开放任务，请先收口到单任务。';
  if (code === 'EXECUTION_PROJECT_TASK_STATE_DRIFT') return '项目执行态与任务状态不一致，请先校正数据。';
  if (code === 'EXECUTION_PROJECT_ACTIVITY_DRIFT') return '跟进行为与 mail.activity 不一致，请先校正活动记录。';
  if (code === 'PILOT_ROOT_TASK_MISSING') return '试点前必须先初始化项目根任务。';
  if (code === 'PILOT_SINGLE_OPEN_TASK_REQUIRED') return '试点版要求仅保留 1 个开放任务。';
  if (code === 'PILOT_REQUIRED_FIELDS_MISSING') return '试点关键字段仍未补齐，请先补全配置。';
  if (code === 'PILOT_LIFECYCLE_STATE_BLOCKED') return '当前项目生命周期状态不允许作为首轮试点。';
  if (code === 'EXECUTION_TRANSITION_READY_TO_IN_PROGRESS') return '已从执行就绪推进到执行中。';
  if (code === 'EXECUTION_TRANSITION_IN_PROGRESS_TO_DONE') return '已从执行中推进到执行完成。';
  if (code === 'EXECUTION_TRANSITION_BLOCKED_TO_READY') return '已从执行阻塞恢复到执行就绪。';
  if (code === 'EXECUTION_TRANSITION_NOT_ALLOWED') return '当前状态不允许执行这一步推进。';
  if (code === 'EXECUTION_TRANSITION_WRITE_FAILED') return '执行状态写入失败，请刷新后重试。';
  return code || '已返回结果';
}

function humanExecutionState(state: string) {
  const value = asText(state);
  if (value === 'ready') return '执行就绪';
  if (value === 'in_progress') return '执行中';
  if (value === 'blocked') return '执行阻塞';
  if (value === 'done') return '执行完成';
  return value || '-';
}

function actionStateLabel(state: string) {
  if (state === 'ready' || state === 'available') return '可执行';
  if (state === 'blocked') return '受阻';
  if (state === 'planned') return '预留';
  return '待处理';
}

function actionHint(row: Record<string, unknown>) {
  const rawHint = asText(row.hint || '等待后续场景接入');
  const reasonCode = asText(row.reason_code || '');
  const reason = humanReason(reasonCode);
  if (!reasonCode) return rawHint;
  if (rawHint.includes(reason)) return rawHint;
  return `${rawHint} ${reason}`;
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
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    const status = asText(row.status || 'fail');
    const reasonCode = asText(row.reason_code || '');
    return {
      key: asText(row.key || `pilot_check_${index + 1}`),
      title: `${asText(row.label || row.key || '试点检查')} · ${status === 'pass' ? '通过' : '受阻'}`,
      description: asText(row.message || '') || humanReason(reasonCode),
    };
  });
});

const nextActions = computed<ActionCard[]>(() => {
  const payload = blockData('next_actions');
  const data = (payload?.data && typeof payload.data === 'object') ? payload.data : {};
  const actions = Array.isArray(data.actions) ? data.actions : [];
  return actions.map((item, index) => {
    const row = item && typeof item === 'object' ? item as Record<string, unknown> : {};
    const state = asText(row.state || 'available') || 'available';
    const intent = asText(row.intent || '');
    return {
      key: asText(row.key || `action_${index + 1}`),
      label: asText(row.label || row.key || '下一步动作'),
      hint: actionHint(row),
      intent,
      params: (row.params && typeof row.params === 'object') ? row.params as Record<string, unknown> : {},
      state,
      stateLabel: actionStateLabel(state),
      stateTone: state === 'blocked' ? 'warning' : 'success',
      buttonLabel: intent.endsWith('.enter') ? '进入' : intent === 'project.execution.advance' ? '推进' : '执行',
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
    return `当前状态：${stateLabel || '执行推进'}，且未通过首轮试点检查。`;
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
        project_id: entry.value?.project_id || resolveProjectIdFromQuery(),
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
  const tasks = blockDescriptors.value.map((row) => refreshBlock(asText(row.key || '')));
  await Promise.allSettled(tasks);
}

async function loadEntry(intent: string, params: Record<string, unknown>) {
  const projectId = asNumber(params.project_id || resolveProjectIdFromQuery());
  loadingTitle.value = '正在加载场景...';
  pageStatus.value = 'loading';
  try {
    const data = await intentRequest<GenericEntry>({
      intent,
      params,
      context: {
        scene_key: currentSceneKey.value || intent.replace('.enter', ''),
        page_key: 'project.management.dashboard',
        project_id: projectId,
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
    const result = await intentRequest<Record<string, unknown>>({
      intent: action.intent,
      params: action.params,
      context: {
        scene_key: currentSceneKey.value,
        page_key: 'project.management.dashboard',
        project_id: entry.value?.project_id || resolveProjectIdFromQuery(),
      },
    });
    const fromState = asText(result.from_state || '');
    const toState = asText(result.to_state || '');
    const reasonCode = asText(result.reason_code || '');
    const blocked = asText(result.result || '') === 'blocked';
    const message = asText(result.message || '');
    transitionFeedback.value = {
      variant: blocked ? 'warning' : 'success',
      title: blocked ? '动作执行受阻' : '动作执行完成',
      message: fromState && toState
        ? `状态变化：${humanExecutionState(fromState)} → ${humanExecutionState(toState)}。${humanReason(reasonCode)}`
        : `执行结果：${message || humanReason(reasonCode)}。`,
    };
    await refreshAllBlocks();
  } catch (err) {
    transitionFeedback.value = {
      variant: 'warning',
      title: '动作执行失败',
      message: err instanceof Error ? err.message : 'unknown error',
    };
  }
}

async function loadLifecycleEntry() {
  const projectId = resolveProjectIdFromQuery();
  if (projectId <= 0) {
    pageStatus.value = 'error';
    errorTitle.value = '缺少项目上下文';
    errorMessage.value = '访问项目生命周期工作台必须提供 project_id。';
    return;
  }
  await loadEntry(PROJECT_DASHBOARD_ENTRY_INTENT, { project_id: projectId });
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
.risk-list {
  display: grid;
  gap: 12px;
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
