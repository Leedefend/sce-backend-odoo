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

    <view v-if="warningMessages.length" class="warning-stack">
      <view v-for="message in warningMessages" :key="message" class="warning-stack__item">
        {{ message }}
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
          <switch
            v-if="isBooleanField(field)"
            :checked="Boolean(records[0][field.fieldCode])"
            :disabled="field.disabled"
            @change="handleBooleanChange(field, $event)"
          />
          <picker
            v-else-if="isSelectionField(field)"
            mode="selector"
            :range="selectionOptions(field)"
            range-key="label"
            :value="selectionIndex(field, records[0][field.fieldCode])"
            :disabled="field.disabled"
            @change="handleSelectionChange(field, $event)"
          >
            <view class="field-row__picker">{{ formatFieldValue(field, records[0][field.fieldCode]) || '请选择' }}</view>
          </picker>
          <button
            v-else-if="isRemoteSelectionField(field)"
            class="field-row__load"
            :disabled="many2OneLoadingKey === fieldOptionKey(field)"
            @click="loadFieldOptions(field)"
          >
            {{ many2OneLoadingKey === fieldOptionKey(field) ? '加载中...' : '加载选项' }}
          </button>
          <view v-else-if="isRemoteSearchableMany2OneField(field)" class="field-row__remote">
            <picker
              v-if="many2OneOptions(field).length"
              mode="selector"
              :range="many2OneOptions(field)"
              range-key="label"
              :value="many2OneIndex(field, records[0][field.fieldCode])"
              :disabled="field.disabled"
              @change="handleMany2OneChange(field, $event)"
            >
              <view class="field-row__picker field-row__picker--remote">{{ formatFieldValue(field, records[0][field.fieldCode]) || '请选择' }}</view>
            </picker>
            <input
              class="field-row__search"
              type="text"
              confirm-type="search"
              :value="optionSearchValue(field)"
              placeholder="搜索"
              :disabled="field.disabled"
              @input="handleOptionSearchInput(field, $event)"
              @confirm="loadFieldOptions(field)"
            />
            <button
              class="field-row__load"
              :disabled="many2OneLoadingKey === fieldOptionKey(field)"
              @click="loadFieldOptions(field)"
            >
              {{ many2OneLoadingKey === fieldOptionKey(field) ? '加载中...' : '加载' }}
            </button>
          </view>
          <picker
            v-else-if="isMany2OneField(field)"
            mode="selector"
            :range="many2OneOptions(field)"
            range-key="label"
            :value="many2OneIndex(field, records[0][field.fieldCode])"
            :disabled="field.disabled"
            @change="handleMany2OneChange(field, $event)"
          >
            <view class="field-row__picker">{{ formatFieldValue(field, records[0][field.fieldCode]) || '请选择' }}</view>
          </picker>
          <picker
            v-else-if="isDateField(field)"
            mode="date"
            :value="datePickerValue(records[0][field.fieldCode])"
            :disabled="field.disabled"
            @change="handleDateChange(field, $event)"
          >
            <view class="field-row__picker">{{ datePickerValue(records[0][field.fieldCode]) || '请选择' }}</view>
          </picker>
          <view v-else-if="isDateTimeField(field)" class="field-row__datetime">
            <picker
              mode="date"
              :value="datePickerValue(records[0][field.fieldCode])"
              :disabled="field.disabled"
              @change="handleDateTimeDateChange(field, $event)"
            >
              <view class="field-row__picker field-row__picker--datetime">{{ datePickerValue(records[0][field.fieldCode]) || '日期' }}</view>
            </picker>
            <picker
              mode="time"
              :value="timePickerValue(records[0][field.fieldCode])"
              :disabled="field.disabled"
              @change="handleDateTimeTimeChange(field, $event)"
            >
              <view class="field-row__picker field-row__picker--time">{{ timePickerValue(records[0][field.fieldCode]) || '时间' }}</view>
            </picker>
          </view>
          <input
            v-else-if="isEditableField(field)"
            class="field-row__input"
            :type="editableInputType(field)"
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
            <view class="relation-block__head-actions">
              <text class="relation-block__count">{{ block.rowCount }} 行</text>
              <button
                v-if="!isPageReadonly"
                class="relation-block__add"
                @click="openCreateRelationRow(block)"
              >
                新增
              </button>
            </view>
          </view>
          <view v-for="row in block.rows" :key="row.key" class="relation-block__row">
            <text class="relation-block__summary">{{ row.summary }}</text>
            <button
              v-if="!isPageReadonly"
              class="relation-block__edit"
              @click="editRelationRow(block, row)"
            >
              编辑
            </button>
            <button
              v-if="!isPageReadonly"
              class="relation-block__remove"
              @click="removeRelationRow(block, row)"
            >
              移除
            </button>
          </view>
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
      <view v-if="relationEditor.visible" class="relation-editor">
        <view class="relation-editor__head">
          <text class="relation-editor__title">{{ relationEditor.mode === 'create' ? '新增明细' : '编辑明细' }}</text>
          <button class="relation-editor__close" @click="closeRelationEditor">关闭</button>
        </view>
        <view class="relation-editor__body">
          <view v-for="field in relationEditorFields" :key="field" class="relation-editor__field">
            <text class="relation-editor__label">{{ field }}</text>
            <input
              class="relation-editor__input"
              type="text"
              :value="formatEditableValue(relationEditor.values[field])"
              @input="handleRelationEditorInput(field, $event)"
            />
          </view>
        </view>
        <view class="relation-editor__actions">
          <button class="relation-editor__cancel" @click="closeRelationEditor">取消</button>
          <button class="relation-editor__save" @click="saveRelationEditor">保存明细</button>
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
  editFields: string[];
  blockType: string;
  valueType: string;
  optionDomain: unknown;
  optionDomainRaw: string;
  optionContextRaw: string;
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
  tracePolicy: Dict;
  refreshMode: string;
  targetScope: string;
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
  editFields: string[];
  rows: RelationDisplayRow[];
}

interface RelationDisplayRow {
  key: string;
  rowId: string;
  rowKey: string;
  summary: string;
  raw: Dict;
}

interface RelationEditorState {
  visible: boolean;
  mode: 'create' | 'edit';
  block: RelationBlock | null;
  row: RelationDisplayRow | null;
  values: Dict;
}

interface SelectOption {
  value: unknown;
  label: string;
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
const STANDARD_FORM_ACTIONS = ['form.save', 'form.validate', 'record.delete'];

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
const many2OneLoadingKey = ref('');
const optionSearchText = ref<Record<string, string>>({});
const warningMessages = ref<string[]>([]);
const relationEditor = ref<RelationEditorState>({
  visible: false,
  mode: 'create',
  block: null,
  row: null,
  values: {},
});
let fieldActionTimer: ReturnType<typeof setTimeout> | null = null;
let warningTimer: ReturnType<typeof setTimeout> | null = null;

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
const commandActions = computed(() => actions.value.filter(isExecutableCommandAction));
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
const relationEditorFields = computed(() => {
  const block = relationEditor.value.block;
  if (!block) return [];
  const fields = block.editFields.length ? block.editFields : Object.keys(relationEditor.value.values);
  return fields.filter((field) => field && !field.startsWith('__') && !['id', 'row_key', 'key', 'virtual_id'].includes(field));
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
  return requestIntentWithRetry(endpoint, token, payload, currentRuntimeRetryPolicy());
}

async function requestIntentWithRetry(endpoint: string, token: string, payload: Dict, retryPolicy: Dict): Promise<Dict> {
  const maxRetries = Math.max(0, Math.min(3, Number(retryPolicy.maxRetries || retryPolicy.max_retries) || 0));
  const timeoutMs = Math.max(3000, Number(retryPolicy.timeoutMs || retryPolicy.timeout_ms || retryPolicy.requestTimeoutMs || retryPolicy.request_timeout_ms) || 15000);
  for (let attempt = 0; attempt <= maxRetries; attempt += 1) {
    try {
      return await requestIntentOnce(endpoint, token, payload, timeoutMs);
    } catch (err) {
      if (!shouldRetryIntentError(err) || attempt >= maxRetries) throw err;
      await delay(retryDelayMs(retryPolicy, attempt));
    }
  }
  return requestIntentOnce(endpoint, token, payload, timeoutMs);
}

function requestIntentOnce(endpoint: string, token: string, payload: Dict, timeoutMs: number): Promise<Dict> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: endpoint,
      method: 'POST',
      data: payload,
      timeout: timeoutMs,
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

function currentRuntimeRetryPolicy(): Dict {
  return asDict(asDict(contract.value?.runtimeContract).retryPolicy);
}

function shouldRetryIntentError(err: unknown): boolean {
  const row = asDict(err);
  const code = Number(row.code);
  if (code === 408 || code === 429 || code >= 500) return true;
  if (code === 401 || code === 403) return false;
  const message = err instanceof Error ? err.message.toLowerCase() : asText(row.message).toLowerCase();
  return message.includes('network') || message.includes('timeout') || message.includes('request failed') || message.includes('request:fail');
}

function retryDelayMs(retryPolicy: Dict, attempt: number): number {
  const baseDelay = Number(retryPolicy.backoffMs || retryPolicy.backoff_ms || retryPolicy.retryDelayMs || retryPolicy.retry_delay_ms) || 300;
  const multiplier = Math.max(1, Number(retryPolicy.backoffMultiplier || retryPolicy.backoff_multiplier) || 2);
  return Math.min(3000, Math.round(baseDelay * (multiplier ** attempt)));
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
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
  clearWarningMessages();
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
  const subject = asText(query.subject).toLowerCase();
  const actionId = asText(query.action_id || query.actionId || (subject === 'action' ? query.id : ''));
  if (actionId) {
    return {
      op: 'action_open',
      action_id: actionId,
      view_type: asText(query.view_type || query.viewType, TARGET_VIEW_TYPE),
      ...contractRouteParams(query),
    };
  }
  const menuId = asText(query.menu_id || query.menuId || (subject === 'menu' ? query.id : ''));
  if (menuId) {
    return { op: 'menu', menu_id: menuId, ...contractRouteParams(query) };
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
          editFields: collectRelationEditFields(config),
          blockType: asText(config.blockType),
          valueType: asText(config.valueType || config.type || widget.valueType || widget.value_type),
          optionDomain: widgetState.domain || widgetState.domain_raw || config.domain || config.domain_raw || widget.domain || widget.domain_raw,
          optionDomainRaw: asText(widgetState.domain_raw || widgetState.domainRaw || config.domain_raw || config.domainRaw || widget.domain_raw || widget.domainRaw),
          optionContextRaw: asText(widgetState.context_raw || widgetState.contextRaw || config.context_raw || config.contextRaw || widget.context_raw || widget.contextRaw),
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
    const fieldName = asText(linePatch.dataKey || linePatch.data_key || linePatch.field || linePatch.relation_field || linePatch.fieldCode);
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
        tracePolicy: asDict(row.tracePolicy || row.trace_policy),
        refreshMode: normalizeRefreshMode(row.refreshMode),
        targetScope: normalizeActionTargetScope(row.targetScope || row.target_scope || asDict(row.target).targetScope || asDict(row.target).target_scope),
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
      const editFields = resolveRelationEditFields(widget, dataKey, dataMeta, rows);
      return {
        widgetId: widget.widgetId,
        fieldCode: widget.fieldCode,
        dataKey,
        label: widget.label,
        rowCount: rows.length,
        total,
        moreCount: Math.max(0, total - visibleRows.length),
        canLoadMore: Boolean(dataSource && total > rows.length),
        editFields,
        rows: visibleRows.map((row, index) => ({
          key: relationRowKey(row, widget.widgetId, index),
          rowId: asText(row.id),
          rowKey: asText(row.row_key || row.key || row.virtual_id || row.__row_key),
          summary: formatRelationRow(row, summaryFields),
          raw: row,
        })),
      };
    })
    .filter((block) => block.rowCount > 0 || block.editFields.length > 0 || !isPageReadonly.value);
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

function collectRelationEditFields(config: Dict): string[] {
  return [
    ...fieldNamesFromList(config.editFields || config.edit_fields),
    ...fieldNamesFromList(config.formFields || config.form_fields),
    ...fieldNamesFromList(config.inlineFields || config.inline_fields),
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

function resolveRelationEditFields(widget: ContractWidget, dataKey: string, dataMeta: Dict, rows: Dict[]): string[] {
  const meta = asDict(dataMeta[dataKey] || dataMeta[widget.fieldCode] || dataMeta[widget.widgetId]);
  const fromMeta = [
    ...fieldNamesFromList(meta.editFields || meta.edit_fields),
    ...fieldNamesFromList(meta.formFields || meta.form_fields),
    ...fieldNamesFromList(meta.columns || meta.fields),
  ];
  const fromRows = rows.flatMap((row) => Object.keys(row))
    .filter((field) => field && !field.startsWith('__') && !['id', 'row_key', 'key', 'virtual_id'].includes(field));
  return [
    ...widget.editFields,
    ...fromMeta,
    ...widget.summaryFields,
    ...fromRows,
  ].filter((field, index, all) => field && all.indexOf(field) === index).slice(0, 8);
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

function relationRowKey(row: Dict, widgetId: string, index: number): string {
  return asText(row.id || row.row_key || row.key || row.virtual_id || row.__row_key, `${widgetId}.${index}`);
}

async function removeRelationRow(block: RelationBlock, row: RelationDisplayRow) {
  const confirmed = await confirmRelationRowRemove(block);
  if (!confirmed) return;
  applyUnifiedPagePatchV2({
    updateType: 'partial',
    dataPatch: {
      relationRows: {
        line_patches: [{
          field: block.fieldCode,
          dataKey: block.dataKey,
          row_id: row.rowId || undefined,
          row_key: row.rowKey || row.key,
          row_state: 'delete',
          command_hint: ['unlink'],
        }],
      },
    },
  });
  pushWarningMessages([`${block.label} 行已标记移除，保存后生效`]);
}

function openCreateRelationRow(block: RelationBlock) {
  const values = relationEditorInitialValues(block, null);
  relationEditor.value = {
    visible: true,
    mode: 'create',
    block,
    row: null,
    values,
  };
}

function editRelationRow(block: RelationBlock, row: RelationDisplayRow) {
  const values = relationEditorInitialValues(block, row);
  relationEditor.value = {
    visible: true,
    mode: 'edit',
    block,
    row,
    values,
  };
}

function closeRelationEditor() {
  relationEditor.value = {
    visible: false,
    mode: 'create',
    block: null,
    row: null,
    values: {},
  };
}

function relationEditorInitialValues(block: RelationBlock, row: RelationDisplayRow | null): Dict {
  const raw = row ? asDict(row.raw) : {};
  const fields = (block.editFields.length ? block.editFields : Object.keys(raw)).length
    ? (block.editFields.length ? block.editFields : Object.keys(raw))
    : ['name'];
  return fields
    .filter((field) => field && !field.startsWith('__') && !['id', 'row_key', 'key', 'virtual_id'].includes(field))
    .reduce<Dict>((acc, field) => {
      acc[field] = raw[field] ?? '';
      return acc;
    }, {});
}

function handleRelationEditorInput(field: string, event: unknown) {
  const detail = asDict(asDict(event).detail);
  relationEditor.value = {
    ...relationEditor.value,
    values: {
      ...relationEditor.value.values,
      [field]: detail.value,
    },
  };
}

function saveRelationEditor() {
  const block = relationEditor.value.block;
  if (!block) return;
  const row = relationEditor.value.row;
  const mode = relationEditor.value.mode;
  const rowKey = row?.rowKey || row?.key || `mobile-new-${Date.now()}`;
  applyUnifiedPagePatchV2({
    updateType: 'partial',
    dataPatch: {
      relationRows: {
        line_patches: [{
          field: block.fieldCode,
          dataKey: block.dataKey,
          row_id: mode === 'edit' ? row?.rowId || undefined : undefined,
          row_key: rowKey,
          row_state: mode === 'create' ? 'create' : 'update',
          command_hint: [mode === 'create' ? 'create' : 'update'],
          patch: { ...relationEditor.value.values },
        }],
      },
    },
  });
  pushWarningMessages([`${block.label} 行已${mode === 'create' ? '新增' : '更新'}，保存后生效`]);
  closeRelationEditor();
}

function confirmRelationRowRemove(block: RelationBlock): Promise<boolean> {
  return new Promise((resolve) => {
    uni.showModal({
      title: '确认移除',
      content: `移除 ${block.label} 中的该行？`,
      confirmColor: '#d14343',
      success: (result) => resolve(Boolean(result.confirm)),
      fail: () => resolve(false),
    });
  });
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
  return ['input', 'number', 'date', 'datetime'].includes(type) || component.includes('input') || component.includes('textarea');
}

function isBooleanField(field: ContractWidget): boolean {
  if (isListSurface.value || isPageReadonly.value || field.readonly || field.disabled || !field.fieldCode) return false;
  const type = `${field.widgetType} ${field.componentKey} ${field.valueType}`.toLowerCase();
  return type.includes('boolean') || type.includes('switch') || type.includes('checkbox');
}

function isSelectionField(field: ContractWidget): boolean {
  if (isListSurface.value || isPageReadonly.value || field.readonly || field.disabled || !field.fieldCode) return false;
  const type = `${field.widgetType} ${field.componentKey} ${field.valueType}`.toLowerCase();
  return Boolean(selectionOptions(field).length) && (type.includes('select') || type.includes('selection') || type.includes('radio'));
}

function isRemoteSelectionField(field: ContractWidget): boolean {
  if (isListSurface.value || isPageReadonly.value || field.readonly || field.disabled || !field.fieldCode) return false;
  const type = `${field.widgetType} ${field.componentKey} ${field.valueType}`.toLowerCase();
  return !selectionOptions(field).length && Boolean(resolveFieldOptionDataSource(field)) && (type.includes('select') || type.includes('selection') || type.includes('radio'));
}

function isMany2OneField(field: ContractWidget): boolean {
  if (isListSurface.value || isPageReadonly.value || field.readonly || field.disabled || !field.fieldCode) return false;
  const type = `${field.widgetType} ${field.componentKey} ${field.valueType}`.toLowerCase();
  return Boolean(many2OneOptions(field).length) && (type.includes('many2one') || type.includes('select.remote'));
}

function isRemoteSearchableMany2OneField(field: ContractWidget): boolean {
  if (isListSurface.value || isPageReadonly.value || field.readonly || field.disabled || !field.fieldCode) return false;
  const type = `${field.widgetType} ${field.componentKey} ${field.valueType}`.toLowerCase();
  return Boolean(resolveFieldOptionDataSource(field)) && (type.includes('many2one') || type.includes('select.remote'));
}

function isRemoteMany2OneField(field: ContractWidget): boolean {
  if (isListSurface.value || isPageReadonly.value || field.readonly || field.disabled || !field.fieldCode) return false;
  const type = `${field.widgetType} ${field.componentKey} ${field.valueType}`.toLowerCase();
  return !many2OneOptions(field).length && Boolean(resolveFieldOptionDataSource(field)) && (type.includes('many2one') || type.includes('select.remote'));
}

function isDateField(field: ContractWidget): boolean {
  if (isListSurface.value || isPageReadonly.value || field.readonly || field.disabled || !field.fieldCode) return false;
  const type = `${field.widgetType} ${field.componentKey} ${field.valueType}`.toLowerCase();
  return type.includes('date') && !type.includes('datetime');
}

function isDateTimeField(field: ContractWidget): boolean {
  if (isListSurface.value || isPageReadonly.value || field.readonly || field.disabled || !field.fieldCode) return false;
  const type = `${field.widgetType} ${field.componentKey} ${field.valueType}`.toLowerCase();
  return type.includes('datetime');
}

function editableInputType(field: ContractWidget): string {
  const type = `${field.widgetType} ${field.componentKey} ${field.valueType}`.toLowerCase();
  if (type.includes('number') || type.includes('integer') || type.includes('float') || type.includes('monetary')) return 'digit';
  return 'text';
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
  setEditableFieldValue(field, normalizeEditableValue(field, detail.value));
}

function handleBooleanChange(field: ContractWidget, event: unknown) {
  setEditableFieldValue(field, Boolean(asDict(asDict(event).detail).value));
}

function handleSelectionChange(field: ContractWidget, event: unknown) {
  const index = Number(asDict(asDict(event).detail).value);
  const option = selectionOptions(field)[Number.isFinite(index) ? index : -1];
  if (!option) return;
  setEditableFieldValue(field, option.value);
}

function handleMany2OneChange(field: ContractWidget, event: unknown) {
  const index = Number(asDict(asDict(event).detail).value);
  const option = many2OneOptions(field)[Number.isFinite(index) ? index : -1];
  if (!option) return;
  setEditableFieldValue(field, [option.value, option.label]);
}

function handleOptionSearchInput(field: ContractWidget, event: unknown) {
  const detail = asDict(asDict(event).detail);
  optionSearchText.value = {
    ...optionSearchText.value,
    [fieldOptionKey(field)]: asText(detail.value),
  };
}

function handleDateChange(field: ContractWidget, event: unknown) {
  const value = asText(asDict(asDict(event).detail).value);
  if (value) setEditableFieldValue(field, value);
}

function handleDateTimeDateChange(field: ContractWidget, event: unknown) {
  const value = asText(asDict(asDict(event).detail).value);
  if (value) setEditableFieldValue(field, combineDateTimeValue(value, timePickerValue(records.value[0]?.[field.fieldCode])));
}

function handleDateTimeTimeChange(field: ContractWidget, event: unknown) {
  const value = asText(asDict(asDict(event).detail).value);
  if (value) setEditableFieldValue(field, combineDateTimeValue(datePickerValue(records.value[0]?.[field.fieldCode]), value));
}

function setEditableFieldValue(field: ContractWidget, value: unknown) {
  if (!records.value.length || !field.fieldCode) return;
  records.value = [
    {
      ...records.value[0],
      [field.fieldCode]: value,
    },
    ...records.value.slice(1),
  ];
  scheduleFieldAction(field, 'change');
}

function normalizeEditableValue(field: ContractWidget, value: unknown): unknown {
  const type = `${field.widgetType} ${field.componentKey} ${field.valueType}`.toLowerCase();
  if (!type.includes('number') && !type.includes('integer') && !type.includes('float') && !type.includes('monetary')) return value;
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : value;
}

function datePickerValue(value: unknown): string {
  const text = formatEditableValue(value);
  const match = text.match(/\d{4}-\d{2}-\d{2}/);
  return match ? match[0] : '';
}

function timePickerValue(value: unknown): string {
  const text = formatEditableValue(value);
  const match = text.match(/\d{2}:\d{2}/);
  return match ? match[0] : '00:00';
}

function combineDateTimeValue(dateValue: string, timeValue: string): string {
  const datePart = dateValue || new Date().toISOString().slice(0, 10);
  const timePart = timeValue || '00:00';
  return `${datePart} ${timePart}:00`;
}

function selectionOptions(field: ContractWidget): SelectOption[] {
  const dictData = asDict(asDict(contract.value?.dataContract).dictData);
  const dictKey = asText(field.dictKey, field.fieldCode);
  return asList(dictData[dictKey]).map((item) => {
    const row = asDict(item);
    return {
      value: row.value ?? row.key ?? row.id,
      label: asText(row.label || row.name || row.display_name || row.value || row.key || row.id),
    };
  }).filter((item) => item.label);
}

function selectionIndex(field: ContractWidget, value: unknown): number {
  const rawText = asText(Array.isArray(value) ? value[0] : value);
  const index = selectionOptions(field).findIndex((item) => asText(item.value) === rawText);
  return index >= 0 ? index : 0;
}

function many2OneOptions(field: ContractWidget): SelectOption[] {
  return selectionOptions(field);
}

function many2OneIndex(field: ContractWidget, value: unknown): number {
  return selectionIndex(field, value);
}

function fieldOptionKey(field: ContractWidget): string {
  return asText(field.dictKey, field.fieldCode || field.widgetId);
}

function resolveFieldOptionDataSource(field: ContractWidget): Dict | null {
  const dataSources = asDict(asDict(contract.value?.dataContract).dataSource);
  const key = fieldOptionKey(field);
  const source = asDict(dataSources[key] || dataSources[field.fieldCode] || dataSources[field.widgetId]);
  return Object.keys(source).length ? source : null;
}

async function loadMany2OneOptions(field: ContractWidget) {
  await loadFieldOptions(field);
}

async function loadFieldOptions(field: ContractWidget) {
  const runtime = resolveRuntimeEndpoint();
  const dataSource = resolveFieldOptionDataSource(field);
  const sourceIntent = asText(dataSource?.intent || dataSource?.query || dataSource?.provider, 'api.data');
  const sourceParams = asDict(dataSource?.params);
  const model = asText(sourceParams.model);
  if (!runtime || !contract.value || !model) {
    uni.showToast({ title: '当前字段缺少选项数据源', icon: 'none' });
    return;
  }
  const key = fieldOptionKey(field);
  many2OneLoadingKey.value = key;
  try {
    const response = await requestIntent(runtime.endpoint, runtime.token, {
      intent: sourceIntent,
      params: {
        ...sourceParams,
        op: asText(sourceParams.op, 'list'),
        model,
        fields: asList(sourceParams.fields).length ? sourceParams.fields : ['id', 'display_name', 'name'],
        limit: Number(sourceParams.limit) || 20,
        offset: 0,
        dataKey: key,
        data_key: key,
        ...fieldOptionSearchParams(field),
        ...fieldOptionDomainParams(field, sourceParams),
        ...contractTraceParams(contract.value),
      },
    });
    mergeFieldOptions(field, asDict(response.data));
  } catch (err) {
    uni.showToast({ title: normalizeError(err, '选项加载失败').slice(0, 48), icon: 'none' });
  } finally {
    many2OneLoadingKey.value = '';
  }
}

function mergeMany2OneOptions(field: ContractWidget, data: Dict) {
  mergeFieldOptions(field, data);
}

function mergeFieldOptions(field: ContractWidget, data: Dict) {
  const key = fieldOptionKey(field);
  const dictRows = asList(asDict(data.dictData)[key]);
  const sourceRows = dictRows.length ? dictRows : asList(data.records || data.rows || data.items);
  const rows = sourceRows
    .map((item) => asDict(item))
    .map((row) => ({
      value: row.value ?? row.key ?? row.id,
      label: asText(row.label || row.display_name || row.name || row.value || row.key || row.id),
    }))
    .filter((row) => row.value !== undefined && row.label);
  if (!rows.length || !contract.value) return;
  const current = asDict(contract.value);
  const currentData = asDict(current.dataContract);
  const dictData = asDict(currentData.dictData);
  contract.value = {
    ...current,
    dataContract: {
      ...currentData,
      dictData: {
        ...dictData,
        [key]: rows,
      },
    },
  };
}

function fieldOptionDomainParams(field: ContractWidget, sourceParams: Dict): Dict {
  const params: Dict = {};
  const domainRaw = asText(field.optionDomainRaw || sourceParams.domain_raw || sourceParams.domainRaw);
  const contextRaw = asText(field.optionContextRaw || sourceParams.context_raw || sourceParams.contextRaw);
  if (domainRaw) params.domain_raw = domainRaw;
  if (contextRaw) params.context_raw = contextRaw;
  if (!domainRaw && field.optionDomain !== undefined) params.domain = field.optionDomain;
  return params;
}

function optionSearchValue(field: ContractWidget): string {
  return asText(optionSearchText.value[fieldOptionKey(field)]);
}

function fieldOptionSearchParams(field: ContractWidget): Dict {
  const keyword = optionSearchValue(field);
  if (!keyword || !isRemoteSearchableMany2OneField(field)) return {};
  return {
    search: keyword,
    query: keyword,
    name_search: keyword,
  };
}

function clearMany2OneOptionsByFieldCodes(fieldCodes: string[]) {
  clearFieldOptionsByFieldCodes(fieldCodes);
}

function clearFieldOptionsByFieldCodes(fieldCodes: string[]) {
  if (!contract.value || !fieldCodes.length) return;
  const keys = widgets.value
    .filter((field) => fieldCodes.includes(field.fieldCode))
    .map((field) => fieldOptionKey(field))
    .filter((key, index, all) => key && all.indexOf(key) === index);
  if (!keys.length) return;
  const current = asDict(contract.value);
  const currentData = asDict(current.dataContract);
  const dictData = { ...asDict(currentData.dictData) };
  keys.forEach((key) => {
    delete dictData[key];
  });
  contract.value = {
    ...current,
    dataContract: {
      ...currentData,
      dictData,
    },
  };
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
  const requestId = onchangeRequestId(action);
  try {
    const response = await requestIntent(runtime.endpoint, runtime.token, {
      intent: 'api.onchange',
      params: {
        action_id: action.actionId,
        source_widget_id: action.sourceWidgetId,
        trigger_type: action.triggerType,
        model: modelName.value,
        res_id: currentRecordId() || undefined,
        values: { ...currentRecord },
        changed_fields: [field.fieldCode],
        include_v2_patch: true,
        contract_version: contractVersion.value,
        request_id: requestId,
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

function onchangeRequestId(action: ContractAction): string {
  const existing = asText(contractMeta.value.requestId || contractMeta.value.request_id);
  if (existing) return existing;
  if (action.tracePolicy.required === true) return `mobile.${action.actionId}.${Date.now()}`;
  return '';
}

function resolveFieldAction(field: ContractWidget, triggerType: string): ContractAction | null {
  const candidates = [field.widgetId, field.fieldCode, `field.${field.fieldCode}`].filter(Boolean);
  return actions.value.find((action) => action.triggerType === triggerType && candidates.includes(action.sourceWidgetId)) || null;
}

function applyOnchangeDataPatch(response: Dict) {
  const data = asDict(response.data);
  const patch = asDict(data.patch);
  if (Object.keys(patch).length && records.value.length) {
    records.value = [{ ...records.value[0], ...patch }, ...records.value.slice(1)];
  }
  applyOnchangeModifiersPatch(data.modifiers_patch || data.modifiersPatch);
  applyOnchangeLinePatches(data.line_patches || data.linePatches);
}

function applyOnchangeModifiersPatch(raw: unknown) {
  const domainChangedFields: string[] = [];
  const rows = Object.entries(asDict(raw))
    .map(([fieldCode, modifiers]) => {
      const row = asDict(modifiers);
      const status: Dict = { widgetId: `field.${fieldCode}` };
      if ('readonly' in row) status.readonly = Boolean(row.readonly);
      if ('required' in row) status.required = Boolean(row.required);
      if ('invisible' in row) status.visible = !row.invisible;
      if ('domain' in row) {
        status.domain = row.domain;
        domainChangedFields.push(fieldCode);
      }
      if ('domain_raw' in row || 'domainRaw' in row) {
        status.domain_raw = row.domain_raw || row.domainRaw;
        domainChangedFields.push(fieldCode);
      }
      return status;
    })
    .filter((row) => Object.keys(row).length > 1);
  if (rows.length) applyUnifiedPagePatchV2({ statusPatch: { widgetStatus: rows } });
  clearFieldOptionsByFieldCodes(domainChangedFields);
}

function applyOnchangeLinePatches(raw: unknown) {
  const rows = asList(raw).map((item) => asDict(item)).filter((row) => Object.keys(row).length);
  if (rows.length) applyUnifiedPagePatchV2({ dataPatch: { relationRows: { line_patches: rows } } });
}

function isExecutableCommandAction(action: ContractAction): boolean {
  if (!['click', 'submit', 'confirm', 'delete', 'refresh', 'select'].includes(action.triggerType)) return false;
  if (action.intent === 'execute_button') return Boolean(asText(action.button.name || action.actionKey));
  if (isStandardFormAction(action)) return !isListSurface.value && Boolean(asText(action.actionKey || action.intent));
  if (action.intent === 'api.data') return true;
  if (action.intent === 'ui.contract') return hasContractTarget(action.target);
  return false;
}

function isStandardFormAction(action: ContractAction): boolean {
  return STANDARD_FORM_ACTIONS.includes(action.intent);
}

function hasContractTarget(target: Dict): boolean {
  return Boolean(asText(
    target.action_id
      || target.actionId
      || target.model
      || target.res_model
      || target.resModel
      || target.target_model
      || target.targetModel
      || target.scene_key
      || target.sceneKey,
  ));
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
  if (isStandardFormAction(action)) {
    await executeStandardFormAction(action);
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

async function executeStandardFormAction(action: ContractAction) {
  const runtime = resolveRuntimeEndpoint();
  const model = actionTargetModel(action);
  const resId = currentRecordId();
  if (!runtime || !contract.value || !model) {
    uni.showToast({ title: '当前动作缺少执行参数', icon: 'none' });
    return;
  }
  if (action.intent === 'record.delete' && (!resId || !(await confirmDestructiveAction(action)))) return;
  runningActionId.value = action.actionId;
  try {
    const response = await requestIntent(runtime.endpoint, runtime.token, {
      intent: action.intent,
      params: standardFormActionParams(action, model, resId),
    });
    const appliedPatch = applyResponseUnifiedPagePatch(response);
    showActionResponseFeedback(response);
    if (appliedPatch && normalizeRefreshMode(action.refreshMode) === 'none') return;
    await applyActionEffect(asDict(asDict(response.data).effect), action, runtime.endpoint, runtime.token);
  } catch (err) {
    uni.showToast({ title: normalizeError(err, '动作执行失败').slice(0, 48), icon: 'none' });
  } finally {
    runningActionId.value = '';
  }
}

function standardFormActionParams(action: ContractAction, model: string, resId: number): Dict {
  const params: Dict = {
    model,
    action_key: asText(action.actionKey, action.intent),
    context: {
      ...actionExecutionContext(action),
      ...contractTraceContext(contract.value),
    },
    ...contractTraceParams(contract.value),
  };
  if (resId) {
    params.res_id = resId;
    params.record_id = resId;
  }
  if (action.intent === 'form.save') {
    params.values = currentRecordValues();
    params.relationRows = currentRelationRows();
    params.relation_rows = currentRelationRows();
  }
  return params;
}

function currentRecordValues(): Dict {
  return records.value.length ? { ...asDict(records.value[0]) } : {};
}

function currentRelationRows(): Dict {
  return asDict(dataContract.value.relationRows);
}

function confirmDestructiveAction(action: ContractAction): Promise<boolean> {
  return new Promise((resolve) => {
    uni.showModal({
      title: '确认删除',
      content: action.label || '删除后不可恢复',
      confirmColor: '#d14343',
      success: (result) => resolve(Boolean(result.confirm)),
      fail: () => resolve(false),
    });
  });
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
  const warnings = collectResponseWarnings(response);
  if (warnings.length) pushWarningMessages(warnings);
  const warning = firstResponseWarning(response);
  const message = warning || asText(effect.message || result.message || data.message);
  if (message) uni.showToast({ title: message.slice(0, 48), icon: warning ? 'none' : 'success' });
}

function firstResponseWarning(response: Dict): string {
  return collectResponseWarnings(response)[0] || '';
}

function collectResponseWarnings(response: Dict): string[] {
  const data = asDict(response.data);
  const rows = [
    ...asList(response.warnings),
    ...asList(data.warnings),
    ...asList(data.warning ? [data.warning] : []),
  ];
  return rows
    .map((item) => {
      if (typeof item === 'string') return asText(item);
      const row = asDict(item);
      return asText(row.message || row.title || row.reason_code || row.reasonCode);
    })
    .filter((message, index, all) => message && all.indexOf(message) === index)
    .slice(0, 3);
}

function pushWarningMessages(messages: string[]) {
  const next = [...messages, ...warningMessages.value]
    .filter((message, index, all) => message && all.indexOf(message) === index)
    .slice(0, 4);
  warningMessages.value = next;
  if (warningTimer) clearTimeout(warningTimer);
  warningTimer = setTimeout(() => {
    warningMessages.value = [];
    warningTimer = null;
  }, 8000);
}

function clearWarningMessages() {
  warningMessages.value = [];
  if (warningTimer) {
    clearTimeout(warningTimer);
    warningTimer = null;
  }
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
  const targetScope = action ? normalizeActionTargetScope(action.targetScope) : '';
  if (targetScope === 'runtime' || targetScope === 'contract') {
    await loadContract();
    return;
  }
  if (targetScope === 'dataSource' || targetScope === 'data_source') {
    await loadRecords(endpoint, token, contract.value, false);
    return;
  }
  const targets = action ? actionRefreshTargets(action) : [];
  if (targets.length && needsFullContractRefresh(targets)) {
    await loadContract();
    return;
  }
  await loadRecords(endpoint, token, contract.value, false);
}

function normalizeActionTargetScope(value: unknown): string {
  const scope = asText(value).replace(/-/g, '_').toLowerCase();
  if (scope === 'datasource') return 'dataSource';
  if (scope === 'data_source') return 'data_source';
  if (scope === 'runtime') return 'runtime';
  if (scope === 'contract' || scope === 'page') return 'contract';
  return scope;
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

.warning-stack {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  margin-bottom: 22rpx;
}

.warning-stack__item {
  padding: 16rpx 18rpx;
  border: 1rpx solid #f0d28a;
  border-radius: 8rpx;
  background: #fff8e6;
  color: #7a4d05;
  font-size: 23rpx;
  line-height: 1.35;
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

.relation-block__head-actions {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 10rpx;
}

.relation-block__title,
.relation-block__count,
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

.relation-block__add,
.relation-block__edit {
  flex: 0 0 auto;
  height: 48rpx;
  margin: 0;
  border: 1rpx solid #bdd4ec;
  border-radius: 8rpx;
  background: #f2f8ff;
  color: #1f5f99;
  font-size: 21rpx;
  line-height: 48rpx;
}

.relation-block__add {
  width: 92rpx;
}

.relation-block__edit {
  width: 86rpx;
}

.relation-block__row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 8rpx 0;
  color: #344154;
  font-size: 22rpx;
  border-top: 1rpx solid #e8edf2;
}

.relation-block__summary {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.relation-block__remove {
  flex: 0 0 auto;
  width: 92rpx;
  height: 48rpx;
  margin: 0;
  border: 1rpx solid #efc6c6;
  border-radius: 8rpx;
  background: #fff7f7;
  color: #a33a3a;
  font-size: 21rpx;
  line-height: 48rpx;
}

.relation-editor {
  margin-top: 16rpx;
  padding: 16rpx;
  border: 1rpx solid #cdd8e4;
  border-radius: 8rpx;
  background: #ffffff;
}

.relation-editor__head,
.relation-editor__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.relation-editor__title {
  color: #17202a;
  font-size: 25rpx;
  font-weight: 700;
}

.relation-editor__close,
.relation-editor__cancel,
.relation-editor__save {
  height: 52rpx;
  margin: 0;
  border-radius: 8rpx;
  font-size: 22rpx;
  line-height: 52rpx;
}

.relation-editor__close,
.relation-editor__cancel {
  width: 104rpx;
  border: 1rpx solid #d8e0e8;
  background: #ffffff;
  color: #344154;
}

.relation-editor__save {
  width: 148rpx;
  border: 1rpx solid #1f5f99;
  background: #1f5f99;
  color: #ffffff;
}

.relation-editor__body {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin: 16rpx 0;
}

.relation-editor__field {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.relation-editor__label {
  flex: 0 0 170rpx;
  min-width: 0;
  color: #5d7188;
  font-size: 22rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.relation-editor__input {
  flex: 1;
  min-width: 0;
  height: 58rpx;
  box-sizing: border-box;
  padding: 0 14rpx;
  border: 1rpx solid #d8e0e8;
  border-radius: 8rpx;
  background: #ffffff;
  color: #17202a;
  font-size: 23rpx;
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

.field-row__picker {
  min-width: 180rpx;
  max-width: 320rpx;
  height: 56rpx;
  padding: 0 14rpx;
  border: 1rpx solid #cfd8e3;
  border-radius: 8rpx;
  background: #fff;
  color: #17202a;
  font-size: 24rpx;
  line-height: 56rpx;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field-row__datetime {
  display: flex;
  flex: 0 0 auto;
  gap: 8rpx;
  justify-content: flex-end;
}

.field-row__remote {
  display: flex;
  flex: 1;
  min-width: 0;
  gap: 8rpx;
  justify-content: flex-end;
}

.field-row__search {
  flex: 1 1 120rpx;
  min-width: 110rpx;
  max-width: 180rpx;
  height: 56rpx;
  padding: 0 12rpx;
  border: 1rpx solid #cfd8e3;
  border-radius: 8rpx;
  background: #fff;
  color: #17202a;
  font-size: 23rpx;
  line-height: 56rpx;
}

.field-row__picker--remote {
  min-width: 150rpx;
  max-width: 190rpx;
}

.field-row__picker--datetime {
  min-width: 170rpx;
  max-width: 190rpx;
}

.field-row__picker--time {
  min-width: 120rpx;
  max-width: 130rpx;
}

.field-row__load {
  flex: 0 0 auto;
  min-width: 150rpx;
  height: 56rpx;
  padding: 0 16rpx;
  border: 1rpx solid #cfd8e3;
  border-radius: 8rpx;
  background: #fff;
  color: #245f9e;
  font-size: 23rpx;
  line-height: 56rpx;
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
