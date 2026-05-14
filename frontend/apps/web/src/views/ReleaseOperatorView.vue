<template>
  <main class="release-operator">
    <section class="release-operator__header">
      <div>
        <p class="eyebrow">{{ copy.eyebrow || 'Release Operator Surface' }}</p>
        <h1>{{ copy.title || '发布控制台' }}</h1>
        <p>{{ copy.description || '查看当前发布状态、候选快照、待审批动作与回滚目标。' }}</p>
      </div>
      <div class="release-operator__actions">
        <select v-model="selectedProduct" class="release-operator__select" @change="loadSurface">
          <option v-for="product in products" :key="product.product_key" :value="product.product_key">
            {{ product.label || product.product_key }} · {{ product.product_key }}
          </option>
        </select>
        <button class="sc-btn sc-btn-ghost" type="button" :disabled="loading" @click="loadSurface">
          {{ copy.action_refresh || '刷新' }}
        </button>
        <button
          class="sc-btn sc-btn-ghost"
          type="button"
          :disabled="busyKey === 'sync_policy' || !syncPolicyAction.enabled"
          @click="syncPolicy"
        >
          {{ copy.sync_policy_action_label || '同步已实现能力' }}
        </button>
        <button
          class="sc-btn sc-btn-primary"
          type="button"
          :disabled="busyKey === 'freeze' || !freezeAction.enabled"
          @click="freeze"
        >
          {{ copy.freeze_action_label || '冻结候选快照' }}
        </button>
      </div>
    </section>

    <StatusPanel
      v-if="loading && !surface"
      title="正在加载发布控制台..."
      variant="info"
    />
    <StatusPanel
      v-else-if="error"
      :title="copy.error_title || '加载失败'"
      :message="error"
      variant="error"
      :on-retry="loadSurface"
    />

    <template v-else-if="surface">
      <section class="release-operator__metrics">
        <article class="release-operator__metric">
          <span>{{ copy.metric_current_product || '当前产品' }}</span>
          <strong>{{ identity.product_key || '-' }}</strong>
        </article>
        <article class="release-operator__metric">
          <span>{{ copy.metric_active_snapshot || 'Active Released Snapshot' }}</span>
          <strong>{{ activeSnapshot.version || activeSnapshot.id || '-' }}</strong>
        </article>
        <article class="release-operator__metric">
          <span>{{ copy.metric_latest_action || 'Latest Action' }}</span>
          <strong>{{ runtimeSummary.latest_action_type || '-' }}</strong>
        </article>
        <article class="release-operator__metric">
          <span>{{ copy.metric_approval_state || 'Approval State' }}</span>
          <strong>{{ runtimeSummary.latest_action_approval_state || '-' }}</strong>
        </article>
      </section>

      <section class="release-operator__section">
        <div class="release-operator__section-head">
          <h2>{{ copy.section_control_scope || '受控内容' }}</h2>
          <p>{{ controlScope.policy_state || '-' }} / {{ controlScope.access_level || '-' }}</p>
        </div>
        <div class="release-operator__policy-control">
          <label>
            <span>{{ copy.policy_state_label || '发布状态' }}</span>
            <select v-model="policyState" class="release-operator__select">
              <option value="draft">draft</option>
              <option value="preview">preview</option>
              <option value="stable">stable</option>
              <option value="archived">archived</option>
            </select>
          </label>
          <label>
            <span>{{ copy.policy_access_label || '访问级别' }}</span>
            <select v-model="policyAccessLevel" class="release-operator__select">
              <option value="public">public</option>
              <option value="internal">internal</option>
              <option value="role_restricted">role_restricted</option>
            </select>
          </label>
          <button
            class="sc-btn sc-btn-ghost"
            type="button"
            :disabled="busyKey === 'update_policy' || !updatePolicyAction.enabled"
            @click="savePolicy"
          >
            {{ copy.save_policy_action_label || '保存策略' }}
          </button>
        </div>
        <div class="release-operator__scope-grid">
          <article>
            <span>{{ copy.metric_controlled_menus || '受控菜单' }}</span>
            <strong>{{ controlScope.menu_count ?? 0 }}</strong>
          </article>
          <article>
            <span>{{ copy.metric_controlled_scenes || '受控场景' }}</span>
            <strong>{{ controlScope.scene_count ?? 0 }}</strong>
          </article>
          <article>
            <span>{{ copy.metric_controlled_capabilities || '受控能力' }}</span>
            <strong>{{ controlScope.capability_count ?? 0 }}</strong>
          </article>
        </div>
        <div v-if="controlledScenes.length" class="release-operator__chips">
          <span v-for="scene in controlledScenes" :key="sceneChipLabel(scene)">
            {{ sceneChipLabel(scene) }}
          </span>
        </div>
      </section>

      <section class="release-operator__section">
        <div class="release-operator__section-head">
          <h2>{{ copy.section_candidate || '可 Promote 候选' }}</h2>
          <p>{{ copy.hint_candidate || '仅展示当前产品下 candidate / approved 状态的候选快照。' }}</p>
        </div>
        <div v-if="candidateSnapshots.length" class="release-operator__table-wrap">
          <table class="release-operator__table">
            <thead>
              <tr>
                <th>版本</th>
                <th>状态</th>
                <th>通道</th>
                <th>冻结时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="snapshot in candidateSnapshots" :key="`candidate-${snapshot.id}`">
                <td>{{ snapshot.version || '-' }}</td>
                <td><span class="release-operator__pill">{{ snapshot.state || '-' }}</span></td>
                <td>{{ snapshot.channel || '-' }}</td>
                <td>{{ snapshot.frozen_at || '-' }}</td>
                <td>
                  <button
                    class="sc-btn sc-btn-primary release-operator__row-action"
                    type="button"
                    :disabled="busyKey === `promote:${snapshot.id}`"
                    @click="promote(snapshot)"
                  >
                    发布
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="release-operator__empty">{{ copy.empty_candidate || '当前没有可 Promote 的候选快照。' }}</p>
      </section>

      <section class="release-operator__section">
        <div class="release-operator__section-head">
          <h2>{{ copy.section_pending || '待审批动作' }}</h2>
          <p>{{ copy.hint_pending_count_prefix || '当前数量：' }}{{ pendingActions.length }}</p>
        </div>
        <div v-if="pendingActions.length" class="release-operator__table-wrap">
          <table class="release-operator__table">
            <thead>
              <tr>
                <th>动作</th>
                <th>产品</th>
                <th>审批</th>
                <th>请求时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="action in pendingActions" :key="`pending-${action.id}`">
                <td>{{ action.action_type || '-' }}</td>
                <td>{{ action.product_key || '-' }}</td>
                <td>{{ action.approval_state || '-' }}</td>
                <td>{{ action.requested_at || '-' }}</td>
                <td>
                  <button
                    class="sc-btn sc-btn-primary release-operator__row-action"
                    type="button"
                    :disabled="busyKey === `approve:${action.id}` || action.can_approve === false"
                    @click="approve(action)"
                  >
                    {{ copy.approve_action_label || '审批并执行' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="release-operator__empty">{{ copy.empty_pending || '当前没有待审批动作。' }}</p>
      </section>

      <section class="release-operator__section release-operator__section--split">
        <div>
          <h2>{{ copy.section_rollback || '回滚' }}</h2>
          <p>{{ copy.hint_rollback || '仅当当前 active released snapshot 存在 rollback target 时可执行。' }}</p>
        </div>
        <button
          class="sc-btn sc-btn-ghost"
          type="button"
          :disabled="!rollbackAction.enabled || busyKey === 'rollback'"
          @click="rollback"
        >
          {{ copy.rollback_action_label || '执行回滚' }}
        </button>
      </section>

      <section class="release-operator__section">
        <div class="release-operator__section-head">
          <h2>{{ copy.section_history || '发布历史' }}</h2>
          <p>{{ copy.hint_history || '最近 action 与 snapshot。' }}</p>
        </div>
        <div class="release-operator__history">
          <div>
            <h3>{{ copy.history_snapshots_title || 'Snapshots' }}</h3>
            <ul>
              <li v-for="snapshot in historySnapshots" :key="`history-snapshot-${snapshot.id}`">
                <strong>{{ snapshot.version || snapshot.id }}</strong>
                <span>{{ snapshot.state || '-' }}</span>
              </li>
            </ul>
          </div>
          <div>
            <h3>{{ copy.history_actions_title || 'Actions' }}</h3>
            <ul>
              <li v-for="action in historyActions" :key="`history-action-${action.id}`">
                <strong>{{ action.action_type || action.id }}</strong>
                <span>{{ action.state || '-' }} / {{ action.approval_state || '-' }}</span>
              </li>
            </ul>
          </div>
        </div>
      </section>
    </template>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { intentRequest } from '../api/intents';

type AnyRecord = Record<string, unknown>;

interface ProductRow {
  product_key: string;
  label?: string;
}

interface SnapshotRow {
  id: number;
  version?: string;
  state?: string;
  channel?: string;
  frozen_at?: string;
}

interface ReleaseActionRow {
  id: number;
  action_type?: string;
  product_key?: string;
  state?: string;
  approval_state?: string;
  requested_at?: string;
  can_approve?: boolean;
}

interface ReleaseOperatorSurface {
  copy?: AnyRecord;
  identity?: AnyRecord;
  products?: ProductRow[];
  control_scope?: AnyRecord;
  release_state?: AnyRecord;
  pending_approval?: { actions?: ReleaseActionRow[] };
  candidate_snapshots?: SnapshotRow[];
  release_history?: { actions?: ReleaseActionRow[]; snapshots?: SnapshotRow[] };
  available_actions?: AnyRecord;
}

const route = useRoute();
const initialProduct = String(route.query.product_key || '').trim();
const surface = ref<ReleaseOperatorSurface | null>(null);
const selectedProduct = ref(initialProduct);
const loading = ref(false);
const error = ref('');
const busyKey = ref('');
const policyState = ref('stable');
const policyAccessLevel = ref('public');

const copy = computed<Record<string, string>>(() => {
  const raw = surface.value?.copy || {};
  return Object.fromEntries(
    Object.entries(raw).map(([key, value]) => [key, String(value || '')]),
  );
});
const identity = computed(() => surface.value?.identity || {});
const products = computed(() => surface.value?.products || []);
const controlScope = computed(() => surface.value?.control_scope || {});
const controlledScenes = computed(() => {
  const scenes = controlScope.value.scenes;
  return Array.isArray(scenes) ? scenes as AnyRecord[] : [];
});
const releaseState = computed(() => surface.value?.release_state || {});
const activeSnapshot = computed(() => (releaseState.value.active_snapshot || {}) as AnyRecord);
const runtimeSummary = computed(() => (releaseState.value.runtime_summary || {}) as AnyRecord);
const candidateSnapshots = computed(() => surface.value?.candidate_snapshots || []);
const pendingActions = computed(() => surface.value?.pending_approval?.actions || []);
const historySnapshots = computed(() => surface.value?.release_history?.snapshots || []);
const historyActions = computed(() => surface.value?.release_history?.actions || []);
const rollbackAction = computed(() => {
  const actions = surface.value?.available_actions || {};
  return (actions.rollback || {}) as { enabled?: boolean; params?: AnyRecord };
});
const syncPolicyAction = computed(() => {
  const actions = surface.value?.available_actions || {};
  return (actions.sync_policy || {}) as { enabled?: boolean; params?: AnyRecord };
});
const updatePolicyAction = computed(() => {
  const actions = surface.value?.available_actions || {};
  return (actions.update_policy || {}) as { enabled?: boolean; params?: AnyRecord };
});

function sceneChipLabel(scene: AnyRecord) {
  return String(scene.label || scene.scene_key || scene.key || '').trim() || '未命名场景';
}
const freezeAction = computed(() => {
  const actions = surface.value?.available_actions || {};
  return (actions.freeze || {}) as { enabled?: boolean; params?: AnyRecord };
});

function hydratePolicyControls(payload: ReleaseOperatorSurface) {
  const scope = payload.control_scope || {};
  policyState.value = String(scope.policy_state || 'stable');
  policyAccessLevel.value = String(scope.access_level || 'public');
}

async function loadSurface() {
  loading.value = true;
  error.value = '';
  try {
    const payload = await intentRequest<ReleaseOperatorSurface>({
      intent: 'release.operator.surface',
      params: {
        product_key: selectedProduct.value,
        action_limit: 20,
      },
    });
    surface.value = payload;
    hydratePolicyControls(payload);
    const resolvedProduct = String(payload.identity?.product_key || '').trim();
    if (resolvedProduct) {
      selectedProduct.value = resolvedProduct;
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '发布控制台不可用';
  } finally {
    loading.value = false;
  }
}

async function runWrite(intent: string, params: AnyRecord, key: string) {
  busyKey.value = key;
  error.value = '';
  try {
    const result = await intentRequest<{ surface?: ReleaseOperatorSurface }>({ intent, params });
    if (result.surface) {
      surface.value = result.surface;
      hydratePolicyControls(result.surface);
      const resolvedProduct = String(result.surface.identity?.product_key || '').trim();
      if (resolvedProduct) selectedProduct.value = resolvedProduct;
    } else {
      await loadSurface();
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '发布动作执行失败';
  } finally {
    busyKey.value = '';
  }
}

function promote(snapshot: SnapshotRow) {
  void runWrite(
    'release.operator.promote',
    {
      product_key: selectedProduct.value,
      snapshot_id: snapshot.id,
      replace_active: true,
    },
    `promote:${snapshot.id}`,
  );
}

function approve(action: ReleaseActionRow) {
  void runWrite('release.operator.approve', { action_id: action.id }, `approve:${action.id}`);
}

function freeze() {
  const params = freezeAction.value.params || { product_key: selectedProduct.value };
  void runWrite('release.operator.freeze', params, 'freeze');
}

function syncPolicy() {
  const params = syncPolicyAction.value.params || { product_key: selectedProduct.value };
  void runWrite('release.operator.sync_policy', params, 'sync_policy');
}

function savePolicy() {
  const params = updatePolicyAction.value.params || { product_key: selectedProduct.value };
  void runWrite(
    'release.operator.update_policy',
    {
      ...params,
      product_key: selectedProduct.value,
      state: policyState.value,
      access_level: policyAccessLevel.value,
    },
    'update_policy',
  );
}

function rollback() {
  const params = rollbackAction.value.params || {};
  void runWrite('release.operator.rollback', params, 'rollback');
}

onMounted(() => {
  void loadSurface();
});
</script>

<style scoped>
.release-operator {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 24px;
}

.release-operator__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.release-operator__header h1 {
  margin: 2px 0 8px;
  font-size: 28px;
  line-height: 1.2;
}

.release-operator__header p {
  margin: 0;
  color: #64748b;
}

.release-operator__actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.release-operator__select {
  min-width: 190px;
  height: 38px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #0f172a;
  padding: 0 10px;
}

.release-operator__metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.release-operator__metric,
.release-operator__section {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
}

.release-operator__metric {
  padding: 14px;
}

.release-operator__metric span {
  display: block;
  margin-bottom: 8px;
  color: #64748b;
  font-size: 12px;
}

.release-operator__metric strong {
  display: block;
  overflow-wrap: anywhere;
  color: #0f172a;
  font-size: 18px;
}

.release-operator__scope-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.release-operator__policy-control {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 10px;
  margin-bottom: 12px;
}

.release-operator__policy-control label {
  display: grid;
  gap: 6px;
}

.release-operator__policy-control span {
  color: #64748b;
  font-size: 12px;
}

.release-operator__scope-grid article {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
}

.release-operator__scope-grid span {
  display: block;
  margin-bottom: 8px;
  color: #64748b;
  font-size: 12px;
}

.release-operator__scope-grid strong {
  color: #0f172a;
  font-size: 22px;
}

.release-operator__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.release-operator__chips span {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  padding: 5px 10px;
  color: #334155;
  font-size: 12px;
}

.release-operator__section {
  padding: 16px;
}

.release-operator__section--split {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.release-operator__section h2,
.release-operator__section h3 {
  margin: 0;
  color: #0f172a;
}

.release-operator__section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.release-operator__section p {
  margin: 6px 0 0;
  color: #64748b;
}

.release-operator__table-wrap {
  overflow-x: auto;
}

.release-operator__table {
  width: 100%;
  border-collapse: collapse;
}

.release-operator__table th,
.release-operator__table td {
  border-top: 1px solid #e2e8f0;
  padding: 10px 8px;
  text-align: left;
  white-space: nowrap;
}

.release-operator__table th {
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}

.release-operator__pill {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  border-radius: 999px;
  background: #e0f2fe;
  color: #075985;
  padding: 0 9px;
  font-size: 12px;
}

.release-operator__row-action {
  min-width: 72px;
}

.release-operator__empty {
  border-top: 1px solid #e2e8f0;
  padding-top: 12px;
}

.release-operator__history {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.release-operator__history ul {
  display: grid;
  gap: 8px;
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
}

.release-operator__history li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-top: 1px solid #e2e8f0;
  padding-top: 8px;
}

.release-operator__history span {
  color: #64748b;
}

@media (max-width: 900px) {
  .release-operator {
    padding: 16px;
  }

  .release-operator__header,
  .release-operator__section-head,
  .release-operator__section--split {
    flex-direction: column;
    align-items: stretch;
  }

  .release-operator__metrics,
  .release-operator__scope-grid,
  .release-operator__history {
    grid-template-columns: 1fr;
  }

  .release-operator__actions {
    flex-wrap: wrap;
  }
}
</style>
