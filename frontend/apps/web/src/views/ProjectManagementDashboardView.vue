<template>
  <section class="project-dashboard-page">
    <section v-if="pageStatus === 'loading'" class="status-wrap">
      <StatusPanel title="正在进入项目驾驶舱..." variant="info" />
    </section>
    <section v-else-if="pageStatus === 'error'" class="status-wrap">
      <StatusPanel :title="errorTitle" :message="errorMessage" variant="error" />
    </section>
    <section v-else class="dashboard-shell">
      <header class="hero-card">
        <div>
          <p class="eyebrow">Project Dashboard</p>
          <h1>{{ entry?.title || '项目驾驶舱' }}</h1>
          <p class="hero-subtitle">项目 ID {{ entry?.project_id || '-' }}</p>
        </div>
        <button type="button" class="ghost-button" @click="refreshAllBlocks">刷新区块</button>
      </header>

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
            当前区块暂无数据。
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

type DashboardRuntimeHint = {
  intent?: string;
  params?: Record<string, unknown>;
};

type DashboardEntry = {
  project_id?: number;
  title?: string;
  summary?: Record<string, unknown>;
  blocks?: Array<{ key?: string; title?: string; state?: string }>;
  suggested_action?: DashboardRuntimeHint & { reason_code?: string; key?: string };
  runtime_fetch_hints?: {
    blocks?: Record<string, DashboardRuntimeHint>;
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

const route = useRoute();
const pageStatus = ref<'loading' | 'error' | 'ready'>('loading');
const errorTitle = ref('项目驾驶舱加载失败');
const errorMessage = ref('');
const entry = ref<DashboardEntry | null>(null);
const runtimeBlocks = ref<Record<string, BlockRuntimeState>>({});

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

const blockDescriptors = computed(() => entry.value?.blocks || []);

const summaryRows = computed(() => {
  const summary = (entry.value?.summary && typeof entry.value.summary === 'object') ? entry.value.summary : {};
  return [
    { key: 'project_code', label: '项目编码', value: asText(summary.project_code || '--') || '--' },
    { key: 'manager_name', label: '项目经理', value: asText(summary.manager_name || '--') || '--' },
    { key: 'partner_name', label: '建设单位', value: asText(summary.partner_name || '--') || '--' },
    { key: 'stage_name', label: '当前阶段', value: asText(summary.stage_name || '--') || '--' },
    { key: 'health_state', label: '健康度', value: asText(summary.health_state || '--') || '--' },
  ];
});

function blockState(blockKey: string): BlockRuntimeState {
  return runtimeBlocks.value[blockKey] || { loading: false, error: '', payload: null };
}

function blockData(blockKey: string) {
  return blockState(blockKey).payload;
}

function blockCaption(blockKey: string) {
  if (blockKey === 'progress') return '进度区块独立加载，失败不影响整页。';
  if (blockKey === 'risks') return '风险区块独立加载，失败不影响整页。';
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
        scene_key: 'project.dashboard',
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

async function loadDashboardEntry() {
  const projectId = resolveProjectIdFromQuery();
  if (projectId <= 0) {
    pageStatus.value = 'error';
    errorTitle.value = '缺少项目上下文';
    errorMessage.value = '访问项目驾驶舱必须提供 project_id。';
    return;
  }

  try {
    pageStatus.value = 'loading';
    const data = await intentRequest<DashboardEntry>({
      intent: 'project.dashboard.enter',
      params: { project_id: projectId },
      context: {
        scene_key: 'project.dashboard',
        page_key: 'project.management.dashboard',
        project_id: projectId,
      },
    });
    entry.value = (data && typeof data === 'object') ? data : {};
    resetRuntimeBlocks();
    pageStatus.value = 'ready';
    await refreshAllBlocks();
  } catch (err) {
    pageStatus.value = 'error';
    errorTitle.value = '项目驾驶舱加载失败';
    errorMessage.value = err instanceof Error ? err.message : 'unknown error';
  }
}

watch(
  () => route.fullPath,
  () => {
    void loadDashboardEntry();
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
.block-card {
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
.block-header p {
  margin: 8px 0 0;
  color: #627d98;
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

.metric-list,
.risk-list {
  display: grid;
  gap: 10px;
}

.metric-row,
.risk-summary {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #f6f9fb;
  color: #243b53;
}

.risk-summary {
  flex-wrap: wrap;
}

.risk-alert {
  padding: 12px;
  border-radius: 12px;
  background: #fff6f4;
  border: 1px solid rgba(191, 90, 60, 0.12);
}

.risk-alert strong {
  color: #7c2d12;
}

.risk-alert p {
  margin: 6px 0 0;
  color: #9a3412;
}

.block-status {
  padding: 14px;
  border-radius: 12px;
  background: #f6f9fb;
  color: #52606d;
}

.block-status-error {
  background: #fff1f2;
  color: #b42318;
}

.block-status-warning {
  background: #fff7ed;
  color: #b45309;
}

.ghost-button {
  border: 1px solid rgba(16, 42, 67, 0.12);
  border-radius: 999px;
  background: white;
  color: #102a43;
  padding: 8px 14px;
  cursor: pointer;
}

@media (max-width: 720px) {
  .project-dashboard-page {
    padding: 12px;
  }

  .hero-card,
  .block-header {
    grid-template-columns: 1fr;
    display: grid;
  }
}
</style>
