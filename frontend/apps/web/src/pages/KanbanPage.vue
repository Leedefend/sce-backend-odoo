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

    <section v-else-if="groupColumns.length" class="kanban-columns">
      <article
        v-for="column in groupColumns"
        :key="column.key"
        class="kanban-column"
      >
        <header class="kanban-column-header">
          <div>
            <p class="kanban-column-label">{{ column.label }}</p>
            <p v-if="groupFieldLabel" class="kanban-column-field">{{ groupFieldLabel }}</p>
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
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
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

const groupField = computed(() => {
  const preferred = (props.statusFields || []).find((field) => field && field !== props.titleField);
  return preferred || '';
});

const groupFieldLabel = computed(() => {
  if (!groupField.value) return '';
  return fieldLabel(groupField.value);
});

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

const modeLabelText = computed(() => pageModeLabel(props.pageMode || 'workspace'));

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
  gap: 16px;
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
  border-radius: 18px;
  border: 1px solid #dbe4f0;
  background: linear-gradient(180deg, #f8fbff 0%, #f3f7fc 100%);
}

.kanban-column-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.kanban-column-label {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.kanban-column-field {
  margin: 4px 0 0;
  font-size: 11px;
  color: #64748b;
}

.kanban-column-count {
  min-width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #e2e8f0;
  color: #334155;
  font-size: 12px;
  font-weight: 700;
}

.kanban-column-body {
  display: grid;
  gap: 12px;
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
</style>
