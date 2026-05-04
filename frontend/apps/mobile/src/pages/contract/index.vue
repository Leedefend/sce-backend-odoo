<template>
  <view class="page">
    <view class="header">
      <view>
        <view class="kicker">契约运行页</view>
        <view class="title">{{ pageTitle }}</view>
        <view class="subtitle">{{ modelName }} · {{ viewTypeLabel }}</view>
      </view>
      <button class="header__action" :disabled="loading" @click="loadContract">刷新</button>
    </view>

    <view class="summary">
      <view class="summary__item">
        <text class="summary__label">契约版本</text>
        <text class="summary__value">{{ contractVersion || '-' }}</text>
      </view>
      <view class="summary__item">
        <text class="summary__label">终端类型</text>
        <text class="summary__value">{{ clientType || '-' }}</text>
      </view>
      <view class="summary__item">
        <text class="summary__label">布局模式</text>
        <text class="summary__value">{{ adaptMode || '-' }}</text>
      </view>
    </view>

    <view v-if="loading" class="state">正在读取契约...</view>
    <view v-else-if="error" class="state state--error">
      <text>{{ error }}</text>
    </view>
    <view v-else class="section">
      <view class="section__head">
        <view class="section__title">字段组件</view>
        <view class="section__count">{{ widgets.length }} 项</view>
      </view>
      <view v-if="widgets.length" class="field-list">
        <view v-for="widget in widgets" :key="widget.widgetId" class="field-row">
          <view class="field-row__main">
            <text class="field-row__label">{{ widget.label }}</text>
            <text class="field-row__code">{{ widget.fieldCode }}</text>
          </view>
          <view class="field-row__meta">{{ widget.componentKey || widget.widgetType }}</view>
        </view>
      </view>
      <view v-else class="empty">当前契约未返回可渲染字段</view>
    </view>

    <view v-if="actions.length" class="section">
      <view class="section__head">
        <view class="section__title">可用动作</view>
        <view class="section__count">{{ actions.length }} 项</view>
      </view>
      <view class="action-list">
        <button v-for="action in actions" :key="action.actionId" class="action" @click="selectAction(action.actionId)">
          {{ action.actionId }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';

type Dict = Record<string, unknown>;

interface ContractWidget {
  widgetId: string;
  widgetType: string;
  fieldCode: string;
  label: string;
  componentKey: string;
}

interface ContractAction {
  actionId: string;
}

const TARGET_MODEL = 'construction.contract';
const TARGET_VIEW_TYPE = 'tree';
const CLIENT_TYPE = 'harmony_h5';

const loading = ref(false);
const error = ref('');
const contract = ref<Dict | null>(null);
const routeQuery = ref<Dict>({});

const pageInfo = computed(() => asDict(contract.value?.pageInfo));
const layoutContract = computed(() => asDict(contract.value?.layoutContract));
const actionContract = computed(() => asDict(contract.value?.actionContract));
const pageTitle = computed(() => asText(pageInfo.value.pageName, '契约运行'));
const modelName = computed(() => asText(pageInfo.value.model, TARGET_MODEL));
const viewTypeLabel = computed(() => asText(pageInfo.value.viewType, 'list'));
const contractVersion = computed(() => asText(pageInfo.value.contractVersion));
const clientType = computed(() => asText(pageInfo.value.clientType, CLIENT_TYPE));
const adaptMode = computed(() => asText(layoutContract.value.adaptMode));
const widgets = computed(() => collectWidgets(layoutContract.value));
const actions = computed(() => collectActions(actionContract.value));

function readStorage(key: string): string {
  try {
    return String(uni.getStorageSync(key) || '').trim();
  } catch {
    return '';
  }
}

function asDict(value: unknown): Dict {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Dict : {};
}

function asList(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asText(value: unknown, fallback = ''): string {
  const text = String(value || '').trim();
  return text || fallback;
}

function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '');
}

function normalizeError(err: unknown): string {
  if (err instanceof Error && err.message) {
    const message = err.message.toLowerCase();
    if (message.includes('401') || message.includes('403') || message.includes('token')) {
      return '登录已失效，请重新登录';
    }
    if (message.includes('network') || message.includes('request') || message.includes('timeout')) {
      return '服务暂不可用，请检查服务地址';
    }
  }
  return '契约读取失败';
}

function requestIntent(endpoint: string, token: string, payload: Dict): Promise<Dict> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: endpoint,
      method: 'POST',
      data: payload,
      timeout: 15000,
      header: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        'X-SC-Client-Type': CLIENT_TYPE,
      },
      success: (response) => {
        const statusCode = Number(response.statusCode || 0);
        const body = asDict(response.data);
        if (statusCode < 200 || statusCode >= 300) {
          reject(new Error(`request failed: ${statusCode}`));
          return;
        }
        if (body.ok === false) {
          const bodyError = asDict(body.error);
          reject(new Error(asText(bodyError.message || body.error, 'intent failed')));
          return;
        }
        resolve(body);
      },
      fail: (requestError) => reject(new Error(requestError.errMsg || 'request failed')),
    });
  });
}

async function loadContract() {
  const baseUrl = normalizeBaseUrl(readStorage('sc_mobile_base_url'));
  const dbName = readStorage('sc_mobile_db');
  const token = readStorage('sc_mobile_token');
  if (!baseUrl || !dbName || !token) {
    uni.reLaunch({ url: '/pages/login/index' });
    return;
  }

  loading.value = true;
  error.value = '';
  try {
    const endpoint = `${baseUrl}/api/v1/intent?db=${encodeURIComponent(dbName)}`;
    const targetParams = buildTargetParams();
    const response = await requestIntent(endpoint, token, {
      intent: 'ui.contract.v2',
      params: {
        client_type: CLIENT_TYPE,
        delivery_profile: 'mobile_compact',
        ...targetParams,
        limit: 20,
      },
    });
    contract.value = asDict(response.data);
  } catch (err) {
    error.value = normalizeError(err);
    contract.value = null;
  } finally {
    loading.value = false;
  }
}

function buildTargetParams(): Dict {
  const query = routeQuery.value;
  const menuId = asText(query.menu_id || query.menuId || query.id);
  if (menuId) {
    return { op: 'menu', menu_id: menuId };
  }
  const actionId = asText(query.action_id || query.actionId);
  if (actionId) {
    return { op: 'action_open', action_id: actionId, view_type: asText(query.view_type || query.viewType, TARGET_VIEW_TYPE) };
  }
  const model = asText(query.model);
  if (model) {
    return { op: 'model', model, view_type: asText(query.view_type || query.viewType, TARGET_VIEW_TYPE) };
  }
  const sceneKey = asText(query.scene_key || query.sceneKey);
  if (sceneKey) {
    return { source_type: 'scene_contract_v1', scene_key: sceneKey };
  }
  return { source_type: 'ui.contract', op: 'model', model: TARGET_MODEL, view_type: TARGET_VIEW_TYPE };
}

function collectWidgets(layout: Dict): ContractWidget[] {
  const rows: ContractWidget[] = [];
  function walkContainers(containers: unknown[]) {
    containers.forEach((container) => {
      const row = asDict(container);
      asList(row.widgetList).forEach((item) => {
        const widget = asDict(item);
        const widgetId = asText(widget.widgetId);
        if (!widgetId) return;
        rows.push({
          widgetId,
          widgetType: asText(widget.widgetType),
          fieldCode: asText(widget.fieldCode),
          label: asText(widget.label, asText(widget.fieldCode, widgetId)),
          componentKey: asText(widget.componentKey),
        });
      });
      walkContainers(asList(row.children));
    });
  }
  walkContainers(asList(layout.containerTree));
  return rows;
}

function collectActions(action: Dict): ContractAction[] {
  return asList(action.actionRuleList)
    .map((item) => ({ actionId: asText(asDict(item).actionId) }))
    .filter((item) => item.actionId);
}

function selectAction(actionId: string) {
  uni.showToast({ title: actionId, icon: 'none' });
}

onLoad((query) => {
  routeQuery.value = asDict(query);
});

onShow(loadContract);
</script>

<style scoped>
.page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 34rpx 28rpx 44rpx;
  background: #f4f6f8;
  color: #17202a;
}

.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.kicker {
  color: #5d7188;
  font-size: 23rpx;
  font-weight: 600;
}

.title {
  margin-top: 8rpx;
  color: #17202a;
  font-size: 36rpx;
  font-weight: 700;
  line-height: 1.25;
}

.subtitle {
  margin-top: 8rpx;
  color: #607083;
  font-size: 23rpx;
  line-height: 1.35;
}

.header__action {
  width: 108rpx;
  height: 56rpx;
  margin: 0;
  border-radius: 8rpx;
  background: #ffffff;
  color: #344154;
  font-size: 23rpx;
  line-height: 56rpx;
}

.summary,
.section,
.state {
  border: 1rpx solid #dfe5ec;
  border-radius: 8rpx;
  background: #ffffff;
}

.summary {
  display: flex;
  margin-bottom: 22rpx;
}

.summary__item {
  flex: 1;
  min-width: 0;
  padding: 18rpx 14rpx;
  border-right: 1rpx solid #edf1f5;
}

.summary__item:last-child {
  border-right: 0;
}

.summary__label {
  display: block;
  color: #667789;
  font-size: 21rpx;
  line-height: 1.25;
}

.summary__value {
  display: block;
  margin-top: 8rpx;
  color: #17202a;
  font-size: 24rpx;
  font-weight: 600;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.state {
  padding: 26rpx 24rpx;
  color: #607083;
  font-size: 25rpx;
}

.state--error {
  color: #9f2f2f;
}

.section {
  margin-top: 22rpx;
  padding: 22rpx;
}

.section__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.section__title {
  color: #344154;
  font-size: 26rpx;
  font-weight: 700;
}

.section__count {
  color: #667789;
  font-size: 22rpx;
}

.field-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.field-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  padding: 18rpx 16rpx;
  border: 1rpx solid #e6ebf1;
  border-radius: 8rpx;
  background: #fbfcfd;
}

.field-row__main {
  min-width: 0;
}

.field-row__label,
.field-row__code {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field-row__label {
  color: #17202a;
  font-size: 26rpx;
  font-weight: 600;
  line-height: 1.25;
}

.field-row__code {
  margin-top: 6rpx;
  color: #667789;
  font-size: 21rpx;
  line-height: 1.25;
}

.field-row__meta {
  flex: 0 0 auto;
  max-width: 220rpx;
  color: #3d6f6a;
  font-size: 21rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty {
  color: #667789;
  font-size: 24rpx;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.action {
  height: 68rpx;
  border-radius: 8rpx;
  background: #1f3a5f;
  color: #ffffff;
  font-size: 23rpx;
  line-height: 68rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
