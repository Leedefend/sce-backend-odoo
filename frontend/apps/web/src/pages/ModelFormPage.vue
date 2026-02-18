<template>
  <main class="page">
    <header class="header">
      <div>
        <h1>{{ title }}</h1>
        <p class="meta">Model: {{ model }} · ID: {{ recordIdDisplay }}</p>
        <p v-if="contractMetaLine" class="meta">{{ contractMetaLine }}</p>
        <p v-if="actionFeedback" class="action-feedback" :class="{ error: !actionFeedback.success }">
          {{ actionFeedback.message }} <span class="code">({{ actionFeedback.reasonCode }})</span>
        </p>
        <p v-if="actionFeedback && actionFeedback.traceId" class="action-evidence">
          trace: <code>{{ actionFeedback.traceId }}</code>
          <span v-if="actionFeedback.requestId"> · request: <code>{{ actionFeedback.requestId }}</code></span>
          <span v-if="actionFeedback.replayed"> · replayed</span>
          <button type="button" class="evidence-copy" @click="copyActionEvidence">复制证据</button>
          <button type="button" class="evidence-copy" @click="copyLatestExecutionBundle">复制执行包</button>
          <button type="button" class="evidence-copy" @click="exportLatestExecutionBundle">导出执行包</button>
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
          v-for="action in contractHeaderActions"
          :key="`contract-open-${action.key}`"
          class="action secondary"
          :disabled="saving || loading || !action.actionId"
          :title="action.description"
          @click="openContractAction(action)"
        >
          {{ action.label }}
        </button>
        <button
          v-for="action in displayedSemanticActionButtons"
          :key="`semantic-${action.key}`"
          :disabled="!recordId || saving || loading || actionBusy || !action.allowed"
          class="action secondary"
          :class="{ primary: action.key === primaryActionKey, caution: isCautionAction(action) }"
          :title="semanticActionTooltip(action)"
          @click="runSemanticAction(action)"
        >
          {{ actionBusy && actionBusyKey === action.key ? `${action.label} · 执行中...` : action.label }}
        </button>
        <button :disabled="!lastSemanticAction || actionBusy || loading" class="action secondary" @click="rerunLastSemanticAction">
          {{ retryLastActionLabel }}
        </button>
        <button :disabled="saving || !canSaveByContract" @click="save">{{ saving ? 'Saving...' : 'Save' }}</button>
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
          aria-label="搜索动作或原因码"
        />
        <button type="button" class="stats-refresh" @click="resetActionPanelPrefs">重置面板</button>
      </section>
      <section v-if="blockedReasonCodes.length" class="semantic-action-reason-chips">
        <span>阻塞原因:</span>
        <button
          v-for="reason in blockedReasonCodes"
          :key="`blocked-reason-${reason}`"
          type="button"
          class="reason-chip"
          @click="applyBlockedReasonFilter(reason)"
        >
          {{ reason }}
        </button>
      </section>
      <section v-if="semanticActionButtons.length" class="semantic-action-stats">
        <span :class="['readiness-badge', readinessLevelClass]">就绪度: {{ actionReadinessScore }}%</span>
        <span>主动作: {{ primaryActionKey || '-' }}</span>
        <span>当前筛选: {{ actionFilterMode }}</span>
        <span>显示中: {{ displayedSemanticActionButtons.length }}</span>
        <span v-if="actionHistory.length">近期成功率: {{ actionHistorySuccessRate }}%</span>
        <span :class="{ stale: actionSurfaceIsStale }">刷新: {{ actionSurfaceAgeLabel }}</span>
        <span v-if="actionSurfaceRefreshPaused" class="stale">自动刷新已暂停（页面非激活）</span>
        <span v-if="actionSurfaceLoadedAtText">刷新时刻: {{ actionSurfaceLoadedAtText }}</span>
        <span v-if="allowedActionLabels.length">可执行: {{ allowedActionLabels.join(' / ') }}</span>
        <span v-if="latestFailureReason">最近失败: {{ latestFailureReason }}</span>
        <span v-if="blockedTopReasons.length">阻塞TOP: {{ blockedTopReasons.join(' / ') }}</span>
        <button type="button" class="stats-refresh" title="复制阻塞动作文本" aria-label="复制阻塞动作文本" @click="copyBlockedReasonsText">复制阻塞文本</button>
        <button type="button" class="stats-refresh" title="复制可执行动作文本" aria-label="复制可执行动作文本" @click="copyAllowedActionsText">复制可执行文本</button>
        <button type="button" class="stats-refresh" title="复制动作统计快照" aria-label="复制动作统计快照" @click="copyActionStats">复制统计</button>
        <button type="button" class="stats-refresh" title="导出可执行动作摘要" aria-label="导出可执行动作摘要" @click="exportAllowedSummary">导出可执行</button>
        <button type="button" class="stats-refresh" title="导出阻塞动作摘要" aria-label="导出阻塞动作摘要" @click="exportBlockedSummary">导出阻塞</button>
        <button type="button" class="stats-refresh" title="刷新动作面" aria-label="刷新动作面" @click="loadPaymentActionSurface">刷新动作面</button>
        <button
          type="button"
          class="stats-refresh"
          :disabled="!primaryAllowedAction || actionBusy || loading"
          title="执行当前主动作"
          aria-label="执行当前主动作"
          @click="primaryAllowedAction && runSemanticAction(primaryAllowedAction)"
        >
          执行主动作
        </button>
        <button type="button" class="stats-refresh" title="复制动作面JSON" aria-label="复制动作面JSON" @click="copyActionSurface">复制动作面</button>
        <button type="button" class="stats-refresh" title="复制主动作说明" aria-label="复制主动作说明" @click="copyPrimaryActionBrief">复制主动作说明</button>
        <button type="button" class="stats-refresh" title="导出动作面JSON" aria-label="导出动作面JSON" @click="exportActionSurface">导出动作面</button>
        <label class="auto-refresh-toggle">
          历史条数
          <select v-model.number="actionHistoryLimit">
            <option :value="6">6</option>
            <option :value="10">10</option>
            <option :value="20">20</option>
          </select>
        </label>
        <label class="auto-refresh-toggle">
          <input v-model="autoRefreshActionSurface" type="checkbox" />
          自动刷新
        </label>
        <label class="auto-refresh-toggle">
          间隔
          <select v-model.number="autoRefreshIntervalSec">
            <option :value="15">15s</option>
            <option :value="30">30s</option>
            <option :value="60">60s</option>
          </select>
        </label>
      </section>
      <section v-if="semanticActionButtons.length && actionSurfaceIsStale" class="semantic-action-stale-banner">
        <span>动作面可能过期（超过 60 秒），请先刷新后再执行。</span>
        <button type="button" class="stats-refresh" @click="loadPaymentActionSurface">立即刷新</button>
      </section>
      <section v-if="semanticActionButtons.length && !semanticActionStats.allowed" class="semantic-action-stale-banner">
        <span>当前没有可执行动作，请先处理阻塞原因或执行建议动作。</span>
        <button
          v-if="firstSuggestedBlockedAction"
          type="button"
          class="stats-refresh"
          @click="runBlockedSuggestedAction(firstSuggestedBlockedAction)"
        >
          执行首个建议
        </button>
      </section>
      <section v-if="topBlockedActions.length" class="semantic-action-stale-banner">
        <span>主要阻塞：{{ topBlockedActions.join(' / ') }}</span>
      </section>
      <section v-if="semanticActionButtons.length" class="semantic-action-shortcuts">
        快捷键: <code>Ctrl+Enter</code> 执行主动作 · <code>Alt+R</code> 重试上次动作 · <code>Alt+F</code> 刷新动作面 · <code>Alt+H</code> 重置历史筛选 · <code>?</code> 显示/隐藏帮助
      </section>
      <section v-if="semanticActionButtons.length && shortcutHelpVisible" class="semantic-action-stale-banner">
        <span>帮助：`Ctrl+Enter` 执行主动作；`Alt+R` 重试；`Alt+F` 刷新；`Alt+H` 重置历史筛选；`?` 切换帮助显示。</span>
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
          <h3>
            最近操作
            <small class="history-count">可见 {{ displayedActionHistory.length }} / 总计 {{ actionHistory.length }}</small>
          </h3>
          <div class="history-actions">
            <button type="button" class="history-clear" title="复制最新Trace" aria-label="复制最新Trace" @click="copyLatestTrace">复制最新Trace</button>
            <button type="button" class="history-clear" title="复制当前视图历史记录" aria-label="复制当前视图历史记录" :disabled="!hasVisibleHistory" @click="copyAllHistory">复制当前视图</button>
            <button type="button" class="history-clear" title="导出当前视图历史JSON" aria-label="导出当前视图历史JSON" :disabled="!hasVisibleHistory" @click="exportActionHistory">导出当前视图</button>
            <button type="button" class="history-clear" title="复制当前视图历史JSON" aria-label="复制当前视图历史JSON" :disabled="!hasVisibleHistory" @click="copyVisibleHistoryJson">复制当前JSON</button>
            <button type="button" class="history-clear" title="导出当前视图历史CSV" aria-label="导出当前视图历史CSV" :disabled="!hasVisibleHistory" @click="exportActionHistoryCsv">导出当前CSV</button>
            <button type="button" class="history-clear" title="复制当前视图Trace列表" aria-label="复制当前视图Trace列表" :disabled="!hasVisibleTrace" @click="copyVisibleTraces">复制Trace列表</button>
            <button type="button" class="history-clear" title="复制当前视图原因统计" aria-label="复制当前视图原因统计" :disabled="!hasVisibleHistory" @click="copyVisibleReasonStats">复制原因统计</button>
            <button type="button" class="history-clear" title="复制筛选查询串" aria-label="复制筛选查询串" @click="copyHistoryFilterQuery">复制查询串</button>
            <button type="button" class="history-clear" title="复制筛选摘要" aria-label="复制筛选摘要" @click="copyHistoryFilterSummary">复制筛选摘要</button>
            <button type="button" class="history-clear" title="导出证据包" aria-label="导出证据包" @click="exportEvidenceBundle">导出证据包</button>
            <button type="button" class="history-clear" title="仅清空当前筛选视图" aria-label="仅清空当前筛选视图" :disabled="actionBusy || loading || !hasVisibleHistory" @click="clearVisibleHistory">清空当前视图</button>
            <button type="button" class="history-clear" :disabled="actionBusy || loading || !actionHistory.length" @click="clearActionHistory">清空</button>
            <button type="button" class="history-clear" :disabled="actionBusy || loading || !canUndoHistoryClear" @click="undoHistoryClear">撤销清空</button>
          </div>
        </div>
        <div class="history-filters">
          <input
            ref="historySearchInputRef"
            v-model.trim="historySearch"
            class="history-search"
            type="text"
            placeholder="搜索历史动作/原因码/Trace"
            aria-label="搜索历史动作、原因码或Trace"
          />
          <button type="button" :class="{ active: historyOutcomeFilter === 'ALL' }" @click="historyOutcomeFilter = 'ALL'">全部结果</button>
          <button type="button" :class="{ active: historyOutcomeFilter === 'SUCCESS' }" @click="historyOutcomeFilter = 'SUCCESS'">成功</button>
          <button type="button" :class="{ active: historyOutcomeFilter === 'FAILED' }" @click="historyOutcomeFilter = 'FAILED'">失败</button>
          <button type="button" class="history-clear" @click="applyFailureFocusPreset">失败聚焦</button>
          <button type="button" class="history-clear" @click="applySuccessFocusPreset">成功巡检</button>
          <button type="button" :class="{ active: historySortMode === 'DESC' }" @click="historySortMode = 'DESC'">最新优先</button>
          <button type="button" :class="{ active: historySortMode === 'ASC' }" @click="historySortMode = 'ASC'">最早优先</button>
          <button type="button" :class="{ active: historyDurationFilter === 'ALL' }" @click="historyDurationFilter = 'ALL'">全部耗时</button>
          <button type="button" :class="{ active: historyDurationFilter === 'LE_1S' }" @click="historyDurationFilter = 'LE_1S'">≤1s</button>
          <button type="button" :class="{ active: historyDurationFilter === 'BETWEEN_1S_3S' }" @click="historyDurationFilter = 'BETWEEN_1S_3S'">1-3s</button>
          <button type="button" :class="{ active: historyDurationFilter === 'GT_3S' }" @click="historyDurationFilter = 'GT_3S'">&gt;3s</button>
          <button type="button" :class="{ active: historyTimeWindow === 'ALL' }" @click="historyTimeWindow = 'ALL'">全部时间</button>
          <button type="button" :class="{ active: historyTimeWindow === 'H1' }" @click="historyTimeWindow = 'H1'">近1小时</button>
          <button type="button" :class="{ active: historyTimeWindow === 'D1' }" @click="historyTimeWindow = 'D1'">近24小时</button>
          <button type="button" :class="{ active: historyTimeWindow === 'D7' }" @click="historyTimeWindow = 'D7'">近7天</button>
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
          <button type="button" class="history-clear" @click="resetHistoryFilters">重置历史筛选</button>
        </div>
        <div class="history-filter-summary">
          当前筛选: {{ historyFilterSummaryText }}
        </div>
        <div v-if="actionHistory.length && !displayedActionHistory.length" class="history-empty-tip">
          当前筛选条件下暂无记录。
          <button type="button" class="history-clear" @click="resetHistoryFilters">恢复全部</button>
        </div>
        <ul>
          <li v-for="entry in displayedActionHistory" :key="entry.key">
            <strong>{{ entry.label }}</strong>
            <span class="history-outcome" :class="{ error: !entry.success }">{{ entry.reasonCode }}</span>
            <span class="history-meta">state: {{ entry.stateBefore || '-' }}</span>
            <span class="history-meta">cost: {{ historyDurationLabel(entry) }}</span>
            <span class="history-meta">at: {{ entry.atText }} ({{ historyAgeLabel(entry) }})</span>
            <button
              v-if="entry.traceId"
              type="button"
              class="history-trace-link"
              :title="`按 Trace 过滤: ${entry.traceId}`"
              @click="applyHistoryTraceFilter(entry.traceId)"
            >
              trace: {{ entry.traceId }}
            </button>
            <button type="button" class="history-copy" @click="copyHistoryEntry(entry)">复制</button>
          </li>
        </ul>
      </section>
      <section v-else-if="semanticActionButtons.length" class="semantic-action-history history-empty">
        <h3>最近操作</h3>
        <p>还没有执行记录。可先点击上方动作按钮，系统将自动记录原因码与 Trace。</p>
      </section>
      <section v-if="contractWarnings.length" class="contract-warning-block">
        <h3>契约告警</h3>
        <ul>
          <li v-for="warn in contractWarnings" :key="warn">{{ warn }}</li>
        </ul>
      </section>
      <section v-if="contractTransitions.length" class="contract-workflow-block">
        <h3>流程建议</h3>
        <div class="workflow-actions">
          <button
            v-for="item in contractTransitions"
            :key="item.key"
            type="button"
            class="stats-refresh"
            :title="item.notes || item.label"
          >
            {{ item.label }}
          </button>
        </div>
      </section>
      <section v-if="contractSearchFilters.length" class="contract-search-block">
        <h3>契约筛选</h3>
        <div class="workflow-actions">
          <button
            v-for="item in contractSearchFilters"
            :key="`filter-${item.key}`"
            type="button"
            class="stats-refresh"
            @click="applyContractFilter(item.key)"
          >
            {{ item.label }}
          </button>
        </div>
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
import { loadActionContractRaw } from '../api/contract';
import { extractFieldNames, resolveView } from '../app/resolvers/viewResolver';
import FieldValue from '../components/FieldValue.vue';
import StatusPanel from '../components/StatusPanel.vue';
import ViewLayoutRenderer from '../components/view/ViewLayoutRenderer.vue';
import type { ActionContract, ViewButton, ViewContract } from '@sc/schema';
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
  durationMs: number;
  at: number;
  atText: string;
};

const actionFeedback = ref<ActionFeedback | null>(null);
const actionHistory = ref<ActionHistoryEntry[]>([]);
const lastSemanticAction = ref<{ action: string; reason: string; label: string } | null>(null);
const historyReasonFilter = ref('ALL');
const historyOutcomeFilter = ref<'ALL' | 'SUCCESS' | 'FAILED'>('ALL');
const historyDurationFilter = ref<'ALL' | 'LE_1S' | 'BETWEEN_1S_3S' | 'GT_3S'>('ALL');
const historyTimeWindow = ref<'ALL' | 'H1' | 'D1' | 'D7'>('ALL');
const historySortMode = ref<'DESC' | 'ASC'>('DESC');
const historySearch = ref('');
const historySearchInputRef = ref<HTMLInputElement | null>(null);
const lastClearedHistorySnapshot = ref<{ storageKey: string; entries: ActionHistoryEntry[] } | null>(null);
let actionFeedbackTimer: ReturnType<typeof setTimeout> | null = null;
let actionSurfaceRefreshTimer: ReturnType<typeof setInterval> | null = null;
const actionFilterStorageKey = 'sc.payment.action_filter.v1';
const actionHistoryStoragePrefix = 'sc.payment.action_history.v1';
const historyReasonFilterStoragePrefix = 'sc.payment.history_reason_filter.v1';
const historyOutcomeFilterStoragePrefix = 'sc.payment.history_outcome_filter.v1';
const historyDurationFilterStoragePrefix = 'sc.payment.history_duration_filter.v1';
const historyTimeWindowStoragePrefix = 'sc.payment.history_time_window.v1';
const historySearchStoragePrefix = 'sc.payment.history_search.v1';
const historySortModeStoragePrefix = 'sc.payment.history_sort_mode.v1';
const actionHistoryLimitStorageKey = 'sc.payment.history_limit.v1';
const autoRefreshIntervalStorageKey = 'sc.payment.auto_refresh_interval.v1';
const actionSearchStoragePrefix = 'sc.payment.action_search.v1';

const model = computed(() => String(route.params.model || ''));
const recordId = computed(() => (route.params.id === 'new' ? null : Number(route.params.id)));
const recordIdDisplay = computed(() => (recordId.value ? recordId.value : 'new'));
const actionIdFromQuery = computed(() => {
  const raw = route.query.action_id;
  const value = Array.isArray(raw) ? raw[0] : raw;
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
});
const actionContract = ref<ActionContract | null>(null);
const actionContractMeta = ref<Record<string, unknown> | null>(null);
const title = computed(() => {
  const headTitle = String(actionContract.value?.head?.title || '').trim();
  if (headTitle) return headTitle;
  return `Form: ${model.value}`;
});
const errorCopy = computed(() => resolveErrorCopy(error.value, 'failed to load record'));
const actionHistoryStorageKey = computed(() => `${actionHistoryStoragePrefix}:${model.value}:${recordIdDisplay.value}`);
const historyReasonFilterStorageKey = computed(
  () => `${historyReasonFilterStoragePrefix}:${model.value}:${recordIdDisplay.value}`,
);
const historyOutcomeFilterStorageKey = computed(
  () => `${historyOutcomeFilterStoragePrefix}:${model.value}:${recordIdDisplay.value}`,
);
const historyDurationFilterStorageKey = computed(
  () => `${historyDurationFilterStoragePrefix}:${model.value}:${recordIdDisplay.value}`,
);
const historyTimeWindowStorageKey = computed(
  () => `${historyTimeWindowStoragePrefix}:${model.value}:${recordIdDisplay.value}`,
);
const historySearchStorageKey = computed(
  () => `${historySearchStoragePrefix}:${model.value}:${recordIdDisplay.value}`,
);
const historySortModeStorageKey = computed(
  () => `${historySortModeStoragePrefix}:${model.value}:${recordIdDisplay.value}`,
);
const actionSearchStorageKey = computed(() => `${actionSearchStoragePrefix}:${model.value}:${recordIdDisplay.value}`);
const canUndoHistoryClear = computed(
  () => Boolean(lastClearedHistorySnapshot.value) && lastClearedHistorySnapshot.value?.storageKey === actionHistoryStorageKey.value,
);
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

type ContractOpenAction = {
  key: string;
  label: string;
  actionId: number | null;
  description: string;
};

const contractRights = computed(() => {
  const head = actionContract.value?.head?.permissions;
  const effectiveRights = actionContract.value?.permissions?.effective?.rights;
  const resolve = (key: string) => {
    const fromHead = head?.[key as keyof typeof head];
    if (typeof fromHead === 'boolean') return fromHead;
    const fromEffective = effectiveRights?.[key as keyof typeof effectiveRights];
    if (typeof fromEffective === 'boolean') return fromEffective;
    return true;
  };
  return {
    read: resolve('read'),
    write: resolve('write'),
    create: resolve('create'),
    unlink: resolve('unlink'),
  };
});

const canSaveByContract = computed(() => {
  if (recordId.value) return contractRights.value.write;
  return contractRights.value.create;
});

function toActionId(raw: unknown): number | null {
  const parsed = Number(raw || 0);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

const contractHeaderActions = computed<ContractOpenAction[]>(() => {
  const toolbar = actionContract.value?.toolbar?.header;
  const buttons = actionContract.value?.buttons;
  const merged: unknown[] = [];
  if (Array.isArray(toolbar)) merged.push(...toolbar);
  if (Array.isArray(buttons)) merged.push(...buttons);

  const seen = new Set<string>();
  const result: ContractOpenAction[] = [];
  for (const item of merged) {
    if (!item || typeof item !== 'object') continue;
    const row = item as Record<string, unknown>;
    if (String(row.kind || '').toLowerCase() !== 'open') continue;
    const level = String(row.level || '').toLowerCase();
    if (level && level !== 'header' && level !== 'toolbar') continue;
    const payload = row.payload as Record<string, unknown> | undefined;
    const actionId = toActionId(payload?.action_id) ?? toActionId(payload?.ref);
    const key = String(row.key || `open_${actionId || 'na'}_${result.length}`).trim();
    if (!key || seen.has(key)) continue;
    seen.add(key);
    result.push({
      key,
      label: String(row.label || key),
      actionId,
      description: String((payload && payload.xml_id) || ''),
    });
  }
  return result.slice(0, 8);
});

const contractMetaLine = computed(() => {
  const root = actionContract.value;
  if (!root) return '';
  const viewType = String(root.head?.view_type || root.view_type || '').trim() || '-';
  const filters = Array.isArray(root.search?.filters) ? root.search.filters.length : 0;
  const transitions = Array.isArray(root.workflow?.transitions) ? root.workflow.transitions.length : 0;
  const contractMode = String(actionContractMeta.value?.contract_mode || '').trim();
  const parts = [
    `contract.view_type=${viewType}`,
    `filters=${filters}`,
    `transitions=${transitions}`,
    `rights=${contractRights.value.read ? 'R' : '-'}${contractRights.value.write ? 'W' : '-'}${contractRights.value.create ? 'C' : '-'}${contractRights.value.unlink ? 'D' : '-'}`,
  ];
  if (root.degraded) parts.push('degraded=yes');
  if (Array.isArray(root.missing_models) && root.missing_models.length) {
    parts.push(`missing_models=${root.missing_models.length}`);
  }
  if (contractMode) parts.push(`mode=${contractMode}`);
  return parts.join(' · ');
});

const contractWarnings = computed(() => {
  const warnings = actionContract.value?.warnings;
  if (!Array.isArray(warnings)) return [];
  return warnings
    .map((item) => {
      if (typeof item === 'string') return item.trim();
      if (item && typeof item === 'object') {
        const row = item as Record<string, unknown>;
        return String(row.message || row.code || '').trim();
      }
      return '';
    })
    .filter(Boolean);
});

const contractTransitions = computed(() => {
  const transitions = actionContract.value?.workflow?.transitions;
  if (!Array.isArray(transitions)) return [];
  return transitions
    .map((item, index) => {
      const trigger = item?.trigger || {};
      const label = String(trigger.label || trigger.name || `transition_${index + 1}`).trim();
      const notes = String(item?.notes || '').trim();
      return { key: `${label}_${index}`, label, notes };
    })
    .filter((item) => item.label)
    .slice(0, 8);
});

const contractSearchFilters = computed(() => {
  const filters = actionContract.value?.search?.filters;
  if (!Array.isArray(filters)) return [];
  return filters
    .map((item) => {
      const key = String(item?.key || '').trim();
      const label = String(item?.label || key).trim();
      return { key, label };
    })
    .filter((item) => item.key && item.label)
    .slice(0, 10);
});

function extractContractFieldOrder(contract: ActionContract | null) {
  const layout = contract?.views?.form?.layout;
  if (!Array.isArray(layout)) return [];
  const ordered: string[] = [];
  for (const node of layout) {
    if (!node || typeof node !== 'object') continue;
    const kind = String(node.type || '').trim().toLowerCase();
    const name = String(node.name || '').trim();
    if (kind !== 'field' || !name || ordered.includes(name)) continue;
    ordered.push(name);
  }
  return ordered;
}
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
const autoRefreshIntervalSec = ref(15);
const actionSurfaceRefreshPaused = ref(false);
const primaryActionKey = ref('');
const isPaymentRequestModel = computed(() => model.value === 'payment.request');
const actionFilterMode = ref<'all' | 'allowed' | 'blocked'>('all');
const hideBlockedHints = ref(false);
const semanticActionSearch = ref('');
const actionHistoryLimit = ref(6);
const shortcutHelpVisible = ref(false);
try {
  const cachedFilter = String(window.localStorage.getItem(actionFilterStorageKey) || '').trim();
  if (cachedFilter === 'all' || cachedFilter === 'allowed' || cachedFilter === 'blocked') {
    actionFilterMode.value = cachedFilter;
  }
  const cachedInterval = Number(window.localStorage.getItem(autoRefreshIntervalStorageKey) || 15);
  if ([15, 30, 60].includes(cachedInterval)) {
    autoRefreshIntervalSec.value = cachedInterval;
  }
  const cachedHistoryLimit = Number(window.localStorage.getItem(actionHistoryLimitStorageKey) || 6);
  if ([6, 10, 20].includes(cachedHistoryLimit)) {
    actionHistoryLimit.value = cachedHistoryLimit;
  }
} catch {
  // Ignore storage errors and keep default mode.
}
function hydrateRecordScopedPanelPrefs() {
  try {
    const cachedReason = String(window.localStorage.getItem(historyReasonFilterStorageKey.value) || '').trim();
    historyReasonFilter.value = cachedReason || 'ALL';
    const cachedOutcome = String(window.localStorage.getItem(historyOutcomeFilterStorageKey.value) || '').trim();
    historyOutcomeFilter.value = cachedOutcome === 'SUCCESS' || cachedOutcome === 'FAILED' ? cachedOutcome : 'ALL';
    const cachedDuration = String(window.localStorage.getItem(historyDurationFilterStorageKey.value) || '').trim();
    historyDurationFilter.value =
      cachedDuration === 'LE_1S' || cachedDuration === 'BETWEEN_1S_3S' || cachedDuration === 'GT_3S'
        ? cachedDuration
        : 'ALL';
    const cachedTimeWindow = String(window.localStorage.getItem(historyTimeWindowStorageKey.value) || '').trim();
    historyTimeWindow.value =
      cachedTimeWindow === 'H1' || cachedTimeWindow === 'D1' || cachedTimeWindow === 'D7' ? cachedTimeWindow : 'ALL';
    historySearch.value = String(window.localStorage.getItem(historySearchStorageKey.value) || '');
    const cachedSort = String(window.localStorage.getItem(historySortModeStorageKey.value) || '').trim();
    historySortMode.value = cachedSort === 'ASC' ? 'ASC' : 'DESC';
    semanticActionSearch.value = String(window.localStorage.getItem(actionSearchStorageKey.value) || '');
  } catch {
    historyReasonFilter.value = 'ALL';
    historyOutcomeFilter.value = 'ALL';
    historyDurationFilter.value = 'ALL';
    historyTimeWindow.value = 'ALL';
    historySearch.value = '';
    historySortMode.value = 'DESC';
    semanticActionSearch.value = '';
  }
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
const actionReadinessScore = computed(() => {
  const total = Math.max(1, semanticActionStats.value.total);
  const allowed = semanticActionStats.value.allowed;
  const base = Math.round((allowed / total) * 100);
  return actionSurfaceIsStale.value ? Math.max(0, base - 10) : base;
});
const readinessLevelClass = computed(() => {
  if (actionReadinessScore.value >= 80) return "good";
  if (actionReadinessScore.value >= 50) return "warn";
  return "bad";
});
const blockedTopReasons = computed(() => {
  const counts = new Map<string, number>();
  for (const item of semanticActionButtons.value) {
    if (item.allowed) continue;
    const key = item.reasonCode || "UNKNOWN";
    counts.set(key, Number(counts.get(key) || 0) + 1);
  }
  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([reason, count]) => `${reason}:${count}`);
});
const blockedReasonCodes = computed(() => blockedTopReasons.value.map((item) => item.split(':')[0]).filter(Boolean));
const topBlockedActions = computed(() => {
  return semanticActionButtons.value
    .filter((item) => !item.allowed)
    .slice(0, 3)
    .map((item) => `${item.label}(${item.reasonCode || 'UNKNOWN'})`);
});
const allowedActionLabels = computed(() => {
  return semanticActionButtons.value
    .filter((item) => item.allowed)
    .map((item) => item.label)
    .slice(0, 3);
});
const latestFailureReason = computed(() => {
  const failed = actionHistory.value.find((item) => !item.success);
  return failed ? `${failed.reasonCode} (${failed.label})` : '';
});
const firstSuggestedBlockedAction = computed(
  () =>
    semanticActionButtons.value.find(
      (item) => !item.allowed && item.suggestedAction && suggestedActionMeta(item).canRun,
    ) || null,
);
const actionHistorySuccessRate = computed(() => {
  if (!actionHistory.value.length) return 0;
  const success = actionHistory.value.filter((item) => item.success).length;
  return Math.round((success / actionHistory.value.length) * 100);
});

async function copyActionStats() {
  if (!semanticActionButtons.value.length) return;
  const payload = {
    model: model.value,
    record_id: recordId.value,
    primary_action_key: primaryActionKey.value,
    total: semanticActionStats.value.total,
    allowed: semanticActionStats.value.allowed,
    blocked: semanticActionStats.value.blocked,
    stale: actionSurfaceIsStale.value,
    age: actionSurfaceAgeLabel.value,
    blocked_top_reasons: blockedTopReasons.value,
    at: Date.now(),
  };
  try {
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    actionFeedback.value = {
      message: '动作统计已复制',
      reasonCode: 'ACTION_STATS_COPIED',
      success: true,
      traceId: lastTraceId.value,
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: '动作统计复制失败',
      reasonCode: 'ACTION_STATS_COPY_FAILED',
      success: false,
      traceId: lastTraceId.value,
    };
  }
}

function applyBlockedReasonFilter(reason: string) {
  actionFilterMode.value = 'blocked';
  semanticActionSearch.value = reason;
}

function exportBlockedSummary() {
  if (!semanticActionButtons.value.length || !recordId.value) return;
  const blocked = semanticActionButtons.value
    .filter((item) => !item.allowed)
    .map((item) => ({
      key: item.key,
      label: item.label,
      reason_code: item.reasonCode || "UNKNOWN",
      blocked_message: item.blockedMessage || "",
      required_role: item.requiredRoleLabel || item.requiredRoleKey || "",
      handoff_required: item.handoffRequired,
    }));
  const payload = {
    model: model.value,
    record_id: recordId.value,
    exported_at: Date.now(),
    blocked_count: blocked.length,
    blocked_top_reasons: blockedTopReasons.value,
    blocked_actions: blocked,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `payment_blocked_summary_${model.value}_${recordId.value}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function exportAllowedSummary() {
  if (!semanticActionButtons.value.length || !recordId.value) return;
  const allowed = semanticActionButtons.value
    .filter((item) => item.allowed)
    .map((item) => ({
      key: item.key,
      label: item.label,
      next_state_hint: item.nextStateHint,
      execute_intent: item.executeIntent,
      delivery_priority: item.deliveryPriority,
    }));
  const payload = {
    model: model.value,
    record_id: recordId.value,
    exported_at: Date.now(),
    primary_action_key: primaryActionKey.value,
    allowed_count: allowed.length,
    allowed_actions: allowed,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `payment_allowed_summary_${model.value}_${recordId.value}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function copyBlockedReasonsText() {
  const blocked = semanticActionButtons.value.filter((item) => !item.allowed);
  if (!blocked.length) return;
  const lines = blocked.map(
    (item) => `${item.label}: ${item.reasonCode || 'UNKNOWN'}${item.blockedMessage ? ` (${item.blockedMessage})` : ''}`,
  );
  try {
    await navigator.clipboard.writeText(lines.join('\n'));
    actionFeedback.value = {
      message: '阻塞文本已复制',
      reasonCode: 'BLOCKED_TEXT_COPIED',
      success: true,
      traceId: lastTraceId.value,
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: '阻塞文本复制失败',
      reasonCode: 'BLOCKED_TEXT_COPY_FAILED',
      success: false,
      traceId: lastTraceId.value,
    };
  }
}

async function copyAllowedActionsText() {
  const allowed = semanticActionButtons.value.filter((item) => item.allowed);
  if (!allowed.length) return;
  const lines = allowed.map((item) => `${item.label}: ${item.nextStateHint || '可执行'}`);
  try {
    await navigator.clipboard.writeText(lines.join('\n'));
    actionFeedback.value = {
      message: '可执行文本已复制',
      reasonCode: 'ALLOWED_TEXT_COPIED',
      success: true,
      traceId: lastTraceId.value,
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: '可执行文本复制失败',
      reasonCode: 'ALLOWED_TEXT_COPY_FAILED',
      success: false,
      traceId: lastTraceId.value,
    };
  }
}
const actionSurfaceAgeLabel = computed(() => {
  if (!paymentActionSurfaceLoadedAt.value) return '-';
  const deltaSec = Math.max(0, Math.floor((Date.now() - paymentActionSurfaceLoadedAt.value) / 1000));
  if (deltaSec < 60) return `${deltaSec}s`;
  const min = Math.floor(deltaSec / 60);
  const sec = deltaSec % 60;
  return `${min}m${sec}s`;
});
const actionSurfaceLoadedAtText = computed(() => {
  if (!paymentActionSurfaceLoadedAt.value) return '';
  return new Date(paymentActionSurfaceLoadedAt.value).toLocaleTimeString('zh-CN', { hour12: false });
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
  const keyword = historySearch.value.toLowerCase();
  const now = Date.now();
  const windowMs =
    historyTimeWindow.value === 'H1' ? 3600_000 : historyTimeWindow.value === 'D1' ? 86_400_000 : historyTimeWindow.value === 'D7' ? 604_800_000 : 0;
  const byTime =
    windowMs > 0 ? actionHistory.value.filter((item) => Math.max(0, now - Number(item.at || 0)) <= windowMs) : actionHistory.value;
  const byOutcome =
    historyOutcomeFilter.value === 'ALL'
      ? byTime
      : byTime.filter((item) =>
          historyOutcomeFilter.value === 'SUCCESS' ? item.success : !item.success,
        );
  const byReason =
    historyReasonFilter.value === 'ALL'
      ? byOutcome
      : byOutcome.filter((item) => item.reasonCode === historyReasonFilter.value);
  const byDuration = byReason.filter((item) => {
    const duration = Math.max(0, Number(item.durationMs || 0));
    if (historyDurationFilter.value === 'LE_1S') return duration <= 1000;
    if (historyDurationFilter.value === 'BETWEEN_1S_3S') return duration > 1000 && duration <= 3000;
    if (historyDurationFilter.value === 'GT_3S') return duration > 3000;
    return true;
  });
  if (!keyword) return byDuration;
  return byDuration.filter((item) =>
    `${item.label} ${item.reasonCode} ${item.traceId}`.toLowerCase().includes(keyword),
  );
});
const displayedActionHistory = computed(() => {
  const rows = [...filteredActionHistory.value];
  return rows.sort((a, b) => (historySortMode.value === 'ASC' ? a.at - b.at : b.at - a.at));
});
const hasVisibleHistory = computed(() => displayedActionHistory.value.length > 0);
const hasVisibleTrace = computed(() =>
  displayedActionHistory.value.some((entry) => String(entry.traceId || '').trim().length > 0),
);
const historyFilterSummaryText = computed(() => {
  const parts = [
    `结果=${historyOutcomeFilter.value}`,
    `耗时=${historyDurationFilter.value}`,
    `时间=${historyTimeWindow.value}`,
    `原因=${historyReasonFilter.value}`,
    `排序=${historySortMode.value}`,
  ];
  if (historySearch.value.trim()) {
    parts.push(`搜索=${historySearch.value.trim()}`);
  }
  return parts.join(' · ');
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
  { label: 'action_id', value: actionIdFromQuery.value || '-' },
  { label: 'render_mode', value: renderMode.value },
  { label: 'layout_present', value: Boolean(viewContract.value?.layout) },
  { label: 'layout_nodes', value: JSON.stringify(layoutStats.value) },
  { label: 'contract_loaded', value: Boolean(actionContract.value) },
  { label: 'contract_mode', value: String(actionContractMeta.value?.contract_mode || '-') },
  { label: 'contract_buttons', value: Array.isArray(actionContract.value?.buttons) ? actionContract.value?.buttons.length : 0 },
  { label: 'contract_toolbar_header', value: Array.isArray(actionContract.value?.toolbar?.header) ? actionContract.value?.toolbar?.header.length : 0 },
  { label: 'contract_rights', value: `${contractRights.value.read ? 'R' : '-'}${contractRights.value.write ? 'W' : '-'}${contractRights.value.create ? 'C' : '-'}${contractRights.value.unlink ? 'D' : '-'}` },
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
  actionContract.value = null;
  actionContractMeta.value = null;

  if (!model.value) {
    setError(new Error('Missing model'), 'Missing model');
    loading.value = false;
    return;
  }

  try {
    if (actionIdFromQuery.value) {
      const actionContractRes = await loadActionContractRaw(actionIdFromQuery.value);
      if (actionContractRes?.data && typeof actionContractRes.data === 'object') {
        actionContract.value = actionContractRes.data as ActionContract;
      }
      actionContractMeta.value = actionContractRes?.meta || null;
    }
    const view = await resolveView(model.value, 'form');
    viewContract.value = view;
    if (view.layout) {
      layoutStats.value = analyzeLayout(view.layout);
    }
    const layoutFieldNames = extractFieldNames(view.layout).filter(Boolean);
    const contractFieldOrder = extractContractFieldOrder(actionContract.value);
    const fieldNames = contractFieldOrder.length ? contractFieldOrder : layoutFieldNames;
    const read = recordId.value
      ? await readRecord({
          model: model.value,
          ids: [recordId.value],
          fields: fieldNames.length ? fieldNames : '*',
        })
      : { records: [{}] };

    const record = read.records?.[0] ?? {};
    const contractFields = (actionContract.value?.fields || {}) as Record<string, ViewContract['fields'][string]>;
    const fieldGroups = actionContract.value?.permissions?.field_groups || {};
    fields.value = (fieldNames.length ? fieldNames : Object.keys(record))
      .filter((name) => {
        const groupsXmlids = fieldGroups[name]?.groups_xmlids;
        return hasGroupAccess(Array.isArray(groupsXmlids) ? groupsXmlids : []);
      })
      .map((name) => {
      const fromView = view.fields?.[name];
      const fromContract = contractFields[name];
      const descriptor = fromView || fromContract;
      const readonlyByPermission = recordId.value ? !contractRights.value.write : !contractRights.value.create;
      return {
        name,
        label: descriptor?.string ?? name,
        descriptor,
        readonly: Boolean(descriptor?.readonly || readonlyByPermission),
      };
    });

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

function hasGroupAccess(groupsXmlids?: string[]) {
  if (!Array.isArray(groupsXmlids) || !groupsXmlids.length) return true;
  return groupsXmlids.some((group) => userGroups.value.includes(group));
}

async function openContractAction(action: ContractOpenAction) {
  if (!action.actionId) return;
  await router.push({
    name: 'action',
    params: { actionId: String(action.actionId) },
    query: {
      menu_id: getQueryNumber('menu_id'),
      action_id: action.actionId,
    },
  });
}

async function applyContractFilter(filterKey: string) {
  if (!actionIdFromQuery.value || !filterKey) return;
  await router.push({
    name: 'action',
    params: { actionId: String(actionIdFromQuery.value) },
    query: {
      menu_id: getQueryNumber('menu_id'),
      action_id: actionIdFromQuery.value,
      preset_filter: filterKey,
    },
  });
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

function isCautionAction(action: SemanticActionButton) {
  return action.key === 'approve' || action.key === 'done';
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
    `filter=${actionFilterMode.value}`,
    `blocked_top=${blockedTopReasons.value.join(',') || '-'}`,
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

async function copyPrimaryActionBrief() {
  if (!primaryAllowedAction.value) return;
  const lines = [
    `record=${model.value}:${recordId.value || '-'}`,
    `primary_action=${primaryAllowedAction.value.label}(${primaryAllowedAction.value.key})`,
    `next_state=${primaryAllowedAction.value.nextStateHint || '-'}`,
    `allowed=${String(primaryAllowedAction.value.allowed)}`,
    `trace_id=${lastTraceId.value || '-'}`,
    `blocked_top=${blockedTopReasons.value.join(',') || '-'}`,
  ];
  try {
    await navigator.clipboard.writeText(lines.join('\n'));
    actionFeedback.value = {
      message: '主动作说明已复制',
      reasonCode: 'PRIMARY_ACTION_BRIEF_COPIED',
      success: true,
      traceId: lastTraceId.value,
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: '主动作说明复制失败',
      reasonCode: 'PRIMARY_ACTION_BRIEF_COPY_FAILED',
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

function resetActionPanelPrefs() {
  actionFilterMode.value = 'all';
  hideBlockedHints.value = false;
  semanticActionSearch.value = '';
  resetHistoryFilters();
  autoRefreshActionSurface.value = false;
  autoRefreshIntervalSec.value = 15;
  actionHistoryLimit.value = 6;
  try {
    window.localStorage.removeItem(actionFilterStorageKey);
    window.localStorage.removeItem(historyReasonFilterStorageKey.value);
    window.localStorage.removeItem(historyOutcomeFilterStorageKey.value);
    window.localStorage.removeItem(historyDurationFilterStorageKey.value);
    window.localStorage.removeItem(historyTimeWindowStorageKey.value);
    window.localStorage.removeItem(historySearchStorageKey.value);
    window.localStorage.removeItem(historySortModeStorageKey.value);
    window.localStorage.removeItem(actionSearchStorageKey.value);
    window.localStorage.removeItem(autoRefreshIntervalStorageKey);
    window.localStorage.removeItem(actionHistoryLimitStorageKey);
  } catch {
    // Ignore storage errors.
  }
}

function resetHistoryFilters() {
  historyReasonFilter.value = 'ALL';
  historyOutcomeFilter.value = 'ALL';
  historyDurationFilter.value = 'ALL';
  historyTimeWindow.value = 'ALL';
  historySearch.value = '';
  historySortMode.value = 'DESC';
}

function applyFailureFocusPreset() {
  historyOutcomeFilter.value = 'FAILED';
  historyTimeWindow.value = 'D1';
  historySortMode.value = 'DESC';
}

function applySuccessFocusPreset() {
  historyOutcomeFilter.value = 'SUCCESS';
  historyTimeWindow.value = 'D1';
  historySortMode.value = 'DESC';
}

function applyHistoryTraceFilter(traceId: string) {
  historySearch.value = String(traceId || '').trim();
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

function createActionHistoryKey(seed = 'entry') {
  const safeSeed = String(seed || 'entry')
    .replace(/[^a-zA-Z0-9_-]/g, '_')
    .slice(0, 48);
  return `${safeSeed}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
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
  const startedAt = Date.now();
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
        key: createActionHistoryKey(action.key),
        label: action.label,
        reasonCode: parsed.reasonCode,
        success: parsed.success,
        stateBefore,
        traceId: response.traceId || '',
        durationMs: Math.max(0, Date.now() - startedAt),
        at: Date.now(),
        atText: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      },
      ...actionHistory.value,
    ].slice(0, actionHistoryLimit.value);
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
  if (actionBusy.value || loading.value) return;
  if (!actionHistory.value.length) return;
  const confirmed = window.confirm(`确定要清空全部历史记录吗？将删除 ${actionHistory.value.length} 条记录。`);
  if (!confirmed) return;
  lastClearedHistorySnapshot.value = { storageKey: actionHistoryStorageKey.value, entries: [...actionHistory.value] };
  actionHistory.value = [];
  actionFeedback.value = {
    message: '已清空全部历史记录',
    reasonCode: 'HISTORY_ALL_CLEARED',
    success: true,
    traceId: lastTraceId.value,
  };
  armActionFeedbackAutoClear();
}

function clearVisibleHistory() {
  if (actionBusy.value || loading.value) return;
  if (!displayedActionHistory.value.length) return;
  const confirmed = window.confirm(`确定要清空当前筛选视图吗？将删除 ${displayedActionHistory.value.length} 条记录。`);
  if (!confirmed) return;
  lastClearedHistorySnapshot.value = { storageKey: actionHistoryStorageKey.value, entries: [...actionHistory.value] };
  const keys = new Set(displayedActionHistory.value.map((item) => item.key));
  const before = actionHistory.value.length;
  actionHistory.value = actionHistory.value.filter((item) => !keys.has(item.key));
  const removed = Math.max(0, before - actionHistory.value.length);
  actionFeedback.value = {
    message: `已清空当前视图历史（${removed} 条）`,
    reasonCode: 'HISTORY_VISIBLE_CLEARED',
    success: true,
    traceId: lastTraceId.value,
  };
  armActionFeedbackAutoClear();
}

function undoHistoryClear() {
  if (actionBusy.value || loading.value) return;
  if (!lastClearedHistorySnapshot.value) return;
  if (lastClearedHistorySnapshot.value.storageKey !== actionHistoryStorageKey.value) return;
  actionHistory.value = [...lastClearedHistorySnapshot.value.entries].slice(0, actionHistoryLimit.value);
  lastClearedHistorySnapshot.value = null;
  actionFeedback.value = {
    message: `已恢复历史记录（${actionHistory.value.length} 条）`,
    reasonCode: 'HISTORY_CLEAR_UNDONE',
    success: true,
    traceId: lastTraceId.value,
  };
  armActionFeedbackAutoClear();
}

function historyAgeLabel(entry: ActionHistoryEntry) {
  const deltaSec = Math.max(0, Math.floor((Date.now() - Number(entry.at || 0)) / 1000));
  if (deltaSec < 60) return `${deltaSec}s ago`;
  const min = Math.floor(deltaSec / 60);
  const sec = deltaSec % 60;
  return `${min}m${sec}s ago`;
}

function historyDurationLabel(entry: ActionHistoryEntry) {
  const ms = Math.max(0, Number(entry.durationMs || 0));
  if (!ms) return '-';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
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
    `duration=${historyDurationLabel(entry)}`,
    `trace_id=${entry.traceId || '-'}`,
    `success=${String(entry.success)}`,
  ].join('\n');
  try {
    await navigator.clipboard.writeText(payload);
  } catch {
    // Ignore clipboard failures for this utility action.
  }
}

async function copyLatestTrace() {
  const latestHistory = [...actionHistory.value]
    .sort((a, b) => Number(b.at || 0) - Number(a.at || 0))
    .find((entry) => String(entry.traceId || '').trim());
  const trace = String(latestHistory?.traceId || actionFeedback.value?.traceId || lastTraceId.value || '').trim();
  if (!trace) return;
  try {
    await navigator.clipboard.writeText(trace);
    actionFeedback.value = {
      message: '最新 Trace 已复制',
      reasonCode: 'LATEST_TRACE_COPIED',
      success: true,
      traceId: trace,
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: '最新 Trace 复制失败',
      reasonCode: 'LATEST_TRACE_COPY_FAILED',
      success: false,
      traceId: trace,
    };
  }
}

async function copyAllHistory() {
  if (!displayedActionHistory.value.length) return;
  const lines = displayedActionHistory.value.map((entry) =>
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
    actionFeedback.value = {
      message: `已复制当前视图历史（${displayedActionHistory.value.length} 条）`,
      reasonCode: 'HISTORY_VISIBLE_COPIED',
      success: true,
      traceId: lastTraceId.value,
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: '当前视图历史复制失败',
      reasonCode: 'HISTORY_VISIBLE_COPY_FAILED',
      success: false,
      traceId: lastTraceId.value,
    };
  }
}

async function copyVisibleTraces() {
  const traces = Array.from(
    new Set(
      displayedActionHistory.value
        .map((entry) => String(entry.traceId || '').trim())
        .filter(Boolean),
    ),
  );
  if (!traces.length) return;
  try {
    await navigator.clipboard.writeText(traces.join('\n'));
    actionFeedback.value = {
      message: `已复制 Trace 列表（${traces.length} 条）`,
      reasonCode: 'HISTORY_TRACE_LIST_COPIED',
      success: true,
      traceId: traces[0],
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: 'Trace 列表复制失败',
      reasonCode: 'HISTORY_TRACE_LIST_COPY_FAILED',
      success: false,
      traceId: lastTraceId.value,
    };
  }
}

async function copyVisibleReasonStats() {
  if (!displayedActionHistory.value.length) return;
  const counts = new Map<string, number>();
  for (const entry of displayedActionHistory.value) {
    const reason = String(entry.reasonCode || 'UNKNOWN').trim() || 'UNKNOWN';
    counts.set(reason, Number(counts.get(reason) || 0) + 1);
  }
  const lines = Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([reason, count]) => `${reason}: ${count}`);
  try {
    await navigator.clipboard.writeText(lines.join('\n'));
    actionFeedback.value = {
      message: `原因统计已复制（${lines.length} 类）`,
      reasonCode: 'HISTORY_REASON_STATS_COPIED',
      success: true,
      traceId: lastTraceId.value,
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: '原因统计复制失败',
      reasonCode: 'HISTORY_REASON_STATS_COPY_FAILED',
      success: false,
      traceId: lastTraceId.value,
    };
  }
}

async function copyHistoryFilterSummary() {
  if (!actionHistory.value.length) {
    actionFeedback.value = {
      message: '暂无可复制的历史筛选摘要',
      reasonCode: 'HISTORY_FILTER_SUMMARY_EMPTY',
      success: false,
      traceId: lastTraceId.value,
    };
    armActionFeedbackAutoClear();
    return;
  }
  const payload = [
    `record=${model.value}:${recordId.value || '-'}`,
    `history_limit=${actionHistoryLimit.value}`,
    `history_total=${actionHistory.value.length}`,
    `history_visible=${displayedActionHistory.value.length}`,
    `outcome_filter=${historyOutcomeFilter.value}`,
    `duration_filter=${historyDurationFilter.value}`,
    `time_window=${historyTimeWindow.value}`,
    `reason_filter=${historyReasonFilter.value}`,
    `search=${historySearch.value || '-'}`,
    `sort_mode=${historySortMode.value}`,
    `trace_id=${lastTraceId.value || '-'}`,
  ].join('\n');
  try {
    await navigator.clipboard.writeText(payload);
    actionFeedback.value = {
      message: '历史筛选摘要已复制',
      reasonCode: 'HISTORY_FILTER_SUMMARY_COPIED',
      success: true,
      traceId: lastTraceId.value,
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: '历史筛选摘要复制失败',
      reasonCode: 'HISTORY_FILTER_SUMMARY_COPY_FAILED',
      success: false,
      traceId: lastTraceId.value,
    };
  }
}

async function copyHistoryFilterQuery() {
  const query = [
    `model=${encodeURIComponent(model.value)}`,
    `record_id=${encodeURIComponent(String(recordId.value || '-'))}`,
    `outcome=${encodeURIComponent(historyOutcomeFilter.value)}`,
    `duration=${encodeURIComponent(historyDurationFilter.value)}`,
    `time_window=${encodeURIComponent(historyTimeWindow.value)}`,
    `reason=${encodeURIComponent(historyReasonFilter.value)}`,
    `sort=${encodeURIComponent(historySortMode.value)}`,
    `search=${encodeURIComponent(historySearch.value || '')}`,
  ].join('&');
  try {
    await navigator.clipboard.writeText(query);
    actionFeedback.value = {
      message: '筛选查询串已复制',
      reasonCode: 'HISTORY_FILTER_QUERY_COPIED',
      success: true,
      traceId: lastTraceId.value,
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: '筛选查询串复制失败',
      reasonCode: 'HISTORY_FILTER_QUERY_COPY_FAILED',
      success: false,
      traceId: lastTraceId.value,
    };
  }
}

function exportActionHistory() {
  if (!displayedActionHistory.value.length || !recordId.value) return;
  const ts = new Date()
    .toISOString()
    .replace(/[-:]/g, '')
    .replace(/\.\d{3}Z$/, 'Z');
  const outcomeTag = historyOutcomeFilter.value.toLowerCase();
  const reasonTag = historyReasonFilter.value === 'ALL' ? 'all' : 'reason';
  const searchTag = historySearch.value.trim() ? 'search' : 'nosearch';
  const fileSuffix = `${ts}_${historySortMode.value.toLowerCase()}_${outcomeTag}_${reasonTag}_${searchTag}`;
  const payload = {
    model: model.value,
    record_id: recordId.value,
    exported_at: Date.now(),
    history_total: actionHistory.value.length,
    history_visible: displayedActionHistory.value.length,
    outcome_filter: historyOutcomeFilter.value,
    duration_filter: historyDurationFilter.value,
    time_window: historyTimeWindow.value,
    reason_filter: historyReasonFilter.value,
    search: historySearch.value || '',
    sort_mode: historySortMode.value,
    entries: displayedActionHistory.value,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `payment_action_history_${model.value}_${recordId.value}_${fileSuffix}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function copyVisibleHistoryJson() {
  if (!displayedActionHistory.value.length) return;
  const payload = {
    model: model.value,
    record_id: recordId.value || null,
    exported_at: Date.now(),
    entries: displayedActionHistory.value,
  };
  try {
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    actionFeedback.value = {
      message: `当前视图 JSON 已复制（${displayedActionHistory.value.length} 条）`,
      reasonCode: 'HISTORY_VISIBLE_JSON_COPIED',
      success: true,
      traceId: lastTraceId.value,
    };
    armActionFeedbackAutoClear();
  } catch {
    actionFeedback.value = {
      message: '当前视图 JSON 复制失败',
      reasonCode: 'HISTORY_VISIBLE_JSON_COPY_FAILED',
      success: false,
      traceId: lastTraceId.value,
    };
  }
}

function exportActionHistoryCsv() {
  if (!displayedActionHistory.value.length || !recordId.value) return;
  const ts = new Date()
    .toISOString()
    .replace(/[-:]/g, '')
    .replace(/\.\d{3}Z$/, 'Z');
  const outcomeTag = historyOutcomeFilter.value.toLowerCase();
  const reasonTag = historyReasonFilter.value === 'ALL' ? 'all' : 'reason';
  const searchTag = historySearch.value.trim() ? 'search' : 'nosearch';
  const fileSuffix = `${ts}_${historySortMode.value.toLowerCase()}_${outcomeTag}_${reasonTag}_${searchTag}`;
  const header = ["label", "reason_code", "success", "state_before", "trace_id", "duration_ms", "at_epoch", "at"];
  const rows = displayedActionHistory.value.map((entry) =>
    [
      entry.label,
      entry.reasonCode,
      String(entry.success),
      entry.stateBefore || '',
      entry.traceId || '',
      String(Math.max(0, Number(entry.durationMs || 0))),
      String(Number(entry.at || 0)),
      entry.atText || '',
    ]
      .map((item) => `"${String(item).replace(/"/g, '""')}"`)
      .join(','),
  );
  const csv = [header.join(','), ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `payment_action_history_${model.value}_${recordId.value}_${fileSuffix}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function onSemanticHotkey(event: KeyboardEvent) {
  const target = event.target as HTMLElement | null;
  const isTypingContext =
    !!target &&
    (target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.tagName === 'SELECT' ||
      Boolean(target.isContentEditable));
  if (!event.ctrlKey && !event.altKey && !event.metaKey && event.key === '/' && !isTypingContext) {
    event.preventDefault();
    historySearchInputRef.value?.focus();
    historySearchInputRef.value?.select();
    return;
  }
  if (!event.ctrlKey && !event.altKey && !event.metaKey && event.key === 'Escape' && target === historySearchInputRef.value) {
    event.preventDefault();
    historySearch.value = '';
    return;
  }
  if (isTypingContext) {
    return;
  }
  if (!event.ctrlKey && !event.altKey && event.key === '?') {
    event.preventDefault();
    shortcutHelpVisible.value = !shortcutHelpVisible.value;
    return;
  }
  if (event.ctrlKey && event.key === 'Enter' && primaryAllowedAction.value && !actionBusy.value && !loading.value) {
    event.preventDefault();
    runSemanticAction(primaryAllowedAction.value);
    return;
  }
  if (event.altKey && (event.key === 'r' || event.key === 'R') && lastSemanticAction.value && !actionBusy.value) {
    event.preventDefault();
    rerunLastSemanticAction();
    return;
  }
  if (event.altKey && (event.key === 'f' || event.key === 'F') && !loading.value && !actionBusy.value) {
    event.preventDefault();
    void loadPaymentActionSurface();
    return;
  }
  if (event.altKey && (event.key === 'h' || event.key === 'H')) {
    event.preventDefault();
    resetHistoryFilters();
  }
}

function shouldRefreshActionSurface() {
  return (
    autoRefreshActionSurface.value &&
    !actionSurfaceRefreshPaused.value &&
    Boolean(recordId.value) &&
    isPaymentRequestModel.value &&
    !loading.value &&
    !actionBusy.value
  );
}

function onVisibilityChange() {
  actionSurfaceRefreshPaused.value = document.hidden;
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

function latestExecutionBundle() {
  return {
    model: model.value,
    record_id: recordId.value,
    exported_at: Date.now(),
    trace_id: actionFeedback.value?.traceId || lastTraceId.value || "",
    last_feedback: actionFeedback.value,
    last_semantic_action: lastSemanticAction.value,
    primary_action_key: primaryActionKey.value,
    action_surface_loaded_at: paymentActionSurfaceLoadedAt.value,
    action_surface_stale: actionSurfaceIsStale.value,
    history_top3: actionHistory.value.slice(0, 3),
  };
}

async function copyLatestExecutionBundle() {
  if (!actionFeedback.value) return;
  try {
    await navigator.clipboard.writeText(JSON.stringify(latestExecutionBundle(), null, 2));
    actionFeedback.value = {
      ...actionFeedback.value,
      message: `${actionFeedback.value.message}（执行包已复制）`,
    };
    armActionFeedbackAutoClear();
  } catch {
    // Ignore clipboard failures; keep primary action result visible.
  }
}

function exportLatestExecutionBundle() {
  if (!actionFeedback.value || !recordId.value) return;
  const bundle = latestExecutionBundle();
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `payment_execution_bundle_${model.value}_${recordId.value}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
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
  document.addEventListener('visibilitychange', onVisibilityChange);
  actionSurfaceRefreshPaused.value = document.hidden;
  const interval = Math.max(5, Number(autoRefreshIntervalSec.value || 15)) * 1000;
  actionSurfaceRefreshTimer = window.setInterval(() => {
    if (!shouldRefreshActionSurface()) return;
    void loadPaymentActionSurface();
  }, interval);
});
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onSemanticHotkey);
  document.removeEventListener('visibilitychange', onVisibilityChange);
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
watch(historyReasonFilter, (value) => {
  try {
    window.localStorage.setItem(historyReasonFilterStorageKey.value, value);
  } catch {
    // Ignore storage errors.
  }
});
watch(historyOutcomeFilter, (value) => {
  try {
    window.localStorage.setItem(historyOutcomeFilterStorageKey.value, value);
  } catch {
    // Ignore storage errors.
  }
});
watch(historyDurationFilter, (value) => {
  try {
    window.localStorage.setItem(historyDurationFilterStorageKey.value, value);
  } catch {
    // Ignore storage errors.
  }
});
watch(historyTimeWindow, (value) => {
  try {
    window.localStorage.setItem(historyTimeWindowStorageKey.value, value);
  } catch {
    // Ignore storage errors.
  }
});
watch(historySearch, (value) => {
  try {
    window.localStorage.setItem(historySearchStorageKey.value, value);
  } catch {
    // Ignore storage errors.
  }
});
watch(historySortMode, (value) => {
  try {
    window.localStorage.setItem(historySortModeStorageKey.value, value);
  } catch {
    // Ignore storage errors.
  }
});
watch(autoRefreshIntervalSec, (value) => {
  const interval = [15, 30, 60].includes(Number(value)) ? Number(value) : 15;
  try {
    window.localStorage.setItem(autoRefreshIntervalStorageKey, String(interval));
  } catch {
    // Ignore storage errors.
  }
  if (actionSurfaceRefreshTimer) {
    clearInterval(actionSurfaceRefreshTimer);
    actionSurfaceRefreshTimer = window.setInterval(() => {
      if (!shouldRefreshActionSurface()) return;
      void loadPaymentActionSurface();
    }, interval * 1000);
  }
});
watch(actionHistoryLimit, (value) => {
  const normalized = [6, 10, 20].includes(Number(value)) ? Number(value) : 6;
  actionHistoryLimit.value = normalized;
  actionHistory.value = actionHistory.value.slice(0, normalized);
  try {
    window.localStorage.setItem(actionHistoryLimitStorageKey, String(normalized));
  } catch {
    // Ignore storage errors.
  }
});
watch(semanticActionSearch, (value) => {
  try {
    window.localStorage.setItem(actionSearchStorageKey.value, value);
  } catch {
    // Ignore storage errors.
  }
});
watch(
  [
    historyReasonFilterStorageKey,
    historyOutcomeFilterStorageKey,
    historyDurationFilterStorageKey,
    historyTimeWindowStorageKey,
    historySearchStorageKey,
    historySortModeStorageKey,
    actionSearchStorageKey,
  ],
  () => {
    hydrateRecordScopedPanelPrefs();
  },
  { immediate: true },
);
watch(
  actionHistory,
  (value) => {
    try {
      window.localStorage.setItem(actionHistoryStorageKey.value, JSON.stringify(value.slice(0, actionHistoryLimit.value)));
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
        const usedKeys = new Set<string>();
        actionHistory.value = parsed.slice(0, actionHistoryLimit.value).map((item, index) => {
          const baseKey = String(item?.key || '').trim() || createActionHistoryKey(`entry_${index}`);
          let key = baseKey;
          while (usedKeys.has(key)) {
            key = createActionHistoryKey(baseKey);
          }
          usedKeys.add(key);
          return {
            key,
            label: String(item?.label || '-'),
            reasonCode: String(item?.reasonCode || ''),
            success: Boolean(item?.success),
            stateBefore: String(item?.stateBefore || ''),
            traceId: String(item?.traceId || ''),
            durationMs: Number(item?.durationMs || 0),
            at: Number(item?.at || Date.now()),
            atText: String(item?.atText || ''),
          };
        });
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

.actions .caution {
  border-color: #f59e0b;
  color: #92400e;
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

.semantic-action-reason-chips {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #475569;
  font-size: 12px;
}

.reason-chip {
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid #fed7aa;
  background: #fff7ed;
  color: #9a3412;
  font-size: 11px;
}

.semantic-action-stats .stale {
  color: #b45309;
  font-weight: 600;
}

.readiness-badge {
  border-radius: 999px;
  padding: 2px 8px;
  border: 1px solid #cbd5e1;
}

.readiness-badge.good {
  color: #065f46;
  border-color: #6ee7b7;
  background: #ecfdf5;
}

.readiness-badge.warn {
  color: #92400e;
  border-color: #fcd34d;
  background: #fffbeb;
}

.readiness-badge.bad {
  color: #991b1b;
  border-color: #fca5a5;
  background: #fef2f2;
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

.auto-refresh-toggle select {
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #ffffff;
  color: #334155;
  font-size: 11px;
  padding: 2px 6px;
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

.history-count {
  margin-left: 8px;
  font-size: 12px;
  color: #475569;
  font-weight: 500;
}

.semantic-action-history.history-empty p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.history-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.history-search {
  min-width: 220px;
  padding: 4px 8px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 12px;
}

.history-filters {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
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

.history-empty-tip {
  margin-bottom: 8px;
  color: #64748b;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.history-filter-summary {
  margin-bottom: 8px;
  color: #475569;
  font-size: 12px;
}

.history-clear {
  padding: 2px 8px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  font-size: 11px;
}

.history-clear:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.semantic-action-history ul {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
}

.semantic-action-history li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.history-outcome {
  color: #0f766e;
}

.history-outcome.error {
  color: #b91c1c;
}

.history-meta {
  color: #64748b;
  font-size: 12px;
  overflow-wrap: anywhere;
}

.history-copy {
  padding: 2px 8px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  font-size: 11px;
}

@media (max-width: 900px) {
  .history-search {
    min-width: 0;
    width: 100%;
  }
}

.history-trace-link {
  padding: 0;
  border: none;
  background: transparent;
  color: #1d4ed8;
  font-size: 12px;
  text-decoration: underline;
  cursor: pointer;
  overflow-wrap: anywhere;
  word-break: break-all;
}

.contract-warning-block,
.contract-workflow-block,
.contract-search-block {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px 12px;
  background: #f8fafc;
  margin-bottom: 10px;
}

.contract-warning-block h3,
.contract-workflow-block h3,
.contract-search-block h3 {
  margin: 0 0 8px;
  font-size: 13px;
  color: #334155;
}

.contract-warning-block ul {
  margin: 0;
  padding-left: 16px;
  color: #b45309;
}

.workflow-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
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
