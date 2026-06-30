import type {
  ContractV2ActionRule,
  ContractV2ButtonStatus,
  ContractV2Container,
  ContractV2ContainerStatus,
  ContractV2Dictionary,
  ContractV2NormalizedStore,
  ContractV2Snapshot,
  ContractV2UnsupportedFeature,
  ContractV2Widget,
  ContractV2WidgetStatus,
} from './types';

export type ContractV2SourceContext = {
  context?: ContractV2Dictionary;
  domain?: unknown[];
  contextRaw?: string;
  domainRaw?: string;
  renderProfile?: string;
};

export type ContractV2FieldStatusByCode = Record<string, {
  visible?: boolean;
  readonly?: boolean;
  required?: boolean;
  disabled?: boolean;
  reasonCode?: string;
}>;

export type ContractV2ValueSource = {
  kind: 'none' | 'main_data' | 'primary';
  values: ContractV2Dictionary;
};

function walkContainers(containers: ContractV2Container[], visit: (container: ContractV2Container) => void): void {
  containers.forEach((container) => {
    visit(container);
    walkContainers(container.children, visit);
    walkContainers(container.pages || [], visit);
    walkContainers(container.tabs || [], visit);
    walkContainers(container.nodes || [], visit);
    walkContainers(container.items || [], visit);
  });
}

function indexBy<T>(rows: T[], readKey: (row: T) => string): Map<string, T> {
  const out = new Map<string, T>();
  rows.forEach((row) => {
    const key = readKey(row);
    if (key) out.set(key, row);
  });
  return out;
}

function collectUnsupported(): ContractV2UnsupportedFeature[] {
  return [];
}

function primaryDataSource(snapshot: ContractV2Snapshot): ContractV2Dictionary | null {
  const source = snapshot.dataContract.dataSource.primary;
  return source && Object.keys(source).length ? source : null;
}

function asDict(value: unknown): ContractV2Dictionary {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as ContractV2Dictionary : {};
}

function asList(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asText(value: unknown): string {
  return String(value || '').trim();
}

function spanValue(value: unknown): number {
  const numberValue = Number(value);
  return Number.isInteger(numberValue) && numberValue >= 1 && numberValue <= 24 ? numberValue : 24;
}

function synthesizeWidgetFromContainer(container: ContractV2Container): ContractV2Widget | null {
  const type = asText(container.type || container.containerType).toLowerCase();
  if (type !== 'field') return null;
  const fieldInfo = asDict(container.fieldInfo || container.field_info);
  const attributes = asDict(container.attributes);
  const fieldCode = asText(container.name || fieldInfo.name || attributes.name);
  if (!fieldCode) return null;
  const componentConfig = asDict(fieldInfo.componentConfig || fieldInfo.component_config || attributes.componentConfig || attributes.component_config);
  const fieldType = asText(fieldInfo.type || fieldInfo.ttype);
  const relation = asText(fieldInfo.relation);
  const relationEntry = asDict(fieldInfo.relationEntry || fieldInfo.relation_entry || componentConfig.relationEntry || componentConfig.relation_entry);
  const widgetOptions = asDict(fieldInfo.widgetOptions || fieldInfo.widget_options || fieldInfo.options || componentConfig.widgetOptions || componentConfig.widget_options);
  const mergedComponentConfig = {
    ...componentConfig,
    ...(fieldType && !asText(componentConfig.fieldType || componentConfig.field_type || componentConfig.ttype)
      ? { fieldType }
      : {}),
    ...(relation && !asText(componentConfig.relation) ? { relation } : {}),
    ...(Array.isArray(fieldInfo.selection) && !Array.isArray(componentConfig.selection) ? { selection: fieldInfo.selection } : {}),
    ...(Object.keys(relationEntry).length ? { relationEntry } : {}),
    ...(Object.keys(widgetOptions).length ? { widgetOptions } : {}),
  };
  return {
    widgetId: asText(attributes.widgetId || attributes.widget_id) || `field.${fieldCode}`,
    widgetType: asText(container.widget || fieldInfo.widget || fieldType || container.containerType) || 'display',
    fieldCode,
    label: asText(container.label || container.string || fieldInfo.label || fieldInfo.string) || fieldCode,
    span: spanValue(container.span || fieldInfo.span || attributes.span),
    componentKey: asText(fieldInfo.componentKey || fieldInfo.component_key || attributes.componentKey || attributes.component_key) || 'sc.display.text',
    capabilities: [],
    componentConfig: mergedComponentConfig,
    ...(fieldType ? { fieldType } : {}),
    ...(relation ? { relation } : {}),
  };
}

function collectWidgets(snapshot: ContractV2Snapshot): ContractV2Widget[] {
  const out: ContractV2Widget[] = [];
  const seen = new Set<string>();
  const pushWidget = (widget: ContractV2Widget | null) => {
    if (!widget || !widget.widgetId || seen.has(widget.widgetId)) return;
    seen.add(widget.widgetId);
    out.push(widget);
  };
  walkContainers(snapshot.layoutContract.containerTree, (container) => {
    container.widgetList.forEach(pushWidget);
    pushWidget(synthesizeWidgetFromContainer(container));
  });
  return out;
}

export function createContractV2Store(snapshot: ContractV2Snapshot): ContractV2NormalizedStore {
  const widgets = collectWidgets(snapshot);
  return {
    snapshot,
    widgetsById: indexBy<ContractV2Widget>(widgets, (widget) => widget.widgetId),
    widgetsByFieldCode: indexBy<ContractV2Widget>(widgets, (widget) => widget.fieldCode),
    actionsById: indexBy<ContractV2ActionRule>(snapshot.actionContract.actionRuleList, (action) => action.actionId),
    widgetStatusById: indexBy<ContractV2WidgetStatus>(snapshot.statusContract.widgetStatus, (status) => status.widgetId),
    buttonStatusById: indexBy<ContractV2ButtonStatus>(snapshot.statusContract.buttonStatus, (status) => status.btnId),
    containerStatusById: indexBy<ContractV2ContainerStatus>(snapshot.statusContract.containerStatus, (status) => status.containerId),
    primaryDataSource: primaryDataSource(snapshot),
    unsupported: collectUnsupported(),
  };
}

export function collectContractV2FieldStatusByCode(store: ContractV2NormalizedStore | null): ContractV2FieldStatusByCode {
  const out: ContractV2FieldStatusByCode = {};
  if (!store) return out;
  store.widgetStatusById.forEach((status, widgetId) => {
    const widget = store.widgetsById.get(widgetId);
    const fieldCode = String(widget?.fieldCode || '').trim();
    if (!fieldCode) return;
    out[fieldCode] = {
      ...(out[fieldCode] || {}),
      ...(typeof status.visible === 'boolean' ? { visible: status.visible } : {}),
      ...(typeof status.readonly === 'boolean' ? { readonly: status.readonly } : {}),
      ...(typeof status.required === 'boolean' ? { required: status.required } : {}),
      ...(typeof status.disabled === 'boolean' ? { disabled: status.disabled } : {}),
      ...(status.reasonCode ? { reasonCode: status.reasonCode } : {}),
    };
  });
  return out;
}

export function collectContractV2ButtonStatusById(store: ContractV2NormalizedStore | null): Record<string, ContractV2ButtonStatus> {
  const out: Record<string, ContractV2ButtonStatus> = {};
  if (!store) return out;
  store.buttonStatusById.forEach((status, btnId) => {
    out[btnId] = {
      btnId,
      ...(typeof status.visible === 'boolean' ? { visible: status.visible } : {}),
      ...(typeof status.disabled === 'boolean' ? { disabled: status.disabled } : {}),
      ...(status.reasonCode ? { reasonCode: status.reasonCode } : {}),
    };
  });
  return out;
}

export function resolveContractV2ContainerTree(store: ContractV2NormalizedStore | null): ContractV2Container[] {
  if (!store) return [];
  return store.snapshot.layoutContract.containerTree;
}

export function resolveContractV2FormStructureContract(store: ContractV2NormalizedStore | null): ContractV2Dictionary {
  if (!store) return {};
  return asDict(store.snapshot.formStructureContract);
}

export function resolveContractV2GlobalStatus(store: ContractV2NormalizedStore | null) {
  if (!store) return null;
  const row = store.snapshot.statusContract.globalStatus || {};
  if (!Object.keys(row).length) return null;
  return {
    ...(typeof row.pageVisible === 'boolean' ? { pageVisible: row.pageVisible } : {}),
    ...(asText(row.pageAuth) ? { pageAuth: asText(row.pageAuth) } : {}),
    ...(asText(row.reasonCode) ? { reasonCode: asText(row.reasonCode) } : {}),
  };
}

export function resolveContractV2MainData(store: ContractV2NormalizedStore | null): ContractV2Dictionary {
  if (!store) return {};
  return asDict(store.snapshot.dataContract.mainData);
}

export function resolveContractV2ValueSource(store: ContractV2NormalizedStore | null): ContractV2ValueSource {
  if (!store) return { kind: 'none', values: {} };
  const fieldCodes = Array.from(store.widgetsByFieldCode.keys());
  const coverage = (values: ContractV2Dictionary) => fieldCodes.filter((fieldCode) => (
    Object.prototype.hasOwnProperty.call(values, fieldCode)
  )).length;
  const mainData = resolveContractV2MainData(store);
  if (coverage(mainData) > 0) return { kind: 'main_data', values: mainData };
  const primary = store.primaryDataSource || {};
  if (coverage(primary) > 0) return { kind: 'primary', values: primary };
  if (Object.keys(mainData).length) return { kind: 'main_data', values: mainData };
  if (Object.keys(primary).length) return { kind: 'primary', values: primary };
  return { kind: 'none', values: {} };
}

export function resolveContractV2SourceContext(store: ContractV2NormalizedStore | null): ContractV2SourceContext {
  if (!store) return {};
  const dataMeta = asDict(store.snapshot.dataContract.dataMeta);
  const runtime = asDict(store.snapshot.runtimeContract);
  const source = asDict(dataMeta.sourceContext || dataMeta.source_context || runtime.sourceContext || runtime.source_context);
  if (!Object.keys(source).length) return {};
  const context = asDict(source.context);
  const domain = asList(source.domain);
  const contextRaw = asText(source.context_raw || source.contextRaw);
  const domainRaw = asText(source.domain_raw || source.domainRaw);
  const renderProfile = asText(source.renderProfile || source.render_profile).toLowerCase();
  return {
    ...(Object.keys(context).length ? { context } : {}),
    ...(domain.length ? { domain } : {}),
    ...(contextRaw ? { contextRaw } : {}),
    ...(domainRaw ? { domainRaw } : {}),
    ...(renderProfile ? { renderProfile } : {}),
  };
}
