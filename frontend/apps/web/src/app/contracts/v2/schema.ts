import type {
  ContractV2ActionContract,
  ContractV2ActionRule,
  ContractV2ButtonStatus,
  ContractV2ClientType,
  ContractV2Container,
  ContractV2ContainerStatus,
  ContractV2DataContract,
  ContractV2Dictionary,
  ContractV2GlobalStatus,
  ContractV2LayoutContract,
  ContractV2PageInfo,
  ContractV2SelectorStatus,
  ContractV2Snapshot,
  ContractV2StatusContract,
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

function optionalString(source: ContractV2Dictionary, key: string): string | undefined {
  return asString(source[key]) || undefined;
}

function readObject(source: ContractV2Dictionary, key: string, path: string, issues: DecodeIssue[]): ContractV2Dictionary {
  const value = source[key];
  if (!isRecord(value)) {
    issues.push({ path: `${path}.${key}`, message: 'must be an object' });
    return {};
  }
  return value;
}

function readArray(source: ContractV2Dictionary, key: string, path: string, issues: DecodeIssue[]): unknown[] {
  const value = source[key];
  if (!Array.isArray(value)) {
    issues.push({ path: `${path}.${key}`, message: 'must be an array' });
    return [];
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

function decodePageInfo(source: ContractV2Dictionary, issues: DecodeIssue[]): ContractV2PageInfo {
  const contractVersion = requiredString(source, 'contractVersion', 'pageInfo', issues);
  if (!/^2\.\d+\.\d+(?:[-+].*)?$/.test(contractVersion)) {
    issues.push({ path: 'pageInfo.contractVersion', message: 'must be semantic version 2.x.y' });
  }
  return {
    pageId: requiredString(source, 'pageId', 'pageInfo', issues),
    sceneKey: requiredString(source, 'sceneKey', 'pageInfo', issues),
    pageName: requiredString(source, 'pageName', 'pageInfo', issues),
    model: requiredString(source, 'model', 'pageInfo', issues),
    viewType: requiredString(source, 'viewType', 'pageInfo', issues),
    layoutType: requiredString(source, 'layoutType', 'pageInfo', issues),
    contractVersion,
    clientType: decodeClientType(requiredString(source, 'clientType', 'pageInfo', issues), issues),
  };
}

function decodeWidget(raw: unknown, path: string, issues: DecodeIssue[]): ContractV2Widget | null {
  if (!isRecord(raw)) {
    issues.push({ path, message: 'widget must be an object' });
    return null;
  }
  const widgetId = requiredString(raw, 'widgetId', path, issues);
  const fieldCode = requiredString(raw, 'fieldCode', path, issues);
  const widgetType = requiredString(raw, 'widgetType', path, issues);
  const componentKey = requiredString(raw, 'componentKey', path, issues);
  if (!widgetId || !fieldCode || !widgetType || !componentKey) return null;
  const componentConfig = asRecord(raw.componentConfig);
  return {
    widgetId,
    widgetType,
    fieldCode,
    label: requiredString(raw, 'label', path, issues),
    componentKey,
    ...(Object.keys(componentConfig).length ? { componentConfig } : {}),
    ...(optionalString(raw, 'fieldType') ? { fieldType: optionalString(raw, 'fieldType') } : {}),
    ...(optionalString(raw, 'relation') ? { relation: optionalString(raw, 'relation') } : {}),
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
  const children = (Array.isArray(raw.children) ? raw.children : [])
    .map((item, index) => decodeContainer(item, `${path}.children[${index}]`, issues))
    .filter((item): item is ContractV2Container => Boolean(item));
  const widgetList = (Array.isArray(raw.widgetList) ? raw.widgetList : [])
    .map((item, index) => decodeWidget(item, `${path}.widgetList[${index}]`, issues))
    .filter((item): item is ContractV2Widget => Boolean(item));
  return {
    containerId,
    containerType,
    title: asString(raw.title),
    children,
    widgetList,
  };
}

function decodeLayoutContract(source: ContractV2Dictionary, issues: DecodeIssue[]): ContractV2LayoutContract {
  const containerTree = readArray(source, 'containerTree', 'layoutContract', issues)
    .map((item, index) => decodeContainer(item, `layoutContract.containerTree[${index}]`, issues))
    .filter((item): item is ContractV2Container => Boolean(item));
  return {
    layoutType: requiredString(source, 'layoutType', 'layoutContract', issues),
    adaptMode: requiredString(source, 'adaptMode', 'layoutContract', issues),
    containerTree,
    componentRegistry: asRecord(source.componentRegistry),
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
  return {
    actionId,
    triggerType: requiredString(raw, 'triggerType', path, issues),
    sourceWidgetId: requiredString(raw, 'sourceWidgetId', path, issues),
    targetIds: asStringArray(raw.targetIds),
    dispatchMode: requiredString(raw, 'dispatchMode', path, issues),
    targetScope: requiredString(raw, 'targetScope', path, issues),
    refreshMode: requiredString(raw, 'refreshMode', path, issues),
    ...(optionalString(raw, 'actionKey') ? { actionKey: optionalString(raw, 'actionKey') } : {}),
    ...(optionalString(raw, 'label') ? { label: optionalString(raw, 'label') } : {}),
    ...(optionalString(raw, 'intent') ? { intent: optionalString(raw, 'intent') } : {}),
    ...(Object.keys(target).length ? { target } : {}),
    ...(Object.keys(button).length ? { button } : {}),
  };
}

function decodeActionContract(source: ContractV2Dictionary, issues: DecodeIssue[]): ContractV2ActionContract {
  const actionRuleList = readArray(source, 'actionRuleList', 'actionContract', issues)
    .map((item, index) => decodeActionRule(item, `actionContract.actionRuleList[${index}]`, issues))
    .filter((item): item is ContractV2ActionRule => Boolean(item));
  const dependencyGraphRaw = asRecord(source.dependencyGraph);
  const dependencyGraph = Object.entries(dependencyGraphRaw).reduce<Record<string, string[]>>((acc, [key, value]) => {
    acc[key] = asStringArray(value);
    return acc;
  }, {});
  return {
    actionRuleList,
    ...(Object.keys(dependencyGraph).length ? { dependencyGraph } : {}),
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

function decodeDataContract(source: ContractV2Dictionary): ContractV2DataContract {
  const treeData = decodeRowsMap(source.treeData);
  const ganttData = decodeRowsMap(source.ganttData);
  return {
    mainData: asRecord(source.mainData),
    tableRows: decodeRowsMap(source.tableRows),
    relationRows: decodeRowsMap(source.relationRows),
    dictData: asRecord(source.dictData),
    pagination: asRecord(source.pagination),
    dataSource: decodeDataSources(source.dataSource),
    dataMeta: asRecord(source.dataMeta),
    ...(Object.keys(treeData).length ? { treeData } : {}),
    ...(Object.keys(ganttData).length ? { ganttData } : {}),
  };
}

function decodeGlobalStatus(source: ContractV2Dictionary): ContractV2GlobalStatus {
  return {
    pageVisible: optionalBoolean(source.pageVisible),
    ...(optionalString(source, 'pageAuth') ? { pageAuth: optionalString(source, 'pageAuth') } : {}),
    ...(optionalString(source, 'reasonCode') || optionalString(source, 'reason_code')
      ? { reasonCode: optionalString(source, 'reasonCode') || optionalString(source, 'reason_code') }
      : {}),
  };
}

function decodeWidgetStatus(raw: unknown): ContractV2WidgetStatus | null {
  if (!isRecord(raw)) return null;
  const widgetId = asString(raw.widgetId);
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
  const btnId = asString(raw.btnId);
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
  const containerId = asString(raw.containerId);
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
    globalStatus: decodeGlobalStatus(asRecord(source.globalStatus)),
    widgetStatus: (Array.isArray(source.widgetStatus) ? source.widgetStatus : [])
      .map(decodeWidgetStatus)
      .filter((item): item is ContractV2WidgetStatus => Boolean(item)),
    buttonStatus: (Array.isArray(source.buttonStatus) ? source.buttonStatus : [])
      .map(decodeButtonStatus)
      .filter((item): item is ContractV2ButtonStatus => Boolean(item)),
    containerStatus: (Array.isArray(source.containerStatus) ? source.containerStatus : [])
      .map(decodeContainerStatus)
      .filter((item): item is ContractV2ContainerStatus => Boolean(item)),
    selectorStatus: (Array.isArray(source.selectorStatus) ? source.selectorStatus : [])
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
  const pageInfo = decodePageInfo(readObject(root, 'pageInfo', '$', issues), issues);
  const layoutContract = decodeLayoutContract(readObject(root, 'layoutContract', '$', issues), issues);
  const actionContract = decodeActionContract(readObject(root, 'actionContract', '$', issues), issues);
  const dataContract = decodeDataContract(readObject(root, 'dataContract', '$', issues));
  const statusContract = decodeStatusContract(asRecord(root.statusContract));
  if (issues.length) {
    throw new ContractV2DecodeError(issues);
  }
  return {
    pageInfo,
    layoutContract,
    statusContract,
    actionContract,
    dataContract,
    runtimeContract: asRecord(root.runtimeContract),
    meta: asRecord(root.meta),
    ...(isRecord(root.searchContract) ? { searchContract: root.searchContract } : {}),
  };
}
