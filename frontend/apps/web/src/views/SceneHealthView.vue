<template>
  <section class="scene-health">
    <header class="header">
      <div>
        <h2>Scene Health Dashboard</h2>
        <p>可视化查看场景健康状态与自动降级结果。</p>
      </div>
      <div class="actions">
        <label>
          <span>Company</span>
          <select v-model="companyIdText" @change="loadHealth">
            <option value="">Current</option>
            <option v-for="company in companies" :key="company.id" :value="String(company.id)">
              {{ company.name }}
            </option>
          </select>
        </label>
        <button class="secondary" @click="loadHealth">Refresh</button>
      </div>
    </header>

    <StatusPanel v-if="loading" title="Loading scene health..." variant="info" />
    <StatusPanel
      v-else-if="errorText"
      title="Health contract invalid"
      :message="errorText"
      :trace-id="errorTraceId || undefined"
      variant="error"
      :on-retry="loadHealth"
    />

    <div v-else-if="health" class="content">
      <article class="pill-row">
        <span class="pill">channel: {{ health.scene_channel || '-' }}</span>
        <span class="pill" :class="{ warn: health.rollback_active }">
          rollback: {{ health.rollback_active ? 'active' : 'off' }}
        </span>
        <span class="pill">version: {{ health.scene_version || '-' }}</span>
        <span class="pill">schema: {{ health.schema_version || '-' }}</span>
      </article>

      <section class="cards">
        <article class="card danger">
          <h3>Critical Resolve Errors</h3>
          <p>{{ health.summary.critical_resolve_errors_count }}</p>
        </article>
        <article class="card danger">
          <h3>Critical Drift Warn</h3>
          <p>{{ health.summary.critical_drift_warn_count }}</p>
        </article>
        <article class="card">
          <h3>Non-Critical Debt</h3>
          <p>{{ health.summary.non_critical_debt_count }}</p>
        </article>
      </section>

      <article class="meta">
        <p><strong>contract_ref:</strong> {{ health.contract_ref || '-' }}</p>
        <p><strong>trace_id:</strong> {{ health.trace_id || '-' }}</p>
        <p><strong>updated_at:</strong> {{ health.last_updated_at || '-' }}</p>
        <p><strong>auto_degrade:</strong> {{ autoDegradeLabel }}</p>
      </article>

      <details open>
        <summary>Resolve Errors ({{ health.details.resolve_errors.length }})</summary>
        <pre>{{ JSON.stringify(health.details.resolve_errors, null, 2) }}</pre>
      </details>
      <details>
        <summary>Drift ({{ health.details.drift.length }})</summary>
        <pre>{{ JSON.stringify(health.details.drift, null, 2) }}</pre>
      </details>
      <details>
        <summary>Debt ({{ health.details.debt.length }})</summary>
        <pre>{{ JSON.stringify(health.details.debt, null, 2) }}</pre>
      </details>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import StatusPanel from '../components/StatusPanel.vue';
import { intentRequest, intentRequestRaw } from '../api/intents';

type SceneHealth = {
  company_id: number | null;
  scene_channel: string;
  rollback_active: boolean;
  scene_version: string;
  schema_version: string;
  contract_ref: string;
  summary: {
    critical_resolve_errors_count: number;
    critical_drift_warn_count: number;
    non_critical_debt_count: number;
  };
  details: {
    resolve_errors: Array<Record<string, unknown>>;
    drift: Array<Record<string, unknown>>;
    debt: Array<Record<string, unknown>>;
  };
  auto_degrade?: {
    triggered?: boolean;
    reason_codes?: string[];
    action_taken?: string;
  };
  last_updated_at: string;
  trace_id: string;
};

const loading = ref(false);
const health = ref<SceneHealth | null>(null);
const errorText = ref('');
const errorTraceId = ref('');
const companyIdText = ref('');
const companies = ref<Array<{ id: number; name: string }>>([]);

const autoDegradeLabel = computed(() => {
  const value = health.value?.auto_degrade;
  if (!value) return 'triggered=false';
  const reasons = Array.isArray(value.reason_codes) && value.reason_codes.length ? value.reason_codes.join(',') : '-';
  return `triggered=${Boolean(value.triggered)} action=${value.action_taken || '-'} reasons=${reasons}`;
});

function validateHealthContract(raw: unknown): SceneHealth {
  if (!raw || typeof raw !== 'object') throw new Error('scene.health response missing');
  const value = raw as Record<string, unknown>;
  const requiredRoot = ['scene_channel', 'rollback_active', 'summary', 'details', 'trace_id'];
  for (const key of requiredRoot) {
    if (!(key in value)) {
      throw new Error(`scene.health missing key: ${key}`);
    }
  }
  const summary = value.summary as Record<string, unknown>;
  if (
    typeof summary?.critical_resolve_errors_count !== 'number' ||
    typeof summary?.critical_drift_warn_count !== 'number'
  ) {
    throw new Error('scene.health.summary critical counters missing');
  }
  const details = value.details as Record<string, unknown>;
  if (!Array.isArray(details?.resolve_errors) || !Array.isArray(details?.drift) || !Array.isArray(details?.debt)) {
    throw new Error('scene.health.details arrays missing');
  }
  return value as SceneHealth;
}

async function loadCompanies() {
  try {
    const res = await intentRequest<{ records?: Array<{ id: number; name: string }> }>({
      intent: 'api.data',
      params: {
        op: 'list',
        model: 'res.company',
        fields: ['id', 'name'],
        limit: 50,
        order: 'id asc',
      },
    });
    companies.value = Array.isArray(res.records) ? res.records : [];
  } catch {
    companies.value = [];
  }
}

async function loadHealth() {
  loading.value = true;
  errorText.value = '';
  errorTraceId.value = '';
  try {
    const companyId = companyIdText.value ? Number(companyIdText.value) : undefined;
    const response = await intentRequestRaw<SceneHealth>({
      intent: 'scene.health',
      params: {
        ...(companyId ? { company_id: companyId } : {}),
      },
    });
    const parsed = validateHealthContract(response.data);
    health.value = parsed;
    errorTraceId.value = parsed.trace_id || response.traceId || '';
  } catch (err) {
    health.value = null;
    errorText.value = err instanceof Error ? err.message : 'health request failed';
    if (err && typeof err === 'object' && 'traceId' in err) {
      errorTraceId.value = String((err as { traceId?: string }).traceId || '');
    }
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  await loadCompanies();
  await loadHealth();
});
</script>

<style scoped>
.scene-health {
  display: grid;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 16px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.header h2 {
  margin: 0;
}

.header p {
  margin: 4px 0 0;
  color: #6b7280;
}

.actions {
  display: flex;
  align-items: end;
  gap: 12px;
}

.actions label {
  display: grid;
  gap: 6px;
  font-size: 12px;
  color: #4b5563;
}

.actions select {
  min-width: 180px;
}

.content {
  display: grid;
  gap: 14px;
}

.pill-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.pill {
  background: #eef2ff;
  color: #1f2937;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
}

.pill.warn {
  background: #fee2e2;
  color: #991b1b;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.card {
  border-radius: 12px;
  padding: 16px;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.card.danger {
  border-color: rgba(185, 28, 28, 0.25);
}

.card h3 {
  margin: 0 0 8px;
  font-size: 13px;
}

.card p {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}

.meta {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  padding: 12px 14px;
}

.meta p {
  margin: 4px 0;
}

details {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  padding: 10px 12px;
}

summary {
  cursor: pointer;
  font-weight: 600;
}

pre {
  overflow: auto;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 8px;
  padding: 10px;
  font-size: 12px;
}

.secondary {
  border: 1px solid rgba(15, 23, 42, 0.2);
  background: white;
  border-radius: 8px;
  padding: 8px 10px;
  cursor: pointer;
}
</style>
