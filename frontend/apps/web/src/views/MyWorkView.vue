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
    <div v-if="!loading && !errorText && retryFailedIds.length" class="retry-bar">
      <span>失败待办 {{ retryFailedIds.length }} 条</span>
      <button class="link-btn" @click="selectRetryFailedItems">选中失败项</button>
      <button class="link-btn done-btn" @click="retryFailedTodos">重试失败项</button>
      <button class="link-btn" @click="copyRetrySummary">复制失败摘要</button>
      <button class="link-btn secondary-btn" @click="clearRetryFailed">忽略</button>
    </div>
    <section v-if="!loading && !errorText && retryFailedItems.length" class="retry-details">
      <p class="retry-title">失败明细</p>
      <p v-if="retryReasonSummary.length" class="retry-summary">
        失败原因分布：
        <span v-for="item in retryReasonSummary" :key="`reason-${item.reason_code}`">
          {{ item.reason_code }} x {{ item.count }}
        </span>
      </p>
      <ul>
        <li v-for="item in retryFailedItems" :key="`failed-${item.id}`">
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
          <button
            v-if="failedItemRecord(item.id)"
            class="link-btn mini-btn"
            @click="openRecord(failedItemRecord(item.id)!)"
          >
            打开记录
          </button>
        </li>
      </ul>
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
import {
  canRunSuggestedAction,
  executeSuggestedAction,
  parseSuggestedAction,
  suggestedActionLabel,
} from '../app/suggestedAction';

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
const retryFailedItems = ref<Array<{ id: number; reason_code: string; message: string; retryable?: boolean; suggested_action?: string }>>([]);
const retryReasonSummary = ref<Array<{ reason_code: string; count: number }>>([]);
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
  todoSelectionIds.value = Array.from(next);
}

function toggleAllTodoSelection(event: Event) {
  const checked = Boolean((event.target as HTMLInputElement | null)?.checked);
  if (!checked) {
    todoSelectionIds.value = todoSelectionIds.value.filter((id) => !currentTodoRows.value.includes(id));
    return;
  }
  const merged = new Set(todoSelectionIds.value);
  currentTodoRows.value.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged);
}

function clearTodoSelection() {
  todoSelectionIds.value = [];
}

function clearRetryFailed() {
  retryFailedIds.value = [];
  retryFailedItems.value = [];
  retryReasonSummary.value = [];
}

function selectRetryFailedItems() {
  if (!retryFailedIds.value.length) return;
  const merged = new Set(todoSelectionIds.value);
  retryFailedIds.value.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged);
}

function failedItemRecord(id: number) {
  return todoItemMap.value.get(id);
}

function failedSuggestedActionLabel(item: { suggested_action?: string }) {
  const parsed = parseSuggestedAction(item.suggested_action);
  const canRun = canRunSuggestedAction(parsed, {
    hasRetryHandler: true,
    hasActionHandler: true,
  });
  if (!canRun) return '';
  return suggestedActionLabel(parsed);
}

function runFailedSuggestedAction(item: { id: number; suggested_action?: string }) {
  const parsed = parseSuggestedAction(item.suggested_action);
  executeSuggestedAction(parsed, {
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

function formatFailedItemText(item: { id: number; reason_code: string; message: string; retryable?: boolean; suggested_action?: string }) {
  const actionHint = resolveSuggestedAction(item.suggested_action, item.reason_code, item.retryable);
  const retryTag = item.retryable === true ? 'retryable' : item.retryable === false ? 'non-retryable' : '';
  return [`#${item.id} ${item.reason_code || 'UNKNOWN'} ${item.message || '-'}`, retryTag, actionHint]
    .filter(Boolean)
    .join(' | ');
}

function buildRetrySummaryText() {
  if (!retryFailedItems.value.length) return '';
  const reasons = retryReasonSummary.value
    .map((item) => `${item.reason_code} x ${item.count}`)
    .join('; ');
  const lines = retryFailedItems.value.map((item) => formatFailedItemText(item));
  return [`失败待办 ${retryFailedIds.value.length} 条`, reasons ? `原因分布: ${reasons}` : '', ...lines]
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
  retryFailedIds.value = [];
  retryFailedItems.value = [];
  retryReasonSummary.value = [];
  try {
    const result = await completeMyWorkItemsBatch({
      ids: [...todoSelectionIds.value],
      source: 'mail.activity',
      note: 'Completed from my-work batch action.',
    });
    if (!result.success) {
      const first = result.failed_items?.[0];
      const failedPreview = (result.failed_items || [])
        .slice(0, 3)
        .map((item) => formatFailedItemText(item))
        .join('；');
      retryFailedIds.value = (result.failed_items || []).map((item) => item.id).filter((id) => Number.isFinite(id) && id > 0);
      retryFailedItems.value = (result.failed_items || []).slice(0, 10);
      retryReasonSummary.value = (result.failed_reason_summary || []).slice(0, 5);
      actionFeedback.value = `批量完成部分失败：${result.done_count} 成功，${result.failed_count} 失败${
        first ? `（${failedPreview}）` : ''
      }`;
      actionFeedbackError.value = true;
    } else {
      actionFeedback.value = `批量完成成功：${result.done_count} 条`;
      actionFeedbackError.value = false;
      retryFailedItems.value = [];
      retryReasonSummary.value = [];
    }
    await load();
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : '批量完成待办失败';
    statusError.value = buildStatusError(err, errorText.value);
  } finally {
    loading.value = false;
  }
}

async function retryFailedTodos() {
  if (!retryFailedIds.value.length) return;
  loading.value = true;
  errorText.value = '';
  statusError.value = null;
  try {
    const result = await completeMyWorkItemsBatch({
      ids: [...retryFailedIds.value],
      source: 'mail.activity',
      note: 'Retry failed items from my-work.',
    });
    if (!result.success) {
      const failedPreview = (result.failed_items || [])
        .slice(0, 3)
        .map((item) => formatFailedItemText(item))
        .join('；');
      retryFailedIds.value = (result.failed_items || []).map((item) => item.id).filter((id) => Number.isFinite(id) && id > 0);
      retryFailedItems.value = (result.failed_items || []).slice(0, 10);
      retryReasonSummary.value = (result.failed_reason_summary || []).slice(0, 5);
      actionFeedback.value = `重试后仍有失败：${result.done_count} 成功，${result.failed_count} 失败（${failedPreview}）`;
      actionFeedbackError.value = true;
    } else {
      retryFailedIds.value = [];
      retryFailedItems.value = [];
      retryReasonSummary.value = [];
      actionFeedback.value = `重试成功：${result.done_count} 条`;
      actionFeedbackError.value = false;
    }
    await load();
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : '重试失败项失败';
    statusError.value = buildStatusError(err, errorText.value);
  } finally {
    loading.value = false;
  }
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

onMounted(() => {
  restoreFilters();
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

.retry-details ul {
  margin: 8px 0 0;
  padding-left: 20px;
}

.retry-title {
  margin: 0;
  color: #b91c1c;
  font-weight: 600;
}

.retry-summary {
  margin: 8px 0 0;
  color: #9f1239;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
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
</style>
