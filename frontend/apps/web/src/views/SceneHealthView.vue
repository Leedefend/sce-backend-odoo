<template>
  <section class="scene-health">
    <header v-if="pageSectionEnabled('header', true) && pageSectionTagIs('header', 'header')" class="header" :style="pageSectionStyle('header')">
      <div>
        <h2>{{ pageText('title', '场景健康状态') }}</h2>
        <p>{{ pageText('subtitle', '可视化查看场景健康状态与自动降级结果。') }}</p>
      </div>
      <div class="actions">
        <label>
          <span>公司</span>
          <select v-model="companyIdText" @change="loadHealth">
            <option value="">当前公司</option>
            <option v-for="company in companies" :key="company.id" :value="String(company.id)">
              {{ company.name }}
            </option>
          </select>
        </label>
        <button
          v-for="action in headerActions"
          :key="action.key"
          class="secondary"
          @click="executeHeaderAction(action.key)"
        >
          {{ action.label }}
        </button>
      </div>
    </header>

    <StatusPanel
      v-if="pageSectionEnabled('status_loading', true) && pageSectionTagIs('status_loading', 'section') && loading"
      :title="pageText('loading_title', '正在加载场景健康状态')"
      variant="info"
      :style="pageSectionStyle('status_loading')"
    />
    <StatusPanel
      v-else-if="pageSectionEnabled('status_error', true) && pageSectionTagIs('status_error', 'section') && errorText"
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="statusError?.traceId || errorTraceId || undefined"
      :error-code="statusError?.code"
      :reason-code="statusError?.reasonCode"
      :error-category="statusError?.errorCategory"
      :error-details="statusError?.details"
      :retryable="statusError?.retryable"
      :hint="errorCopy.hint"
      :suggested-action="statusError?.suggestedAction"
      variant="error"
      :on-retry="loadHealth"
      :style="pageSectionStyle('status_error')"
    />

    <div
      v-else-if="pageSectionEnabled('content', true) && pageSectionTagIs('content', 'div') && health"
      class="content"
      :style="pageSectionStyle('content')"
    >
      <article class="pill-row">
        <span class="pill">通道：{{ sceneChannelLabel(health.scene_channel) }}</span>
        <span class="pill" :class="{ warn: health.rollback_active }">
          回滚：{{ health.rollback_active ? '已启用' : '未启用' }}
        </span>
        <span class="pill">版本：{{ health.scene_version || '-' }}</span>
        <span class="pill">健康模型：{{ healthSchemaVersionLabel }}</span>
      </article>

      <section v-if="pageSectionEnabled('cards', true) && pageSectionTagIs('cards', 'section')" class="cards" :style="pageSectionStyle('cards')">
        <article class="card danger">
          <h3>关键配置问题</h3>
          <p>{{ health.summary.critical_resolve_errors_count }}</p>
        </article>
        <article class="card danger">
          <h3>关键漂移预警</h3>
          <p>{{ health.summary.critical_drift_warn_count }}</p>
        </article>
        <article class="card">
          <h3>一般治理项</h3>
          <p>{{ health.summary.non_critical_debt_count }}</p>
        </article>
      </section>

      <article v-if="pageSectionEnabled('meta', true) && pageSectionTagIs('meta', 'section')" class="meta" :style="pageSectionStyle('meta')">
        <p><strong>配置版本：</strong> {{ health.contract_ref || '未返回' }}</p>
        <p><strong>处理编号：</strong> {{ health.trace_id || '-' }}</p>
        <p><strong>更新时间：</strong> {{ health.last_updated_at || '-' }}</p>
        <p><strong>自动降级：</strong> {{ autoDegradeLabel }}</p>
        <p v-if="governanceTraceId"><strong>治理处理编号：</strong> {{ governanceTraceId }}</p>
      </article>

      <article
        v-if="pageSectionEnabled('governance_runtime', true) && pageSectionTagIs('governance_runtime', 'section') && governanceSnapshot"
        class="meta"
        :style="pageSectionStyle('governance_runtime')"
      >
        <p><strong>治理通道：</strong> {{ sceneChannelLabel(governanceSnapshot.scene_channel) }}</p>
        <p><strong>运行策略：</strong> {{ runtimeSourceLabel(governanceSnapshot.runtime_source) }}</p>
        <p><strong>治理门禁：</strong> {{ governanceGatesLabel }}</p>
        <p><strong>治理原因：</strong> {{ governanceReasonsLabel }}</p>
        <p><strong>场景消费：</strong> {{ governanceConsumptionLabel }}</p>
      </article>

      <section v-if="pageSectionEnabled('governance', true) && pageSectionTagIs('governance', 'section')" class="governance" :style="pageSectionStyle('governance')">
        <h3>治理操作</h3>
        <div class="governance-grid">
          <label>
            <span>目标通道</span>
            <select v-model="targetChannel">
              <option value="stable">稳定版</option>
              <option value="beta">灰度版</option>
              <option value="dev">开发版</option>
            </select>
          </label>
          <label class="reason">
            <span>操作说明（必填）</span>
            <input v-model="governanceReason" type="text" placeholder="填写本次治理原因" />
          </label>
        </div>
        <div class="governance-actions">
          <button class="secondary" :disabled="governanceBusy" @click="runGovernance('set_channel')">切换通道</button>
          <button class="danger" :disabled="governanceBusy" @click="runGovernance('rollback')">回滚稳定版</button>
          <button class="secondary" :disabled="governanceBusy" @click="runGovernance('pin_stable')">固定稳定版</button>
          <button class="secondary" :disabled="governanceBusy" @click="runGovernance('export_contract')">下载治理快照</button>
        </div>
      </section>

      <details
        v-if="pageSectionEnabled('details_resolve_errors', true) && pageSectionTagIs('details_resolve_errors', 'details')"
        :style="pageSectionStyle('details_resolve_errors')"
        :open="pageSectionOpenDefault('details_resolve_errors', true)"
      >
        <summary>配置解析问题（{{ health.details?.resolve_errors?.length || 0 }}）</summary>
        <ul v-if="health.details?.resolve_errors?.length" class="diagnostic-list">
          <li v-for="item in health.details.resolve_errors" :key="diagnosticItemKey(item)">
            <strong>{{ diagnosticItemTitle(item) }}</strong>
            <span>{{ diagnosticItemMeta(item) }}</span>
          </li>
        </ul>
        <p v-else class="empty-text">暂无配置解析问题</p>
      </details>
      <details
        v-if="pageSectionEnabled('details_drift', true) && pageSectionTagIs('details_drift', 'details')"
        :style="pageSectionStyle('details_drift')"
        :open="pageSectionOpenDefault('details_drift', false)"
      >
        <summary>配置漂移（{{ health.details?.drift?.length || 0 }}）</summary>
        <ul v-if="health.details?.drift?.length" class="diagnostic-list">
          <li v-for="item in health.details.drift" :key="diagnosticItemKey(item)">
            <strong>{{ diagnosticItemTitle(item) }}</strong>
            <span>{{ diagnosticItemMeta(item) }}</span>
          </li>
        </ul>
        <p v-else class="empty-text">暂无配置漂移</p>
      </details>
      <details
        v-if="pageSectionEnabled('details_debt', true) && pageSectionTagIs('details_debt', 'details')"
        :style="pageSectionStyle('details_debt')"
        :open="pageSectionOpenDefault('details_debt', false)"
      >
        <summary>治理事项（{{ health.details?.debt?.length || 0 }}）</summary>
        <ul v-if="health.details?.debt?.length" class="diagnostic-list">
          <li v-for="item in health.details.debt" :key="diagnosticItemKey(item)">
            <strong>{{ diagnosticItemTitle(item) }}</strong>
            <span>{{ diagnosticItemMeta(item) }}</span>
          </li>
        </ul>
        <p v-else class="empty-text">暂无治理事项</p>
      </details>
    </div>
    <ProductConfirmDialog
      :open="rollbackConfirm.state.open"
      :title="rollbackConfirm.state.title"
      :message="rollbackConfirm.state.message"
      :confirm-label="rollbackConfirm.state.confirmLabel"
      :cancel-label="rollbackConfirm.state.cancelLabel"
      :tone="rollbackConfirm.state.tone"
      @confirm="rollbackConfirm.confirm"
      @cancel="rollbackConfirm.cancel"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import ProductConfirmDialog from '../components/ProductConfirmDialog.vue';
import StatusPanel from '../components/StatusPanel.vue';
import { intentRequest } from '../api/intents';
import { buildStatusError, resolveErrorCopy, type StatusError } from '../composables/useStatus';
import { useProductConfirmDialog } from '../composables/useProductConfirmDialog';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import {
  fetchSceneHealth,
  governanceExportContract,
  governancePinStable,
  governanceRollback,
  governanceSetChannel,
} from '../api/scene';
import type { SceneChannel, SceneDiagnosticsItem, SceneHealthContract } from '../contracts/scene';
import { useSessionStore } from '../stores/session';

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
const rollbackConfirm = useProductConfirmDialog();
const router = useRouter();
const session = useSessionStore();
const pageContract = usePageContract('scene_health');
const pageText = pageContract.text;
const pageActionText = pageContract.actionText;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionOpenDefault = pageContract.sectionOpenDefault;
const pageSectionTagIs = pageContract.sectionTagIs;
const errorCopy = computed(() => resolveErrorCopy(statusError.value, errorText.value || pageText('error_fallback', '场景健康状态加载失败')));
const headerActions = computed(() => {
  if (pageGlobalActions.value.length) return pageGlobalActions.value;
  return [{ key: 'refresh_page', label: pageActionText('refresh_page', '刷新'), intent: 'api.data' }];
});

const autoDegradeLabel = computed(() => {
  const value = health.value?.auto_degrade;
  if (!value) return '未触发';
  const reasonCount = Array.isArray(value.reason_codes) ? value.reason_codes.filter(Boolean).length : 0;
  return `${Boolean(value.triggered) ? '已触发' : '未触发'}；处理动作：${degradeActionLabel(value.action_taken)}；治理项：${reasonCount}`;
});

const healthSchemaVersionLabel = computed(() => {
  const value = String(health.value?.schema_version || '').trim();
  if (!value) return '未返回';
  if (value === 'scene_health_v1') return '标准版';
  return value.replace(/[_-]+/g, ' ');
});

function sceneChannelLabel(value: unknown): string {
  const channel = String(value || '');
  if (channel === 'stable') return '稳定版';
  if (channel === 'beta') return '灰度版';
  if (channel === 'dev') return '开发版';
  return channel || '-';
}

function runtimeSourceLabel(value: unknown): string {
  const source = String(value || '').trim().toLowerCase();
  if (!source) return '未返回';
  if (source === 'governed') return '治理结果';
  if (source === 'stable') return '稳定版';
  if (source === 'rollback') return '回滚稳定版';
  if (source === 'contract') return '已发布配置';
  if (source === 'fallback') return '系统补充配置';
  if (source === 'legacy') return '历史数据适配';
  if (source === 'dev') return '开发配置';
  return source.replace(/[_-]+/g, ' ');
}

function degradeActionLabel(value: unknown): string {
  const action = String(value || '').trim().toLowerCase();
  const mapping: Record<string, string> = {
    none: '无',
    notify: '已提醒',
    switch_channel: '已切换通道',
    rollback: '已回滚稳定版',
    pin_stable: '已固定稳定版',
  };
  if (!action) return '无';
  return mapping[action] || action.replace(/[_-]+/g, ' ');
}

const governanceSnapshot = computed(() => {
  const value = session.sceneGovernanceV1;
  return value && typeof value === 'object' ? value : null;
});

const governanceGatesLabel = computed(() => {
  const gates = governanceSnapshot.value?.gates;
  if (!gates || typeof gates !== 'object') return '-';
  const row = gates as Record<string, unknown>;
  return [
    `编排：${Boolean(row.orchestrator_applied) ? '已应用' : '未应用'}`,
    `治理：${Boolean(row.governance_applied) ? '已应用' : '未应用'}`,
    `交付策略：${Boolean(row.delivery_policy_applied) ? '已应用' : '未应用'}`,
    `导航策略：${Boolean(row.nav_policy_validation_ok) ? '通过' : '未通过'}`,
    `自动降级：${Boolean(row.auto_degrade_triggered) ? '已触发' : '未触发'}`,
  ].join('；');
});

const governanceReasonsLabel = computed(() => {
  const reasons = governanceSnapshot.value?.reasons;
  if (!reasons || typeof reasons !== 'object') return '-';
  const row = reasons as Record<string, unknown>;
  const autoCodes = Array.isArray(row.auto_degrade_reason_codes)
    ? row.auto_degrade_reason_codes.map((item) => String(item || '')).filter(Boolean)
    : [];
  const resolveCodes = Array.isArray(row.resolve_error_codes)
    ? row.resolve_error_codes.map((item) => String(item || '')).filter(Boolean)
    : [];
  return `自动调整：${autoCodes.length}；解析异常：${resolveCodes.length}`;
});

const governanceConsumptionLabel = computed(() => {
  const consumption = governanceSnapshot.value?.scene_ready_consumption;
  if (!consumption || typeof consumption !== 'object') return '-';
  const row = consumption as Record<string, unknown>;
  const enabled = Boolean(row.enabled);
  const sceneTypes = Number(row.scene_type_count || 0);
  const scenes = Number(row.scene_count || 0);
  const aggregate = (row.aggregate && typeof row.aggregate === 'object')
    ? (row.aggregate as Record<string, unknown>)
    : {};
  const baseRate = (aggregate.base_fact_consumption_rate && typeof aggregate.base_fact_consumption_rate === 'object')
    ? (aggregate.base_fact_consumption_rate as Record<string, unknown>)
    : {};
  const surfaceRate = (aggregate.surface_nonempty_rate && typeof aggregate.surface_nonempty_rate === 'object')
    ? (aggregate.surface_nonempty_rate as Record<string, unknown>)
    : {};
  const baseSearch = Number(baseRate.search || 0).toFixed(2);
  const surfaceAction = Number(surfaceRate.action_surface || 0).toFixed(2);
  return `启用：${enabled ? '是' : '否'}；场景类型：${sceneTypes}；场景：${scenes}；基础检索：${baseSearch}；操作面：${surfaceAction}`;
});

function diagnosticItemKey(item: SceneDiagnosticsItem) {
  return [
    item.scene_key,
    item.code,
    item.severity,
    item.created_at,
    item.ts,
    item.message,
  ].map((part) => String(part || '')).join(':');
}

function diagnosticItemTitle(item: SceneDiagnosticsItem) {
  const scene = String(item.scene_key || '').trim();
  const message = String(item.message || '').trim();
  if (scene && message) return `${scene}：${message}`;
  return message || scene || '待确认事项';
}

function diagnosticItemMeta(item: SceneDiagnosticsItem) {
  const parts = [
    item.severity ? `级别：${item.severity}` : '',
    item.code ? `原因：${item.code}` : '',
    item.created_at || item.ts ? `时间：${item.created_at || item.ts}` : '',
  ].filter(Boolean);
  return parts.join('；') || '暂无更多说明';
}

function validateHealthContract(raw: unknown): SceneHealthContract {
  if (!raw || typeof raw !== 'object') throw new Error(pageText('error_health_payload_missing', '场景健康数据返回为空'));
  const value = raw as Record<string, unknown>;
  const requiredRoot = ['scene_channel', 'rollback_active', 'summary', 'details', 'trace_id'];
  for (const key of requiredRoot) {
    if (!(key in value)) {
      throw new Error(`${pageText('error_health_payload_incomplete', '场景健康数据不完整：')}${key}`);
    }
  }
  const summary = value.summary as Record<string, unknown>;
  if (
    typeof summary?.critical_resolve_errors_count !== 'number' ||
    typeof summary?.critical_drift_warn_count !== 'number'
  ) {
    throw new Error(pageText('error_health_summary_incomplete', '场景健康汇总数据不完整'));
  }
  if ('details' in value) {
    const details = value.details as Record<string, unknown>;
    if (!Array.isArray(details?.resolve_errors) || !Array.isArray(details?.drift) || !Array.isArray(details?.debt)) {
      throw new Error(pageText('error_health_details_incomplete', '场景健康明细数据不完整'));
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
    errorText.value = err instanceof Error ? err.message : pageText('error_fallback', '场景健康状态加载失败');
    statusError.value = buildStatusError(err, errorText.value);
    errorTraceId.value = statusError.value.traceId || '';
  } finally {
    loading.value = false;
  }
}

async function executeHeaderAction(actionKey: string) {
  const handled = await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    onRefresh: loadHealth,
    onFallback: async (key) => {
      if (key === 'refresh_page') {
        await loadHealth();
        return true;
      }
      return false;
    },
  });
  if (!handled && actionKey === 'refresh_page') {
    await loadHealth();
  }
}

async function runGovernance(action: 'set_channel' | 'rollback' | 'pin_stable' | 'export_contract') {
  const reason = governanceReason.value.trim();
  if (!reason) {
    errorText.value = pageText('error_reason_required', '请填写治理操作说明');
    statusError.value = { message: errorText.value };
    return;
  }
  governanceBusy.value = true;
  errorText.value = '';
  statusError.value = null;
  try {
    if (action === 'rollback') {
      const ok = await rollbackConfirm.open({
        title: pageText('confirm_rollback_title', '确认回滚稳定版'),
        message: pageText('confirm_rollback_message', '回滚后将固定到稳定版治理结果，请确认是否继续。'),
        confirmLabel: pageText('confirm_rollback_ok', '回滚'),
        cancelLabel: pageText('confirm_cancel', '取消'),
        tone: 'danger',
      });
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
    errorText.value = err instanceof Error ? err.message : pageText('error_governance_failed', '治理操作失败');
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
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-panel);
  border: 1px solid var(--sc-app-border);
}

.header h2 {
  margin: 0;
}

.header p {
  margin: 4px 0 0;
  color: var(--sc-semantic-text-muted);
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
  color: var(--sc-app-text-secondary);
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
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
}

.pill.warn {
  background: var(--sc-app-danger-bg);
  color: var(--sc-app-danger-text);
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.card {
  border-radius: var(--sc-component-panel-radius);
  padding: 16px;
  background: var(--sc-app-panel);
  border: 1px solid var(--sc-app-border);
}

.card.danger {
  border-color: var(--sc-app-danger-border);
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
  background: var(--sc-app-panel);
  border-radius: var(--sc-component-panel-radius);
  border: 1px solid var(--sc-app-border);
  padding: 12px 14px;
}

.meta p {
  margin: 4px 0;
}

.governance {
  background: var(--sc-app-panel);
  border-radius: var(--sc-component-panel-radius);
  border: 1px solid var(--sc-app-border);
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
  color: var(--sc-app-text-secondary);
}

.governance-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.danger {
  border: 1px solid var(--sc-app-danger-border);
  background: var(--sc-app-danger-bg);
  color: var(--sc-app-danger-text);
  border-radius: var(--sc-component-button-radius);
  padding: 8px 10px;
  cursor: pointer;
}

details {
  background: var(--sc-app-panel);
  border-radius: var(--sc-component-panel-radius);
  border: 1px solid var(--sc-app-border);
  padding: 10px 12px;
}

summary {
  cursor: pointer;
  font-weight: 600;
}

.diagnostic-list {
  display: grid;
  gap: 8px;
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
}

.diagnostic-list li {
  display: grid;
  gap: 4px;
  padding: 10px;
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-muted-bg);
  border: 1px solid var(--sc-app-border);
}

.diagnostic-list span,
.empty-text {
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.empty-text {
  margin: 10px 0 0;
}

.secondary {
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  border-radius: var(--sc-component-button-radius);
  padding: 8px 10px;
  cursor: pointer;
}
</style>
