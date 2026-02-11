<template>
  <section class="my-work">
    <header class="hero">
      <div>
        <h2>我的工作</h2>
        <p>统一查看待我处理、我负责、@我的、我关注的事项。</p>
      </div>
      <div class="actions">
        <button class="secondary" @click="load">刷新</button>
      </div>
    </header>

    <StatusPanel v-if="loading" title="加载我的工作中..." variant="info" />
    <StatusPanel
      v-else-if="errorText"
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="statusError?.traceId || undefined"
      :error-code="statusError?.code"
      :reason-code="statusError?.reasonCode"
      :error-category="statusError?.errorCategory"
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
    <div v-if="!loading && !errorText && retryFailedIds.length" class="retry-bar">
      <span>失败待办 {{ retryFailedIds.length }} 条</span>
      <span v-if="lastBatchExecutionMode" class="meta-chip">模式: {{ lastBatchExecutionMode }}</span>
      <span v-if="lastBatchReplay" class="meta-chip replay">重放结果</span>
      <button class="link-btn" @click="selectRetryFailedItems">选中失败项</button>
      <button class="link-btn" @click="selectAllFailedItems">选中全部失败项</button>
      <button class="link-btn" @click="selectRetryableFailedItems">仅选可重试项</button>
      <button class="link-btn" @click="selectNonRetryableFailedItems">仅选不可重试项</button>
      <button class="link-btn done-btn" @click="retryFailedTodos">重试失败项</button>
      <button class="link-btn" @click="copyRetrySummary">复制失败摘要</button>
      <button class="link-btn" @click="copyVisibleRetrySummary">复制当前视图</button>
      <button class="link-btn" :disabled="!retryFailedItems.length" @click="exportRetryFailedCsv">导出失败 CSV</button>
      <button class="link-btn" :disabled="!retryRequestParams" @click="copyRetryRequest">复制重试请求</button>
      <button class="link-btn" :disabled="!retryRequestParams" @click="exportRetryRequestJson">导出重试 JSON</button>
      <button class="link-btn" :disabled="!retryFailedItems.length" @click="focusFailedInMainList">主列表定位失败</button>
      <button class="link-btn" :disabled="!lastBatchTraceId" @click="copyBatchTraceId">复制 Trace</button>
      <button class="link-btn secondary-btn" @click="clearRetryFailed">忽略</button>
    </div>
    <section v-if="!loading && !errorText && retryFailedItems.length" class="retry-details">
      <p class="retry-title">失败明细</p>
      <details v-if="retryRequestParams" class="retry-request-preview">
        <summary>重试请求预览</summary>
        <div class="retry-note-presets">
          <button type="button" class="link-btn mini-btn" @click="applyRetryNotePreset('系统重试：网络抖动后重放')">网络抖动</button>
          <button type="button" class="link-btn mini-btn" @click="applyRetryNotePreset('系统重试：并发冲突后重放')">并发冲突</button>
          <button type="button" class="link-btn mini-btn" @click="applyRetryNotePreset('系统重试：依赖状态已满足')">依赖满足</button>
        </div>
        <label class="retry-note-editor">
          重试备注
          <textarea
            v-model="retryNoteDraft"
            rows="2"
            placeholder="可选：补充本次重试说明"
          />
        </label>
        <pre>{{ retryRequestJson }}</pre>
      </details>
      <p v-if="retryRetryableSummary" class="retry-summary">
        重试能力：可重试 {{ retryRetryableSummary.retryable }} / 不可重试 {{ retryRetryableSummary.non_retryable }}
      </p>
      <p class="retry-summary">
        当前展示 {{ visibleRetryFailedItems.length }} / {{ retryFilteredItems.length }} 条
        <button
          v-if="retryFilteredItems.length > retryPreviewLimit"
          type="button"
          class="link-btn mini-btn"
          @click="toggleRetryFailedExpanded"
        >
          {{ retryFailedExpanded ? '收起' : '展开全部' }}
        </button>
      </p>
      <input
        v-model.trim="retrySearchText"
        class="search-input retry-search"
        type="search"
        placeholder="筛选失败明细：ID / 原因码 / 消息"
      />
      <div class="retry-toggle">
        <button
          type="button"
          class="reason-chip"
          :class="{ active: retryFilterMode === 'all' }"
          @click="setRetryFilterMode('all')"
        >
          全部
        </button>
        <button
          type="button"
          class="reason-chip"
          :class="{ active: retryFilterMode === 'retryable' }"
          @click="setRetryFilterMode('retryable')"
        >
          仅可重试
        </button>
        <button
          type="button"
          class="reason-chip"
          :class="{ active: retryFilterMode === 'non_retryable' }"
          @click="setRetryFilterMode('non_retryable')"
        >
          仅不可重试
        </button>
        <button
          type="button"
          class="reason-chip"
          :class="{ active: retryGroupByReason }"
          @click="toggleRetryGroupByReason"
        >
          {{ retryGroupByReason ? '平铺显示' : '按原因分组' }}
        </button>
      </div>
      <p v-if="retryReasonSummary.length" class="retry-summary">
        失败原因分布：
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
          清除失败筛选
        </button>
      </p>
      <p v-if="retryFailedGroups.length" class="retry-summary">
        分组摘要：
        <span v-for="group in retryFailedGroups" :key="`group-${group.reason_code}`" class="group-actions">
          <button
            type="button"
            class="reason-chip"
            @click="applyReasonFilterFromFailure(group.reason_code)"
          >
            {{ group.reason_code }} ({{ group.count }} / 可重试 {{ group.retryable_count }})
          </button>
          <button
            type="button"
            class="link-btn mini-btn"
            :disabled="!group.retryable_count"
            @click="selectRetryableByReasonGroup(group.reason_code)"
          >
            选中此组
          </button>
          <button
            type="button"
            class="link-btn mini-btn"
            :disabled="!group.retryable_count"
            @click="retryByReasonGroup(group.reason_code)"
          >
            重试此组
          </button>
        </span>
      </p>
      <ul v-if="!retryGroupByReason">
        <li v-for="item in visibleRetryFailedItems" :key="`failed-${item.id}`">
          <span class="failed-id">#{{ item.id }}</span>
          <span class="failed-code">{{ item.reason_code || 'UNKNOWN' }}</span>
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
          <button class="link-btn mini-btn" @click="copyFailedItemLine(item)">复制单条</button>
          <button
            v-if="failedItemRecord(item.id)"
            class="link-btn mini-btn"
            @click="openRecord(failedItemRecord(item.id)!)"
          >
            打开记录
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
              <button class="link-btn mini-btn" @click="copyFailedItemLine(item)">复制单条</button>
            </li>
          </ul>
        </div>
      </div>
    </section>
    <template v-if="!loading && !errorText">
      <section class="summary-grid">
        <article
          v-for="item in summary"
          :key="item.key"
          class="summary-card"
          :class="{ active: activeSection === item.key }"
          @click="selectSection(item.key)"
        >
          <p class="label">{{ item.label }}</p>
          <p class="count">{{ item.count }}</p>
        </article>
      </section>

      <section class="tabs">
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

      <section class="filters">
        <input
          v-model.trim="searchText"
          class="search-input"
          type="search"
          placeholder="搜索事项 / 模型 / 动作"
          @keydown.enter="applyFilters"
        />
        <select v-model="sourceFilter" class="filter-select">
          <option value="ALL">全部来源</option>
          <option v-for="source in sourceOptions" :key="`src-${source}`" :value="source">
            {{ source }}
          </option>
        </select>
        <select v-model="reasonFilter" class="filter-select">
          <option value="ALL">全部原因码</option>
          <option v-for="reason in reasonOptions" :key="`reason-${reason}`" :value="reason">
            {{ reason }}
          </option>
        </select>
        <select v-model="sortBy" class="filter-select">
          <option value="id">排序：ID</option>
          <option value="deadline">排序：截止日</option>
          <option value="title">排序：事项标题</option>
          <option value="reason_code">排序：原因码</option>
          <option value="source">排序：来源</option>
        </select>
        <select v-model="sortDir" class="filter-select">
          <option value="desc">降序</option>
          <option value="asc">升序</option>
        </select>
        <select v-model.number="pageSize" class="filter-select">
          <option :value="10">每页 10</option>
          <option :value="20">每页 20</option>
          <option :value="40">每页 40</option>
        </select>
        <div class="preset-actions">
          <button class="link-btn mini-btn" @click="applyFilters">应用筛选</button>
          <button class="link-btn mini-btn" @click="resetFilters">重置筛选</button>
          <button class="link-btn mini-btn" @click="saveFilterPreset">保存常用筛选</button>
          <button class="link-btn mini-btn" :disabled="!hasFilterPreset" @click="applyFilterPreset">应用常用筛选</button>
          <button class="link-btn mini-btn" :disabled="!hasFilterPreset" @click="clearFilterPreset">清除预设</button>
        </div>
      </section>
      <p v-if="summaryStatus?.hint" class="status-hint">{{ summaryStatus.hint }}</p>

      <section v-if="todoSelectionIds.length" class="batch-bar">
        <span>已选 {{ todoSelectionIds.length }} 条待办</span>
        <button class="link-btn done-btn" :disabled="loading" @click="completeSelectedTodos">批量完成</button>
        <button class="link-btn secondary-btn" :disabled="loading" @click="clearTodoSelection">清空</button>
      </section>

      <section class="table-wrap">
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
              <th>分区</th>
              <th>事项</th>
              <th>模型</th>
              <th>动作</th>
              <th>原因码</th>
              <th>截止日</th>
              <th>入口</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!filteredItems.length">
              <td colspan="8" class="empty">{{ summaryStatus?.message || emptyCopy.message }}</td>
            </tr>
            <tr v-for="item in filteredItems" :key="`${item.section || 'all'}-${item.id}`">
              <td class="cell-select">
                <input
                  v-if="isCompletableTodo(item)"
                  type="checkbox"
                  :checked="todoSelectionIdSet.has(item.id)"
                  :disabled="loading"
                  @change="toggleTodoSelection(item.id, $event)"
                />
              </td>
              <td>{{ item.section_label || '-' }}</td>
              <td>{{ item.title || '-' }}</td>
              <td>{{ item.model || '-' }}</td>
              <td>{{ item.action_label || '-' }}</td>
              <td>{{ item.reason_code || '-' }}</td>
              <td>{{ item.deadline || '-' }}</td>
              <td>
                <button
                  v-if="item.section === 'todo' && item.source === 'mail.activity'"
                  class="link-btn done-btn"
                  :disabled="loading"
                  @click="completeItem(item)"
                >
                  完成待办
                </button>
                <button class="link-btn" @click="openRecord(item)">打开记录</button>
                <button class="link-btn secondary-btn" @click="openScene(item.scene_key)">进入场景</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="pager">
        <button class="link-btn" :disabled="loading || page <= 1" @click="goToPage(page - 1)">上一页</button>
        <span>第 {{ page }} / {{ totalPages }} 页</span>
        <button class="link-btn" :disabled="loading || page >= totalPages" @click="goToPage(page + 1)">下一页</button>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { completeMyWorkItem, completeMyWorkItemsBatch, fetchMyWorkSummary, type MyWorkRecordItem, type MyWorkSection, type MyWorkSummaryItem } from '../api/myWork';
import StatusPanel from '../components/StatusPanel.vue';
import { buildStatusError, resolveEmptyCopy, resolveErrorCopy, resolveSuggestedAction, type StatusError } from '../composables/useStatus';
import { describeSuggestedAction, runSuggestedAction } from '../composables/useSuggestedAction';

const router = useRouter();

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
const sortBy = ref('id');
const sortDir = ref<'asc' | 'desc'>('desc');
const page = ref(1);
const pageSize = ref(20);
const totalPages = ref(1);
const sourceFacetRows = ref<Array<{ key: string; count: number }>>([]);
const reasonFacetRows = ref<Array<{ key: string; count: number }>>([]);
const summaryStatus = ref<{ state: string; reason_code: string; message: string; hint: string } | null>(null);
const myWorkFilterStorageKey = 'sc.mywork.filters.v1';
const myWorkPresetStorageKey = 'sc.mywork.filter_preset.v1';
const myWorkRetryPanelStorageKey = 'sc.mywork.retry_panel.v1';
const hasFilterPreset = ref(false);
const errorCopy = computed(() => resolveErrorCopy(statusError.value, errorText.value || 'Failed to load my work'));
const emptyCopy = computed(() => resolveEmptyCopy('my_work'));
const todoSelectionIdSet = computed(() => new Set(todoSelectionIds.value));
const autoQueryDelayMs = 300;
let autoQueryTimer: ReturnType<typeof setTimeout> | null = null;
const suspendAutoLoad = ref(false);

const filteredItems = computed(() => items.value);
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
      source: sourceFilter.value,
      reasonCode: reasonFilter.value,
      search: searchText.value.trim(),
    });
    sections.value = Array.isArray(data.sections) ? data.sections : [];
    summary.value = Array.isArray(data.summary) ? data.summary : [];
    items.value = Array.isArray(data.items) ? data.items : [];
    summaryStatus.value = data.status || null;
    page.value = Math.max(1, Number(data.filters?.page || page.value || 1));
    pageSize.value = Math.max(1, Number(data.filters?.page_size || pageSize.value || 20));
    totalPages.value = Math.max(1, Number(data.filters?.total_pages || 1));
    sortBy.value = String(data.filters?.sort_by || sortBy.value || 'id');
    sortDir.value = (String(data.filters?.sort_dir || sortDir.value || 'desc') === 'asc' ? 'asc' : 'desc');
    sourceFacetRows.value = Array.isArray(data.facets?.source_counts) ? data.facets?.source_counts || [] : [];
    reasonFacetRows.value = Array.isArray(data.facets?.reason_code_counts) ? data.facets?.reason_code_counts || [] : [];
    todoSelectionIds.value = [];
    if (sections.value.length && !sections.value.find((sec) => sec.key === activeSection.value)) {
      activeSection.value = sections.value[0].key;
    }
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : '请求失败';
    statusError.value = buildStatusError(err, errorText.value);
  } finally {
    suspendAutoLoad.value = false;
    loading.value = false;
  }
}

function selectSection(key: string) {
  if (!key) return;
  activeSection.value = key;
  page.value = 1;
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
    actionFeedback.value = '常用筛选已保存';
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = '保存常用筛选失败';
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
    actionFeedback.value = '已应用常用筛选';
    actionFeedbackError.value = false;
    page.value = 1;
    void load();
  } catch {
    actionFeedback.value = '应用常用筛选失败';
    actionFeedbackError.value = true;
  }
}

function clearFilterPreset() {
  try {
    window.localStorage.removeItem(myWorkPresetStorageKey);
    hasFilterPreset.value = false;
    actionFeedback.value = '已清除常用筛选';
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = '清除常用筛选失败';
    actionFeedbackError.value = true;
  }
}

function resetFilters() {
  searchText.value = '';
  sourceFilter.value = 'ALL';
  reasonFilter.value = 'ALL';
  sortBy.value = 'id';
  sortDir.value = 'desc';
  pageSize.value = 20;
  page.value = 1;
  const todoSection = sections.value.find((item) => item.key === 'todo');
  activeSection.value = todoSection?.key || sections.value[0]?.key || 'todo';
  actionFeedback.value = '筛选条件已重置';
  actionFeedbackError.value = false;
  void load();
}

function onErrorSuggestedActionExecuted(payload: { action: string; success: boolean }) {
  actionFeedback.value = payload.success
    ? `已执行建议动作：${payload.action || 'unknown'}`
    : `建议动作执行失败：${payload.action || 'unknown'}`;
  actionFeedbackError.value = !payload.success;
}

function openScene(sceneKey: string) {
  if (!sceneKey) return;
  router.push({ path: `/s/${sceneKey}` }).catch(() => {});
}

function openRecord(item: MyWorkRecordItem) {
  if (item.model && item.record_id) {
    router.push({ path: `/r/${item.model}/${item.record_id}` }).catch(() => {});
    return;
  }
  openScene(item.scene_key);
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

function toggleRetryFailedExpanded() {
  retryFailedExpanded.value = !retryFailedExpanded.value;
}

function selectRetryFailedItems() {
  const candidateIds = retryRequestParams.value?.retry_ids?.length ? retryRequestParams.value.retry_ids : retryFailedIds.value;
  if (!candidateIds.length) {
    actionFeedback.value = '当前没有可重试失败项';
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
    actionFeedback.value = '当前没有失败项可选择';
    actionFeedbackError.value = true;
    return;
  }
  const merged = new Set(todoSelectionIds.value);
  failedIds.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged).sort((a, b) => a - b);
  actionFeedback.value = `已选中 ${failedIds.length} 条失败项`;
  actionFeedbackError.value = false;
}

function selectRetryableFailedItems() {
  const retryableIds = retryFailedItems.value
    .filter((item) => Boolean(item.retryable))
    .map((item) => Number(item.id))
    .filter((id) => Number.isFinite(id) && id > 0);
  if (!retryableIds.length) {
    actionFeedback.value = '当前没有可重试失败项';
    actionFeedbackError.value = true;
    return;
  }
  const merged = new Set(todoSelectionIds.value);
  retryableIds.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged).sort((a, b) => a - b);
  actionFeedback.value = `已选中 ${retryableIds.length} 条可重试失败项`;
  actionFeedbackError.value = false;
}

function selectNonRetryableFailedItems() {
  const ids = retryFailedItems.value
    .filter((item) => item.retryable === false)
    .map((item) => Number(item.id))
    .filter((id) => Number.isFinite(id) && id > 0);
  if (!ids.length) {
    actionFeedback.value = '当前没有不可重试失败项';
    actionFeedbackError.value = true;
    return;
  }
  const merged = new Set(todoSelectionIds.value);
  ids.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged).sort((a, b) => a - b);
  actionFeedback.value = `已选中 ${ids.length} 条不可重试失败项`;
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
  actionFeedback.value = `已按失败原因筛选：${reasonCode}`;
  actionFeedbackError.value = false;
  void load();
}

function clearReasonFilterFromFailure() {
  reasonFilter.value = 'ALL';
  page.value = 1;
  actionFeedback.value = '已清除失败原因筛选';
  actionFeedbackError.value = false;
  void load();
}

function formatFailedItemText(item: { id: number; reason_code: string; message: string; retryable?: boolean; suggested_action?: string }) {
  const actionHint = resolveSuggestedAction(item.suggested_action, item.reason_code, item.retryable);
  const retryTag = item.retryable === true ? 'retryable' : item.retryable === false ? 'non-retryable' : '';
  return [`#${item.id} ${item.reason_code || 'UNKNOWN'} ${item.message || '-'}`, retryTag, actionHint]
    .filter(Boolean)
    .join(' | ');
}

function buildRetrySummaryText() {
  if (!retryFailedItems.value.length) return '';
  const reasons = retryFailedGroups.value.length
    ? retryFailedGroups.value
        .map((item) => `${item.reason_code} x ${item.count} (retryable ${item.retryable_count})`)
        .join('; ')
    : retryReasonSummary.value
    .map((item) => `${item.reason_code} x ${item.count}`)
    .join('; ');
  const lines = retryFailedItems.value.map((item) => formatFailedItemText(item));
  return [
    `失败待办 ${retryFailedIds.value.length} 条`,
    reasons ? `原因分布: ${reasons}` : '',
    typeof todoRemaining.value === 'number' ? `剩余待办: ${todoRemaining.value}` : '',
    ...lines,
  ]
    .filter(Boolean)
    .join('\n');
}

function buildVisibleRetrySummaryText() {
  const lines = visibleRetryFailedItems.value.map((item) => formatFailedItemText(item));
  return [
    `筛选模式: ${retryFilterMode.value}`,
    `显示模式: ${retryGroupByReason.value ? 'grouped' : 'flat'}`,
    `当前视图条目: ${visibleRetryFailedItems.value.length}`,
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
    actionFeedback.value = '失败摘要已复制';
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = '复制失败，请检查浏览器剪贴板权限';
    actionFeedbackError.value = true;
  }
}

async function copyFailedItemLine(item: { id: number; reason_code: string; message: string; retryable?: boolean; suggested_action?: string }) {
  const line = formatFailedItemText(item);
  if (!line) return;
  try {
    await navigator.clipboard.writeText(line);
    actionFeedback.value = `失败项 #${item.id} 已复制`;
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = `复制失败项 #${item.id} 失败`;
    actionFeedbackError.value = true;
  }
}

async function copyVisibleRetrySummary() {
  const summaryText = buildVisibleRetrySummaryText();
  if (!summaryText) return;
  try {
    await navigator.clipboard.writeText(summaryText);
    actionFeedback.value = '当前视图摘要已复制';
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = '复制当前视图摘要失败，请检查浏览器剪贴板权限';
    actionFeedbackError.value = true;
  }
}

function focusFailedInMainList() {
  if (!retryFailedItems.value.length) return;
  activeSection.value = 'todo';
  sourceFilter.value = 'mail.activity';
  reasonFilter.value = retryReasonSummary.value[0]?.reason_code || 'ALL';
  page.value = 1;
  actionFeedback.value = '已定位到主列表失败待办视图';
  actionFeedbackError.value = false;
  void load();
}

async function copyRetryRequest() {
  const payload = retryRequestParams.value;
  if (!payload) return;
  try {
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    actionFeedback.value = '重试请求已复制';
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = '复制重试请求失败，请检查浏览器剪贴板权限';
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
    actionFeedback.value = '重试请求 JSON 已导出';
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = '导出重试请求 JSON 失败';
    actionFeedbackError.value = true;
  }
}

async function copyBatchTraceId() {
  if (!lastBatchTraceId.value) return;
  try {
    await navigator.clipboard.writeText(lastBatchTraceId.value);
    actionFeedback.value = 'trace_id 已复制';
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = '复制 trace_id 失败，请检查浏览器剪贴板权限';
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
    actionFeedback.value = `失败明细 CSV 已导出（${retryFailedItems.value.length} 条）`;
    actionFeedbackError.value = false;
  } catch {
    actionFeedback.value = '导出失败明细 CSV 失败';
    actionFeedbackError.value = true;
  }
}

async function completeItem(item: MyWorkRecordItem) {
  if (!item?.id || !item?.source) return;
  loading.value = true;
  actionFeedback.value = '';
  actionFeedbackError.value = false;
  retryFailedIds.value = [];
  retryFailedItems.value = [];
  retryReasonSummary.value = [];
  try {
    const result = await completeMyWorkItem({
      id: item.id,
      source: item.source,
      note: 'Completed from my-work UI.',
    });
    const actionHint = resolveSuggestedAction(result.suggested_action, result.reason_code, result.retryable);
    actionFeedback.value = [result.message || (result.success ? '待办已完成' : '完成待办失败'), actionHint]
      .filter(Boolean)
      .join(' | ');
    actionFeedbackError.value = !result.success;
    await load();
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : '完成待办失败';
    statusError.value = buildStatusError(err, errorText.value);
  } finally {
    loading.value = false;
  }
}

async function completeSelectedTodos() {
  if (!todoSelectionIds.value.length) return;
  if (!window.confirm(`确认批量完成 ${todoSelectionIds.value.length} 条待办？`)) return;
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
    applyBatchFeedback(result, '批量完成');
    await load();
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : '批量完成待办失败';
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
    '重试',
  );
}

async function retryByReasonGroup(reasonCode: string) {
  const ids = retryFailedItems.value
    .filter((item) => item.reason_code === reasonCode && item.retryable)
    .map((item) => Number(item.id))
    .filter((id) => Number.isFinite(id) && id > 0);
  if (!ids.length) {
    actionFeedback.value = `原因组 ${reasonCode} 没有可重试项`;
    actionFeedbackError.value = true;
    return;
  }
  await runRetryBatch(
    ids,
    resolveRetryNote(`Retry failed group ${reasonCode} from my-work.`),
    buildBatchRequestId('mw_retry_group'),
    retryRequestParams.value?.source || 'mail.activity',
    `重试(${reasonCode})`,
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
    actionFeedback.value = `原因组 ${reasonCode} 没有可重试项`;
    actionFeedbackError.value = true;
    return;
  }
  const merged = new Set(todoSelectionIds.value);
  ids.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged).sort((a, b) => a - b);
  actionFeedback.value = `已选中 ${ids.length} 条 ${reasonCode} 可重试项`;
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
    errorText.value = err instanceof Error ? err.message : '重试失败项失败';
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
    actionFeedback.value = `${actionLabel}部分失败：${result.done_count} 成功，${result.failed_count} 失败${
      failedPreview ? `（${failedPreview}）` : ''
    }${typeof todoRemaining.value === 'number' ? `，剩余待办 ${todoRemaining.value} 条` : ''}${
      lastBatchReplay.value ? `，命中重放#${lastReplayAuditId.value || 0}` : ''
    }`;
    actionFeedbackError.value = true;
    return;
  }

  actionFeedback.value = `${actionLabel}成功：${result.done_count} 条${
    typeof todoRemaining.value === 'number' ? `，剩余待办 ${todoRemaining.value} 条` : ''
  }${lastBatchReplay.value ? `，命中重放#${lastReplayAuditId.value || 0}` : ''}`;
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

onMounted(() => {
  restoreFilters();
  restoreRetryPanelState();
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
</script>

<style scoped>
.my-work {
  display: grid;
  gap: 16px;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 16px;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.1), rgba(37, 99, 235, 0.08));
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

.secondary {
  border: 1px solid #93c5fd;
  border-radius: 8px;
  background: #eff6ff;
  color: #1e3a8a;
  padding: 8px 10px;
  cursor: pointer;
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
  grid-template-columns: minmax(220px, 1fr) repeat(5, auto);
  gap: 8px;
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

.batch-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-hint {
  margin: 0;
  color: #475569;
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
}

.retry-details {
  border: 1px solid #fecaca;
  border-radius: 8px;
  background: #fff1f2;
  padding: 10px 12px;
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
