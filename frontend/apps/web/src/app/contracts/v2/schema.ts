import type {
  ContractV2ActionContract,
  ContractV2ActionRule,
  ContractV2Auth,
  ContractV2ButtonStatus,
  ContractV2AdaptMode,
  ContractV2ClientType,
  ContractV2Container,
  ContractV2ContainerStatus,
  ContractV2DataContract,
  ContractV2DataMeta,
  ContractV2Dictionary,
  ContractV2DispatchMode,
  ContractV2FieldGroups,
  ContractV2GlobalStatus,
  ContractV2LayoutType,
  ContractV2LayoutContract,
  ContractV2Meta,
  ContractV2PageRenderMode,
  ContractV2PageInfo,
  ContractV2CachePolicy,
  ContractV2PatchOperation,
  ContractV2PatchStrategy,
  ContractV2SelectorStatus,
  ContractV2Snapshot,
  ContractV2StatusContract,
  ContractV2RefreshMode,
  ContractV2RenderStrategy,
  ContractV2RuntimeContract,
  ContractV2TargetScope,
  ContractV2TriggerType,
  ContractV2VisibleFields,
  ContractV2ViewType,
  ContractV2Widget,
  ContractV2WidgetStatus,
} from './types';

type DecodeIssue = {
  path: string;
  message: string;
};

export class ContractV2DecodeError extends Error {
  issues: DecodeIssue[];

  constructor(issues: DecodeIssue[]) {
    super(`invalid contract v2 snapshot: ${issues.map((issue) => `${issue.path} ${issue.message}`).join('; ')}`);
    this.name = 'ContractV2DecodeError';
    this.issues = issues;
  }
}

function isRecord(value: unknown): value is ContractV2Dictionary {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function asRecord(value: unknown): ContractV2Dictionary {
  return isRecord(value) ? value : {};
}

function asString(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => asString(item)).filter(Boolean) : [];
}

function optionalBoolean(value: unknown): boolean | undefined {
  return typeof value === 'boolean' ? value : undefined;
}

function requiredBoolean(source: ContractV2Dictionary, key: string, path: string, issues: DecodeIssue[], fallback: boolean): boolean {
  const value = source[key];
  if (typeof value === 'boolean') return value;
  issues.push({ path: `${path}.${key}`, message: 'must be a boolean' });
  return fallback;
}

function requiredString(source: ContractV2Dictionary, key: string, path: string, issues: DecodeIssue[]): string {
  const value = asString(source[key]);
  if (!value) {
    issues.push({ path: `${path}.${key}`, message: 'is required' });
  }
  return value;
}

function optionalString(source: ContractV2Dictionary, key: string): string | undefined {
  return asString(source[key]) || undefined;
}

function readAliasedObject(
  source: ContractV2Dictionary,
  key: string,
  aliases: string[],
  path: string,
  issues: DecodeIssue[],
): ContractV2Dictionary {
  const value = source[key] || aliases.map((alias) => source[alias]).find(isRecord);
  if (!isRecord(value)) {
    const aliasMessage = aliases.length ? `; aliases checked: ${aliases.join(', ')}` : '';
    issues.push({ path: `${path}.${key}`, message: `must be an object${aliasMessage}` });
    return {};
  }
  return value;
}

function decodeClientType(value: string, issues: DecodeIssue[]): ContractV2ClientType {
  if (value === 'web_pc' || value === 'wx_mini' || value === 'harmony_h5') {
    return value;
  }
  issues.push({ path: 'pageInfo.clientType', message: `unsupported client type ${value || '<empty>'}` });
  return 'web_pc';
}

function decodeViewType(value: string, path: string, issues: DecodeIssue[]): ContractV2ViewType {
  if (value === 'form' || value === 'list' || value === 'table' || value === 'kanban' || value === 'tree' || value === 'gantt' || value === 'combine') {
    return value;
  }
  issues.push({ path, message: `unsupported view type ${value || '<empty>'}` });
  return 'form';
}

function decodeLayoutType(value: string, path: string, issues: DecodeIssue[]): ContractV2LayoutType {
  if (value === 'form' || value === 'table' || value === 'kanban' || value === 'tree' || value === 'gantt' || value === 'combine') {
    return value;
  }
  issues.push({ path, message: `unsupported layout type ${value || '<empty>'}` });
  return 'form';
}

function decodeAdaptMode(value: string, path: string, issues: DecodeIssue[]): ContractV2AdaptMode {
  if (value === 'pc' || value === 'mobile') {
    return value;
  }
  issues.push({ path, message: `unsupported adapt mode ${value || '<empty>'}` });
  return 'pc';
}

function decodeTriggerType(value: string, path: string, issues: DecodeIssue[]): ContractV2TriggerType {
  if (value === 'change' || value === 'click' || value === 'select' || value === 'refresh' || value === 'add' || value === 'delete' || value === 'confirm' || value === 'submit' || value === 'blur' || value === 'focus') {
    return value;
  }
  issues.push({ path, message: `unsupported trigger type ${value || '<empty>'}` });
  return 'click';
}

function decodeDispatchMode(value: string, path: string, issues: DecodeIssue[]): ContractV2DispatchMode {
  if (value === 'local' || value === 'server' || value === 'serverDebounced' || value === 'serverBlocking') {
    return value;
  }
  issues.push({ path, message: `unsupported dispatch mode ${value || '<empty>'}` });
  return 'local';
}

function decodeTargetScope(value: string, path: string, issues: DecodeIssue[]): ContractV2TargetScope {
  if (value === 'widget' || value === 'container' || value === 'page' || value === 'dataSource' || value === 'runtime') {
    return value;
  }
  issues.push({ path, message: `unsupported target scope ${value || '<empty>'}` });
  return 'page';
}

function decodeRefreshMode(value: string, path: string, issues: DecodeIssue[]): ContractV2RefreshMode {
  if (value === 'none' || value === 'partial' || value === 'full') {
    return value;
  }
  issues.push({ path, message: `unsupported refresh mode ${value || '<empty>'}` });
  return 'none';
}

function decodeAuth(value: string, path: string, issues: DecodeIssue[]): ContractV2Auth | undefined {
  if (!value) return undefined;
  if (value === 'none' || value === 'read' || value === 'edit' || value === 'admin') {
    return value;
  }
  issues.push({ path, message: `unsupported auth ${value}` });
  return undefined;
}

function decodePageRenderMode(value: string, path: string, issues: DecodeIssue[]): ContractV2PageRenderMode {
  if (value === 'governed') {
    return value;
  }
  issues.push({ path, message: `unsupported render mode ${value || '<empty>'}` });
  return 'governed';
}

function decodePatchStrategy(value: string, path: string, issues: DecodeIssue[]): ContractV2PatchStrategy {
  if (value === 'incremental' || value === 'full') {
    return value;
  }
  issues.push({ path, message: `unsupported patch strategy ${value || '<empty>'}` });
  return 'incremental';
}

function decodeCachePolicy(value: string, path: string, issues: DecodeIssue[]): ContractV2CachePolicy {
  if (value === 'none' || value === 'etag' || value === 'snapshot') {
    return value;
  }
  issues.push({ path, message: `unsupported cache policy ${value || '<empty>'}` });
  return 'none';
}

function decodeRenderStrategy(value: string, path: string, issues: DecodeIssue[]): ContractV2RenderStrategy | undefined {
  if (!value) return undefined;
  if (value === 'sync' || value === 'scheduled' || value === 'virtualized') {
    return value;
  }
  issues.push({ path, message: `unsupported render strategy ${value}` });
  return undefined;
}

function decodePatchOperation(value: string, path: string, issues: DecodeIssue[]): ContractV2PatchOperation | null {
  if (value === 'replace' || value === 'merge' || value === 'append' || value === 'remove' || value === 'reorder' || value === 'invalidate') {
    return value;
  }
  issues.push({ path, message: `unsupported patch operation ${value || '<empty>'}` });
  return null;
}

function requiredRecord(source: ContractV2Dictionary, key: string, path: string, issues: DecodeIssue[]): ContractV2Dictionary {
  const value = source[key];
  if (isRecord(value)) return value;
  issues.push({ path: `${path}.${key}`, message: 'must be an object' });
  return {};
}

function requiredArray(source: ContractV2Dictionary, key: string, path: string, issues: DecodeIssue[]): unknown[] {
  const value = source[key];
  if (Array.isArray(value)) return value;
  issues.push({ path: `${path}.${key}`, message: 'must be an array' });
  return [];
}

function requiredIntegerInRange(
  source: ContractV2Dictionary,
  key: string,
  path: string,
  issues: DecodeIssue[],
  fallback: number,
): number {
  const value = Number(source[key]);
  if (Number.isInteger(value) && value >= 1 && value <= 24) return value;
  issues.push({ path: `${path}.${key}`, message: 'must be an integer between 1 and 24' });
  return fallback;
}

function decodePageInfo(source: ContractV2Dictionary, issues: DecodeIssue[]): ContractV2PageInfo {
  const contractVersion = requiredString(source, 'contractVersion', 'pageInfo', issues);
  if (!/^2\.\d+\.\d+$/.test(contractVersion)) {
    issues.push({ path: 'pageInfo.contractVersion', message: 'must be semantic version 2.x.y' });
  }
  return {
    pageId: requiredString(source, 'pageId', 'pageInfo', issues),
    sceneKey: requiredString(source, 'sceneKey', 'pageInfo', issues),
    pageName: requiredString(source, 'pageName', 'pageInfo', issues),
    model: requiredString(source, 'model', 'pageInfo', issues),
    viewType: decodeViewType(requiredString(source, 'viewType', 'pageInfo', issues), 'pageInfo.viewType', issues),
    layoutType: decodeLayoutType(requiredString(source, 'layoutType', 'pageInfo', issues), 'pageInfo.layoutType', issues),
    renderMode: decodePageRenderMode(requiredString(source, 'renderMode', 'pageInfo', issues), 'pageInfo.renderMode', issues),
    contractVersion,
    clientType: decodeClientType(requiredString(source, 'clientType', 'pageInfo', issues), issues),
  };
}

function decodeWidget(raw: unknown, path: string, issues: DecodeIssue[]): ContractV2Widget | null {
  if (!isRecord(raw)) {
    issues.push({ path, message: 'widget must be an object' });
    return null;
  }
  const componentConfig = requiredRecord(raw, 'componentConfig', path, issues);
  const fieldCode = requiredString(raw, 'fieldCode', path, issues);
  const widgetId = requiredString(raw, 'widgetId', path, issues);
  const widgetType = requiredString(raw, 'widgetType', path, issues);
  const componentKey = requiredString(raw, 'componentKey', path, issues);
  if (!widgetId || !fieldCode) return null;
  return {
    widgetId,
    widgetType,
    fieldCode,
    label: requiredString(raw, 'label', path, issues),
    span: requiredIntegerInRange(raw, 'span', path, issues, 24),
    componentKey,
    capabilities: asStringArray(raw.capabilities),
    componentConfig,
    ...(isRecord(raw.formStructureRole) ? { formStructureRole: raw.formStructureRole } : {}),
  };
}

function decodeContainer(raw: unknown, path: string, issues: DecodeIssue[]): ContractV2Container | null {
  if (!isRecord(raw)) {
    issues.push({ path, message: 'container must be an object' });
    return null;
  }
  const containerId = requiredString(raw, 'containerId', path, issues);
  const containerType = requiredString(raw, 'containerType', path, issues);
  if (!containerId || !containerType) return null;
  const children = requiredArray(raw, 'children', path, issues)
    .map((item, index) => decodeContainer(item, `${path}.children[${index}]`, issues))
    .filter((item): item is ContractV2Container => Boolean(item));
  const decodeNodeList = (key: 'pages' | 'tabs' | 'nodes' | 'items'): ContractV2Container[] => (
    Array.isArray(raw[key]) ? raw[key] : []
  )
    .map((item, index) => decodeContainer(item, `${path}.${key}[${index}]`, issues))
    .filter((item): item is ContractV2Container => Boolean(item));
  const widgetList = requiredArray(raw, 'widgetList', path, issues)
    .map((item, index) => decodeWidget(item, `${path}.widgetList[${index}]`, issues))
    .filter((item): item is ContractV2Widget => Boolean(item));
  const pages = decodeNodeList('pages');
  const tabs = decodeNodeList('tabs');
  const nodes = decodeNodeList('nodes');
  const items = decodeNodeList('items');
  const attributes = asRecord(raw.attributes);
  const fieldInfo = asRecord(raw.fieldInfo || raw.field_info);
  const action = asRecord(raw.action);
  const modifiers = asRecord(raw.modifiers);
  const formStructure = asRecord(raw.formStructure || raw.form_structure);
  const formStructureRole = asRecord(raw.formStructureRole || raw.form_structure_role);
  return {
    containerId,
    containerType,
    type: asString(raw.type) || containerType,
    ...(asString(raw.name) ? { name: asString(raw.name) } : {}),
    ...(asString(raw.string) ? { string: asString(raw.string) } : {}),
    ...(asString(raw.label) ? { label: asString(raw.label) } : {}),
    title: requiredString(raw, 'title', path, issues),
    span: requiredIntegerInRange(raw, 'span', path, issues, 24),
    ...(asString(raw.styleToken) ? { styleToken: asString(raw.styleToken) } : {}),
    ...(Number(raw.cols || raw.col) ? { cols: Number(raw.cols || raw.col) } : {}),
    ...(Number(raw.columns) ? { columns: Number(raw.columns) } : {}),
    ...(asString(raw.widget) ? { widget: asString(raw.widget) } : {}),
    ...(Object.keys(attributes).length ? { attributes } : {}),
    ...(Object.keys(fieldInfo).length ? { fieldInfo, field_info: fieldInfo } : {}),
    ...(asString(raw.buttonType || raw.button_type) ? { buttonType: asString(raw.buttonType || raw.button_type) } : {}),
    ...(Object.keys(action).length ? { action } : {}),
    ...(Object.keys(modifiers).length ? { modifiers } : {}),
    ...(Object.prototype.hasOwnProperty.call(raw, 'invisible') ? { invisible: raw.invisible } : {}),
    ...(Object.prototype.hasOwnProperty.call(raw, 'readonly') ? { readonly: raw.readonly } : {}),
    ...(Object.prototype.hasOwnProperty.call(raw, 'required') ? { required: raw.required } : {}),
    ...(Object.keys(formStructure).length ? { formStructure } : {}),
    ...(Object.keys(formStructureRole).length ? { formStructureRole } : {}),
    children,
    ...(pages.length ? { pages } : {}),
    ...(tabs.length ? { tabs } : {}),
    ...(nodes.length ? { nodes } : {}),
    ...(items.length ? { items } : {}),
    widgetList,
  };
}

function decodeLayoutContract(source: ContractV2Dictionary, issues: DecodeIssue[]): ContractV2LayoutContract {
  const containerTreeRaw = Array.isArray(source.containerTree) ? source.containerTree : [];
  if (!Array.isArray(source.containerTree)) {
    issues.push({ path: 'layoutContract.containerTree', message: 'must be an array' });
  }
  const containerTree = containerTreeRaw
    .map((item, index) => decodeContainer(item, `layoutContract.containerTree[${index}]`, issues))
    .filter((item): item is ContractV2Container => Boolean(item));
  return {
    pageId: requiredString(source, 'pageId', 'layoutContract', issues),
    layoutType: decodeLayoutType(requiredString(source, 'layoutType', 'layoutContract', issues), 'layoutContract.layoutType', issues),
    adaptMode: decodeAdaptMode(requiredString(source, 'adaptMode', 'layoutContract', issues), 'layoutContract.adaptMode', issues),
    containerTree,
    layoutHints: requiredRecord(source, 'layoutHints', 'layoutContract', issues),
    componentRegistry: requiredRecord(source, 'componentRegistry', 'layoutContract', issues),
    ...(Object.keys(asRecord(source.listProfile)).length
      ? { listProfile: asRecord(source.listProfile) }
      : {}),
  };
}

function decodeActionRule(raw: unknown, path: string, issues: DecodeIssue[]): ContractV2ActionRule | null {
  if (!isRecord(raw)) {
    issues.push({ path, message: 'action rule must be an object' });
    return null;
  }
  const actionId = requiredString(raw, 'actionId', path, issues);
  if (!actionId) return null;
  const target = asRecord(raw.target);
  const button = asRecord(raw.button);
  const submitPolicy = asRecord(raw.submitPolicy);
  const tracePolicy = asRecord(raw.tracePolicy);
  return {
    actionId,
    triggerType: decodeTriggerType(requiredString(raw, 'triggerType', path, issues), `${path}.triggerType`, issues),
    sourceWidgetId: requiredString(raw, 'sourceWidgetId', path, issues),
    targetIds: asStringArray(raw.targetIds),
    dispatchMode: decodeDispatchMode(requiredString(raw, 'dispatchMode', path, issues), `${path}.dispatchMode`, issues),
    targetScope: decodeTargetScope(requiredString(raw, 'targetScope', path, issues), `${path}.targetScope`, issues),
    refreshMode: decodeRefreshMode(requiredString(raw, 'refreshMode', path, issues), `${path}.refreshMode`, issues),
    ...(optionalString(raw, 'actionKey') ? { actionKey: optionalString(raw, 'actionKey') } : {}),
    ...(optionalString(raw, 'label') ? { label: optionalString(raw, 'label') } : {}),
    ...(optionalString(raw, 'intent') ? { intent: optionalString(raw, 'intent') } : {}),
    ...(Object.keys(target).length ? { target } : {}),
    ...(Object.keys(button).length ? { button } : {}),
    ...(Object.keys(submitPolicy).length ? { submitPolicy } : {}),
    ...(Object.keys(tracePolicy).length ? { tracePolicy } : {}),
  };
}

function decodeActionContract(source: ContractV2Dictionary, issues: DecodeIssue[]): ContractV2ActionContract {
  const actionRuleListRaw = Array.isArray(source.actionRuleList) ? source.actionRuleList : [];
  if (!Array.isArray(source.actionRuleList)) {
    issues.push({ path: 'actionContract.actionRuleList', message: 'must be an array' });
  }
  const actionRuleList = actionRuleListRaw
    .map((item, index) => decodeActionRule(item, `actionContract.actionRuleList[${index}]`, issues))
    .filter((item): item is ContractV2ActionRule => Boolean(item));
  const dependencyGraphRaw = requiredRecord(source, 'dependencyGraph', 'actionContract', issues);
  const dependencyGraph = Object.entries(dependencyGraphRaw).reduce<Record<string, string[]>>((acc, [key, value]) => {
    acc[key] = asStringArray(value);
    return acc;
  }, {});
  return {
    actionRuleList,
    dependencyGraph,
    ...(Object.keys(asRecord(source.deletePolicy)).length
      ? { deletePolicy: asRecord(source.deletePolicy) }
      : {}),
    ...(Object.keys(asRecord(source.surfacePolicies)).length
      ? { surfacePolicies: asRecord(source.surfacePolicies) }
      : {}),
  };
}

function decodeRowsMap(value: unknown): Record<string, unknown[]> {
  const rows = asRecord(value);
  return Object.entries(rows).reduce<Record<string, unknown[]>>((acc, [key, item]) => {
    acc[key] = Array.isArray(item) ? item : [];
    return acc;
  }, {});
}

function decodeDataSources(value: unknown): Record<string, ContractV2Dictionary> {
  const rows = asRecord(value);
  return Object.entries(rows).reduce<Record<string, ContractV2Dictionary>>((acc, [key, item]) => {
    acc[key] = asRecord(item);
    return acc;
  }, {});
}

function decodeVisibleFields(value: unknown, path: string, issues: DecodeIssue[]): ContractV2VisibleFields | undefined {
  const row = asRecord(value);
  const fields = asStringArray(row.fields);
  if (!fields.length) {
    if (Object.keys(row).length) {
      issues.push({ path: `${path}.fields`, message: 'must be a non-empty string array' });
    }
    return undefined;
  }
  const sourceAuthority = asRecord(row.sourceAuthority);
  return {
    fields,
    ...(Object.keys(sourceAuthority).length ? { sourceAuthority } : {}),
  };
}

function decodeFieldGroups(value: unknown, path: string, issues: DecodeIssue[]): ContractV2FieldGroups | undefined {
  const row = asRecord(value);
  const rawGroups = Array.isArray(row.groups) ? row.groups : [];
  const groups = rawGroups
    .map((item) => asRecord(item))
    .filter((item) => Object.keys(item).length > 0);
  if (!groups.length) {
    if (Object.keys(row).length) {
      issues.push({ path: `${path}.groups`, message: 'must be a non-empty object array' });
    }
    return undefined;
  }
  const sourceAuthority = asRecord(row.sourceAuthority);
  return {
    groups,
    ...(Object.keys(sourceAuthority).length ? { sourceAuthority } : {}),
  };
}

function decodeDataMeta(value: unknown, issues: DecodeIssue[]): ContractV2DataMeta {
  const row = asRecord(value);
  const businessOperationProfile = asRecord(row.businessOperationProfile);
  const forbiddenKeys = [
    'business_operation_profile',
    'visible_fields',
    'field_groups',
    'legacy' + 'ContractProjection',
    'legacy_contract' + '_projection',
  ];
  forbiddenKeys.forEach((key) => {
    if (Object.prototype.hasOwnProperty.call(row, key)) {
      issues.push({ path: `dataContract.dataMeta.${key}`, message: 'is not allowed in strict V2 dataMeta' });
    }
  });
  const visibleFields = decodeVisibleFields(row.visibleFields, 'dataContract.dataMeta.visibleFields', issues);
  const fieldGroups = decodeFieldGroups(row.fieldGroups, 'dataContract.dataMeta.fieldGroups', issues);
  return {
    ...row,
    ...(Object.keys(businessOperationProfile).length ? { businessOperationProfile } : {}),
    ...(visibleFields ? { visibleFields } : {}),
    ...(fieldGroups ? { fieldGroups } : {}),
  };
}

function decodeDataContract(source: ContractV2Dictionary, issues: DecodeIssue[]): ContractV2DataContract {
  const treeData = decodeRowsMap(source.treeData);
  const ganttData = decodeRowsMap(source.ganttData);
  return {
    mainData: requiredRecord(source, 'mainData', 'dataContract', issues),
    tableRows: decodeRowsMap(requiredRecord(source, 'tableRows', 'dataContract', issues)),
    relationRows: decodeRowsMap(requiredRecord(source, 'relationRows', 'dataContract', issues)),
    dictData: requiredRecord(source, 'dictData', 'dataContract', issues),
    pagination: requiredRecord(source, 'pagination', 'dataContract', issues),
    dataSource: decodeDataSources(requiredRecord(source, 'dataSource', 'dataContract', issues)),
    dataMeta: decodeDataMeta(requiredRecord(source, 'dataMeta', 'dataContract', issues), issues),
    ...(Object.keys(treeData).length ? { treeData } : {}),
    ...(Object.keys(ganttData).length ? { ganttData } : {}),
  };
}

function decodeGlobalStatus(source: ContractV2Dictionary): ContractV2GlobalStatus {
  return {
    pageVisible: optionalBoolean(source.pageVisible),
    ...(optionalString(source, 'pageAuth') ? { pageAuth: optionalString(source, 'pageAuth') } : {}),
    ...(optionalString(source, 'reasonCode')
      ? { reasonCode: optionalString(source, 'reasonCode') }
      : {}),
  };
}

function decodeWidgetStatus(raw: unknown, path: string, issues: DecodeIssue[]): ContractV2WidgetStatus | null {
  if (!isRecord(raw)) return null;
  const widgetId = asString(raw.widgetId);
  if (!widgetId) return null;
  const auth = decodeAuth(asString(raw.auth), `${path}.auth`, issues);
  return {
    widgetId,
    visible: optionalBoolean(raw.visible),
    readonly: optionalBoolean(raw.readonly),
    required: optionalBoolean(raw.required),
    disabled: optionalBoolean(raw.disabled),
    ...(optionalString(raw, 'placeholder') ? { placeholder: optionalString(raw, 'placeholder') } : {}),
    ...(auth ? { auth } : {}),
    ...(optionalString(raw, 'reasonCode')
      ? { reasonCode: optionalString(raw, 'reasonCode') }
      : {}),
  };
}

function decodeButtonStatus(raw: unknown): ContractV2ButtonStatus | null {
  if (!isRecord(raw)) return null;
  const btnId = asString(raw.btnId);
  if (!btnId) return null;
  return {
    btnId,
    visible: optionalBoolean(raw.visible),
    disabled: optionalBoolean(raw.disabled),
    ...(optionalString(raw, 'reasonCode')
      ? { reasonCode: optionalString(raw, 'reasonCode') }
      : {}),
  };
}

function decodeContainerStatus(raw: unknown): ContractV2ContainerStatus | null {
  if (!isRecord(raw)) return null;
  const containerId = asString(raw.containerId);
  if (!containerId) return null;
  return {
    containerId,
    visible: optionalBoolean(raw.visible),
    disabled: optionalBoolean(raw.disabled),
    ...(optionalString(raw, 'reasonCode')
      ? { reasonCode: optionalString(raw, 'reasonCode') }
      : {}),
  };
}

function decodeSelectorStatus(raw: unknown): ContractV2SelectorStatus | null {
  if (!isRecord(raw)) return null;
  const selector = asString(raw.selector);
  if (!selector) return null;
  return {
    selector,
    visible: optionalBoolean(raw.visible),
    readonly: optionalBoolean(raw.readonly),
    required: optionalBoolean(raw.required),
    disabled: optionalBoolean(raw.disabled),
    ...(optionalString(raw, 'reasonCode')
      ? { reasonCode: optionalString(raw, 'reasonCode') }
      : {}),
  };
}

function decodeStatusContract(source: ContractV2Dictionary, issues: DecodeIssue[]): ContractV2StatusContract {
  return {
    globalStatus: decodeGlobalStatus(requiredRecord(source, 'globalStatus', 'statusContract', issues)),
    widgetStatus: requiredArray(source, 'widgetStatus', 'statusContract', issues)
      .map((item, index) => decodeWidgetStatus(item, `statusContract.widgetStatus[${index}]`, issues))
      .filter((item): item is ContractV2WidgetStatus => Boolean(item)),
    buttonStatus: requiredArray(source, 'buttonStatus', 'statusContract', issues)
      .map(decodeButtonStatus)
      .filter((item): item is ContractV2ButtonStatus => Boolean(item)),
    containerStatus: requiredArray(source, 'containerStatus', 'statusContract', issues)
      .map(decodeContainerStatus)
      .filter((item): item is ContractV2ContainerStatus => Boolean(item)),
    selectorStatus: requiredArray(source, 'selectorStatus', 'statusContract', issues)
      .map(decodeSelectorStatus)
      .filter((item): item is ContractV2SelectorStatus => Boolean(item)),
  };
}

function decodeRuntimeContract(source: ContractV2Dictionary, issues: DecodeIssue[]): ContractV2RuntimeContract {
  const renderStrategy = decodeRenderStrategy(asString(source.renderStrategy), 'runtimeContract.renderStrategy', issues);
  const patchOperations = Array.isArray(source.patchOperations)
    ? source.patchOperations
      .map((item, index) => decodePatchOperation(asString(item), `runtimeContract.patchOperations[${index}]`, issues))
      .filter((item): item is ContractV2PatchOperation => Boolean(item))
    : [];
  return {
    patchStrategy: decodePatchStrategy(requiredString(source, 'patchStrategy', 'runtimeContract', issues), 'runtimeContract.patchStrategy', issues),
    cachePolicy: decodeCachePolicy(requiredString(source, 'cachePolicy', 'runtimeContract', issues), 'runtimeContract.cachePolicy', issues),
    optimistic: requiredBoolean(source, 'optimistic', 'runtimeContract', issues, false),
    lazyContainer: asStringArray(source.lazyContainer),
    virtualization: requiredRecord(source, 'virtualization', 'runtimeContract', issues),
    retryPolicy: requiredRecord(source, 'retryPolicy', 'runtimeContract', issues),
    ...(renderStrategy ? { renderStrategy } : {}),
    ...(isRecord(source.hydration) ? { hydration: source.hydration } : {}),
    ...(patchOperations.length ? { patchOperations } : {}),
    ...(isRecord(source.tracePolicy) ? { tracePolicy: source.tracePolicy } : {}),
    ...(isRecord(source.complexityBudget) ? { complexityBudget: source.complexityBudget } : {}),
    ...(isRecord(source.aiEnvelope) ? { aiEnvelope: source.aiEnvelope } : {}),
  };
}

function decodeMeta(source: ContractV2Dictionary, issues: DecodeIssue[]): ContractV2Meta {
  return {
    etag: requiredString(source, 'etag', 'meta', issues),
    snapshotId: requiredString(source, 'snapshotId', 'meta', issues),
    traceId: requiredString(source, 'traceId', 'meta', issues),
    requestId: requiredString(source, 'requestId', 'meta', issues),
    sourceType: requiredString(source, 'sourceType', 'meta', issues),
  };
}

export function decodeContractV2Snapshot(value: unknown): ContractV2Snapshot {
  const root = asRecord(value);
  const issues: DecodeIssue[] = [];
  const pageInfo = decodePageInfo(readAliasedObject(root, 'pageInfo', [], '$', issues), issues);
  const layoutContract = decodeLayoutContract(readAliasedObject(root, 'layoutContract', [], '$', issues), issues);
  const statusContract = decodeStatusContract(readAliasedObject(root, 'statusContract', [], '$', issues), issues);
  const actionContract = decodeActionContract(readAliasedObject(root, 'actionContract', [], '$', issues), issues);
  const dataContract = decodeDataContract(readAliasedObject(root, 'dataContract', [], '$', issues), issues);
  const runtimeContract = decodeRuntimeContract(readAliasedObject(root, 'runtimeContract', [], '$', issues), issues);
  const meta = decodeMeta(readAliasedObject(root, 'meta', [], '$', issues), issues);
  if (issues.length) {
    throw new ContractV2DecodeError(issues);
  }
  return {
    pageInfo,
    layoutContract,
    statusContract,
    actionContract,
    dataContract,
    runtimeContract,
    meta,
    ...(isRecord(root.formStructureContract)
      ? { formStructureContract: asRecord(root.formStructureContract) }
      : {}),
  };
}
