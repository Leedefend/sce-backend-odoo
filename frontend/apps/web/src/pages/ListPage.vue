<template>
  <PageLayout class="page">
    <template #header v-if="!compactDeliveryMode">
      <PageHeader
        :title="title"
        :subtitle="headerSubtitle"
        :status="status"
        :status-label="statusLabel"
        :loading="loading"
        :on-reload="onReload"
        :primary-action-label="primaryActionLabel"
        :on-primary-action="onPrimaryAction || undefined"
        :mode-label="headerModeLabel"
        :record-count="recordCountSafe"
      />
    </template>

    <template #filter>
      <section v-if="showUnifiedTopbar" class="unified-topbar">
        <div class="topbar-title">
          <strong>{{ title }}</strong>
          <span>{{ recordCountSafe }} 条</span>
        </div>
        <div class="topbar-search" :class="{ 'topbar-search--native': nativeLike }">
          <input
            v-model="searchInputValue"
            type="search"
            :placeholder="searchPlaceholder || '搜索'"
            :disabled="loading"
            @focus="openNativeSearchMenu"
            @click="openNativeSearchMenu"
            @keydown.escape="closeNativeSearchMenu"
            @keyup.enter="submitSearch"
          />
          <button
            v-if="nativeLike"
            type="button"
            class="search-menu-toggle"
            :class="{ active: searchMenuOpen }"
            :disabled="loading"
            @click="toggleNativeSearchMenu"
          >
            ▾
          </button>
          <button type="button" :disabled="loading" @click="submitSearch">搜索</button>
          <div v-if="showNativeSearchMenu" class="native-search-menu" @mousedown.prevent>
            <p v-if="!nativeSearchMenuHasItems" class="native-search-menu-empty">
              当前搜索视图没有可用筛选或分组
            </p>
            <section
              v-for="section in nativeSearchMenuSections"
              :key="section.key"
              class="native-search-menu-section"
            >
              <p>{{ section.label }}</p>
              <button
                v-for="item in section.items"
                :key="`${section.key}-${item.key}`"
                type="button"
                :class="{ active: isNativeSearchMenuItemActive(section.key, item.key, item.kind) }"
                :disabled="loading || !isNativeSearchMenuItemExecutable(section.key, item)"
                @click="applyNativeSearchMenuItem(section.key, item)"
              >
                {{ item.label }}
              </button>
              <button
                v-if="section.key === 'filters' && activeContractFilterKey"
                type="button"
                class="native-search-menu-clear"
                :disabled="loading"
                @click="clearNativeSearchMenuSection(section.key)"
              >
                清除筛选器
              </button>
              <button
                v-if="section.key === 'group_by' && activeGroupByField"
                type="button"
                class="native-search-menu-clear"
                :disabled="loading"
                @click="clearNativeSearchMenuSection(section.key)"
              >
                清除分组
              </button>
            </section>
          </div>
        </div>
        <div v-if="showNativeFilterChips" class="topbar-tabs topbar-tabs--contract">
          <button
            v-for="chip in quickFilters || []"
            :key="`quick-filter-${chip.key}`"
            type="button"
            :class="{ active: activeContractFilterKey === chip.key }"
            :disabled="loading"
            @click="onApplyContractFilter?.(chip.key)"
          >
            {{ chip.label }}
          </button>
          <button
            v-if="activeContractFilterKey"
            type="button"
            :disabled="loading"
            @click="onClearContractFilter?.()"
          >
            清除
          </button>
        </div>
        <div v-if="showNativeGroupChips" class="topbar-tabs topbar-tabs--group">
          <button
            v-for="chip in groupByOptions || []"
            :key="`group-by-${chip.key}`"
            type="button"
            :class="{ active: activeGroupByField === chip.key }"
            :disabled="loading"
            @click="onApplyGroupBy?.(chip.key)"
          >
            {{ chip.label }}
          </button>
          <button
            v-if="activeGroupByField"
            type="button"
            :disabled="loading"
            @click="onClearGroupBy?.()"
          >
            清除分组
          </button>
        </div>
        <div v-else-if="!nativeLike" class="topbar-tabs">
          <button
            type="button"
            :class="{ active: (filterValue || 'all') === 'all' }"
            :disabled="loading"
            @click="onFilter('all')"
          >
            全部
          </button>
          <button
            v-if="hasActiveField"
            type="button"
            :class="{ active: filterValue === 'active' }"
            :disabled="loading"
            @click="onFilter('active')"
          >
            进行中
          </button>
          <button
            v-if="hasActiveField"
            type="button"
            :class="{ active: filterValue === 'archived' }"
            :disabled="loading"
            @click="onFilter('archived')"
          >
            已归档
          </button>
        </div>
        <div class="topbar-sort" v-if="(sortOptions || []).length">
          <select :value="sortValue || ''" :disabled="loading" @change="onSortSelectChange">
            <option value="">默认排序</option>
            <option v-for="opt in sortOptions || []" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
        <div class="topbar-pagination" v-if="showFlatPagination">
          <button type="button" :disabled="loading || !canPagePrev" @click="pagePrev">上一页</button>
          <span>{{ paginationPageText }}</span>
          <button type="button" :disabled="loading || !canPageNext" @click="pageNext">下一页</button>
        </div>
        <button
          v-if="primaryActionLabel && onPrimaryAction"
          type="button"
          class="topbar-primary"
          :disabled="loading"
          @click="onPrimaryAction"
        >
          {{ primaryActionLabel }}
        </button>
      </section>
    </template>

    <template #content>

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
      retry-label="重新加载"
    />
    <StatusPanel
      v-else-if="status === 'empty'"
      :title="emptyCopy.title"
      :message="emptyMessageText"
      variant="info"
      :on-retry="onReload"
      retry-label="刷新"
    />

    <section v-if="status === 'ok' && showBatchBar && (!compactDeliveryMode || selectedCount > 0)" class="batch-bar">
      <div class="batch-bar__summary">
        <span class="batch-bar__eyebrow">批量处理</span>
        <strong class="batch-bar__count">已选 {{ selectedCount }} 条</strong>
      </div>
      <div class="batch-bar__actions">
        <button v-if="showArchive" type="button" :disabled="loading || !selectedCount" @click="callBatchAction('archive')">批量归档</button>
        <button v-if="showActivate" type="button" :disabled="loading || !selectedCount" @click="callBatchAction('activate')">批量激活</button>
        <button v-if="showDelete" type="button" class="danger" :disabled="loading || !selectedCount" @click="callBatchAction('delete')">批量删除</button>
        <template v-if="showAssign">
          <select :value="String(selectedAssigneeId || '')" :disabled="loading" @change="onAssigneeSelectChange">
            <option value="">选择负责人</option>
            <option v-for="opt in assigneeOptions || []" :key="opt.id" :value="String(opt.id)">{{ opt.name }}</option>
          </select>
          <button type="button" class="primary" :disabled="loading || !selectedCount || !selectedAssigneeId" @click="callBatchAssign">批量指派</button>
        </template>
        <button type="button" :disabled="loading || !selectedCount" @click="callBatchExport('selected')">导出选中 CSV</button>
        <button type="button" :disabled="loading || !records.length" @click="callBatchExport('all')">导出当前页 CSV</button>
        <button type="button" class="ghost" :disabled="loading" @click="clearSelection">清空</button>
      </div>
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

    <section v-if="status === 'ok' && summaryItemsSafe.length" class="summary-strip">
      <article
        v-for="item in summaryItemsSafe"
        :key="item.key"
        class="summary-card"
        :class="`tone-${item.tone || 'neutral'}`"
      >
        <p class="summary-label">{{ item.label }}</p>
        <p class="summary-value">{{ item.value }}</p>
      </article>
    </section>

    <section v-if="status === 'ok' && showDetailZone" class="table">
      <div v-if="!compactDeliveryMode && !nativeLike" class="table-hint">{{ rowActionHintText }}</div>
      <section v-if="groupedRows.length" class="grouped-table">
        <header class="grouped-toolbar">
          <span>{{ groupToolbarLabel }}</span>
          <div v-if="!nativeLike" class="grouped-toolbar-actions">
            <button
              type="button"
              class="grouped-sort-btn"
              :disabled="loading || !groupedRows.length || !hasCollapsedGroups"
              @click="expandAllGroups"
            >
              全部展开
            </button>
            <button
              type="button"
              class="grouped-sort-btn"
              :disabled="loading || !groupedRows.length || allGroupsCollapsed"
              @click="collapseAllGroups"
            >
              全部收起
            </button>
            <select :value="String(groupSampleLimit || 3)" :disabled="loading" @change="onGroupSampleLimitSelectChange">
              <option value="3">每组 3 条</option>
              <option value="5">每组 5 条</option>
              <option value="8">每组 8 条</option>
            </select>
            <button type="button" class="grouped-sort-btn" :disabled="loading || !groupedRows.length" @click="toggleGroupSort">
              {{ groupSortLabel }}
            </button>
          </div>
        </header>
        <article v-for="group in sortedGroupedRows" :key="group.key" class="group-block">
          <header class="group-head">
            <button
              type="button"
              class="group-toggle"
              :disabled="loading || Boolean(group.loading)"
              @click="toggleGroupCollapsed(group.key)"
            >
              {{ isGroupCollapsed(group.key) ? '展开' : '收起' }}
            </button>
            <p>{{ group.label }}</p>
            <span>{{ group.count }} 条</span>
            <div v-if="!nativeLike && onGroupPageChange" class="group-page">
              <button
                type="button"
                class="group-page-btn"
                :disabled="loading || Boolean(group.loading) || !canGroupPagePrev(group)"
                @click="pageGroupPrev(group)"
              >
                上一页
              </button>
              <span>{{ groupPageInfoText(group) }}</span>
              <button
                type="button"
                class="group-page-btn"
                :disabled="loading || Boolean(group.loading) || !canGroupPageNext(group)"
                @click="pageGroupNext(group)"
              >
                下一页
              </button>
              <input
                class="group-page-input"
                :value="groupJumpPageInput[group.key] || String(groupCurrentPage(group))"
                :disabled="loading || Boolean(group.loading) || groupTotalPages(group) <= 1"
                inputmode="numeric"
                pattern="[0-9]*"
                @change="onGroupJumpInputChange(group.key, $event)"
              />
              <button
                type="button"
                class="group-page-btn"
                :disabled="loading || Boolean(group.loading) || groupTotalPages(group) <= 1"
                @click="jumpGroupPage(group)"
              >
                跳转
              </button>
            </div>
            <button
              v-if="!nativeLike && onOpenGroup"
              type="button"
              class="group-open-btn"
              :disabled="loading || Boolean(group.loading)"
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
                :class="rowToneClass(row)"
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
                  <div v-else-if="isOwnerColumn(col)" class="cell-inline-meta">
                    <span class="cell-inline-meta__label">{{ columnLabel(col) }}</span>
                    <strong class="cell-inline-meta__value">{{ semanticCell(col, row[col]).text }}</strong>
                  </div>
                  <div v-else-if="isProgressColumn(col)" class="cell-progress">
                    <span class="cell-progress__label">{{ columnLabel(col) }}</span>
                    <strong class="cell-progress__value">{{ semanticCell(col, row[col]).text }}</strong>
                  </div>
                  <span v-else>{{ semanticCell(col, row[col]).text }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </article>
      </section>
      <table v-if="!groupedRows.length">
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
          <tr v-for="(row, index) in records" :key="String(row.id ?? index)" :class="rowToneClass(row)" @click="handleRow(row)">
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
              <div v-else-if="isStatusColumn(col) || isRiskColumn(col)">
                <span class="status-badge" :class="`tone-${semanticCell(col, row[col]).tone}`">
                  {{ semanticCell(col, row[col]).text }}
                </span>
              </div>
              <div v-else-if="isOwnerColumn(col)" class="cell-inline-meta">
                <span class="cell-inline-meta__label">{{ columnLabel(col) }}</span>
                <strong class="cell-inline-meta__value">{{ semanticCell(col, row[col]).text }}</strong>
              </div>
              <div v-else-if="isProgressColumn(col)" class="cell-progress">
                <span class="cell-progress__label">{{ columnLabel(col) }}</span>
                <strong class="cell-progress__value">{{ semanticCell(col, row[col]).text }}</strong>
              </div>
              <div v-else>
                {{ semanticCell(col, row[col]).text }}
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
    <StatusPanel
      v-else-if="status === 'ok'"
      title="当前列表语义未开放详情区"
      message="semantic_page 未声明 detail_zone，已按契约隐藏列表主体。"
      variant="info"
      :on-retry="onReload"
      retry-label="刷新"
    />
    </template>
  </PageLayout>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import StatusPanel from '../components/StatusPanel.vue';
import PageHeader from '../components/page/PageHeader.vue';
import PageLayout from '../components/page/PageLayout.vue';
import { resolveEmptyCopy, resolveErrorCopy, type StatusError } from '../composables/useStatus';
import type { SceneListProfile } from '../app/resolvers/sceneRegistry';
import { semanticValueByField } from '../utils/semantic';
import { pageModeLabel } from '../app/pageMode';

type BatchDetailLine = {
  text: string;
  actionRaw?: string;
  actionLabel?: string;
};

type ToolbarChip = {
  key: string;
  label: string;
};

type NativeSearchMenuItem = {
  key: string;
  label: string;
  kind?: string;
  field?: string;
  section?: string;
  source?: string;
  domain_raw?: string;
  context_raw?: string;
  default?: boolean;
  is_default?: boolean;
  executable?: boolean;
};

type NativeSearchMenuSection = {
  key: string;
  label: string;
  items: NativeSearchMenuItem[];
};

type NativeSearchMenu = {
  interaction_model?: string;
  sections?: NativeSearchMenuSection[];
  controls?: NativeSearchMenuItem[];
};

type ToolbarSection = {
  key: string;
  kind: string;
  priority: number;
  visible: boolean;
  collapsible: boolean;
  defaultOpen: boolean;
};

type OptimizationComposition = {
  toolbarSections?: ToolbarSection[];
  activeConditions?: {
    visible?: boolean;
    include?: string[];
    mergeRules?: Record<string, unknown>;
  };
  highFrequencyFilters?: Array<{ key: string }>;
  advancedFilters?: {
    visible?: boolean;
    collapsible?: boolean;
    defaultOpen?: boolean;
    source?: Record<string, unknown>;
  };
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
  sortSourceLabel?: string;
  searchTerm?: string;
  searchPlaceholder?: string;
  sortOptions?: Array<{ label: string; value: string }>;
  sortValue?: string;
  filterValue?: 'all' | 'active' | 'archived';
  hasActiveField?: boolean;
  quickFilters?: ToolbarChip[];
  savedFilters?: ToolbarChip[];
  groupByOptions?: ToolbarChip[];
  nativeSearchMenu?: NativeSearchMenu | null;
  searchPanelOptions?: ToolbarChip[];
  searchableFieldOptions?: ToolbarChip[];
  searchableFieldTotalCount?: number;
  searchableFieldCountLabel?: string;
  savedFilterCountLabel?: string;
  groupByCountLabel?: string;
  searchPanelCountLabel?: string;
  routePresetLabel?: string;
  routePresetSource?: string;
  searchModeLabel?: string;
  optimizationComposition?: OptimizationComposition | null;
  activeContractFilterKey?: string;
  activeSavedFilterKey?: string;
  activeGroupByField?: string;
  subtitle: string;
  statusLabel: string;
  pageMode?: string;
  sceneKey?: string;
  semanticZones?: Array<Record<string, unknown>>;
  recordCount?: number;
  primaryActionLabel?: string;
  onPrimaryAction?: (() => void) | null;
  listProfile?: SceneListProfile | null;
  columnLabels?: Record<string, string>;
  onFilter: (value: 'all' | 'active' | 'archived') => void;
  onApplyContractFilter?: (key: string) => void;
  onClearContractFilter?: () => void;
  onApplySavedFilter?: (key: string) => void;
  onClearSavedFilter?: () => void;
  onApplyGroupBy?: (key: string) => void;
  onClearGroupBy?: () => void;
  onClearRoutePreset?: () => void;
  summaryItems?: Array<{ key: string; label: string; value: string; tone?: string }>;
  selectedIds?: number[];
  onToggleSelection?: (id: number, selected: boolean) => void;
  onToggleSelectionAll?: (ids: number[], selected: boolean) => void;
  onBatchAction?: (action: 'archive' | 'activate' | 'delete') => void;
  showDelete?: boolean;
  showArchive?: boolean;
  showActivate?: boolean;
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
  pageOffset?: number;
  pageLimit?: number;
  pageTotal?: number | null;
  onPageChange?: (nextOffset: number) => void;
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
  nativeLike?: boolean;
}>();
const errorCopy = computed(() =>
  resolveErrorCopy(
    props.error || null,
    props.errorMessage || '列表加载失败',
  ),
);
const emptyCopy = computed(() =>
  resolveEmptyCopy('list', { primaryActionLabel: props.primaryActionLabel }),
);
const emptyMessageText = computed(() => {
  if (props.nativeLike) return emptyCopy.value.message;
  const pageTitle = String(props.title || '').trim();
  if (pageTitle.includes('投标')) {
    const actionLabel = String(props.primaryActionLabel || '').trim() || '新建记录';
    return `当前暂无投标数据。建议先点击“${actionLabel}”创建一条示例投标，再返回列表继续办理。`;
  }
  return emptyCopy.value.message;
});
const groupedRows = computed(() =>
  Array.isArray(props.groupedRows) ? props.groupedRows : [],
);
const groupJumpPageInput = ref<Record<string, string>>({});
const groupSortDesc = computed(() => (props.groupSort || 'desc') === 'desc');
const sortedGroupedRows = computed(() => {
  const rows = [...groupedRows.value];
  if (props.nativeLike) return rows;
  rows.sort((a, b) => {
    const cmp = Number(a.count || 0) - Number(b.count || 0);
    if (cmp === 0) return String(a.label || '').localeCompare(String(b.label || ''));
    return groupSortDesc.value ? -cmp : cmp;
  });
  return rows;
});
const groupSortLabel = computed(() => (groupSortDesc.value ? '按数量降序' : '按数量升序'));
const groupToolbarLabel = computed(() => {
  const activeLabel = String(props.groupByOptions?.find((item) => item.key === props.activeGroupByField)?.label || '').trim();
  if (activeLabel) return activeLabel;
  return props.nativeLike ? '分组' : '分组结果';
});
const searchMenuOpen = ref(false);
const nativeSearchMenuSections = computed<NativeSearchMenuSection[]>(() => {
  if (!props.nativeLike) return [];
  const fallbackSections: NativeSearchMenuSection[] = [
    { key: 'filters', label: '筛选', items: nativeMenuItemsFromChips(props.quickFilters || [], 'filters') },
    { key: 'group_by', label: '分组方式', items: nativeMenuItemsFromChips(props.groupByOptions || [], 'group_by') },
    { key: 'favorites', label: '收藏夹', items: nativeMenuItemsFromChips(props.savedFilters || [], 'favorites') },
    { key: 'searchpanel', label: '搜索面板', items: nativeMenuItemsFromChips(props.searchPanelOptions || [], 'searchpanel') },
  ];
  const sections = Array.isArray(props.nativeSearchMenu?.sections) ? props.nativeSearchMenu.sections : fallbackSections;
  const controls = Array.isArray(props.nativeSearchMenu?.controls)
    ? props.nativeSearchMenu.controls
    : [];
  const normalized = sections
    .map((section) => {
      const key = String(section?.key || '').trim();
      const label = String(section?.label || key).trim();
      const items = Array.isArray(section?.items) ? section.items : [];
      const sectionControls = controls.filter((item) => String((item as { section?: string })?.section || '').trim() === key);
      return {
        key,
        label,
        items: [...items, ...sectionControls]
          .map((item) => normalizeNativeSearchMenuItem(item, key))
          .filter((item) => item.key && item.label),
      };
    })
    .filter((section) => section.key && section.label);
  if (normalized.some((section) => section.items.length > 0)) return normalized;
  return fallbackSections;
});
const nativeSearchMenuDeclared = computed(() =>
  props.nativeLike,
);
const nativeSearchMenuHasItems = computed(() =>
  nativeSearchMenuSections.value.some((section) => section.items.length > 0),
);
const showNativeSearchMenu = computed(() => props.nativeLike && searchMenuOpen.value && nativeSearchMenuDeclared.value);
const showNativeFilterChips = computed(() => false);
const showNativeGroupChips = computed(() => false);
const rowActionHintText = computed(() => {
  if (props.nativeLike) return '';
  if (groupedRows.value.length > 0) {
    return '点击分组内记录查看详情；可使用“展开/收起”“查看全部”继续处理分组数据';
  }
  const pageTitle = String(props.title || '').trim();
  const actionLabel = String(props.primaryActionLabel || '').trim();
  if (pageTitle.includes('预算') || pageTitle.includes('成本')) {
    if (actionLabel) return `先选择一条记录查看详情；新增请点击右上角“${actionLabel}”`;
    return '先选择一条记录查看详情，再继续预算/成本处理';
  }
  if (actionLabel) return `点击列表行可查看详情；新增请使用右上角“${actionLabel}”`;
  return '点击列表行可查看详情并继续处理';
});
const semanticZoneKeySet = computed(() => {
  const rows = Array.isArray(props.semanticZones) ? props.semanticZones : [];
  const keys = rows
    .map((item) => String((item && typeof item === 'object' && !Array.isArray(item) ? item.key : '') || '').trim())
    .filter(Boolean);
  return new Set(keys);
});
const showActionZone = computed(() => semanticZoneKeySet.value.size === 0 || semanticZoneKeySet.value.has('action_zone'));
const showDetailZone = computed(() => semanticZoneKeySet.value.size === 0 || semanticZoneKeySet.value.has('detail_zone'));
const recordCountSafe = computed(() => {
  const raw = Number(props.recordCount);
  if (Number.isFinite(raw) && raw >= 0) return Math.trunc(raw);
  return props.records.length;
});
const paginationLimit = computed(() => {
  const raw = Number(props.pageLimit || 0);
  if (Number.isFinite(raw) && raw > 0) return Math.trunc(raw);
  return 0;
});
const paginationOffset = computed(() => {
  const raw = Number(props.pageOffset || 0);
  if (Number.isFinite(raw) && raw >= 0) return Math.trunc(raw);
  return 0;
});
const paginationTotal = computed(() => {
  const raw = Number(props.pageTotal);
  if (Number.isFinite(raw) && raw >= 0) return Math.trunc(raw);
  return recordCountSafe.value;
});
const showPagination = computed(() => {
  return Boolean(props.onPageChange)
    && paginationLimit.value > 0
    && paginationTotal.value > paginationLimit.value;
});
const showFlatPagination = computed(() => showPagination.value && !groupedRows.value.length);
const paginationCurrentPage = computed(() => {
  if (paginationLimit.value <= 0) return 1;
  return Math.floor(paginationOffset.value / paginationLimit.value) + 1;
});
const paginationTotalPages = computed(() => {
  if (paginationLimit.value <= 0) return 1;
  return Math.max(1, Math.ceil(paginationTotal.value / paginationLimit.value));
});
const canPagePrev = computed(() => paginationOffset.value > 0);
const canPageNext = computed(() => paginationOffset.value + paginationLimit.value < paginationTotal.value);
const paginationPageText = computed(() => `${paginationCurrentPage.value} / ${paginationTotalPages.value} 页`);
const pageModeLabelText = computed(() => pageModeLabel(props.pageMode || 'list'));
const compactDeliveryMode = computed(() => String(import.meta.env.VITE_UI_COMPACT_MODE || '1').trim() !== '0');
const headerSubtitle = computed(() => compactDeliveryMode.value || props.nativeLike ? '' : props.subtitle);
const headerModeLabel = computed(() => compactDeliveryMode.value || props.nativeLike ? '' : pageModeLabelText.value);
const showUnifiedTopbar = computed(() => showActionZone.value);
const summaryItemsSafe = computed(() => Array.isArray(props.summaryItems) ? props.summaryItems.slice(0, 4) : []);
const searchInputValue = ref(String(props.searchTerm || ''));
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

function isRiskColumn(field: string) {
  const key = String(field || '').toLowerCase();
  return key.includes('risk') || key.includes('warning') || key.includes('alert') || key.includes('priority');
}

function isOwnerColumn(field: string) {
  const key = String(field || '').toLowerCase();
  return key.includes('manager') || key.includes('owner') || key.includes('assignee') || key.includes('user');
}

function isProgressColumn(field: string) {
  const key = String(field || '').toLowerCase();
  return key.includes('progress') || key.includes('rate') || key.includes('percent') || key.includes('completion');
}

function rowToneClass(row: Record<string, unknown>) {
  for (const col of displayedColumns.value) {
    if (!isStatusColumn(col) && !isRiskColumn(col)) continue;
    const tone = String(semanticCell(col, row[col]).tone || '').trim();
    if (tone === 'danger') return 'row-tone-danger';
    if (tone === 'warning') return 'row-tone-warning';
    if (tone === 'success') return 'row-tone-success';
    if (tone === 'info') return 'row-tone-info';
  }
  return '';
}

function toggleGroupCollapsed(key: string) {
  if (props.loading) return;
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
  if (props.loading) return;
  if (!props.onGroupSortChange) return;
  props.onGroupSortChange(groupSortDesc.value ? 'asc' : 'desc');
}

function openGroup(group: { key: string; label: string; count: number; domain?: unknown[] }) {
  if (props.loading) return;
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
  if (props.loading) return;
  if (!props.onGroupPageChange) return;
  const limit = resolveGroupPageLimit(group);
  const offset = resolveGroupPageOffset(group);
  const next = Math.max(0, offset - limit);
  props.onGroupPageChange({ key: group.key, label: group.label, count: group.count, domain: group.domain, offset: next, limit });
}

function pageGroupNext(group: { key: string; label: string; count: number; domain?: unknown[]; pageOffset?: number; pageLimit?: number }) {
  if (props.loading) return;
  if (!props.onGroupPageChange) return;
  const limit = resolveGroupPageLimit(group);
  const offset = resolveGroupPageOffset(group);
  const maxOffset = Math.max(0, Number(group.count || 0) - limit);
  const next = Math.min(maxOffset, offset + limit);
  props.onGroupPageChange({ key: group.key, label: group.label, count: group.count, domain: group.domain, offset: next, limit });
}

function jumpGroupPage(group: { key: string; label: string; count: number; domain?: unknown[]; pageOffset?: number; pageLimit?: number }) {
  if (props.loading) return;
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
  if (props.loading) return;
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

watch(
  () => props.searchTerm,
  (value) => {
    searchInputValue.value = String(value || '');
  },
  { immediate: true },
);

function openNativeSearchMenu() {
  if (!props.nativeLike || props.loading || !nativeSearchMenuDeclared.value) return;
  searchMenuOpen.value = true;
}

function closeNativeSearchMenu() {
  searchMenuOpen.value = false;
}

function toggleNativeSearchMenu() {
  if (!props.nativeLike || props.loading || !nativeSearchMenuDeclared.value) return;
  searchMenuOpen.value = !searchMenuOpen.value;
}

function nativeMenuItemsFromChips(rows: ToolbarChip[], kind: string): NativeSearchMenuItem[] {
  return rows
    .map((item) => ({
      key: String(item?.key || '').trim(),
      label: String(item?.label || item?.key || '').trim(),
      kind,
      executable: true,
    }))
    .filter((item) => item.key && item.label);
}

function normalizeNativeSearchMenuItem(item: NativeSearchMenuItem, fallbackKind: string): NativeSearchMenuItem {
  const source = String((item as { source?: string })?.source || '').trim();
  const domainRaw = String((item as { domain_raw?: string })?.domain_raw || '').trim();
  const contextRaw = String((item as { context_raw?: string })?.context_raw || '').trim();
  const isDefault = item?.default === true || item?.is_default === true;
  const executable = item?.executable === true
    || (source !== 'action_domain' && !isDefault && Boolean(domainRaw || contextRaw || item?.field));
  return {
    key: String(item?.key || '').trim(),
    label: String(item?.label || item?.key || '').trim(),
    kind: String(item?.kind || fallbackKind).trim() || fallbackKind,
    field: String(item?.field || '').trim(),
    section: String(item?.section || '').trim(),
    source,
    domain_raw: domainRaw,
    context_raw: contextRaw,
    default: item?.default,
    is_default: item?.is_default,
    executable,
  };
}

function isNativeSearchMenuItemExecutable(sectionKey: string, item: NativeSearchMenuItem) {
  if (item.kind === 'control') return false;
  if (sectionKey === 'searchpanel') return false;
  return item.executable === true;
}

function isNativeSearchMenuItemActive(sectionKey: string, itemKey: string, kind?: string) {
  if (kind === 'control') return false;
  if (sectionKey === 'filters') return String(props.activeContractFilterKey || '') === itemKey;
  if (sectionKey === 'favorites') return String(props.activeSavedFilterKey || '') === itemKey;
  if (sectionKey === 'group_by') return String(props.activeGroupByField || '') === itemKey;
  return false;
}

function applyNativeSearchMenuItem(sectionKey: string, item: NativeSearchMenuItem) {
  const itemKey = String(item?.key || '').trim();
  if (props.loading || !itemKey) return;
  if (!isNativeSearchMenuItemExecutable(sectionKey, item)) return;
  if (sectionKey === 'filters') {
    props.onApplyContractFilter?.(itemKey);
  } else if (sectionKey === 'favorites') {
    props.onApplySavedFilter?.(itemKey);
  } else if (sectionKey === 'group_by') {
    props.onApplyGroupBy?.(itemKey);
  }
  closeNativeSearchMenu();
}

function clearNativeSearchMenuSection(sectionKey: string) {
  if (props.loading) return;
  if (sectionKey === 'filters') {
    props.onClearContractFilter?.();
  } else if (sectionKey === 'favorites') {
    props.onClearSavedFilter?.();
  } else if (sectionKey === 'group_by') {
    props.onClearGroupBy?.();
  }
  closeNativeSearchMenu();
}

function submitSearch() {
  if (props.loading) return;
  props.onSearch(searchInputValue.value || '');
}

function onSortSelectChange(event: Event) {
  if (props.loading) return;
  const value = String((event.target as HTMLSelectElement | null)?.value || '');
  props.onSort(value);
}

function onGroupSampleLimitSelectChange(event: Event) {
  if (props.loading) return;
  const value = Number((event.target as HTMLSelectElement | null)?.value || 0);
  if (!Number.isFinite(value)) return;
  props.onGroupSampleLimitChange?.(value);
}

function collapseAllGroups() {
  if (props.loading) return;
  if (!props.onGroupCollapsedChange) return;
  props.onGroupCollapsedChange(sortedGroupedRows.value.map((item) => item.key));
}

function expandAllGroups() {
  if (props.loading) return;
  if (!props.onGroupCollapsedChange) return;
  props.onGroupCollapsedChange([]);
}

function handleRow(row: Record<string, unknown>) {
  if (props.loading) return;
  props.onRowClick(row);
}

function pagePrev() {
  if (props.loading) return;
  if (!props.onPageChange || !canPagePrev.value) return;
  const next = Math.max(0, paginationOffset.value - paginationLimit.value);
  props.onPageChange(next);
}

function pageNext() {
  if (props.loading) return;
  if (!props.onPageChange || !canPageNext.value) return;
  const next = paginationOffset.value + paginationLimit.value;
  props.onPageChange(next);
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
const showBatchBar = computed(() => !props.nativeLike && showSelectionColumn.value && groupedRows.value.length === 0);
const showArchive = computed(() => props.showArchive !== false);
const showActivate = computed(() => props.showActivate !== false);
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
  if (props.loading) return;
  const id = rowId(row);
  if (!id || !props.onToggleSelection) return;
  props.onToggleSelection(id, selected);
}

function onToggleAll(selected: boolean) {
  if (props.loading) return;
  if (!props.onToggleSelectionAll) return;
  props.onToggleSelectionAll(selectableRows.value, selected);
}

function clearSelection() {
  if (props.loading) return;
  props.onClearSelection?.();
}

function callBatchAction(action: 'archive' | 'activate' | 'delete') {
  if (props.loading) return;
  if (selectedCount.value <= 0) return;
  const label = action === 'archive' ? '归档' : action === 'activate' ? '激活' : '删除';
  if (!window.confirm(`确认批量${label} ${selectedCount.value} 条记录？`)) {
    return;
  }
  props.onBatchAction?.(action);
}

function callBatchAssign() {
  if (props.loading) return;
  if (!props.selectedAssigneeId) return;
  if (selectedCount.value <= 0) return;
  if (!window.confirm(`确认将 ${selectedCount.value} 条记录批量指派给当前负责人？`)) {
    return;
  }
  props.onBatchAssign?.(props.selectedAssigneeId);
}

function callBatchExport(scope: 'selected' | 'all') {
  if (props.loading) return;
  const count = scope === 'selected' ? selectedCount.value : props.records.length;
  if (count <= 0) return;
  const label = scope === 'selected' ? '导出选中' : '导出当前页';
  if (!window.confirm(`确认${label}（${count} 条）为 CSV？`)) {
    return;
  }
  props.onBatchExport?.(scope);
}

function onSelectAllChange(event: Event) {
  if (props.loading) return;
  const checked = Boolean((event.target as HTMLInputElement | null)?.checked);
  onToggleAll(checked);
}

function onRowCheckboxChange(row: Record<string, unknown>, event: Event) {
  if (props.loading) return;
  const checked = Boolean((event.target as HTMLInputElement | null)?.checked);
  onToggleRow(row, checked);
}

function onAssigneeSelectChange(event: Event) {
  if (props.loading) return;
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
  if (props.loading) return;
  props.onDownloadFailedCsv?.();
}

function loadMoreFailures() {
  if (props.loading) return;
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
  if (props.loading) return;
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
  gap: var(--ui-space-3);
}

.unified-topbar {
  display: grid;
  grid-template-columns: auto minmax(320px, 1.4fr) auto auto auto;
  align-items: center;
  gap: var(--ui-space-2);
  padding: var(--ui-space-3);
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-md);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 245, 239, 0.92));
  box-shadow: var(--ui-shadow-sm);
}

.topbar-title {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  min-width: 120px;
}

.topbar-title strong {
  font-size: var(--ui-font-size-lg);
  color: var(--ui-color-ink-strong);
  line-height: 1;
}

.topbar-title span {
  color: var(--ui-color-ink-muted);
  font-size: var(--ui-font-size-xs);
}

.topbar-search {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
}

.topbar-search input {
  flex: 1;
  min-width: 180px;
  height: 40px;
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-sm);
  padding: 0 var(--ui-space-3);
}

.topbar-search--native input {
  padding-right: 28px;
}

.search-menu-toggle {
  width: 32px;
  padding: 0;
}

.search-menu-toggle.active {
  border-color: var(--ui-color-primary-700);
  color: var(--ui-color-primary-700);
  background: var(--ui-color-primary-050);
}

.native-search-menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: var(--ui-z-dropdown);
  display: grid;
  grid-template-columns: repeat(2, minmax(180px, 1fr));
  gap: 10px;
  width: min(620px, calc(100vw - 48px));
  padding: 10px;
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-sm);
  background: rgba(255, 255, 255, 0.98);
  box-shadow: var(--ui-shadow-md);
}

.native-search-menu-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.native-search-menu-section p {
  margin: 0;
  color: var(--ui-color-ink-muted);
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-semibold);
}

.native-search-menu-empty {
  grid-column: 1 / -1;
  margin: 0;
  padding: 8px;
  border: 1px dashed var(--ui-color-border-strong);
  border-radius: var(--ui-radius-sm);
  color: var(--ui-color-ink-muted);
  font-size: var(--ui-font-size-xs);
  background: rgba(248, 245, 239, 0.72);
}

.native-search-menu-section button {
  justify-content: flex-start;
  width: 100%;
  overflow: hidden;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.native-search-menu-section button.active {
  border-color: var(--ui-color-primary-700);
  color: var(--ui-color-primary-700);
  background: var(--ui-color-primary-050);
}

.native-search-menu-section button:disabled {
  color: var(--ui-color-ink-soft);
  cursor: not-allowed;
  background: rgba(248, 245, 239, 0.72);
}

.native-search-menu-clear {
  color: var(--ui-color-danger-600);
}

.topbar-search button,
.topbar-tabs button,
.topbar-pagination button,
.topbar-sort select {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-sm);
  background: rgba(255, 255, 255, 0.84);
  color: var(--ui-color-ink-strong);
  padding: 0 12px;
  font-size: var(--ui-font-size-xs);
  box-shadow: var(--ui-shadow-xs);
}

.topbar-tabs {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.topbar-tabs button.active {
  border-color: var(--ui-color-primary-700);
  color: var(--ui-color-primary-700);
  background: var(--ui-color-primary-050);
}

.topbar-sort {
  display: inline-flex;
}

.topbar-pagination {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--ui-color-ink-muted);
  font-size: var(--ui-font-size-xs);
}

.topbar-primary {
  height: 38px;
  border: 1px solid var(--ui-color-primary-700);
  border-radius: 10px;
  background: var(--ui-color-primary-700);
  color: #fff;
  padding: 0 16px;
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-semibold);
  box-shadow: 0 10px 20px rgba(61, 120, 159, 0.18);
}

.topbar-primary:disabled {
  opacity: 0.55;
}

.table {
  overflow: auto;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-md);
  box-shadow: var(--ui-shadow-md);
}

.table-hint {
  padding: 10px 16px 0;
  color: var(--ui-color-ink-muted);
  font-size: var(--ui-font-size-sm);
}

.table-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px 16px;
  border-top: 1px solid var(--ui-color-border);
  background: rgba(255, 255, 255, 0.72);
}

.table-pagination-meta,
.table-pagination-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--ui-color-ink-muted);
  font-size: var(--ui-font-size-xs);
}

.table-page-btn {
  padding: 6px 10px;
  border-radius: var(--ui-radius-pill);
  border: 1px solid var(--ui-color-border);
  background: rgba(255, 255, 255, 0.84);
  color: var(--ui-color-ink-strong);
}

.table-page-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.summary-card {
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-sm);
  background: rgba(255, 255, 255, 0.92);
  padding: var(--ui-space-3);
  box-shadow: var(--ui-shadow-xs);
}

.summary-label {
  margin: 0;
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-muted);
}

.summary-value {
  margin: 6px 0 0;
  font-size: var(--ui-font-size-xl);
  font-weight: var(--ui-font-weight-bold);
}

.summary-card.tone-danger { background: #fef2f2; border-color: #fecaca; color: #b91c1c; }
.summary-card.tone-warning { background: #fffbeb; border-color: #fde68a; color: #b45309; }
.summary-card.tone-success { background: #ecfdf5; border-color: #a7f3d0; color: #047857; }
.summary-card.tone-info { background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; }
.summary-card.tone-neutral { background: rgba(255, 255, 255, 0.94); }

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
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 10px 12px;
}

.batch-bar__summary {
  display: grid;
  gap: 2px;
}

.batch-bar__eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

.batch-bar__count {
  font-size: 14px;
  color: #0f172a;
}

.batch-bar__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.batch-bar button {
  border: 1px solid #cbd5e1;
  background: #fff;
  border-radius: 10px;
  padding: 6px 10px;
  cursor: pointer;
}

.batch-bar button.primary {
  border-color: #1d4ed8;
  background: #1d4ed8;
  color: #fff;
}

.batch-bar button.danger {
  border-color: #fecaca;
  color: #b91c1c;
  background: #fff5f5;
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

tr.row-tone-danger td:first-child,
tr.row-tone-warning td:first-child,
tr.row-tone-success td:first-child,
tr.row-tone-info td:first-child {
  box-shadow: inset 3px 0 0 transparent;
}

tr.row-tone-danger td:first-child { box-shadow: inset 3px 0 0 #ef4444; }
tr.row-tone-warning td:first-child { box-shadow: inset 3px 0 0 #f59e0b; }
tr.row-tone-success td:first-child { box-shadow: inset 3px 0 0 #10b981; }
tr.row-tone-info td:first-child { box-shadow: inset 3px 0 0 #3b82f6; }

.cell-primary {
  display: grid;
  gap: 4px;
}

.cell-primary .primary {
  font-weight: 700;
  color: #0f172a;
  line-height: 1.45;
}

.cell-primary .secondary {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

.cell-inline-meta,
.cell-progress {
  display: grid;
  gap: 2px;
}

.cell-inline-meta__label,
.cell-progress__label {
  font-size: 11px;
  color: #94a3b8;
}

.cell-inline-meta__value,
.cell-progress__value {
  font-size: 13px;
  line-height: 1.4;
  color: #0f172a;
  font-weight: 600;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 3px 9px;
  font-size: 12px;
  border: 1px solid #d1d5db;
  font-weight: 600;
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

@media (max-width: 1180px) {
  .unified-topbar {
    grid-template-columns: 1fr;
    align-items: stretch;
  }
}

@media (max-width: 860px) {
  .batch-bar {
    grid-template-columns: 1fr;
  }
}

</style>
