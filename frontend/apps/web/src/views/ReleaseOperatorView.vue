<template>
  <section class="release-operator" :data-read-model-version="readModel.contract_version || ''">
    <header class="hero">
      <div>
        <p class="eyebrow">{{ surfaceText('eyebrow', 'Release Operator Surface') }}</p>
        <h1>{{ pageText('title', '发布控制台') }}</h1>
        <p class="description">{{ surfaceText('description', pageText('description', '发布控制台说明暂不可用。')) }}</p>
      </div>
      <div class="product-switch">
        <button
          v-for="item in products"
          :key="item.product_key"
          class="switch"
          :class="{ active: item.product_key === currentProductKey }"
          @click="openProduct(item.product_key)"
        >
          {{ item.label }}
        </button>
      </div>
    </header>

    <section v-if="errorMessage" class="panel panel-error">
      <h2>{{ surfaceText('error_title', pageText('error_title', '加载失败')) }}</h2>
      <p>{{ errorMessage }}</p>
      <button class="ghost" @click="loadSurface">{{ surfaceText('action_retry', pageText('action_retry', '重试')) }}</button>
    </section>

    <template v-else>
      <section class="panel">
        <div class="panel-head">
          <h2>{{ surfaceText('section_release_state', pageText('section_release_state', '当前发布状态')) }}</h2>
          <button class="ghost" :disabled="loading" @click="loadSurface">{{ surfaceText('action_refresh', '刷新') }}</button>
        </div>
        <div class="state-grid">
          <article class="metric">
            <span class="label">{{ surfaceText('metric_current_product', '当前产品') }}</span>
            <strong>{{ releaseState.product_key || currentProductKey }}</strong>
          </article>
          <article class="metric">
            <span class="label">{{ surfaceText('metric_active_snapshot', 'Active Released Snapshot') }}</span>
            <strong>{{ releaseState.active_version || 'N/A' }}</strong>
          </article>
          <article class="metric">
            <span class="label">{{ surfaceText('metric_latest_action', 'Latest Action') }}</span>
            <strong>{{ releaseState.latest_action_type || 'N/A' }}</strong>
          </article>
          <article class="metric">
            <span class="label">{{ surfaceText('metric_approval_state', 'Approval State') }}</span>
            <strong>{{ releaseState.latest_action_approval_state || 'N/A' }}</strong>
          </article>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>{{ surfaceText('section_candidate', pageText('section_candidate', '可 Promote 候选')) }}</h2>
          <span class="hint">{{ surfaceText('hint_candidate', pageText('hint_candidate', '候选快照说明暂不可用。')) }}</span>
        </div>
        <div v-if="candidateSnapshots.length" class="list">
          <article v-for="row in candidateSnapshots" :key="`candidate-${row.id}`" class="list-row">
            <div>
              <strong>{{ row.version }}</strong>
              <p>{{ row.state }} · snapshot {{ row.id }}</p>
            </div>
            <button
              class="primary"
              :disabled="loading || !row.promote_action?.enabled"
              @click="runPromote(row.promote_action)"
            >
              {{ row.promote_action?.label || '发起 Promote' }}
            </button>
          </article>
        </div>
        <p v-else class="empty">{{ surfaceText('empty_candidate', pageText('empty_candidate', '候选快照空态说明暂不可用。')) }}</p>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>{{ surfaceText('section_pending', pageText('section_pending', '待审批动作')) }}</h2>
          <span class="hint">{{ surfaceText('hint_pending_count_prefix', pageText('hint_pending_count_prefix', '当前数量：')) }}{{ pendingApprovals.length }}</span>
        </div>
        <div v-if="pendingApprovals.length" class="list">
          <article v-for="row in pendingApprovals" :key="`pending-${row.id}`" class="list-row">
            <div>
              <strong>{{ row.action_type }}</strong>
              <p>action {{ row.id }} · {{ row.product_key }} · {{ row.approval_state }}</p>
            </div>
            <button
              class="primary"
              :disabled="loading || !row.can_approve"
              @click="approveAction(row.id)"
            >
              {{ surfaceText('approve_action_label', '审批并执行') }}
            </button>
          </article>
        </div>
        <p v-else class="empty">{{ surfaceText('empty_pending', pageText('empty_pending', '待审批空态说明暂不可用。')) }}</p>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>{{ surfaceText('section_rollback', pageText('section_rollback', '回滚')) }}</h2>
          <span class="hint">{{ surfaceText('hint_rollback', pageText('hint_rollback', '回滚说明暂不可用。')) }}</span>
        </div>
        <div class="list-row">
          <div>
            <strong>{{ surfaceText('rollback_target_label', 'Rollback Target') }}</strong>
            <p>snapshot {{ rollbackAction.params?.target_snapshot_id || 0 }}</p>
          </div>
          <button
            class="danger"
            :disabled="loading || !rollbackAction.enabled"
            @click="runRollback"
          >
            {{ surfaceText('rollback_action_label', '执行回滚') }}
          </button>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>{{ surfaceText('section_history', '发布历史') }}</h2>
          <span class="hint">{{ surfaceText('hint_history', '最近 action 与 snapshot。') }}</span>
        </div>
        <div class="history-grid">
          <div>
            <h3>{{ surfaceText('history_actions_title', 'Actions') }}</h3>
            <ul class="history">
              <li v-for="row in historyActions" :key="`action-${row.id}`">
                <strong>{{ row.action_type }}</strong>
                <span>{{ row.state }} · {{ row.approval_state || 'n/a' }}</span>
              </li>
            </ul>
          </div>
          <div>
            <h3>{{ surfaceText('history_snapshots_title', 'Snapshots') }}</h3>
            <ul class="history">
              <li v-for="row in historySnapshots" :key="`snapshot-${row.id}`">
                <strong>{{ row.version }}</strong>
                <span>{{ row.state }} · active={{ row.is_active ? 'yes' : 'no' }}</span>
              </li>
            </ul>
          </div>
        </div>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { intentRequest } from '../api/intents';
import { usePageContract } from '../app/pageContract';

type OperatorAction = {
  key?: string;
  label?: string;
  intent?: string;
  enabled?: boolean;
  reason_code?: string;
  params?: Record<string, unknown>;
};

type OperatorSnapshot = {
  id: number;
  version?: string;
  state?: string;
  is_active?: boolean;
  promote_action?: OperatorAction | null;
};

type OperatorPendingAction = {
  id: number;
  action_type?: string;
  product_key?: string;
  approval_state?: string;
  can_approve?: boolean;
};

type OperatorSurface = {
  copy?: Record<string, unknown>;
  read_model_v1?: Record<string, unknown>;
  identity?: Record<string, unknown>;
  products?: Array<Record<string, unknown>>;
  release_state?: {
    active_snapshot?: Record<string, unknown>;
    runtime_summary?: Record<string, unknown>;
  };
  pending_approval?: {
    actions?: OperatorPendingAction[];
  };
  candidate_snapshots?: OperatorSnapshot[];
  release_history?: {
    actions?: Array<Record<string, unknown>>;
    snapshots?: Array<Record<string, unknown>>;
  };
  available_actions?: {
    rollback?: OperatorAction;
  };
};

const router = useRouter();
const route = useRoute();
const pageContract = usePageContract('release_operator');
const pageText = pageContract.text;

const loading = ref(false);
const errorMessage = ref('');
const surface = ref<OperatorSurface>({});

function buildLegacyReadModel(value: OperatorSurface): Record<string, unknown> {
  return {
    contract_version: '',
    identity: value.identity || {},
    products: Array.isArray(value.products) ? value.products : [],
    current_release_state: value.release_state || {},
    pending_approval_queue: value.pending_approval || {},
    candidate_snapshots: Array.isArray(value.candidate_snapshots) ? value.candidate_snapshots : [],
    release_history_summary: value.release_history || {},
    available_operator_actions: value.available_actions || {},
  };
}

const readModel = computed<Record<string, unknown>>(() => {
  const row = surface.value.read_model_v1;
  if (row && typeof row === 'object') {
    return row as Record<string, unknown>;
  }
  return buildLegacyReadModel(surface.value);
});

const surfaceCopy = computed<Record<string, unknown>>(() => {
  const readModelCopy = readModel.value.copy;
  if (readModelCopy && typeof readModelCopy === 'object') {
    return readModelCopy as Record<string, unknown>;
  }
  const topLevelCopy = surface.value.copy;
  if (topLevelCopy && typeof topLevelCopy === 'object') {
    return topLevelCopy as Record<string, unknown>;
  }
  return {};
});

function surfaceText(key: string, fallback = ''): string {
  const value = surfaceCopy.value[key];
  return typeof value === 'string' && value.trim() ? value.trim() : fallback;
}

function syncReadModelRuntimeMarker(contractVersion: string) {
  if (typeof window === 'undefined') return;
  (window as Window & { __releaseOperatorReadModelVersion?: string }).__releaseOperatorReadModelVersion = contractVersion;
}

const currentProductKey = computed(() => {
  const raw = String(route.query.product_key || '').trim();
  return raw || 'construction.standard';
});

const products = computed(() => {
  const rows = Array.isArray(readModel.value.products) ? readModel.value.products : [];
  return rows.map((row) => ({
    product_key: String(row.product_key || '').trim(),
    label: String(row.label || row.product_key || '').trim(),
  })).filter((row) => row.product_key);
});

const releaseState = computed(() => {
  const state = (readModel.value.current_release_state && typeof readModel.value.current_release_state === 'object')
    ? readModel.value.current_release_state as Record<string, unknown>
    : {};
  const activeSnapshot = (state.active_snapshot && typeof state.active_snapshot === 'object')
    ? state.active_snapshot as Record<string, unknown>
    : {};
  const runtimeSummary = (state.runtime_summary && typeof state.runtime_summary === 'object')
    ? state.runtime_summary as Record<string, unknown>
    : {};
  return {
    product_key: String((readModel.value.identity as Record<string, unknown> | undefined)?.product_key || '').trim(),
    active_version: String(activeSnapshot.version || runtimeSummary.active_snapshot_version || '').trim(),
    latest_action_type: String(runtimeSummary.latest_action_type || '').trim(),
    latest_action_approval_state: String(runtimeSummary.latest_action_approval_state || '').trim(),
  };
});

const pendingApprovals = computed(() => {
  const queue = (readModel.value.pending_approval_queue && typeof readModel.value.pending_approval_queue === 'object')
    ? readModel.value.pending_approval_queue as Record<string, unknown>
    : {};
  const rows = queue.actions;
  return Array.isArray(rows) ? rows : [];
});

const candidateSnapshots = computed(() => {
  const rows = Array.isArray(readModel.value.candidate_snapshots) ? readModel.value.candidate_snapshots : [];
  const availableActions = (readModel.value.available_operator_actions && typeof readModel.value.available_operator_actions === 'object')
    ? readModel.value.available_operator_actions as Record<string, unknown>
    : {};
  const promoteActions = Array.isArray(availableActions.promote)
    ? (availableActions.promote as OperatorAction[])
    : [];
  return rows.map((row) => ({
    ...row,
    promote_action: promoteActions.find((item) => Number(item.params?.snapshot_id || 0) === Number(row.id || 0)) || null,
  }));
});

const rollbackAction = computed<OperatorAction>(() => {
  const availableActions = (readModel.value.available_operator_actions && typeof readModel.value.available_operator_actions === 'object')
    ? readModel.value.available_operator_actions as Record<string, unknown>
    : {};
  const row = availableActions.rollback;
  return row && typeof row === 'object' ? row : { enabled: false, params: {} };
});

const historyActions = computed(() => {
  const history = (readModel.value.release_history_summary && typeof readModel.value.release_history_summary === 'object')
    ? readModel.value.release_history_summary as Record<string, unknown>
    : {};
  const rows = history.actions;
  return Array.isArray(rows) ? rows : [];
});

const historySnapshots = computed(() => {
  const history = (readModel.value.release_history_summary && typeof readModel.value.release_history_summary === 'object')
    ? readModel.value.release_history_summary as Record<string, unknown>
    : {};
  const rows = history.snapshots;
  return Array.isArray(rows) ? rows : [];
});

async function loadSurface() {
  loading.value = true;
  errorMessage.value = '';
  let lastError: unknown = null;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const result = await intentRequest<OperatorSurface>({
        intent: 'release.operator.surface',
        params: {
          product_key: currentProductKey.value,
          action_limit: 20,
        },
      });
      surface.value = result || {};
      syncReadModelRuntimeMarker(String((result?.read_model_v1 as Record<string, unknown> | undefined)?.contract_version || ''));
      loading.value = false;
      return;
    } catch (error) {
      lastError = error;
      if (attempt < 2) {
        await new Promise((resolve) => window.setTimeout(resolve, 1200));
      }
    }
  }
  syncReadModelRuntimeMarker('');
  errorMessage.value = String((lastError as Error)?.message || lastError || 'release operator load failed');
  loading.value = false;
}

function openProduct(productKey: string) {
  router.push({ path: '/release/operator', query: { product_key: productKey } }).catch(() => {});
}

async function runPromote(action: OperatorAction | null | undefined) {
  if (!action?.intent || !action.enabled) return;
  loading.value = true;
  errorMessage.value = '';
  try {
    await intentRequest({
      intent: action.intent,
      params: action.params || {},
    });
    await loadSurface();
  } catch (error) {
    errorMessage.value = String((error as Error)?.message || error || 'promote failed');
    loading.value = false;
  }
}

async function approveAction(actionId: number) {
  loading.value = true;
  errorMessage.value = '';
  try {
    await intentRequest({
      intent: 'release.operator.approve',
      params: {
        action_id: actionId,
        execute_after_approval: true,
      },
    });
    await loadSurface();
  } catch (error) {
    errorMessage.value = String((error as Error)?.message || error || 'approval failed');
    loading.value = false;
  }
}

async function runRollback() {
  if (!rollbackAction.value.intent || !rollbackAction.value.enabled) return;
  loading.value = true;
  errorMessage.value = '';
  try {
    await intentRequest({
      intent: rollbackAction.value.intent,
      params: rollbackAction.value.params || {},
    });
    await loadSurface();
  } catch (error) {
    errorMessage.value = String((error as Error)?.message || error || 'rollback failed');
    loading.value = false;
  }
}

onMounted(() => {
  loadSurface().catch(() => {});
});
</script>

<style scoped>
.release-operator {
  display: grid;
  gap: 18px;
  padding: 28px;
}

.hero,
.panel {
  border-radius: 20px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
  padding: 24px;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  background: linear-gradient(145deg, #fffaf5 0%, #f4f7fb 100%);
}

.eyebrow,
.hint {
  margin: 0;
  color: #8b5e3c;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.description,
.empty,
.list-row p {
  margin: 6px 0 0;
  color: #475569;
}

.product-switch,
.panel-head,
.list-row,
.state-grid,
.history-grid {
  display: flex;
  gap: 12px;
}

.product-switch,
.panel-head {
  align-items: center;
  justify-content: space-between;
}

.switch,
.ghost,
.primary,
.danger {
  border-radius: 999px;
  padding: 10px 16px;
  font-weight: 600;
  cursor: pointer;
}

.switch,
.ghost {
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: #fff;
  color: #0f172a;
}

.switch.active,
.primary {
  border: 0;
  background: linear-gradient(135deg, #2f3a5f, #1d4e89);
  color: #fff;
}

.danger {
  border: 0;
  background: linear-gradient(135deg, #7f1d1d, #b91c1c);
  color: #fff;
}

.panel-error {
  border-color: rgba(185, 28, 28, 0.24);
}

.state-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-top: 16px;
}

.metric {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 16px;
  background: #f8fafc;
}

.metric .label {
  font-size: 12px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.list {
  display: grid;
  gap: 12px;
}

.list-row {
  justify-content: space-between;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  margin-top: 16px;
}

.history {
  display: grid;
  gap: 10px;
  padding-left: 18px;
}

.history li {
  display: grid;
  gap: 4px;
  color: #475569;
}
</style>
