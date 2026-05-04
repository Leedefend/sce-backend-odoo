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
    <view v-else-if="isListSurface" class="section">
      <view class="section__head">
        <view class="section__title">业务数据</view>
        <view class="section__count">{{ recordCountLabel }}</view>
      </view>
      <view v-if="dataLoading" class="empty">正在读取业务数据...</view>
      <view v-else-if="dataError" class="empty empty--error">{{ dataError }}</view>
      <view v-else-if="records.length" class="record-list">
        <view v-for="record in records" :key="recordKey(record)" class="record-card" @click="openRecord(record)">
          <view v-for="field in displayFields" :key="field.fieldCode" class="record-row">
            <text class="record-row__label">{{ field.label }}</text>
            <text class="record-row__value">{{ formatFieldValue(field, record[field.fieldCode]) }}</text>
          </view>
        </view>
        <button v-if="canLoadMore" class="load-more" :disabled="dataLoading" @click="loadMoreRecords">
          {{ dataLoading ? '加载中...' : '加载更多' }}
        </button>
      </view>
      <view v-else class="empty">当前没有可显示的数据</view>
    </view>

    <view v-else-if="recordRows.length" class="section">
      <view class="section__head">
        <view class="section__title">业务记录</view>
        <view class="section__count">{{ recordRows.length }} 项</view>
      </view>
      <view class="field-list">
        <view v-for="row in recordRows" :key="row.fieldCode" class="field-row field-row--value">
          <view class="field-row__main">
            <text class="field-row__label">{{ row.label }}</text>
            <text class="field-row__code">{{ row.fieldCode }}</text>
          </view>
          <view class="field-row__value">{{ row.value }}</view>
        </view>
      </view>
    </view>

    <view v-else-if="sceneBlocks.length" class="section">
      <view class="section__head">
        <view class="section__title">页面内容</view>
        <view class="section__count">{{ sceneBlocks.length }} 项</view>
      </view>
      <view class="field-list">
        <view v-for="block in sceneBlocks" :key="block.widgetId" class="field-row">
          <view class="field-row__main">
            <text class="field-row__label">{{ block.label }}</text>
            <text class="field-row__code">{{ block.blockType || block.fieldCode }}</text>
          </view>
          <view class="field-row__meta">{{ block.componentKey || block.widgetType }}</view>
        </view>
      </view>
    </view>

    <view v-else class="section">
      <view class="section__head">
        <view class="section__title">字段组件</view>
        <view class="section__count">{{ widgets.length }} 项</view>
      </view>
      <view v-if="displayFields.length" class="field-list">
        <view v-for="widget in displayFields" :key="widget.widgetId" class="field-row">
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
        <button
          v-for="action in actions"
          :key="action.actionId"
          class="action"
          :class="{ 'action--disabled': action.disabled }"
          :disabled="action.disabled || Boolean(runningActionId)"
          @click="selectAction(action)"
        >
          {{ runningActionId === action.actionId ? '处理中...' : (action.label || action.actionId) }}
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
  dictKey: string;
  blockType: string;
  visible: boolean;
  readonly: boolean;
  required: boolean;
  disabled: boolean;
}

interface ContractAction {
  actionId: string;
  actionKey: string;
  label: string;
  intent: string;
  refreshMode: string;
  target: Dict;
  button: Dict;
  visible: boolean;
  disabled: boolean;
}

interface RecordRow {
  fieldCode: string;
  label: string;
  value: string;
}

const TARGET_MODEL = 'construction.contract';
const TARGET_VIEW_TYPE = 'tree';
const CLIENT_TYPE = 'harmony_h5';

const loading = ref(false);
const error = ref('');
const contract = ref<Dict | null>(null);
const routeQuery = ref<Dict>({});
const dataLoading = ref(false);
const dataError = ref('');
const records = ref<Dict[]>([]);
const recordTotal = ref<number | null>(null);
const nextOffset = ref(0);
const runningActionId = ref('');

const pageInfo = computed(() => asDict(contract.value?.pageInfo));
const layoutContract = computed(() => asDict(contract.value?.layoutContract));
const actionContract = computed(() => asDict(contract.value?.actionContract));
const statusContract = computed(() => asDict(contract.value?.statusContract));
const globalStatus = computed(() => collectGlobalStatus(statusContract.value));
const isPageReadable = computed(() => {
  const auth = asText(globalStatus.value.pageAuth).toLowerCase();
  return globalStatus.value.pageVisible !== false && auth !== 'none';
});
const isPageReadonly = computed(() => {
  const auth = asText(globalStatus.value.pageAuth).toLowerCase();
  return auth === 'read';
});
const pageTitle = computed(() => asText(pageInfo.value.pageName, '契约运行'));
const modelName = computed(() => asText(pageInfo.value.model, TARGET_MODEL));
const viewTypeLabel = computed(() => asText(pageInfo.value.viewType, 'list'));
const contractVersion = computed(() => asText(pageInfo.value.contractVersion));
const clientType = computed(() => asText(pageInfo.value.clientType, CLIENT_TYPE));
const adaptMode = computed(() => asText(layoutContract.value.adaptMode));
const widgets = computed(() => collectWidgets(layoutContract.value, statusContract.value));
const businessFields = computed(() => widgets.value.filter(isBusinessDisplayField));
const listDisplayFields = computed(() => businessFields.value.slice(0, 8));
const displayFields = computed(() => (isListSurface.value ? listDisplayFields.value : businessFields.value));
const sceneBlocks = computed(() => widgets.value.filter((item) => item.visible && item.widgetType === 'display' && item.fieldCode));
const actions = computed(() => collectActions(actionContract.value, statusContract.value));
const isListSurface = computed(() => ['list', 'tree', 'kanban', 'table'].includes(viewTypeLabel.value));
const recordRows = computed<RecordRow[]>(() => {
  if (isListSurface.value || !records.value.length) return [];
  const record = records.value[0];
  return displayFields.value.map((field) => ({
    fieldCode: field.fieldCode,
    label: field.label,
    value: formatFieldValue(field, record[field.fieldCode]),
  }));
});
const recordCountLabel = computed(() => {
  if (recordTotal.value !== null) return `${recordTotal.value} 条`;
  return `${records.value.length} 条`;
});
const canLoadMore = computed(() => {
  if (!isListSurface.value || dataLoading.value) return false;
  if (recordTotal.value === null) return records.value.length > 0 && nextOffset.value > records.value.length;
  return records.value.length < recordTotal.value;
});

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

function parseMaybeJsonRecord(value: unknown): Dict {
  if (!value) return {};
  if (value && typeof value === 'object' && !Array.isArray(value)) return value as Dict;
  if (typeof value !== 'string') return {};
  try {
    const parsed = JSON.parse(value.trim());
    return asDict(parsed);
  } catch {
    return {};
  }
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
    const nextContract = asDict(response.data);
    const nextGlobalStatus = collectGlobalStatus(asDict(nextContract.statusContract));
    if (nextGlobalStatus.pageVisible === false || asText(nextGlobalStatus.pageAuth).toLowerCase() === 'none') {
      contract.value = nextContract;
      records.value = [];
      recordTotal.value = null;
      nextOffset.value = 0;
      dataError.value = '';
      error.value = asText(nextGlobalStatus.reasonCode, '当前页面无访问权限');
      return;
    }
    contract.value = nextContract;
    await loadRecords(endpoint, token, nextContract, false);
  } catch (err) {
    error.value = normalizeError(err);
    contract.value = null;
    records.value = [];
    recordTotal.value = null;
  } finally {
    loading.value = false;
  }
}

async function loadRecords(endpoint: string, token: string, nextContract: Dict, append: boolean) {
  const info = asDict(nextContract.pageInfo);
  const model = asText(info.model);
  const viewType = asText(info.viewType);
  const source = resolvePrimaryDataSource(nextContract);
  const sourceParams = asDict(source.params);
  const sourceIntent = asText(source.intent || source.query, 'api.data');
  const sourceOp = asText(sourceParams.op, ['list', 'tree', 'kanban', 'table'].includes(viewType) ? 'list' : 'read');
  if (!model || !sourceIntent || (sourceOp === 'list' && !['list', 'tree', 'kanban', 'table'].includes(viewType))) {
    hydrateInlineRecords(nextContract);
    dataError.value = '';
    return;
  }
  const fields = asList(sourceParams.fields)
    .map((item) => asText(item))
    .filter((field, index, all) => field && all.indexOf(field) === index);
  if (!fields.length) fields.push('display_name');
  if (!fields.includes('id')) fields.unshift('id');
  dataLoading.value = true;
  dataError.value = '';
  try {
    const requestParams: Dict = {
      ...sourceParams,
      op: sourceOp,
      model,
      fields,
    };
    if (sourceOp === 'read') {
      requestParams.ids = normalizeIds(sourceParams.ids);
    } else {
      requestParams.limit = Number(sourceParams.limit) || 20;
      requestParams.offset = append ? nextOffset.value : 0;
      requestParams.need_total = true;
    }
    const response = await requestIntent(endpoint, token, {
      intent: sourceIntent,
      params: requestParams,
    });
    const data = asDict(response.data);
    const nextRecords = asList(data.records).map((item) => asDict(item));
    records.value = append ? records.value.concat(nextRecords) : nextRecords;
    if (sourceOp === 'read') {
      recordTotal.value = nextRecords.length;
      nextOffset.value = nextRecords.length;
    } else {
      const total = Number(data.total);
      recordTotal.value = Number.isFinite(total) ? total : null;
      const offset = Number(data.next_offset);
      nextOffset.value = Number.isFinite(offset) ? offset : records.value.length;
    }
  } catch (err) {
    if (!append) {
      records.value = [];
      recordTotal.value = null;
      nextOffset.value = 0;
    }
    dataError.value = normalizeError(err);
  } finally {
    dataLoading.value = false;
  }
}

async function loadMoreRecords() {
  const baseUrl = normalizeBaseUrl(readStorage('sc_mobile_base_url'));
  const dbName = readStorage('sc_mobile_db');
  const token = readStorage('sc_mobile_token');
  if (!baseUrl || !dbName || !token || !contract.value) return;
  const endpoint = `${baseUrl}/api/v1/intent?db=${encodeURIComponent(dbName)}`;
  await loadRecords(endpoint, token, contract.value, true);
}

function buildTargetParams(): Dict {
  const query = routeQuery.value;
  const menuId = asText(query.menu_id || query.menuId || query.id);
  if (menuId) {
    return { op: 'menu', menu_id: menuId, ...contractRouteParams(query) };
  }
  const actionId = asText(query.action_id || query.actionId);
  if (actionId) {
    return {
      op: 'action_open',
      action_id: actionId,
      view_type: asText(query.view_type || query.viewType, TARGET_VIEW_TYPE),
      ...contractRouteParams(query),
    };
  }
  const model = asText(query.model);
  if (model) {
    return { op: 'model', model, view_type: asText(query.view_type || query.viewType, TARGET_VIEW_TYPE), ...contractRouteParams(query) };
  }
  const sceneKey = asText(query.scene_key || query.sceneKey);
  if (sceneKey) {
    return { source_type: 'scene_contract_v1', scene_key: sceneKey };
  }
  return { source_type: 'ui.contract', op: 'model', model: TARGET_MODEL, view_type: TARGET_VIEW_TYPE };
}

function collectWidgets(layout: Dict, status: Dict): ContractWidget[] {
  const rows: ContractWidget[] = [];
  const widgetStatus = collectWidgetStatus(status);
  const containerStatus = collectContainerStatus(status);
  function walkContainers(containers: unknown[], inherited: Dict = {}) {
    containers.forEach((container) => {
      const row = asDict(container);
      const containerId = asText(row.containerId);
      const state = containerStatus[containerId] || {};
      const containerVisible = inherited.visible === false || state.visible === false ? false : state.visible;
      const containerDisabled = inherited.disabled === true || state.disabled === true ? true : state.disabled;
      const nextState: Dict = {
        visible: containerVisible,
        disabled: containerDisabled,
      };
      asList(row.widgetList).forEach((item) => {
        const widget = asDict(item);
        const widgetId = asText(widget.widgetId);
        if (!widgetId) return;
        const widgetState = widgetStatus[widgetId] || {};
        rows.push({
          widgetId,
          widgetType: asText(widget.widgetType),
          fieldCode: asText(widget.fieldCode),
          label: asText(widget.label, asText(widget.fieldCode, widgetId)),
          componentKey: asText(widget.componentKey),
          dictKey: asText(asDict(widget.componentConfig).dictKey),
          blockType: asText(asDict(widget.componentConfig).blockType),
          visible: widgetState.visible !== false && nextState.visible !== false,
          readonly: widgetState.readonly === true || nextState.disabled === true,
          required: widgetState.required === true,
          disabled: widgetState.disabled === true || nextState.disabled === true,
        });
      });
      walkContainers(asList(row.children), nextState);
    });
  }
  walkContainers(asList(layout.containerTree));
  return rows;
}

function collectContainerStatus(status: Dict): Record<string, Dict> {
  return asList(status.containerStatus).reduce<Record<string, Dict>>((acc, item) => {
    const row = asDict(item);
    const containerId = asText(row.containerId);
    if (containerId) acc[containerId] = row;
    return acc;
  }, {});
}

function collectWidgetStatus(status: Dict): Record<string, Dict> {
  return asList(status.widgetStatus).reduce<Record<string, Dict>>((acc, item) => {
    const row = asDict(item);
    const widgetId = asText(row.widgetId);
    if (widgetId) acc[widgetId] = row;
    return acc;
  }, {});
}

function collectGlobalStatus(status: Dict): Dict {
  return asDict(status.globalStatus);
}

function applyUnifiedPagePatchV2(patchRaw: unknown) {
  const patch = asDict(patchRaw);
  if (!patch.updateType) return;
  const layoutPatch = asDict(patch.layoutPatch);
  const runtimePatch = asDict(patch.runtimePatch);
  const dataPatch = asDict(patch.dataPatch);
  const mainData = asDict(dataPatch.mainData);
  if (Object.keys(mainData).length && records.value.length) {
    records.value = records.value.map((record, index) => (index === 0 ? { ...record, ...mainData } : record));
  }
  const tableRowsPatch = asDict(dataPatch.tableRows);
  const relationRowsPatch = asDict(dataPatch.relationRows);
  const treeDataPatch = asDict(dataPatch.treeData);
  const ganttDataPatch = asDict(dataPatch.ganttData);
  const dictDataPatch = asDict(dataPatch.dictData);
  const paginationPatch = asDict(dataPatch.pagination);
  const statusPatch = asDict(patch.statusPatch);
  const globalPatch = asDict(statusPatch.globalStatus);
  const containerPatchRows = asList(statusPatch.containerStatus).map((item) => asDict(item));
  const widgetPatchRows = asList(statusPatch.widgetStatus).map((item) => asDict(item));
  const buttonPatchRows = asList(statusPatch.buttonStatus).map((item) => asDict(item));
  const hasDataContractPatch = Boolean(
    Object.keys(mainData).length
    || Object.keys(tableRowsPatch).length
    || Object.keys(relationRowsPatch).length
    || Object.keys(treeDataPatch).length
    || Object.keys(ganttDataPatch).length
    || Object.keys(dictDataPatch).length
    || Object.keys(paginationPatch).length
  );
  const hasLayoutPatch = Object.keys(layoutPatch).length > 0;
  const hasRuntimePatch = Object.keys(runtimePatch).length > 0;
  if (!hasLayoutPatch && !hasRuntimePatch && !hasDataContractPatch && !Object.keys(globalPatch).length && !containerPatchRows.length && !widgetPatchRows.length && !buttonPatchRows.length) return;
  const current = asDict(contract.value);
  const currentLayout = asDict(current.layoutContract);
  const currentData = asDict(current.dataContract);
  const currentRuntime = asDict(current.runtimeContract);
  const currentStatus = asDict(current.statusContract);
  const nextLayout = hasLayoutPatch ? { ...currentLayout, ...layoutPatch } : currentLayout;
  const nextData = {
    ...currentData,
    mainData: { ...asDict(currentData.mainData), ...mainData },
    tableRows: { ...asDict(currentData.tableRows), ...tableRowsPatch },
    relationRows: { ...asDict(currentData.relationRows), ...relationRowsPatch },
    treeData: { ...asDict(currentData.treeData), ...treeDataPatch },
    ganttData: { ...asDict(currentData.ganttData), ...ganttDataPatch },
    dictData: { ...asDict(currentData.dictData), ...dictDataPatch },
    pagination: { ...asDict(currentData.pagination), ...paginationPatch },
  };
  const nextStatus = {
    ...currentStatus,
    globalStatus: Object.keys(globalPatch).length
      ? { ...asDict(currentStatus.globalStatus), ...globalPatch }
      : asDict(currentStatus.globalStatus),
    containerStatus: mergeStatusRows(asList(currentStatus.containerStatus), containerPatchRows, 'containerId'),
    widgetStatus: mergeStatusRows(asList(currentStatus.widgetStatus), widgetPatchRows, 'widgetId'),
    buttonStatus: mergeStatusRows(asList(currentStatus.buttonStatus), buttonPatchRows, 'btnId'),
  };
  const nextRuntime = hasRuntimePatch ? { ...currentRuntime, ...runtimePatch } : currentRuntime;
  contract.value = {
    ...current,
    layoutContract: nextLayout,
    dataContract: nextData,
    runtimeContract: nextRuntime,
    statusContract: nextStatus,
  };
}

function mergeStatusRows(baseRows: unknown[], patchRows: Dict[], keyName: string): Dict[] {
  const byKey = new Map<string, Dict>();
  baseRows.map((item) => asDict(item)).forEach((row) => {
    const key = asText(row[keyName]);
    if (key) byKey.set(key, row);
  });
  patchRows.forEach((row) => {
    const key = asText(row[keyName]);
    if (!key) return;
    byKey.set(key, { ...(byKey.get(key) || {}), ...row });
  });
  return Array.from(byKey.values());
}

function collectButtonStatus(status: Dict): Record<string, Dict> {
  return asList(status.buttonStatus).reduce<Record<string, Dict>>((acc, item) => {
    const row = asDict(item);
    const btnId = asText(row.btnId || row.buttonId || row.actionId);
    if (btnId) acc[btnId] = row;
    return acc;
  }, {});
}

function collectActions(action: Dict, status: Dict): ContractAction[] {
  const buttonStatus = collectButtonStatus(status);
  return asList(action.actionRuleList)
    .map((item) => {
      const row = asDict(item);
      const actionId = asText(row.actionId);
      const actionKey = asText(row.actionKey, actionId.replace(/^action\./, ''));
      const state = buttonStatus[`btn.${actionKey}`] || buttonStatus[actionId] || {};
      return {
        actionId,
        actionKey,
        label: asText(row.label, actionId),
        intent: asText(row.intent, 'ui.contract'),
        refreshMode: normalizeRefreshMode(row.refreshMode),
        target: asDict(row.target),
        button: asDict(row.button),
        visible: state.visible !== false,
        disabled: state.disabled === true || isPageReadonly.value || !isPageReadable.value,
      };
    })
    .filter((item) => item.actionId && item.visible);
}

function resolvePrimaryDataSource(nextContract: Dict): Dict {
  const dataContract = asDict(nextContract.dataContract);
  const dataSources = asDict(dataContract.dataSource);
  const primary = asDict(dataSources.primary);
  if (primary.intent || primary.query) return primary;
  if (hasInlineData(dataContract)) return {};
  return buildFallbackDataSource(nextContract);
}

function hasInlineData(dataContract: Dict): boolean {
  return Boolean(Object.keys(asDict(dataContract.mainData)).length || firstInlineRows(dataContract).length);
}

function hasInlineRows(dataContract: Dict): boolean {
  return Boolean(firstInlineRows(dataContract).length);
}

function firstInlineRows(dataContract: Dict): Dict[] {
  const tableRows = firstRecordList(asDict(dataContract.tableRows));
  if (tableRows.length) return tableRows;
  const treeRows = firstRecordList(asDict(dataContract.treeData));
  if (treeRows.length) return treeRows;
  return [];
}

function firstRecordList(rowsByKey: Dict): Dict[] {
  for (const value of Object.values(rowsByKey)) {
    const rows = asList(value).map((item) => asDict(item)).filter((item) => Object.keys(item).length);
    if (rows.length) return rows;
  }
  return [];
}

function hydrateInlineRecords(nextContract: Dict) {
  const dataContract = asDict(nextContract.dataContract);
  const mainData = asDict(dataContract.mainData);
  const inlineRows = firstInlineRows(dataContract);
  const inlineRecords = inlineRows.length ? inlineRows : (Object.keys(mainData).length ? [mainData] : []);
  records.value = inlineRecords;
  const pagination = asDict(dataContract.pagination);
  const firstPagination = Object.values(pagination).map((item) => asDict(item)).find((item) => Object.keys(item).length) || {};
  const total = Number(firstPagination.total);
  recordTotal.value = Number.isFinite(total) ? total : inlineRecords.length;
  nextOffset.value = inlineRecords.length;
}

function buildFallbackDataSource(nextContract: Dict): Dict {
  const info = asDict(nextContract.pageInfo);
  const model = asText(info.model);
  const viewType = asText(info.viewType);
  const recordId = asText(routeQuery.value.record_id || routeQuery.value.recordId || routeQuery.value.res_id || routeQuery.value.resId);
  const fields = collectWidgets(asDict(nextContract.layoutContract), asDict(nextContract.statusContract))
    .filter(isBusinessDisplayField)
    .map((item) => item.fieldCode)
    .filter((field, index, all) => field && all.indexOf(field) === index)
    .slice(0, 12);
  return {
    intent: 'api.data',
    params: {
      op: recordId && viewType === 'form' ? 'read' : 'list',
      model,
      ...(recordId && viewType === 'form' ? { ids: [Number(recordId)] } : {}),
      fields,
      limit: 20,
      offset: 0,
      need_total: true,
    },
  };
}

function contractRouteParams(query: Dict): Dict {
  const params: Dict = {};
  const recordId = Number(asText(query.record_id || query.recordId || query.res_id || query.resId));
  if (Number.isFinite(recordId) && recordId > 0) params.record_id = recordId;
  const domainRaw = asText(query.domain_raw || query.domainRaw);
  if (domainRaw) params.domain_raw = domainRaw;
  const contextRaw = asText(query.context_raw || query.contextRaw);
  if (contextRaw) params.context_raw = contextRaw;
  return params;
}

function normalizeIds(value: unknown): number[] {
  return asList(value)
    .map((item) => Number(item))
    .filter((item) => Number.isFinite(item) && item > 0);
}

function isBusinessDisplayField(widget: ContractWidget): boolean {
  if (!widget.visible) return false;
  const field = widget.fieldCode;
  if (widget.widgetType === 'display') return false;
  if (!field || field === 'id' || field.startsWith('__')) return false;
  const technicalPrefixes = [
    'access_',
    'activity_',
    'message_',
    'website_',
  ];
  if (technicalPrefixes.some((prefix) => field.startsWith(prefix))) return false;
  const technicalFields = new Set([
    'active',
    'create_date',
    'create_uid',
    'display_name',
    'write_date',
    'write_uid',
  ]);
  return !technicalFields.has(field);
}

async function selectAction(action: ContractAction) {
  if (runningActionId.value) return;
  const runtime = resolveRuntimeEndpoint();
  if (action.intent === 'api.data') {
    if (runtime) await applyActionRefreshMode(action.refreshMode, runtime.endpoint, runtime.token);
    return;
  }
  if (action.intent === 'ui.contract') {
    openContractTarget(action.target);
    return;
  }
  if (action.intent !== 'execute_button') {
    uni.showToast({ title: action.label || action.actionId, icon: 'none' });
    return;
  }
  const baseUrl = normalizeBaseUrl(readStorage('sc_mobile_base_url'));
  const dbName = readStorage('sc_mobile_db');
  const token = readStorage('sc_mobile_token');
  const model = actionTargetModel(action);
  const resId = currentRecordId();
  const buttonName = asText(action.button.name, action.actionKey);
  const context = actionExecutionContext(action);
  if (!baseUrl || !dbName || !token || !model || !resId || !buttonName) {
    uni.showToast({ title: '当前动作缺少执行参数', icon: 'none' });
    return;
  }
  runningActionId.value = action.actionId;
  try {
    const endpoint = `${baseUrl}/api/v1/intent?db=${encodeURIComponent(dbName)}`;
    const response = await requestIntent(endpoint, token, {
      intent: 'execute_button',
      params: {
        model,
        res_id: resId,
        button: {
          name: buttonName,
          type: asText(action.button.type, 'object'),
          server_action_id: action.button.server_action_id,
          xml_id: action.button.xml_id,
        },
        context,
      },
    });
    await applyActionEffect(asDict(asDict(response.data).effect), action, endpoint, token);
  } catch {
    uni.showToast({ title: '动作执行失败', icon: 'none' });
  } finally {
    runningActionId.value = '';
  }
}

function actionTargetModel(action: ContractAction): string {
  const target = action.target;
  return asText(target.model || target.res_model || target.resModel || target.target_model || target.targetModel, modelName.value);
}

function actionExecutionContext(action: ContractAction): Dict {
  const target = action.target;
  const context = {
    ...parseMaybeJsonRecord(target.context || target.contextRaw || target.context_raw),
    ...parseMaybeJsonRecord(action.button.context || action.button.contextRaw || action.button.context_raw),
  };
  const contextRaw = asText(target.context_raw || target.contextRaw || action.button.context_raw || action.button.contextRaw);
  if (contextRaw) context.context_raw = contextRaw;
  return context;
}

function normalizeRefreshMode(value: unknown): string {
  const mode = asText(value, 'partial').toLowerCase();
  return ['none', 'partial', 'full'].includes(mode) ? mode : 'partial';
}

function resolveRuntimeEndpoint(): { endpoint: string; token: string } | null {
  const baseUrl = normalizeBaseUrl(readStorage('sc_mobile_base_url'));
  const dbName = readStorage('sc_mobile_db');
  const token = readStorage('sc_mobile_token');
  if (!baseUrl || !dbName || !token) return null;
  return {
    endpoint: `${baseUrl}/api/v1/intent?db=${encodeURIComponent(dbName)}`,
    token,
  };
}

function currentRecordId(): number {
  const fromRoute = Number(asText(routeQuery.value.record_id || routeQuery.value.recordId || routeQuery.value.res_id || routeQuery.value.resId));
  if (Number.isFinite(fromRoute) && fromRoute > 0) return fromRoute;
  if (isListSurface.value) return 0;
  const fromRecord = Number(asText(records.value[0]?.id));
  return Number.isFinite(fromRecord) && fromRecord > 0 ? fromRecord : 0;
}

async function applyActionEffect(effect: Dict, action: ContractAction, endpoint: string, token: string) {
  const type = asText(effect.type);
  const target = asDict(effect.target);
  if (type === 'navigate') {
    const kind = asText(target.kind);
    if (kind === 'action') {
      const actionId = asText(target.action_id || target.actionId);
      if (actionId) {
        openContractTarget({ action_id: actionId });
        return;
      }
    }
    if (kind === 'record') {
      const model = asText(target.model);
      const recordId = asText(target.id || target.res_id || target.record_id);
      if (model && recordId) {
        openContractTarget({ model, view_type: 'form', record_id: recordId });
        return;
      }
    }
  }
  await applyActionRefreshMode(action.refreshMode, endpoint, token);
}

async function applyActionRefreshMode(refreshMode: string, endpoint: string, token: string) {
  const mode = normalizeRefreshMode(refreshMode);
  if (mode === 'none') return;
  if (mode === 'full' || !contract.value) {
    await loadContract();
    return;
  }
  await loadRecords(endpoint, token, contract.value, false);
}

function openContractTarget(target: Dict) {
  const query: string[] = [];
  const actionId = asText(target.action_id || target.actionId);
  if (actionId) query.push(`action_id=${encodeURIComponent(actionId)}`);
  const model = asText(target.model || target.res_model || target.resModel || target.target_model || target.targetModel);
  if (model) query.push(`model=${encodeURIComponent(model)}`);
  const viewMode = asText(target.view_mode || target.viewMode);
  const viewType = asText(target.view_type || target.viewType, viewMode.split(',').map((item) => item.trim()).find(Boolean) || '');
  if (viewType) query.push(`view_type=${encodeURIComponent(viewType)}`);
  const recordId = asText(target.record_id || target.recordId || target.res_id || target.resId || target.id);
  if (recordId) query.push(`record_id=${encodeURIComponent(recordId)}`);
  const sceneKey = asText(target.scene_key || target.sceneKey);
  if (sceneKey) query.push(`scene_key=${encodeURIComponent(sceneKey)}`);
  const domainRaw = asText(target.domain_raw || target.domainRaw);
  if (domainRaw) query.push(`domain_raw=${encodeURIComponent(domainRaw)}`);
  const contextRaw = asText(target.context_raw || target.contextRaw);
  if (contextRaw) query.push(`context_raw=${encodeURIComponent(contextRaw)}`);
  if (!query.length) {
    void loadContract();
    return;
  }
  uni.navigateTo({ url: `/pages/contract/index?${query.join('&')}` });
}

function openRecord(record: Dict) {
  if (!isListSurface.value) return;
  const recordId = asText(record.id);
  const model = modelName.value;
  if (!recordId || !model) return;
  openContractTarget({ model, view_type: 'form', record_id: recordId });
}

function recordKey(record: Dict): string {
  return asText(record.id, JSON.stringify(record));
}

function formatFieldValue(field: ContractWidget, value: unknown): string {
  const dictLabel = resolveDictLabel(field, value);
  return dictLabel || formatValue(value);
}

function resolveDictLabel(field: ContractWidget, value: unknown): string {
  const dictData = asDict(asDict(contract.value?.dataContract).dictData);
  const dictKey = asText(field.dictKey, field.fieldCode);
  const rows = asList(dictData[dictKey]);
  const rawValue = Array.isArray(value) ? value[0] : value;
  const rawText = asText(rawValue);
  if (!rawText) return '';
  for (const item of rows) {
    const row = asDict(item);
    const optionValue = asText(row.value || row.key || row.id);
    if (optionValue === rawText) return asText(row.label || row.name || row.display_name);
  }
  return '';
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) {
    if (value.length >= 2) return asText(value[1], asText(value[0], '-'));
    return value.map((item) => asText(item)).filter(Boolean).join(', ') || '-';
  }
  if (value && typeof value === 'object') {
    const row = asDict(value);
    return asText(row.display_name || row.name || row.label || row.value, '-');
  }
  if (value === false || value === null || value === undefined || value === '') return '-';
  return String(value);
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

.field-row--value {
  align-items: flex-start;
}

.field-row__value {
  flex: 1;
  min-width: 0;
  color: #17202a;
  font-size: 24rpx;
  line-height: 1.35;
  text-align: right;
  word-break: break-word;
}

.empty {
  color: #667789;
  font-size: 24rpx;
}

.empty--error {
  color: #9f2f2f;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.record-card {
  padding: 18rpx 16rpx;
  border: 1rpx solid #e6ebf1;
  border-radius: 8rpx;
  background: #fbfcfd;
}

.record-row {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
  padding: 8rpx 0;
}

.record-row:first-child {
  padding-top: 0;
}

.record-row:last-child {
  padding-bottom: 0;
}

.record-row__label {
  flex: 0 0 168rpx;
  color: #667789;
  font-size: 22rpx;
  line-height: 1.35;
}

.record-row__value {
  flex: 1;
  min-width: 0;
  color: #17202a;
  font-size: 25rpx;
  line-height: 1.35;
  word-break: break-word;
}

.load-more {
  height: 66rpx;
  margin-top: 4rpx;
  border-radius: 8rpx;
  background: #ffffff;
  color: #1f3a5f;
  border: 1rpx solid #cbd6e2;
  font-size: 24rpx;
  line-height: 66rpx;
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

.action--disabled {
  background: #8a98a8;
  color: #eef2f6;
}
</style>
