export type ContractV2ClientType = 'web_pc' | 'wx_mini' | 'harmony_h5';
export type ContractV2ViewType = 'form' | 'list' | 'table' | 'kanban' | 'tree' | 'gantt' | 'combine';
export type ContractV2LayoutType = 'form' | 'table' | 'kanban' | 'tree' | 'gantt' | 'combine';
export type ContractV2AdaptMode = 'pc' | 'mobile';
export type ContractV2TriggerType = 'change' | 'click' | 'select' | 'refresh' | 'add' | 'delete' | 'confirm' | 'submit' | 'blur' | 'focus';
export type ContractV2DispatchMode = 'local' | 'server' | 'serverDebounced' | 'serverBlocking';
export type ContractV2TargetScope = 'widget' | 'container' | 'page' | 'dataSource' | 'runtime';
export type ContractV2RefreshMode = 'none' | 'partial' | 'full';
export type ContractV2Auth = 'none' | 'read' | 'edit' | 'admin';
export type ContractV2PatchStrategy = 'incremental' | 'full';
export type ContractV2CachePolicy = 'none' | 'etag' | 'snapshot';
export type ContractV2RenderStrategy = 'sync' | 'scheduled' | 'virtualized';
export type ContractV2PatchOperation = 'replace' | 'merge' | 'append' | 'remove' | 'reorder' | 'invalidate';
export type ContractV2PageRenderMode = 'governed';
export type ContractV2Dictionary = Record<string, unknown>;

export interface ContractV2PageInfo {
  pageId: string;
  sceneKey: string;
  pageName: string;
  model: string;
  viewType: ContractV2ViewType;
  layoutType: ContractV2LayoutType;
  renderMode: ContractV2PageRenderMode;
  contractVersion: string;
  clientType: ContractV2ClientType;
}

export interface ContractV2Widget {
  widgetId: string;
  widgetType: string;
  fieldCode: string;
  label: string;
  span: number;
  componentKey: string;
  capabilities: string[];
  componentConfig: ContractV2Dictionary;
  fieldType?: string;
  relation?: string;
  formStructureRole?: ContractV2Dictionary;
}

export interface ContractV2Container {
  containerId: string;
  containerType: string;
  type?: string;
  name?: string;
  string?: string;
  label?: string;
  title: string;
  span: number;
  styleToken?: string;
  cols?: number;
  columns?: number;
  widget?: string;
  attributes?: ContractV2Dictionary;
  fieldInfo?: ContractV2Dictionary;
  field_info?: ContractV2Dictionary;
  buttonType?: string;
  action?: ContractV2Dictionary | null;
  modifiers?: ContractV2Dictionary;
  invisible?: unknown;
  readonly?: unknown;
  required?: unknown;
  formStructure?: ContractV2Dictionary;
  formStructureRole?: ContractV2Dictionary;
  children: ContractV2Container[];
  pages?: ContractV2Container[];
  tabs?: ContractV2Container[];
  nodes?: ContractV2Container[];
  items?: ContractV2Container[];
  widgetList: ContractV2Widget[];
}

export interface ContractV2LayoutContract {
  pageId: string;
  layoutType: ContractV2LayoutType;
  adaptMode: ContractV2AdaptMode;
  containerTree: ContractV2Container[];
  layoutHints: ContractV2Dictionary;
  componentRegistry: ContractV2Dictionary;
  listProfile?: ContractV2Dictionary;
}

export interface ContractV2ActionRule {
  actionId: string;
  triggerType: ContractV2TriggerType;
  sourceWidgetId: string;
  targetIds: string[];
  dispatchMode: ContractV2DispatchMode;
  targetScope: ContractV2TargetScope;
  refreshMode: ContractV2RefreshMode;
  actionKey?: string;
  label?: string;
  intent?: string;
  target?: ContractV2Dictionary;
  button?: ContractV2Dictionary;
  submitPolicy?: ContractV2Dictionary;
  tracePolicy?: ContractV2Dictionary;
}

export interface ContractV2ActionContract {
  actionRuleList: ContractV2ActionRule[];
  dependencyGraph: Record<string, string[]>;
  deletePolicy?: ContractV2Dictionary;
  surfacePolicies?: ContractV2Dictionary;
}

export interface ContractV2VisibleFields {
  fields: string[];
  sourceAuthority?: ContractV2Dictionary;
}

export interface ContractV2FieldGroups {
  groups: ContractV2Dictionary[];
  sourceAuthority?: ContractV2Dictionary;
}

export interface ContractV2DataMeta extends ContractV2Dictionary {
  businessOperationProfile?: ContractV2Dictionary;
  visibleFields?: ContractV2VisibleFields;
  fieldGroups?: ContractV2FieldGroups;
}

export interface ContractV2DataContract {
  mainData: ContractV2Dictionary;
  tableRows: Record<string, unknown[]>;
  relationRows: Record<string, unknown[]>;
  dictData: Record<string, unknown>;
  pagination: Record<string, unknown>;
  dataSource: Record<string, ContractV2Dictionary>;
  dataMeta: ContractV2DataMeta;
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
  placeholder?: string;
  auth?: ContractV2Auth;
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

export interface ContractV2RuntimeContract {
  patchStrategy: ContractV2PatchStrategy;
  cachePolicy: ContractV2CachePolicy;
  optimistic: boolean;
  lazyContainer: string[];
  virtualization: ContractV2Dictionary;
  retryPolicy: ContractV2Dictionary;
  renderStrategy?: ContractV2RenderStrategy;
  hydration?: ContractV2Dictionary;
  patchOperations?: ContractV2PatchOperation[];
  tracePolicy?: ContractV2Dictionary;
  complexityBudget?: ContractV2Dictionary;
  aiEnvelope?: ContractV2Dictionary;
}

export interface ContractV2Meta {
  etag: string;
  snapshotId: string;
  traceId: string;
  requestId: string;
  sourceType: string;
}

export interface ContractV2Snapshot {
  pageInfo: ContractV2PageInfo;
  layoutContract: ContractV2LayoutContract;
  statusContract: ContractV2StatusContract;
  actionContract: ContractV2ActionContract;
  dataContract: ContractV2DataContract;
  runtimeContract: ContractV2RuntimeContract;
  meta: ContractV2Meta;
  formStructureContract?: ContractV2Dictionary;
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
