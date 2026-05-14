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
          <h2>产品配置发布线</h2>
          <p>草案、检查、候选、发布、生效</p>
        </div>
        <div class="release-operator__pipeline">
          <article v-for="stage in pipelineStages" :key="pipelineKey(stage)">
            <span :class="['release-operator__stage-dot', `release-operator__stage-dot--${stage.status || 'pending'}`]"></span>
            <strong>{{ stage.label || stage.key || '-' }}</strong>
            <small>{{ stage.count ?? 0 }}</small>
          </article>
        </div>
        <div class="release-operator__summary-grid">
          <article>
            <span>当前发布页</span>
            <strong>{{ changeSummary.active_page_count ?? 0 }}</strong>
          </article>
          <article>
            <span>草案发布页</span>
            <strong>{{ changeSummary.draft_page_count ?? 0 }}</strong>
          </article>
          <article>
            <span>差异</span>
            <strong>{{ changeSummary.page_count_delta ?? 0 }}</strong>
          </article>
          <article>
            <span>预览/下线</span>
            <strong>{{ changeSummary.preview_page_count ?? 0 }} / {{ changeSummary.hidden_page_count ?? 0 }}</strong>
          </article>
        </div>
        <div class="release-operator__checks">
          <article v-for="check in preflightChecks" :key="pipelineKey(check)" :class="`release-operator__check--${check.status || 'pass'}`">
            <strong>{{ check.label || check.key || '-' }}</strong>
            <span>{{ check.message || '-' }}</span>
          </article>
        </div>
        <div class="release-operator__audience">
          <strong>生效试算</strong>
          <span>公司 {{ audienceSimulation.company_count ?? 0 }} 个，订阅 {{ audienceSimulation.subscription_count ?? 0 }} 个，角色 {{ audienceRoles }}</span>
        </div>
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
        <div v-if="controlDefinitions.length" class="release-operator__definition-grid">
          <article v-for="item in controlDefinitions" :key="definitionKey(item)">
            <strong>{{ item.label || item.key || '-' }}</strong>
            <span>{{ item.meaning || '-' }}</span>
          </article>
        </div>
        <div class="release-operator__scope-grid">
          <article>
            <span>{{ copy.metric_controlled_menus || '受控菜单' }}</span>
            <strong>{{ controlScope.menu_count ?? 0 }}</strong>
          </article>
          <article>
            <span>{{ copy.metric_controlled_pages || '受控页面' }}</span>
            <strong>{{ controlScope.page_count ?? controlScope.menu_count ?? 0 }}</strong>
          </article>
          <article>
            <span>{{ copy.metric_controlled_capabilities || '受控能力' }}</span>
            <strong>{{ controlScope.capability_count ?? 0 }}</strong>
          </article>
        </div>
        <div v-if="controlledPages.length" class="release-operator__table-wrap release-operator__page-table">
          <table class="release-operator__table">
            <thead>
              <tr>
                <th>用户菜单</th>
                <th>页面</th>
                <th>路由</th>
                <th>发布阶段</th>
                <th>可见范围</th>
                <th>来源</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="page in controlledPages" :key="pageKey(page)">
                <td>{{ page.visible_menu_path || page.group_label || '-' }}</td>
                <td>{{ page.page_label || page.label || page.page_key || '-' }}</td>
                <td>{{ page.route || '-' }}</td>
                <td>
                  <span :class="['release-operator__pill', releaseStateClass(page)]">
                    {{ releaseStateLabel(page) }}
                  </span>
                </td>
                <td>{{ accessLevelLabel(page) }}</td>
                <td>{{ sourceLabel(page) }}</td>
                <td>
                  <div class="release-operator__row-actions">
                    <button
                      class="sc-btn sc-btn-ghost release-operator__row-action"
                      type="button"
                      :disabled="busyKey === `page:${pageKey(page)}:released` || !updatePagePolicyAction.enabled"
                      @click="updatePagePolicy(page, { release_state: 'released', enabled: true })"
                    >
                      发布
                    </button>
                    <button
                      class="sc-btn sc-btn-ghost release-operator__row-action"
                      type="button"
                      :disabled="busyKey === `page:${pageKey(page)}:preview` || !updatePagePolicyAction.enabled"
                      @click="updatePagePolicy(page, { release_state: 'preview', enabled: true })"
                    >
                      预览
                    </button>
                    <button
                      class="sc-btn sc-btn-ghost release-operator__row-action"
                      type="button"
                      :disabled="busyKey === `page:${pageKey(page)}:hidden` || !updatePagePolicyAction.enabled"
                      @click="updatePagePolicy(page, { release_state: 'hidden', enabled: false })"
                    >
                      下线
                    </button>
                    <button
                      class="sc-btn sc-btn-ghost release-operator__row-action"
                      type="button"
                      :disabled="busyKey === `page:${pageKey(page)}:internal` || !updatePagePolicyAction.enabled"
                      @click="updatePagePolicy(page, { access_level: page.access_level === 'internal' ? 'public' : 'internal' })"
                    >
                      {{ page.access_level === 'internal' ? '转公开' : '内部' }}
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
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
  release_pipeline?: AnyRecord;
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
const releasePipeline = computed(() => surface.value?.release_pipeline || {});
const pipelineStages = computed(() => {
  const stages = releasePipeline.value.stages;
  return Array.isArray(stages) ? stages as AnyRecord[] : [];
});
const changeSummary = computed(() => (releasePipeline.value.change_summary || {}) as AnyRecord);
const preflightChecks = computed(() => {
  const checks = releasePipeline.value.preflight_checks;
  return Array.isArray(checks) ? checks as AnyRecord[] : [];
});
const audienceSimulation = computed(() => (releasePipeline.value.audience_simulation || {}) as AnyRecord);
const audienceRoles = computed(() => {
  const roles = audienceSimulation.value.role_scope;
  return Array.isArray(roles) && roles.length ? roles.join(', ') : '-';
});
const controlledPages = computed(() => {
  const pages = controlScope.value.pages;
  return Array.isArray(pages) ? pages as AnyRecord[] : [];
});
const controlDefinitions = computed(() => {
  const items = controlScope.value.control_definition;
  return Array.isArray(items) ? items as AnyRecord[] : [];
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
const updatePagePolicyAction = computed(() => {
  const actions = surface.value?.available_actions || {};
  return (actions.update_page_policy || {}) as { enabled?: boolean; params?: AnyRecord };
});

function pageKey(page: AnyRecord) {
  return String(page.page_key || page.scene_key || page.menu_key || page.capability_key || '').trim();
}
function definitionKey(item: AnyRecord) {
  return String(item.key || item.label || '').trim();
}
function pipelineKey(item: AnyRecord) {
  return String(item.key || item.label || '').trim();
}
function releaseStateLabel(page: AnyRecord) {
  const state = String(page.release_state || (page.enabled === false ? 'hidden' : 'released'));
  const labels: Record<string, string> = {
    released: '正式发布',
    preview: '预览',
    hidden: '未发布',
    retired: '已下线',
  };
  return labels[state] || state || '-';
}
function releaseStateClass(page: AnyRecord) {
  const state = String(page.release_state || (page.enabled === false ? 'hidden' : 'released'));
  if (state === 'preview') return 'release-operator__pill--preview';
  if (state === 'hidden' || state === 'retired' || page.enabled === false) return 'release-operator__pill--muted';
  return '';
}
function accessLevelLabel(page: AnyRecord) {
  const level = String(page.access_level || 'public');
  const labels: Record<string, string> = {
    public: '授权用户',
    internal: '内部可见',
    role_restricted: '按角色',
  };
  return labels[level] || level;
}
function sourceLabel(page: AnyRecord) {
  const menu = String(page.menu_xmlid || '').trim();
  const model = String(page.res_model || '').trim();
  if (menu && model) return `${menu} / ${model}`;
  return menu || model || String(page.source_kind || '').trim() || '-';
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

function updatePagePolicy(page: AnyRecord, updates: AnyRecord) {
  const key = pageKey(page);
  if (!key) return;
  const params = updatePagePolicyAction.value.params || { product_key: selectedProduct.value };
  const state = String(updates.release_state || updates.access_level || 'update');
  void runWrite(
    'release.operator.update_page_policy',
    {
      ...params,
      product_key: selectedProduct.value,
      page_key: key,
      ...updates,
    },
    `page:${key}:${state}`,
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

.release-operator__pipeline,
.release-operator__summary-grid,
.release-operator__checks {
  display: grid;
  gap: 10px;
}

.release-operator__pipeline {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.release-operator__pipeline article,
.release-operator__summary-grid article,
.release-operator__checks article,
.release-operator__audience {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px;
}

.release-operator__pipeline article {
  display: grid;
  gap: 6px;
}

.release-operator__pipeline strong,
.release-operator__summary-grid strong,
.release-operator__checks strong,
.release-operator__audience strong {
  color: #0f172a;
  font-size: 13px;
}

.release-operator__pipeline small,
.release-operator__summary-grid span,
.release-operator__checks span,
.release-operator__audience span {
  color: #64748b;
  font-size: 12px;
}

.release-operator__stage-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #94a3b8;
}

.release-operator__stage-dot--done,
.release-operator__stage-dot--active,
.release-operator__stage-dot--preview {
  background: #0ea5e9;
}

.release-operator__stage-dot--warn {
  background: #f59e0b;
}

.release-operator__stage-dot--blocked {
  background: #ef4444;
}

.release-operator__summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 10px;
}

.release-operator__summary-grid article {
  display: grid;
  gap: 6px;
}

.release-operator__summary-grid strong {
  font-size: 20px;
}

.release-operator__checks {
  grid-template-columns: repeat(5, minmax(0, 1fr));
  margin-top: 10px;
}

.release-operator__check--fail {
  border-color: #fecaca;
  background: #fef2f2;
}

.release-operator__check--warn {
  border-color: #fde68a;
  background: #fffbeb;
}

.release-operator__audience {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
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

.release-operator__definition-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.release-operator__definition-grid article {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px;
}

.release-operator__definition-grid strong,
.release-operator__definition-grid span {
  display: block;
}

.release-operator__definition-grid strong {
  margin-bottom: 5px;
  color: #0f172a;
  font-size: 13px;
}

.release-operator__definition-grid span {
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
  white-space: normal;
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

.release-operator__page-table {
  margin-top: 12px;
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

.release-operator__pill--muted {
  background: #f1f5f9;
  color: #64748b;
}

.release-operator__pill--preview {
  background: #fef3c7;
  color: #92400e;
}

.release-operator__row-actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
}

.release-operator__row-action {
  min-width: 52px;
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
  .release-operator__pipeline,
  .release-operator__summary-grid,
  .release-operator__checks,
  .release-operator__definition-grid,
  .release-operator__history {
    grid-template-columns: 1fr;
  }

  .release-operator__audience {
    flex-direction: column;
  }

  .release-operator__actions {
    flex-wrap: wrap;
  }
}
</style>
