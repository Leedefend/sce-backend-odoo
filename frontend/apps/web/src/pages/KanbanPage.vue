<template>
  <section class="page">
    <PageHeader
      :title="title"
      :subtitle="subtitle"
      :status="status"
      :status-label="statusLabel"
      :loading="loading"
      :on-reload="onReload"
      :mode-label="modeLabelText"
      :record-count="records.length"
    />

    <StatusPanel v-if="loading" title="Loading cards..." variant="info" />
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

    <template v-else>
      <section v-if="showPagination" class="pagination-bar pagination-bar--top">
        <span>{{ paginationSummary }}</span>
        <div class="pagination-actions">
          <button
            type="button"
            class="pagination-btn"
            :disabled="loading || !canPagePrev"
            @click="pagePrev"
          >
            上一页
          </button>
          <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button
            type="button"
            class="pagination-btn"
            :disabled="loading || !canPageNext"
            @click="pageNext"
          >
            下一页
          </button>
          <input
            class="pagination-input"
            :value="pageJumpInput"
            :disabled="loading || totalPages <= 1"
            inputmode="numeric"
            pattern="[0-9]*"
            @input="onPageJumpInput"
            @keyup.enter="jumpPage"
          />
          <button
            type="button"
            class="pagination-btn"
            :disabled="loading || totalPages <= 1"
            @click="jumpPage"
          >
            跳转
          </button>
        </div>
      </section>

      <section class="grid">
        <article
          v-for="(row, index) in records"
          :key="String(row.id ?? index)"
          class="card"
          :class="`tone-${rowTone(row)}`"
          @click="handleCard(row)"
        >
          <h3 class="card-title">{{ formatValue(row[titleField]) || formatValue(row.name) || formatValue(row.display_name) || row.id }}</h3>
          <div v-if="statusMetaFields.length" class="status-chips">
            <span v-for="field in statusMetaFields" :key="`status-${field}`" class="status-chip">
              {{ fieldLabel(field) }}: {{ semanticCell(field, row[field]).text }}
            </span>
          </div>
          <dl v-if="primaryMetaFields.length" class="card-meta primary">
            <div v-for="field in primaryMetaFields" :key="`primary-${field}`" class="meta-row">
              <dt>{{ fieldLabel(field) }}</dt>
              <dd>{{ semanticCell(field, row[field]).text }}</dd>
            </div>
          </dl>
          <dl class="card-meta">
            <div v-for="field in secondaryMetaFields" :key="field" class="meta-row">
              <dt>{{ fieldLabel(field) }}</dt>
              <dd>{{ semanticCell(field, row[field]).text }}</dd>
            </div>
          </dl>
        </article>
      </section>

      <section v-if="showPagination" class="pagination-bar">
        <span>{{ paginationSummary }}</span>
        <div class="pagination-actions">
          <button
            type="button"
            class="pagination-btn"
            :disabled="loading || !canPagePrev"
            @click="pagePrev"
          >
            上一页
          </button>
          <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button
            type="button"
            class="pagination-btn"
            :disabled="loading || !canPageNext"
            @click="pageNext"
          >
            下一页
          </button>
          <input
            class="pagination-input"
            :value="pageJumpInput"
            :disabled="loading || totalPages <= 1"
            inputmode="numeric"
            pattern="[0-9]*"
            @input="onPageJumpInput"
            @keyup.enter="jumpPage"
          />
          <button
            type="button"
            class="pagination-btn"
            :disabled="loading || totalPages <= 1"
            @click="jumpPage"
          >
            跳转
          </button>
        </div>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import StatusPanel from '../components/StatusPanel.vue';
import PageHeader from '../components/page/PageHeader.vue';
import { resolveEmptyCopy, resolveErrorCopy, type StatusError } from '../composables/useStatus';
import { pageModeLabel } from '../app/pageMode';
import { semanticStatus, semanticValueByField } from '../utils/semantic';

const props = defineProps<{
  title: string;
  status: 'loading' | 'ok' | 'empty' | 'error';
  loading: boolean;
  errorMessage?: string;
  traceId?: string;
  errorCode?: number | null;
  errorHint?: string;
  error?: StatusError | null;
  records: Array<Record<string, unknown>>;
  fields: string[];
  primaryFields?: string[];
  secondaryFields?: string[];
  statusFields?: string[];
  fieldLabels?: Record<string, string>;
  titleField: string;
  onReload: () => void;
  onCardClick: (row: Record<string, unknown>) => void;
  subtitle: string;
  statusLabel: string;
  pageMode?: string;
  sceneKey?: string;
  listTotalCount?: number | null;
  listOffset?: number;
  listLimit?: number;
  onPageChange?: (offset: number) => void;
}>();
const errorCopy = computed(() =>
  resolveErrorCopy(
    props.error || null,
    props.errorMessage || 'Card load failed',
  ),
);
const emptyCopy = computed(() => resolveEmptyCopy('card'));

const fallbackMetaFields = computed(() => props.fields.filter((field) => field !== props.titleField));
const statusMetaFields = computed(() => {
  const preferred = (props.statusFields || []).filter((field) => field && field !== props.titleField);
  if (preferred.length) return preferred.slice(0, 2);
  return [];
});
const primaryMetaFields = computed(() => {
  const preferred = (props.primaryFields || []).filter(
    (field) => field && field !== props.titleField && !statusMetaFields.value.includes(field),
  );
  if (preferred.length) return preferred.slice(0, 2);
  return fallbackMetaFields.value.filter((field) => !statusMetaFields.value.includes(field)).slice(0, 2);
});
const secondaryMetaFields = computed(() => {
  const preferred = (props.secondaryFields || []).filter(
    (field) =>
      field
      && field !== props.titleField
      && !statusMetaFields.value.includes(field)
      && !primaryMetaFields.value.includes(field),
  );
  if (preferred.length) return preferred.slice(0, 3);
  return fallbackMetaFields.value
    .filter((field) => !statusMetaFields.value.includes(field) && !primaryMetaFields.value.includes(field))
    .slice(0, 3);
});

const modeLabelText = computed(() => pageModeLabel(props.pageMode || 'workspace'));
const pageJumpInput = ref('');
const observedListLimit = ref(0);
const listLimit = computed(() => {
  if (observedListLimit.value > 0) return observedListLimit.value;
  const limit = Number(props.listLimit || 40);
  return Number.isFinite(limit) && limit > 0 ? Math.trunc(limit) : 40;
});
const listTotal = computed(() => {
  if (props.listTotalCount === null || typeof props.listTotalCount === 'undefined') return null;
  const raw = Number(props.listTotalCount);
  if (!Number.isFinite(raw) || raw < 0) return null;
  return Math.trunc(raw);
});
const listOffset = computed(() => {
  const offset = Number(props.listOffset || 0);
  if (!Number.isFinite(offset) || offset <= 0) return 0;
  return Math.trunc(offset);
});
const totalPages = computed(() => {
  const total = listTotal.value || 0;
  return Math.max(1, Math.ceil(total / listLimit.value));
});
const currentPage = computed(() => Math.min(totalPages.value, Math.floor(listOffset.value / listLimit.value) + 1));
const rangeStart = computed(() => {
  const total = listTotal.value || 0;
  if (!total) return 0;
  return Math.min(total, listOffset.value + 1);
});
const rangeEnd = computed(() => {
  const total = listTotal.value || 0;
  if (!total) return 0;
  return Math.min(total, listOffset.value + props.records.length);
});
const showPagination = computed(() => listTotal.value !== null && props.status === 'ok');
const canPagePrev = computed(() => listOffset.value > 0);
const canPageNext = computed(() => {
  const total = listTotal.value || 0;
  return listOffset.value + listLimit.value < total;
});
const paginationSummary = computed(() => {
  const total = listTotal.value || 0;
  if (!total) return '共 0 条';
  return `共 ${total} 条，当前 ${rangeStart.value}-${rangeEnd.value} 条`;
});

function semanticCell(field: string, value: unknown) {
  return semanticValueByField(field, value);
}

function rowTone(row: Record<string, unknown>) {
  const state = row.state || row.stage_id || row.status;
  return semanticStatus(state).tone;
}

function fieldLabel(name: string) {
  const labels = props.fieldLabels || {};
  return labels[name] || name;
}

function handleCard(row: Record<string, unknown>) {
  props.onCardClick(row);
}

function emitPageOffset(offset: number) {
  if (!props.onPageChange) return;
  const total = listTotal.value || 0;
  const maxOffset = total > 0 ? Math.floor((total - 1) / listLimit.value) * listLimit.value : 0;
  const normalized = Math.min(Math.max(Math.trunc(offset || 0), 0), maxOffset);
  props.onPageChange(normalized);
}

function pagePrev() {
  emitPageOffset(listOffset.value - listLimit.value);
}

function pageNext() {
  emitPageOffset(listOffset.value + listLimit.value);
}

function onPageJumpInput(event: Event) {
  pageJumpInput.value = String((event.target as HTMLInputElement | null)?.value || '');
}

function jumpPage() {
  const page = Number(pageJumpInput.value || currentPage.value);
  if (!Number.isFinite(page)) return;
  const normalizedPage = Math.min(Math.max(Math.trunc(page), 1), totalPages.value);
  pageJumpInput.value = String(normalizedPage);
  emitPageOffset((normalizedPage - 1) * listLimit.value);
}

watch(
  currentPage,
  (page) => {
    pageJumpInput.value = String(page);
  },
  { immediate: true },
);

watch(
  [() => props.records.length, listTotal],
  ([length, totalRaw]) => {
    const total = totalRaw || 0;
    if (length <= 0 || total <= 0) return;
    if (length > observedListLimit.value) {
      observedListLimit.value = length;
      return;
    }
    if (listOffset.value === 0) {
      observedListLimit.value = length;
    }
  },
  { immediate: true },
);

function formatValue(value: unknown) {
  if (Array.isArray(value)) {
    if (value.length > 1 && value[1] !== null && value[1] !== undefined) {
      return String(value[1]);
    }
    if (value.length > 0 && value[0] !== null && value[0] !== undefined) {
      return String(value[0]);
    }
    return '';
  }
  if (value && typeof value === 'object') {
    const maybeName = (value as Record<string, unknown>).name;
    if (maybeName !== null && maybeName !== undefined && String(maybeName).trim()) {
      return String(maybeName);
    }
    return '';
  }
  if (value === null || value === undefined) {
    return '';
  }
  return String(value);
}
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
}


.grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.card {
  background: white;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.08);
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 34px rgba(15, 23, 42, 0.12);
}

.card.tone-danger { border: 1px solid #fecaca; background: #fff7f7; }
.card.tone-warning { border: 1px solid #fde68a; background: #fffcf2; }
.card.tone-success { border: 1px solid #a7f3d0; background: #f7fffb; }

.card-title {
  margin: 0 0 10px;
  font-size: 16px;
  color: #0f172a;
}

.status-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.status-chip {
  font-size: 11px;
  line-height: 1;
  padding: 5px 8px;
  border-radius: 999px;
  background: #ecfeff;
  border: 1px solid #99f6e4;
  color: #0f766e;
}

.card-meta {
  display: grid;
  gap: 6px;
  margin: 0;
}

.card-meta.primary {
  margin-bottom: 10px;
}

.meta-row {
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 6px;
  font-size: 12px;
  color: #475569;
}

.meta-row dt {
  font-weight: 600;
  color: #334155;
}

.meta-row dd {
  margin: 0;
  color: #64748b;
}

.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  padding: 10px 12px;
  color: #475569;
  font-size: 13px;
}

.pagination-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.pagination-btn {
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #fff;
  color: #1d4ed8;
  padding: 4px 10px;
  font-size: 13px;
  cursor: pointer;
}

.pagination-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.pagination-input {
  width: 60px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 4px 8px;
  color: #0f172a;
  font-size: 13px;
}

@media (max-width: 720px) {
  .pagination-bar,
  .pagination-actions {
    align-items: flex-start;
    flex-wrap: wrap;
  }
}
</style>
