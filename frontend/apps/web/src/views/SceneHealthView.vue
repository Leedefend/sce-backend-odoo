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
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="statusError?.traceId || errorTraceId || undefined"
      :error-code="statusError?.code"
      :reason-code="statusError?.reasonCode"
      :hint="errorCopy.hint"
      :suggested-action="statusError?.suggestedAction"
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
        <p v-if="governanceTraceId"><strong>governance_trace:</strong> {{ governanceTraceId }}</p>
      </article>

      <section class="governance">
        <h3>Governance Actions</h3>
        <div class="governance-grid">
          <label>
            <span>Target Channel</span>
            <select v-model="targetChannel">
              <option value="stable">stable</option>
              <option value="beta">beta</option>
              <option value="dev">dev</option>
            </select>
          </label>
          <label class="reason">
            <span>Reason (required)</span>
            <input v-model="governanceReason" type="text" placeholder="input reason" />
          </label>
        </div>
        <div class="governance-actions">
          <button class="secondary" :disabled="governanceBusy" @click="runGovernance('set_channel')">Set Channel</button>
          <button class="danger" :disabled="governanceBusy" @click="runGovernance('rollback')">Rollback</button>
          <button class="secondary" :disabled="governanceBusy" @click="runGovernance('pin_stable')">Pin Stable</button>
          <button class="secondary" :disabled="governanceBusy" @click="runGovernance('export_contract')">Export Contract</button>
        </div>
      </section>

      <details open>
        <summary>Resolve Errors ({{ health.details?.resolve_errors?.length || 0 }})</summary>
        <pre>{{ JSON.stringify(health.details?.resolve_errors || [], null, 2) }}</pre>
      </details>
      <details>
        <summary>Drift ({{ health.details?.drift?.length || 0 }})</summary>
        <pre>{{ JSON.stringify(health.details?.drift || [], null, 2) }}</pre>
      </details>
      <details>
        <summary>Debt ({{ health.details?.debt?.length || 0 }})</summary>
        <pre>{{ JSON.stringify(health.details?.debt || [], null, 2) }}</pre>
      </details>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import StatusPanel from '../components/StatusPanel.vue';
import { intentRequest } from '../api/intents';
import { buildStatusError, resolveErrorCopy, type StatusError } from '../composables/useStatus';
import {
  fetchSceneHealth,
  governanceExportContract,
  governancePinStable,
  governanceRollback,
  governanceSetChannel,
} from '../api/scene';
import type { SceneChannel, SceneHealthContract } from '../contracts/scene';

const loading = ref(false);
const governanceBusy = ref(false);
const health = ref<SceneHealthContract | null>(null);
const errorText = ref('');
const errorTraceId = ref('');
const statusError = ref<StatusError | null>(null);
const companyIdText = ref('');
const companies = ref<Array<{ id: number; name: string }>>([]);
const targetChannel = ref<SceneChannel>('stable');
const governanceReason = ref('');
const governanceTraceId = ref('');
const errorCopy = computed(() => resolveErrorCopy(statusError.value, errorText.value || 'health request failed'));

const autoDegradeLabel = computed(() => {
  const value = health.value?.auto_degrade;
  if (!value) return 'triggered=false';
  const reasons = Array.isArray(value.reason_codes) && value.reason_codes.length ? value.reason_codes.join(',') : '-';
  return `triggered=${Boolean(value.triggered)} action=${value.action_taken || '-'} reasons=${reasons}`;
});

function validateHealthContract(raw: unknown): SceneHealthContract {
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
  if ('details' in value) {
    const details = value.details as Record<string, unknown>;
    if (!Array.isArray(details?.resolve_errors) || !Array.isArray(details?.drift) || !Array.isArray(details?.debt)) {
      throw new Error('scene.health.details arrays missing');
    }
  }
  return value as unknown as SceneHealthContract;
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
  statusError.value = null;
  try {
    const companyId = companyIdText.value ? Number(companyIdText.value) : undefined;
    const response = await fetchSceneHealth({
      mode: 'full',
      limit: 100,
      offset: 0,
      ...(companyId ? { company_id: companyId } : {}),
    });
    const parsed = validateHealthContract(response.data);
    health.value = parsed;
    errorTraceId.value = parsed.trace_id || response.traceId || '';
  } catch (err) {
    health.value = null;
    errorText.value = err instanceof Error ? err.message : 'health request failed';
    statusError.value = buildStatusError(err, errorText.value);
    errorTraceId.value = statusError.value.traceId || '';
  } finally {
    loading.value = false;
  }
}

async function runGovernance(action: 'set_channel' | 'rollback' | 'pin_stable' | 'export_contract') {
  const reason = governanceReason.value.trim();
  if (!reason) {
    errorText.value = 'reason is required for governance action';
    statusError.value = { message: errorText.value };
    return;
  }
  governanceBusy.value = true;
  errorText.value = '';
  statusError.value = null;
  try {
    if (action === 'rollback') {
      const ok = window.confirm('Confirm rollback to stable pinned mode?');
      if (!ok) {
        governanceBusy.value = false;
        return;
      }
    }
    const companyId = companyIdText.value ? Number(companyIdText.value) : undefined;
    let response: { readonly data: { readonly trace_id: string }; readonly traceId: string };
    if (action === 'set_channel') {
      response = await governanceSetChannel({
        reason,
        channel: targetChannel.value,
        ...(companyId ? { company_id: companyId } : {}),
      });
    } else if (action === 'rollback') {
      response = await governanceRollback({ reason });
    } else if (action === 'pin_stable') {
      response = await governancePinStable({ reason });
    } else {
      response = await governanceExportContract({ reason, channel: targetChannel.value });
    }
    governanceTraceId.value = response.data.trace_id || response.traceId || '';
    await loadHealth();
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : 'governance action failed';
    statusError.value = buildStatusError(err, errorText.value);
    errorTraceId.value = statusError.value.traceId || '';
  } finally {
    governanceBusy.value = false;
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

.governance {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  padding: 12px 14px;
  display: grid;
  gap: 12px;
}

.governance h3 {
  margin: 0;
  font-size: 14px;
}

.governance-grid {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 12px;
}

.governance-grid label {
  display: grid;
  gap: 6px;
  font-size: 12px;
  color: #4b5563;
}

.governance-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.danger {
  border: 1px solid rgba(185, 28, 28, 0.4);
  background: #fee2e2;
  color: #991b1b;
  border-radius: 8px;
  padding: 8px 10px;
  cursor: pointer;
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
