import type {
  ContractV2ActionContract,
  ContractV2ActionRule,
  ContractV2ButtonStatus,
  ContractV2ClientType,
  ContractV2Container,
  ContractV2ContainerStatus,
  ContractV2DataContract,
  ContractV2DataMeta,
  ContractV2Dictionary,
  ContractV2FieldGroups,
  ContractV2GlobalStatus,
  ContractV2LayoutContract,
  ContractV2PageInfo,
  ContractV2SelectorStatus,
  ContractV2Snapshot,
  ContractV2StatusContract,
  ContractV2VisibleFields,
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

function requiredString(source: ContractV2Dictionary, key: string, path: string, issues: DecodeIssue[]): string {
  const value = asString(source[key]);
  if (!value) {
    issues.push({ path: `${path}.${key}`, message: 'is required' });
  }
  return value;
}

function requiredAliasedString(
  source: ContractV2Dictionary,
  key: string,
  aliases: string[],
  path: string,
  issues: DecodeIssue[],
): string {
  const value = asString(source[key]) || aliases.map((alias) => asString(source[alias])).find(Boolean) || '';
  if (!value) {
    issues.push({ path: `${path}.${key}`, message: `is required; aliases checked: ${aliases.join(', ')}` });
  }
  return value;
}

function optionalString(source: ContractV2Dictionary, key: string): string | undefined {
  return asString(source[key]) || undefined;
}

function optionalAliasedString(source: ContractV2Dictionary, key: string, aliases: string[]): string | undefined {
  return asString(source[key]) || aliases.map((alias) => asString(source[alias])).find(Boolean) || undefined;
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
    issues.push({ path: `${path}.${key}`, message: `must be an object; aliases checked: ${aliases.join(', ')}` });
    return {};
  }
  return value;
}

function aliasedRecord(source: ContractV2Dictionary, key: string, aliases: string[]): ContractV2Dictionary {
  return asRecord(source[key] || aliases.map((alias) => source[alias]).find(isRecord));
}

function aliasedArray(source: ContractV2Dictionary, key: string, aliases: string[]): unknown[] {
  const value = source[key] || aliases.map((alias) => source[alias]).find(Array.isArray);
  return Array.isArray(value) ? value : [];
}

function decodeClientType(value: string, issues: DecodeIssue[]): ContractV2ClientType {
  if (value === 'web_pc' || value === 'wx_mini' || value === 'harmony_h5') {
    return value;
  }
  issues.push({ path: 'pageInfo.clientType', message: `unsupported client type ${value || '<empty>'}` });
  return 'web_pc';
}

function decodePageInfo(source: ContractV2Dictionary, issues: DecodeIssue[]): ContractV2PageInfo {
  const contractVersion = requiredAliasedString(source, 'contractVersion', ['contract_version'], 'pageInfo', issues);
  if (!/^2\.\d+\.\d+(?:[-+].*)?$/.test(contractVersion)) {
    issues.push({ path: 'pageInfo.contractVersion', message: 'must be semantic version 2.x.y' });
  }
  return {
    pageId: requiredAliasedString(source, 'pageId', ['page_id'], 'pageInfo', issues),
    sceneKey: requiredAliasedString(source, 'sceneKey', ['scene_key'], 'pageInfo', issues),
    pageName: requiredAliasedString(source, 'pageName', ['page_name', 'title'], 'pageInfo', issues),
    model: requiredString(source, 'model', 'pageInfo', issues),
    viewType: requiredAliasedString(source, 'viewType', ['view_type'], 'pageInfo', issues),
    layoutType: requiredAliasedString(source, 'layoutType', ['layout_type'], 'pageInfo', issues),
    contractVersion,
    clientType: decodeClientType(requiredAliasedString(source, 'clientType', ['client_type'], 'pageInfo', issues), issues),
  };
}

function decodeWidget(raw: unknown, path: string, issues: DecodeIssue[]): ContractV2Widget | null {
  if (!isRecord(raw)) {
    issues.push({ path, message: 'widget must be an object' });
    return null;
  }
  const fieldInfo = asRecord(raw.fieldInfo || raw.field_info);
  const componentConfig = asRecord(raw.componentConfig || raw.component_config || fieldInfo.componentConfig || fieldInfo.component_config);
  const relationEntry = asRecord(fieldInfo.relationEntry || fieldInfo.relation_entry || componentConfig.relationEntry || componentConfig.relation_entry);
  const widgetOptions = asRecord(fieldInfo.widgetOptions || fieldInfo.widget_options || fieldInfo.options || componentConfig.widgetOptions || componentConfig.widget_options);
  const fieldCode = optionalAliasedString(raw, 'fieldCode', ['field_code', 'name', 'field']) || asString(fieldInfo.name);
  const widgetId = optionalAliasedString(raw, 'widgetId', ['widget_id', 'id']) || (fieldCode ? `field.${fieldCode}` : '');
  const widgetType = (
    optionalAliasedString(raw, 'widgetType', ['widget_type', 'widget', 'type'])
    || asString(fieldInfo.widget)
    || asString(fieldInfo.type)
    || asString(fieldInfo.ttype)
    || 'display'
  );
  const componentKey = (
    optionalAliasedString(raw, 'componentKey', ['component_key'])
    || asString(fieldInfo.componentKey)
    || asString(fieldInfo.component_key)
    || 'sc.display.text'
  );
  if (!widgetId || !fieldCode) return null;
  const mergedComponentConfig = {
    ...componentConfig,
    ...(Array.isArray(fieldInfo.selection) && !Array.isArray(componentConfig.selection) ? { selection: fieldInfo.selection } : {}),
    ...(Object.keys(relationEntry).length ? { relationEntry } : {}),
    ...(Object.keys(widgetOptions).length ? { widgetOptions } : {}),
  };
  return {
    widgetId,
    widgetType,
    fieldCode,
    label: optionalAliasedString(raw, 'label', ['string', 'title']) || asString(fieldInfo.label) || asString(fieldInfo.string) || fieldCode,
    componentKey,
    ...(Object.keys(mergedComponentConfig).length ? { componentConfig: mergedComponentConfig } : {}),
    ...(optionalAliasedString(raw, 'fieldType', ['field_type', 'ttype']) || asString(fieldInfo.type) || asString(fieldInfo.ttype)
      ? { fieldType: optionalAliasedString(raw, 'fieldType', ['field_type', 'ttype']) || asString(fieldInfo.type) || asString(fieldInfo.ttype) }
      : {}),
    ...(optionalString(raw, 'relation') || asString(fieldInfo.relation) ? { relation: optionalString(raw, 'relation') || asString(fieldInfo.relation) } : {}),
  };
}

function decodeContainer(raw: unknown, path: string, issues: DecodeIssue[]): ContractV2Container | null {
  if (!isRecord(raw)) {
    issues.push({ path, message: 'container must be an object' });
    return null;
  }
  const containerId = requiredAliasedString(raw, 'containerId', ['container_id', 'id', 'name'], path, issues);
  const containerType = requiredAliasedString(raw, 'containerType', ['container_type', 'type'], path, issues);
  if (!containerId || !containerType) return null;
  const children = (Array.isArray(raw.children) ? raw.children : [])
    .map((item, index) => decodeContainer(item, `${path}.children[${index}]`, issues))
    .filter((item): item is ContractV2Container => Boolean(item));
  const decodeNodeList = (key: 'pages' | 'tabs' | 'nodes' | 'items'): ContractV2Container[] => (
    Array.isArray(raw[key]) ? raw[key] : []
  )
    .map((item, index) => decodeContainer(item, `${path}.${key}[${index}]`, issues))
    .filter((item): item is ContractV2Container => Boolean(item));
  const widgetListRaw = Array.isArray(raw.widgetList)
    ? raw.widgetList
    : Array.isArray(raw.widget_list)
      ? raw.widget_list
      : Array.isArray(raw.widgets)
        ? raw.widgets
        : [];
  const widgetList = widgetListRaw
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
    title: asString(raw.title) || asString(raw.string) || asString(raw.label),
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
  const containerTreeRaw = aliasedArray(source, 'containerTree', ['container_tree', 'containerList', 'container_list']);
  if (!containerTreeRaw.length && !Array.isArray(source.containerTree) && !Array.isArray(source.container_tree)) {
    issues.push({ path: 'layoutContract.containerTree', message: 'must be an array; aliases checked: container_tree, containerList, container_list' });
  }
  const containerTree = containerTreeRaw
    .map((item, index) => decodeContainer(item, `layoutContract.containerTree[${index}]`, issues))
    .filter((item): item is ContractV2Container => Boolean(item));
  return {
    layoutType: requiredAliasedString(source, 'layoutType', ['layout_type'], 'layoutContract', issues),
    adaptMode: requiredAliasedString(source, 'adaptMode', ['adapt_mode'], 'layoutContract', issues),
    containerTree,
    componentRegistry: aliasedRecord(source, 'componentRegistry', ['component_registry']),
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
  const actionId = requiredAliasedString(raw, 'actionId', ['action_id', 'id', 'key'], path, issues);
  if (!actionId) return null;
  const target = asRecord(raw.target);
  const button = asRecord(raw.button);
  return {
    actionId,
    triggerType: requiredAliasedString(raw, 'triggerType', ['trigger_type'], path, issues),
    sourceWidgetId: requiredAliasedString(raw, 'sourceWidgetId', ['source_widget_id'], path, issues),
    targetIds: asStringArray(raw.targetIds || raw.target_ids),
    dispatchMode: requiredAliasedString(raw, 'dispatchMode', ['dispatch_mode'], path, issues),
    targetScope: requiredAliasedString(raw, 'targetScope', ['target_scope'], path, issues),
    refreshMode: requiredAliasedString(raw, 'refreshMode', ['refresh_mode'], path, issues),
    ...(optionalAliasedString(raw, 'actionKey', ['action_key', 'key']) ? { actionKey: optionalAliasedString(raw, 'actionKey', ['action_key', 'key']) } : {}),
    ...(optionalString(raw, 'label') ? { label: optionalString(raw, 'label') } : {}),
    ...(optionalString(raw, 'intent') ? { intent: optionalString(raw, 'intent') } : {}),
    ...(Object.keys(target).length ? { target } : {}),
    ...(Object.keys(button).length ? { button } : {}),
  };
}

function decodeActionContract(source: ContractV2Dictionary, issues: DecodeIssue[]): ContractV2ActionContract {
  const actionRuleListRaw = aliasedArray(source, 'actionRuleList', ['action_rule_list', 'actions']);
  if (!actionRuleListRaw.length && !Array.isArray(source.actionRuleList) && !Array.isArray(source.action_rule_list)) {
    issues.push({ path: 'actionContract.actionRuleList', message: 'must be an array; aliases checked: action_rule_list, actions' });
  }
  const actionRuleList = actionRuleListRaw
    .map((item, index) => decodeActionRule(item, `actionContract.actionRuleList[${index}]`, issues))
    .filter((item): item is ContractV2ActionRule => Boolean(item));
  const dependencyGraphRaw = aliasedRecord(source, 'dependencyGraph', ['dependency_graph']);
  const dependencyGraph = Object.entries(dependencyGraphRaw).reduce<Record<string, string[]>>((acc, [key, value]) => {
    acc[key] = asStringArray(value);
    return acc;
  }, {});
  return {
    actionRuleList,
    ...(Object.keys(dependencyGraph).length ? { dependencyGraph } : {}),
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

function decodeVisibleFields(value: unknown): ContractV2VisibleFields | undefined {
  const row = asRecord(value);
  const fields = Array.isArray(value)
    ? asStringArray(value)
    : asStringArray(row.fields || row.fieldNames || row.field_names);
  if (!fields.length) return undefined;
  const sourceAuthority = asRecord(row.sourceAuthority);
  return {
    fields,
    ...(Object.keys(sourceAuthority).length ? { sourceAuthority } : {}),
  };
}

function decodeFieldGroups(value: unknown): ContractV2FieldGroups | undefined {
  const row = asRecord(value);
  const rawGroups = Array.isArray(value)
    ? value
    : (Array.isArray(row.groups) ? row.groups : Array.isArray(row.items) ? row.items : []);
  const groups = rawGroups
    .map((item) => asRecord(item))
    .filter((item) => Object.keys(item).length > 0);
  if (!groups.length) return undefined;
  const sourceAuthority = asRecord(row.sourceAuthority);
  return {
    groups,
    ...(Object.keys(sourceAuthority).length ? { sourceAuthority } : {}),
  };
}

function decodeDataMeta(value: unknown): ContractV2DataMeta {
  const row = asRecord(value);
  const businessOperationProfile = asRecord(row.businessOperationProfile);
  const visibleFields = decodeVisibleFields(row.visibleFields);
  const fieldGroups = decodeFieldGroups(row.fieldGroups);
  return {
    ...row,
    ...(Object.keys(businessOperationProfile).length ? { businessOperationProfile } : {}),
    ...(visibleFields ? { visibleFields } : {}),
    ...(fieldGroups ? { fieldGroups } : {}),
  };
}

function decodeDataContract(source: ContractV2Dictionary): ContractV2DataContract {
  const treeData = decodeRowsMap(source.treeData || source.tree_data);
  const ganttData = decodeRowsMap(source.ganttData || source.gantt_data);
  return {
    mainData: aliasedRecord(source, 'mainData', ['main_data']),
    tableRows: decodeRowsMap(source.tableRows || source.table_rows),
    relationRows: decodeRowsMap(source.relationRows || source.relation_rows),
    dictData: aliasedRecord(source, 'dictData', ['dict_data']),
    pagination: asRecord(source.pagination),
    dataSource: decodeDataSources(source.dataSource || source.data_source),
    dataMeta: decodeDataMeta(source.dataMeta || source.data_meta),
    ...(Object.keys(treeData).length ? { treeData } : {}),
    ...(Object.keys(ganttData).length ? { ganttData } : {}),
  };
}

function decodeGlobalStatus(source: ContractV2Dictionary): ContractV2GlobalStatus {
  return {
    pageVisible: optionalBoolean(source.pageVisible) ?? optionalBoolean(source.page_visible),
    ...(optionalAliasedString(source, 'pageAuth', ['page_auth']) ? { pageAuth: optionalAliasedString(source, 'pageAuth', ['page_auth']) } : {}),
    ...(optionalString(source, 'reasonCode') || optionalString(source, 'reason_code')
      ? { reasonCode: optionalString(source, 'reasonCode') || optionalString(source, 'reason_code') }
      : {}),
  };
}

function decodeWidgetStatus(raw: unknown): ContractV2WidgetStatus | null {
  if (!isRecord(raw)) return null;
  const widgetId = asString(raw.widgetId) || asString(raw.widget_id);
  if (!widgetId) return null;
  return {
    widgetId,
    visible: optionalBoolean(raw.visible),
    readonly: optionalBoolean(raw.readonly),
    required: optionalBoolean(raw.required),
    disabled: optionalBoolean(raw.disabled),
    ...(optionalString(raw, 'reasonCode') || optionalString(raw, 'reason_code')
      ? { reasonCode: optionalString(raw, 'reasonCode') || optionalString(raw, 'reason_code') }
      : {}),
  };
}

function decodeButtonStatus(raw: unknown): ContractV2ButtonStatus | null {
  if (!isRecord(raw)) return null;
  const btnId = asString(raw.btnId) || asString(raw.btn_id);
  if (!btnId) return null;
  return {
    btnId,
    visible: optionalBoolean(raw.visible),
    disabled: optionalBoolean(raw.disabled),
    ...(optionalString(raw, 'reasonCode') || optionalString(raw, 'reason_code')
      ? { reasonCode: optionalString(raw, 'reasonCode') || optionalString(raw, 'reason_code') }
      : {}),
  };
}

function decodeContainerStatus(raw: unknown): ContractV2ContainerStatus | null {
  if (!isRecord(raw)) return null;
  const containerId = asString(raw.containerId) || asString(raw.container_id);
  if (!containerId) return null;
  return {
    containerId,
    visible: optionalBoolean(raw.visible),
    disabled: optionalBoolean(raw.disabled),
    ...(optionalString(raw, 'reasonCode') || optionalString(raw, 'reason_code')
      ? { reasonCode: optionalString(raw, 'reasonCode') || optionalString(raw, 'reason_code') }
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
    ...(optionalString(raw, 'reasonCode') || optionalString(raw, 'reason_code')
      ? { reasonCode: optionalString(raw, 'reasonCode') || optionalString(raw, 'reason_code') }
      : {}),
  };
}

function decodeStatusContract(source: ContractV2Dictionary): ContractV2StatusContract {
  return {
    globalStatus: decodeGlobalStatus(aliasedRecord(source, 'globalStatus', ['global_status'])),
    widgetStatus: aliasedArray(source, 'widgetStatus', ['widget_status'])
      .map(decodeWidgetStatus)
      .filter((item): item is ContractV2WidgetStatus => Boolean(item)),
    buttonStatus: aliasedArray(source, 'buttonStatus', ['button_status'])
      .map(decodeButtonStatus)
      .filter((item): item is ContractV2ButtonStatus => Boolean(item)),
    containerStatus: aliasedArray(source, 'containerStatus', ['container_status'])
      .map(decodeContainerStatus)
      .filter((item): item is ContractV2ContainerStatus => Boolean(item)),
    selectorStatus: aliasedArray(source, 'selectorStatus', ['selector_status'])
      .map(decodeSelectorStatus)
      .filter((item): item is ContractV2SelectorStatus => Boolean(item)),
  };
}

export function extractContractV2Candidate(value: unknown): unknown {
  const root = asRecord(value);
  const data = asRecord(root.data);
  const rawBody = asRecord(root.rawBody);
  return (
    root.unified_page_contract_v2 ||
    root.__unified_page_contract_v2 ||
    data.unified_page_contract_v2 ||
    data.__unified_page_contract_v2 ||
    rawBody.unified_page_contract_v2 ||
    rawBody.__unified_page_contract_v2 ||
    value
  );
}

export function decodeContractV2Snapshot(value: unknown): ContractV2Snapshot {
  const root = asRecord(extractContractV2Candidate(value));
  const issues: DecodeIssue[] = [];
  const pageInfo = decodePageInfo(readAliasedObject(root, 'pageInfo', ['page_info'], '$', issues), issues);
  const layoutContract = decodeLayoutContract(readAliasedObject(root, 'layoutContract', ['layout_contract'], '$', issues), issues);
  const actionContract = decodeActionContract(readAliasedObject(root, 'actionContract', ['action_contract'], '$', issues), issues);
  const dataContract = decodeDataContract(readAliasedObject(root, 'dataContract', ['data_contract'], '$', issues));
  const statusContract = decodeStatusContract(aliasedRecord(root, 'statusContract', ['status_contract']));
  if (issues.length) {
    throw new ContractV2DecodeError(issues);
  }
  return {
    pageInfo,
    layoutContract,
    statusContract,
    actionContract,
    dataContract,
    runtimeContract: aliasedRecord(root, 'runtimeContract', ['runtime_contract']),
    meta: asRecord(root.meta),
    ...(isRecord(root.formStructureContract)
      ? { formStructureContract: asRecord(root.formStructureContract) }
      : {}),
    ...(isRecord(root.searchContract) ? { searchContract: root.searchContract } : {}),
  };
}
