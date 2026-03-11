<template>
  <PageRenderer
    v-if="useUnifiedHomeRenderer"
    :contract="homeOrchestrationContract"
    :datasets="homeOrchestrationDatasets"
    @action="handleHomeBlockAction"
  />

  <section v-else class="capability-home">
    <!-- Page intent: 优先处理风险与审批，快速判断经营状态并进入下一步动作。 -->
    <header v-if="isHomeSectionEnabled('hero') && isHomeSectionTag('hero', 'header')" class="hero" :class="homeSectionClass('hero')" :style="homeSectionStyle('hero')">
      <div class="hero-main">
        <h2>{{ heroTitle }}</h2>
        <p class="lead">{{ heroLead }}</p>
        <div class="hero-info-row">
          <p class="role-line">
            <span>{{ homeLayoutText('hero.role_label', '当前角色') }}：{{ roleLabel }}</span>
            <span class="dot">·</span>
            <span>{{ homeLayoutText('hero.landing_label', '默认入口') }}：{{ roleLandingLabel }}</span>
            <button class="inline-link" @click="openRoleLanding">{{ homeLayoutText('hero.open_landing_action', '打开默认入口') }}</button>
          </p>
          <div class="view-toggle">
            <button
              v-for="action in heroQuickActions"
              :key="`hero-action-${action.key}`"
              class="my-work-btn"
              @click="executeHeroAction(action.key)"
            >
              {{ action.label }}
            </button>
            <button :class="{ active: viewMode === 'card' }" @click="viewMode = 'card'">{{ homeLayoutText('hero.view_mode_card', '卡片') }}</button>
            <button :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">{{ homeLayoutText('hero.view_mode_list', '列表') }}</button>
          </div>
        </div>
        <p class="product-line">
          <span v-for="tag in heroProductTags" :key="`hero-tag-${tag}`" class="product-pill">{{ tag }}</span>
        </p>
        <p class="bundle-line">
          <span>{{ homeLayoutText('hero.updated_at_label', '数据更新时间') }}：{{ dataUpdatedAt }}</span>
          <span class="dot">·</span>
          <span :class="partialDataNotice ? 'partial-data' : 'steady-data'">
            {{ partialDataNotice || homeLayoutText('hero.steady_notice', '当前运行平稳') }}
          </span>
        </p>
        <p v-if="partialDataDetailLine" class="bundle-line partial-data-detail">
          {{ partialDataDetailLine }}
        </p>
        <p v-if="isHudEnabled" class="hud-line">
          HUD: role_key={{ roleSurface?.role_code || '-' }} · landing_scene_key={{ roleLandingScene }}
        </p>
        <p v-if="isHudEnabled" class="hud-line">
          HUD: internal_tiles={{ internalTileCount }} · visible_mode=show_all
        </p>
        <p v-if="isHudEnabled" class="hud-line">
          HUD: orchestration_blocks={{ orchestrationBlocks.length }} · role_variant={{ roleVariantCode || '-' }}
        </p>
      </div>
    </header>

    <section v-if="isHomeSectionEnabled('metrics') && isHomeSectionTag('metrics', 'section')" class="value-grid" :class="homeSectionClass('metrics')" :style="homeSectionStyle('metrics')" :aria-label="homeLayoutText('metrics.aria_label', '核心价值区')">
      <article v-for="metric in coreMetrics" :key="metric.key" class="value-card" :class="[`tone-${metric.tone || 'neutral'}`, `progress-${metric.progress || 'running'}`]">
        <p class="value-label">{{ metric.label }}</p>
        <p class="value-number">{{ metric.value }}</p>
        <p class="value-meta">
          <span class="value-state" :class="`state-${metric.level}`">{{ levelLabel(metric.level) }}</span>
          <span>{{ metric.delta }}</span>
        </p>
        <p class="value-judge">{{ metric.hint }}</p>
      </article>
    </section>

    <section v-if="isHomeSectionEnabled('today_actions') && isHomeSectionTag('today_actions', 'section')" class="today-actions" :class="homeSectionClass('today_actions')" :style="homeSectionStyle('today_actions')" :aria-label="homeLayoutText('today_actions.aria_label', '今日建议')">
      <header class="today-actions-header">
        <h3>{{ homeLayoutText('today_actions.title', '今日待办') }}</h3>
        <p>{{ homeLayoutText('today_actions.subtitle', '点击可直接进入处理界面。') }}</p>
      </header>
      <div class="today-actions-grid">
        <article v-for="item in concreteTodos" :key="item.id" class="today-card" :class="[`tone-${item.tone || 'info'}`, `progress-${item.progress || 'pending'}`]">
          <p class="today-title">
            <span>{{ item.title }}</span>
            <span v-if="item.status" class="today-status" :class="`today-status-${item.status}`">
              {{ item.status === 'urgent' ? homeLayoutText('today_actions.status_urgent', '紧急') : homeLayoutText('today_actions.status_normal', '普通') }}
            </span>
          </p>
          <p class="today-desc">{{ item.description }}</p>
          <p v-if="typeof item.count === 'number'" class="today-count">{{ homeLayoutText('today_actions.count_prefix', '待处理') }} {{ item.count }}</p>
          <button class="today-btn" :disabled="item.ready === false" @click="openSuggestion(item)">
            {{ item.ready === false ? homeLayoutText('today_actions.coming_soon_action', '即将开放') : todoActionLabel(item.title) }}
          </button>
        </article>
      </div>
    </section>

    <section v-if="isHomeSectionEnabled('risk') && isHomeSectionTag('risk', 'section')" class="risk-section" :class="homeSectionClass('risk')" :style="homeSectionStyle('risk')" :aria-label="homeLayoutText('risk.aria_label', '关键风险区')">
      <header class="risk-header">
        <h3>{{ homeLayoutText('risk.title', '关键风险') }}</h3>
        <p>{{ homeLayoutText('risk.subtitle', '10 秒识别整体风险态势。') }}</p>
        <p class="risk-summary">{{ riskSummaryLine }}</p>
      </header>
      <div class="risk-grid">
        <article class="risk-card risk-red" :class="{ glow: riskBuckets.red >= 3 }">
          <p>{{ homeLayoutText('risk.bucket.red', '严重 ⚠') }}</p>
          <strong>{{ riskBuckets.red }}</strong>
        </article>
        <article class="risk-card risk-amber" :class="{ glow: riskBuckets.amber >= 4 }">
          <p>{{ homeLayoutText('risk.bucket.amber', '关注 ⏳') }}</p>
          <strong>{{ riskBuckets.amber }}</strong>
        </article>
        <article class="risk-card risk-green">
          <p>{{ homeLayoutText('risk.bucket.green', '正常 ✓') }}</p>
          <strong>{{ riskBuckets.green }}</strong>
        </article>
      </div>
      <div class="risk-trend">
        <p class="risk-subtitle">{{ homeLayoutText('risk.trend_title', '风险趋势（7/30 天）') }}</p>
        <div class="trend-bars">
          <div v-for="(item, idx) in riskTrend" :key="`trend-${idx}`" class="trend-item">
            <span class="trend-label">{{ item.label }}</span>
            <div class="trend-track"><div class="trend-fill" :style="{ width: `${item.percent}%` }"></div></div>
            <span class="trend-value">{{ item.value }}</span>
          </div>
        </div>
      </div>
      <div class="risk-source">
        <p class="risk-subtitle">{{ homeLayoutText('risk.sources_title', '风险来源分布') }}</p>
        <div class="source-tags">
          <span v-for="item in riskSources" :key="`source-${item.label}`" class="source-tag">{{ item.label }} {{ item.count }}</span>
        </div>
      </div>
      <div class="risk-actions">
        <p class="risk-subtitle">{{ homeLayoutText('risk.actions_title', '风险待处理清单') }}</p>
        <div class="risk-action-list">
          <article v-for="item in riskActionItems" :key="item.id" class="risk-action-item">
            <p class="risk-action-title">{{ item.title }}</p>
            <p class="risk-action-desc">{{ item.description }}</p>
            <div class="risk-action-buttons">
              <button @click="openRiskAction(item, 'detail')">{{ homeLayoutText('risk.actions.detail', '看详情') }}</button>
              <button @click="openRiskAction(item, 'assign')">{{ homeLayoutText('risk.actions.assign', '分派') }}</button>
              <button @click="openRiskAction(item, 'close')">{{ homeLayoutText('risk.actions.close', '关闭') }}</button>
              <button @click="openRiskAction(item, 'approve')">{{ homeLayoutText('risk.actions.approve', '发起审批') }}</button>
            </div>
          </article>
        </div>
      </div>
    </section>

    <details v-if="isHomeSectionEnabled('ops') && isHomeSectionTag('ops', 'details')" class="secondary-panel" :class="homeSectionClass('ops')" :style="homeSectionStyle('ops')" :open="isHomeSectionOpenDefault('ops')">
      <summary>{{ homeLayoutText('ops.title', '项目经营概览') }}</summary>
      <section class="ops-section" :aria-label="homeLayoutText('ops.aria_label', '项目经营概览区')">
        <div class="ops-grid">
          <article class="ops-card">
            <p>{{ homeLayoutText('ops.compare.title', '合同额 vs 累计产值') }}</p>
            <div class="compare-line">
              <span>{{ homeLayoutText('ops.compare.contract', '合同额') }}</span>
              <div class="compare-track"><div class="compare-fill contract" :style="{ width: `${opsBars.contract}%` }"></div></div>
              <strong>{{ opsBars.contract }}%</strong>
            </div>
            <div class="compare-line">
              <span>{{ homeLayoutText('ops.compare.output', '累计产值') }}</span>
              <div class="compare-track"><div class="compare-fill output" :style="{ width: `${opsBars.output}%` }"></div></div>
              <strong>{{ opsBars.output }}%</strong>
            </div>
          </article>
          <article class="ops-card">
            <p>{{ homeLayoutText('ops.kpi.cost_rate', '成本执行率') }}</p>
            <h4>{{ opsKpi.costRate }}%</h4>
            <small>{{ trendText(opsKpi.costRateDelta) }}</small>
          </article>
          <article class="ops-card">
            <p>{{ homeLayoutText('ops.kpi.payment_rate', '资金支付比例') }}</p>
            <h4>{{ opsKpi.paymentRate }}%</h4>
            <small>{{ trendText(opsKpi.paymentRateDelta) }}</small>
          </article>
          <article class="ops-card">
            <p>{{ homeLayoutText('ops.kpi.output_trend', '本月产值趋势') }}</p>
            <h4>{{ trendText(opsKpi.outputTrendDelta) }}</h4>
            <small>{{ homeLayoutText('ops.kpi.output_note', '基于当前可见业务数据') }}</small>
          </article>
        </div>
      </section>
    </details>

    <details v-if="isHomeSectionEnabled('advice') && isHomeSectionTag('advice', 'details')" class="secondary-panel" :class="homeSectionClass('advice')" :style="homeSectionStyle('advice')" :open="isHomeSectionOpenDefault('advice')">
      <summary>{{ homeLayoutText('advice.title', '系统建议关注事项') }}</summary>
      <section class="advice-section" :aria-label="homeLayoutText('advice.aria_label', '系统建议关注事项')">
        <div class="advice-list">
          <article v-for="item in systemAdvice" :key="item.id" class="advice-item" :class="`advice-${item.level}`">
            <p class="advice-title">{{ item.title }}</p>
            <p class="advice-desc">{{ item.description }}</p>
            <button v-if="item.actionLabel" class="advice-btn" @click="openAdvice(item)">{{ item.actionLabel }}</button>
          </article>
        </div>
      </section>
    </details>

    <section v-if="isHomeSectionEnabled('group_overview') && isHomeSectionTag('group_overview', 'section') && capabilityGroupCards.length" class="group-overview" :class="homeSectionClass('group_overview')" :style="homeSectionStyle('group_overview')" :aria-label="homeLayoutText('group_overview.aria_label', '辅助入口区')">
      <header class="group-overview-header">
        <h3>{{ homeLayoutText('group_overview.title', '辅助入口') }}</h3>
        <p>{{ homeLayoutText('group_overview.subtitle', '按业务域查看功能分组与可用状态。') }}</p>
      </header>
      <div class="group-overview-grid">
        <article v-for="group in capabilityGroupCards" :key="`group-${group.key}`" class="group-card">
          <p class="group-title">{{ group.label }}</p>
          <p class="group-meta">{{ homeLayoutText('group_overview.capability_count_prefix', '功能数') }} {{ group.capabilityCount }}</p>
          <p class="group-meta">
            {{ homeLayoutText('group_overview.allow_prefix', '可用') }} {{ group.allowCount }} · {{ homeLayoutText('group_overview.readonly_prefix', '只读') }} {{ group.readonlyCount }} · {{ homeLayoutText('group_overview.deny_prefix', '禁用') }} {{ group.denyCount }}
          </p>
        </article>
      </div>
    </section>

    <section v-if="isHomeSectionEnabled('filters') && isHomeSectionTag('filters', 'section')" class="filters" :class="homeSectionClass('filters')" :style="homeSectionStyle('filters')">
      <div v-if="enterError" class="status-panel" role="status" aria-live="polite">
        <p class="status-title">{{ pageText('entry_error_title_prefix', '进入失败：') }}{{ enterError.message }}</p>
        <p class="status-detail">{{ enterError.hint }}</p>
        <p v-if="isHudEnabled" class="status-meta">
          code={{ enterError.code || '-' }} · trace_id={{ enterError.traceId || '-' }}
        </p>
        <div class="status-actions">
          <button v-if="lastFailedEntry" @click="retryOpen">{{ pageText('action_retry', '重试') }}</button>
          <button @click="clearEnterError">{{ pageText('action_acknowledge', '知道了') }}</button>
        </div>
      </div>
      <div class="search-row">
        <input
          v-model.trim="searchText"
          class="search-input"
          type="search"
          :placeholder="pageText('search_placeholder', '搜索功能名称或说明')"
        />
        <button v-if="searchText.trim()" class="search-clear-btn" @click="clearSearchText">{{ pageText('search_clear', '清空搜索') }}</button>
      </div>
      <p class="result-summary">{{ resultSummaryText }}</p>
      <label class="ready-only">
        <input v-model="readyOnly" type="checkbox" />
        {{ pageText('ready_only_label', '仅显示可进入功能') }}
      </label>
      <div class="state-filters">
        <button :class="{ active: stateFilter === 'ALL' }" @click="stateFilter = 'ALL'">
          {{ pageText('state_all', '全部') }} {{ allCount }}
        </button>
        <button :class="{ active: stateFilter === 'READY' }" @click="stateFilter = 'READY'">
          {{ pageText('state_ready', '可进入') }} {{ stateCounts.READY }}
        </button>
        <button
          :class="{ active: stateFilter === 'LOCKED' }"
          :disabled="readyOnly"
          @click="stateFilter = 'LOCKED'"
        >
          {{ pageText('state_locked', '暂不可用') }} {{ stateCounts.LOCKED }}
        </button>
        <button
          :class="{ active: stateFilter === 'PREVIEW' }"
          :disabled="readyOnly"
          @click="stateFilter = 'PREVIEW'"
        >
          {{ pageText('state_preview', '即将开放') }} {{ stateCounts.PREVIEW }}
        </button>
      </div>
      <div v-if="!isDeliveryMode" class="state-filters">
        <button :class="{ active: capabilityStateFilter === 'ALL' }" @click="capabilityStateFilter = 'ALL'">
          {{ pageText('capability_state_all', '功能语义：全部') }}
        </button>
        <button :class="{ active: capabilityStateFilter === 'allow' }" @click="capabilityStateFilter = 'allow'">
          {{ pageText('capability_state_allow', '可用') }} {{ capabilityStateCounts.allow }}
        </button>
        <button :class="{ active: capabilityStateFilter === 'readonly' }" @click="capabilityStateFilter = 'readonly'">
          {{ pageText('capability_state_readonly', '只读') }} {{ capabilityStateCounts.readonly }}
        </button>
        <button :class="{ active: capabilityStateFilter === 'deny' }" @click="capabilityStateFilter = 'deny'">
          {{ pageText('capability_state_deny', '禁止') }} {{ capabilityStateCounts.deny }}
        </button>
        <button :class="{ active: capabilityStateFilter === 'pending' }" @click="capabilityStateFilter = 'pending'">
          {{ pageText('capability_state_pending', '待开放') }} {{ capabilityStateCounts.pending }}
        </button>
        <button :class="{ active: capabilityStateFilter === 'coming_soon' }" @click="capabilityStateFilter = 'coming_soon'">
          {{ pageText('capability_state_coming_soon', '建设中') }} {{ capabilityStateCounts.coming_soon }}
        </button>
      </div>
      <p v-if="readyOnly" class="filter-tip">{{ pageText('filter_tip_ready_only', '已启用“仅显示可进入功能”，暂不可用与即将开放不会展示。') }}</p>
      <div v-if="lockedReasonOptions.length" class="reason-filters">
        <button :class="{ active: lockReasonFilter === 'ALL' }" @click="lockReasonFilter = 'ALL'">
          {{ pageText('lock_reason_all', '锁定原因：全部') }}
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
        <button class="filter-chip filter-chip-clear" @click="clearSearchAndFilters">{{ pageText('action_clear_all_filters', '清空全部筛选') }}</button>
      </div>
      <div v-if="groupedEntries.length" class="group-actions">
        <button @click="expandAllSceneGroups">{{ pageText('action_expand_all_groups', '展开全部分组') }}</button>
        <button @click="collapseAllSceneGroups">{{ pageText('action_collapse_all_groups', '折叠全部分组') }}</button>
        <button v-if="hasRecentGroup" @click="clearRecentEntries">{{ pageText('action_clear_recent', '清空最近使用') }}</button>
      </div>
    </section>

    <div v-if="!filteredEntries.length" class="empty">
      <template v-if="entries.length">
        <p>
          {{
            readyOnlyNoResult
              ? pageText('empty_ready_only_no_result', '当前启用了“仅显示可进入功能”，暂时没有可进入功能。')
              : searchKeyword
                ? `${pageText('empty_search_no_result_prefix', '未找到与“')}${searchKeyword}${pageText('empty_search_no_result_suffix', '”相关的功能，请调整筛选条件。')}`
                : pageText('empty_filter_no_result', '未找到相关功能，请调整筛选条件。')
          }}
        </p>
        <div class="empty-actions">
          <button v-if="lockReasonFilter !== 'ALL'" class="empty-btn" @click="clearLockReasonFilter">{{ pageText('action_clear_lock_reason', '清除锁定原因') }}</button>
          <button v-if="readyOnlyNoResult" class="empty-btn" @click="showAllCapabilities">{{ pageText('action_show_all_capabilities', '显示全部功能') }}</button>
          <button class="empty-btn" @click="clearSearchAndFilters">{{ pageText('action_clear_search_filters', '清空搜索与筛选') }}</button>
        </div>
      </template>
      <template v-else>
        <p>{{ pageText('empty_no_capability', '当前账号暂无可用功能，可能因为角色权限未开通或工作台尚未配置。') }}</p>
        <div class="empty-actions">
          <button v-if="hasRoleSwitch" class="empty-btn" @click="goToMyWork">{{ pageText('action_switch_role', '切换角色') }}</button>
          <button class="empty-btn" @click="goHome">{{ pageText('action_back_home', '返回首页') }}</button>
          <button class="empty-btn secondary" @click="toggleEmptyHelp">
            {{ showEmptyHelp ? pageText('action_collapse_help', '收起帮助') : pageText('action_expand_help', '查看帮助') }}
          </button>
        </div>
        <p v-if="showEmptyHelp" class="empty-help">
          {{ pageText('empty_help_detail', '建议先点击“切换角色”确认当前角色；若仍无功能，请联系管理员开通角色权限或配置工作台目录。') }}
        </p>
      </template>
    </div>

    <div v-else-if="isHomeSectionEnabled('scene_groups') && isHomeSectionTag('scene_groups', 'div')" class="scene-groups" :class="homeSectionClass('scene_groups')" :style="homeSectionStyle('scene_groups')">
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
                <template v-for="(part, index) in highlightParts(entry.subtitle || pageText('entry_subtitle_empty', '无说明'))" :key="`sub-${entry.id}-${index}`">
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
import { readWorkspaceContext } from '../app/workspaceContext';
import { isDeliveryModeEnabled, isHudEnabled as resolveHudEnabled } from '../config/debug';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import PageRenderer from '../components/page/PageRenderer.vue';
import type { PageBlockActionEvent, PageOrchestrationContract } from '../app/pageOrchestration';

type EntryState = 'READY' | 'LOCKED' | 'PREVIEW';
type MetricLevel = 'green' | 'amber' | 'red';
type SuggestionStatus = 'urgent' | 'normal';
type SemanticTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral';
type SemanticProgress = 'overdue' | 'blocked' | 'pending' | 'running' | 'completed';
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
  tone?: SemanticTone;
  progress?: SemanticProgress;
  ready?: boolean;
  entryId: string;
};
type CoreMetric = {
  key: string;
  label: string;
  value: string;
  level: MetricLevel;
  tone?: SemanticTone;
  progress?: SemanticProgress;
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
  entryKey?: string;
};
type FilterChip = { key: string; label: string };

const router = useRouter();
const route = useRoute();
const session = useSessionStore();
const pageContract = usePageContract('home');
const pageTextByPageContract = pageContract.text;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const homeOrchestrationActions = computed<Record<string, unknown>>(() => {
  const actionSchema = workspacePageOrchestrationV1.value.action_schema;
  if (!actionSchema || typeof actionSchema !== 'object') return {};
  const actions = (actionSchema as Record<string, unknown>).actions;
  return actions && typeof actions === 'object' ? actions as Record<string, unknown> : {};
});
const pageText = (key: string, fallback: string) => pageTextByPageContract(key, fallback);
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
const isHudEnabled = computed(() => resolveHudEnabled(route));
const isDeliveryMode = computed(() => isDeliveryModeEnabled());
const isAdmin = computed(() => {
  const groups = session.user?.groups_xmlids || [];
  return groups.includes('base.group_system') || groups.includes('smart_construction_core.group_sc_cap_config_admin');
});
const heroQuickActions = computed(() => {
  const supported = new Set(['open_my_work', 'open_usage_analytics']);
  const actions = pageGlobalActions.value.filter((item) => {
    if (!supported.has(item.key)) return false;
    if (item.key === 'open_usage_analytics' && !isAdmin.value) return false;
    return true;
  });
  if (actions.length) return actions;
  const fallback = [{ key: 'open_my_work', label: homeLayoutText('hero.open_my_work_action', '我的工作'), intent: 'ui.contract' }];
  if (isAdmin.value) {
    fallback.push({ key: 'open_usage_analytics', label: homeLayoutText('hero.open_usage_action', '使用分析'), intent: 'ui.contract' });
  }
  return fallback;
});
const productFacts = computed(() => session.productFacts);
const roleSurface = computed(() => session.roleSurface);
const capabilityGroups = computed(() => session.capabilityGroups);
const workspaceHome = computed(() => (session.workspaceHome || {}) as Record<string, unknown>);
const workspaceLayout = computed(() => (
  workspaceHome.value.layout && typeof workspaceHome.value.layout === 'object'
    ? workspaceHome.value.layout as Record<string, unknown>
    : {}
));
const workspaceLayoutTexts = computed(() => (
  workspaceLayout.value.texts && typeof workspaceLayout.value.texts === 'object'
    ? workspaceLayout.value.texts as Record<string, unknown>
    : {}
));
const workspaceLayoutActions = computed(() => (
  workspaceLayout.value.actions && typeof workspaceLayout.value.actions === 'object'
    ? workspaceLayout.value.actions as Record<string, unknown>
    : {}
));
type HomeSectionTag = 'header' | 'section' | 'details' | 'div';
type HomeSectionConfig = { enabled: boolean; tag: HomeSectionTag | ''; open: boolean | null };

const workspaceLayoutSections = computed(() => {
  const source = Array.isArray(workspaceLayout.value.sections) ? workspaceLayout.value.sections : [];
  const map = new Map<string, HomeSectionConfig>();
  source.forEach((item) => {
    if (!item || typeof item !== 'object') return;
    const row = item as Record<string, unknown>;
    const key = asText(row.key);
    if (!key) return;
    const tagRaw = asText(row.tag).toLowerCase();
    const tag = (
      tagRaw === 'header'
      || tagRaw === 'section'
      || tagRaw === 'details'
      || tagRaw === 'div'
    ) ? tagRaw : '';
    map.set(key, {
      enabled: row.enabled === true,
      tag,
      open: typeof row.open === 'boolean' ? row.open : null,
    });
  });
  return map;
});
const workspacePageOrchestration = computed(() => (
  workspaceHome.value.page_orchestration && typeof workspaceHome.value.page_orchestration === 'object'
    ? workspaceHome.value.page_orchestration as Record<string, unknown>
    : {}
));
const workspacePageOrchestrationV1 = computed(() => (
  workspaceHome.value.page_orchestration_v1 && typeof workspaceHome.value.page_orchestration_v1 === 'object'
    ? workspaceHome.value.page_orchestration_v1 as Record<string, unknown>
    : {}
));
const workspacePageOrchestrationV1DataSources = computed(() => (
  workspacePageOrchestrationV1.value.data_sources && typeof workspacePageOrchestrationV1.value.data_sources === 'object'
    ? workspacePageOrchestrationV1.value.data_sources as Record<string, unknown>
    : {}
));
const homeOrchestrationContract = computed<PageOrchestrationContract>(() => {
  return workspacePageOrchestrationV1.value as PageOrchestrationContract;
});
const useUnifiedHomeRenderer = computed(() => {
  if (asText(route.query.legacy_home) === '1') return false;
  const contract = homeOrchestrationContract.value || {};
  const hasV1 = asText(contract.contract_version) === 'page_orchestration_v1';
  const isDashboard = asText(contract.scene_key) === 'portal.dashboard';
  const zones = Array.isArray(contract.zones) ? contract.zones : [];
  return hasV1 && isDashboard && zones.length > 0;
});
const orchestrationBlocks = computed(() => {
  const zones = Array.isArray(workspacePageOrchestrationV1.value.zones)
    ? workspacePageOrchestrationV1.value.zones
    : [];
  const hasV1Zones = zones.length > 0;
  const dataSources = workspacePageOrchestrationV1DataSources.value;
  const flattenedV1: Record<string, unknown>[] = [];
  zones.forEach((zone) => {
    if (!zone || typeof zone !== 'object') return;
    const zoneRow = zone as Record<string, unknown>;
    const zoneType = asText(zoneRow.zone_type);
    const blocks = Array.isArray(zoneRow.blocks) ? zoneRow.blocks : [];
    blocks.forEach((item) => {
      if (!item || typeof item !== 'object') return;
      const blockRow = item as Record<string, unknown>;
      const sectionKey = asText(blockRow.section_key);
      const dataSourceKey = asText(blockRow.data_source);
      if (!sectionKey || !dataSourceKey) return;
      const dataSource = dataSources[dataSourceKey];
      if (!dataSource || typeof dataSource !== 'object') return;
      const sourceType = asText((dataSource as Record<string, unknown>).source_type);
      if (!sourceType) return;
      flattenedV1.push({
        ...blockRow,
        zone: asText(blockRow.zone) || zoneType || 'support',
      });
    });
  });
  if (hasV1Zones) {
    return flattenedV1;
  }
  const legacy = Array.isArray(workspacePageOrchestration.value.blocks)
    ? workspacePageOrchestration.value.blocks
    : [];
  return legacy
    .map((item) => (item && typeof item === 'object' ? item as Record<string, unknown> : null))
    .filter((item): item is Record<string, unknown> => Boolean(item));
});
const roleVariantCode = computed(() => {
  const roleVariant = workspaceHome.value.role_variant;
  if (roleVariant && typeof roleVariant === 'object') {
    const roleCode = asText((roleVariant as Record<string, unknown>).role_code);
    if (roleCode) return roleCode;
  }
  const orchestrationPage = workspacePageOrchestrationV1.value.page;
  if (orchestrationPage && typeof orchestrationPage === 'object') {
    return asText((orchestrationPage as Record<string, unknown>).role_code);
  }
  return '';
});
const orchestrationSectionOrderMap = computed(() => {
  const map = new Map<string, number>();
  orchestrationBlocks.value.forEach((block, idx) => {
    const visible = typeof block.visible === 'boolean' ? block.visible : true;
    if (!visible) return;
    const sourcePath = asText(block.source_path);
    const sectionKey = asText(block.section_key) || (sourcePath ? sourcePath.split('.')[0] || '' : '');
    if (!sectionKey || map.has(sectionKey)) return;
    const orderRaw = Number(block.order);
    const order = Number.isFinite(orderRaw) && orderRaw > 0 ? Math.trunc(orderRaw) : idx + 1;
    map.set(sectionKey, order);
  });
  return map;
});
const orchestrationSectionSemanticMap = computed(() => {
  const map = new Map<string, { zone: string; focus: boolean; tone: SemanticTone; progress: SemanticProgress }>();
  orchestrationBlocks.value.forEach((block) => {
    const visible = typeof block.visible === 'boolean' ? block.visible : true;
    if (!visible) return;
    const sourcePath = asText(block.source_path);
    const sectionKey = asText(block.section_key) || (sourcePath ? sourcePath.split('.')[0] || '' : '');
    if (!sectionKey || map.has(sectionKey)) return;
    map.set(sectionKey, {
      zone: asText(block.zone) || 'support',
      focus: block.focus === true,
      tone: normalizeTone(block.tone, 'neutral'),
      progress: normalizeProgress(block.progress, 'running'),
    });
  });
  return map;
});
const homeSectionOrderMap = computed(() => {
  const source = Array.isArray(workspaceLayout.value.sections) ? workspaceLayout.value.sections : [];
  const map = new Map<string, number>();
  source.forEach((item, idx) => {
    if (!item || typeof item !== 'object') return;
    const key = asText((item as Record<string, unknown>).key);
    if (!key || map.has(key)) return;
    const orchestrationOrder = orchestrationSectionOrderMap.value.get(key);
    map.set(key, orchestrationOrder || idx + 1);
  });
  orchestrationSectionOrderMap.value.forEach((order, key) => {
    if (!map.has(key)) {
      map.set(key, order);
    }
  });
  return map;
});
const workspaceHero = computed(() => (workspaceHome.value.hero && typeof workspaceHome.value.hero === 'object'
  ? workspaceHome.value.hero as Record<string, unknown>
  : {}));
const heroTitle = computed(() => asText(workspaceHero.value.title) || pageText('title', '工作台'));
const heroLead = computed(() => asText(workspaceHero.value.lead) || pageText('hero_lead', '围绕项目经营、风险与审批，优先处理今天最关键事项。'));
const heroProductTags = computed(() => {
  const raw = Array.isArray(workspaceHero.value.product_tags) ? workspaceHero.value.product_tags : [];
  return raw.map((item) => asText(item)).filter(Boolean);
});
const dataUpdatedAt = computed(() => asText(workspaceHero.value.updated_at) || '--:--');
const partialDataNotice = computed(() => asText(workspaceHero.value.status_notice));
const partialDataDetailLine = computed(() => asText(workspaceHero.value.status_detail));
const hasRoleSwitch = computed(() => Object.keys(session.roleSurfaceMap || {}).length > 1);
const roleLabel = computed(() => {
  const raw = asText(roleSurface.value?.role_label) || asText(roleSurface.value?.role_code);
  const normalized = raw.toLowerCase();
  if (!raw) return pageText('role_fallback_owner', '负责人');
  if (normalized === 'executive') return pageText('role_label_executive', '高管');
  if (normalized === 'owner') return pageText('role_label_owner', '负责人');
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
  const scoreMap = capabilityGroupScoreMap.value;
  return capabilityGroups.value
    .slice()
    .sort((a, b) => a.sequence - b.sequence)
    .filter((group) => !isDeliveryMode.value || (scoreMap.get(group.key) || 0) >= 0)
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
const capabilityGroupScoreMap = computed(() => {
  const map = new Map<string, number>();
  capabilityGroups.value.forEach((group) => {
    const readyCount = Number(group.state_counts?.READY || 0);
    const allowCount = Number(group.capability_state_counts?.allow || 0);
    map.set(group.key, readyCount * 2 + allowCount);
  });
  return map;
});
const licenseLevelLabel = computed(() => String(productFacts.value?.license?.level || '').trim() || 'unknown');
const bundleNameLabel = computed(() => String(productFacts.value?.bundle?.name || '').trim() || 'default');
const defaultSceneKey = computed(() => {
  const first = session.scenes.find((scene) => asText(scene.key));
  return first ? asText(first.key) : '';
});
const roleLandingScene = computed(() => asText(roleSurface.value?.landing_scene_key) || defaultSceneKey.value);
const roleLandingLabel = computed(() => sceneTitleMap.value.get(roleLandingScene.value) || pageText('role_landing_fallback', '工作台首页'));
const internalTileCount = computed(() => {
  let count = 0;
  session.scenes.forEach((scene) => {
    const sceneKey = asText(scene.key);
    if (!sceneKey) return;
    const tiles = Array.isArray(scene.tiles) ? scene.tiles : [];
    tiles.forEach((tile, tileIndex) => {
      const key = asText(tile.key);
      if (!key) return;
      const title = asText((tile as { title?: string }).title) || `${pageText('tile_title_fallback_prefix', '功能 ')}${tileIndex + 1}`;
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

function homeLayoutText(key: string, fallback: string) {
  const value = asText(workspaceLayoutTexts.value[key]);
  return value || fallback;
}

function isHomeSectionEnabled(key: string) {
  const sectionMap = workspaceLayoutSections.value;
  if (!sectionMap.size) return true;
  return sectionMap.get(key)?.enabled === true;
}

function isHomeSectionTag(key: string, expected: HomeSectionTag) {
  const sectionMap = workspaceLayoutSections.value;
  if (!sectionMap.size) return true;
  return sectionMap.get(key)?.tag === expected;
}

function isHomeSectionOpenDefault(key: string, fallback = false) {
  const sectionMap = workspaceLayoutSections.value;
  if (!sectionMap.size) return fallback;
  return sectionMap.get(key)?.open === true;
}

function homeSectionStyle(key: string) {
  const order = homeSectionOrderMap.value.get(key);
  if (!order) return {};
  return { order: String(order) };
}

function homeSectionClass(key: string) {
  const semantic = orchestrationSectionSemanticMap.value.get(key);
  if (!semantic) return [];
  return [
    `zone-${semantic.zone || 'support'}`,
    `tone-${semantic.tone}`,
    `progress-${semantic.progress}`,
    semantic.focus ? 'is-focus' : 'is-secondary',
  ];
}

function asText(value: unknown) {
  const text = String(value ?? '').trim();
  if (!text || text.toLowerCase() === 'undefined' || text.toLowerCase() === 'null') return '';
  return text;
}

function normalizeTone(value: unknown, fallback: SemanticTone = 'neutral'): SemanticTone {
  const tone = asText(value).toLowerCase();
  if (tone === 'success' || tone === 'warning' || tone === 'danger' || tone === 'info' || tone === 'neutral') {
    return tone;
  }
  return fallback;
}

function normalizeProgress(value: unknown, fallback: SemanticProgress = 'running'): SemanticProgress {
  const progress = asText(value).toLowerCase();
  if (
    progress === 'overdue'
    || progress === 'blocked'
    || progress === 'pending'
    || progress === 'running'
    || progress === 'completed'
  ) {
    return progress;
  }
  return fallback;
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
  if (!key) return pageText('scene_title_uncategorized', '未分类模块');
  if (isHudEnabled.value) {
    return `${pageText('scene_title_uncategorized_with_key_prefix', '未分类模块（')}${key}${pageText('scene_title_uncategorized_with_key_suffix', ')')}`;
  }
  return pageText('scene_title_uncategorized', '未分类模块');
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
        (isHudEnabled.value ? key : `${pageText('tile_title_fallback_prefix', '功能 ')}${sceneIndex + 1}-${tileIndex + 1}`);
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

function includesAny(value: string, keywords: string[]) {
  const text = String(value || '').toLowerCase();
  if (!text) return false;
  return keywords.some((item) => text.includes(String(item || '').toLowerCase()));
}

function keywordList(key: string, fallbackCsv: string) {
  return String(pageText(key, fallbackCsv) || '')
    .split(',')
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

const coreMetrics = computed<CoreMetric[]>(() => {
  const source = Array.isArray(workspaceHome.value.metrics) ? workspaceHome.value.metrics : [];
  return source
    .map((item, idx) => {
      const row = (item && typeof item === 'object') ? item as Record<string, unknown> : {};
      const levelRaw = asText(row.level).toLowerCase();
      const level: MetricLevel = levelRaw === 'red' || levelRaw === 'amber' ? levelRaw : 'green';
      return {
        key: asText(row.key) || `metric-${idx + 1}`,
        label: asText(row.label) || `${pageText('metric_title_fallback_prefix', '指标 ')}${idx + 1}`,
        value: asText(row.value) || '0',
        level,
        tone: normalizeTone(row.tone),
        progress: normalizeProgress(row.progress),
        delta: asText(row.delta) || '',
        hint: asText(row.hint) || '',
      };
    })
    .filter((item) => item.label);
});

const concreteTodos = computed<SuggestionItem[]>(() => {
  const source = Array.isArray(workspaceHome.value.today_actions) ? workspaceHome.value.today_actions : [];
  return source.map((item, idx) => {
    const row = (item && typeof item === 'object') ? item as Record<string, unknown> : {};
    const entryKey = asText(row.entry_key);
    const sceneKey = asText(row.scene_key);
    const matched = entries.value.find((entry) => (entryKey && entry.key === entryKey) || (sceneKey && entry.sceneKey === sceneKey));
    const statusRaw = asText(row.status).toLowerCase();
    return {
      id: asText(row.id) || `todo-${idx + 1}`,
      title: asText(row.title) || `${pageText('todo_title_fallback_prefix', '待办 ')}${idx + 1}`,
      description: asText(row.description) || pageText('todo_desc_fallback', '点击进入处理'),
      count: Number(row.count || 0),
      status: statusRaw === 'urgent' ? 'urgent' : 'normal',
      tone: normalizeTone(row.tone, statusRaw === 'urgent' ? 'danger' : 'info'),
      progress: normalizeProgress(row.progress, 'pending'),
      ready: matched ? matched.state === 'READY' : Boolean(row.ready),
      entryId: matched?.id || '',
    };
  });
});

const riskBuckets = computed(() => {
  const risk = (workspaceHome.value.risk && typeof workspaceHome.value.risk === 'object')
    ? workspaceHome.value.risk as Record<string, unknown>
    : {};
  const buckets = (risk.buckets && typeof risk.buckets === 'object')
    ? risk.buckets as Record<string, unknown>
    : {};
  return {
    red: Number(buckets.red || 0),
    amber: Number(buckets.amber || 0),
    green: Number(buckets.green || 0),
  };
});

const riskTrend = computed(() => {
  const risk = (workspaceHome.value.risk && typeof workspaceHome.value.risk === 'object')
    ? workspaceHome.value.risk as Record<string, unknown>
    : {};
  const source = Array.isArray(risk.trend) ? risk.trend : [];
  return source.map((item, idx) => {
    const row = (item && typeof item === 'object') ? item as Record<string, unknown> : {};
    return {
      label: asText(row.label) || `${pageText('risk_trend_label_prefix', 'T-')}${idx + 1}`,
      value: Number(row.value || 0),
      percent: Number(row.percent || 0),
    };
  });
});

const riskSummaryLine = computed(() => {
  const risk = (workspaceHome.value.risk && typeof workspaceHome.value.risk === 'object')
    ? workspaceHome.value.risk as Record<string, unknown>
    : {};
  return asText(risk.summary) || pageText('risk_summary_fallback', '当前未出现严重风险，建议保持日常巡检节奏。');
});

const riskActionItems = computed<RiskActionItem[]>(() => {
  const risk = (workspaceHome.value.risk && typeof workspaceHome.value.risk === 'object')
    ? workspaceHome.value.risk as Record<string, unknown>
    : {};
  const source = Array.isArray(risk.actions) ? risk.actions : [];
  return source.map((item, idx) => {
    const row = (item && typeof item === 'object') ? item as Record<string, unknown> : {};
    return {
      id: asText(row.id) || `risk-${idx + 1}`,
      title: asText(row.title) || `${pageText('risk_action_title_fallback_prefix', '风险事项 ')}${idx + 1}`,
      description: asText(row.description) || '',
      entryKey: asText(row.entry_key),
      sceneKey: asText(row.scene_key),
      path: asText(row.path),
      query: normalizeContextQuery(row.query),
    };
  });
});

const riskSources = computed(() => {
  const risk = (workspaceHome.value.risk && typeof workspaceHome.value.risk === 'object')
    ? workspaceHome.value.risk as Record<string, unknown>
    : {};
  const source = Array.isArray(risk.sources) ? risk.sources : [];
  return source.map((item, idx) => {
    const row = (item && typeof item === 'object') ? item as Record<string, unknown> : {};
    return {
      label: asText(row.label) || `${pageText('risk_source_label_fallback_prefix', '来源 ')}${idx + 1}`,
      count: Number(row.count || 0),
    };
  });
});

const opsBars = computed(() => {
  const ops = (workspaceHome.value.ops && typeof workspaceHome.value.ops === 'object')
    ? workspaceHome.value.ops as Record<string, unknown>
    : {};
  const bars = (ops.bars && typeof ops.bars === 'object') ? ops.bars as Record<string, unknown> : {};
  return {
    contract: Number(bars.contract || 100),
    output: Number(bars.output || 0),
  };
});

const opsKpi = computed(() => {
  const ops = (workspaceHome.value.ops && typeof workspaceHome.value.ops === 'object')
    ? workspaceHome.value.ops as Record<string, unknown>
    : {};
  const kpi = (ops.kpi && typeof ops.kpi === 'object') ? ops.kpi as Record<string, unknown> : {};
  return {
    costRate: Number(kpi.cost_rate || 0),
    paymentRate: Number(kpi.payment_rate || 0),
    costRateDelta: Number(kpi.cost_rate_delta || 0),
    paymentRateDelta: Number(kpi.payment_rate_delta || 0),
    outputTrendDelta: Number(kpi.output_trend_delta || 0),
  };
});

function levelLabel(level: MetricLevel) {
  if (level === 'red') return pageText('level_red', '严重');
  if (level === 'amber') return pageText('level_amber', '关注');
  return pageText('level_green', '正常');
}

function trendText(delta: number) {
  const value = Number(delta || 0);
  if (value > 0) return `${pageText('trend_up_prefix', '↑ ')}${Math.abs(value)}%`;
  if (value < 0) return `${pageText('trend_down_prefix', '↓ ')}${Math.abs(value)}%`;
  return pageText('trend_flat', '→ 0%');
}

function todoActionLabel(title: string) {
  const text = String(title || '').toLowerCase();
  if (includesAny(text, keywordList('todo_keywords_approval', '付款,支付,approval,审批'))) {
    return homeLayoutText('actions.todo_approval', pageText('todo_label_approval', '审核付款申请'));
  }
  if (includesAny(text, keywordList('todo_keywords_contract', '合同,contract'))) {
    return homeLayoutText('actions.todo_contract', pageText('todo_label_contract', '查看合同异常'));
  }
  if (includesAny(text, keywordList('todo_keywords_risk', '风险,risk'))) {
    return homeLayoutText('actions.todo_risk', pageText('todo_label_risk', '处理风险事项'));
  }
  if (includesAny(text, keywordList('todo_keywords_change', '变更,change'))) {
    return homeLayoutText('actions.todo_change', pageText('todo_label_change', '确认变更事项'));
  }
  if (includesAny(text, keywordList('todo_keywords_overdue', '逾期,任务,todo'))) {
    return homeLayoutText('actions.todo_overdue', pageText('todo_label_overdue', '处理逾期任务'));
  }
  return asText(workspaceLayoutActions.value.todo_default) || homeLayoutText('actions.todo_default', pageText('todo_label_default', '查看详情'));
}

const systemAdvice = computed<AdviceItem[]>(() => {
  const source = Array.isArray(workspaceHome.value.advice) ? workspaceHome.value.advice : [];
  return source.map((item, idx) => {
    const row = (item && typeof item === 'object') ? item as Record<string, unknown> : {};
    const levelRaw = asText(row.level).toLowerCase();
    return {
      id: asText(row.id) || `advice-${idx + 1}`,
      level: levelRaw === 'red' || levelRaw === 'amber' ? levelRaw : 'green',
      title: asText(row.title) || `${pageText('advice_title_fallback_prefix', '建议 ')}${idx + 1}`,
      description: asText(row.description),
      actionLabel: asText(row.action_label),
      actionEntryId: asText(row.entry_id),
      actionPath: asText(row.path),
      actionQuery: normalizeContextQuery(row.query),
    };
  });
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
  if (path === '/bundle-dashboard') {
    openBundleDashboard();
    return;
  }
  router.push({ path, query: item.actionQuery || workspaceContextQuery.value }).catch(() => {});
}

function openBundleDashboard() {
  void trackUsageEvent('workspace.nav_click', {
    target: 'bundle_dashboard',
    from: 'workspace.home',
    license_level: licenseLevelLabel.value,
    bundle_name: bundleNameLabel.value,
  }).catch(() => {});
  router.push({ path: '/my-work', query: workspaceContextQuery.value }).catch(() => {});
}

function openRiskAction(item: RiskActionItem, action: 'detail' | 'assign' | 'close' | 'approve') {
  void trackUsageEvent('workspace.risk_action_click', { item_id: item.id, action }).catch(() => {});
  if (item.entryKey) {
    const byKey = entries.value.find((candidate) => candidate.key === item.entryKey && candidate.state === 'READY');
    if (byKey) {
      void openScene(byKey);
      return;
    }
  }
  if (item.sceneKey) {
    const entry = entries.value.find((candidate) => candidate.sceneKey === item.sceneKey && candidate.state === 'READY');
    if (entry) {
      void openScene(entry);
      return;
    }
  }
  router.push({ path: item.path || '/my-work', query: item.query || { section: 'todo' } }).catch(() => {});
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
  const parts = [
    `${pageText('result_summary_prefix', '当前显示 ')}${filteredEntries.value.length}${pageText('result_summary_middle', ' / ')}${entries.value.length}${pageText('result_summary_suffix', ' 项功能')}`,
  ];
  if (stateFilter.value !== 'ALL') parts.push(`${pageText('result_summary_state_prefix', '状态：')}${stateLabel(stateFilter.value)}`);
  if (!isDeliveryMode.value && capabilityStateFilter.value !== 'ALL') {
    parts.push(`${pageText('result_summary_capability_state_prefix', '功能语义：')}${capabilityStateLabel(capabilityStateFilter.value)}`);
  }
  if (lockReasonFilter.value !== 'ALL') parts.push(`${pageText('result_summary_reason_prefix', '原因：')}${lockReasonLabel(lockReasonFilter.value)}`);
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
  if (keyword) chips.push({ key: 'search', label: `${pageText('chip_search_prefix', '搜索：')}${keyword}` });
  if (readyOnly.value) chips.push({ key: 'ready-only', label: pageText('chip_ready_only', '仅显示可进入') });
  if (stateFilter.value !== 'ALL') chips.push({ key: 'state', label: `${pageText('chip_state_prefix', '状态：')}${stateLabel(stateFilter.value)}` });
  if (!isDeliveryMode.value && capabilityStateFilter.value !== 'ALL') {
    chips.push({
      key: 'capability-state',
      label: `${pageText('chip_capability_state_prefix', '功能语义：')}${capabilityStateLabel(capabilityStateFilter.value)}`,
    });
  }
  if (lockReasonFilter.value !== 'ALL') {
    chips.push({ key: 'reason', label: `${pageText('chip_reason_prefix', '锁定原因：')}${lockReasonLabel(lockReasonFilter.value)}` });
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
    const bucketKey = entry.groupKey || entry.sceneKey;
    const resolvedBucketKey = isDeliveryMode.value ? entry.sceneKey : bucketKey;
    const bucketTitle = isDeliveryMode.value ? entry.sceneTitle : (entry.groupLabel || entry.sceneTitle);
    const current = map.get(resolvedBucketKey);
    if (current) {
      current.items.push(entry);
      const scenes = sceneSetMap.get(resolvedBucketKey) || new Set<string>();
      scenes.add(entry.sceneTitle);
      sceneSetMap.set(resolvedBucketKey, scenes);
      return;
    }
    map.set(resolvedBucketKey, {
      sceneKey: resolvedBucketKey,
      sceneTitle: bucketTitle,
      sceneSummary: '',
      items: [entry],
    });
    sceneSetMap.set(resolvedBucketKey, new Set([entry.sceneTitle]));
  });
  const grouped = Array.from(map.values())
    .map((group) => {
      const scenes = Array.from(sceneSetMap.get(group.sceneKey) || []);
      return {
        ...group,
        sceneSummary: scenes.length > 1
          ? `${pageText('scene_summary_prefix', '覆盖场景：')}${scenes.slice(0, 3).join('、')}${scenes.length > 3 ? pageText('scene_summary_more', '…') : ''}`
          : '',
      };
    })
    .sort((a, b) => a.sceneTitle.localeCompare(b.sceneTitle));
  if (!recentItems.length) return grouped;
  return [{ sceneKey: '__recent__', sceneTitle: pageText('recent_group_title', '最近使用'), sceneSummary: '', items: recentItems }, ...grouped];
});
const hasRecentGroup = computed(() => groupedEntries.value.some((group) => group.sceneKey === '__recent__'));
const homeOrchestrationDatasets = computed<Record<string, unknown>>(() => {
  const readyEntries = entries.value
    .filter((entry) => entry.state === 'READY')
    .slice(0, 12)
    .map((entry) => ({
      id: entry.id,
      key: entry.key,
      title: entry.title,
      hint: entry.subtitle,
      scene_key: entry.sceneKey,
      route: entry.route,
      action_id: entry.targetActionId,
      menu_id: entry.targetMenuId,
      entry_id: entry.id,
    }));
  const capabilityEntries = capabilityGroupCards.value
    .slice(0, 8)
    .map((group) => ({
      id: group.key,
      key: group.key,
      title: group.label,
      hint: `${homeLayoutText('group_overview.capability_count_prefix', '功能数')} ${group.capabilityCount}`,
      action_key: '',
    }));
  const riskAlerts = riskActionItems.value.slice(0, 10).map((item) => ({
    id: item.id,
    title: item.title,
    description: item.description,
    tone: 'danger',
    scene_key: item.sceneKey,
    path: item.path,
    query: item.query,
    entry_key: item.entryKey,
  }));
  return {
    ds_hero: {
      title: heroTitle.value,
      lead: heroLead.value,
      role_label: roleLabel.value,
      landing_label: roleLandingLabel.value,
      updated_at: dataUpdatedAt.value,
      status_notice: partialDataNotice.value,
      status_detail: partialDataDetailLine.value,
    },
    ds_metrics: coreMetrics.value,
    ds_today_todos: concreteTodos.value.map((item) => ({
      id: item.id,
      title: item.title,
      description: item.description,
      tone: item.tone || 'warning',
      action_label: todoActionLabel(item.title),
      entry_id: item.entryId,
      action_key: 'open_scene',
    })),
    ds_risk_alerts: riskAlerts,
    ds_ops_progress: {
      bars: opsBars.value,
      kpi: opsKpi.value,
      summary: riskSummaryLine.value,
    },
    ds_scene_groups: readyEntries,
    ds_capability_groups: capabilityEntries,
    ds_advice: systemAdvice.value,
    ds_filters: {
      result_summary: resultSummaryText.value,
      active_filters: activeFilterChips.value,
    },
  };
});

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
  if (code === 'PERMISSION_DENIED') return pageText('lock_reason_permission_denied', '权限不足');
  if (code === 'FEATURE_DISABLED') return pageText('lock_reason_feature_disabled', '订阅未开通');
  if (code === 'ROLE_SCOPE_MISMATCH') return pageText('lock_reason_role_scope_mismatch', '角色范围不匹配');
  if (code === 'CAPABILITY_SCOPE_MISSING') return pageText('lock_reason_scope_missing', '缺少前置条件');
  if (code === 'CAPABILITY_SCOPE_CYCLE') return pageText('lock_reason_scope_cycle', '功能依赖异常');
  if (code === 'COMING_SOON') return pageText('lock_reason_coming_soon', '功能建设中');
  if (code === 'PENDING_APPROVAL') return pageText('lock_reason_waiting_open', '待审批开放');
  return pageText('lock_reason_default', '当前不可用');
}

function capabilityStateLabel(state: string) {
  const normalized = String(state || '').toLowerCase();
  if (normalized === 'readonly') return pageText('capability_state_readonly', '只读');
  if (normalized === 'deny') return pageText('capability_state_deny', '禁止');
  if (normalized === 'pending') return pageText('capability_state_pending', '待开放');
  if (normalized === 'coming_soon') return pageText('capability_state_coming_soon', '建设中');
  return pageText('capability_state_allow', '可用');
}

function stateLabel(state: EntryState) {
  if (state === 'READY') return pageText('state_ready', '可进入');
  if (state === 'LOCKED') return pageText('state_locked', '暂不可用');
  return pageText('state_preview', '即将开放');
}

function canEnter(entry: CapabilityEntry) {
  return entry.state === 'READY';
}

function actionLabel(entry: CapabilityEntry) {
  if (entry.state === 'LOCKED') return pageText('action_enter_disabled', '暂不可用');
  if (entry.state === 'PREVIEW') return pageText('action_enter_preview', '即将开放');
  if (entry.capabilityState === 'readonly') return pageText('action_enter_readonly', '只读进入');
  const mergeText = `${entry.title} ${entry.subtitle} ${entry.key} ${entry.sceneKey}`.toLowerCase();
  if (includesAny(mergeText, keywordList('action_enter_keywords_approval', 'payment,付款,支付,approval,审批'))) return pageText('action_enter_approval', '审核付款申请');
  if (includesAny(mergeText, keywordList('action_enter_keywords_contract', 'contract,合同'))) return pageText('action_enter_contract', '查看合同异常');
  if (includesAny(mergeText, keywordList('action_enter_keywords_risk', 'risk,风险,预警'))) return pageText('action_enter_risk', '处理风险事项');
  if (includesAny(mergeText, keywordList('action_enter_keywords_change', 'change,变更'))) return pageText('action_enter_change', '确认变更事项');
  if (includesAny(mergeText, keywordList('action_enter_keywords_task', 'task,任务,todo,待办'))) return pageText('action_enter_task', '处理任务');
  return pageText('action_enter_default', '进入处理');
}

function orchestrationActionIntent(key: string, fallback = 'ui.contract') {
  const row = homeOrchestrationActions.value[key];
  if (!row || typeof row !== 'object') return fallback;
  const intent = asText((row as Record<string, unknown>).intent);
  return intent || fallback;
}

function orchestrationActionTarget(key: string) {
  const row = homeOrchestrationActions.value[key];
  if (!row || typeof row !== 'object') return {};
  const target = (row as Record<string, unknown>).target;
  return target && typeof target === 'object' ? target as Record<string, unknown> : {};
}

function findEntryForActionItem(item: Record<string, unknown>) {
  const entryId = asText(item.entry_id || item.entryId);
  if (entryId) {
    const byId = entries.value.find((entry) => entry.id === entryId);
    if (byId) return byId;
  }
  const entryKey = asText(item.entry_key || item.entryKey || item.key);
  if (entryKey) {
    const byKey = entries.value.find((entry) => entry.key === entryKey && entry.state === 'READY');
    if (byKey) return byKey;
  }
  const sceneKey = asText(item.scene_key || item.sceneKey);
  if (sceneKey) {
    const byScene = entries.value.find((entry) => entry.sceneKey === sceneKey && entry.state === 'READY');
    if (byScene) return byScene;
  }
  return null;
}

async function handleHomeBlockAction(event: PageBlockActionEvent) {
  const actionKey = asText(event.actionKey);
  const item = event.item && typeof event.item === 'object' ? event.item as Record<string, unknown> : {};
  const linkedEntry = findEntryForActionItem(item);
  if (linkedEntry) {
    await openScene(linkedEntry);
    return;
  }

  const path = asText(item.path || item.route);
  if (path) {
    await router.push({ path, query: normalizeContextQuery(item.query) || workspaceContextQuery.value });
    return;
  }

  const handled = await executePageContractAction({
    actionKey,
    router,
    actionIntent: orchestrationActionIntent,
    actionTarget: orchestrationActionTarget,
    query: workspaceContextQuery.value,
    onRefresh: async () => {
      await session.bootstrap();
    },
    onFallback: async (key) => {
      if (key === 'open_my_work') {
        goToMyWork();
        return true;
      }
      if (key === 'open_landing') {
        openRoleLanding();
        return true;
      }
      if (key === 'open_risk_dashboard') {
        await router.push({ path: '/s/portal.lifecycle', query: workspaceContextQuery.value });
        return true;
      }
      if (key === 'open_scene') {
        const sceneKey = asText(item.scene_key || item.sceneKey);
        if (sceneKey) {
          await router.push({ path: `/s/${sceneKey}`, query: workspaceContextQuery.value });
          return true;
        }
      }
      return false;
    },
  });

  if (!handled && actionKey === 'refresh') {
    await session.bootstrap();
  }
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

async function executeHeroAction(actionKey: string) {
  void trackUsageEvent('workspace.nav_click', {
    target: actionKey,
    from: 'workspace.home',
  }).catch(() => {});
  const handled = await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: workspaceContextQuery.value,
    onFallback: async (key) => {
      if (key === 'open_my_work') {
        router.push({ path: '/my-work', query: workspaceContextQuery.value }).catch(() => {});
        return true;
      }
      if (key === 'open_usage_analytics' && isAdmin.value) {
        router.push({ path: '/admin/usage-analytics' }).catch(() => {});
        return true;
      }
      return false;
    },
  });
  if (!handled && actionKey === 'open_my_work') {
    router.push({ path: '/my-work', query: workspaceContextQuery.value }).catch(() => {});
  }
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
  const message = asText((error as { message?: unknown })?.message) || pageText('enter_error_message_fallback', '功能入口暂时不可用');
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
  if (code === 'PERMISSION_DENIED') return pageText('enter_error_hint_permission_denied', '请联系管理员开通对应权限后重试。');
  if (code === 'ROUTE_NOT_FOUND') return pageText('enter_error_hint_route_not_found', '入口配置异常，请稍后重试或联系管理员。');
  if (code === 'TIMEOUT') return pageText('enter_error_hint_timeout', '网络连接超时，请检查网络后点击重试。');
  return pageText('enter_error_hint_default', '请稍后重试；如果问题持续，请联系管理员。');
}

onMounted(() => {
  void trackUsageEvent('workspace.view', {
    role_key: asText(roleSurface.value?.role_code) || 'unknown',
    landing_scene_key: roleLandingScene.value,
  }).catch(() => {});
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

.is-focus {
  box-shadow: 0 0 0 2px rgba(42, 146, 255, 0.28);
}

.is-secondary {
  opacity: 0.98;
}

.zone-primary {
  border-left: 3px solid #2a92ff;
}

.zone-analysis {
  border-left: 3px solid #6b7b8c;
}

.zone-support {
  border-left: 3px solid #93a1b0;
}
</style>
