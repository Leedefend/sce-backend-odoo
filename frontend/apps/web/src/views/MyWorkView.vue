<template>
  <PageRenderer
    v-if="useUnifiedMyWorkRenderer"
    :contract="myWorkOrchestrationContract"
    :datasets="myWorkOrchestrationDatasets"
    @action="handleMyWorkBlockAction"
  />

  <section v-else class="my-work">
    <!-- Page intent: 聚合待办并提供可执行入口，默认进入即可开工。 -->
    <header
      v-if="pageSectionEnabled('hero', true) && pageSectionTagIs('hero', 'header')"
      class="hero"
      :style="pageSectionStyle('hero')"
    >
      <div class="hero-main">
        <div>
          <h2>{{ pageText('title', '我的工作') }}</h2>
          <p>{{ pageText('hero_subtitle', '聚合待办并直接处理，默认从“待我处理”开工。') }}</p>
        </div>
        <div class="hero-tools">
          <button
            v-for="action in headerActions"
            :key="action.key"
            class="secondary"
            @click="executeHeaderAction(action.key)"
          >
            {{ action.label || action.key }}
          </button>
        </div>
      </div>
      <div v-if="!loading && !errorText && (generatedAtText || appliedPresetLabel || visibilityNotice)" class="hero-context">
        <span v-if="appliedPresetLabel" class="context-chip">
          {{ pageText('context_preset_prefix', '推荐视图：') }}{{ appliedPresetLabel }}<span v-if="routeContextSource">（{{ routeContextSource }}）</span>
        </span>
        <button v-if="appliedPresetLabel" class="link-btn mini-btn" @click="clearRoutePreset">{{ pageText('action_clear_preset', '清除推荐') }}</button>
        <span v-if="visibilityNotice" class="context-chip warn">
          {{ visibilityNotice }}<span v-if="restrictedSourceText">（{{ restrictedSourceText }}）</span>
        </span>
        <span v-if="generatedAtText" class="context-chip subtle">{{ pageText('context_updated_at_prefix', '更新于 ') }}{{ generatedAtText }}</span>
      </div>
    </header>

    <StatusPanel v-if="loading" :title="pageText('loading_title', '加载我的工作中...')" variant="info" />
    <StatusPanel
      v-else-if="errorText"
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="statusError?.traceId || undefined"
      :error-code="statusError?.code"
      :reason-code="statusError?.reasonCode"
      :error-category="statusError?.errorCategory"
      :error-details="statusError?.details"
      :retryable="statusError?.retryable"
      :hint="errorCopy.hint"
      :suggested-action="statusError?.suggestedAction"
      variant="error"
      :on-retry="load"
      @action-executed="onErrorSuggestedActionExecuted"
    />
    <p v-if="!loading && !errorText && actionFeedback" class="action-feedback" :class="{ error: actionFeedbackError }">
      {{ actionFeedback }}
    </p>
    <p v-if="!loading && !errorText && batchEvidenceText" class="batch-evidence">
      {{ batchEvidenceText }}
    </p>
    <details
      v-if="!loading && !errorText && retryFailedIds.length && pageSectionEnabled('retry_panel', true) && pageSectionTagIs('retry_panel', 'details')"
      class="retry-panel"
      :open="pageSectionOpenDefault('retry_panel', false)"
      :style="pageSectionStyle('retry_panel')"
    >
      <summary class="retry-bar">
        <span>{{ pageText('retry_failed_prefix', '失败待办 ') }}{{ retryFailedIds.length }}{{ pageText('retry_failed_suffix', ' 条') }}</span>
        <span v-if="lastBatchExecutionMode" class="meta-chip">{{ pageText('retry_mode_prefix', '模式: ') }}{{ lastBatchExecutionMode }}</span>
        <span v-if="lastBatchReplay" class="meta-chip replay">{{ pageText('retry_replay', '重放结果') }}</span>
        <span class="retry-expand-hint">{{ pageText('retry_expand_hint', '展开处理') }}</span>
      </summary>
      <section v-if="retryFailedItems.length" class="retry-details">
        <p class="retry-title">{{ pageText('retry_title', '失败明细') }}</p>
        <div class="retry-actions">
          <button class="link-btn" @click="selectRetryFailedItems">{{ pageText('retry_action_select_failed', '选中失败项') }}</button>
          <button class="link-btn" @click="selectAllFailedItems">{{ pageText('retry_action_select_all_failed', '选中全部失败项') }}</button>
          <button class="link-btn" @click="selectRetryableFailedItems">{{ pageText('retry_action_select_retryable_only', '仅选可重试项') }}</button>
          <button class="link-btn" @click="selectNonRetryableFailedItems">{{ pageText('retry_action_select_non_retryable_only', '仅选不可重试项') }}</button>
          <button class="link-btn done-btn" @click="retryFailedTodos">{{ pageText('retry_action_retry_failed', '重试失败项') }}</button>
          <button class="link-btn" @click="copyRetrySummary">{{ pageText('retry_action_copy_summary', '复制失败摘要') }}</button>
          <button class="link-btn" @click="copyVisibleRetrySummary">{{ pageText('retry_action_copy_current_view', '复制当前视图') }}</button>
          <button class="link-btn" :disabled="!retryFailedItems.length" @click="exportRetryFailedCsv">{{ pageText('retry_action_export_failed_csv', '导出失败 CSV') }}</button>
          <button class="link-btn" :disabled="!retryRequestParams" @click="copyRetryRequest">{{ pageText('retry_action_copy_retry_request', '复制重试请求') }}</button>
          <button class="link-btn" :disabled="!retryRequestParams" @click="exportRetryRequestJson">{{ pageText('retry_action_export_retry_json', '导出重试 JSON') }}</button>
          <button class="link-btn" :disabled="!retryFailedItems.length" @click="focusFailedInMainList">{{ pageText('retry_action_focus_in_main_list', '主列表定位失败') }}</button>
          <button class="link-btn" :disabled="!lastBatchTraceId" @click="copyBatchTraceId">{{ pageText('retry_action_copy_trace', '复制 Trace') }}</button>
          <button class="link-btn secondary-btn" @click="clearRetryFailed">{{ pageText('retry_action_ignore', '忽略') }}</button>
        </div>
      <details v-if="retryRequestParams" class="retry-request-preview">
        <summary>{{ pageText('retry_request_preview_title', '重试请求预览') }}</summary>
        <div class="retry-note-presets">
          <button
            type="button"
            class="link-btn mini-btn"
            @click="applyRetryNotePreset(pageText('retry_note_template_network', '系统重试：网络抖动后重放'))"
          >
            {{ pageText('retry_note_preset_network', '网络抖动') }}
          </button>
          <button
            type="button"
            class="link-btn mini-btn"
            @click="applyRetryNotePreset(pageText('retry_note_template_conflict', '系统重试：并发冲突后重放'))"
          >
            {{ pageText('retry_note_preset_conflict', '并发冲突') }}
          </button>
          <button
            type="button"
            class="link-btn mini-btn"
            @click="applyRetryNotePreset(pageText('retry_note_template_dependency', '系统重试：依赖状态已满足'))"
          >
            {{ pageText('retry_note_preset_dependency', '依赖满足') }}
          </button>
        </div>
        <label class="retry-note-editor">
          {{ pageText('retry_note_label', '重试备注') }}
          <textarea
            v-model="retryNoteDraft"
            rows="2"
            :placeholder="pageText('retry_note_placeholder', '可选：补充本次重试说明')"
          />
        </label>
        <pre>{{ retryRequestJson }}</pre>
      </details>
      <p v-if="retryRetryableSummary" class="retry-summary">
        {{ pageText('retry_capability_prefix', '重试能力：可重试 ') }}{{ retryRetryableSummary.retryable }}{{ pageText('retry_capability_middle', ' / 不可重试 ') }}{{ retryRetryableSummary.non_retryable }}
      </p>
      <p class="retry-summary">
        {{ pageText('retry_visible_prefix', '当前展示 ') }}{{ visibleRetryFailedItems.length }}{{ pageText('retry_visible_middle', ' / ') }}{{ retryFilteredItems.length }}{{ pageText('retry_visible_suffix', ' 条') }}
        <button
          v-if="retryFilteredItems.length > retryPreviewLimit"
          type="button"
          class="link-btn mini-btn"
          @click="toggleRetryFailedExpanded"
        >
          {{ retryFailedExpanded ? pageText('retry_action_collapse_all', '收起') : pageText('retry_action_expand_all', '展开全部') }}
        </button>
      </p>
      <input
        v-model.trim="retrySearchText"
        class="search-input retry-search"
        type="search"
        :placeholder="pageText('retry_search_placeholder', '筛选失败明细：ID / 原因码 / 消息')"
      />
      <div class="retry-toggle">
        <button
          type="button"
          class="reason-chip"
          :class="{ active: retryFilterMode === 'all' }"
          @click="setRetryFilterMode('all')"
        >
          {{ pageText('retry_filter_all', '全部') }}
        </button>
        <button
          type="button"
          class="reason-chip"
          :class="{ active: retryFilterMode === 'retryable' }"
          @click="setRetryFilterMode('retryable')"
        >
          {{ pageText('retry_filter_retryable_only', '仅可重试') }}
        </button>
        <button
          type="button"
          class="reason-chip"
          :class="{ active: retryFilterMode === 'non_retryable' }"
          @click="setRetryFilterMode('non_retryable')"
        >
          {{ pageText('retry_filter_non_retryable_only', '仅不可重试') }}
        </button>
        <button
          type="button"
          class="reason-chip"
          :class="{ active: retryGroupByReason }"
          @click="toggleRetryGroupByReason"
        >
          {{ retryGroupByReason ? pageText('retry_group_mode_flat', '平铺显示') : pageText('retry_group_mode_grouped', '按原因分组') }}
        </button>
        <button
          type="button"
          class="reason-chip"
          @click="resetRetryPanelState"
        >
          {{ pageText('retry_action_reset_panel', '重置面板') }}
        </button>
      </div>
      <p v-if="retryReasonSummary.length" class="retry-summary">
        {{ pageText('retry_reason_distribution_prefix', '失败原因分布：') }}
        <button
          v-for="item in retryReasonSummary"
          :key="`reason-${item.reason_code}`"
          type="button"
          class="reason-chip"
          @click="applyReasonFilterFromFailure(item.reason_code)"
        >
          {{ item.reason_code }} x {{ item.count }}
        </button>
        <button
          v-if="reasonFilter !== 'ALL'"
          type="button"
          class="link-btn mini-btn"
          @click="clearReasonFilterFromFailure"
        >
          {{ pageText('retry_action_clear_failed_filter', '清除失败筛选') }}
        </button>
      </p>
      <p v-if="retryFailedGroups.length" class="retry-summary">
        {{ pageText('retry_group_summary_prefix', '分组摘要：') }}
        <span v-for="group in retryFailedGroups" :key="`group-${group.reason_code}`" class="group-actions">
          <button
            type="button"
            class="reason-chip"
            @click="applyReasonFilterFromFailure(group.reason_code)"
          >
            {{ group.reason_code }} ({{ group.count }} / {{ pageText('retry_group_retryable_prefix', '可重试 ') }}{{ group.retryable_count }})
          </button>
          <button
            type="button"
            class="link-btn mini-btn"
            :disabled="!group.retryable_count"
            @click="selectRetryableByReasonGroup(group.reason_code)"
          >
            {{ pageText('retry_action_select_group', '选中此组') }}
          </button>
          <button
            type="button"
            class="link-btn mini-btn"
            :disabled="!group.retryable_count"
            @click="retryByReasonGroup(group.reason_code)"
          >
            {{ pageText('retry_action_retry_group', '重试此组') }}
          </button>
        </span>
      </p>
      <ul v-if="!retryGroupByReason">
        <li v-for="item in visibleRetryFailedItems" :key="`failed-${item.id}`">
          <span class="failed-id">#{{ item.id }}</span>
          <span class="failed-code">{{ item.reason_code || pageText('retry_unknown_reason_code', 'UNKNOWN') }}</span>
          <span class="failed-msg">{{ item.message || '-' }}</span>
          <span v-if="resolveSuggestedAction(item.suggested_action, item.reason_code, item.retryable)" class="failed-hint">
            {{ resolveSuggestedAction(item.suggested_action, item.reason_code, item.retryable) }}
          </span>
          <button
            v-if="failedSuggestedActionLabel(item)"
            class="link-btn mini-btn"
            @click="runFailedSuggestedAction(item)"
          >
            {{ failedSuggestedActionLabel(item) }}
          </button>
          <button class="link-btn mini-btn" @click="copyFailedItemLine(item)">{{ pageText('retry_action_copy_single', '复制单条') }}</button>
          <button
            v-if="failedItemRecord(item.id)"
            class="link-btn mini-btn"
            @click="openRecord(failedItemRecord(item.id)!)"
          >
            {{ pageText('retry_action_open_record', '打开记录') }}
          </button>
        </li>
      </ul>
      <div v-else class="retry-grouped-list">
        <div v-for="group in groupedVisibleRetryItems" :key="`visible-group-${group.reasonCode}`" class="retry-group-block">
          <p class="retry-group-title">{{ group.reasonCode }} ({{ group.items.length }})</p>
          <ul>
            <li v-for="item in group.items" :key="`failed-grouped-${item.id}`">
              <span class="failed-id">#{{ item.id }}</span>
              <span class="failed-msg">{{ item.message || '-' }}</span>
              <span v-if="resolveSuggestedAction(item.suggested_action, item.reason_code, item.retryable)" class="failed-hint">
                {{ resolveSuggestedAction(item.suggested_action, item.reason_code, item.retryable) }}
              </span>
              <button
                v-if="failedSuggestedActionLabel(item)"
                class="link-btn mini-btn"
                @click="runFailedSuggestedAction(item)"
              >
                {{ failedSuggestedActionLabel(item) }}
              </button>
              <button class="link-btn mini-btn" @click="copyFailedItemLine(item)">{{ pageText('retry_action_copy_single', '复制单条') }}</button>
            </li>
          </ul>
        </div>
      </div>
      </section>
    </details>
    <template v-if="!loading && !errorText">
      <section
        v-if="pageSectionEnabled('todo_focus', true) && pageSectionTagIs('todo_focus', 'section')"
        class="summary-grid"
        :style="pageSectionStyle('todo_focus')"
      >
        <article
          v-for="item in summaryCards"
          :key="item.key"
          class="summary-card"
          :class="{ active: activeSection === item.key }"
          @click="selectSection(item.key)"
        >
          <p class="label">{{ item.label }}</p>
          <p class="count">{{ item.count }}</p>
        </article>
      </section>

      <section
        v-if="pageSectionEnabled('todo_focus', true) && pageSectionTagIs('todo_focus', 'section')"
        class="tabs"
        :style="pageSectionStyle('todo_focus')"
      >
        <button
          v-for="sec in sections"
          :key="sec.key"
          type="button"
          class="tab"
          :class="{ active: activeSection === sec.key }"
          @click="selectSection(sec.key)"
        >
          {{ sec.label }}
        </button>
      </section>

      <section
        v-if="pageSectionEnabled('todo_focus', true) && pageSectionTagIs('todo_focus', 'section')"
        class="filters"
        :style="pageSectionStyle('todo_focus')"
      >
        <div class="filter-bar">
          <input
            v-model.trim="searchText"
            class="search-input"
            type="search"
            :placeholder="pageText('filter_search_placeholder', '搜索事项 / 来源 / 动作')"
            @keydown.enter="applyFilters"
          />
          <button class="link-btn mini-btn" @click="showAdvancedFilters = !showAdvancedFilters">
            {{ showAdvancedFilters ? pageText('action_collapse_filters', '收起筛选') : pageText('action_expand_filters', '展开筛选') }}
          </button>
          <button class="link-btn mini-btn" @click="applyFilters">{{ pageText('action_apply_filters', '应用') }}</button>
          <button class="link-btn mini-btn" @click="resetFilters">{{ pageText('action_reset_filters', '重置') }}</button>
        </div>
        <div v-if="showAdvancedFilters" class="filter-advanced">
          <select v-model="sourceFilter" class="filter-select">
            <option value="ALL">{{ pageText('filter_source_all', '全部来源') }}</option>
            <option v-for="source in sourceOptions" :key="`src-${source}`" :value="source">
              {{ source }}
            </option>
          </select>
          <select v-model="reasonFilter" class="filter-select">
            <option value="ALL">{{ pageText('filter_reason_all', '全部原因码') }}</option>
            <option v-for="reason in reasonOptions" :key="`reason-${reason}`" :value="reason">
              {{ reason }}
            </option>
          </select>
          <select v-model="sortBy" class="filter-select">
            <option value="priority">{{ pageText('sort_priority', '排序：优先级') }}</option>
            <option value="deadline">{{ pageText('sort_deadline', '排序：截止日') }}</option>
            <option value="title">{{ pageText('sort_title', '排序：事项标题') }}</option>
            <option value="reason_code">{{ pageText('sort_reason_code', '排序：原因码') }}</option>
            <option value="source">{{ pageText('sort_source', '排序：来源') }}</option>
            <option value="id">{{ pageText('sort_id', '排序：ID') }}</option>
          </select>
          <select v-model="sortDir" class="filter-select">
            <option value="desc">{{ pageText('sort_desc', '降序') }}</option>
            <option value="asc">{{ pageText('sort_asc', '升序') }}</option>
          </select>
          <select v-model.number="pageSize" class="filter-select">
            <option :value="10">{{ pageText('page_size_10', '每页 10') }}</option>
            <option :value="20">{{ pageText('page_size_20', '每页 20') }}</option>
            <option :value="40">{{ pageText('page_size_40', '每页 40') }}</option>
          </select>
          <div class="preset-actions">
            <button class="link-btn mini-btn" @click="saveFilterPreset">{{ pageText('action_save_preset', '保存常用筛选') }}</button>
            <button class="link-btn mini-btn" :disabled="!hasFilterPreset" @click="applyFilterPreset">{{ pageText('action_apply_preset', '应用常用筛选') }}</button>
            <button class="link-btn mini-btn" :disabled="!hasFilterPreset" @click="clearFilterPreset">{{ pageText('action_clear_saved_preset', '清除预设') }}</button>
          </div>
        </div>
      </section>
      <p v-if="summaryStatus?.hint && summaryStatus?.state !== 'FILTER_EMPTY'" class="status-hint">{{ summaryStatus.hint }}</p>
      <section v-if="showFilterEmptyGuide" class="filter-empty-guide">
        <p class="guide-title">{{ pageText('filter_empty_title', '当前筛选条件没有匹配结果') }}</p>
        <p class="guide-text">{{ pageText('filter_empty_desc', '建议先恢复推荐视图，或一键清空筛选后重试。') }}</p>
        <div class="guide-actions">
          <button class="guide-btn primary" @click="applyRecommendedView">{{ pageText('action_restore_recommended_view', '恢复推荐视图') }}</button>
          <button class="guide-btn" @click="resetFilters">{{ pageText('action_clear_filters', '清空筛选') }}</button>
        </div>
      </section>

      <section v-if="todoSelectionIds.length" class="batch-bar">
        <span>{{ pageText('batch_selected_prefix', '已选 ') }}{{ todoSelectionIds.length }}{{ pageText('batch_selected_suffix', ' 条待办') }}</span>
        <button class="link-btn done-btn" :disabled="loading" @click="completeSelectedTodos">{{ pageText('action_batch_complete', '批量完成') }}</button>
        <button class="link-btn secondary-btn" :disabled="loading" @click="clearTodoSelection">{{ pageText('action_clear_selection', '清空') }}</button>
      </section>

      <section
        v-if="pageSectionEnabled('list_main', true) && pageSectionTagIs('list_main', 'section')"
        class="table-wrap"
        :style="pageSectionStyle('list_main')"
      >
        <section v-if="!displayItems.length && !showFilterEmptyGuide" class="empty-guide">
          <p class="empty-title">{{ summaryStatus?.message || pageText('empty_title_default', '当前无待处理事项') }}</p>
          <p class="empty-desc">{{ pageText('empty_desc', '状态良好。你可以返回工作台查看整体态势，或进入风险驾驶舱继续巡检。') }}</p>
          <div class="guide-actions">
            <button class="guide-btn primary" @click="goWorkbench">{{ pageText('action_go_workbench', '去工作台') }}</button>
            <button class="guide-btn" @click="goRiskCockpit">{{ pageText('action_go_risk_cockpit', '去风险驾驶舱') }}</button>
          </div>
        </section>
        <table>
          <thead>
            <tr>
              <th class="cell-select">
                <input
                  type="checkbox"
                  :checked="allTodoSelected"
                  :disabled="loading || !currentTodoRows.length"
                  @change="toggleAllTodoSelection($event)"
                />
              </th>
              <th>{{ pageText('table_col_item', '事项') }}</th>
              <th>{{ pageText('table_col_action', '动作') }}</th>
              <th>{{ pageText('table_col_deadline', '截止日') }}</th>
              <th>{{ pageText('table_col_priority', '优先级') }}</th>
              <th>{{ pageText('table_col_reason_code', '原因码') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!displayItems.length">
              <td colspan="6" class="empty">{{ summaryStatus?.message || emptyCopy.message }}</td>
            </tr>
            <tr
              v-for="item in displayItems"
              :key="`${item.section || 'all'}-${item.id}`"
              class="clickable-row"
              @click="openPrimaryEntry(item)"
            >
              <td class="cell-select">
                <input
                  v-if="isCompletableTodo(item)"
                  type="checkbox"
                  :checked="todoSelectionIdSet.has(item.id)"
                  :disabled="loading"
                  @click.stop
                  @change="toggleTodoSelection(item.id, $event)"
                />
              </td>
              <td>
                <div>{{ item.title || '-' }}</div>
                <small class="item-meta">{{ item.source || '-' }}</small>
              </td>
              <td>{{ item.action_label || '-' }}</td>
              <td>{{ item.deadline || '-' }}</td>
              <td>{{ formatPriority(item.priority) }}</td>
              <td>{{ item.reason_code || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section
        v-if="pageSectionEnabled('list_main', true) && pageSectionTagIs('list_main', 'section')"
        class="pager"
        :style="pageSectionStyle('list_main')"
      >
        <button class="link-btn" :disabled="loading || page <= 1" @click="goToPage(page - 1)">{{ pageText('pager_prev', '上一页') }}</button>
        <span>{{ pageText('pager_middle_prefix', '第 ') }}{{ page }}{{ pageText('pager_middle_sep', ' / ') }}{{ totalPages }}{{ pageText('pager_middle_suffix', ' 页') }}</span>
        <button class="link-btn" :disabled="loading || page >= totalPages" @click="goToPage(page + 1)">{{ pageText('pager_next', '下一页') }}</button>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { completeMyWorkItemsBatch, fetchMyWorkSummary, type MyWorkRecordItem, type MyWorkSection, type MyWorkSummaryItem } from '../api/myWork';
import { trackUsageEvent } from '../api/usage';
import StatusPanel from '../components/StatusPanel.vue';
import { buildStatusError, resolveEmptyCopy, resolveErrorCopy, resolveSuggestedAction, type StatusError } from '../composables/useStatus';
import { describeSuggestedAction, runSuggestedAction } from '../composables/useSuggestedAction';
import { parseWorkspaceEntryContext, readWorkspaceContext } from '../app/workspaceContext';
import { getSceneByKey } from '../app/resolvers/sceneRegistry';
import { findActionMeta, findActionNodeByModel } from '../app/menu';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import PageRenderer from '../components/page/PageRenderer.vue';
import type { PageBlockActionEvent, PageOrchestrationContract } from '../app/pageOrchestration';
import { useSessionStore } from '../stores/session';

const router = useRouter();
const route = useRoute();
const session = useSessionStore();
const pageContract = usePageContract('my_work');
const pageText = pageContract.text;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionOpenDefault = pageContract.sectionOpenDefault;
const pageSectionTagIs = pageContract.sectionTagIs;
const pageSectionStyle = pageContract.sectionStyle;

const myWorkOrchestrationContract = computed<PageOrchestrationContract>(() => {
  const contract = pageContract.contract.value?.page_orchestration_v1;
  return (contract && typeof contract === 'object') ? contract as unknown as PageOrchestrationContract : {};
});
const useUnifiedMyWorkRenderer = computed(() => {
  if (String(route.query.legacy_my_work || '').trim() === '1') return false;
  const contract = myWorkOrchestrationContract.value || {};
  const hasV1 = String(contract.contract_version || '') === 'page_orchestration_v1';
  const zones = Array.isArray(contract.zones) ? contract.zones : [];
  return hasV1 && zones.length > 0;
});

const loading = ref(false);
const errorText = ref('');
const statusError = ref<StatusError | null>(null);
const sections = ref<MyWorkSection[]>([]);
const summary = ref<MyWorkSummaryItem[]>([]);
const items = ref<MyWorkRecordItem[]>([]);
const activeSection = ref<string>('todo');
const todoSelectionIds = ref<number[]>([]);
const retryFailedIds = ref<number[]>([]);
const retryFailedItems = ref<
  Array<{
    id: number;
    reason_code: string;
    message: string;
    retryable?: boolean;
    suggested_action?: string;
    error_category?: string;
    trace_id?: string;
  }>
>([]);
const retryReasonSummary = ref<Array<{ reason_code: string; count: number }>>([]);
const retryFailedGroups = ref<Array<{ reason_code: string; count: number; retryable_count: number; suggested_action?: string; sample_ids?: number[] }>>([]);
const retryRetryableSummary = ref<{ retryable: number; non_retryable: number } | null>(null);
const retryRequestParams = ref<{ source?: string; retry_ids?: number[]; note?: string; request_id?: string } | null>(null);
const retryNoteDraft = ref('');
const todoRemaining = ref<number | null>(null);
const lastBatchExecutionMode = ref<string>('');
const lastBatchReplay = ref(false);
const lastBatchTraceId = ref('');
const lastReplayAuditId = ref<number>(0);
const lastReplayAgeMs = ref<number>(0);
const retryFilterMode = ref<'all' | 'retryable' | 'non_retryable'>('all');
const retryFailedExpanded = ref(false);
const retryPreviewLimit = 10;
const retryGroupByReason = ref(false);
const retrySearchText = ref('');
const actionFeedback = ref('');
const actionFeedbackError = ref(false);
const searchText = ref('');
const sourceFilter = ref('ALL');
const reasonFilter = ref('ALL');
const sortBy = ref('priority');
const sortDir = ref<'asc' | 'desc'>('desc');
const showAdvancedFilters = ref(false);
const page = ref(1);
const pageSize = ref(20);
const totalPages = ref(1);
const sourceFacetRows = ref<Array<{ key: string; count: number }>>([]);
const reasonFacetRows = ref<Array<{ key: string; count: number }>>([]);
const sectionFilteredFacetRows = ref<Array<{ key: string; count: number }>>([]);
const summaryStatus = ref<{ state: string; reason_code: string; message: string; hint: string } | null>(null);
const generatedAt = ref('');
const summaryVisibility = ref<{
  partial_data_hidden?: boolean;
  message?: string;
  restricted_sources?: Array<{ model: string; readable: boolean; reason: string }>;
} | null>(null);
const myWorkFilterStorageKey = 'sc.mywork.filters.v1';
const myWorkPresetStorageKey = 'sc.mywork.filter_preset.v1';
const myWorkRetryPanelStorageKey = 'sc.mywork.retry_panel.v1';
const hasFilterPreset = ref(false);
const appliedPresetLabel = ref('');
const routeContextSource = ref('');
const lastTrackedPreset = ref('');
const errorCopy = computed(() => resolveErrorCopy(statusError.value, errorText.value || 'Failed to load my work'));
const emptyCopy = computed(() => resolveEmptyCopy('my_work'));
const generatedAtText = computed(() => {
  const raw = String(generatedAt.value || '').trim();
  if (!raw) return '';
  const hasZone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(raw);
  const isoLike = raw.includes('T') ? raw : raw.replace(' ', 'T');
  const normalized = hasZone ? isoLike : `${isoLike}Z`;
  const dt = new Date(normalized);
  if (Number.isNaN(dt.getTime())) return raw;
  return dt.toLocaleString();
});
const visibilityNotice = computed(() => {
  if (!summaryVisibility.value?.partial_data_hidden) return '';
  const base = String(summaryVisibility.value?.message || pageText('partial_data_hidden', '部分数据未显示'));
  return `${base}${pageText('visibility_notice_suffix', '，请联系管理员开通对应权限。')}`;
});
const restrictedSourceText = computed(() => {
  const rows = Array.isArray(summaryVisibility.value?.restricted_sources)
    ? summaryVisibility.value?.restricted_sources || []
    : [];
  const names = rows
    .map((item) => mapRestrictedModelLabel(String(item?.model || '').trim()))
    .filter(Boolean);
  return names.join(' / ');
});
const showFilterEmptyGuide = computed(() => summaryStatus.value?.state === 'FILTER_EMPTY');
const hasScopedFilters = computed(() => Boolean(searchText.value.trim() || sourceFilter.value !== 'ALL' || reasonFilter.value !== 'ALL'));
const summaryCards = computed(() => {
  if (!hasScopedFilters.value) return summary.value;
  const map = new Map<string, number>();
  sectionFilteredFacetRows.value.forEach((row) => map.set(String(row.key || ''), Number(row.count || 0)));
  return summary.value.map((row) => ({
    ...row,
    count: map.has(String(row.key || '')) ? Number(map.get(String(row.key || '')) || 0) : 0,
  }));
});
const todoSelectionIdSet = computed(() => new Set(todoSelectionIds.value));
const autoQueryDelayMs = 300;
let autoQueryTimer: ReturnType<typeof setTimeout> | null = null;
const suspendAutoLoad = ref(false);

const filteredItems = computed(() => {
  const section = String(activeSection.value || '').trim();
  if (!section || section === 'all') return items.value;
  return items.value.filter((item) => String(item.section || '').trim() === section);
});
const displayItems = computed(() => {
  const rows = [...filteredItems.value];
  const priorityScore = (raw: unknown) => {
    const key = String(raw || '').toLowerCase();
    if (key === 'high') return 3;
    if (key === 'medium') return 2;
    if (key === 'low') return 1;
    return 0;
  };
  rows.sort((a, b) => {
    const byPriority = priorityScore(b.priority) - priorityScore(a.priority);
    if (byPriority !== 0) return byPriority;
    const ad = String(a.deadline || '9999-12-31');
    const bd = String(b.deadline || '9999-12-31');
    return ad.localeCompare(bd);
  });
  return rows;
});
const currentTodoRows = computed(() =>
  filteredItems.value.filter((item) => isCompletableTodo(item)).map((item) => item.id),
);
const todoItemMap = computed(() => {
  const map = new Map<number, MyWorkRecordItem>();
  for (const item of items.value) {
    if (isCompletableTodo(item) && Number.isFinite(item.id)) {
      map.set(item.id, item);
    }
  }
  return map;
});
const allTodoSelected = computed(() => {
  if (!currentTodoRows.value.length) return false;
  return currentTodoRows.value.every((id) => todoSelectionIdSet.value.has(id));
});
const sourceOptions = computed(() => {
  if (sourceFacetRows.value.length) {
    return sourceFacetRows.value.map((item) => item.key).filter(Boolean);
  }
  const set = new Set<string>();
  items.value.forEach((item) => {
    const source = String(item.source || '');
    if (source) set.add(source);
  });
  return Array.from(set).sort();
});
const reasonOptions = computed(() => {
  if (reasonFacetRows.value.length) {
    return reasonFacetRows.value.map((item) => item.key).filter(Boolean);
  }
  const set = new Set<string>();
  items.value.forEach((item) => {
    const reason = String(item.reason_code || '');
    if (reason) set.add(reason);
  });
  return Array.from(set).sort();
});
const retryFilteredItems = computed(() => {
  const byRetryable = (() => {
    if (retryFilterMode.value === 'all') return retryFailedItems.value;
    if (retryFilterMode.value === 'retryable') {
      return retryFailedItems.value.filter((item) => Boolean(item.retryable));
    }
    return retryFailedItems.value.filter((item) => item.retryable === false);
  })();
  const keyword = retrySearchText.value.trim().toLowerCase();
  if (!keyword) return byRetryable;
  return byRetryable.filter((item) => {
    const hay = `${item.id} ${item.reason_code || ''} ${item.message || ''}`.toLowerCase();
    return hay.includes(keyword);
  });
});
const visibleRetryFailedItems = computed(() => {
  if (retryFailedExpanded.value) return retryFilteredItems.value;
  return retryFilteredItems.value.slice(0, retryPreviewLimit);
});
const retryRequestJson = computed(() => {
  if (!retryRequestParams.value) return '';
  try {
    return JSON.stringify(
      {
        ...retryRequestParams.value,
        note: retryNoteDraft.value || retryRequestParams.value.note || '',
      },
      null,
      2,
    );
  } catch {
    return '';
  }
});
const batchEvidenceText = computed(() => {
  if (!lastBatchTraceId.value && !lastReplayAuditId.value) return '';
  const rows = [];
  if (lastBatchTraceId.value) rows.push(`trace_id: ${lastBatchTraceId.value}`);
  if (lastReplayAuditId.value > 0) rows.push(`replay_audit_id: ${lastReplayAuditId.value}`);
  if (lastReplayAgeMs.value > 0) rows.push(`replay_age_ms: ${lastReplayAgeMs.value}`);
  return rows.join(' | ');
});
const groupedVisibleRetryItems = computed(() => {
  const map = new Map<string, typeof visibleRetryFailedItems.value>();
  for (const item of visibleRetryFailedItems.value) {
    const code = item.reason_code || 'UNKNOWN';
    const rows = map.get(code) || [];
    rows.push(item);
    map.set(code, rows);
  }
  return Array.from(map.entries()).map(([reasonCode, rows]) => ({ reasonCode, items: rows }));
});
const headerActions = computed(() => pageGlobalActions.value);
const myWorkOrchestrationDatasets = computed<Record<string, unknown>>(() => {
  const summaryMetrics = summaryCards.value.map((item) => ({
    key: String(item.key || ''),
    label: String(item.label || item.key || ''),
    value: Number(item.count || 0),
    tone: item.key === activeSection.value ? 'info' : 'neutral',
  }));
  const todoRows = displayItems.value.slice(0, 20).map((item) => ({
    id: item.id,
    title: String(item.title || '-'),
    description: `${String(item.source || '-')}${item.deadline ? ` · ${item.deadline}` : ''}`,
    tone: item.reason_code ? 'warning' : 'info',
    action_key: 'open_item',
    entry_id: item.id,
    scene_key: item.scene_key,
  }));
  const sectionEntries = sections.value.map((sec) => ({
    id: String(sec.key || ''),
    key: String(sec.key || ''),
    title: String(sec.label || sec.key || ''),
    hint: `${pageText('batch_selected_prefix', '已选 ')}${Number((sec as { count?: unknown }).count || 0)}${pageText('batch_selected_suffix', ' 条待办')}`,
    action_key: 'switch_section',
    section_key: String(sec.key || ''),
  }));
  const retryAlerts = retryFailedItems.value.slice(0, 10).map((item) => ({
    id: String(item.id),
    title: `#${item.id} ${item.reason_code || 'UNKNOWN'}`,
    description: String(item.message || '-'),
    tone: item.retryable === false ? 'danger' : 'warning',
    action_key: 'focus_retry_item',
  }));
  return {
    ds_section_hero: summaryMetrics,
    ds_section_todo_focus: todoRows,
    ds_section_list_main: todoRows,
    ds_section_retry_panel: retryAlerts,
    ds_section_tabs: sectionEntries,
    ds_section_filters: sectionEntries,
  };
});
let autoSectionAligned = false;

function findRecommendedSectionKey() {
  const ranked = (summary.value || [])
    .filter((item) => Number(item.count || 0) > 0)
    .sort((a, b) => Number(b.count || 0) - Number(a.count || 0));
  return ranked[0]?.key || sections.value[0]?.key || 'todo';
}

function mapRestrictedModelLabel(modelName: string) {
  const mapping: Record<string, string> = {
    'sc.workflow.workitem': pageText('model_label_sc_workflow_workitem', '流程待办'),
    'tier.review': pageText('model_label_tier_review', '审批复核'),
    'mail.activity': pageText('model_label_mail_activity', '待办活动'),
    'project.task': pageText('model_label_project_task', '项目任务'),
    'project.project': pageText('model_label_project_project', '项目主数据'),
    'mail.message': pageText('model_label_mail_message', '消息提醒'),
    'mail.followers': pageText('model_label_mail_followers', '关注记录'),
  };
  return mapping[modelName] || modelName;
}

function formatPriority(priority: string | undefined) {
  const raw = String(priority || '').trim().toLowerCase();
  if (raw === 'high') return pageText('priority_high', '高');
  if (raw === 'low') return pageText('priority_low', '低');
  return pageText('priority_medium', '中');
}

function setActionFeedback(message: string, isError = false, autoClearMs = 0) {
  actionFeedback.value = message;
  actionFeedbackError.value = isError;
  if (!isError && autoClearMs > 0) {
    window.setTimeout(() => {
      if (actionFeedback.value === message && !actionFeedbackError.value) {
        actionFeedback.value = '';
      }
    }, autoClearMs);
  }
}

async function applyRecommendedView() {
  searchText.value = '';
  sourceFilter.value = 'ALL';
  reasonFilter.value = 'ALL';
  sortBy.value = 'priority';
  sortDir.value = 'desc';
  pageSize.value = 20;
  page.value = 1;
  activeSection.value = findRecommendedSectionKey();
  setActionFeedback(pageText('feedback_restore_recommended', '已恢复推荐视图'), false, 3000);
  await load();
}

async function load() {
  loading.value = true;
  errorText.value = '';
  statusError.value = null;
  summaryStatus.value = null;
  suspendAutoLoad.value = true;
  try {
    const data = await fetchMyWorkSummary(80, 16, {
      page: page.value,
      pageSize: pageSize.value,
      sortBy: sortBy.value,
      sortDir: sortDir.value,
      section: activeSection.value || 'all',
      source: sourceFilter.value === 'ALL' ? 'all' : sourceFilter.value,
      reasonCode: reasonFilter.value === 'ALL' ? 'all' : reasonFilter.value,
      search: searchText.value.trim(),
    });
    sections.value = Array.isArray(data.sections) ? data.sections : [];
    summary.value = Array.isArray(data.summary) ? data.summary : [];
    items.value = Array.isArray(data.items) ? data.items : [];
    generatedAt.value = String(data.generated_at || '');
    summaryStatus.value = data.status || null;
    summaryVisibility.value = data.visibility || null;
    page.value = Math.max(1, Number(data.filters?.page || page.value || 1));
    pageSize.value = Math.max(1, Number(data.filters?.page_size || pageSize.value || 20));
    totalPages.value = Math.max(1, Number(data.filters?.total_pages || 1));
    sortBy.value = String(data.filters?.sort_by || sortBy.value || 'priority');
    sortDir.value = (String(data.filters?.sort_dir || sortDir.value || 'desc') === 'asc' ? 'asc' : 'desc');
    sourceFacetRows.value = Array.isArray(data.facets?.source_counts) ? data.facets?.source_counts || [] : [];
    reasonFacetRows.value = Array.isArray(data.facets?.reason_code_counts) ? data.facets?.reason_code_counts || [] : [];
    sectionFilteredFacetRows.value = Array.isArray(data.facets?.section_counts_filtered)
      ? data.facets?.section_counts_filtered || []
      : [];
    todoSelectionIds.value = [];
    if (!autoSectionAligned) {
      const currentCount = Number(summary.value.find((item) => item.key === activeSection.value)?.count || 0);
      if (currentCount <= 0) {
        const nextKey = findRecommendedSectionKey();
        if (nextKey && nextKey !== activeSection.value) {
          autoSectionAligned = true;
          activeSection.value = nextKey;
          page.value = 1;
          await load();
          return;
        }
      }
      autoSectionAligned = true;
    }
    if (sections.value.length && !sections.value.find((sec) => sec.key === activeSection.value)) {
      activeSection.value = sections.value[0].key;
    }
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : pageText('error_request_failed', '请求失败');
    statusError.value = buildStatusError(err, errorText.value);
    summaryVisibility.value = null;
  } finally {
    suspendAutoLoad.value = false;
    loading.value = false;
  }
}

function selectSection(key: string) {
  if (!key) return;
  if (activeSection.value === key) return;
  activeSection.value = key;
  page.value = 1;
  void load();
}

function applyFilters() {
  page.value = 1;
  void load();
}

function goToPage(nextPage: number) {
  page.value = Math.max(1, Math.min(totalPages.value || 1, Number(nextPage || 1)));
  void load();
}

function scheduleAutoLoad() {
  if (autoQueryTimer) {
    clearTimeout(autoQueryTimer);
  }
  autoQueryTimer = setTimeout(() => {
    autoQueryTimer = null;
    void load();
  }, autoQueryDelayMs);
}

function saveFilterPreset() {
  try {
    window.localStorage.setItem(
      myWorkPresetStorageKey,
      JSON.stringify({
        activeSection: activeSection.value,
        searchText: searchText.value,
        sourceFilter: sourceFilter.value,
        reasonFilter: reasonFilter.value,
        sortBy: sortBy.value,
        sortDir: sortDir.value,
        pageSize: pageSize.value,
      }),
    );
    hasFilterPreset.value = true;
    actionFeedback.value = pageText('feedback_save_preset_ok', '常用筛选已保存');
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = pageText('feedback_save_preset_failed', '保存常用筛选失败');
    actionFeedbackError.value = true;
  }
}

function applyFilterPreset() {
  try {
    const raw = window.localStorage.getItem(myWorkPresetStorageKey);
    if (!raw) return;
    const parsed = JSON.parse(raw) as {
      activeSection?: string;
      searchText?: string;
      sourceFilter?: string;
      reasonFilter?: string;
      sortBy?: string;
      sortDir?: 'asc' | 'desc';
      pageSize?: number;
    };
    if (parsed.activeSection) activeSection.value = parsed.activeSection;
    if (typeof parsed.searchText === 'string') searchText.value = parsed.searchText;
    if (typeof parsed.sourceFilter === 'string') sourceFilter.value = parsed.sourceFilter;
    if (typeof parsed.reasonFilter === 'string') reasonFilter.value = parsed.reasonFilter;
    if (typeof parsed.sortBy === 'string') sortBy.value = parsed.sortBy;
    if (parsed.sortDir === 'asc' || parsed.sortDir === 'desc') sortDir.value = parsed.sortDir;
    if (typeof parsed.pageSize === 'number' && Number.isFinite(parsed.pageSize) && parsed.pageSize > 0) pageSize.value = parsed.pageSize;
    actionFeedback.value = pageText('feedback_apply_preset_ok', '已应用常用筛选');
    actionFeedbackError.value = false;
    page.value = 1;
    void load();
  } catch {
    actionFeedback.value = pageText('feedback_apply_preset_failed', '应用常用筛选失败');
    actionFeedbackError.value = true;
  }
}

function clearFilterPreset() {
  try {
    window.localStorage.removeItem(myWorkPresetStorageKey);
    hasFilterPreset.value = false;
    actionFeedback.value = pageText('feedback_clear_preset_ok', '已清除常用筛选');
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = pageText('feedback_clear_preset_failed', '清除常用筛选失败');
    actionFeedbackError.value = true;
  }
}

function resetFilters() {
  searchText.value = '';
  sourceFilter.value = 'ALL';
  reasonFilter.value = 'ALL';
  sortBy.value = 'priority';
  sortDir.value = 'desc';
  pageSize.value = 20;
  page.value = 1;
  const todoSection = sections.value.find((item) => item.key === 'todo');
  activeSection.value = todoSection?.key || sections.value[0]?.key || 'todo';
  actionFeedback.value = pageText('feedback_filters_reset', '筛选条件已重置');
  actionFeedbackError.value = false;
  void load();
}

function goWorkbench() {
  router.push({ path: '/' }).catch(() => {});
}

function goRiskCockpit() {
  router.push({ path: '/s/projects.dashboard' }).catch(() => {});
}

async function handleMyWorkBlockAction(event: PageBlockActionEvent) {
  const actionKey = String(event.actionKey || '').trim();
  const item = event.item && typeof event.item === 'object' ? event.item as Record<string, unknown> : {};
  if (actionKey === 'switch_section') {
    const sectionKey = String(item.section_key || '').trim();
    if (sectionKey) {
      selectSection(sectionKey);
      return;
    }
  }
  if (actionKey === 'open_item' || actionKey === 'focus_retry_item') {
    const itemId = Number(item.entry_id || item.id || 0);
    if (itemId > 0) {
      const record = items.value.find((row) => row.id === itemId);
      if (record) {
        openPrimaryEntry(record);
        return;
      }
    }
  }
  await executeHeaderAction(actionKey);
}

async function executeHeaderAction(actionKey: string) {
  const handled = await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: resolveWorkspaceContextQuery(),
    onRefresh: load,
    onFallback: async (key) => {
      if (key === 'open_workbench') {
        goWorkbench();
        return true;
      }
      if (key === 'open_risk_dashboard') {
        goRiskCockpit();
        return true;
      }
      if (key === 'refresh_page' || key === 'refresh') {
        await load();
        return true;
      }
      return false;
    },
  });
  if (!handled) {
    setActionFeedback(pageText('enter_error_message_fallback', '功能入口暂时不可用'), true);
  }
}

function onErrorSuggestedActionExecuted(payload: { action: string; success: boolean }) {
  actionFeedback.value = payload.success
    ? `${pageText('feedback_suggest_action_ok_prefix', '已执行建议动作：')}${payload.action || 'unknown'}`
    : `${pageText('feedback_suggest_action_failed_prefix', '建议动作执行失败：')}${payload.action || 'unknown'}`;
  actionFeedbackError.value = !payload.success;
}

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
}

function resolveRecordActionContext(modelName: string, fallback?: { actionId?: number; menuId?: number }) {
  const model = String(modelName || '').trim();
  const fallbackActionId = Number(fallback?.actionId || 0);
  const fallbackMenuId = Number(fallback?.menuId || 0);
  if (fallbackActionId > 0) {
    return {
      action_id: fallbackActionId,
      menu_id: fallbackMenuId > 0 ? fallbackMenuId : undefined,
    };
  }
  if (!model) return { action_id: undefined, menu_id: undefined };
  const node = findActionNodeByModel(session.menuTree || [], model);
  const actionId = Number(node?.meta?.action_id || 0);
  const menuId = Number(node?.menu_id || node?.id || 0);
  return {
    action_id: actionId > 0 ? actionId : undefined,
    menu_id: menuId > 0 ? menuId : undefined,
  };
}

function openScene(sceneKey: string, directTarget?: MyWorkRecordItem['target']) {
  const key = String(sceneKey || '').trim();
  if (!key) return;
  const query = resolveWorkspaceContextQuery();
  const scene = getSceneByKey(key);
  const target = directTarget || scene?.target || {};
  const targetActionId = Number(target.action_id || 0);
  const actionMeta = targetActionId > 0 ? findActionMeta(session.menuTree || [], targetActionId) : null;
  if (targetActionId > 0 && actionMeta) {
    router.push({ path: `/a/${targetActionId}`, query: { menu_id: target.menu_id || undefined, ...query } }).catch(() => {});
    return;
  }
  if (target.model && target.record_id) {
    const context = resolveRecordActionContext(String(target.model || ''), {
      actionId: Number(target.action_id || 0),
      menuId: Number(target.menu_id || 0),
    });
    if (!context.action_id) {
      router.push({ path: `/s/${key}`, query }).catch(() => {});
      return;
    }
    router
      .push({
        path: `/r/${target.model}/${target.record_id}`,
        query: { menu_id: context.menu_id, action_id: context.action_id, ...query },
      })
      .catch(() => {});
    return;
  }
  if (target.route && typeof target.route === 'string' && !target.route.startsWith('/portal/')) {
    router.push({ path: target.route, query }).catch(() => {});
    return;
  }
  router.push({ path: `/s/${key}`, query }).catch(() => {});
}

function openRecord(item: MyWorkRecordItem) {
  const target = item.target || {};
  const targetActionId = Number(target.action_id || 0);
  if (targetActionId > 0) {
    if (target.model && target.record_id) {
      router
        .push({
          path: `/r/${target.model}/${target.record_id}`,
          query: { ...resolveWorkspaceContextQuery(), menu_id: target.menu_id || undefined, action_id: targetActionId },
        })
        .catch(() => {});
      return;
    }
    router
      .push({
        path: `/a/${targetActionId}`,
        query: { ...resolveWorkspaceContextQuery(), menu_id: target.menu_id || undefined },
      })
      .catch(() => {});
    return;
  }

  if (item.model && item.record_id) {
    const scene = getSceneByKey(item.scene_key);
    const sceneTarget = scene?.target || {};
    const context = resolveRecordActionContext(String(item.model || ''), {
      actionId: Number(sceneTarget.action_id || 0),
      menuId: Number(sceneTarget.menu_id || 0),
    });
    if (!context.action_id) {
      openScene(item.scene_key, target);
      return;
    }
    router
      .push({
        path: `/r/${item.model}/${item.record_id}`,
        query: { ...resolveWorkspaceContextQuery(), menu_id: context.menu_id, action_id: context.action_id },
      })
      .catch(() => {});
    return;
  }
  openScene(item.scene_key, target);
}

function openPrimaryEntry(item: MyWorkRecordItem) {
  if (!item) return;
  openRecord(item);
}

function isCompletableTodo(item: MyWorkRecordItem) {
  return item.section === 'todo' && item.source === 'mail.activity';
}

function toggleTodoSelection(id: number, event: Event) {
  const checked = Boolean((event.target as HTMLInputElement | null)?.checked);
  const next = new Set(todoSelectionIds.value);
  if (checked) next.add(id);
  else next.delete(id);
  todoSelectionIds.value = Array.from(next).sort((a, b) => a - b);
}

function toggleAllTodoSelection(event: Event) {
  const checked = Boolean((event.target as HTMLInputElement | null)?.checked);
  if (!checked) {
    todoSelectionIds.value = todoSelectionIds.value.filter((id) => !currentTodoRows.value.includes(id));
    return;
  }
  const merged = new Set(todoSelectionIds.value);
  currentTodoRows.value.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged).sort((a, b) => a - b);
}

function clearTodoSelection() {
  todoSelectionIds.value = [];
}

function clearRetryFailed() {
  retryFailedIds.value = [];
  retryFailedItems.value = [];
  retryReasonSummary.value = [];
  retryFailedGroups.value = [];
  retryRetryableSummary.value = null;
  retryRequestParams.value = null;
  retryNoteDraft.value = '';
  todoRemaining.value = null;
  lastBatchExecutionMode.value = '';
  lastBatchReplay.value = false;
  lastBatchTraceId.value = '';
  lastReplayAuditId.value = 0;
  lastReplayAgeMs.value = 0;
  retryFilterMode.value = 'all';
  retryFailedExpanded.value = false;
  retrySearchText.value = '';
}

function buildBatchRequestId(prefix: string) {
  const stamp = Date.now().toString(36);
  const random = Math.random().toString(36).slice(2, 8);
  return `${prefix}_${stamp}_${random}`;
}

function setRetryFilterMode(mode: 'all' | 'retryable' | 'non_retryable') {
  retryFilterMode.value = mode;
  retryFailedExpanded.value = false;
}

function toggleRetryGroupByReason() {
  retryGroupByReason.value = !retryGroupByReason.value;
}

function resetRetryPanelState() {
  retryFilterMode.value = 'all';
  retryGroupByReason.value = false;
  retrySearchText.value = '';
  retryFailedExpanded.value = false;
  try {
    window.localStorage.removeItem(myWorkRetryPanelStorageKey);
  } catch {
    // Ignore remove errors in private mode.
  }
}

function toggleRetryFailedExpanded() {
  retryFailedExpanded.value = !retryFailedExpanded.value;
}

function selectRetryFailedItems() {
  const candidateIds = retryRequestParams.value?.retry_ids?.length ? retryRequestParams.value.retry_ids : retryFailedIds.value;
  if (!candidateIds.length) {
    actionFeedback.value = pageText('feedback_none_retryable', '当前没有可重试失败项');
    actionFeedbackError.value = true;
    return;
  }
  const merged = new Set(todoSelectionIds.value);
  candidateIds.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged).sort((a, b) => a - b);
}

function selectAllFailedItems() {
  const failedIds = retryFailedItems.value
    .map((item) => Number(item.id))
    .filter((id) => Number.isFinite(id) && id > 0);
  if (!failedIds.length) {
    actionFeedback.value = pageText('feedback_none_failed_selectable', '当前没有失败项可选择');
    actionFeedbackError.value = true;
    return;
  }
  const merged = new Set(todoSelectionIds.value);
  failedIds.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged).sort((a, b) => a - b);
  actionFeedback.value = `${pageText('feedback_selected_failed_prefix', '已选中 ')}${failedIds.length}${pageText('feedback_selected_failed_suffix', ' 条失败项')}`;
  actionFeedbackError.value = false;
}

function selectRetryableFailedItems() {
  const retryableIds = retryFailedItems.value
    .filter((item) => Boolean(item.retryable))
    .map((item) => Number(item.id))
    .filter((id) => Number.isFinite(id) && id > 0);
  if (!retryableIds.length) {
    actionFeedback.value = pageText('feedback_none_retryable', '当前没有可重试失败项');
    actionFeedbackError.value = true;
    return;
  }
  const merged = new Set(todoSelectionIds.value);
  retryableIds.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged).sort((a, b) => a - b);
  actionFeedback.value = `${pageText('feedback_selected_failed_prefix', '已选中 ')}${retryableIds.length}${pageText('feedback_selected_retryable_suffix', ' 条可重试失败项')}`;
  actionFeedbackError.value = false;
}

function selectNonRetryableFailedItems() {
  const ids = retryFailedItems.value
    .filter((item) => item.retryable === false)
    .map((item) => Number(item.id))
    .filter((id) => Number.isFinite(id) && id > 0);
  if (!ids.length) {
    actionFeedback.value = pageText('feedback_none_non_retryable', '当前没有不可重试失败项');
    actionFeedbackError.value = true;
    return;
  }
  const merged = new Set(todoSelectionIds.value);
  ids.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged).sort((a, b) => a - b);
  actionFeedback.value = `${pageText('feedback_selected_failed_prefix', '已选中 ')}${ids.length}${pageText('feedback_selected_non_retryable_suffix', ' 条不可重试失败项')}`;
  actionFeedbackError.value = false;
}

function failedItemRecord(id: number) {
  return todoItemMap.value.get(id);
}

function failedSuggestedActionLabel(item: { suggested_action?: string }) {
  const action = describeSuggestedAction(item.suggested_action, {
    hasRetryHandler: true,
    hasActionHandler: true,
  });
  return action.label;
}

function runFailedSuggestedAction(item: { id: number; suggested_action?: string }) {
  runSuggestedAction(item.suggested_action, {
    onRetry: load,
    onSuggestedAction: (actionRaw: string) => {
      if (actionRaw !== 'open_record') return false;
      const record = failedItemRecord(item.id);
      if (!record) return false;
      openRecord(record);
      return true;
    },
  });
}

function applyReasonFilterFromFailure(reasonCode: string) {
  if (!reasonCode) return;
  reasonFilter.value = reasonCode;
  page.value = 1;
  actionFeedback.value = `${pageText('feedback_filtered_by_reason_prefix', '已按失败原因筛选：')}${reasonCode}`;
  actionFeedbackError.value = false;
  void load();
}

function clearReasonFilterFromFailure() {
  reasonFilter.value = 'ALL';
  page.value = 1;
  actionFeedback.value = pageText('feedback_cleared_reason_filter', '已清除失败原因筛选');
  actionFeedbackError.value = false;
  void load();
}

function formatFailedItemText(item: { id: number; reason_code: string; message: string; retryable?: boolean; suggested_action?: string }) {
  const actionHint = resolveSuggestedAction(item.suggested_action, item.reason_code, item.retryable);
  const retryTag = item.retryable === true
    ? pageText('retry_tag_retryable', '可重试')
    : item.retryable === false
      ? pageText('retry_tag_non_retryable', '不可重试')
      : '';
  return [`#${item.id} ${item.reason_code || pageText('retry_unknown_reason_code', 'UNKNOWN')} ${item.message || '-'}`, retryTag, actionHint]
    .filter(Boolean)
    .join(' | ');
}

function buildRetrySummaryText() {
  if (!retryFailedItems.value.length) return '';
  const reasons = retryFailedGroups.value.length
    ? retryFailedGroups.value
        .map((item) =>
          `${item.reason_code}${pageText('retry_summary_group_count_sep', ' x ')}${item.count}${pageText('retry_summary_group_retryable_left', ' (')}${pageText('retry_group_retryable_prefix', '可重试 ')}${item.retryable_count}${pageText('retry_summary_group_retryable_right', ')')}`,
        )
        .join('; ')
    : retryReasonSummary.value
    .map((item) => `${item.reason_code}${pageText('retry_summary_group_count_sep', ' x ')}${item.count}`)
    .join('; ');
  const lines = retryFailedItems.value.map((item) => formatFailedItemText(item));
  return [
    `${pageText('retry_summary_header_prefix', '失败待办 ')}${retryFailedIds.value.length}${pageText('retry_summary_header_suffix', ' 条')}`,
    reasons ? `${pageText('retry_summary_reason_dist_prefix', '原因分布: ')}${reasons}` : '',
    typeof todoRemaining.value === 'number' ? `${pageText('retry_summary_remaining_prefix', '剩余待办: ')}${todoRemaining.value}` : '',
    ...lines,
  ]
    .filter(Boolean)
    .join('\n');
}

function buildVisibleRetrySummaryText() {
  const lines = visibleRetryFailedItems.value.map((item) => formatFailedItemText(item));
  return [
    `${pageText('retry_visible_mode_prefix', '筛选模式: ')}${retryFilterMode.value}`,
    `${pageText('retry_visible_display_prefix', '显示模式: ')}${retryGroupByReason.value ? pageText('retry_visible_display_grouped', 'grouped') : pageText('retry_visible_display_flat', 'flat')}`,
    `${pageText('retry_visible_items_prefix', '当前视图条目: ')}${visibleRetryFailedItems.value.length}`,
    ...lines,
  ]
    .filter(Boolean)
    .join('\n');
}

async function copyRetrySummary() {
  const summaryText = buildRetrySummaryText();
  if (!summaryText) return;
  try {
    await navigator.clipboard.writeText(summaryText);
    actionFeedback.value = pageText('feedback_copy_summary_ok', '失败摘要已复制');
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = pageText('feedback_copy_failed', '复制失败，请检查浏览器剪贴板权限');
    actionFeedbackError.value = true;
  }
}

async function copyFailedItemLine(item: { id: number; reason_code: string; message: string; retryable?: boolean; suggested_action?: string }) {
  const line = formatFailedItemText(item);
  if (!line) return;
  try {
    await navigator.clipboard.writeText(line);
    actionFeedback.value = `${pageText('feedback_copy_item_ok_prefix', '失败项 #')}${item.id}${pageText('feedback_copy_item_ok_suffix', ' 已复制')}`;
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = `${pageText('feedback_copy_item_failed_prefix', '复制失败项 #')}${item.id}${pageText('feedback_copy_item_failed_suffix', ' 失败')}`;
    actionFeedbackError.value = true;
  }
}

async function copyVisibleRetrySummary() {
  const summaryText = buildVisibleRetrySummaryText();
  if (!summaryText) return;
  try {
    await navigator.clipboard.writeText(summaryText);
    actionFeedback.value = pageText('feedback_copy_view_summary_ok', '当前视图摘要已复制');
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = pageText('feedback_copy_view_summary_failed', '复制当前视图摘要失败，请检查浏览器剪贴板权限');
    actionFeedbackError.value = true;
  }
}

function focusFailedInMainList() {
  if (!retryFailedItems.value.length) return;
  activeSection.value = 'todo';
  sourceFilter.value = 'mail.activity';
  reasonFilter.value = retryReasonSummary.value[0]?.reason_code || 'ALL';
  page.value = 1;
  actionFeedback.value = pageText('feedback_focus_main_failed_view', '已定位到主列表失败待办视图');
  actionFeedbackError.value = false;
  void load();
}

async function copyRetryRequest() {
  const payload = retryRequestParams.value;
  if (!payload) return;
  try {
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    actionFeedback.value = pageText('feedback_copy_retry_request_ok', '重试请求已复制');
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = pageText('feedback_copy_retry_request_failed', '复制重试请求失败，请检查浏览器剪贴板权限');
    actionFeedbackError.value = true;
  }
}

function exportRetryRequestJson() {
  if (!retryRequestParams.value) return;
  try {
    const payload = {
      ...retryRequestParams.value,
      note: retryNoteDraft.value || retryRequestParams.value.note || '',
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8;' });
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = href;
    anchor.download = `my-work-retry-request-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(href);
    actionFeedback.value = pageText('feedback_export_retry_json_ok', '重试请求 JSON 已导出');
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = pageText('feedback_export_retry_json_failed', '导出重试请求 JSON 失败');
    actionFeedbackError.value = true;
  }
}

async function copyBatchTraceId() {
  if (!lastBatchTraceId.value) return;
  try {
    await navigator.clipboard.writeText(lastBatchTraceId.value);
    actionFeedback.value = pageText('feedback_copy_trace_ok', 'trace_id 已复制');
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = pageText('feedback_copy_trace_failed', '复制 trace_id 失败，请检查浏览器剪贴板权限');
    actionFeedbackError.value = true;
  }
}

function escapeCsvCell(raw: unknown) {
  const text = String(raw ?? '');
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function buildRetryFailedCsv() {
  const header = ['id', 'reason_code', 'retryable', 'error_category', 'suggested_action', 'message', 'trace_id'];
  const rows = retryFailedItems.value.map((item) => [
    item.id,
    item.reason_code || '',
    item.retryable === true ? 'true' : item.retryable === false ? 'false' : '',
    item.error_category || '',
    item.suggested_action || '',
    item.message || '',
    item.trace_id || '',
  ]);
  return [header, ...rows]
    .map((row) => row.map((cell) => escapeCsvCell(cell)).join(','))
    .join('\n');
}

function exportRetryFailedCsv() {
  if (!retryFailedItems.value.length) return;
  try {
    const csv = buildRetryFailedCsv();
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = href;
    anchor.download = `my-work-failed-items-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.csv`;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(href);
    actionFeedback.value = `${pageText('feedback_export_failed_csv_ok_prefix', '失败明细 CSV 已导出（')}${retryFailedItems.value.length}${pageText('feedback_export_failed_csv_ok_suffix', ' 条）')}`;
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = pageText('feedback_export_failed_csv_failed', '导出失败明细 CSV 失败');
    actionFeedbackError.value = true;
  }
}

async function completeSelectedTodos() {
  if (!todoSelectionIds.value.length) return;
  if (!window.confirm(
    `${pageText('confirm_batch_complete_prefix', '确认批量完成 ')}${todoSelectionIds.value.length}${pageText('confirm_batch_complete_suffix', ' 条待办？')}`,
  )) return;
  loading.value = true;
  errorText.value = '';
  statusError.value = null;
  actionFeedback.value = '';
  actionFeedbackError.value = false;
  clearRetryFailed();
  try {
    const result = await completeMyWorkItemsBatch({
      ids: [...todoSelectionIds.value],
      source: 'mail.activity',
      note: 'Completed from my-work batch action.',
      request_id: buildBatchRequestId('mw_batch_ui'),
    });
    applyBatchFeedback(result, pageText('batch_action_complete', '批量完成'));
    await load();
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : pageText('error_batch_complete_failed', '批量完成待办失败');
    statusError.value = buildStatusError(err, errorText.value);
  } finally {
    loading.value = false;
  }
}

async function retryFailedTodos() {
  const candidateRetryIds = retryRequestParams.value?.retry_ids?.length ? retryRequestParams.value.retry_ids : retryFailedIds.value;
  if (!candidateRetryIds.length) return;
  await runRetryBatch(
    candidateRetryIds,
    resolveRetryNote('Retry failed items from my-work.'),
    retryRequestParams.value?.request_id || buildBatchRequestId('mw_retry_ui'),
    retryRequestParams.value?.source || 'mail.activity',
    pageText('batch_action_retry', '重试'),
  );
}

async function retryByReasonGroup(reasonCode: string) {
  const ids = retryFailedItems.value
    .filter((item) => item.reason_code === reasonCode && item.retryable)
    .map((item) => Number(item.id))
    .filter((id) => Number.isFinite(id) && id > 0);
  if (!ids.length) {
    actionFeedback.value = `${pageText('feedback_reason_group_no_retry_prefix', '原因组 ')}${reasonCode}${pageText('feedback_reason_group_no_retry_suffix', ' 没有可重试项')}`;
    actionFeedbackError.value = true;
    return;
  }
  await runRetryBatch(
    ids,
    resolveRetryNote(`Retry failed group ${reasonCode} from my-work.`),
    buildBatchRequestId('mw_retry_group'),
    retryRequestParams.value?.source || 'mail.activity',
    `${pageText('batch_action_retry_group_left', '重试(')}${reasonCode}${pageText('batch_action_retry_group_right', ')')}`,
  );
}

function resolveRetryNote(defaultNote: string) {
  const draft = retryNoteDraft.value.trim();
  if (draft) return draft;
  const templateNote = String(retryRequestParams.value?.note || '').trim();
  if (templateNote) return templateNote;
  return defaultNote;
}

function applyRetryNotePreset(note: string) {
  retryNoteDraft.value = note;
}

function selectRetryableByReasonGroup(reasonCode: string) {
  const ids = retryFailedItems.value
    .filter((item) => item.reason_code === reasonCode && item.retryable)
    .map((item) => Number(item.id))
    .filter((id) => Number.isFinite(id) && id > 0);
  if (!ids.length) {
    actionFeedback.value = `${pageText('feedback_reason_group_no_retry_prefix', '原因组 ')}${reasonCode}${pageText('feedback_reason_group_no_retry_suffix', ' 没有可重试项')}`;
    actionFeedbackError.value = true;
    return;
  }
  const merged = new Set(todoSelectionIds.value);
  ids.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged).sort((a, b) => a - b);
  actionFeedback.value = `${pageText('feedback_selected_reason_retryable_prefix', '已选中 ')}${ids.length}${pageText('feedback_selected_reason_retryable_middle', ' 条 ')}${reasonCode}${pageText('feedback_selected_reason_retryable_suffix', ' 可重试项')}`;
  actionFeedbackError.value = false;
}

async function runRetryBatch(
  ids: number[],
  note: string,
  requestId: string,
  source: string,
  actionLabel: string,
) {
  loading.value = true;
  errorText.value = '';
  statusError.value = null;
  try {
    const result = await completeMyWorkItemsBatch({
      ids: [...ids],
      retry_ids: [...ids],
      source,
      note,
      request_id: requestId,
    });
    applyBatchFeedback(result, actionLabel);
    await load();
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : pageText('error_retry_failed_items_failed', '重试失败项失败');
    statusError.value = buildStatusError(err, errorText.value);
  } finally {
    loading.value = false;
  }
}

function applyBatchFeedback(
  result: {
    success: boolean;
    done_count: number;
    failed_count: number;
    completed_ids?: number[];
    failed_items?: Array<{
      id: number;
      reason_code: string;
      message: string;
      retryable?: boolean;
      suggested_action?: string;
      error_category?: string;
      trace_id?: string;
    }>;
    failed_retry_ids?: number[];
    failed_reason_summary?: Array<{ reason_code: string; count: number }>;
    failed_groups?: Array<{ reason_code: string; count: number; retryable_count: number; suggested_action?: string; sample_ids?: number[] }>;
    failed_retryable_summary?: { retryable: number; non_retryable: number };
    retry_request?: { params?: { source?: string; retry_ids?: number[]; note?: string; request_id?: string } } | null;
    todo_remaining?: number;
    execution_mode?: string;
    idempotent_replay?: boolean;
    trace_id?: string;
    replay_from_audit_id?: number;
    replay_age_ms?: number;
  },
  actionLabel: string,
) {
  const completedIdSet = new Set(
    (result.completed_ids || [])
      .map((id) => Number(id))
      .filter((id) => Number.isFinite(id) && id > 0),
  );
  if (completedIdSet.size) {
    todoSelectionIds.value = todoSelectionIds.value.filter((id) => !completedIdSet.has(id));
  }
  todoRemaining.value = typeof result.todo_remaining === 'number' ? result.todo_remaining : null;
  lastBatchExecutionMode.value = String(result.execution_mode || '');
  lastBatchReplay.value = Boolean(result.idempotent_replay);
  lastBatchTraceId.value = String(result.trace_id || '');
  lastReplayAuditId.value = Math.max(0, Number(result.replay_from_audit_id || 0));
  lastReplayAgeMs.value = Math.max(0, Number(result.replay_age_ms || 0));
  const retryIdsFromResponse = Array.isArray(result.failed_retry_ids) ? result.failed_retry_ids : [];
  const retryIdsFromTemplate = Array.isArray(result.retry_request?.params?.retry_ids)
    ? result.retry_request?.params?.retry_ids || []
    : [];
  const fallbackRetryIds = (result.failed_items || [])
    .filter((item) => item.retryable)
    .map((item) => item.id);
  const mergedRetryIds = retryIdsFromResponse.length
    ? retryIdsFromResponse
    : retryIdsFromTemplate.length
      ? retryIdsFromTemplate
      : fallbackRetryIds;
  retryFailedIds.value = mergedRetryIds.filter((id) => Number.isFinite(id) && id > 0);
  retryFailedItems.value = result.failed_items || [];
  retryReasonSummary.value = (result.failed_reason_summary || []).slice(0, 5);
  retryFailedGroups.value = (result.failed_groups || []).slice(0, 5);
  retryRetryableSummary.value = result.failed_retryable_summary || null;
  retryRequestParams.value = result.retry_request?.params || null;
  retryNoteDraft.value = String(result.retry_request?.params?.note || '');

  if (!result.success) {
    const failedPreview = retryFailedItems.value
      .slice(0, 3)
      .map((item) => formatFailedItemText(item))
      .join('；');
    actionFeedback.value = `${actionLabel}${pageText('batch_feedback_partial_suffix', '部分失败：')}${result.done_count}${pageText('batch_feedback_success_count_suffix', ' 成功，')}${result.failed_count}${pageText('batch_feedback_failed_count_suffix', ' 失败')}${
      failedPreview ? `${pageText('batch_feedback_preview_left', '（')}${failedPreview}${pageText('batch_feedback_preview_right', '）')}` : ''
    }${typeof todoRemaining.value === 'number' ? `${pageText('batch_feedback_remaining_prefix', '，剩余待办 ')}${todoRemaining.value}${pageText('batch_feedback_remaining_suffix', ' 条')}` : ''}${
      lastBatchReplay.value ? `${pageText('batch_feedback_replay_prefix', '，命中重放#')}${lastReplayAuditId.value || 0}` : ''
    }`;
    actionFeedbackError.value = true;
    return;
  }

  actionFeedback.value = `${actionLabel}${pageText('batch_feedback_success_suffix', '成功：')}${result.done_count}${pageText('batch_feedback_done_suffix', ' 条')}${
    typeof todoRemaining.value === 'number' ? `${pageText('batch_feedback_remaining_prefix', '，剩余待办 ')}${todoRemaining.value}${pageText('batch_feedback_remaining_suffix', ' 条')}` : ''
  }${lastBatchReplay.value ? `${pageText('batch_feedback_replay_prefix', '，命中重放#')}${lastReplayAuditId.value || 0}` : ''}`;
  actionFeedbackError.value = false;
}

function restoreFilters() {
  try {
    const raw = window.localStorage.getItem(myWorkFilterStorageKey);
    if (!raw) return;
    const parsed = JSON.parse(raw) as {
      activeSection?: string;
      searchText?: string;
      sourceFilter?: string;
      reasonFilter?: string;
      sortBy?: string;
      sortDir?: 'asc' | 'desc';
      pageSize?: number;
    };
    if (parsed.activeSection) activeSection.value = parsed.activeSection;
    if (typeof parsed.searchText === 'string') searchText.value = parsed.searchText;
    if (typeof parsed.sourceFilter === 'string') sourceFilter.value = parsed.sourceFilter;
    if (typeof parsed.reasonFilter === 'string') reasonFilter.value = parsed.reasonFilter;
    if (typeof parsed.sortBy === 'string') sortBy.value = parsed.sortBy;
    if (parsed.sortDir === 'asc' || parsed.sortDir === 'desc') sortDir.value = parsed.sortDir;
    if (typeof parsed.pageSize === 'number' && Number.isFinite(parsed.pageSize) && parsed.pageSize > 0) pageSize.value = parsed.pageSize;
  } catch {
    // Ignore broken local cache.
  }
}

function restoreRetryPanelState() {
  try {
    const raw = window.localStorage.getItem(myWorkRetryPanelStorageKey);
    if (!raw) return;
    const parsed = JSON.parse(raw) as {
      retryFilterMode?: 'all' | 'retryable' | 'non_retryable';
      retryGroupByReason?: boolean;
      retrySearchText?: string;
    };
    if (parsed.retryFilterMode === 'all' || parsed.retryFilterMode === 'retryable' || parsed.retryFilterMode === 'non_retryable') {
      retryFilterMode.value = parsed.retryFilterMode;
    }
    if (typeof parsed.retryGroupByReason === 'boolean') {
      retryGroupByReason.value = parsed.retryGroupByReason;
    }
    if (typeof parsed.retrySearchText === 'string') {
      retrySearchText.value = parsed.retrySearchText;
    }
  } catch {
    // Ignore broken local cache.
  }
}

function applyRouteOverrides() {
  let changed = false;
  const context = readWorkspaceContext(route.query as Record<string, unknown>);
  const entryContext = parseWorkspaceEntryContext(context.entry_context);
  const preset = String(context.preset || '').trim();
  const section = String(route.query.section || entryContext.section || '').trim();
  const source = String(route.query.source || entryContext.source || '').trim();
  const reason = String(route.query.reason || entryContext.reason || '').trim();
  const search = String(context.search || entryContext.search || '').trim();
  routeContextSource.value = String(context.ctx_source || '').trim();

  const setIfDiff = <T>(target: { value: T }, next: T) => {
    if (target.value === next) return;
    target.value = next;
    changed = true;
  };

  appliedPresetLabel.value = preset ? `${pageText('preset_label_prefix', '预设视图：')}${preset}` : '';
  if (preset && preset !== lastTrackedPreset.value) {
    lastTrackedPreset.value = preset;
    void trackUsageEvent('workspace.preset.apply', { preset, view: 'my_work' }).catch(() => {});
  }
  if (!preset) {
    lastTrackedPreset.value = '';
  }

  if (section) setIfDiff(activeSection, section);
  if (source && source !== 'workspace_today') setIfDiff(sourceFilter, source);
  if (reason) setIfDiff(reasonFilter, reason);
  if (search) setIfDiff(searchText, search);
  if (changed) {
    page.value = 1;
  }
  return changed;
}

function clearRoutePreset() {
  appliedPresetLabel.value = '';
  routeContextSource.value = '';
  void trackUsageEvent('workspace.preset.clear', { view: 'my_work' }).catch(() => {});
  router.replace({ path: '/my-work' }).catch(() => {});
}

onMounted(() => {
  restoreFilters();
  restoreRetryPanelState();
  applyRouteOverrides();
  hasFilterPreset.value = Boolean(window.localStorage.getItem(myWorkPresetStorageKey));
  void load();
});

onUnmounted(() => {
  if (autoQueryTimer) {
    clearTimeout(autoQueryTimer);
    autoQueryTimer = null;
  }
});

watch([activeSection, searchText, sourceFilter, reasonFilter, sortBy, sortDir, pageSize], () => {
  try {
    window.localStorage.setItem(
      myWorkFilterStorageKey,
      JSON.stringify({
        activeSection: activeSection.value,
        searchText: searchText.value,
        sourceFilter: sourceFilter.value,
        reasonFilter: reasonFilter.value,
        sortBy: sortBy.value,
        sortDir: sortDir.value,
        pageSize: pageSize.value,
      }),
    );
  } catch {
    // Ignore persist errors in private mode.
  }
});

watch([retryFilterMode, retryGroupByReason, retrySearchText], () => {
  try {
    window.localStorage.setItem(
      myWorkRetryPanelStorageKey,
      JSON.stringify({
        retryFilterMode: retryFilterMode.value,
        retryGroupByReason: retryGroupByReason.value,
        retrySearchText: retrySearchText.value,
      }),
    );
  } catch {
    // Ignore persist errors in private mode.
  }
});

watch([activeSection, searchText, sourceFilter, reasonFilter, sortBy, sortDir, pageSize], () => {
  if (suspendAutoLoad.value) return;
  page.value = 1;
  scheduleAutoLoad();
});

watch(
  () => route.fullPath,
  () => {
    if (applyRouteOverrides()) {
      void load();
    }
  },
);
</script>

<style scoped>
.my-work {
  display: grid;
  gap: 16px;
}

.hero {
  display: grid;
  gap: 10px;
  padding: 16px;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.06), rgba(37, 99, 235, 0.05));
}

.hero-main {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.hero-tools {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.hero h2 {
  margin: 0 0 4px;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  font-size: 12px;
}

.meta-chip.replay {
  border-color: #93c5fd;
  background: #eff6ff;
  color: #1d4ed8;
}

.reason-chip {
  margin: 0 6px 6px 0;
  padding: 2px 8px;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: #f8fafc;
  color: #334155;
  font-size: 12px;
  cursor: pointer;
}

.reason-chip.active {
  border-color: #3b82f6;
  background: #dbeafe;
  color: #1d4ed8;
}

.hero p {
  margin: 0;
  color: #334155;
}

.hero-context {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.context-chip {
  border: 1px solid #dbeafe;
  border-radius: 999px;
  background: #f8fafc;
  color: #334155;
  font-size: 12px;
  line-height: 1.2;
  padding: 4px 10px;
}

.context-chip.warn {
  border-color: #fde68a;
  background: #fffbeb;
  color: #92400e;
}

.context-chip.subtle {
  border-color: #e2e8f0;
  color: #64748b;
}

.secondary {
  border: 1px solid #93c5fd;
  border-radius: 8px;
  background: #eff6ff;
  color: #1e3a8a;
  padding: 8px 10px;
  cursor: pointer;
}

@media (max-width: 780px) {
  .hero-main {
    flex-direction: column;
  }

  .hero-tools {
    width: 100%;
    justify-content: space-between;
  }
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
}

.summary-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px;
  background: #fff;
  cursor: pointer;
}

.summary-card.active {
  border-color: #2563eb;
  box-shadow: inset 0 0 0 1px #2563eb;
}

.summary-card .label {
  margin: 0;
  color: #475569;
  font-size: 13px;
}

.summary-card .count {
  margin: 6px 0 0;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}

.tabs {
  display: flex;
  gap: 8px;
}

.filters {
  display: grid;
  gap: 8px;
}

.filter-bar {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) repeat(3, auto);
  gap: 8px;
}

.filter-advanced {
  display: grid;
  grid-template-columns: repeat(5, auto);
  gap: 8px;
  align-items: center;
}

.search-input,
.filter-select {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
}

.preset-actions {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  grid-column: 1 / -1;
}

.tab {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: #fff;
  color: #334155;
  padding: 6px 10px;
  cursor: pointer;
}

.tab.active {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #1d4ed8;
}

.table-wrap {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.empty-guide {
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
  background: #f8fafc;
}

.empty-title {
  margin: 0;
  color: #0f172a;
  font-weight: 700;
}

.empty-desc {
  margin: 6px 0 0;
  color: #475569;
  font-size: 13px;
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-hint {
  margin: 0;
  color: #475569;
}

.filter-empty-guide {
  border: 1px solid #fcd34d;
  border-radius: 10px;
  background: #fff7ed;
  padding: 12px;
}

.guide-title {
  margin: 0;
  color: #9a3412;
  font-weight: 700;
}

.guide-text {
  margin: 6px 0 0;
  color: #7c2d12;
}

.guide-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}

.guide-btn {
  border: 1px solid #fed7aa;
  border-radius: 8px;
  background: #fff;
  color: #7c2d12;
  padding: 6px 10px;
  cursor: pointer;
}

.guide-btn.primary {
  border-color: #fb923c;
  background: #fed7aa;
  color: #7c2d12;
}

.pager {
  display: flex;
  align-items: center;
  gap: 10px;
}

.retry-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.retry-panel {
  border: 1px solid #fecaca;
  border-radius: 8px;
  background: #fff1f2;
}

.retry-panel > summary {
  list-style: none;
  padding: 10px 12px;
}

.retry-panel > summary::-webkit-details-marker {
  display: none;
}

.retry-expand-hint {
  margin-left: auto;
  color: #7f1d1d;
  font-size: 12px;
}

.retry-actions {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.retry-details {
  border-top: 1px solid #fecaca;
  padding: 10px 12px 12px;
}

.retry-request-preview {
  margin-top: 8px;
}

.retry-request-preview pre {
  margin: 6px 0 0;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
  color: #334155;
  font-size: 12px;
  overflow-x: auto;
}

.retry-note-editor {
  margin-top: 6px;
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: #475569;
}

.retry-note-presets {
  margin-top: 6px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.retry-note-editor textarea {
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 6px 8px;
  font-family: inherit;
  font-size: 12px;
  background: #fff;
}

.retry-details ul {
  margin: 8px 0 0;
  padding-left: 20px;
}

.retry-grouped-list {
  margin-top: 8px;
  display: grid;
  gap: 8px;
}

.retry-group-block {
  border: 1px dashed #fecaca;
  border-radius: 6px;
  padding: 6px 8px;
}

.retry-group-title {
  margin: 0;
  color: #9f1239;
  font-size: 12px;
  font-weight: 700;
}

.retry-title {
  margin: 0;
  color: #b91c1c;
  font-weight: 600;
}

.retry-toggle {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.retry-search {
  margin-top: 8px;
  width: 100%;
}

.retry-summary {
  margin: 8px 0 0;
  color: #9f1239;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.group-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.failed-id {
  font-weight: 700;
}

.failed-code {
  margin-left: 8px;
  color: #9f1239;
}

.failed-msg {
  margin-left: 8px;
  color: #7f1d1d;
}

.failed-hint {
  margin-left: 8px;
  color: #64748b;
  font-size: 12px;
}

.item-meta {
  color: #64748b;
  font-size: 12px;
}

.mini-btn {
  margin-left: 8px;
  padding: 2px 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid #f1f5f9;
}

.cell-select {
  width: 36px;
  text-align: center;
}

th {
  font-size: 12px;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: #64748b;
}

.empty {
  text-align: center;
  color: #64748b;
  padding: 20px 0;
}

.clickable-row {
  cursor: pointer;
}

.clickable-row:hover {
  background: #f8fafc;
}

.link-btn {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  padding: 6px 10px;
  cursor: pointer;
}

.secondary-btn {
  margin-left: 8px;
}

.done-btn {
  border-color: #86efac;
  background: #f0fdf4;
  color: #166534;
  margin-right: 8px;
}

.action-feedback {
  margin: 0;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #bbf7d0;
  background: #f0fdf4;
  color: #166534;
}

.action-feedback.error {
  border-color: #fecaca;
  background: #fff1f2;
  color: #b91c1c;
}

.batch-evidence {
  margin: -6px 0 0;
  color: #64748b;
  font-size: 12px;
}
</style>
