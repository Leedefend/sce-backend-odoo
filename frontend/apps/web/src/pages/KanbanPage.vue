<template>
  <section class="page">
    <header class="header">
      <div>
        <h2>{{ title }}</h2>
        <p class="meta">{{ subtitle }}</p>
      </div>
      <div class="actions">
        <span class="pill" :class="status">{{ statusLabel }}</span>
        <button class="ghost" @click="onReload" :disabled="loading">Reload</button>
      </div>
    </header>

    <StatusPanel v-if="loading" title="Loading cards..." variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
      title="Request failed"
      :message="error?.message || errorMessage"
      :trace-id="error?.traceId || traceId"
      :error-code="error?.code || errorCode"
      :hint="error?.hint || errorHint"
      variant="error"
      :on-retry="onReload"
    />
    <StatusPanel
      v-else-if="status === 'empty'"
      title="No data"
      message="No cards returned for this action."
      variant="info"
      :on-retry="onReload"
    />

    <section v-else class="grid">
      <article
        v-for="(row, index) in records"
        :key="String(row.id ?? index)"
        class="card"
        @click="handleCard(row)"
      >
        <h3 class="card-title">{{ formatValue(row[titleField]) || formatValue(row.name) || formatValue(row.display_name) || row.id }}</h3>
        <dl class="card-meta">
          <div v-for="field in metaFields" :key="field" class="meta-row">
            <dt>{{ field }}</dt>
            <dd>{{ formatValue(row[field]) }}</dd>
          </div>
        </dl>
      </article>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import StatusPanel from '../components/StatusPanel.vue';
import type { StatusError } from '../composables/useStatus';

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
  titleField: string;
  onReload: () => void;
  onCardClick: (row: Record<string, unknown>) => void;
}>();

const statusLabel = computed(() => {
  if (props.status === 'loading') return 'Loading';
  if (props.status === 'error') return 'Error';
  if (props.status === 'empty') return 'Empty';
  return 'Ready';
});

const subtitle = computed(() => `${props.records.length} cards · ${props.fields.length} fields`);

const metaFields = computed(() => props.fields.filter((field) => field !== props.titleField).slice(0, 4));

function formatValue(value: unknown) {
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  if (value && typeof value === 'object') {
    return JSON.stringify(value);
  }
  return value ?? '';
}

function handleCard(row: Record<string, unknown>) {
  props.onCardClick(row);
}
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.meta {
  color: #64748b;
  font-size: 14px;
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

.card-title {
  margin: 0 0 12px;
  font-size: 16px;
  color: #0f172a;
}

.card-meta {
  display: grid;
  gap: 6px;
  margin: 0;
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
