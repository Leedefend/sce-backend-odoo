import {
  isLitePreviewLegacyFallbackMode,
  type LitePreviewFallbackMode,
} from './unifiedPageContractLiteCompat';

export type LiteClientType = 'web_pc' | 'wx_mini' | 'harmony_h5';
export type LiteViewType = 'form' | 'tree' | 'list' | 'kanban' | 'search' | 'gantt' | 'popup' | 'combine';
export type LitePatchOperation = 'merge' | 'replace';

export interface UnifiedPageContractLite {
  pageInfo: {
    pageId: string;
    sceneKey: string;
    model: string;
    viewType: LiteViewType;
    clientType: LiteClientType;
    contractVersion: '2.0.0';
  };
  layoutContract: {
    layoutType: LiteViewType;
    containerList: LiteContainer[];
  };
  statusContract: {
    widgetStatus: LiteWidgetStatus[];
    buttonStatus: LiteButtonStatus[];
  };
  actionContract: {
    actionRuleList: LiteActionRule[];
  };
  dataContract: {
    mainData: Record<string, unknown>;
    relationData: Record<string, unknown>;
    dictData: Record<string, unknown>;
  };
  meta: {
    etag: string;
    traceId: string;
    semanticAdapter?: Record<string, unknown>;
  };
}

export interface LiteContainer {
  containerId: string;
  containerType: string;
  title: string;
  children: LiteContainer[];
  widgetList: LiteWidget[];
}

export interface LiteWidget {
  widgetId: string;
  widgetType: string;
  fieldCode: string;
  label: string;
  component: string;
  props: Record<string, unknown>;
}

export interface LiteWidgetStatus {
  widgetId: string;
  visible: boolean;
  readonly: boolean;
  required: boolean;
  disabled: boolean;
}

export interface LiteButtonStatus {
  btnId: string;
  visible: boolean;
  disabled: boolean;
}

export interface LiteActionRule {
  actionId: string;
  triggerType: string;
  sourceWidgetId: string;
  dispatchMode: 'server';
  refreshMode: 'partial' | 'full';
}

export interface UnifiedPageContractLitePatch {
  updateType: 'partial';
  operation: LitePatchOperation;
  statusPatch: Record<string, unknown>;
  dataPatch: Record<string, unknown>;
  layoutPatch: Record<string, unknown>;
}

export type LitePreviewEnvelope = {
  contractMode: 'lite_preview';
  contractVersion: '2.0.0';
  entryPoint: 'load_contract' | 'api_onchange';
  payloadType: 'lite_contract' | 'lite_patch';
  fallbackMode: LitePreviewFallbackMode;
  payload: unknown;
  meta?: Record<string, unknown>;
};

const TOP_LEVEL_KEYS = ['actionContract', 'dataContract', 'layoutContract', 'meta', 'pageInfo', 'statusContract'];

function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function hasOnlyKeys(value: Record<string, unknown>, keys: string[]): boolean {
  const allowed = new Set(keys);
  return Object.keys(value).every((key) => allowed.has(key)) && keys.every((key) => key in value);
}

function isString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function isBoolean(value: unknown): value is boolean {
  return typeof value === 'boolean';
}

function isRecordArray(value: unknown): value is Array<Record<string, unknown>> {
  return Array.isArray(value) && value.every(isObject);
}

export function isUnifiedPageContractLite(value: unknown): value is UnifiedPageContractLite {
  if (!isObject(value) || !hasOnlyKeys(value, TOP_LEVEL_KEYS)) return false;

  const pageInfo = value.pageInfo;
  if (!isObject(pageInfo)) return false;
  if (pageInfo.contractVersion !== '2.0.0') return false;
  if (!isString(pageInfo.pageId) || !isString(pageInfo.sceneKey) || !isString(pageInfo.model)) return false;
  if (!isString(pageInfo.viewType) || !isString(pageInfo.clientType)) return false;

  const layout = value.layoutContract;
  if (!isObject(layout) || !isString(layout.layoutType) || !Array.isArray(layout.containerList)) return false;

  const status = value.statusContract;
  if (!isObject(status) || !isRecordArray(status.widgetStatus) || !isRecordArray(status.buttonStatus)) return false;
  if (!status.widgetStatus.every((row) =>
    isString(row.widgetId) &&
    isBoolean(row.visible) &&
    isBoolean(row.readonly) &&
    isBoolean(row.required) &&
    isBoolean(row.disabled),
  )) return false;
  if (!status.buttonStatus.every((row) => isString(row.btnId) && isBoolean(row.visible) && isBoolean(row.disabled))) return false;

  const action = value.actionContract;
  if (!isObject(action) || !isRecordArray(action.actionRuleList)) return false;
  if (!action.actionRuleList.every((row) =>
    isString(row.actionId) &&
    isString(row.triggerType) &&
    isString(row.sourceWidgetId) &&
    row.dispatchMode === 'server' &&
    (row.refreshMode === 'partial' || row.refreshMode === 'full'),
  )) return false;

  const data = value.dataContract;
  if (!isObject(data) || !isObject(data.mainData) || !isObject(data.relationData) || !isObject(data.dictData)) return false;

  const meta = value.meta;
  return isObject(meta) && isString(meta.etag) && isString(meta.traceId);
}

export function extractLitePreviewEnvelope(value: unknown): LitePreviewEnvelope | null {
  if (!isObject(value)) return null;
  const preview = value.lite_preview;
  if (!isObject(preview)) return null;
  if (preview.contractMode !== 'lite_preview') return null;
  if (preview.contractVersion !== '2.0.0') return null;
  if (preview.entryPoint !== 'load_contract' && preview.entryPoint !== 'api_onchange') return null;
  if (preview.payloadType !== 'lite_contract' && preview.payloadType !== 'lite_patch') return null;
  if (!isLitePreviewLegacyFallbackMode(preview.fallbackMode)) return null;
  return preview as LitePreviewEnvelope;
}
