export type UnifiedPageContractV2ClientType = 'web_pc' | 'wx_mini' | 'harmony_h5';

export type UnifiedPageContractV2Widget = {
  widgetId: string;
  widgetType: string;
  fieldCode: string;
  label: string;
  componentKey: string;
  componentConfig?: Record<string, unknown>;
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
  dataContract: {
    dataSource?: Record<string, unknown>;
    dataMeta?: Record<string, unknown>;
  };
  runtimeContract: Record<string, unknown>;
  meta: Record<string, unknown>;
};

type Dict = Record<string, unknown>;

function asDict(value: unknown): Dict {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Dict : {};
}

function asList(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asText(value: unknown): string {
  return String(value || '').trim();
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
  const visit = (rows: unknown[]) => {
    rows.forEach((item) => {
      const row = asDict(item);
      asList(row.widgetList).forEach((widgetRaw) => {
        const widget = asDict(widgetRaw);
        const widgetId = asText(widget.widgetId);
        if (!widgetId) return;
        out.push({
          widgetId,
          widgetType: asText(widget.widgetType),
          fieldCode: asText(widget.fieldCode),
          label: asText(widget.label),
          componentKey: asText(widget.componentKey),
          componentConfig: asDict(widget.componentConfig),
        });
      });
      visit(asList(row.children));
    });
  };
  visit(v2.layoutContract.containerTree);
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
      const current = containerStatus[containerId] || { containerId };
      const merged: UnifiedPageContractV2ContainerStatus = {
        containerId,
        visible: inherited.visible === false || current.visible === false ? false : current.visible,
        disabled: inherited.disabled === true || current.disabled === true ? true : current.disabled,
        reasonCode: current.reasonCode || inherited.reasonCode,
      };
      asList(row.widgetList).forEach((widgetRaw) => {
        const widget = asDict(widgetRaw);
        const fieldCode = asText(widget.fieldCode);
        if (fieldCode) out[fieldCode] = merged;
      });
      visit(asList(row.children), merged);
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
