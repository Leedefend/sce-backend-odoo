export type UnifiedPageContractV2ClientType = 'web_pc' | 'wx_mini' | 'harmony_h5';

export type UnifiedPageContractV2Widget = {
  widgetId: string;
  widgetType: string;
  fieldCode: string;
  label: string;
  componentKey: string;
  componentConfig?: Record<string, unknown>;
  fieldType?: string;
  relation?: string;
};

export type UnifiedPageContractV2Container = {
  containerId: string;
  containerType: string;
  title: string;
  children: UnifiedPageContractV2Container[];
  widgetList: UnifiedPageContractV2Widget[];
};

export type UnifiedPageContractV2Action = {
  actionId: string;
  actionKey?: string;
  label?: string;
  intent?: string;
  target?: Record<string, unknown>;
  button?: {
    name?: string;
    type?: string;
  };
  triggerType: string;
  sourceWidgetId: string;
  targetIds: string[];
  dispatchMode: string;
  targetScope: string;
  refreshMode: string;
};

export type UnifiedPageContractV2WidgetStatus = {
  widgetId: string;
  visible?: boolean;
  readonly?: boolean;
  required?: boolean;
  disabled?: boolean;
};

export type UnifiedPageContractV2ButtonStatus = {
  btnId: string;
  visible?: boolean;
  disabled?: boolean;
  reasonCode?: string;
};

export type UnifiedPageContractV2SelectorStatus = {
  selector: string;
  visible?: boolean;
  readonly?: boolean;
  required?: boolean;
  disabled?: boolean;
  reasonCode?: string;
};

export type UnifiedPageContractV2GlobalStatus = {
  pageVisible?: boolean;
  pageAuth?: string;
  reasonCode?: string;
};

export type UnifiedPageContractV2ContainerStatus = {
  containerId: string;
  visible?: boolean;
  disabled?: boolean;
  reasonCode?: string;
};

export type UnifiedPageContractV2VisibleFields = {
  fields: string[];
  sourceAuthority?: Record<string, unknown>;
};

export type UnifiedPageContractV2FieldGroups = {
  groups: Array<Record<string, unknown>>;
  sourceAuthority?: Record<string, unknown>;
};

export type UnifiedPageContractV2DataMeta = Record<string, unknown> & {
  businessOperationProfile?: Record<string, unknown>;
  visibleFields?: UnifiedPageContractV2VisibleFields;
  fieldGroups?: UnifiedPageContractV2FieldGroups;
};

export type UnifiedPageContractV2 = {
  pageInfo: {
    pageId: string;
    sceneKey: string;
    pageName: string;
    model: string;
    viewType: string;
    layoutType: string;
    contractVersion: string;
    clientType: UnifiedPageContractV2ClientType;
  };
  layoutContract: {
    layoutType: string;
    adaptMode: string;
    containerTree: UnifiedPageContractV2Container[];
    listProfile?: Record<string, unknown>;
    componentRegistry: Record<string, unknown>;
  };
  statusContract: Record<string, unknown>;
  actionContract: {
    actionRuleList: UnifiedPageContractV2Action[];
    dependencyGraph?: Record<string, string[]>;
    deletePolicy?: Record<string, unknown>;
    surfacePolicies?: Record<string, unknown>;
  };
  searchContract?: Record<string, unknown>;
  dataContract: {
    dataSource?: Record<string, unknown>;
    search?: Record<string, unknown>;
    dataMeta?: UnifiedPageContractV2DataMeta;
  };
  runtimeContract: Record<string, unknown>;
  formStructureContract?: Record<string, unknown>;
  meta: Record<string, unknown>;
};

type Dict = Record<string, unknown>;

export type UnifiedPageContractV2SourceContext = {
  context?: Dict;
  domain?: unknown[];
  contextRaw?: string;
  domainRaw?: string;
  renderProfile?: string;
};

function asDict(value: unknown): Dict {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Dict : {};
}

function asList(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asText(value: unknown): string {
  return String(value || '').trim();
}

function readDictAlias(source: Dict, key: string, alias: string): Dict {
  return asDict(source[key] || source[alias]);
}

function readListAlias(source: Dict, key: string, alias: string): unknown[] {
  return asList(source[key] || source[alias]);
}

function readBooleanAlias(source: Dict, key: string, alias: string): boolean | undefined {
  const value = source[key] ?? source[alias];
  return typeof value === 'boolean' ? value : undefined;
}

function walkUnifiedPageContractV2LayoutNodes(rows: unknown[], visit: (row: Dict) => void) {
  asList(rows).forEach((item) => {
    const row = asDict(item);
    if (!Object.keys(row).length) return;
    visit(row);
    for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
      walkUnifiedPageContractV2LayoutNodes(asList(row[key]), visit);
    }
  });
}

function synthesizeUnifiedPageContractV2Widget(row: Dict): UnifiedPageContractV2Widget | null {
  const fieldInfo = asDict(row.fieldInfo || row.field_info);
  const widgetId = asText(row.widgetId || row.widget_id || (asText(row.fieldCode || row.name || row.field) ? `field.${asText(row.fieldCode || row.name || row.field)}` : ''));
  const fieldCode = asText(row.fieldCode || row.name || row.field || fieldInfo.name);
  const widgetType = asText(row.widgetType || row.widget || fieldInfo.widget || row.type);
  if (!widgetId || !fieldCode) return null;
  const attributes = asDict(row.attributes);
  const label = asText(row.label || row.string || row.title || fieldInfo.label || fieldCode);
  const componentKey = asText(row.componentKey || row.component_key || fieldInfo.componentKey || fieldInfo.component_key);
  const componentConfig = asDict(row.componentConfig || row.component_config || fieldInfo.componentConfig || fieldInfo.component_config || attributes.componentConfig || attributes.component_config);
  const relationEntry = asDict(fieldInfo.relation_entry || fieldInfo.relationEntry || componentConfig.relationEntry || componentConfig.relation_entry);
  const widgetOptions = asDict(fieldInfo.widgetOptions || fieldInfo.widget_options || fieldInfo.options || componentConfig.widgetOptions || componentConfig.widget_options);
  const subview = asDict(fieldInfo.subview || fieldInfo.subView || componentConfig.subview || componentConfig.subView);
  return {
    widgetId,
    widgetType,
    fieldCode,
    label,
    componentKey: componentKey || 'sc.display.text',
    componentConfig: {
      ...(componentConfig || {}),
      ...(asText(fieldInfo.type || fieldInfo.ttype) ? { fieldType: asText(fieldInfo.type || fieldInfo.ttype) } : {}),
      ...(asText(fieldInfo.relation) ? { relation: asText(fieldInfo.relation) } : {}),
      ...(asText(fieldInfo.relation_field || fieldInfo.relationField) ? { relation_field: asText(fieldInfo.relation_field || fieldInfo.relationField) } : {}),
      ...(Array.isArray(fieldInfo.selection) ? { selection: fieldInfo.selection } : {}),
      ...(Object.keys(relationEntry).length ? { relationEntry } : {}),
      ...(Object.keys(widgetOptions).length ? { widgetOptions } : {}),
      ...(Object.keys(subview).length ? { subview } : {}),
    },
    fieldType: asText(fieldInfo.type || fieldInfo.ttype) || undefined,
    relation: asText(fieldInfo.relation) || undefined,
  };
}

function mergeUnifiedPageContractV2Widget(existing: UnifiedPageContractV2Widget, candidate: UnifiedPageContractV2Widget): UnifiedPageContractV2Widget {
  const existingConfig = asDict(existing.componentConfig);
  const candidateConfig = asDict(candidate.componentConfig);
  return {
    ...existing,
    widgetType: existing.widgetType || candidate.widgetType,
    fieldCode: existing.fieldCode || candidate.fieldCode,
    label: existing.label || candidate.label,
    componentKey: existing.componentKey || candidate.componentKey,
    componentConfig: {
      ...existingConfig,
      ...candidateConfig,
    },
    fieldType: existing.fieldType || candidate.fieldType,
    relation: existing.relation || candidate.relation,
  };
}

export function isUnifiedPageContractV2(value: unknown): value is UnifiedPageContractV2 {
  const root = asDict(value);
  const pageInfo = readDictAlias(root, 'pageInfo', 'page_info');
  const layout = readDictAlias(root, 'layoutContract', 'layout_contract');
  const action = readDictAlias(root, 'actionContract', 'action_contract');
  return (
    (asText(pageInfo.contractVersion).startsWith('2.') || asText(pageInfo.contract_version).startsWith('2.'))
    && (asText(pageInfo.pageId).length > 0 || asText(pageInfo.page_id).length > 0)
    && (asText(pageInfo.clientType).length > 0 || asText(pageInfo.client_type).length > 0)
    && Array.isArray(layout.containerTree || layout.container_tree)
    && Array.isArray(action.actionRuleList || action.action_rule_list)
  );
}

export function resolveUnifiedPageContractV2(contract: unknown): UnifiedPageContractV2 | null {
  const root = asDict(contract);
  const direct = root.__unified_page_contract_v2;
  if (isUnifiedPageContractV2(direct)) return direct;
  if (isUnifiedPageContractV2(contract)) return contract;
  const rawBody = asDict(root.rawBody);
  const raw = rawBody.unified_page_contract_v2;
  return isUnifiedPageContractV2(raw) ? raw : null;
}

export function collectUnifiedPageContractV2Widgets(contract: unknown): UnifiedPageContractV2Widget[] {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return [];
  const out: UnifiedPageContractV2Widget[] = [];
  const byWidgetId = new Map<string, number>();
  const layout = readDictAlias(asDict(v2), 'layoutContract', 'layout_contract');
  walkUnifiedPageContractV2LayoutNodes(readListAlias(layout, 'containerTree', 'container_tree'), (row) => {
    readListAlias(row, 'widgetList', 'widget_list').forEach((widgetRaw) => {
      const widget = asDict(widgetRaw);
      const synthesized = synthesizeUnifiedPageContractV2Widget(widget);
      if (!synthesized) return;
      const existingIndex = byWidgetId.get(synthesized.widgetId);
      if (typeof existingIndex === 'number') {
        out[existingIndex] = mergeUnifiedPageContractV2Widget(out[existingIndex], synthesized);
        return;
      }
      byWidgetId.set(synthesized.widgetId, out.length);
      out.push(synthesized);
    });
    if (asText(row.type || row.kind).toLowerCase() !== 'field') return;
    const synthesized = synthesizeUnifiedPageContractV2Widget(row);
    if (!synthesized) return;
    const existingIndex = byWidgetId.get(synthesized.widgetId);
    if (typeof existingIndex === 'number') {
      out[existingIndex] = mergeUnifiedPageContractV2Widget(out[existingIndex], synthesized);
      return;
    }
    byWidgetId.set(synthesized.widgetId, out.length);
    out.push(synthesized);
  });
  return out;
}

export function collectUnifiedPageContractV2FieldWidgets(contract: unknown): UnifiedPageContractV2Widget[] {
  const seen = new Set<string>();
  return collectUnifiedPageContractV2Widgets(contract)
    .filter((widget) => widget.fieldCode && widget.widgetType !== 'display')
    .filter((widget) => {
      if (seen.has(widget.fieldCode)) return false;
      seen.add(widget.fieldCode);
      return true;
    });
}

export function collectUnifiedPageContractV2WidgetStatus(contract: unknown): Record<string, UnifiedPageContractV2WidgetStatus> {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return {};
  const status = readDictAlias(asDict(v2), 'statusContract', 'status_contract');
  return readListAlias(status, 'widgetStatus', 'widget_status').reduce<Record<string, UnifiedPageContractV2WidgetStatus>>((acc, item) => {
    const row = asDict(item);
    const widgetId = asText(row.widgetId || row.widget_id);
    if (!widgetId) return acc;
    acc[widgetId] = {
      widgetId,
      visible: typeof row.visible === 'boolean' ? row.visible : undefined,
      readonly: typeof row.readonly === 'boolean' ? row.readonly : undefined,
      required: typeof row.required === 'boolean' ? row.required : undefined,
      disabled: typeof row.disabled === 'boolean' ? row.disabled : undefined,
    };
    return acc;
  }, {});
}

export function collectUnifiedPageContractV2ButtonStatus(contract: unknown): Record<string, UnifiedPageContractV2ButtonStatus> {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return {};
  const status = readDictAlias(asDict(v2), 'statusContract', 'status_contract');
  return readListAlias(status, 'buttonStatus', 'button_status').reduce<Record<string, UnifiedPageContractV2ButtonStatus>>((acc, item) => {
    const row = asDict(item);
    const btnId = asText(row.btnId || row.btn_id);
    if (!btnId) return acc;
    acc[btnId] = {
      btnId,
      visible: typeof row.visible === 'boolean' ? row.visible : undefined,
      disabled: typeof row.disabled === 'boolean' ? row.disabled : undefined,
      reasonCode: asText(row.reasonCode || row.reason_code) || undefined,
    };
    return acc;
  }, {});
}

export function collectUnifiedPageContractV2SelectorStatus(contract: unknown): UnifiedPageContractV2SelectorStatus[] {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return [];
  const status = readDictAlias(asDict(v2), 'statusContract', 'status_contract');
  return readListAlias(status, 'selectorStatus', 'selector_status').reduce<UnifiedPageContractV2SelectorStatus[]>((acc, item) => {
    const row = asDict(item);
    const selector = asText(row.selector);
    if (!selector) return acc;
    acc.push({
      selector,
      visible: typeof row.visible === 'boolean' ? row.visible : undefined,
      readonly: typeof row.readonly === 'boolean' ? row.readonly : undefined,
      required: typeof row.required === 'boolean' ? row.required : undefined,
      disabled: typeof row.disabled === 'boolean' ? row.disabled : undefined,
      reasonCode: asText(row.reasonCode || row.reason_code) || undefined,
    });
    return acc;
  }, []);
}

function matchesUnifiedPageContractV2Selector(pattern: string, selector: string): boolean {
  if (!pattern || !selector) return false;
  if (pattern === selector) return true;
  if (pattern.endsWith('.*')) {
    const prefix = pattern.slice(0, -1);
    return selector.startsWith(prefix);
  }
  return false;
}

export function resolveUnifiedPageContractV2SelectorStatus(
  contract: unknown,
  selectors: string[],
): UnifiedPageContractV2SelectorStatus | null {
  const normalized = selectors.map((item) => asText(item)).filter(Boolean);
  if (!normalized.length) return null;
  for (const row of collectUnifiedPageContractV2SelectorStatus(contract)) {
    if (normalized.some((selector) => matchesUnifiedPageContractV2Selector(row.selector, selector))) {
      return row;
    }
  }
  return null;
}

export function resolveUnifiedPageContractV2GlobalStatus(contract: unknown): UnifiedPageContractV2GlobalStatus | null {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return null;
  const status = readDictAlias(asDict(v2), 'statusContract', 'status_contract');
  const row = readDictAlias(status, 'globalStatus', 'global_status');
  if (!Object.keys(row).length) return null;
  return {
    pageVisible: readBooleanAlias(row, 'pageVisible', 'page_visible'),
    pageAuth: asText(row.pageAuth || row.page_auth) || undefined,
    reasonCode: asText(row.reasonCode || row.reason_code) || undefined,
  };
}

export function resolveUnifiedPageContractV2SourceContext(contract: unknown): UnifiedPageContractV2SourceContext {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return {};
  const data = readDictAlias(asDict(v2), 'dataContract', 'data_contract');
  const dataMeta = readDictAlias(data, 'dataMeta', 'data_meta');
  const runtime = readDictAlias(asDict(v2), 'runtimeContract', 'runtime_contract');
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

export function resolveUnifiedPageContractV2MainData(contract: unknown): Dict {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return {};
  const data = readDictAlias(asDict(v2), 'dataContract', 'data_contract');
  return readDictAlias(data, 'mainData', 'main_data');
}

export function collectUnifiedPageContractV2ContainerStatus(contract: unknown): Record<string, UnifiedPageContractV2ContainerStatus> {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return {};
  const status = readDictAlias(asDict(v2), 'statusContract', 'status_contract');
  return readListAlias(status, 'containerStatus', 'container_status').reduce<Record<string, UnifiedPageContractV2ContainerStatus>>((acc, item) => {
    const row = asDict(item);
    const containerId = asText(row.containerId || row.container_id);
    if (!containerId) return acc;
    acc[containerId] = {
      containerId,
      visible: typeof row.visible === 'boolean' ? row.visible : undefined,
      disabled: typeof row.disabled === 'boolean' ? row.disabled : undefined,
      reasonCode: asText(row.reasonCode || row.reason_code) || undefined,
    };
    return acc;
  }, {});
}

export function collectUnifiedPageContractV2FieldContainerStatus(contract: unknown): Record<string, UnifiedPageContractV2ContainerStatus> {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return {};
  const containerStatus = collectUnifiedPageContractV2ContainerStatus(contract);
  const out: Record<string, UnifiedPageContractV2ContainerStatus> = {};
  const visit = (rows: unknown[], inherited: UnifiedPageContractV2ContainerStatus) => {
    rows.forEach((item) => {
      const row = asDict(item);
      const containerId = asText(row.containerId);
      const current = containerId ? (containerStatus[containerId] || { containerId }) : inherited;
      const merged: UnifiedPageContractV2ContainerStatus = {
        containerId: containerId || inherited.containerId,
        visible: inherited.visible === false || current.visible === false ? false : current.visible,
        disabled: inherited.disabled === true || current.disabled === true ? true : current.disabled,
        reasonCode: current.reasonCode || inherited.reasonCode,
      };
      readListAlias(row, 'widgetList', 'widget_list').forEach((widgetRaw) => {
        const widget = asDict(widgetRaw);
        const fieldCode = asText(widget.fieldCode);
        if (fieldCode) out[fieldCode] = merged;
      });
      if (asText(row.type || row.kind).toLowerCase() === 'field') {
        const fieldInfo = asDict(row.fieldInfo || row.field_info);
        const fieldCode = asText(row.fieldCode || row.name || row.field || fieldInfo.name);
        if (fieldCode) out[fieldCode] = merged;
      }
      for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
        visit(asList(row[key]), merged);
      }
    });
  };
  const layout = readDictAlias(asDict(v2), 'layoutContract', 'layout_contract');
  visit(readListAlias(layout, 'containerTree', 'container_tree'), { containerId: '', visible: true, disabled: false });
  return out;
}

export function collectUnifiedPageContractV2FieldStatus(contract: unknown): Record<string, UnifiedPageContractV2WidgetStatus> {
  const widgetStatus = collectUnifiedPageContractV2WidgetStatus(contract);
  return collectUnifiedPageContractV2FieldWidgets(contract).reduce<Record<string, UnifiedPageContractV2WidgetStatus>>((acc, widget) => {
    if (!widget.fieldCode) return acc;
    acc[widget.fieldCode] = widgetStatus[widget.widgetId] || { widgetId: widget.widgetId };
    return acc;
  }, {});
}

export function resolveUnifiedPageContractV2PrimaryDataSource(contract: unknown): Record<string, unknown> {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return {};
  const data = readDictAlias(asDict(v2), 'dataContract', 'data_contract');
  const dataSource = readDictAlias(data, 'dataSource', 'data_source');
  return asDict(dataSource.primary);
}

export function resolveUnifiedPageContractV2DeletePolicy(contract: unknown): Record<string, unknown> {
  const root = asDict(contract);
  const v2 = resolveUnifiedPageContractV2(contract);
  const source = v2 ? asDict(v2) : root;
  const action = readDictAlias(source, 'actionContract', 'action_contract');
  const formal = readDictAlias(action, 'deletePolicy', 'delete_policy');
  if (Object.keys(formal).length) return formal;
  return asDict(source.delete_policy);
}

export function resolveUnifiedPageContractV2SurfacePolicies(contract: unknown): Record<string, unknown> {
  const root = asDict(contract);
  const v2 = resolveUnifiedPageContractV2(contract);
  const source = v2 ? asDict(v2) : root;
  const action = readDictAlias(source, 'actionContract', 'action_contract');
  const formal = readDictAlias(action, 'surfacePolicies', 'surface_policies');
  if (Object.keys(formal).length) return formal;
  return asDict(source.surface_policies);
}

export function resolveUnifiedPageContractV2ListProfile(contract: unknown): Record<string, unknown> {
  const root = asDict(contract);
  const v2 = resolveUnifiedPageContractV2(contract);
  const source = v2 ? asDict(v2) : root;
  const layout = readDictAlias(source, 'layoutContract', 'layout_contract');
  const formal = readDictAlias(layout, 'listProfile', 'list_profile');
  if (Object.keys(formal).length) return formal;
  return asDict(source.list_profile);
}

function resolveUnifiedPageContractV2DataMeta(contract: unknown): Dict {
  const root = asDict(contract);
  const v2 = resolveUnifiedPageContractV2(contract);
  const source = v2 ? asDict(v2) : root;
  const data = readDictAlias(source, 'dataContract', 'data_contract');
  return readDictAlias(data, 'dataMeta', 'data_meta');
}

export function resolveUnifiedPageContractV2BusinessOperationProfile(contract: unknown): Record<string, unknown> {
  const root = asDict(contract);
  const dataMeta = resolveUnifiedPageContractV2DataMeta(contract);
  const formal = readDictAlias(dataMeta, 'businessOperationProfile', 'business_operation_profile');
  if (Object.keys(formal).length) return formal;
  return asDict(root.business_operation_profile);
}

export function resolveUnifiedPageContractV2VisibleFields(contract: unknown): string[] {
  const dataMeta = resolveUnifiedPageContractV2DataMeta(contract);
  const formal = dataMeta.visibleFields || dataMeta.visible_fields;
  const formalRow = asDict(formal);
  const formalFields = Array.isArray(formal)
    ? formal
    : asList(formalRow.fields || formalRow.fieldNames || formalRow.field_names);
  if (formalFields.length) {
    return formalFields.map((item) => asText(item)).filter(Boolean);
  }
  const root = asDict(contract);
  const rootFields = asList(root.visible_fields);
  if (rootFields.length) {
    return rootFields.map((item) => asText(item)).filter(Boolean);
  }
  return collectUnifiedPageContractV2FieldWidgets(contract)
    .map((widget) => asText(widget.fieldCode))
    .filter(Boolean);
}

export function resolveUnifiedPageContractV2FieldGroups(contract: unknown): Array<Record<string, unknown>> {
  const dataMeta = resolveUnifiedPageContractV2DataMeta(contract);
  const formal = dataMeta.fieldGroups || dataMeta.field_groups;
  const formalRow = asDict(formal);
  const groups = Array.isArray(formal)
    ? formal
    : asList(formalRow.groups || formalRow.items || formalRow.fieldGroups || formalRow.field_groups);
  if (groups.length) {
    return groups.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object' && !Array.isArray(item));
  }
  const root = asDict(contract);
  return asList(root.field_groups)
    .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object' && !Array.isArray(item));
}

export function resolveUnifiedPageContractV2FormStructureContract(contract: unknown): Record<string, unknown> {
  const root = asDict(contract);
  const v2 = resolveUnifiedPageContractV2(contract);
  const source = v2 ? asDict(v2) : root;
  const formal = readDictAlias(source, 'formStructureContract', 'form_structure_contract');
  if (Object.keys(formal).length) return formal;
  return {};
}
