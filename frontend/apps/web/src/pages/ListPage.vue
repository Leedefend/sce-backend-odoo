<template>
  <section class="page">
    <PageHeader
      :title="title"
      :subtitle="subtitle"
      :status="status"
      :status-label="statusLabel"
      :loading="loading"
      :on-reload="onReload"
      :mode-label="pageModeLabelText"
      :record-count="recordCountSafe"
    />

    <PageToolbar
      :loading="loading"
      :search-term="searchTerm || ''"
      :sort-options="sortOptions || []"
      :sort-value="sortValue || ''"
      :filter-value="filterValue || 'all'"
      :on-search="onSearch"
      :on-sort="onSort"
      :on-filter="onFilter"
    />

    <section v-if="summaryItems.length" class="summary-strip">
      <article v-for="item in summaryItems" :key="item.key" class="summary-card" :class="`tone-${item.tone || 'neutral'}`">
        <p class="summary-label">{{ item.label }}</p>
        <p class="summary-value">{{ item.value }}</p>
      </article>
    </section>

    <StatusPanel v-if="loading" title="正在加载列表..." variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="error?.traceId || traceId"
      :error-code="error?.code || errorCode"
      :reason-code="error?.reasonCode"
      :error-category="error?.errorCategory"
      :error-details="error?.details"
      :retryable="error?.retryable"
      :hint="errorCopy.hint || errorHint"
      :suggested-action="error?.suggestedAction"
      variant="error"
      :on-retry="onReload"
    />
    <StatusPanel
      v-else-if="status === 'empty'"
      :title="emptyCopy.title"
      :message="emptyCopy.message"
      variant="info"
      :on-retry="onReload"
    />

    <section v-if="status === 'ok' && showBatchBar" class="batch-bar">
      <span>已选 {{ selectedCount }} 条</span>
      <button type="button" :disabled="loading || !selectedCount" @click="callBatchAction('archive')">批量归档</button>
      <button type="button" :disabled="loading || !selectedCount" @click="callBatchAction('activate')">批量激活</button>
      <button v-if="showDelete" type="button" :disabled="loading || !selectedCount" @click="callBatchAction('delete')">批量删除</button>
      <template v-if="showAssign">
        <select :value="String(selectedAssigneeId || '')" :disabled="loading" @change="onAssigneeSelectChange">
          <option value="">选择负责人</option>
          <option v-for="opt in assigneeOptions || []" :key="opt.id" :value="String(opt.id)">{{ opt.name }}</option>
        </select>
        <button type="button" :disabled="loading || !selectedCount || !selectedAssigneeId" @click="callBatchAssign">批量指派</button>
      </template>
      <button type="button" :disabled="loading || !selectedCount" @click="callBatchExport('selected')">导出选中 CSV</button>
      <button type="button" :disabled="loading || !records.length" @click="callBatchExport('all')">导出当前页 CSV</button>
      <button type="button" class="ghost" :disabled="loading" @click="clearSelection">清空</button>
      <span v-if="showDelete" class="batch-note">当前按归档处理，物理删除能力未开放</span>
      <span v-if="batchMessage" class="batch-message">{{ batchMessage }}</span>
    </section>

    <section v-if="status === 'ok' && batchDetails.length" class="batch-details">
      <p v-for="(line, idx) in batchDetails" :key="idx">
        <span>{{ batchDetailText(line) }}</span>
        <button
          v-if="batchDetailActionLabel(line) && onBatchDetailAction"
          type="button"
          class="batch-detail-action"
          :disabled="loading"
          @click="runBatchDetailAction(line)"
        >
          {{ batchDetailActionLabel(line) }}
        </button>
      </p>
      <button
        v-if="hasMoreFailures"
        type="button"
        class="batch-load-more"
        :disabled="loading"
        @click="loadMoreFailures"
      >
        加载更多失败
      </button>
      <button
        v-if="failedCsvAvailable"
        type="button"
        class="batch-download"
        :disabled="loading"
        @click="downloadFailedCsv"
      >
        下载失败清单 CSV
      </button>
    </section>

    <section v-if="status === 'ok'" class="table">
      <section v-if="groupedRows.length" class="grouped-table">
        <header class="grouped-toolbar">
          <span>分组结果</span>
          <div class="grouped-toolbar-actions">
            <button
              type="button"
              class="grouped-sort-btn"
              :disabled="!groupedRows.length || !hasCollapsedGroups"
              @click="expandAllGroups"
            >
              全部展开
            </button>
            <button
              type="button"
              class="grouped-sort-btn"
              :disabled="!groupedRows.length || allGroupsCollapsed"
              @click="collapseAllGroups"
            >
              全部收起
            </button>
            <select :value="String(groupSampleLimit || 3)" @change="onGroupSampleLimitSelectChange">
              <option value="3">每组 3 条</option>
              <option value="5">每组 5 条</option>
              <option value="8">每组 8 条</option>
            </select>
            <button type="button" class="grouped-sort-btn" @click="toggleGroupSort">
              {{ groupSortLabel }}
            </button>
          </div>
        </header>
        <article v-for="group in sortedGroupedRows" :key="group.key" class="group-block">
          <header class="group-head">
            <button type="button" class="group-toggle" @click="toggleGroupCollapsed(group.key)">
              {{ isGroupCollapsed(group.key) ? '展开' : '收起' }}
            </button>
            <p>{{ group.label }}</p>
            <span>{{ group.count }} 条</span>
            <div v-if="onGroupPageChange" class="group-page">
              <button
                type="button"
                class="group-page-btn"
                :disabled="Boolean(group.loading) || !canGroupPagePrev(group)"
                @click="pageGroupPrev(group)"
              >
                上一页
              </button>
              <span>{{ groupPageInfoText(group) }}</span>
              <button
                type="button"
                class="group-page-btn"
                :disabled="Boolean(group.loading) || !canGroupPageNext(group)"
                @click="pageGroupNext(group)"
              >
                下一页
              </button>
              <input
                class="group-page-input"
                :value="groupJumpPageInput[group.key] || String(groupCurrentPage(group))"
                :disabled="Boolean(group.loading) || groupTotalPages(group) <= 1"
                inputmode="numeric"
                pattern="[0-9]*"
                @change="onGroupJumpInputChange(group.key, $event)"
              />
              <button
                type="button"
                class="group-page-btn"
                :disabled="Boolean(group.loading) || groupTotalPages(group) <= 1"
                @click="jumpGroupPage(group)"
              >
                跳转
              </button>
            </div>
            <button
              v-if="onOpenGroup"
              type="button"
              class="group-open-btn"
              @click="openGroup(group)"
            >
              查看全部
            </button>
          </header>
          <table v-if="!isGroupCollapsed(group.key)">
            <thead>
              <tr>
                <th v-for="col in displayedColumns" :key="`group-col-${group.key}-${col}`">{{ columnLabel(col) }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, index) in group.sampleRows"
                :key="`group-row-${group.key}-${String(row.id ?? index)}`"
                @click="handleRow(row)"
              >
                <td v-for="col in displayedColumns" :key="`group-cell-${group.key}-${String(row.id ?? index)}-${col}`">
                  <span
                    v-if="isStatusColumn(col)"
                    class="status-badge"
                    :class="`tone-${semanticCell(col, row[col]).tone}`"
                  >
                    {{ semanticCell(col, row[col]).text }}
                  </span>
                  <span v-else>{{ semanticCell(col, row[col]).text }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </article>
      </section>
      <table>
        <thead>
          <tr>
            <th v-if="showSelectionColumn" class="cell-select">
              <input
                type="checkbox"
                :checked="allSelected"
                :disabled="loading || !selectableRows.length"
                @click.stop
                @change="onSelectAllChange"
              />
            </th>
            <th v-for="col in displayedColumns" :key="col">{{ columnLabel(col) }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in records" :key="String(row.id ?? index)" @click="handleRow(row)">
            <td v-if="showSelectionColumn" class="cell-select" @click.stop>
              <input
                v-if="rowId(row)"
                type="checkbox"
                :checked="isSelected(row)"
                :disabled="loading"
                @change="onRowCheckboxChange(row, $event)"
              />
            </td>
            <td v-for="col in displayedColumns" :key="col">
              <div v-if="col === rowPrimary" class="cell-primary">
                <div class="primary">{{ semanticCell(col, row[col]).text }}</div>
                <div v-if="rowSecondary" class="secondary">{{ semanticCell(rowSecondary, row[rowSecondary]).text }}</div>
              </div>
              <div v-else-if="isStatusColumn(col)">
                <span class="status-badge" :class="`tone-${semanticCell(col, row[col]).tone}`">
                  {{ semanticCell(col, row[col]).text }}
                </span>
              </div>
              <div v-else>
                {{ semanticCell(col, row[col]).text }}
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import StatusPanel from '../components/StatusPanel.vue';
import PageHeader from '../components/page/PageHeader.vue';
import PageToolbar from '../components/page/PageToolbar.vue';
import { resolveEmptyCopy, resolveErrorCopy, type StatusError } from '../composables/useStatus';
import type { SceneListProfile } from '../app/resolvers/sceneRegistry';
import { semanticValueByField } from '../utils/semantic';
import { pageModeLabel } from '../app/pageMode';

type BatchDetailLine = {
  text: string;
  actionRaw?: string;
  actionLabel?: string;
};

const props = defineProps<{
  title: string;
  model: string;
  status: 'loading' | 'ok' | 'empty' | 'error';
  loading: boolean;
  errorMessage?: string;
  traceId?: string;
  errorCode?: number | null;
  errorHint?: string;
  error?: StatusError | null;
  columns: string[];
  records: Array<Record<string, unknown>>;
  onReload: () => void;
  onRowClick: (row: Record<string, unknown>) => void;
  onSearch: (value: string) => void;
  onSort: (value: string) => void;
  sortLabel?: string;
  searchTerm?: string;
  sortOptions?: Array<{ label: string; value: string }>;
  sortValue?: string;
  filterValue?: 'all' | 'active' | 'archived';
  subtitle: string;
  statusLabel: string;
  pageMode?: string;
  sceneKey?: string;
  recordCount?: number;
  listProfile?: SceneListProfile | null;
  columnLabels?: Record<string, string>;
  onFilter: (value: 'all' | 'active' | 'archived') => void;
  summaryItems?: Array<{ key: string; label: string; value: string; tone?: string }>;
  selectedIds?: number[];
  onToggleSelection?: (id: number, selected: boolean) => void;
  onToggleSelectionAll?: (ids: number[], selected: boolean) => void;
  onBatchAction?: (action: 'archive' | 'activate' | 'delete') => void;
  showDelete?: boolean;
  onBatchAssign?: (assigneeId: number) => void;
  onBatchExport?: (scope: 'selected' | 'all') => void;
  onAssigneeChange?: (assigneeId: number | null) => void;
  onClearSelection?: () => void;
  batchMessage?: string;
  batchDetails?: Array<string | BatchDetailLine>;
  failedCsvAvailable?: boolean;
  onDownloadFailedCsv?: () => void;
  hasMoreFailures?: boolean;
  onLoadMoreFailures?: () => void;
  onBatchDetailAction?: (actionRaw: string) => void;
  showAssign?: boolean;
  assigneeOptions?: Array<{ id: number; name: string }>;
  selectedAssigneeId?: number | null;
  groupedRows?: Array<{
    key: string;
    label: string;
    count: number;
    sampleRows: Array<Record<string, unknown>>;
    domain?: unknown[];
    pageOffset?: number;
    pageLimit?: number;
    pageCurrent?: number;
    pageTotal?: number;
    pageRangeStart?: number;
    pageRangeEnd?: number;
    pageWindow?: { start?: number; end?: number };
    pageHasPrev?: boolean;
    pageHasNext?: boolean;
    loading?: boolean;
  }>;
  onOpenGroup?: (group: {
    key: string;
    label: string;
    count: number;
    domain?: unknown[];
  }) => void;
  onGroupPageChange?: (group: {
    key: string;
    label: string;
    count: number;
    domain?: unknown[];
    offset: number;
    limit: number;
  }) => void;
  groupSampleLimit?: number;
  onGroupSampleLimitChange?: (limit: number) => void;
  groupSort?: 'asc' | 'desc';
  onGroupSortChange?: (next: 'asc' | 'desc') => void;
  collapsedGroupKeys?: string[];
  onGroupCollapsedChange?: (keys: string[]) => void;
}>();
const errorCopy = computed(() =>
  resolveErrorCopy(
    props.error || null,
    props.errorMessage || '列表加载失败',
  ),
);
const emptyCopy = computed(() => resolveEmptyCopy('list'));
const groupedRows = computed(() =>
  Array.isArray(props.groupedRows) ? props.groupedRows : [],
);
const groupJumpPageInput = ref<Record<string, string>>({});
const groupSortDesc = computed(() => (props.groupSort || 'desc') === 'desc');
const sortedGroupedRows = computed(() => {
  const rows = [...groupedRows.value];
  rows.sort((a, b) => {
    const cmp = Number(a.count || 0) - Number(b.count || 0);
    if (cmp === 0) return String(a.label || '').localeCompare(String(b.label || ''));
    return groupSortDesc.value ? -cmp : cmp;
  });
  return rows;
});
const groupSortLabel = computed(() => (groupSortDesc.value ? '按数量降序' : '按数量升序'));
const summaryItems = computed(() => Array.isArray(props.summaryItems) ? props.summaryItems : []);
const recordCountSafe = computed(() => {
  const raw = Number(props.recordCount);
  if (Number.isFinite(raw) && raw >= 0) return Math.trunc(raw);
  return props.records.length;
});
const pageModeLabelText = computed(() => pageModeLabel(props.pageMode || 'list'));
const collapsedSet = computed(() => new Set(Array.isArray(props.collapsedGroupKeys) ? props.collapsedGroupKeys : []));
const allGroupsCollapsed = computed(() => {
  if (!sortedGroupedRows.value.length) return false;
  return sortedGroupedRows.value.every((item) => collapsedSet.value.has(item.key));
});
const hasCollapsedGroups = computed(() => {
  if (!sortedGroupedRows.value.length) return false;
  return sortedGroupedRows.value.some((item) => collapsedSet.value.has(item.key));
});
function semanticCell(field: string, value: unknown) {
  return semanticValueByField(field, value);
}

function isStatusColumn(field: string) {
  const key = String(field || '').toLowerCase();
  return key.includes('state') || key.includes('status') || key.includes('stage');
}

function toggleGroupCollapsed(key: string) {
  if (!props.onGroupCollapsedChange) return;
  const set = new Set(collapsedSet.value);
  if (set.has(key)) set.delete(key);
  else set.add(key);
  props.onGroupCollapsedChange(Array.from(set));
}

function isGroupCollapsed(key: string) {
  return collapsedSet.value.has(key);
}

function toggleGroupSort() {
  if (!props.onGroupSortChange) return;
  props.onGroupSortChange(groupSortDesc.value ? 'asc' : 'desc');
}

function openGroup(group: { key: string; label: string; count: number; domain?: unknown[] }) {
  props.onOpenGroup?.(group);
}

function resolveGroupPageLimit(group: { pageLimit?: number }) {
  const limitRaw = Number(group.pageLimit || props.groupSampleLimit || 3);
  return Number.isFinite(limitRaw) && limitRaw > 0 ? Math.trunc(limitRaw) : 3;
}

function resolveGroupPageOffset(group: { pageOffset?: number; count: number; pageLimit?: number }) {
  const limit = resolveGroupPageLimit(group);
  const maxOffset = Math.max(0, Number(group.count || 0) - limit);
  const offsetRaw = Number(group.pageOffset || 0);
  if (!Number.isFinite(offsetRaw)) return 0;
  const clamped = Math.min(Math.max(Math.trunc(offsetRaw), 0), maxOffset);
  return Math.floor(clamped / limit) * limit;
}

function resolveGroupPageMeta(group: {
  count: number;
  pageOffset?: number;
  pageLimit?: number;
  pageCurrent?: number;
  pageTotal?: number;
  pageRangeStart?: number;
  pageRangeEnd?: number;
}) {
  const total = Math.max(0, Number(group.count || 0));
  const limit = Math.max(1, resolveGroupPageLimit(group));
  const offset = resolveGroupPageOffset(group);
  const fallbackTotal = Math.max(1, Math.ceil(total / limit));
  const fallbackCurrent = Math.floor(offset / limit) + 1;
  const fallbackStart = total > 0 ? offset + 1 : 0;
  const fallbackEnd = total > 0 ? Math.min(total, offset + limit) : 0;
  const backendTotal = Math.trunc(Number(group.pageTotal || 0));
  const backendCurrent = Math.trunc(Number(group.pageCurrent || 0));
  const backendStart = Math.trunc(Number(group.pageRangeStart || 0));
  const backendEnd = Math.trunc(Number(group.pageRangeEnd || 0));
  const backendWindow = (group as { pageWindow?: { start?: unknown; end?: unknown } }).pageWindow;
  const backendWindowStart = Math.trunc(Number(backendWindow?.start || 0));
  const backendWindowEnd = Math.trunc(Number(backendWindow?.end || 0));
  return {
    totalPages: backendTotal > 0 ? backendTotal : fallbackTotal,
    currentPage: backendCurrent > 0 ? backendCurrent : fallbackCurrent,
    rangeStart: backendWindowStart >= 0 ? backendWindowStart : (backendStart >= 0 ? backendStart : fallbackStart),
    rangeEnd: backendWindowEnd >= 0 ? backendWindowEnd : (backendEnd >= 0 ? backendEnd : fallbackEnd),
  };
}

function canGroupPagePrev(group: { count: number; pageOffset?: number; pageLimit?: number }) {
  if (typeof (group as { pageHasPrev?: unknown }).pageHasPrev === 'boolean') {
    return Boolean((group as { pageHasPrev?: unknown }).pageHasPrev);
  }
  return resolveGroupPageOffset(group) > 0;
}

function canGroupPageNext(group: { count: number; pageOffset?: number; pageLimit?: number }) {
  if (typeof (group as { pageHasNext?: unknown }).pageHasNext === 'boolean') {
    return Boolean((group as { pageHasNext?: unknown }).pageHasNext);
  }
  const offset = resolveGroupPageOffset(group);
  const limit = resolveGroupPageLimit(group);
  return offset + limit < Number(group.count || 0);
}

function groupPageRangeText(group: { count: number; pageOffset?: number; pageLimit?: number }) {
  const total = Math.max(0, Number(group.count || 0));
  if (!total) return '0 / 0';
  const meta = resolveGroupPageMeta(group);
  const start = meta.rangeStart;
  const end = meta.rangeEnd;
  return `${start}-${end} / ${total}`;
}

function groupTotalPages(group: { count: number; pageLimit?: number }) {
  return resolveGroupPageMeta(group).totalPages;
}

function groupCurrentPage(group: { count: number; pageOffset?: number; pageLimit?: number }) {
  return resolveGroupPageMeta(group).currentPage;
}

function groupPageInfoText(group: { count: number; pageOffset?: number; pageLimit?: number }) {
  return `第 ${groupCurrentPage(group)} / ${groupTotalPages(group)} 页 · ${groupPageRangeText(group)}`;
}

function pageGroupPrev(group: { key: string; label: string; count: number; domain?: unknown[]; pageOffset?: number; pageLimit?: number }) {
  if (!props.onGroupPageChange) return;
  const limit = resolveGroupPageLimit(group);
  const offset = resolveGroupPageOffset(group);
  const next = Math.max(0, offset - limit);
  props.onGroupPageChange({ key: group.key, label: group.label, count: group.count, domain: group.domain, offset: next, limit });
}

function pageGroupNext(group: { key: string; label: string; count: number; domain?: unknown[]; pageOffset?: number; pageLimit?: number }) {
  if (!props.onGroupPageChange) return;
  const limit = resolveGroupPageLimit(group);
  const offset = resolveGroupPageOffset(group);
  const maxOffset = Math.max(0, Number(group.count || 0) - limit);
  const next = Math.min(maxOffset, offset + limit);
  props.onGroupPageChange({ key: group.key, label: group.label, count: group.count, domain: group.domain, offset: next, limit });
}

function jumpGroupPage(group: { key: string; label: string; count: number; domain?: unknown[]; pageOffset?: number; pageLimit?: number }) {
  if (!props.onGroupPageChange) return;
  const totalPages = groupTotalPages(group);
  const raw = String(groupJumpPageInput.value[group.key] || '').trim();
  const page = Number(raw);
  if (!Number.isFinite(page)) return;
  const normalizedPage = Math.min(Math.max(Math.trunc(page), 1), totalPages);
  const limit = resolveGroupPageLimit(group);
  const offset = (normalizedPage - 1) * limit;
  groupJumpPageInput.value = { ...groupJumpPageInput.value, [group.key]: String(normalizedPage) };
  props.onGroupPageChange({ key: group.key, label: group.label, count: group.count, domain: group.domain, offset, limit });
}

function onGroupJumpInputChange(groupKey: string, event: Event) {
  const value = String((event.target as HTMLInputElement | null)?.value || '');
  groupJumpPageInput.value = { ...groupJumpPageInput.value, [groupKey]: value };
}

watch(
  sortedGroupedRows,
  (rows) => {
    const next: Record<string, string> = {};
    rows.forEach((group) => {
      const key = String(group.key || '').trim();
      if (!key) return;
      const existing = groupJumpPageInput.value[key];
      if (existing && existing.trim()) {
        next[key] = existing;
      } else {
        next[key] = String(groupCurrentPage(group));
      }
    });
    groupJumpPageInput.value = next;
  },
  { immediate: true },
);

function onGroupSampleLimitSelectChange(event: Event) {
  const value = Number((event.target as HTMLSelectElement | null)?.value || 0);
  if (!Number.isFinite(value)) return;
  props.onGroupSampleLimitChange?.(value);
}

function collapseAllGroups() {
  if (!props.onGroupCollapsedChange) return;
  props.onGroupCollapsedChange(sortedGroupedRows.value.map((item) => item.key));
}

function expandAllGroups() {
  if (!props.onGroupCollapsedChange) return;
  props.onGroupCollapsedChange([]);
}

function handleRow(row: Record<string, unknown>) {
  props.onRowClick(row);
}

function rowId(row: Record<string, unknown>) {
  const value = row?.id;
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? null : parsed;
  }
  return null;
}

const selectedIdSet = computed(() => new Set((props.selectedIds || []).filter((id) => Number.isFinite(id))));
const selectedCount = computed(() => (props.selectedIds || []).length);
const batchDetails = computed<Array<string | BatchDetailLine>>(() =>
  Array.isArray(props.batchDetails) ? props.batchDetails : [],
);
const selectableRows = computed(() => props.records.map((row) => rowId(row)).filter((id): id is number => typeof id === 'number'));
const showSelectionColumn = computed(() => !!props.onToggleSelection && !!props.onToggleSelectionAll && !!props.onBatchAction);
const showBatchBar = computed(() => showSelectionColumn.value);
const allSelected = computed(() => {
  const rows = selectableRows.value;
  if (!rows.length) return false;
  return rows.every((id) => selectedIdSet.value.has(id));
});

function isSelected(row: Record<string, unknown>) {
  const id = rowId(row);
  if (!id) return false;
  return selectedIdSet.value.has(id);
}

function onToggleRow(row: Record<string, unknown>, selected: boolean) {
  const id = rowId(row);
  if (!id || !props.onToggleSelection) return;
  props.onToggleSelection(id, selected);
}

function onToggleAll(selected: boolean) {
  if (!props.onToggleSelectionAll) return;
  props.onToggleSelectionAll(selectableRows.value, selected);
}

function clearSelection() {
  props.onClearSelection?.();
}

function callBatchAction(action: 'archive' | 'activate' | 'delete') {
  if (selectedCount.value <= 0) return;
  const label = action === 'archive' ? '归档' : action === 'activate' ? '激活' : '删除';
  if (!window.confirm(`确认批量${label} ${selectedCount.value} 条记录？`)) {
    return;
  }
  props.onBatchAction?.(action);
}

function callBatchAssign() {
  if (!props.selectedAssigneeId) return;
  if (selectedCount.value <= 0) return;
  if (!window.confirm(`确认将 ${selectedCount.value} 条记录批量指派给当前负责人？`)) {
    return;
  }
  props.onBatchAssign?.(props.selectedAssigneeId);
}

function callBatchExport(scope: 'selected' | 'all') {
  const count = scope === 'selected' ? selectedCount.value : props.records.length;
  if (count <= 0) return;
  const label = scope === 'selected' ? '导出选中' : '导出当前页';
  if (!window.confirm(`确认${label}（${count} 条）为 CSV？`)) {
    return;
  }
  props.onBatchExport?.(scope);
}

function onSelectAllChange(event: Event) {
  const checked = Boolean((event.target as HTMLInputElement | null)?.checked);
  onToggleAll(checked);
}

function onRowCheckboxChange(row: Record<string, unknown>, event: Event) {
  const checked = Boolean((event.target as HTMLInputElement | null)?.checked);
  onToggleRow(row, checked);
}

function onAssigneeSelectChange(event: Event) {
  const value = String((event.target as HTMLSelectElement | null)?.value || '').trim();
  if (!props.onAssigneeChange) return;
  if (!value) {
    props.onAssigneeChange(null);
    return;
  }
  const id = Number(value);
  props.onAssigneeChange(Number.isNaN(id) ? null : id);
}

function downloadFailedCsv() {
  props.onDownloadFailedCsv?.();
}

function loadMoreFailures() {
  props.onLoadMoreFailures?.();
}

function batchDetailText(line: string | BatchDetailLine) {
  if (typeof line === 'string') return line;
  return String(line?.text || '');
}

function batchDetailActionLabel(line: string | BatchDetailLine) {
  if (!line || typeof line === 'string') return '';
  return String(line.actionLabel || '');
}

function runBatchDetailAction(line: string | BatchDetailLine) {
  if (!props.onBatchDetailAction) return;
  if (!line || typeof line === 'string') return;
  const raw = String(line.actionRaw || '').trim();
  if (!raw) return;
  props.onBatchDetailAction(raw);
}

const rowPrimary = computed(() => props.listProfile?.row_primary || '');
const rowSecondary = computed(() => props.listProfile?.row_secondary || '');
const hiddenColumns = computed(() => {
  return (props.listProfile?.hidden_columns || []).reduce<Record<string, true>>((acc, col) => {
    acc[col] = true;
    return acc;
  }, {});
});
const preferredColumns = computed(() => props.listProfile?.columns || []);
const columnLabels = computed(() => props.listProfile?.column_labels || {});
const contractColumnLabels = computed(() => props.columnLabels || {});
const displayedColumns = computed(() => {
  const source = preferredColumns.value.length ? preferredColumns.value : props.columns;
  const filtered = source.filter((col) => !hiddenColumns.value[col]);
  return filtered.length ? filtered : props.columns.filter((col) => !hiddenColumns.value[col]);
});

function columnLabel(col: string) {
  return columnLabels.value[col] || contractColumnLabels.value[col] || col;
}

</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
}


.table {
  overflow: auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.summary-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  padding: 10px;
}

.summary-label {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

.summary-value {
  margin: 6px 0 0;
  font-size: 20px;
  font-weight: 700;
}

.summary-card.tone-danger { background: #fef2f2; border-color: #fecaca; color: #b91c1c; }
.summary-card.tone-warning { background: #fffbeb; border-color: #fde68a; color: #b45309; }
.summary-card.tone-success { background: #ecfdf5; border-color: #a7f3d0; color: #047857; }
.summary-card.tone-info { background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; }

.grouped-table {
  display: grid;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.grouped-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.grouped-toolbar span {
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
}

.grouped-toolbar-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.grouped-toolbar-actions select {
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: #fff;
  color: #1e3a8a;
  padding: 2px 10px;
  font-size: 12px;
}

.grouped-sort-btn {
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: #fff;
  color: #1d4ed8;
  padding: 2px 10px;
  font-size: 12px;
  cursor: pointer;
}

.group-block {
  border: 1px solid #dbeafe;
  border-radius: 10px;
  background: #fff;
  overflow: hidden;
}

.group-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-bottom: 1px solid #dbeafe;
}

.group-toggle,
.group-open-btn {
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: #fff;
  color: #1d4ed8;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.group-head p {
  margin: 0;
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
}

.group-head span {
  color: #475569;
  font-size: 12px;
}

.group-page {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #475569;
  font-size: 12px;
}

.group-page-btn {
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #fff;
  color: #1d4ed8;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.group-page-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.group-page-input {
  width: 56px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 2px 6px;
  font-size: 12px;
  color: #0f172a;
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px 12px;
}

.batch-bar button {
  border: 1px solid #cbd5e1;
  background: #fff;
  border-radius: 8px;
  padding: 6px 10px;
  cursor: pointer;
}

.batch-bar button.ghost {
  color: #475569;
}

.batch-message {
  margin-left: auto;
  font-size: 13px;
  color: #166534;
}

.batch-note {
  font-size: 12px;
  color: #64748b;
}

.batch-details {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  padding: 8px 10px;
  color: #475569;
  font-size: 13px;
}

.batch-details p {
  margin: 3px 0;
}

.batch-detail-action {
  margin-left: 8px;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.batch-download {
  margin-top: 8px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #fff;
  color: #0f172a;
  padding: 6px 10px;
  cursor: pointer;
}

.batch-load-more {
  margin-top: 8px;
  margin-right: 8px;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 6px 10px;
  cursor: pointer;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
  font-size: 14px;
}

.cell-select {
  width: 44px;
  padding-right: 4px;
}

thead th {
  position: sticky;
  top: 0;
  background: white;
  z-index: 1;
}

tr:hover {
  background: #f1f5f9;
  cursor: pointer;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 12px;
  border: 1px solid #d1d5db;
}

.status-badge.tone-success { background: #ecfdf5; color: #047857; border-color: #a7f3d0; }
.status-badge.tone-warning { background: #fffbeb; color: #b45309; border-color: #fde68a; }
.status-badge.tone-danger { background: #fef2f2; color: #b91c1c; border-color: #fecaca; }
.status-badge.tone-info { background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; }
.status-badge.tone-neutral { background: #f9fafb; color: #374151; border-color: #d1d5db; }

th:first-child,
td:first-child {
  position: sticky;
  left: 0;
  background: #fff;
  z-index: 2;
}

</style>
