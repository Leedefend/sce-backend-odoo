<template>
  <PageLayout class="page">
    <template #header>
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
    </template>

    <template #content>
      <section v-if="status === 'ok' && showDetailZone" class="kanban-detail-zone">
      <section v-if="groupedFilterTabs.length" class="kanban-filter-tabs">
        <button
          v-for="tab in groupedFilterTabs"
          :key="`tab-${tab.key}`"
          type="button"
          class="kanban-filter-tab"
          :class="{ 'kanban-filter-tab--active': selectedGroupKey === tab.key }"
          @click="selectGroupedTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </section>

      <section v-if="filteredGroupColumns.length" class="kanban-columns">
        <article
          v-for="column in filteredGroupColumns"
          :key="column.key"
          class="kanban-column"
        >
          <header class="kanban-column-header">
            <div>
              <p class="kanban-column-label">{{ column.label }}</p>
              <p v-if="groupFieldLabel" class="kanban-column-field">{{ groupFieldLabel }}</p>
              <p v-if="quickActionCount > 0" class="kanban-column-field">快捷操作 {{ quickActionCount }}</p>
            </div>
            <span class="kanban-column-count">{{ column.records.length }}</span>
          </header>
          <section class="kanban-column-body">
            <article
              v-for="(row, index) in column.records"
              :key="String(row.id ?? `${column.key}-${index}`)"
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
              <dl v-if="metricMetaFields.length" class="card-meta metric">
                <div v-for="field in metricMetaFields" :key="`metric-${field}`" class="meta-row">
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
        </article>
      </section>

      <section v-else class="grid">
      <article
        v-for="(row, index) in filteredRecords"
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
        <dl v-if="metricMetaFields.length" class="card-meta metric">
          <div v-for="field in metricMetaFields" :key="`metric-${field}`" class="meta-row">
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
      </section>
    </template>

    <template #feedback>
      <PageFeedback>
        <StatusPanel v-if="loading" title="正在加载看板..." variant="info" />
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
          :message="emptyCopy.message"
          variant="info"
          :on-retry="onReload"
          retry-label="刷新"
        />
        <StatusPanel
          v-else-if="status === 'ok' && !showDetailZone"
          title="当前看板语义未开放详情区"
          message="semantic_page 未声明 detail_zone，已按契约隐藏看板主体。"
          variant="info"
          :on-retry="onReload"
          retry-label="刷新"
        />
      </PageFeedback>
    </template>
  </PageLayout>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import StatusPanel from '../components/StatusPanel.vue';
import PageHeader from '../components/page/PageHeader.vue';
import PageLayout from '../components/page/PageLayout.vue';
import PageFeedback from '../components/page/PageFeedback.vue';
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
  metricFields?: string[];
  quickActionCount?: number;
  activeGroupByField?: string;
  fieldLabels?: Record<string, string>;
  titleField: string;
  onReload: () => void;
  onCardClick: (row: Record<string, unknown>) => void;
  subtitle: string;
  statusLabel: string;
  pageMode?: string;
  sceneKey?: string;
  semanticZones?: Array<Record<string, unknown>>;
}>();
const errorCopy = computed(() =>
  resolveErrorCopy(
    props.error || null,
    props.errorMessage || '看板加载失败',
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
const metricMetaFields = computed(() => {
  const preferred = (props.metricFields || []).filter(
    (field) =>
      field
      && field !== props.titleField
      && !statusMetaFields.value.includes(field)
      && !primaryMetaFields.value.includes(field),
  );
  return preferred.slice(0, 2);
});
const secondaryMetaFields = computed(() => {
  const preferred = (props.secondaryFields || []).filter(
    (field) =>
      field
      && field !== props.titleField
      && !statusMetaFields.value.includes(field)
      && !primaryMetaFields.value.includes(field)
      && !metricMetaFields.value.includes(field),
  );
  if (preferred.length) return preferred.slice(0, 3);
  return fallbackMetaFields.value
    .filter(
      (field) =>
        !statusMetaFields.value.includes(field)
        && !primaryMetaFields.value.includes(field)
        && !metricMetaFields.value.includes(field),
    )
    .slice(0, 3);
});

const groupField = computed(() => {
  const active = String(props.activeGroupByField || '').trim();
  if (active && active !== props.titleField) {
    return active;
  }
  const preferred = (props.statusFields || []).find((field) => field && field !== props.titleField);
  return preferred || '';
});

const groupFieldLabel = computed(() => {
  if (!groupField.value) return '';
  return fieldLabel(groupField.value);
});
const semanticZoneKeySet = computed(() => {
  const rows = Array.isArray(props.semanticZones) ? props.semanticZones : [];
  const keys = rows
    .map((item) => String((item && typeof item === 'object' && !Array.isArray(item) ? item.key : '') || '').trim())
    .filter(Boolean);
  return new Set(keys);
});
const showDetailZone = computed(() => semanticZoneKeySet.value.size === 0 || semanticZoneKeySet.value.has('detail_zone'));

const groupColumns = computed(() => {
  if (!groupField.value) return [];
  const buckets = new Map<string, { key: string; label: string; records: Array<Record<string, unknown>> }>();
  for (const row of props.records) {
    const rawValue = row[groupField.value];
    const label = semanticCell(groupField.value, rawValue).text || formatValue(rawValue) || '未分组';
    const key = normalizeGroupKey(rawValue, label);
    const bucket = buckets.get(key);
    if (bucket) {
      bucket.records.push(row);
      continue;
    }
    buckets.set(key, { key, label, records: [row] });
  }
  return Array.from(buckets.values());
});

const selectedGroupKey = ref('all');
const groupedFilterTabs = computed(() => {
  if (!groupColumns.value.length) return [];
  return [
    { key: 'all', label: `全部（${props.records.length}）` },
    ...groupColumns.value.map((group) => ({ key: group.key, label: `${group.label}（${group.records.length}）` })),
  ];
});
const filteredGroupColumns = computed(() => {
  if (!groupColumns.value.length) return [];
  if (selectedGroupKey.value === 'all') return groupColumns.value;
  return groupColumns.value.filter((group) => group.key === selectedGroupKey.value);
});
const filteredRecords = computed(() => {
  if (!groupColumns.value.length || selectedGroupKey.value === 'all') return props.records;
  return props.records.filter((row) => normalizeGroupKey(row[groupField.value], semanticCell(groupField.value, row[groupField.value]).text || formatValue(row[groupField.value]) || '未分组') === selectedGroupKey.value);
});

watch(groupColumns, (rows) => {
  if (!rows.length) {
    selectedGroupKey.value = 'all';
    return;
  }
  if (selectedGroupKey.value === 'all') return;
  const exists = rows.some((row) => row.key === selectedGroupKey.value);
  if (!exists) selectedGroupKey.value = 'all';
}, { immediate: true });

function selectGroupedTab(key: string) {
  selectedGroupKey.value = key || 'all';
}

const modeLabelText = computed(() => pageModeLabel(props.pageMode || 'workspace'));

function semanticCell(field: string, value: unknown) {
  return semanticValueByField(field, value);
}

function rowTone(row: Record<string, unknown>) {
  const toneFieldCandidates = [groupField.value, ...(props.statusFields || []), 'state', 'stage_id', 'status']
    .map((item) => String(item || '').trim())
    .filter(Boolean);
  for (const field of toneFieldCandidates) {
    if (!(field in row)) continue;
    const semantic = semanticCell(field, row[field]);
    if (semantic.text !== '--') {
      return semantic.tone;
    }
  }
  return semanticStatus(row.state || row.stage_id || row.status).tone;
}

function fieldLabel(name: string) {
  const labels = props.fieldLabels || {};
  return labels[name] || name;
}

function handleCard(row: Record<string, unknown>) {
  if (props.loading) return;
  props.onCardClick(row);
}

function normalizeGroupKey(value: unknown, fallback: string) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item ?? '')).join(':') || fallback;
  }
  if (value && typeof value === 'object') {
    const named = formatValue(value);
    return named || fallback;
  }
  if (value === null || value === undefined || String(value).trim() === '') {
    return fallback;
  }
  return String(value);
}

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
  gap: var(--ui-space-4);
}

.kanban-detail-zone {
  display: grid;
  gap: var(--ui-space-3);
}

.kanban-filter-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.kanban-filter-tab {
  border: 1px solid var(--ui-color-border);
  background: rgba(255, 255, 255, 0.92);
  color: var(--ui-color-ink);
  border-radius: var(--ui-radius-pill);
  padding: 6px 12px;
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-semibold);
  cursor: pointer;
  box-shadow: var(--ui-shadow-xs);
}

.kanban-filter-tab--active {
  background: var(--ui-color-primary-700);
  color: #ffffff;
  border-color: var(--ui-color-primary-700);
}


.grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.kanban-columns {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  align-items: start;
}

.kanban-column {
  display: grid;
  gap: 12px;
  padding: 12px;
  border-radius: var(--ui-radius-md);
  border: 1px solid var(--ui-color-border);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.84) 0%, rgba(240, 245, 248, 0.94) 100%);
}

.kanban-column-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.kanban-column-label {
  margin: 0;
  font-size: var(--ui-font-size-md);
  font-weight: var(--ui-font-weight-bold);
  color: var(--ui-color-ink-strong);
}

.kanban-column-field {
  margin: 4px 0 0;
  font-size: 11px;
  color: var(--ui-color-ink-muted);
}

.kanban-column-count {
  min-width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--ui-radius-pill);
  background: rgba(255, 255, 255, 0.78);
  color: var(--ui-color-ink);
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-bold);
  border: 1px solid var(--ui-color-border);
}

.kanban-column-body {
  display: grid;
  gap: 12px;
}

.card {
  background: rgba(255, 255, 255, 0.96);
  border-radius: var(--ui-radius-md);
  padding: 16px;
  border: 1px solid var(--ui-color-border);
  box-shadow: var(--ui-shadow-sm);
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--ui-shadow-md);
}

.card.tone-danger { border-color: rgba(177, 76, 67, 0.24); background: rgba(255, 240, 238, 0.92); }
.card.tone-warning { border-color: rgba(165, 107, 22, 0.24); background: rgba(255, 245, 223, 0.9); }
.card.tone-success { border-color: rgba(31, 122, 91, 0.2); background: rgba(235, 248, 242, 0.92); }

.card-title {
  margin: 0 0 10px;
  font-size: var(--ui-font-size-lg);
  color: var(--ui-color-ink-strong);
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
  border-radius: var(--ui-radius-pill);
  background: var(--ui-color-success-050);
  border: 1px solid rgba(31, 122, 91, 0.2);
  color: var(--ui-color-success-600);
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
</style>
