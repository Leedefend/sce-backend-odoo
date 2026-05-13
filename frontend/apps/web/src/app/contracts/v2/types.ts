export type ContractV2ClientType = 'web_pc' | 'wx_mini' | 'harmony_h5';
export type ContractV2Dictionary = Record<string, unknown>;

export interface ContractV2PageInfo {
  pageId: string;
  sceneKey: string;
  pageName: string;
  model: string;
  viewType: string;
  layoutType: string;
  contractVersion: string;
  clientType: ContractV2ClientType;
}

export interface ContractV2Widget {
  widgetId: string;
  widgetType: string;
  fieldCode: string;
  label: string;
  componentKey: string;
  componentConfig?: ContractV2Dictionary;
  fieldType?: string;
  relation?: string;
}

export interface ContractV2Container {
  containerId: string;
  containerType: string;
  title: string;
  children: ContractV2Container[];
  widgetList: ContractV2Widget[];
}

export interface ContractV2LayoutContract {
  layoutType: string;
  adaptMode: string;
  containerTree: ContractV2Container[];
  componentRegistry: ContractV2Dictionary;
}

export interface ContractV2ActionRule {
  actionId: string;
  triggerType: string;
  sourceWidgetId: string;
  targetIds: string[];
  dispatchMode: string;
  targetScope: string;
  refreshMode: string;
  actionKey?: string;
  label?: string;
  intent?: string;
  target?: ContractV2Dictionary;
  button?: ContractV2Dictionary;
}

export interface ContractV2ActionContract {
  actionRuleList: ContractV2ActionRule[];
  dependencyGraph?: Record<string, string[]>;
}

export interface ContractV2DataContract {
  mainData: ContractV2Dictionary;
  tableRows: Record<string, unknown[]>;
  relationRows: Record<string, unknown[]>;
  dictData: Record<string, unknown>;
  pagination: Record<string, unknown>;
  dataSource: Record<string, ContractV2Dictionary>;
  dataMeta: ContractV2Dictionary;
  treeData?: Record<string, unknown[]>;
  ganttData?: Record<string, unknown[]>;
}

export interface ContractV2GlobalStatus {
  pageVisible?: boolean;
  pageAuth?: 'none' | 'read' | 'edit' | 'admin' | string;
  reasonCode?: string;
}

export interface ContractV2WidgetStatus {
  widgetId: string;
  visible?: boolean;
  readonly?: boolean;
  required?: boolean;
  disabled?: boolean;
  reasonCode?: string;
}

export interface ContractV2ButtonStatus {
  btnId: string;
  visible?: boolean;
  disabled?: boolean;
  reasonCode?: string;
}

export interface ContractV2ContainerStatus {
  containerId: string;
  visible?: boolean;
  disabled?: boolean;
  reasonCode?: string;
}

export interface ContractV2SelectorStatus {
  selector: string;
  visible?: boolean;
  readonly?: boolean;
  required?: boolean;
  disabled?: boolean;
  reasonCode?: string;
}

export interface ContractV2StatusContract {
  globalStatus: ContractV2GlobalStatus;
  widgetStatus: ContractV2WidgetStatus[];
  buttonStatus: ContractV2ButtonStatus[];
  containerStatus: ContractV2ContainerStatus[];
  selectorStatus: ContractV2SelectorStatus[];
}

export interface ContractV2Snapshot {
  pageInfo: ContractV2PageInfo;
  layoutContract: ContractV2LayoutContract;
  statusContract: ContractV2StatusContract;
  actionContract: ContractV2ActionContract;
  dataContract: ContractV2DataContract;
  runtimeContract: ContractV2Dictionary;
  meta: ContractV2Dictionary;
  searchContract?: ContractV2Dictionary;
}

export interface ContractV2UnsupportedFeature {
  code: string;
  message: string;
  path: string;
}

export interface ContractV2NormalizedStore {
  snapshot: ContractV2Snapshot;
  widgetsById: ReadonlyMap<string, ContractV2Widget>;
  widgetsByFieldCode: ReadonlyMap<string, ContractV2Widget>;
  actionsById: ReadonlyMap<string, ContractV2ActionRule>;
  widgetStatusById: ReadonlyMap<string, ContractV2WidgetStatus>;
  buttonStatusById: ReadonlyMap<string, ContractV2ButtonStatus>;
  containerStatusById: ReadonlyMap<string, ContractV2ContainerStatus>;
  primaryDataSource: ContractV2Dictionary | null;
  unsupported: ContractV2UnsupportedFeature[];
}
