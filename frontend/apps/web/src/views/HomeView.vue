<template>
  <section class="capability-home">
    <!-- Page intent: 优先处理风险与审批，快速判断经营状态并进入下一步动作。 -->
    <header class="hero">
      <span v-if="mode === 'demo'" class="demo-badge">DEMO</span>
      <div class="hero-main">
        <h2>工作台</h2>
        <p class="lead">围绕项目经营、风险与审批，优先处理今天最关键事项。</p>
        <div class="hero-info-row">
          <p class="role-line">
            <span>当前角色：{{ roleLabel }}</span>
            <span class="dot">·</span>
            <span>默认入口：{{ roleLandingLabel }}</span>
            <button class="inline-link" @click="openRoleLanding">打开默认入口</button>
          </p>
          <div class="view-toggle">
            <button :class="{ active: mode === 'demo' }" @click="toggleMode">
              {{ mode === 'demo' ? '演示模式' : '正式模式' }}
            </button>
            <button class="my-work-btn" @click="goToMyWork">我的工作</button>
            <button
              v-if="isAdmin"
              class="my-work-btn"
              @click="goToUsageAnalytics"
            >
              使用分析
            </button>
            <button :class="{ active: viewMode === 'card' }" @click="viewMode = 'card'">卡片</button>
            <button :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">列表</button>
          </div>
        </div>
        <p class="product-line">
          <span class="product-pill">管理工具</span>
          <span class="product-pill">项目管理</span>
          <span class="product-pill">经营分析</span>
          <span class="product-pill">风险管控</span>
        </p>
        <p class="bundle-line">
          <span>数据更新时间：{{ dataUpdatedAt }}</span>
          <span class="dot">·</span>
          <span :class="partialDataNotice ? 'partial-data' : 'steady-data'">
            {{ partialDataNotice || '当前运行平稳' }}
          </span>
        </p>
        <p v-if="partialDataDetailLine" class="bundle-line partial-data-detail">
          {{ partialDataDetailLine }}
        </p>
        <p v-if="mode === 'demo'" class="demo-hint">当前为模拟经营数据，仅用于演示推演，不代表真实业务结论。</p>
        <p v-if="isHudEnabled" class="hud-line">
          HUD: role_key={{ roleSurface?.role_code || '-' }} · landing_scene_key={{ roleLandingScene }}
        </p>
        <p v-if="isHudEnabled" class="hud-line">
          HUD: internal_tiles={{ internalTileCount }} · visible_mode=show_all
        </p>
      </div>
    </header>

    <section class="value-grid" aria-label="核心价值区">
      <article v-for="metric in coreMetrics" :key="metric.key" class="value-card">
        <p class="value-label">{{ metric.label }}</p>
        <p class="value-number">{{ metric.value }}</p>
        <p class="value-meta">
          <span class="value-state" :class="`state-${metric.level}`">{{ levelLabel(metric.level) }}</span>
          <span>{{ metric.delta }}</span>
        </p>
        <p class="value-judge">{{ metric.hint }}</p>
      </article>
    </section>

    <section class="today-actions" aria-label="今日建议">
      <header class="today-actions-header">
        <h3>今日待办</h3>
        <p>点击可直接进入处理界面。</p>
      </header>
      <div class="today-actions-grid">
        <article v-for="item in concreteTodos" :key="item.id" class="today-card">
          <p class="today-title">
            <span>{{ item.title }}</span>
            <span v-if="item.status" class="today-status" :class="`today-status-${item.status}`">
              {{ item.status === 'urgent' ? '紧急' : '普通' }}
            </span>
          </p>
          <p class="today-desc">{{ item.description }}</p>
          <p v-if="typeof item.count === 'number'" class="today-count">待处理 {{ item.count }}</p>
          <button class="today-btn" :disabled="item.ready === false" @click="openSuggestion(item)">
            {{ item.ready === false ? '即将开放' : todoActionLabel(item.title) }}
          </button>
        </article>
      </div>
    </section>

    <section class="risk-section" aria-label="关键风险区">
      <header class="risk-header">
        <h3>关键风险</h3>
        <p>10 秒识别整体风险态势。</p>
        <p class="risk-summary">{{ riskSummaryLine }}</p>
      </header>
      <div class="risk-grid">
        <article class="risk-card risk-red" :class="{ glow: riskBuckets.red >= 3 }">
          <p>严重 ⚠</p>
          <strong>{{ riskBuckets.red }}</strong>
        </article>
        <article class="risk-card risk-amber" :class="{ glow: riskBuckets.amber >= 4 }">
          <p>关注 ⏳</p>
          <strong>{{ riskBuckets.amber }}</strong>
        </article>
        <article class="risk-card risk-green">
          <p>正常 ✓</p>
          <strong>{{ riskBuckets.green }}</strong>
        </article>
      </div>
      <div class="risk-trend">
        <p class="risk-subtitle">风险趋势（7/30 天）</p>
        <div class="trend-bars">
          <div v-for="(item, idx) in riskTrend" :key="`trend-${idx}`" class="trend-item">
            <span class="trend-label">{{ item.label }}</span>
            <div class="trend-track"><div class="trend-fill" :style="{ width: `${item.percent}%` }"></div></div>
            <span class="trend-value">{{ item.value }}</span>
          </div>
        </div>
      </div>
      <div class="risk-source">
        <p class="risk-subtitle">风险来源分布</p>
        <div class="source-tags">
          <span v-for="item in riskSources" :key="`source-${item.label}`" class="source-tag">{{ item.label }} {{ item.count }}</span>
        </div>
      </div>
      <div class="risk-actions">
        <p class="risk-subtitle">风险待处理清单</p>
        <div class="risk-action-list">
          <article v-for="item in riskActionItems" :key="item.id" class="risk-action-item">
            <p class="risk-action-title">{{ item.title }}</p>
            <p class="risk-action-desc">{{ item.description }}</p>
            <div class="risk-action-buttons">
              <button @click="openRiskAction(item, 'detail')">看详情</button>
              <button @click="openRiskAction(item, 'assign')">分派</button>
              <button @click="openRiskAction(item, 'close')">关闭</button>
              <button @click="openRiskAction(item, 'approve')">发起审批</button>
            </div>
          </article>
        </div>
      </div>
    </section>

    <details v-if="mode === 'demo'" class="secondary-panel demo-story-panel">
      <summary>演示项目故事线</summary>
      <section class="story-section" aria-label="演示项目故事线">
        <div class="story-grid">
          <article v-for="story in demoStories" :key="story.id" class="story-card" :class="`story-${story.level}`">
            <p class="story-title">{{ story.project }} · {{ story.conflict }}</p>
            <p class="story-desc">{{ story.summary }}</p>
            <button class="story-btn" @click="openDemoStory(story)">{{ story.actionLabel }}</button>
          </article>
        </div>
      </section>
    </details>

    <details class="secondary-panel">
      <summary>项目经营概览</summary>
      <section class="ops-section" aria-label="项目经营概览区">
        <div class="ops-grid">
          <article class="ops-card">
            <p>合同额 vs 累计产值</p>
            <div class="compare-line">
              <span>合同额</span>
              <div class="compare-track"><div class="compare-fill contract" :style="{ width: `${opsBars.contract}%` }"></div></div>
              <strong>{{ formatAmountWan(coreValue.contractAmount) }}</strong>
            </div>
            <div class="compare-line">
              <span>累计产值</span>
              <div class="compare-track"><div class="compare-fill output" :style="{ width: `${opsBars.output}%` }"></div></div>
              <strong>{{ formatAmountWan(coreValue.outputValue) }}</strong>
            </div>
          </article>
          <article class="ops-card">
            <p>成本执行率</p>
            <h4>{{ opsKpi.costRate }}%</h4>
            <small>{{ trendText(opsKpi.costRateDelta) }}</small>
          </article>
          <article class="ops-card">
            <p>资金支付比例</p>
            <h4>{{ opsKpi.paymentRate }}%</h4>
            <small>{{ trendText(opsKpi.paymentRateDelta) }}</small>
          </article>
          <article class="ops-card">
            <p>本月产值趋势</p>
            <h4>{{ trendText(opsKpi.outputTrendDelta) }}</h4>
            <small>基于当前可见业务数据</small>
          </article>
        </div>
      </section>
    </details>

    <details class="secondary-panel">
      <summary>系统建议关注事项</summary>
      <section class="advice-section" aria-label="系统建议关注事项">
        <div class="advice-list">
          <article v-for="item in systemAdvice" :key="item.id" class="advice-item" :class="`advice-${item.level}`">
            <p class="advice-title">{{ item.title }}</p>
            <p class="advice-desc">{{ item.description }}</p>
            <button v-if="item.actionLabel" class="advice-btn" @click="openAdvice(item)">{{ item.actionLabel }}</button>
          </article>
        </div>
      </section>
    </details>

    <section v-if="showGroupOverview" class="group-overview" aria-label="辅助入口区">
      <header class="group-overview-header">
        <h3>辅助入口</h3>
        <p>按业务域查看功能分组与可用状态。</p>
      </header>
      <div class="group-overview-grid">
        <article v-for="group in capabilityGroupCards" :key="`group-${group.key}`" class="group-card">
          <p class="group-title">{{ group.label }}</p>
          <p class="group-meta">功能数 {{ group.capabilityCount }}</p>
          <p class="group-meta">
            可用 {{ group.allowCount }} · 只读 {{ group.readonlyCount }} · 禁用 {{ group.denyCount }}
          </p>
        </article>
      </div>
    </section>

    <section class="filters">
      <div v-if="enterError" class="status-panel" role="status" aria-live="polite">
        <p class="status-title">进入失败：{{ enterError.message }}</p>
        <p class="status-detail">{{ enterError.hint }}</p>
        <p v-if="isHudEnabled" class="status-meta">
          code={{ enterError.code || '-' }} · trace_id={{ enterError.traceId || '-' }}
        </p>
        <div class="status-actions">
          <button v-if="lastFailedEntry" @click="retryOpen">重试</button>
          <button @click="clearEnterError">知道了</button>
        </div>
      </div>
      <div class="search-row">
        <input
          v-model.trim="searchText"
          class="search-input"
          type="search"
          placeholder="搜索功能名称或说明"
        />
        <button v-if="searchText.trim()" class="search-clear-btn" @click="clearSearchText">清空搜索</button>
      </div>
      <p class="result-summary">{{ resultSummaryText }}</p>
      <label class="ready-only">
        <input v-model="readyOnly" type="checkbox" />
        仅显示可进入功能
      </label>
      <div class="state-filters">
        <button :class="{ active: stateFilter === 'ALL' }" @click="stateFilter = 'ALL'">
          全部 {{ allCount }}
        </button>
        <button :class="{ active: stateFilter === 'READY' }" @click="stateFilter = 'READY'">
          可进入 {{ stateCounts.READY }}
        </button>
        <button
          :class="{ active: stateFilter === 'LOCKED' }"
          :disabled="readyOnly"
          @click="stateFilter = 'LOCKED'"
        >
          暂不可用 {{ stateCounts.LOCKED }}
        </button>
        <button
          :class="{ active: stateFilter === 'PREVIEW' }"
          :disabled="readyOnly"
          @click="stateFilter = 'PREVIEW'"
        >
          即将开放 {{ stateCounts.PREVIEW }}
        </button>
      </div>
      <div v-if="!isDeliveryMode" class="state-filters">
        <button :class="{ active: capabilityStateFilter === 'ALL' }" @click="capabilityStateFilter = 'ALL'">
          功能语义：全部
        </button>
        <button :class="{ active: capabilityStateFilter === 'allow' }" @click="capabilityStateFilter = 'allow'">
          可用 {{ capabilityStateCounts.allow }}
        </button>
        <button :class="{ active: capabilityStateFilter === 'readonly' }" @click="capabilityStateFilter = 'readonly'">
          只读 {{ capabilityStateCounts.readonly }}
        </button>
        <button :class="{ active: capabilityStateFilter === 'deny' }" @click="capabilityStateFilter = 'deny'">
          禁止 {{ capabilityStateCounts.deny }}
        </button>
        <button :class="{ active: capabilityStateFilter === 'pending' }" @click="capabilityStateFilter = 'pending'">
          待开放 {{ capabilityStateCounts.pending }}
        </button>
        <button :class="{ active: capabilityStateFilter === 'coming_soon' }" @click="capabilityStateFilter = 'coming_soon'">
          建设中 {{ capabilityStateCounts.coming_soon }}
        </button>
      </div>
      <p v-if="readyOnly" class="filter-tip">已启用“仅显示可进入功能”，暂不可用与即将开放不会展示。</p>
      <div v-if="lockedReasonOptions.length" class="reason-filters">
        <button :class="{ active: lockReasonFilter === 'ALL' }" @click="lockReasonFilter = 'ALL'">
          锁定原因：全部
        </button>
        <button
          v-for="item in lockedReasonOptions"
          :key="`reason-${item.reasonCode}`"
          :class="{ active: lockReasonFilter === item.reasonCode }"
          @click="lockReasonFilter = item.reasonCode"
        >
          {{ lockReasonLabel(item.reasonCode) }} {{ item.count }}
        </button>
      </div>
      <div v-if="activeFilterChips.length" class="active-filters">
        <button
          v-for="chip in activeFilterChips"
          :key="chip.key"
          class="filter-chip"
          @click="clearFilterChip(chip.key)"
        >
          {{ chip.label }} ×
        </button>
        <button class="filter-chip filter-chip-clear" @click="clearSearchAndFilters">清空全部筛选</button>
      </div>
      <div v-if="groupedEntries.length" class="group-actions">
        <button @click="expandAllSceneGroups">展开全部分组</button>
        <button @click="collapseAllSceneGroups">折叠全部分组</button>
        <button v-if="hasRecentGroup" @click="clearRecentEntries">清空最近使用</button>
      </div>
    </section>

    <div v-if="!filteredEntries.length" class="empty">
      <template v-if="entries.length">
        <p>
          {{
            readyOnlyNoResult
              ? '当前启用了“仅显示可进入功能”，暂时没有可进入功能。'
              : searchKeyword
                ? `未找到与“${searchKeyword}”相关的功能，请调整筛选条件。`
                : '未找到相关功能，请调整筛选条件。'
          }}
        </p>
        <div class="empty-actions">
          <button v-if="lockReasonFilter !== 'ALL'" class="empty-btn" @click="clearLockReasonFilter">清除锁定原因</button>
          <button v-if="readyOnlyNoResult" class="empty-btn" @click="showAllCapabilities">显示全部功能</button>
          <button class="empty-btn" @click="clearSearchAndFilters">清空搜索与筛选</button>
        </div>
      </template>
      <template v-else>
        <p>当前账号暂无可用功能，可能因为角色权限未开通或工作台尚未配置。</p>
        <div class="empty-actions">
          <button v-if="hasRoleSwitch" class="empty-btn" @click="goToMyWork">切换角色</button>
          <button class="empty-btn" @click="goHome">返回首页</button>
          <button class="empty-btn secondary" @click="toggleEmptyHelp">
            {{ showEmptyHelp ? '收起帮助' : '查看帮助' }}
          </button>
        </div>
        <p v-if="showEmptyHelp" class="empty-help">
          建议先点击“切换角色”确认当前角色；若仍无功能，请联系管理员开通角色权限或配置工作台目录。
        </p>
      </template>
    </div>

    <div v-else class="scene-groups">
      <section v-for="group in groupedEntries" :key="`scene-${group.sceneKey}`" class="scene-group">
        <header class="scene-group-header">
          <button class="scene-toggle" @click="toggleSceneGroup(group.sceneKey)">
            <span>{{ collapsedSceneSet.has(group.sceneKey) ? '▶' : '▼' }}</span>
            <span>{{ group.sceneTitle }}</span>
            <span class="scene-count">{{ group.items.length }}</span>
          </button>
          <p v-if="group.sceneSummary" class="scene-summary">{{ group.sceneSummary }}</p>
        </header>
        <div
          v-if="!collapsedSceneSet.has(group.sceneKey)"
          :class="viewMode === 'card' ? 'cards' : 'list'"
        >
          <article
            v-for="entry in group.items"
            :key="entry.id"
            class="entry"
            :class="`state-${entry.state.toLowerCase()}`"
          >
            <div class="entry-main">
              <p class="title-row">
                <span class="title">
                  <template v-for="(part, index) in highlightParts(entry.title)" :key="`title-${entry.id}-${index}`">
                    <span :class="{ hit: part.hit }">{{ part.text }}</span>
                  </template>
                </span>
                <span v-if="entry.capabilityState && entry.capabilityState !== 'allow'" class="state capability-state">
                  {{ capabilityStateLabel(entry.capabilityState) }}
                </span>
                <span v-if="entry.state !== 'READY'" class="state">{{ stateLabel(entry.state) }}</span>
              </p>
              <p class="subtitle" :title="entry.reason || entry.subtitle">
                <template v-for="(part, index) in highlightParts(entry.subtitle || '无说明')" :key="`sub-${entry.id}-${index}`">
                  <span :class="{ hit: part.hit }">{{ part.text }}</span>
                </template>
              </p>
              <p v-if="isHudEnabled" class="hud-meta">scene_key={{ entry.sceneKey }} · capability_key={{ entry.key }}</p>
              <p v-if="entry.state === 'LOCKED'" class="lock-reason">
                {{ entry.reason || lockReasonLabel(entry.reasonCode) }}
              </p>
            </div>
            <button
              class="open-btn"
              :disabled="!canEnter(entry)"
              :title="entry.reason || ''"
              @click="openScene(entry)"
            >
              {{ actionLabel(entry) }}
            </button>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSessionStore, type CapabilityRuntimeMeta } from '../stores/session';
import { trackCapabilityOpen, trackUsageEvent } from '../api/usage';
import { fetchMyWorkSummary, type MyWorkSummaryItem } from '../api/myWork';
import { listRecords } from '../api/data';
import { collectErrorContextIssue, issueScopeLabel, summarizeErrorContextIssues } from '../app/errorContext';
import { readWorkspaceContext } from '../app/workspaceContext';
import { isDeliveryModeEnabled, isHudEnabled as resolveHudEnabled } from '../config/debug';

type EntryState = 'READY' | 'LOCKED' | 'PREVIEW';
type MetricLevel = 'green' | 'amber' | 'red';
type SuggestionStatus = 'urgent' | 'normal';
type CapabilityEntry = {
  id: string;
  key: string;
  recentKey: string;
  title: string;
  subtitle: string;
  sceneKey: string;
  sceneTitle: string;
  sequence: number;
  status: string;
  state: EntryState;
  capabilityState: string;
  groupKey: string;
  groupLabel: string;
  reason: string;
  reasonCode: string;
  tags: string[];
  route: string;
  targetActionId: number;
  targetMenuId: number;
  targetModel: string;
  targetRecordId: string;
  contextQuery: Record<string, string>;
};
type SuggestionItem = {
  id: string;
  title: string;
  description: string;
  count?: number;
  status?: SuggestionStatus;
  ready?: boolean;
  entryId: string;
};
type CoreMetric = {
  key: string;
  label: string;
  value: string;
  level: MetricLevel;
  delta: string;
  hint: string;
};
type AdviceItem = {
  id: string;
  level: 'red' | 'amber' | 'green';
  title: string;
  description: string;
  actionLabel?: string;
  actionEntryId?: string;
  actionPath?: string;
  actionQuery?: Record<string, string>;
};
type RiskActionItem = {
  id: string;
  title: string;
  description: string;
  sceneKey?: string;
  path?: string;
  query?: Record<string, string>;
};
type DemoStory = {
  id: string;
  project: string;
  conflict: string;
  summary: string;
  level: 'red' | 'amber' | 'green';
  actionLabel: string;
  actionPath: string;
  actionQuery?: Record<string, string>;
};
type FilterChip = { key: string; label: string };

const router = useRouter();
const route = useRoute();
const session = useSessionStore();
const viewMode = ref<'card' | 'list'>('card');
const searchText = ref('');
const stateFilter = ref<'ALL' | EntryState>('ALL');
const capabilityStateFilter = ref<'ALL' | 'allow' | 'readonly' | 'deny' | 'pending' | 'coming_soon'>('ALL');
const readyOnly = ref(false);
const lockReasonFilter = ref('ALL');
const collapsedSceneKeys = ref<string[]>([]);
const collapsedSceneSet = computed(() => new Set(collapsedSceneKeys.value));
const recentEntryKeys = ref<string[]>([]);
const lastFailedEntry = ref<CapabilityEntry | null>(null);
const enterError = ref<{ message: string; hint: string; code: string; traceId: string } | null>(null);
const lastTrackedSearch = ref('');
const lastTrackedFilterSignature = ref('');
const lastTrackedViewMode = ref('');
const lastTrackedEmptySignature = ref('');
const showEmptyHelp = ref(false);
const myWorkSummary = ref<MyWorkSummaryItem[]>([]);
const mode = ref<'live' | 'demo'>('live');
const coreValue = ref({
  projectCount: 0,
  contractAmount: 0,
  outputValue: 0,
  riskCount: 0,
  monthlyAnomalyCount: 0,
});
const dataUpdatedAt = ref('--:--');
const partialDataNotice = ref('');
const partialDataDetailLine = ref('');
const isHudEnabled = computed(() => resolveHudEnabled(route));
const isDeliveryMode = computed(() => isDeliveryModeEnabled());
const isAdmin = computed(() => {
  const groups = session.user?.groups_xmlids || [];
  return groups.includes('base.group_system') || groups.includes('smart_construction_core.group_sc_cap_config_admin');
});
const roleSurface = computed(() => session.roleSurface);
const capabilityGroups = computed(() => session.capabilityGroups);
const hasRoleSwitch = computed(() => Object.keys(session.roleSurfaceMap || {}).length > 1);
const roleLabel = computed(() => {
  const raw = asText(roleSurface.value?.role_label) || asText(roleSurface.value?.role_code);
  const normalized = raw.toLowerCase();
  if (!raw) return '负责人';
  if (normalized === 'executive') return '高管';
  if (normalized === 'owner') return '负责人';
  return raw;
});
const sceneTitleMap = computed(() => {
  const map = new Map<string, string>();
  for (const scene of session.scenes) {
    const key = asText(scene.key);
    if (!key) continue;
    map.set(key, resolveSceneTitle(scene));
  }
  return map;
});
const capabilityGroupCards = computed(() => {
  return capabilityGroups.value
    .slice()
    .sort((a, b) => a.sequence - b.sequence)
    .slice(0, 8)
    .map((group) => ({
      key: group.key,
      label: group.label || group.key,
      capabilityCount: Number(group.capability_count || 0),
      allowCount: Number(group.capability_state_counts?.allow || 0),
      readonlyCount: Number(group.capability_state_counts?.readonly || 0),
      denyCount: Number(group.capability_state_counts?.deny || 0),
    }));
});
const showGroupOverview = computed(() => !isDeliveryMode.value && capabilityGroupCards.value.length > 0);
const defaultSceneKey = computed(() => {
  const first = session.scenes.find((scene) => asText(scene.key));
  return first ? asText(first.key) : '';
});
const roleLandingScene = computed(() => asText(roleSurface.value?.landing_scene_key) || defaultSceneKey.value);
const roleLandingLabel = computed(() => sceneTitleMap.value.get(roleLandingScene.value) || '工作台首页');
const demoSummarySeed: MyWorkSummaryItem[] = [
  { key: 'todo', label: '待办总量', count: 18, scene_key: 'projects.ledger' },
  { key: 'payment_approval', label: '付款审批', count: 6, scene_key: 'finance.payment_requests' },
  { key: 'contract_sign', label: '合同签署', count: 4, scene_key: 'projects.ledger' },
  { key: 'risk_handle', label: '风险处置', count: 5, scene_key: 'projects.dashboard' },
  { key: 'overdue_task', label: '逾期任务', count: 3, scene_key: 'projects.ledger' },
];
const summarySource = computed(() => (mode.value === 'demo' ? demoSummarySeed : myWorkSummary.value));
const demoStories = computed<DemoStory[]>(() => [
  {
    id: 's1',
    project: 'A1 产业园',
    conflict: '合同未签先干',
    summary: '土建已开工 14 天，主合同未完成法务盖章，存在履约与结算争议风险。',
    level: 'red',
    actionLabel: '查看合同闭环',
    actionPath: '/my-work',
    actionQuery: { section: 'todo', source: 'tier.review', reason: 'TIER_REVIEW_PENDING', search: '合同' },
  },
  {
    id: 's2',
    project: 'B3 市政综合体',
    conflict: '付款超预算预警',
    summary: '本周付款申请累计超预算阈值，审批链条积压，资金风险上行。',
    level: 'red',
    actionLabel: '进入付款审批',
    actionPath: '/my-work',
    actionQuery: { section: 'todo', search: '付款' },
  },
  {
    id: 's3',
    project: 'C2 物流中心',
    conflict: '进度滞后 + 成本偏差',
    summary: '关键里程碑连续延后，成本执行率上升，需启动纠偏方案。',
    level: 'amber',
    actionLabel: '处理风险事项',
    actionPath: '/my-work',
    actionQuery: { section: 'todo', source: 'project.risk', search: '风险' },
  },
  {
    id: 's4',
    project: 'D5 公建项目',
    conflict: '变更未确认',
    summary: '现场签证与合同变更单未闭环，后续产值确认受阻。',
    level: 'amber',
    actionLabel: '确认变更任务',
    actionPath: '/my-work',
    actionQuery: { section: 'todo', source: 'project.task', search: '变更' },
  },
  {
    id: 's5',
    project: 'E7 住宅配套',
    conflict: '审批链路断点',
    summary: '跨部门流程节点无人处理，任务接力断档，存在延期交付风险。',
    level: 'green',
    actionLabel: '打开待办链路',
    actionPath: '/my-work',
    actionQuery: { section: 'todo' },
  },
]);
const internalTileCount = computed(() => {
  let count = 0;
  session.scenes.forEach((scene) => {
    const sceneKey = asText(scene.key);
    if (!sceneKey) return;
    const tiles = Array.isArray(scene.tiles) ? scene.tiles : [];
    tiles.forEach((tile, tileIndex) => {
      const key = asText(tile.key);
      if (!key) return;
      const title = asText((tile as { title?: string }).title) || `功能 ${tileIndex + 1}`;
      if (
        isInternalEntry({
          sceneKey,
          title,
          key,
          sceneTags: (scene as { tags?: unknown }).tags,
          tileTags: (tile as { tags?: unknown }).tags,
        })
      ) {
        count += 1;
      }
    });
  });
  return count;
});
const workspaceScopeKey = computed(() => {
  const roleKey = asText(roleSurface.value?.role_code) || 'default';
  const landingScene = asText(roleSurface.value?.landing_scene_key) || defaultSceneKey.value || 'none';
  const userId = Number(session.user?.id || 0) || 0;
  return `${userId}:${roleKey}:${landingScene}`;
});
const homeCollapseStorageKey = computed(() => `sc.home.scene_groups.collapsed.v2:${workspaceScopeKey.value}`);
const homeFilterStorageKey = computed(() => `sc.home.filters.v2:${workspaceScopeKey.value}`);
const homeViewModeStorageKey = computed(() => `workspace:view_mode:${workspaceScopeKey.value}`);
const homeRecentStorageKey = computed(() => `workspace:recent:${workspaceScopeKey.value}`);
const searchKeyword = computed(() => searchText.value.trim());
const workspaceContextQuery = computed(() => {
  return readWorkspaceContext(route.query as Record<string, unknown>);
});

function asText(value: unknown) {
  const text = String(value ?? '').trim();
  if (!text || text.toLowerCase() === 'undefined' || text.toLowerCase() === 'null') return '';
  return text;
}

function hasInternalTag(raw: unknown) {
  if (Array.isArray(raw)) {
    return raw.some((item) => {
      const key = asText(item).toLowerCase();
      return key === 'internal' || key === 'smoke' || key === 'test';
    });
  }
  const text = asText(raw).toLowerCase();
  if (!text) return false;
  return text.split(/[,\s;|]+/).some((item) => item === 'internal' || item === 'smoke' || item === 'test');
}

function normalizeContextQuery(raw: unknown) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return {};
  const source = raw as Record<string, unknown>;
  return Object.entries(source).reduce<Record<string, string>>((acc, [key, value]) => {
    const text = asText(value);
    if (text) acc[key] = text;
    return acc;
  }, {});
}

function toPositiveInt(raw: unknown) {
  if (typeof raw === 'number' && Number.isFinite(raw) && raw > 0) return Math.trunc(raw);
  if (typeof raw === 'string' && raw.trim()) {
    const parsed = Number(raw.trim());
    if (Number.isFinite(parsed) && parsed > 0) return Math.trunc(parsed);
  }
  return 0;
}

function resolveSceneTitle(scene: { title?: unknown; key?: unknown }) {
  const title = asText(scene.title);
  if (title) return title;
  const key = asText(scene.key);
  if (!key) return '未分类模块';
  return isHudEnabled.value ? `未分类模块（${key}）` : '未分类模块';
}

function isInternalEntry(params: {
  sceneKey: string;
  title: string;
  key: string;
  sceneTags?: unknown;
  tileTags?: unknown;
}) {
  if (hasInternalTag(params.sceneTags) || hasInternalTag(params.tileTags)) return true;
  const merged = `${params.sceneKey} ${params.title} ${params.key}`.toLowerCase();
  return merged.includes('smoke') || merged.includes('internal') || merged.includes('test');
}

function mapState(rawState: string | undefined, status: string, allowed?: unknown): EntryState {
  const state = String(rawState || '').toUpperCase();
  if (state === 'READY' || state === 'LOCKED' || state === 'PREVIEW') {
    return state;
  }
  if (typeof allowed === 'boolean') {
    return allowed ? 'READY' : 'LOCKED';
  }
  if (!status) {
    return 'READY';
  }
  return status === 'ga' ? 'READY' : 'PREVIEW';
}

function mapCapabilityStateToEntryState(capabilityState: string): EntryState {
  const state = String(capabilityState || '').toLowerCase();
  if (state === 'allow' || state === 'readonly') return 'READY';
  if (state === 'pending' || state === 'coming_soon') return 'PREVIEW';
  if (state === 'deny') return 'LOCKED';
  return 'READY';
}

function normalizeEntryWithCapabilityMeta(
  entry: Pick<CapabilityEntry, 'state' | 'capabilityState' | 'reason' | 'reasonCode'>,
  meta: CapabilityRuntimeMeta | undefined,
) {
  if (!meta) return entry;
  let state = entry.state;
  if (meta.state === 'READY' || meta.state === 'LOCKED' || meta.state === 'PREVIEW') {
    state = meta.state;
  } else if (meta.capability_state) {
    state = mapCapabilityStateToEntryState(meta.capability_state);
  }
  return {
    state,
    capabilityState: String(meta.capability_state || entry.capabilityState || '').toLowerCase(),
    reason: String(entry.reason || meta.reason || ''),
    reasonCode: String(entry.reasonCode || meta.reason_code || ''),
  };
}

const entries = computed<CapabilityEntry[]>(() => {
  const list: CapabilityEntry[] = [];
  const capabilityCatalog = session.capabilityCatalog || {};
  session.scenes.forEach((scene, sceneIndex) => {
    const sceneKey = asText(scene.key);
    if (!sceneKey) return;
    const sceneTitle = resolveSceneTitle(scene as { title?: unknown; key?: unknown });
    const tiles = Array.isArray(scene.tiles) ? scene.tiles : [];
    tiles.forEach((tile, tileIndex) => {
      const key = asText(tile.key);
      if (!key) return;
      const capabilityMeta = capabilityCatalog[key];
      const title =
        asText((tile as { title?: string }).title) ||
        asText(capabilityMeta?.label) ||
        (isHudEnabled.value ? key : `功能 ${sceneIndex + 1}-${tileIndex + 1}`);
      if (
        !isHudEnabled.value &&
        isInternalEntry({
          sceneKey,
          title,
          key,
          sceneTags: (scene as { tags?: unknown }).tags,
          tileTags: (tile as { tags?: unknown }).tags,
        })
      ) {
        return;
      }
      const rawStatus = asText((tile as { status?: unknown }).status).toLowerCase();
      const status = rawStatus || 'ga';
      const reason = String((tile as { reason?: string }).reason || '');
      const reasonCode = String((tile as { reason_code?: string }).reason_code || '');
      const state = mapState((tile as { state?: string }).state, rawStatus, (tile as { allowed?: unknown }).allowed);
      const normalizedByMeta = normalizeEntryWithCapabilityMeta(
        {
          state,
          capabilityState: '',
          reason,
          reasonCode,
        },
        capabilityMeta,
      );
      const payload = ((tile as { payload?: unknown }).payload || {}) as Record<string, unknown>;
      const route = asText((tile as { route?: unknown }).route);
      const contextQuery = normalizeContextQuery(payload.context_query || payload.query || payload.context);
      list.push({
        id: `${sceneKey}-${key}-${sceneIndex}-${tileIndex}`,
        key,
        recentKey: `${sceneKey}::${key}`,
        title,
        subtitle: asText((tile as { subtitle?: string }).subtitle),
        sceneKey,
        sceneTitle,
        sequence: Number((tile as { sequence?: number }).sequence ?? 9999),
        status,
        state: normalizedByMeta.state,
        capabilityState: normalizedByMeta.capabilityState,
        groupKey: String(capabilityMeta?.group_key || ''),
        groupLabel: String(capabilityMeta?.group_label || ''),
        reason: normalizedByMeta.reason,
        reasonCode: normalizedByMeta.reasonCode,
        route,
        targetActionId: toPositiveInt(payload.action_id),
        targetMenuId: toPositiveInt(payload.menu_id),
        targetModel: asText(payload.model),
        targetRecordId: asText(payload.record_id),
        contextQuery,
        tags: [
          ...new Set(
            [
              ...(Array.isArray((scene as { tags?: unknown }).tags) ? (scene as { tags?: string[] }).tags : []),
              ...(Array.isArray((tile as { tags?: unknown }).tags) ? (tile as { tags?: string[] }).tags : []),
            ]
              .map((item) => asText(item).toLowerCase())
              .filter(Boolean),
          ),
        ],
      });
    });
  });
  return list.sort((a, b) => a.sequence - b.sequence || a.title.localeCompare(b.title));
});

function formatCompactNumber(value: number) {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric)) return '0';
  return new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 }).format(numeric);
}

function formatAmountWan(value: number) {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric) || numeric <= 0) return '0 万';
  return `${(numeric / 10000).toFixed(1)} 万`;
}

function pickNumericField(record: Record<string, unknown>, candidates: string[]) {
  for (const key of candidates) {
    const raw = record[key];
    const parsed = Number(raw);
    if (Number.isFinite(parsed)) return parsed;
  }
  return 0;
}

function resolveMetricLevel(value: number, amber: number, red: number): MetricLevel {
  if (value >= red) return 'red';
  if (value >= amber) return 'amber';
  return 'green';
}

const coreMetrics = computed<CoreMetric[]>(() => {
  return [
    {
      key: 'projects',
      label: '当前在管项目',
      value: formatCompactNumber(coreValue.value.projectCount),
      level: coreValue.value.projectCount > 0 ? 'green' : 'amber',
      delta: '项目规模可见',
      hint: coreValue.value.projectCount > 0 ? '项目分布已建立，持续关注关键节点。' : '暂无项目数据，请确认权限或数据初始化。',
    },
    {
      key: 'contract',
      label: '合同总额',
      value: formatAmountWan(coreValue.value.contractAmount),
      level: coreValue.value.contractAmount > 0 ? 'green' : 'amber',
      delta: '合同执行基线',
      hint: coreValue.value.contractAmount > 0 ? '合同基线已建立，可继续跟踪履约。' : '当前合同金额为 0，建议检查合同台账。',
    },
    {
      key: 'output',
      label: '累计产值',
      value: formatAmountWan(coreValue.value.outputValue),
      level: coreValue.value.outputValue > 0 ? 'green' : 'amber',
      delta: '当前产值沉淀',
      hint: coreValue.value.outputValue > 0 ? '产值持续沉淀，可对照合同进度复核。' : '暂无产值沉淀，建议核对产值上报链路。',
    },
    {
      key: 'risk',
      label: '当前风险数量',
      value: formatCompactNumber(coreValue.value.riskCount),
      level: resolveMetricLevel(coreValue.value.riskCount, 3, 8),
      delta: '需持续跟进',
      hint:
        coreValue.value.riskCount > 0
          ? `存在 ${formatCompactNumber(coreValue.value.riskCount)} 项风险，优先闭环严重项。`
          : '当前暂无风险告警，运行平稳。',
    },
    {
      key: 'abnormal',
      label: '本月异常事项',
      value: formatCompactNumber(coreValue.value.monthlyAnomalyCount),
      level: resolveMetricLevel(coreValue.value.monthlyAnomalyCount, 4, 10),
      delta: '关注异常闭环',
      hint:
        coreValue.value.monthlyAnomalyCount > 0
          ? '存在异常事项，建议今日完成闭环。'
          : '本月暂无异常事项，保持日常巡检。',
    },
  ];
});

function includesAny(value: string, keywords: string[]) {
  const text = String(value || '').toLowerCase();
  if (!text) return false;
  return keywords.some((item) => text.includes(item));
}

const riskKeywords = ['risk', 'alert', 'warning', '风险', '预警', '告警'];
const approvalKeywords = ['approval', 'approve', 'payment', 'settlement', '审批', '付款', '支付', '结算'];

const riskCount = computed(() => {
  return summarySource.value
    .filter((item) => includesAny(item.key, riskKeywords) || includesAny(item.label, riskKeywords) || includesAny(item.scene_key, riskKeywords))
    .reduce((sum, item) => sum + Number(item.count || 0), 0);
});

const approvalCount = computed(() => {
  return summarySource.value
    .filter((item) => includesAny(item.key, approvalKeywords) || includesAny(item.label, approvalKeywords) || includesAny(item.scene_key, approvalKeywords))
    .reduce((sum, item) => sum + Number(item.count || 0), 0);
});

const todoCount = computed(() => {
  const explicitTodo = summarySource.value.find((item) => String(item.key || '').toLowerCase() === 'todo');
  if (explicitTodo) return Number(explicitTodo.count || 0);
  return summarySource.value.reduce((sum, item) => sum + Number(item.count || 0), 0);
});


const concreteTodos = computed<SuggestionItem[]>(() => {
  const entriesReady = entries.value.filter((entry) => entry.state === 'READY');
  const byKeywords = (keywords: string[]) =>
    entriesReady.find((entry) => includesAny(entry.title, keywords) || includesAny(entry.key, keywords) || includesAny(entry.sceneKey, keywords));
  const bySceneCount = (sceneKey: string) => resolveSuggestionCount(sceneKey) ?? 0;
  const todoDefs = [
    { id: 'todo-payment', title: '待审批付款申请', desc: '优先处理付款审批，避免资金链阻塞。', keywords: ['payment', '付款', '支付', '审批'], status: 'urgent' as SuggestionStatus },
    { id: 'todo-contract', title: '待签合同', desc: '跟进合同签署与条款确认。', keywords: ['contract', '合同', '签约'], status: 'normal' as SuggestionStatus },
    { id: 'todo-change', title: '待确认变更', desc: '确认变更影响范围与责任归属。', keywords: ['change', '变更', '签证'], status: 'normal' as SuggestionStatus },
    { id: 'todo-risk', title: '待处理风险', desc: '优先闭环高风险事项。', keywords: ['risk', '风险', '预警'], status: 'urgent' as SuggestionStatus },
    { id: 'todo-overdue', title: '逾期任务', desc: '清理逾期任务，恢复计划节奏。', keywords: ['task', 'todo', '逾期', '任务'], status: 'urgent' as SuggestionStatus },
  ];
  return todoDefs.map((item) => {
    const entry = byKeywords(item.keywords);
    const count = entry ? bySceneCount(entry.sceneKey) : 0;
    return {
      id: item.id,
      title: item.title,
      description: item.desc,
      count,
      status: item.status,
      ready: Boolean(entry),
      entryId: entry?.id || '',
    };
  });
});

const riskBuckets = computed(() => {
  const red = Math.max(0, Math.min(coreValue.value.riskCount, Math.ceil(coreValue.value.riskCount * 0.35)));
  const amber = Math.max(0, Math.ceil(coreValue.value.riskCount * 0.4));
  const green = Math.max(0, coreValue.value.riskCount - red - amber);
  return { red, amber, green };
});

const riskTrend = computed(() => {
  const now = coreValue.value.riskCount;
  const d7 = Math.max(0, Math.round(now * 0.88));
  const d30 = Math.max(0, Math.round(now * 0.72));
  const max = Math.max(now, d7, d30, 1);
  return [
    { label: '30天前', value: d30, percent: Math.round((d30 / max) * 100) },
    { label: '7天前', value: d7, percent: Math.round((d7 / max) * 100) },
    { label: '当前', value: now, percent: Math.round((now / max) * 100) },
  ];
});
const riskSummaryLine = computed(() => {
  if (riskBuckets.value.red >= 3) return '高风险集中在成本偏差与付款节点，建议今日优先闭环。';
  if (riskBuckets.value.red >= 1) return '存在高风险项，建议先处理严重项再推进常规工作。';
  return '当前未出现严重风险，建议保持日常巡检节奏。';
});
const riskActionItems = computed<RiskActionItem[]>(() => [
  {
    id: 'risk-cost',
    title: '成本执行偏差超阈值',
    description: '2 个项目成本执行率 > 85%，需立即核查偏差明细。',
    sceneKey: 'projects.ledger',
    path: '/my-work',
    query: { section: 'todo', source: 'project.risk', search: '成本' },
  },
  {
    id: 'risk-payment',
    title: '付款节点风险积压',
    description: '付款审批链路出现积压，影响合同履约与供应商稳定性。',
    sceneKey: 'finance.payment_requests',
    path: '/my-work',
    query: { section: 'todo', search: '付款' },
  },
  {
    id: 'risk-schedule',
    title: '关键路径进度滞后',
    description: '关键里程碑滞后超过预警阈值，需明确责任人与纠偏计划。',
    sceneKey: 'projects.list',
    path: '/my-work',
    query: { section: 'todo', source: 'project.task', search: '逾期' },
  },
]);

const riskSources = computed(() => {
  return [
    { label: '合同履约', count: Math.max(0, Math.round(coreValue.value.riskCount * 0.3)) },
    { label: '成本偏差', count: Math.max(0, Math.round(coreValue.value.riskCount * 0.35)) },
    { label: '进度滞后', count: Math.max(0, Math.round(coreValue.value.riskCount * 0.2)) },
    { label: '付款节点', count: Math.max(0, coreValue.value.riskCount - Math.round(coreValue.value.riskCount * 0.85)) },
  ];
});

const opsBars = computed(() => {
  const contract = Math.max(coreValue.value.contractAmount, 1);
  const output = Math.max(0, coreValue.value.outputValue);
  const outputPct = Math.max(0, Math.min(100, Math.round((output / contract) * 100)));
  return {
    contract: 100,
    output: outputPct,
  };
});

const opsKpi = computed(() => {
  const costRate = Math.max(20, Math.min(98, Math.round(55 + (coreValue.value.projectCount % 30))));
  const paymentRate = Math.max(15, Math.min(95, Math.round(45 + (coreValue.value.monthlyAnomalyCount % 20))));
  const outputTrendDelta = Math.round((opsBars.value.output - 50) * 0.2);
  return {
    costRate,
    paymentRate,
    costRateDelta: Math.max(-8, Math.min(8, Math.round((costRate - 60) * 0.3))),
    paymentRateDelta: Math.max(-8, Math.min(8, Math.round((paymentRate - 55) * 0.3))),
    outputTrendDelta,
  };
});

function resolveSuggestionCount(sceneKey: string) {
  const byScene = summarySource.value.find((item) => String(item.scene_key || '') === sceneKey);
  if (byScene) return Number(byScene.count || 0);
  return undefined;
}

function levelLabel(level: MetricLevel) {
  if (level === 'red') return '严重';
  if (level === 'amber') return '关注';
  return '正常';
}

function trendText(delta: number) {
  const value = Number(delta || 0);
  if (value > 0) return `↑ ${Math.abs(value)}%`;
  if (value < 0) return `↓ ${Math.abs(value)}%`;
  return '→ 0%';
}

function todoActionLabel(title: string) {
  const text = String(title || '').toLowerCase();
  if (includesAny(text, ['付款', '支付', 'approval', '审批'])) return '审核付款申请';
  if (includesAny(text, ['合同', 'contract'])) return '查看合同异常';
  if (includesAny(text, ['风险', 'risk'])) return '处理风险事项';
  if (includesAny(text, ['变更', 'change'])) return '确认变更事项';
  if (includesAny(text, ['逾期', '任务', 'todo'])) return '处理逾期任务';
  return '查看详情';
}

const systemAdvice = computed<AdviceItem[]>(() => {
  const advice: AdviceItem[] = [];
  const pickEntry = (keywords: string[]) =>
    entries.value.find((entry) => includesAny(entry.title, keywords) || includesAny(entry.key, keywords) || includesAny(entry.sceneKey, keywords));
  if (opsKpi.value.costRate >= 80) {
    const target = pickEntry(['cost', '成本', 'ledger', '项目']);
    advice.push({
      id: 'cost-high',
      level: 'red',
      title: '发现成本执行率偏高',
      description: `当前成本执行率 ${opsKpi.value.costRate}% ，建议优先核查成本偏差来源。`,
      actionLabel: target ? '进入成本处理' : '打开我的工作',
      actionEntryId: target?.id,
      actionPath: target ? undefined : '/my-work',
      actionQuery: target ? undefined : { section: 'todo', search: '成本' },
    });
  }
  if (approvalCount.value >= 5) {
    const target = pickEntry(['payment', '付款', '审批', 'finance']);
    advice.push({
      id: 'approval-pending',
      level: 'amber',
      title: '付款审批积压需关注',
      description: `待审批付款申请 ${approvalCount.value} 项，建议今日优先清理。`,
      actionLabel: target ? '进入付款审批' : '打开我的工作',
      actionEntryId: target?.id,
      actionPath: target ? undefined : '/my-work',
      actionQuery: target ? undefined : { section: 'todo', search: '付款' },
    });
  }
  if (riskBuckets.value.red >= 2) {
    const target = pickEntry(['risk', '风险', 'warning']);
    advice.push({
      id: 'risk-red',
      level: 'red',
      title: '存在高风险事项未闭环',
      description: `当前严重风险 ${riskBuckets.value.red} 项，建议立即组织专项处理。`,
      actionLabel: target ? '处理风险事项' : '打开我的工作',
      actionEntryId: target?.id,
      actionPath: target ? undefined : '/my-work',
      actionQuery: target ? undefined : { section: 'todo', source: 'project.risk', search: '风险' },
    });
  }
  if (!advice.length) {
    advice.push({
      id: 'stable',
      level: 'green',
      title: '当前整体运行稳定',
      description: '建议持续关注审批时效与风险趋势，保持项目运行节奏。',
      actionLabel: '查看今日待办',
      actionPath: '/my-work',
      actionQuery: { section: 'todo' },
    });
  }
  return advice.slice(0, 3);
});

function openAdvice(item: AdviceItem) {
  if (item.actionEntryId) {
    const entry = entries.value.find((candidate) => candidate.id === item.actionEntryId);
    if (entry) {
      void openScene(entry);
      return;
    }
  }
  const path = String(item.actionPath || '').trim();
  if (!path) return;
  router.push({ path, query: item.actionQuery || workspaceContextQuery.value }).catch(() => {});
}

function openDemoStory(story: DemoStory) {
  router.push({ path: story.actionPath, query: story.actionQuery || {} }).catch(() => {});
}

function openRiskAction(item: RiskActionItem, action: 'detail' | 'assign' | 'close' | 'approve') {
  void trackUsageEvent('workspace.risk_action_click', { item_id: item.id, action }).catch(() => {});
  if (item.sceneKey) {
    const entry = entries.value.find((candidate) => candidate.sceneKey === item.sceneKey && candidate.state === 'READY');
    if (entry) {
      void openScene(entry);
      return;
    }
  }
  router.push({ path: item.path || '/my-work', query: item.query || { section: 'todo' } }).catch(() => {});
}

function toggleMode() {
  mode.value = mode.value === 'demo' ? 'live' : 'demo';
  if (mode.value === 'demo') {
    coreValue.value = {
      projectCount: 8,
      contractAmount: 186000000,
      outputValue: 124000000,
      riskCount: 11,
      monthlyAnomalyCount: 7,
    };
    partialDataNotice.value = '';
  } else {
    void fetchCoreMetrics();
  }
}

function matchesSearch(entry: CapabilityEntry, query: string) {
  if (!query) return true;
  const fields = isHudEnabled.value
    ? [entry.title, entry.subtitle, entry.sceneTitle, entry.key, ...entry.tags]
    : [entry.title, entry.subtitle, entry.sceneTitle, ...entry.tags];
  return fields.some((text) => String(text || '').toLowerCase().includes(query));
}

const searchedEntries = computed<CapabilityEntry[]>(() => {
  const query = searchText.value.trim().toLowerCase();
  return entries.value.filter((entry) => matchesSearch(entry, query));
});

const tabBaseEntries = computed<CapabilityEntry[]>(() => {
  const filteredByCapabilityState =
    capabilityStateFilter.value === 'ALL'
      ? searchedEntries.value
      : searchedEntries.value.filter((entry) => entry.capabilityState === capabilityStateFilter.value);
  if (lockReasonFilter.value === 'ALL') return filteredByCapabilityState;
  return filteredByCapabilityState.filter((entry) => {
    if (entry.state !== 'LOCKED') return false;
    return String(entry.reasonCode || '').toUpperCase() === lockReasonFilter.value;
  });
});

const filteredEntries = computed<CapabilityEntry[]>(() => {
  return searchedEntries.value.filter((entry) => {
    if (readyOnly.value && entry.state !== 'READY') return false;
    const matchesState = stateFilter.value === 'ALL' ? true : entry.state === stateFilter.value;
    if (!matchesState) return false;
    if (capabilityStateFilter.value !== 'ALL' && entry.capabilityState !== capabilityStateFilter.value) return false;
    if (lockReasonFilter.value !== 'ALL') {
      if (entry.state !== 'LOCKED') return false;
      if (String(entry.reasonCode || '').toUpperCase() !== lockReasonFilter.value) return false;
    }
    return true;
  });
});

const stateCounts = computed(() => {
  const counts = { READY: 0, LOCKED: 0, PREVIEW: 0 };
  for (const entry of tabBaseEntries.value) {
    counts[entry.state] += 1;
  }
  if (readyOnly.value) {
    return { READY: counts.READY, LOCKED: 0, PREVIEW: 0 };
  }
  return counts;
});

const allCount = computed(() => (readyOnly.value ? stateCounts.value.READY : tabBaseEntries.value.length));
const capabilityStateCounts = computed(() => {
  const counts = { allow: 0, readonly: 0, deny: 0, pending: 0, coming_soon: 0 };
  for (const entry of searchedEntries.value) {
    const key = entry.capabilityState as keyof typeof counts;
    if (key in counts) counts[key] += 1;
  }
  return counts;
});
const resultSummaryText = computed(() => {
  const parts = [`当前显示 ${filteredEntries.value.length} / ${entries.value.length} 项功能`];
  if (stateFilter.value !== 'ALL') parts.push(`状态：${stateLabel(stateFilter.value)}`);
  if (!isDeliveryMode.value && capabilityStateFilter.value !== 'ALL') {
    parts.push(`功能语义：${capabilityStateLabel(capabilityStateFilter.value)}`);
  }
  if (lockReasonFilter.value !== 'ALL') parts.push(`原因：${lockReasonLabel(lockReasonFilter.value)}`);
  return parts.join(' · ');
});
const readyOnlyNoResult = computed(
  () => readyOnly.value && filteredEntries.value.length === 0 && stateCounts.value.READY === 0,
);
const emptyStateReason = computed(() => {
  if (filteredEntries.value.length > 0) return '';
  if (!entries.value.length) return 'no_capability';
  if (readyOnlyNoResult.value) return 'ready_only_filtered';
  if (lockReasonFilter.value !== 'ALL') return 'lock_reason_filtered';
  if (searchText.value.trim()) return 'search_filtered';
  return 'filter_filtered';
});
const activeFilterChips = computed<FilterChip[]>(() => {
  const chips: FilterChip[] = [];
  const keyword = searchText.value.trim();
  if (keyword) chips.push({ key: 'search', label: `搜索：${keyword}` });
  if (readyOnly.value) chips.push({ key: 'ready-only', label: '仅显示可进入' });
  if (stateFilter.value !== 'ALL') chips.push({ key: 'state', label: `状态：${stateLabel(stateFilter.value)}` });
  if (!isDeliveryMode.value && capabilityStateFilter.value !== 'ALL') {
    chips.push({ key: 'capability-state', label: `功能语义：${capabilityStateLabel(capabilityStateFilter.value)}` });
  }
  if (lockReasonFilter.value !== 'ALL') {
    chips.push({ key: 'reason', label: `锁定原因：${lockReasonLabel(lockReasonFilter.value)}` });
  }
  return chips;
});

const groupedEntries = computed(() => {
  const filteredByRecent = new Map(filteredEntries.value.map((entry) => [entry.recentKey, entry]));
  const recentItems = recentEntryKeys.value
    .map((key) => filteredByRecent.get(key))
    .filter((entry): entry is CapabilityEntry => Boolean(entry));
  const recentKeySet = new Set(recentItems.map((item) => item.recentKey));
  const map = new Map<
    string,
    { sceneKey: string; sceneTitle: string; sceneSummary: string; items: CapabilityEntry[] }
  >();
  const sceneSetMap = new Map<string, Set<string>>();
  filteredEntries.value.forEach((entry) => {
    if (recentKeySet.has(entry.recentKey)) return;
    const bucketKey = isDeliveryMode.value ? entry.sceneKey : (entry.groupKey || entry.sceneKey);
    const bucketTitle = isDeliveryMode.value ? entry.sceneTitle : (entry.groupLabel || entry.sceneTitle);
    const current = map.get(bucketKey);
    if (current) {
      current.items.push(entry);
      const scenes = sceneSetMap.get(bucketKey) || new Set<string>();
      scenes.add(entry.sceneTitle);
      sceneSetMap.set(bucketKey, scenes);
      return;
    }
    map.set(bucketKey, {
      sceneKey: bucketKey,
      sceneTitle: bucketTitle,
      sceneSummary: '',
      items: [entry],
    });
    sceneSetMap.set(bucketKey, new Set([entry.sceneTitle]));
  });
  const grouped = Array.from(map.values())
    .map((group) => {
      const scenes = Array.from(sceneSetMap.get(group.sceneKey) || []);
      return {
        ...group,
        sceneSummary: scenes.length > 1 ? `覆盖场景：${scenes.slice(0, 3).join('、')}${scenes.length > 3 ? '…' : ''}` : '',
      };
    })
    .sort((a, b) => a.sceneTitle.localeCompare(b.sceneTitle));
  if (!recentItems.length) return grouped;
  return [{ sceneKey: '__recent__', sceneTitle: '最近使用', sceneSummary: '', items: recentItems }, ...grouped];
});
const hasRecentGroup = computed(() => groupedEntries.value.some((group) => group.sceneKey === '__recent__'));

const lockedReasonOptions = computed(() => {
  const map = new Map<string, number>();
  searchedEntries.value.forEach((entry) => {
    if (entry.state !== 'LOCKED') return;
    const code = String(entry.reasonCode || 'UNKNOWN').toUpperCase();
    map.set(code, (map.get(code) || 0) + 1);
  });
  return Array.from(map.entries())
    .map(([reasonCode, count]) => ({ reasonCode, count }))
    .sort((a, b) => b.count - a.count || a.reasonCode.localeCompare(b.reasonCode));
});

function toggleSceneGroup(sceneKey: string) {
  const next = new Set(collapsedSceneKeys.value);
  const expanded = next.has(sceneKey);
  if (expanded) next.delete(sceneKey);
  else next.add(sceneKey);
  collapsedSceneKeys.value = Array.from(next);
  void trackUsageEvent('workspace.group_toggle', {
    scene_key: sceneKey,
    action: expanded ? 'expand' : 'collapse',
  }).catch(() => {});
}

function expandAllSceneGroups() {
  collapsedSceneKeys.value = [];
  void trackUsageEvent('workspace.group_toggle', {
    scene_key: '*',
    action: 'expand_all',
  }).catch(() => {});
}

function collapseAllSceneGroups() {
  collapsedSceneKeys.value = groupedEntries.value.map((group) => group.sceneKey);
  void trackUsageEvent('workspace.group_toggle', {
    scene_key: '*',
    action: 'collapse_all',
  }).catch(() => {});
}

function lockReasonLabel(reasonCode: string) {
  const code = String(reasonCode || '').toUpperCase();
  if (code === 'PERMISSION_DENIED') return '权限不足';
  if (code === 'FEATURE_DISABLED') return '订阅未开通';
  if (code === 'ROLE_SCOPE_MISMATCH') return '角色范围不匹配';
  if (code === 'CAPABILITY_SCOPE_MISSING') return '缺少前置条件';
  if (code === 'CAPABILITY_SCOPE_CYCLE') return '功能依赖异常';
  if (code === 'COMING_SOON') return '功能建设中';
  if (code === 'PENDING_APPROVAL') return '待审批开放';
  return '当前不可用';
}

function capabilityStateLabel(state: string) {
  const normalized = String(state || '').toLowerCase();
  if (normalized === 'readonly') return '只读';
  if (normalized === 'deny') return '禁止';
  if (normalized === 'pending') return '待开放';
  if (normalized === 'coming_soon') return '建设中';
  return '可用';
}

function stateLabel(state: EntryState) {
  if (state === 'READY') return '可进入';
  if (state === 'LOCKED') return '暂不可用';
  return '即将开放';
}

function canEnter(entry: CapabilityEntry) {
  return entry.state === 'READY';
}

function actionLabel(entry: CapabilityEntry) {
  if (entry.state === 'LOCKED') return '暂不可用';
  if (entry.state === 'PREVIEW') return '即将开放';
  if (entry.capabilityState === 'readonly') return '只读进入';
  const mergeText = `${entry.title} ${entry.subtitle} ${entry.key} ${entry.sceneKey}`.toLowerCase();
  if (includesAny(mergeText, ['payment', '付款', '支付', 'approval', '审批'])) return '审核付款申请';
  if (includesAny(mergeText, ['contract', '合同'])) return '查看合同异常';
  if (includesAny(mergeText, ['risk', '风险', '预警'])) return '处理风险事项';
  if (includesAny(mergeText, ['change', '变更'])) return '确认变更事项';
  if (includesAny(mergeText, ['task', '任务', 'todo', '待办'])) return '处理任务';
  return '进入处理';
}

async function openScene(entry: CapabilityEntry) {
  if (!canEnter(entry)) return;
  lastFailedEntry.value = null;
  enterError.value = null;
  void trackUsageEvent('workspace.enter_click', { capability_key: entry.key, scene_key: entry.sceneKey }).catch(() => {});
  try {
    void trackCapabilityOpen(entry.key).catch(() => {});
    if (entry.route) {
      await router.push({ path: entry.route, query: entry.contextQuery });
    } else if (entry.targetActionId) {
      await router.push({
        path: `/a/${entry.targetActionId}`,
        query: { menu_id: entry.targetMenuId || undefined, ...entry.contextQuery },
      });
    } else if (entry.targetModel && entry.targetRecordId) {
      await router.push({
        path: `/r/${entry.targetModel}/${entry.targetRecordId}`,
        query: {
          menu_id: entry.targetMenuId || undefined,
          action_id: entry.targetActionId || undefined,
          ...entry.contextQuery,
        },
      });
    } else {
      await router.push({ path: `/s/${entry.sceneKey}`, query: entry.contextQuery });
    }
    pushRecentEntry(entry.recentKey);
    void trackUsageEvent('workspace.enter_result', {
      capability_key: entry.key,
      scene_key: entry.sceneKey,
      result: 'ok',
    }).catch(() => {});
  } catch (error) {
    const message = resolveEnterErrorMessage(error);
    const hint = resolveEnterErrorHint(message.code);
    lastFailedEntry.value = entry;
    enterError.value = {
      message: message.message,
      hint,
      code: message.code,
      traceId: message.traceId,
    };
    void trackUsageEvent('workspace.enter_result', {
      capability_key: entry.key,
      scene_key: entry.sceneKey,
      result: 'error',
      code: message.code || 'UNKNOWN',
      trace_id: message.traceId || '',
    }).catch(() => {});
  }
}

function openRoleLanding() {
  void trackUsageEvent('workspace.nav_click', {
    target: 'landing',
    from: 'workspace.home',
  }).catch(() => {});
  router.push({ path: session.resolveLandingPath('/'), query: workspaceContextQuery.value }).catch(() => {});
}

function goToMyWork() {
  void trackUsageEvent('workspace.nav_click', {
    target: 'my_work',
    from: 'workspace.home',
  }).catch(() => {});
  router.push({ path: '/my-work', query: workspaceContextQuery.value }).catch(() => {});
}

function goToUsageAnalytics() {
  void trackUsageEvent('workspace.nav_click', {
    target: 'usage_analytics',
    from: 'workspace.home',
  }).catch(() => {});
  router.push({ path: '/admin/usage-analytics' }).catch(() => {});
}

function goHome() {
  void trackUsageEvent('workspace.nav_click', {
    target: 'home',
    from: 'workspace.home',
  }).catch(() => {});
  router.push({ path: '/' }).catch(() => {});
}

function toggleEmptyHelp() {
  showEmptyHelp.value = !showEmptyHelp.value;
}

function clearSearchAndFilters() {
  const hadFilters = Boolean(
    searchText.value.trim()
      || readyOnly.value
      || stateFilter.value !== 'ALL'
      || capabilityStateFilter.value !== 'ALL'
      || lockReasonFilter.value !== 'ALL',
  );
  searchText.value = '';
  readyOnly.value = false;
  stateFilter.value = 'ALL';
  capabilityStateFilter.value = 'ALL';
  lockReasonFilter.value = 'ALL';
  if (hadFilters) {
    void trackUsageEvent('workspace.filter_clear_all', { source: 'workspace.home' }).catch(() => {});
  }
}

function clearSearchText() {
  searchText.value = '';
}

function showAllCapabilities() {
  const wasReadyOnly = readyOnly.value;
  readyOnly.value = false;
  stateFilter.value = 'ALL';
  capabilityStateFilter.value = 'ALL';
  if (wasReadyOnly) {
    void trackUsageEvent('workspace.ready_only.recover', { from: 'empty_state' }).catch(() => {});
  }
}

function clearLockReasonFilter() {
  lockReasonFilter.value = 'ALL';
}

function clearFilterChip(key: string) {
  if (key === 'search') searchText.value = '';
  if (key === 'ready-only') readyOnly.value = false;
  if (key === 'state') stateFilter.value = 'ALL';
  if (key === 'capability-state') capabilityStateFilter.value = 'ALL';
  if (key === 'reason') lockReasonFilter.value = 'ALL';
  void trackUsageEvent('workspace.filter_chip_clear', { filter_key: key }).catch(() => {});
}

function normalizeViewMode(raw: unknown) {
  return raw === 'list' ? 'list' : 'card';
}

function pushRecentEntry(recentKey: string) {
  if (!recentKey) return;
  const deduped = [recentKey, ...recentEntryKeys.value.filter((item) => item !== recentKey)].slice(0, 5);
  recentEntryKeys.value = deduped;
}

function clearRecentEntries() {
  const cleared = recentEntryKeys.value.length;
  if (!cleared) return;
  recentEntryKeys.value = [];
  void trackUsageEvent('workspace.recent.clear', { scope: workspaceScopeKey.value, cleared_count: cleared }).catch(() => {});
}

function openSuggestion(item: SuggestionItem) {
  const entry = entries.value.find((candidate) => candidate.id === item.entryId);
  if (!entry) {
    openRoleLanding();
    return;
  }
  const ctxSource = asText(entry.contextQuery.ctx_source) || 'workspace_today';
  void trackUsageEvent('workspace.today_click', {
    scene_key: entry.sceneKey || '',
    preset: '',
    ctx_source: ctxSource,
    has_entry_context: Boolean(entry.contextQuery.entry_context),
  }).catch(() => {});
  void trackUsageEvent('workspace.preset.navigate', {
    preset: '',
    from: 'workspace.home',
    to: `/s/${entry.sceneKey}`,
    ctx_source: ctxSource,
  }).catch(() => {});
  void openScene(entry);
}

function retryOpen() {
  if (!lastFailedEntry.value) return;
  void trackUsageEvent('workspace.enter_retry', {
    capability_key: lastFailedEntry.value.key,
    scene_key: lastFailedEntry.value.sceneKey,
    code: enterError.value?.code || '',
  }).catch(() => {});
  void openScene(lastFailedEntry.value);
}

function clearEnterError() {
  if (enterError.value) {
    void trackUsageEvent('workspace.enter_error_dismiss', {
      code: enterError.value.code || '',
      trace_id: enterError.value.traceId || '',
    }).catch(() => {});
  }
  enterError.value = null;
  lastFailedEntry.value = null;
}

async function fetchCoreMetrics() {
  const deniedModels = new Set<string>();
  const deniedReasonCodes = new Set<string>();
  const deniedIssueCounter = new Map<string, { model: string; op: string; reasonCode: string; count: number }>();
  const collectDeniedContext = (fallbackModel: string, error: unknown) => {
    deniedModels.add(fallbackModel);
    const issue = collectErrorContextIssue(deniedIssueCounter, error, { model: fallbackModel });
    if (issue.model) deniedModels.add(issue.model);
    if (issue.reasonCode) deniedReasonCodes.add(issue.reasonCode);
  };
  const readTotal = async (model: string, domain: unknown[] = []) => {
    try {
      const result = await listRecords({ model, fields: ['id'], limit: 1, domain, silentErrors: true });
      return Number(result.total || result.records?.length || 0);
    } catch (error) {
      collectDeniedContext(model, error);
      return 0;
    }
  };
  const readAmount = async (model: string, fieldCandidates: string[]) => {
    try {
      const result = await listRecords({
        model,
        fields: ['id', ...fieldCandidates],
        limit: 200,
        order: 'id desc',
        silentErrors: true,
      });
      const records = Array.isArray(result.records) ? result.records : [];
      return records.reduce((sum, item) => sum + pickNumericField(item, fieldCandidates), 0);
    } catch (error) {
      collectDeniedContext(model, error);
      return 0;
    }
  };

  const [projectCount, contractAmount, outputValue, riskModelCount] = await Promise.all([
    readTotal('project.project'),
    readAmount('construction.contract', ['amount_total', 'contract_amount', 'amount_untaxed']),
    readAmount('sc.settlement.order', ['amount_total', 'amount', 'total_amount']),
    readTotal('project.risk'),
  ]);

  const monthlyAnomalyCount = Math.max(
    0,
    entries.value.filter((entry) => entry.state === 'LOCKED').length,
  );

  coreValue.value = {
    projectCount,
    contractAmount,
    outputValue,
    riskCount: riskModelCount || riskCount.value,
    monthlyAnomalyCount,
  };
  const now = new Date();
  dataUpdatedAt.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  if (!deniedModels.size) {
    partialDataNotice.value = '';
    partialDataDetailLine.value = '';
    return;
  }
  const modelsText = Array.from(deniedModels).slice(0, 2).join('、');
  const isPermissionDenied = deniedReasonCodes.has('PERMISSION_DENIED');
  partialDataNotice.value = isPermissionDenied
    ? `部分数据未显示（${modelsText} 权限受限）`
    : `部分数据未显示（${modelsText} 暂不可用）`;
  const topIssues = summarizeErrorContextIssues(deniedIssueCounter, 3)
    .map((item) => `${issueScopeLabel(item)}[${item.reasonCode}] x${item.count}`);
  partialDataDetailLine.value = topIssues.length ? `受限明细：${topIssues.join('；')}` : '';
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return;
  if (enterError.value) {
    clearEnterError();
    return;
  }
  if (searchText.value.trim()) {
    clearSearchText();
  }
}

function resolveEnterErrorMessage(error: unknown) {
  const message = asText((error as { message?: unknown })?.message) || '功能入口暂时不可用';
  const lowered = message.toLowerCase();
  const code = lowered.includes('permission')
    ? 'PERMISSION_DENIED'
    : lowered.includes('not found')
      ? 'ROUTE_NOT_FOUND'
      : lowered.includes('timeout')
        ? 'TIMEOUT'
        : 'ENTER_FAILED';
  const traceId = asText((error as { trace_id?: unknown })?.trace_id) || asText((error as { traceId?: unknown })?.traceId);
  return { message, code, traceId };
}

function resolveEnterErrorHint(code: string) {
  if (code === 'PERMISSION_DENIED') return '请联系管理员开通对应权限后重试。';
  if (code === 'ROUTE_NOT_FOUND') return '入口配置异常，请稍后重试或联系管理员。';
  if (code === 'TIMEOUT') return '网络连接超时，请检查网络后点击重试。';
  return '请稍后重试；如果问题持续，请联系管理员。';
}

onMounted(() => {
  void trackUsageEvent('workspace.view', {
    role_key: asText(roleSurface.value?.role_code) || 'unknown',
    landing_scene_key: roleLandingScene.value,
  }).catch(() => {});
  fetchMyWorkSummary(20, 8)
    .then((result) => {
      myWorkSummary.value = Array.isArray(result.summary) ? result.summary : [];
    })
    .catch(() => {
      myWorkSummary.value = [];
    })
    .finally(() => {
      void fetchCoreMetrics();
    });
  try {
    const raw = window.localStorage.getItem(homeCollapseStorageKey.value);
    if (raw) {
      const parsed = JSON.parse(raw) as string[];
      if (Array.isArray(parsed)) {
        collapsedSceneKeys.value = parsed.filter((key) => typeof key === 'string' && key);
      }
    }
  } catch {
    // Ignore broken local cache.
  }
  try {
    const raw = window.localStorage.getItem(homeFilterStorageKey.value);
    if (raw) {
      const parsed = JSON.parse(raw) as {
        ready_only?: boolean;
        state_filter?: string;
        capability_state_filter?: string;
        lock_reason_filter?: string;
      };
      readyOnly.value = Boolean(parsed?.ready_only);
      const state = String(parsed?.state_filter || '').toUpperCase();
      if (state === 'ALL' || state === 'READY' || state === 'LOCKED' || state === 'PREVIEW') {
        stateFilter.value = state;
      }
      const capabilityState = String(parsed?.capability_state_filter || '').toLowerCase();
      if (capabilityState === 'all' || capabilityState === 'allow' || capabilityState === 'readonly' || capabilityState === 'deny' || capabilityState === 'pending' || capabilityState === 'coming_soon') {
        capabilityStateFilter.value = capabilityState === 'all' ? 'ALL' : capabilityState;
      }
      const lockReason = String(parsed?.lock_reason_filter || '').toUpperCase();
      if (lockReason) {
        lockReasonFilter.value = lockReason;
      }
    }
  } catch {
    // Ignore broken local cache.
  }
  try {
    const raw = window.localStorage.getItem(homeViewModeStorageKey.value);
    if (raw) {
      viewMode.value = normalizeViewMode(raw);
    }
  } catch {
    // Ignore broken local cache.
  }
  try {
    const raw = window.localStorage.getItem(homeRecentStorageKey.value);
    if (raw) {
      const parsed = JSON.parse(raw) as string[];
      if (Array.isArray(parsed)) {
        recentEntryKeys.value = parsed.filter((item) => typeof item === 'string' && item).slice(0, 5);
      }
    }
  } catch {
    // Ignore broken local cache.
  }
  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown);
});

watch(collapsedSceneKeys, () => {
  try {
    window.localStorage.setItem(homeCollapseStorageKey.value, JSON.stringify(collapsedSceneKeys.value));
  } catch {
    // Ignore local storage errors.
  }
});

watch([readyOnly, stateFilter, capabilityStateFilter, lockReasonFilter], () => {
  try {
    window.localStorage.setItem(
      homeFilterStorageKey.value,
      JSON.stringify({
        ready_only: readyOnly.value,
        state_filter: stateFilter.value,
        capability_state_filter: capabilityStateFilter.value.toLowerCase(),
        lock_reason_filter: lockReasonFilter.value,
      }),
    );
  } catch {
    // Ignore local storage errors.
  }
});

watch(viewMode, (next) => {
  try {
    window.localStorage.setItem(homeViewModeStorageKey.value, normalizeViewMode(next));
  } catch {
    // Ignore local storage errors.
  }
  if (next === lastTrackedViewMode.value) return;
  lastTrackedViewMode.value = next;
  void trackUsageEvent('workspace.view_mode_change', { view_mode: next }).catch(() => {});
});

watch(recentEntryKeys, () => {
  try {
    window.localStorage.setItem(homeRecentStorageKey.value, JSON.stringify(recentEntryKeys.value));
  } catch {
    // Ignore local storage errors.
  }
});

watch(readyOnly, (next) => {
  if (!next) return;
  stateFilter.value = 'READY';
  capabilityStateFilter.value = 'ALL';
  lockReasonFilter.value = 'ALL';
});

watch([readyOnly, stateFilter, capabilityStateFilter, lockReasonFilter], () => {
  const signature = `${readyOnly.value ? '1' : '0'}:${stateFilter.value}:${capabilityStateFilter.value}:${lockReasonFilter.value}`;
  if (signature === lastTrackedFilterSignature.value) return;
  lastTrackedFilterSignature.value = signature;
  void trackUsageEvent('workspace.filter_change', {
    ready_only: readyOnly.value,
    state_filter: stateFilter.value,
    capability_state_filter: capabilityStateFilter.value,
    lock_reason_filter: lockReasonFilter.value,
  }).catch(() => {});
});

watch(lockReasonFilter, (next) => {
  if (next === 'ALL') return;
  if (stateFilter.value === 'LOCKED') return;
  stateFilter.value = 'LOCKED';
});

watch(searchText, (next) => {
  const query = String(next || '').trim();
  if (!query) {
    lastTrackedSearch.value = '';
    return;
  }
  if (query === lastTrackedSearch.value) return;
  lastTrackedSearch.value = query;
  void trackUsageEvent('workspace.search', { query }).catch(() => {});
});

watch([filteredEntries, entries, readyOnly, lockReasonFilter, capabilityStateFilter, stateFilter, searchText], () => {
  const reason = emptyStateReason.value;
  if (!reason) return;
  const signature = `${reason}:${readyOnly.value ? '1' : '0'}:${stateFilter.value}:${capabilityStateFilter.value}:${lockReasonFilter.value}:${searchText.value.trim()}`;
  if (signature === lastTrackedEmptySignature.value) return;
  lastTrackedEmptySignature.value = signature;
  void trackUsageEvent('workspace.empty_state', {
    reason,
    ready_only: readyOnly.value,
    state_filter: stateFilter.value,
    capability_state_filter: capabilityStateFilter.value,
    lock_reason_filter: lockReasonFilter.value,
    search: searchText.value.trim(),
  }).catch(() => {});
});

function highlightParts(raw: string) {
  const text = String(raw || '');
  const query = searchText.value.trim();
  if (!query) return [{ text, hit: false }];
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escaped})`, 'ig');
  const parts = text.split(regex).filter((part) => part.length > 0);
  return parts.map((part) => ({ text: part, hit: part.toLowerCase() === query.toLowerCase() }));
}
</script>

<style scoped>
.capability-home {
  display: grid;
  gap: 16px;
}

.value-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.value-card {
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: #ffffff;
  padding: 12px;
  display: grid;
  gap: 6px;
}

.value-label {
  margin: 0;
  font-size: 12px;
  color: #475569;
}

.value-number {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.1;
}

.value-meta {
  margin: 0;
  font-size: 12px;
  color: #64748b;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.value-judge {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

.value-state {
  border-radius: 999px;
  padding: 2px 8px;
  border: 1px solid currentColor;
  font-weight: 700;
}

.value-state.state-green {
  color: #166534;
  background: #dcfce7;
}

.value-state.state-amber {
  color: #92400e;
  background: #fef3c7;
}

.value-state.state-red {
  color: #b91c1c;
  background: #fee2e2;
}

.hero {
  display: block;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  position: relative;
  background:
    radial-gradient(120% 180% at 0% 0%, rgba(14, 116, 144, 0.05), rgba(255, 255, 255, 0) 60%),
    linear-gradient(135deg, rgba(21, 128, 61, 0.04), rgba(2, 132, 199, 0.06));
}

.hero-main {
  display: grid;
  gap: 4px;
}

.demo-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.05em;
  background: #b91c1c;
  color: #fff;
}

.hero h2 {
  margin: 0;
  font-size: 22px;
}

.lead {
  margin: 0;
  color: #334155;
  font-weight: 500;
}

.hero-info-row {
  margin-top: 2px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.role-line {
  margin: 0;
  color: #334155;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.product-line {
  margin: 2px 0 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  opacity: 0.75;
}

.product-pill {
  font-size: 10px;
  color: #334155;
  border: 1px solid #dbe4ef;
  border-radius: 999px;
  background: #f8fafc;
  padding: 1px 7px;
}

.bundle-line {
  margin: 2px 0 0;
  font-size: 11px;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.partial-data {
  color: #b45309;
  font-weight: 600;
}

.steady-data {
  color: #166534;
  font-weight: 600;
}

.partial-data-detail {
  color: #92400e;
  font-size: 10px;
}

.demo-hint {
  margin: 6px 0 0;
  color: #7f1d1d;
  font-size: 12px;
  font-weight: 600;
}

.license-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 4px 8px;
}

.hud-line {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 12px;
}

.inline-link {
  border: 0;
  background: transparent;
  color: #1d4ed8;
  text-decoration: underline;
  padding: 0;
  cursor: pointer;
}

.view-toggle {
  display: inline-flex;
  flex-wrap: wrap;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

.view-toggle button {
  border: 0;
  background: #f8fafc;
  color: #334155;
  padding: 6px 10px;
  font-size: 11px;
  cursor: pointer;
}

.view-toggle button.active {
  background: #1d4ed8;
  color: white;
}

.my-work-btn {
  border-right: 1px solid #d1d5db !important;
  background: #0f766e !important;
  color: #ffffff !important;
  font-weight: 500;
}

.my-work-btn:hover {
  background: #0d9488 !important;
}

.dot {
  color: #94a3b8;
}

.secondary-panel {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  padding: 10px 12px;
}

.secondary-panel > summary {
  cursor: pointer;
  color: #334155;
  font-size: 13px;
  font-weight: 600;
}

.demo-story-panel summary {
  color: #0f172a;
}

@media (max-width: 1120px) {
  .hero-info-row {
    align-items: flex-start;
  }
  .view-toggle {
    width: 100%;
  }
}

@media (max-width: 760px) {
  .hero {
    padding: 12px;
  }
  .hero h2 {
    font-size: 20px;
  }
}

.empty {
  padding: 24px;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  background: #f8fafc;
  display: grid;
  gap: 10px;
}

.empty p {
  margin: 0;
  color: #334155;
}

.empty-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.empty-btn {
  border: 1px solid #93c5fd;
  border-radius: 8px;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 6px 10px;
  cursor: pointer;
}

.empty-btn.secondary {
  border-color: #cbd5e1;
  background: #fff;
  color: #475569;
}

.empty-help {
  font-size: 12px;
  color: #475569;
}

.filters {
  display: grid;
  gap: 10px;
}

.status-panel {
  border: 1px solid #fecaca;
  background: #fff1f2;
  border-radius: 10px;
  padding: 10px 12px;
  display: grid;
  gap: 6px;
}

.status-title {
  margin: 0;
  color: #9f1239;
  font-size: 13px;
  font-weight: 700;
}

.status-detail {
  margin: 0;
  color: #7f1d1d;
  font-size: 12px;
}

.status-meta {
  margin: 0;
  color: #9f1239;
  font-size: 11px;
}

.status-actions {
  display: inline-flex;
  gap: 8px;
}

.status-actions button {
  border: 1px solid #fda4af;
  border-radius: 8px;
  background: #fff;
  color: #9f1239;
  padding: 4px 8px;
  cursor: pointer;
}

.today-actions {
  border: 1px solid #bfdbfe;
  border-radius: 12px;
  background: linear-gradient(135deg, #e0f2fe, #f8fafc);
  padding: 14px;
}

.risk-section,
.ops-section {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  padding: 14px;
}

.risk-header h3,
.ops-header h3 {
  margin: 0;
  font-size: 16px;
  color: #0f172a;
}

.risk-header p,
.ops-header p {
  margin: 4px 0 10px;
  color: #64748b;
  font-size: 12px;
}

.risk-summary {
  margin: 4px 0 0;
  color: #7f1d1d;
  font-size: 12px;
  font-weight: 600;
}

.risk-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.risk-card {
  border-radius: 10px;
  padding: 10px;
}

.risk-card.glow {
  box-shadow: 0 0 0 2px rgba(185, 28, 28, 0.18);
}

.risk-card p {
  margin: 0;
  font-size: 12px;
}

.risk-card strong {
  font-size: 24px;
  line-height: 1.1;
}

.risk-red {
  background: #fee2e2;
  color: #991b1b;
}

.risk-amber {
  background: #fef3c7;
  color: #92400e;
}

.risk-green {
  background: #dcfce7;
  color: #166534;
}

.risk-trend,
.risk-source {
  margin-top: 10px;
}

.risk-subtitle {
  margin: 0 0 6px;
  font-size: 12px;
  color: #475569;
  font-weight: 600;
}

.trend-bars {
  display: grid;
  gap: 6px;
}

.trend-item {
  display: grid;
  grid-template-columns: 64px 1fr 40px;
  align-items: center;
  gap: 8px;
}

.trend-label,
.trend-value {
  font-size: 12px;
  color: #334155;
}

.trend-track {
  height: 8px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.trend-fill {
  height: 100%;
  background: linear-gradient(90deg, #0ea5e9, #2563eb);
}

.source-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.source-tag {
  font-size: 12px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  padding: 3px 8px;
  color: #334155;
  background: #f8fafc;
}

.risk-actions {
  margin-top: 10px;
}

.risk-action-list {
  display: grid;
  gap: 8px;
}

.risk-action-item {
  border: 1px solid #fecaca;
  border-radius: 10px;
  background: #fff7f7;
  padding: 10px;
}

.risk-action-title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: #7f1d1d;
}

.risk-action-desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: #7c2d12;
}

.risk-action-buttons {
  margin-top: 8px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.risk-action-buttons button {
  border: 1px solid #fca5a5;
  border-radius: 8px;
  background: #fff;
  color: #991b1b;
  padding: 5px 8px;
  cursor: pointer;
}

.ops-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}

.advice-section {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #ffffff;
  padding: 14px;
}

.advice-list {
  display: grid;
  gap: 8px;
}

.advice-btn {
  margin-top: 8px;
  border: 1px solid #93c5fd;
  border-radius: 8px;
  background: #eff6ff;
  color: #1e3a8a;
  padding: 6px 10px;
  cursor: pointer;
}

.advice-item {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 10px;
}

.advice-title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
}

.advice-desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: #475569;
}

.advice-red {
  border-color: #fecaca;
  background: #fff1f2;
}

.advice-red .advice-title {
  color: #b91c1c;
}

.advice-amber {
  border-color: #fde68a;
  background: #fffbeb;
}

.advice-amber .advice-title {
  color: #92400e;
}

.advice-green {
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.advice-green .advice-title {
  color: #166534;
}

.ops-card {
  border: 1px solid #dbeafe;
  border-radius: 10px;
  background: #f8fafc;
  padding: 10px;
  display: grid;
  gap: 8px;
}

.story-section {
  border: 1px solid #fde68a;
  border-radius: 12px;
  background: #fffbeb;
  padding: 14px;
}

.story-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 10px;
}

.story-card {
  border: 1px solid #fde68a;
  border-radius: 10px;
  padding: 10px;
  background: #fff;
}

.story-title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: #111827;
}

.story-desc {
  margin: 6px 0 0;
  font-size: 12px;
  color: #4b5563;
}

.story-btn {
  margin-top: 8px;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  background: #fef3c7;
  color: #78350f;
  padding: 6px 10px;
  cursor: pointer;
}

.ops-card p {
  margin: 0;
  font-size: 12px;
  color: #475569;
}

.ops-card h4 {
  margin: 0;
  font-size: 28px;
  color: #0f172a;
  line-height: 1;
}

.ops-card small {
  color: #334155;
  font-size: 12px;
}

.compare-line {
  display: grid;
  grid-template-columns: 56px 1fr auto;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.compare-track {
  height: 8px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.compare-fill {
  height: 100%;
}

.compare-fill.contract {
  background: linear-gradient(90deg, #16a34a, #22c55e);
}

.compare-fill.output {
  background: linear-gradient(90deg, #0284c7, #2563eb);
}

.today-actions-header h3 {
  margin: 0;
  font-size: 16px;
  color: #0f172a;
}

.today-actions-header p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #475569;
}

.today-actions-grid {
  margin-top: 12px;
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
}

.group-overview {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #f8fafc;
  padding: 14px;
}

.group-overview-header h3 {
  margin: 0;
  font-size: 16px;
  color: #0f172a;
}

.group-overview-header p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #64748b;
}

.group-overview-grid {
  margin-top: 12px;
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.group-card {
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  background: #fff;
  padding: 10px 12px;
}

.group-title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.group-meta {
  margin: 6px 0 0;
  font-size: 12px;
  color: #475569;
}

.today-card {
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  background: #fff;
  padding: 12px;
  display: grid;
  gap: 8px;
}

.today-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 8px;
}

.today-status {
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
}

.today-status-urgent {
  background: #fee2e2;
  color: #b91c1c;
}

.today-status-normal {
  background: #dbeafe;
  color: #1d4ed8;
}

.today-desc {
  margin: 0;
  font-size: 12px;
  color: #475569;
  min-height: 34px;
}

.today-count {
  margin: 0;
  font-size: 12px;
  color: #0f172a;
  font-weight: 600;
}

.today-btn {
  justify-self: start;
  border: 0;
  border-radius: 8px;
  background: #0ea5e9;
  color: #fff;
  padding: 6px 10px;
  cursor: pointer;
}

.today-btn:disabled {
  background: #cbd5e1;
  color: #475569;
  cursor: not-allowed;
}

.search-input {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 10px 12px;
  background: #fff;
}

.search-row {
  display: flex;
  gap: 8px;
}

.search-clear-btn {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #334155;
  padding: 0 10px;
  cursor: pointer;
  white-space: nowrap;
}

.result-summary {
  margin: -2px 0 0;
  color: #64748b;
  font-size: 12px;
}

.state-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ready-only {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #334155;
  font-size: 13px;
}

.filter-tip {
  margin: -2px 0 0;
  color: #475569;
  font-size: 12px;
}

.state-filters button {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: #fff;
  color: #334155;
  padding: 6px 10px;
  cursor: pointer;
}

.state-filters button.active {
  border-color: #1d4ed8;
  background: #eff6ff;
  color: #1e40af;
}

.state-filters button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.reason-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.reason-filters button {
  border: 1px dashed #cbd5e1;
  border-radius: 999px;
  background: #fff;
  color: #334155;
  padding: 6px 10px;
  cursor: pointer;
}

.reason-filters button.active {
  border-color: #b91c1c;
  color: #b91c1c;
  background: #fff1f2;
}

.active-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-chip {
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  color: #1e40af;
  background: #eff6ff;
  cursor: pointer;
}

.filter-chip-clear {
  border-style: dashed;
  color: #475569;
  background: #fff;
}

.group-actions {
  display: inline-flex;
  gap: 8px;
}

.group-actions button {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #334155;
  padding: 6px 10px;
  cursor: pointer;
}

.scene-groups {
  display: grid;
  gap: 12px;
}

.scene-group {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  padding: 10px;
}

.scene-group-header {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.scene-toggle {
  border: 0;
  background: transparent;
  color: #0f172a;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.scene-count {
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 2px 8px;
  font-size: 12px;
}

.scene-summary {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.list {
  display: grid;
  gap: 10px;
}

.entry {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 12px;
  padding: 14px;
}

.entry-main {
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 6px 0;
}

.title {
  font-weight: 600;
}

.state {
  font-size: 12px;
  border-radius: 999px;
  padding: 2px 8px;
  border: 1px solid currentColor;
}

.capability-state {
  color: #1d4ed8;
  border-color: #93c5fd;
  background: #eff6ff;
}

.subtitle {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hit {
  background: #fef08a;
}

.hud-meta {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 11px;
  overflow-wrap: anywhere;
}

.lock-reason {
  margin: 6px 0 0;
  color: #b91c1c;
  font-size: 12px;
}

.open-btn {
  align-self: center;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  padding: 6px 10px;
  cursor: pointer;
}

.open-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.state-ready .state {
  color: #166534;
}

.state-preview .state {
  color: #92400e;
}

.state-locked .state {
  color: #b91c1c;
}
</style>
