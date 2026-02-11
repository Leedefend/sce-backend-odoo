<template>
  <section class="page">
    <PageHeader
      :title="title"
      :subtitle="subtitle"
      :status="status"
      :status-label="statusLabel"
      :loading="loading"
      :on-reload="onReload"
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

    <StatusPanel v-if="loading" title="Loading list..." variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="error?.traceId || traceId"
      :error-code="error?.code || errorCode"
      :reason-code="error?.reasonCode"
      :error-category="error?.errorCategory"
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
      <span>{{ selectedCount }} selected</span>
      <button type="button" :disabled="loading || !selectedCount" @click="callBatchAction('archive')">批量归档</button>
      <button type="button" :disabled="loading || !selectedCount" @click="callBatchAction('activate')">批量激活</button>
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
                <div class="primary">{{ formatValue(row[col]) }}</div>
                <div v-if="rowSecondary" class="secondary">{{ formatValue(row[rowSecondary]) }}</div>
              </div>
              <div v-else>
                {{ formatValue(row[col]) }}
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import StatusPanel from '../components/StatusPanel.vue';
import PageHeader from '../components/page/PageHeader.vue';
import PageToolbar from '../components/page/PageToolbar.vue';
import { resolveEmptyCopy, resolveErrorCopy, type StatusError } from '../composables/useStatus';
import type { SceneListProfile } from '../app/resolvers/sceneRegistry';

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
  listProfile?: SceneListProfile | null;
  onFilter: (value: 'all' | 'active' | 'archived') => void;
  selectedIds?: number[];
  onToggleSelection?: (id: number, selected: boolean) => void;
  onToggleSelectionAll?: (ids: number[], selected: boolean) => void;
  onBatchAction?: (action: 'archive' | 'activate') => void;
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
}>();
const errorCopy = computed(() =>
  resolveErrorCopy(
    props.error || null,
    props.errorMessage || 'List load failed',
  ),
);
const emptyCopy = computed(() => resolveEmptyCopy('list'));
function formatValue(value: unknown) {
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  if (Array.isArray(value)) {
    if (value.length === 2 && typeof value[1] === 'string') {
      return value[1];
    }
    return value.join(', ');
  }
  if (value && typeof value === 'object') {
    return JSON.stringify(value);
  }
  return value ?? '';
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

function callBatchAction(action: 'archive' | 'activate') {
  if (selectedCount.value <= 0) return;
  const label = action === 'archive' ? '归档' : '激活';
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
const displayedColumns = computed(() => {
  const source = preferredColumns.value.length ? preferredColumns.value : props.columns;
  const filtered = source.filter((col) => !hiddenColumns.value[col]);
  return filtered.length ? filtered : props.columns.filter((col) => !hiddenColumns.value[col]);
});

function columnLabel(col: string) {
  return columnLabels.value[col] || col;
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

</style>
