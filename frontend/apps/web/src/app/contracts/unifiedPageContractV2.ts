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
    componentRegistry: Record<string, unknown>;
  };
  statusContract: Record<string, unknown>;
  actionContract: {
    actionRuleList: UnifiedPageContractV2Action[];
    dependencyGraph?: Record<string, string[]>;
  };
  searchContract?: Record<string, unknown>;
  dataContract: {
    dataSource?: Record<string, unknown>;
    search?: Record<string, unknown>;
    dataMeta?: Record<string, unknown>;
  };
  runtimeContract: Record<string, unknown>;
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
  const componentKey = asText(row.componentKey || fieldInfo.componentKey);
  const componentConfig = asDict(row.componentConfig || fieldInfo.componentConfig || attributes.componentConfig);
  const relationEntry = asDict(fieldInfo.relation_entry || fieldInfo.relationEntry || componentConfig.relationEntry || componentConfig.relation_entry);
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
      ...(Array.isArray(fieldInfo.selection) ? { selection: fieldInfo.selection } : {}),
      ...(Object.keys(relationEntry).length ? { relationEntry } : {}),
      ...(Object.keys(asDict(fieldInfo.widget_options)).length ? { widgetOptions: asDict(fieldInfo.widget_options) } : {}),
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
  const pageInfo = asDict(root.pageInfo);
  const layout = asDict(root.layoutContract);
  const action = asDict(root.actionContract);
  return (
    asText(pageInfo.contractVersion).startsWith('2.')
    && asText(pageInfo.pageId).length > 0
    && asText(pageInfo.clientType).length > 0
    && Array.isArray(layout.containerTree)
    && Array.isArray(action.actionRuleList)
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
  walkUnifiedPageContractV2LayoutNodes(v2.layoutContract.containerTree, (row) => {
    asList(row.widgetList).forEach((widgetRaw) => {
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
  const status = asDict(v2.statusContract);
  return asList(status.widgetStatus).reduce<Record<string, UnifiedPageContractV2WidgetStatus>>((acc, item) => {
    const row = asDict(item);
    const widgetId = asText(row.widgetId);
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
  const status = asDict(v2.statusContract);
  return asList(status.buttonStatus).reduce<Record<string, UnifiedPageContractV2ButtonStatus>>((acc, item) => {
    const row = asDict(item);
    const btnId = asText(row.btnId);
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
  const status = asDict(v2.statusContract);
  return asList(status.selectorStatus).reduce<UnifiedPageContractV2SelectorStatus[]>((acc, item) => {
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
  const row = asDict(asDict(v2.statusContract).globalStatus);
  if (!Object.keys(row).length) return null;
  return {
    pageVisible: typeof row.pageVisible === 'boolean' ? row.pageVisible : undefined,
    pageAuth: asText(row.pageAuth) || undefined,
    reasonCode: asText(row.reasonCode || row.reason_code) || undefined,
  };
}

export function resolveUnifiedPageContractV2SourceContext(contract: unknown): UnifiedPageContractV2SourceContext {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return {};
  const dataMeta = asDict(v2.dataContract.dataMeta);
  const runtime = asDict(v2.runtimeContract);
  const source = asDict(dataMeta.sourceContext || runtime.sourceContext);
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
  return asDict(asDict(v2.dataContract).mainData);
}

export function collectUnifiedPageContractV2ContainerStatus(contract: unknown): Record<string, UnifiedPageContractV2ContainerStatus> {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return {};
  const status = asDict(v2.statusContract);
  return asList(status.containerStatus).reduce<Record<string, UnifiedPageContractV2ContainerStatus>>((acc, item) => {
    const row = asDict(item);
    const containerId = asText(row.containerId);
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
      asList(row.widgetList).forEach((widgetRaw) => {
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
  visit(v2.layoutContract.containerTree, { containerId: '', visible: true, disabled: false });
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
  return asDict(asDict(v2.dataContract.dataSource).primary);
}
