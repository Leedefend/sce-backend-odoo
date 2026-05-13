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

function walkContainers(containers: ContractV2Container[], visit: (container: ContractV2Container) => void): void {
  containers.forEach((container) => {
    visit(container);
    walkContainers(container.children, visit);
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

function collectWidgets(snapshot: ContractV2Snapshot): ContractV2Widget[] {
  const out: ContractV2Widget[] = [];
  walkContainers(snapshot.layoutContract.containerTree, (container) => {
    out.push(...container.widgetList);
  });
  return out;
}

function collectUnsupported(snapshot: ContractV2Snapshot): ContractV2UnsupportedFeature[] {
  const required = snapshot.meta.requiredCapabilities;
  if (!Array.isArray(required)) return [];
  return required
    .map((item) => String(item || '').trim())
    .filter(Boolean)
    .map((capability) => ({
      code: 'required_capability_not_bound',
      message: `required capability is not bound in web v2 store: ${capability}`,
      path: `meta.requiredCapabilities.${capability}`,
    }));
}

function primaryDataSource(snapshot: ContractV2Snapshot): ContractV2Dictionary | null {
  const source = snapshot.dataContract.dataSource.primary;
  return source && Object.keys(source).length ? source : null;
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
    unsupported: collectUnsupported(snapshot),
  };
}
