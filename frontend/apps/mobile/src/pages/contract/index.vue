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
      <view class="summary__item">
        <text class="summary__label">追踪标识</text>
        <text class="summary__value">{{ traceLabel || '-' }}</text>
      </view>
      <view class="summary__item">
        <text class="summary__label">运行策略</text>
        <text class="summary__value">{{ runtimeLabel || '-' }}</text>
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

    <view v-else-if="recordRows.length || relationBlocks.length" class="section">
      <view class="section__head">
        <view class="section__title">业务记录</view>
        <view class="section__count">{{ recordRows.length + relationBlocks.length }} 项</view>
      </view>
      <view v-if="displayFields.length && records.length" class="field-list">
        <view v-for="field in displayFields" :key="field.widgetId" class="field-row field-row--value">
          <view class="field-row__main">
            <text class="field-row__label">{{ field.label }}</text>
            <text class="field-row__code">{{ field.fieldCode }}</text>
          </view>
          <input
            v-if="isEditableField(field)"
            class="field-row__input"
            :value="formatEditableValue(records[0][field.fieldCode])"
            :disabled="field.disabled"
            @input="handleFieldInput(field, $event)"
            @blur="runFieldAction(field, 'blur')"
          />
          <view v-else class="field-row__value">{{ formatFieldValue(field, records[0][field.fieldCode]) }}</view>
        </view>
      </view>
      <view v-if="relationBlocks.length" class="relation-list">
        <view v-for="block in relationBlocks" :key="block.widgetId" class="relation-block">
          <view class="relation-block__head">
            <text class="relation-block__title">{{ block.label }}</text>
            <text class="relation-block__count">{{ block.rowCount }} 行</text>
          </view>
          <view v-for="row in block.rows" :key="row.key" class="relation-block__row">{{ row.summary }}</view>
          <button
            v-if="block.canLoadMore"
            class="relation-block__more relation-block__more--button"
            :disabled="relationLoadingKey === block.dataKey"
            @click="loadMoreRelationRows(block)"
          >
            {{ relationLoadingKey === block.dataKey ? '加载中...' : `加载更多（还有 ${block.moreCount} 行）` }}
          </button>
          <view v-else-if="block.moreCount > 0" class="relation-block__more">还有 {{ block.moreCount }} 行</view>
          <view v-if="relationErrorKey === block.dataKey && relationError" class="relation-block__error">{{ relationError }}</view>
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

    <view v-if="commandActions.length" class="section">
      <view class="section__head">
        <view class="section__title">可用动作</view>
        <view class="section__count">{{ commandActions.length }} 项</view>
      </view>
      <view class="action-list">
        <button
          v-for="action in commandActions"
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
  dataKey: string;
  dictKey: string;
  summaryFields: string[];
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
  triggerType: string;
  sourceWidgetId: string;
  dispatchMode: string;
  submitPolicy: Dict;
  refreshMode: string;
  targetIds: string[];
  dependencyTargets: string[];
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

interface RelationBlock {
  widgetId: string;
  fieldCode: string;
  dataKey: string;
  label: string;
  rowCount: number;
  total: number;
  moreCount: number;
  canLoadMore: boolean;
  rows: RelationDisplayRow[];
}

interface RelationDisplayRow {
  key: string;
  summary: string;
}

interface InlineRecordSet {
  key: string;
  rows: Dict[];
  section: 'tableRows' | 'treeData';
}

const TARGET_MODEL = 'construction.contract';
const TARGET_VIEW_TYPE = 'tree';
const CLIENT_TYPE = 'harmony_h5';
const DEFAULT_ONCHANGE_DEBOUNCE_MS = 300;

const loading = ref(false);
const error = ref('');
const contract = ref<Dict | null>(null);
const routeQuery = ref<Dict>({});
const dataLoading = ref(false);
const dataError = ref('');
const records = ref<Dict[]>([]);
const recordTotal = ref<number | null>(null);
const nextOffset = ref(0);
const activeRecordDataKey = ref('');
const runningActionId = ref('');
const relationLoadingKey = ref('');
const relationErrorKey = ref('');
const relationError = ref('');
let fieldActionTimer: ReturnType<typeof setTimeout> | null = null;

const pageInfo = computed(() => asDict(contract.value?.pageInfo));
const layoutContract = computed(() => asDict(contract.value?.layoutContract));
const actionContract = computed(() => asDict(contract.value?.actionContract));
const dataContract = computed(() => asDict(contract.value?.dataContract));
const statusContract = computed(() => asDict(contract.value?.statusContract));
const runtimeContract = computed(() => asDict(contract.value?.runtimeContract));
const contractMeta = computed(() => asDict(contract.value?.meta));
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
const traceLabel = computed(() => asText(contractMeta.value.traceId || contractMeta.value.requestId || contractMeta.value.etag || contractMeta.value.snapshotId));
const runtimeLabel = computed(() => {
  const cachePolicy = asText(runtimeContract.value.cachePolicy);
  const retryPolicy = asDict(runtimeContract.value.retryPolicy);
  const maxRetries = asText(retryPolicy.maxRetries);
  return [cachePolicy, maxRetries ? `retry:${maxRetries}` : ''].filter(Boolean).join(' · ');
});
const widgets = computed(() => collectWidgets(layoutContract.value, statusContract.value));
const businessFields = computed(() => widgets.value.filter(isBusinessDisplayField));
const listDisplayFields = computed(() => businessFields.value.slice(0, 8));
const displayFields = computed(() => (isListSurface.value ? listDisplayFields.value : businessFields.value));
const sceneBlocks = computed(() => widgets.value.filter((item) => item.visible && item.widgetType === 'display' && item.fieldCode));
const actions = computed(() => collectActions(actionContract.value, statusContract.value));
const commandActions = computed(() => actions.value.filter((action) => ['click', 'submit', 'confirm', 'delete', 'refresh', 'select'].includes(action.triggerType)));
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
const relationBlocks = computed<RelationBlock[]>(() => collectRelationBlocks(widgets.value, dataContract.value));
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

function asTextList(value: unknown): string[] {
  return asList(value).map((item) => asText(item)).filter(Boolean);
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

function normalizeError(err: unknown, fallback = '契约读取失败'): string {
  const detail = errorDiagnosticLabel(err);
  if (err instanceof Error && err.message) {
    const message = err.message.toLowerCase();
    if (message.includes('401') || message.includes('403') || message.includes('token')) {
      return appendErrorDiagnostic('登录已失效，请重新登录', detail);
    }
    if (message.includes('network') || message.includes('request') || message.includes('timeout')) {
      return appendErrorDiagnostic('服务暂不可用，请检查服务地址', detail);
    }
    return appendErrorDiagnostic(err.message, detail);
  }
  return appendErrorDiagnostic(fallback, detail);
}

function appendErrorDiagnostic(message: string, detail: string): string {
  return detail ? `${message}（${detail}）` : message;
}

function errorDiagnosticLabel(err: unknown): string {
  const row = asDict(err);
  const reasonCode = asText(row.reason_code || row.reasonCode || row.code);
  const traceId = asText(row.trace_id || row.traceId);
  return [reasonCode, traceId].filter(Boolean).join(' · ');
}

function intentError(message: string, details: Dict): Error {
  return Object.assign(new Error(message), details);
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
          const bodyError = asDict(body.error);
          reject(intentError(asText(bodyError.message || body.message, `request failed: ${statusCode}`), {
            code: statusCode,
            reason_code: bodyError.reason_code || bodyError.reasonCode || bodyError.code,
            trace_id: bodyError.trace_id || bodyError.traceId || asDict(body.meta).trace_id,
          }));
          return;
        }
        if (body.ok === false) {
          const bodyError = asDict(body.error);
          reject(intentError(asText(bodyError.message || body.error, 'intent failed'), {
            code: bodyError.code,
            reason_code: bodyError.reason_code || bodyError.reasonCode || bodyError.code,
            trace_id: bodyError.trace_id || bodyError.traceId || asDict(body.meta).trace_id,
          }));
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
  const recordDataKey = asText(source.dataKey || source.data_key || firstInlineRecordSet(asDict(nextContract.dataContract)).key || 'primary');
  const sourceIntent = asText(source.intent || source.query || source.provider);
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
      ...contractTraceParams(nextContract),
    };
    if (sourceOp === 'read') {
      requestParams.ids = normalizeIds(sourceParams.ids);
    } else {
      requestParams.limit = Number(sourceParams.limit) || 20;
      requestParams.offset = append ? nextOffset.value : 0;
      requestParams.need_total = true;
      requestParams.dataKey = recordDataKey;
      requestParams.data_key = recordDataKey;
    }
    const response = await requestIntent(endpoint, token, {
      intent: sourceIntent,
      params: requestParams,
    });
    const data = asDict(response.data);
    const nextRecords = asList(data.records).map((item) => asDict(item));
    records.value = append ? records.value.concat(nextRecords) : nextRecords;
    activeRecordDataKey.value = recordDataKey;
    if (sourceOp === 'read') {
      recordTotal.value = nextRecords.length;
      nextOffset.value = nextRecords.length;
    } else {
      const total = Number(data.total);
      recordTotal.value = Number.isFinite(total) ? total : null;
      const offset = Number(data.next_offset);
      nextOffset.value = Number.isFinite(offset) ? offset : records.value.length;
    }
    syncRecordDataContractRows(nextContract, recordDataKey, viewType, records.value, {
      total: recordTotal.value,
      nextOffset: nextOffset.value,
      limit: Number(requestParams.limit) || records.value.length,
    });
  } catch (err) {
    if (!append) {
      records.value = [];
      recordTotal.value = null;
      nextOffset.value = 0;
    }
    dataError.value = normalizeError(err, '业务数据读取失败');
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

async function loadMoreRelationRows(block: RelationBlock) {
  const runtime = resolveRuntimeEndpoint();
  if (!runtime || !contract.value || relationLoadingKey.value) return;
  const currentDataContract = asDict(contract.value.dataContract);
  const dataSources = asDict(currentDataContract.dataSource);
  const widget = widgets.value.find((item) => item.widgetId === block.widgetId || item.fieldCode === block.fieldCode);
  const dataSource = widget ? resolveRelationDataSource(dataSources, widget, block.dataKey) : null;
  const sourceIntent = asText(dataSource?.intent || dataSource?.query || dataSource?.provider);
  if (!dataSource || !sourceIntent) return;
  const pagination = asDict(currentDataContract.pagination);
  const page = asDict(pagination[block.dataKey] || pagination[block.fieldCode] || pagination[block.widgetId]);
  const sourceParams = asDict(dataSource.params);
  const limit = Number(sourceParams.limit || page.pageSize || page.limit) || 20;
  const offset = Number(page.next_offset || page.nextOffset || sourceParams.offset || block.rowCount);
  const requestParams: Dict = {
    ...sourceParams,
    ...contractTraceParams(contract.value),
    dataKey: block.dataKey,
    data_key: block.dataKey,
    fieldCode: block.fieldCode,
    field_code: block.fieldCode,
    limit,
    offset: Number.isFinite(offset) ? offset : block.rowCount,
  };
  relationLoadingKey.value = block.dataKey;
  relationErrorKey.value = '';
  relationError.value = '';
  try {
    const response = await requestIntent(runtime.endpoint, runtime.token, {
      intent: sourceIntent,
      params: requestParams,
    });
    mergeRelationRowsResponse(block, asDict(response.data), limit);
  } catch (err) {
    relationErrorKey.value = block.dataKey;
    relationError.value = normalizeError(err, '子表加载失败');
  } finally {
    relationLoadingKey.value = '';
  }
}

function mergeRelationRowsResponse(block: RelationBlock, data: Dict, requestedLimit: number) {
  const current = asDict(contract.value);
  const currentData = asDict(current.dataContract);
  const relationRows = asDict(currentData.relationRows);
  const pagination = asDict(currentData.pagination);
  const currentRows = asList(relationRows[block.dataKey]).map((item) => asDict(item)).filter((item) => Object.keys(item).length);
  const nextRows = extractRelationResponseRows(data, block.dataKey);
  const mergedRows = mergeRowsById(currentRows, nextRows);
  const nextOffsetRaw = Number(data.next_offset || data.nextOffset);
  const totalRaw = Number(data.total);
  const pagePatch = asDict(asDict(data.pagination)[block.dataKey] || data.pagination);
  contract.value = {
    ...current,
    dataContract: {
      ...currentData,
      relationRows: {
        ...relationRows,
        [block.dataKey]: mergedRows,
      },
      pagination: {
        ...pagination,
        [block.dataKey]: {
          ...asDict(pagination[block.dataKey]),
          ...pagePatch,
          limit: requestedLimit,
          pageSize: Number(pagePatch.pageSize || pagePatch.limit) || requestedLimit,
          next_offset: Number.isFinite(nextOffsetRaw) ? nextOffsetRaw : mergedRows.length,
          total: Number.isFinite(totalRaw) ? totalRaw : Number(asDict(pagination[block.dataKey]).total) || mergedRows.length,
        },
      },
    },
  };
}

function extractRelationResponseRows(data: Dict, dataKey: string): Dict[] {
  const relationRows = asDict(data.relationRows);
  const tableRows = asDict(data.tableRows);
  const keyedRows = asList(relationRows[dataKey]).length ? relationRows[dataKey] : tableRows[dataKey];
  const rows = asList(keyedRows).length ? keyedRows : (data.records || data.rows || data.items);
  return asList(rows).map((item) => asDict(item)).filter((item) => Object.keys(item).length);
}

function mergeRowsById(baseRows: Dict[], patchRows: Dict[]): Dict[] {
  const out = [...baseRows];
  const indexById = new Map<string, number>();
  out.forEach((row, index) => {
    const id = asText(row.id);
    if (id) indexById.set(id, index);
  });
  patchRows.forEach((row) => {
    const id = asText(row.id);
    const index = id ? indexById.get(id) : undefined;
    if (index === undefined) {
      if (id) indexById.set(id, out.length);
      out.push(row);
    } else {
      out[index] = { ...out[index], ...row };
    }
  });
  return out;
}

function syncRecordDataContractRows(nextContract: Dict, dataKey: string, viewType: string, nextRows: Dict[], page: { total: number | null; nextOffset: number; limit: number }) {
  const current = asDict(contract.value || nextContract);
  const currentData = asDict(current.dataContract);
  const rowSection = viewType === 'tree' ? 'treeData' : 'tableRows';
  const rowsByKey = asDict(currentData[rowSection]);
  const pagination = asDict(currentData.pagination);
  const key = dataKey || firstInlineRecordSet(currentData).key || 'primary';
  contract.value = {
    ...current,
    dataContract: {
      ...currentData,
      [rowSection]: {
        ...rowsByKey,
        [key]: nextRows,
      },
      pagination: {
        ...pagination,
        [key]: {
          ...asDict(pagination[key]),
          limit: page.limit,
          pageSize: page.limit,
          next_offset: page.nextOffset,
          total: page.total === null ? nextRows.length : page.total,
        },
      },
    },
  };
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
  const selectorStatus = collectSelectorStatus(status);
  function walkContainers(containers: unknown[], inherited: Dict = {}) {
    containers.forEach((container) => {
      const row = asDict(container);
      const containerId = asText(row.containerId);
      const containerSelectorState = resolveSelectorStatus(selectorStatus, [containerId]);
      const state = { ...containerSelectorState, ...asDict(containerStatus[containerId]) };
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
        const fieldCode = asText(widget.fieldCode);
        const widgetSelectorState = resolveSelectorStatus(selectorStatus, [widgetId, fieldCode, `${containerId}.${fieldCode}`, `${containerId}.${widgetId}`]);
        const widgetState = { ...widgetSelectorState, ...asDict(widgetStatus[widgetId]) };
        const config = asDict(widget.componentConfig);
        rows.push({
          widgetId,
          widgetType: asText(widget.widgetType),
          fieldCode,
          label: asText(widget.label, asText(fieldCode, widgetId)),
          componentKey: asText(widget.componentKey),
          dataKey: asText(config.dataKey),
          dictKey: asText(config.dictKey),
          summaryFields: collectSummaryFields(config),
          blockType: asText(config.blockType),
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

function collectSelectorStatus(status: Dict): Dict[] {
  return asList(status.selectorStatus).map((item) => asDict(item)).filter((row) => asText(row.selector));
}

function resolveSelectorStatus(rows: Dict[], selectors: string[]): Dict {
  const normalized = selectors.map((item) => asText(item)).filter(Boolean);
  for (const row of rows) {
    const pattern = asText(row.selector);
    if (normalized.some((selector) => matchesSelector(pattern, selector))) return row;
  }
  return {};
}

function matchesSelector(pattern: string, selector: string): boolean {
  if (!pattern || !selector) return false;
  if (pattern === selector) return true;
  if (pattern.endsWith('.*')) return selector.startsWith(pattern.slice(0, -1));
  return false;
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
  const selectorPatchRows = asList(statusPatch.selectorStatus).map((item) => asDict(item));
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
  if (!hasLayoutPatch && !hasRuntimePatch && !hasDataContractPatch && !Object.keys(globalPatch).length && !containerPatchRows.length && !selectorPatchRows.length && !widgetPatchRows.length && !buttonPatchRows.length) return;
  const current = asDict(contract.value);
  const currentLayout = asDict(current.layoutContract);
  const currentData = asDict(current.dataContract);
  const currentRuntime = asDict(current.runtimeContract);
  const currentStatus = asDict(current.statusContract);
  const nextLayout = hasLayoutPatch ? { ...currentLayout, ...layoutPatch } : currentLayout;
  const replaceRows = isReplaceDataPatch(patch, dataPatch);
  const nextData = {
    ...currentData,
    mainData: { ...asDict(currentData.mainData), ...mainData },
    tableRows: mergeRowsByDataKey(asDict(currentData.tableRows), tableRowsPatch, replaceRows),
    relationRows: mergeRowsByDataKey(asDict(currentData.relationRows), relationRowsPatch, replaceRows),
    treeData: mergeRowsByDataKey(asDict(currentData.treeData), treeDataPatch, replaceRows),
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
    selectorStatus: mergeStatusRows(asList(currentStatus.selectorStatus), selectorPatchRows, 'selector'),
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
  syncRecordsFromDataPatch(nextData);
}

function isReplaceDataPatch(patch: Dict, dataPatch: Dict): boolean {
  const operation = asText(dataPatch.patchOperation || dataPatch.operation || patch.patchOperation || patch.operation).toLowerCase();
  return patch.updateType === 'full' || operation === 'replace';
}

function mergeRowsByDataKey(baseRowsByKey: Dict, patchRowsByKey: Dict, replaceRows: boolean): Dict {
  const out = { ...baseRowsByKey };
  Object.entries(patchRowsByKey).forEach(([key, patchValue]) => {
    if (key === 'line_patches') {
      applyLinePatches(out, patchValue);
      return;
    }
    const patchRows = extractPatchRows(patchValue);
    if (!patchRows) {
      out[key] = patchValue;
      return;
    }
    const rowOperation = asText(asDict(patchValue).operation || asDict(patchValue).patchOperation).toLowerCase();
    out[key] = replaceRows || rowOperation === 'replace'
      ? patchRows
      : mergeRowsById(asList(baseRowsByKey[key]).map((item) => asDict(item)), patchRows);
  });
  return out;
}

function applyLinePatches(rowsByKey: Dict, patchValue: unknown) {
  asList(patchValue).map((item) => asDict(item)).forEach((linePatch) => {
    const fieldName = asText(linePatch.field || linePatch.relation_field || linePatch.fieldCode || linePatch.dataKey);
    if (!fieldName) return;
    const baseRows = asList(rowsByKey[fieldName]).map((item) => asDict(item)).filter((item) => Object.keys(item).length);
    rowsByKey[fieldName] = applyLinePatchRows(baseRows, linePatch);
  });
}

function applyLinePatchRows(baseRows: Dict[], linePatch: Dict): Dict[] {
  const rowState = asText(linePatch.row_state || linePatch.state).toLowerCase();
  const command = asList(linePatch.command_hint || linePatch.command).map((item) => asText(item).toLowerCase());
  const removeRow = rowState === 'delete' || rowState === 'deleted' || command.includes('unlink') || command.includes('delete') || command.includes('remove');
  const rowKey = asText(linePatch.row_key || linePatch.key || linePatch.virtual_id);
  const rowId = asText(linePatch.row_id || linePatch.id);
  const patch = asDict(linePatch.patch || linePatch.values || linePatch.value);
  const matches = (row: Dict) => Boolean(
    (rowId && asText(row.id) === rowId)
    || (rowKey && asText(row.row_key || row.key || row.virtual_id || row.__row_key) === rowKey)
  );
  if (removeRow) return baseRows.filter((row) => !matches(row));
  const index = baseRows.findIndex(matches);
  if (index >= 0) {
    return baseRows.map((row, rowIndex) => (rowIndex === index ? { ...row, ...patch } : row));
  }
  return baseRows.concat({
    ...(rowId ? { id: Number(rowId) || rowId } : {}),
    ...(rowKey ? { row_key: rowKey } : {}),
    ...patch,
  });
}

function extractPatchRows(value: unknown): Dict[] | null {
  if (Array.isArray(value)) {
    return value.map((item) => asDict(item)).filter((item) => Object.keys(item).length);
  }
  const row = asDict(value);
  const rows = row.rows || row.records || row.items;
  if (!Array.isArray(rows)) return null;
  return rows.map((item) => asDict(item)).filter((item) => Object.keys(item).length);
}

function syncRecordsFromDataPatch(nextData: Dict) {
  const key = activeRecordDataKey.value;
  if (!key || !isListSurface.value) return;
  const tableRows = asList(asDict(nextData.tableRows)[key]).map((item) => asDict(item)).filter((item) => Object.keys(item).length);
  const treeRows = asList(asDict(nextData.treeData)[key]).map((item) => asDict(item)).filter((item) => Object.keys(item).length);
  const patchedRows = tableRows.length ? tableRows : treeRows;
  if (patchedRows.length) records.value = patchedRows;
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
  const dependencyGraph = asDict(action.dependencyGraph);
  return asList(action.actionRuleList)
    .map((item) => {
      const row = asDict(item);
      const actionId = asText(row.actionId);
      const actionKey = asText(row.actionKey, actionId.replace(/^action\./, ''));
      const sourceWidgetId = asText(row.sourceWidgetId || row.source_widget_id);
      const targetIds = asTextList(row.targetIds || row.target_ids || row.targets);
      const dependencyTargets = collectActionDependencyTargets(dependencyGraph, actionId, actionKey, sourceWidgetId, targetIds);
      const state = buttonStatus[`btn.${actionKey}`] || buttonStatus[actionId] || {};
      return {
        actionId,
        actionKey,
        label: asText(row.label, actionId),
        intent: asText(row.intent, 'ui.contract'),
        triggerType: asText(row.triggerType || row.trigger_type, 'click'),
        sourceWidgetId,
        dispatchMode: asText(row.dispatchMode || row.dispatch_mode, 'server'),
        submitPolicy: asDict(row.submitPolicy || row.submit_policy),
        refreshMode: normalizeRefreshMode(row.refreshMode),
        targetIds,
        dependencyTargets,
        target: asDict(row.target),
        button: asDict(row.button),
        visible: state.visible !== false,
        disabled: state.disabled === true || isPageReadonly.value || !isPageReadable.value,
      };
    })
    .filter((item) => item.actionId && item.visible);
}

function collectActionDependencyTargets(graph: Dict, actionId: string, actionKey: string, sourceWidgetId: string, targetIds: string[]): string[] {
  const out = new Set(targetIds);
  for (const key of [actionId, actionKey, sourceWidgetId]) {
    for (const target of asTextList(graph[key])) {
      out.add(target);
    }
  }
  return Array.from(out);
}

function collectRelationBlocks(sourceWidgets: ContractWidget[], currentDataContract: Dict): RelationBlock[] {
  const relationRows = asDict(currentDataContract.relationRows);
  const pagination = asDict(currentDataContract.pagination);
  const dataMeta = asDict(currentDataContract.dataMeta);
  const dataSources = asDict(currentDataContract.dataSource);
  return sourceWidgets
    .filter((widget) => widget.visible && isRelationWidget(widget))
    .map((widget) => {
      const dataKey = asText(widget.dataKey, widget.fieldCode);
      const rows = asList(relationRows[dataKey]).map((item) => asDict(item)).filter((item) => Object.keys(item).length);
      const summaryFields = resolveRelationSummaryFields(widget, dataKey, dataMeta);
      const page = asDict(pagination[dataKey] || pagination[widget.fieldCode] || pagination[widget.widgetId]);
      const totalRaw = Number(page.total);
      const total = Number.isFinite(totalRaw) ? totalRaw : rows.length;
      const visibleRows = rows.slice(0, rows.length);
      const dataSource = resolveRelationDataSource(dataSources, widget, dataKey);
      return {
        widgetId: widget.widgetId,
        fieldCode: widget.fieldCode,
        dataKey,
        label: widget.label,
        rowCount: rows.length,
        total,
        moreCount: Math.max(0, total - visibleRows.length),
        canLoadMore: Boolean(dataSource && total > rows.length),
        rows: visibleRows.map((row, index) => ({
          key: asText(row.id, `${widget.widgetId}.${index}`),
          summary: formatRelationRow(row, summaryFields),
        })),
      };
    })
    .filter((block) => block.rowCount > 0);
}

function resolveRelationDataSource(dataSources: Dict, widget: ContractWidget, dataKey: string): Dict | null {
  const source = asDict(dataSources[dataKey] || dataSources[widget.fieldCode] || dataSources[widget.widgetId]);
  return Object.keys(source).length ? source : null;
}

function isRelationWidget(widget: ContractWidget): boolean {
  const type = widget.widgetType.toLowerCase();
  const component = widget.componentKey.toLowerCase();
  return type === 'table' || type === 'relation' || component.includes('table') || component.includes('relation');
}

function collectSummaryFields(config: Dict): string[] {
  return [
    ...fieldNamesFromList(config.summaryFields || config.summary_fields),
    ...fieldNamesFromList(config.displayFields || config.display_fields),
    ...fieldNamesFromList(config.columns),
  ].filter((field, index, all) => field && all.indexOf(field) === index);
}

function resolveRelationSummaryFields(widget: ContractWidget, dataKey: string, dataMeta: Dict): string[] {
  const meta = asDict(dataMeta[dataKey] || dataMeta[widget.fieldCode] || dataMeta[widget.widgetId]);
  return [
    ...widget.summaryFields,
    ...fieldNamesFromList(meta.summaryFields || meta.summary_fields),
    ...fieldNamesFromList(meta.displayFields || meta.display_fields),
    ...fieldNamesFromList(meta.columns || meta.fields),
  ].filter((field, index, all) => field && all.indexOf(field) === index);
}

function fieldNamesFromList(value: unknown): string[] {
  return asList(value)
    .map((item) => {
      if (typeof item === 'string') return asText(item);
      const row = asDict(item);
      return asText(row.fieldCode || row.field || row.name || row.key);
    })
    .filter(Boolean);
}

function formatRelationRow(row: Dict, summaryFields: string[]): string {
  const preferred = asText(row.display_name || row.name || row.label);
  if (preferred) return preferred;
  const entries = summaryFields.length
    ? summaryFields.map((field) => [field, row[field]] as [string, unknown]).filter(([, value]) => value !== undefined)
    : Object.entries(row).filter(([key]) => key !== 'id' && !key.startsWith('__')).slice(0, 3);
  const parts = entries
    .map(([key, value]) => `${key}: ${formatValue(value)}`)
    .filter((item) => item.trim());
  return parts.join(' · ') || asText(row.id, '-');
}

function resolvePrimaryDataSource(nextContract: Dict): Dict {
  const dataContract = asDict(nextContract.dataContract);
  const dataSources = asDict(dataContract.dataSource);
  const primary = asDict(dataSources.primary);
  const inlineSet = firstInlineRecordSet(dataContract);
  if (primary.intent || primary.query) return { ...primary, dataKey: asText(primary.dataKey || primary.data_key, inlineSet.key || 'primary') };
  if (inlineSet.key) {
    const keyedSource = asDict(dataSources[inlineSet.key]);
    if (keyedSource.intent || keyedSource.query || keyedSource.provider) return { ...keyedSource, dataKey: inlineSet.key };
  }
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
  return firstInlineRecordSet(dataContract).rows;
}

function firstInlineRecordSet(dataContract: Dict): InlineRecordSet {
  const tableRows = firstRecordList(asDict(dataContract.tableRows), 'tableRows');
  if (tableRows.rows.length) return tableRows;
  const treeRows = firstRecordList(asDict(dataContract.treeData), 'treeData');
  if (treeRows.rows.length) return treeRows;
  return { key: '', rows: [], section: 'tableRows' };
}

function firstRecordList(rowsByKey: Dict, section: 'tableRows' | 'treeData'): InlineRecordSet {
  for (const [key, value] of Object.entries(rowsByKey)) {
    const rows = asList(value).map((item) => asDict(item)).filter((item) => Object.keys(item).length);
    if (rows.length) return { key, rows, section };
  }
  return { key: '', rows: [], section };
}

function hydrateInlineRecords(nextContract: Dict) {
  const dataContract = asDict(nextContract.dataContract);
  const mainData = asDict(dataContract.mainData);
  const inlineSet = firstInlineRecordSet(dataContract);
  const inlineRecords = inlineSet.rows.length ? inlineSet.rows : (Object.keys(mainData).length ? [mainData] : []);
  records.value = inlineRecords;
  activeRecordDataKey.value = inlineSet.key;
  const pagination = asDict(dataContract.pagination);
  const matchedPagination = asDict(pagination[inlineSet.key]);
  const fallbackPagination = Object.values(pagination).map((item) => asDict(item)).find((item) => Object.keys(item).length) || {};
  const total = Number((Object.keys(matchedPagination).length ? matchedPagination : fallbackPagination).total);
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

function contractTraceParams(sourceContract: Dict | null): Dict {
  const meta = asDict(sourceContract?.meta);
  const traceId = asText(meta.traceId || meta.trace_id);
  const requestId = asText(meta.requestId || meta.request_id);
  const out: Dict = {};
  if (traceId) out.trace_id = traceId;
  if (requestId) out.request_id = requestId;
  if (meta.etag) out.contract_etag = meta.etag;
  if (meta.snapshotId || meta.snapshot_id) out.snapshot_id = meta.snapshotId || meta.snapshot_id;
  return out;
}

function contractTraceContext(sourceContract: Dict | null): Dict {
  const params = contractTraceParams(sourceContract);
  const out: Dict = {};
  if (params.trace_id) out.trace_id = params.trace_id;
  if (params.request_id) out.request_id = params.request_id;
  return out;
}

function isEditableField(field: ContractWidget): boolean {
  if (isListSurface.value || isPageReadonly.value || field.readonly || field.disabled || !field.fieldCode) return false;
  const type = field.widgetType.toLowerCase();
  const component = field.componentKey.toLowerCase();
  return type === 'input' || component.includes('input') || component.includes('textarea');
}

function formatEditableValue(value: unknown): string {
  if (value === null || value === undefined) return '';
  if (Array.isArray(value)) return asText(value[1] || value[0]);
  if (typeof value === 'object') return asText(asDict(value).display_name || asDict(value).name || asDict(value).label);
  return String(value);
}

function handleFieldInput(field: ContractWidget, event: unknown) {
  if (!records.value.length || !field.fieldCode) return;
  const detail = asDict(asDict(event).detail);
  records.value = [
    {
      ...records.value[0],
      [field.fieldCode]: detail.value,
    },
    ...records.value.slice(1),
  ];
  scheduleFieldAction(field, 'change');
}

function scheduleFieldAction(field: ContractWidget, triggerType: string) {
  const action = resolveFieldAction(field, triggerType);
  if (!action) return;
  if (fieldActionTimer) clearTimeout(fieldActionTimer);
  const delay = resolveActionDebounceMs(action);
  fieldActionTimer = setTimeout(() => {
    fieldActionTimer = null;
    void runFieldAction(field, triggerType);
  }, delay);
}

function resolveActionDebounceMs(action: ContractAction): number {
  if (action.dispatchMode !== 'serverDebounced') return 0;
  const debounceMs = Number(action.submitPolicy.debounceMs || action.submitPolicy.debounce_ms);
  if (!Number.isFinite(debounceMs)) return DEFAULT_ONCHANGE_DEBOUNCE_MS;
  return Math.max(0, debounceMs);
}

async function runFieldAction(field: ContractWidget, triggerType: string) {
  const action = resolveFieldAction(field, triggerType);
  const runtime = resolveRuntimeEndpoint();
  if (!action || !runtime || !records.value.length || !contract.value) return;
  const currentRecord = records.value[0];
  try {
    const response = await requestIntent(runtime.endpoint, runtime.token, {
      intent: 'api.onchange',
      params: {
        model: modelName.value,
        res_id: currentRecordId() || undefined,
        values: { ...currentRecord },
        changed_fields: [field.fieldCode],
        include_v2_patch: true,
        contract_version: contractVersion.value,
        request_id: asText(contractMeta.value.requestId || contractMeta.value.request_id),
        context: contractTraceContext(contract.value),
        ...contractTraceParams(contract.value),
      },
    });
    applyResponseUnifiedPagePatch(response);
    applyOnchangeDataPatch(response);
    showActionResponseFeedback(response);
    if (normalizeRefreshMode(action.refreshMode) === 'full' || needsFullContractRefresh(actionRefreshTargets(action))) {
      await loadContract();
    }
  } catch (err) {
    uni.showToast({ title: normalizeError(err, '字段联动失败').slice(0, 48), icon: 'none' });
  }
}

function resolveFieldAction(field: ContractWidget, triggerType: string): ContractAction | null {
  const candidates = [field.widgetId, field.fieldCode, `field.${field.fieldCode}`].filter(Boolean);
  return actions.value.find((action) => action.triggerType === triggerType && candidates.includes(action.sourceWidgetId)) || null;
}

function applyOnchangeDataPatch(response: Dict) {
  const data = asDict(response.data);
  const patch = asDict(data.patch);
  if (!Object.keys(patch).length || !records.value.length) return;
  records.value = [{ ...records.value[0], ...patch }, ...records.value.slice(1)];
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
    if (runtime) await applyActionRefreshMode(action.refreshMode, runtime.endpoint, runtime.token, action);
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
        context: {
          ...context,
          ...contractTraceContext(contract.value),
        },
        ...contractTraceParams(contract.value),
      },
    });
    const appliedPatch = applyResponseUnifiedPagePatch(response);
    showActionResponseFeedback(response);
    if (appliedPatch && normalizeRefreshMode(action.refreshMode) === 'none') return;
    await applyActionEffect(asDict(asDict(response.data).effect), action, endpoint, token);
  } catch (err) {
    uni.showToast({ title: normalizeError(err, '动作执行失败').slice(0, 48), icon: 'none' });
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

function applyResponseUnifiedPagePatch(response: Dict): boolean {
  const data = asDict(response.data);
  const patch = asDict(response.unified_page_patch_v2 || data.unified_page_patch_v2 || data.unifiedPagePatchV2);
  if (!Object.keys(patch).length) return false;
  applyUnifiedPagePatchV2(patch);
  return true;
}

function showActionResponseFeedback(response: Dict) {
  const data = asDict(response.data);
  const result = asDict(data.result);
  const effect = asDict(data.effect);
  const warning = firstResponseWarning(response);
  const message = warning || asText(effect.message || result.message || data.message);
  if (message) uni.showToast({ title: message.slice(0, 48), icon: warning ? 'none' : 'success' });
}

function firstResponseWarning(response: Dict): string {
  const data = asDict(response.data);
  const rows = [
    ...asList(response.warnings),
    ...asList(data.warnings),
    ...asList(data.warning ? [data.warning] : []),
  ];
  for (const item of rows) {
    if (typeof item === 'string') return asText(item);
    const row = asDict(item);
    const message = asText(row.message || row.title || row.reason_code || row.reasonCode);
    if (message) return message;
  }
  return '';
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
  if (type === 'toast') {
    const message = asText(effect.message);
    if (message) uni.showToast({ title: message.slice(0, 48), icon: 'none' });
    return;
  }
  await applyActionRefreshMode(action.refreshMode, endpoint, token, action);
}

async function applyActionRefreshMode(refreshMode: string, endpoint: string, token: string, action?: ContractAction) {
  const mode = normalizeRefreshMode(refreshMode);
  if (mode === 'none') return;
  if (mode === 'full' || !contract.value) {
    await loadContract();
    return;
  }
  const targets = action ? actionRefreshTargets(action) : [];
  if (targets.length && needsFullContractRefresh(targets)) {
    await loadContract();
    return;
  }
  await loadRecords(endpoint, token, contract.value, false);
}

function actionRefreshTargets(actionOrMode: ContractAction | string): string[] {
  if (typeof actionOrMode === 'string') return [];
  return Array.from(new Set([...actionOrMode.targetIds, ...actionOrMode.dependencyTargets]));
}

function needsFullContractRefresh(targets: string[]): boolean {
  return targets.some((item) => {
    const target = item.toLowerCase();
    return target === 'page.root'
      || target.startsWith('layout.')
      || target.startsWith('status.')
      || target.startsWith('container.')
      || target.startsWith('btn.')
      || target.startsWith('button.')
      || target.startsWith('relationrows.')
      || target.startsWith('relation_rows.');
  });
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
  flex-wrap: wrap;
  margin-bottom: 22rpx;
}

.summary__item {
  flex: 1 1 30%;
  min-width: 0;
  padding: 18rpx 14rpx;
  border-right: 1rpx solid #edf1f5;
  border-bottom: 1rpx solid #edf1f5;
}

.summary__item:nth-child(3n),
.summary__item:last-child {
  border-right: 0;
}

.summary__item:nth-last-child(-n + 2) {
  border-bottom: 0;
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

.relation-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  margin-top: 14rpx;
}

.relation-block {
  padding: 16rpx;
  border: 1rpx solid #e1e8ee;
  border-radius: 8rpx;
  background: #f8fafb;
}

.relation-block__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 10rpx;
}

.relation-block__title,
.relation-block__count,
.relation-block__row,
.relation-block__more,
.relation-block__error {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.relation-block__title {
  color: #17202a;
  font-size: 24rpx;
  font-weight: 700;
}

.relation-block__count {
  flex: 0 0 auto;
  color: #667789;
  font-size: 21rpx;
}

.relation-block__row {
  padding: 8rpx 0;
  color: #344154;
  font-size: 22rpx;
  border-top: 1rpx solid #e8edf2;
}

.relation-block__more {
  padding-top: 8rpx;
  color: #667789;
  font-size: 21rpx;
  border-top: 1rpx solid #e8edf2;
}

.relation-block__more--button {
  width: 100%;
  margin: 0;
  padding: 8rpx 0 0;
  border: 0;
  border-top: 1rpx solid #e8edf2;
  border-radius: 0;
  background: transparent;
  color: #1f5f99;
  font-size: 21rpx;
  line-height: 1.4;
  text-align: left;
}

.relation-block__more--button[disabled] {
  color: #8b9aac;
}

.relation-block__error {
  padding-top: 8rpx;
  color: #b42318;
  font-size: 21rpx;
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

.field-row__input {
  flex: 1;
  min-width: 180rpx;
  height: 56rpx;
  padding: 0 14rpx;
  border: 1rpx solid #cfd8e3;
  border-radius: 8rpx;
  background: #fff;
  color: #17202a;
  font-size: 24rpx;
  line-height: 56rpx;
  text-align: right;
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
