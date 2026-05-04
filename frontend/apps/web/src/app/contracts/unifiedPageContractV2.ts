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

export function resolveUnifiedPageContractV2PrimaryDataSource(contract: unknown): Record<string, unknown> {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return {};
  return asDict(asDict(v2.dataContract.dataSource).primary);
}
