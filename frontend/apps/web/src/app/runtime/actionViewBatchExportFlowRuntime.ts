import { buildExportRequest, resolveExportGuard } from './actionViewAssigneeExportRuntime';

type Dict = Record<string, unknown>;

export function resolveBatchExportTargetModel(options: {
  resolvedModelRaw: unknown;
  routeModelRaw: unknown;
}): string {
  return String(options.resolvedModelRaw || options.routeModelRaw || '').trim();
}

export function resolveBatchExportGuardDecision(options: {
  targetModel: string;
  scope: 'selected' | 'all';
  selectedCount: number;
}): { ok: boolean; reason?: string } {
  return resolveExportGuard({
    targetModel: options.targetModel,
    scope: options.scope,
    selectedCount: options.selectedCount,
  });
}

export function resolveBatchExportDomainState(options: {
  actionMetaDomainRaw: unknown;
  sceneFiltersRaw: unknown;
  effectiveFilterDomain: unknown[];
  mergeSceneDomainFn: (base: unknown, sceneFilters: unknown) => unknown[];
  mergeActiveFilterDomainFn: (base: unknown) => unknown[];
}): unknown[] {
  void options.actionMetaDomainRaw;
  void options.sceneFiltersRaw;
  void options.mergeSceneDomainFn;
  return options.mergeActiveFilterDomainFn(
    Array.isArray(options.effectiveFilterDomain) ? options.effectiveFilterDomain : [],
  );
}

export function resolveBatchExportRequestPayload(options: {
  model: string;
  scope: 'selected' | 'all';
  selectedIds: number[];
  domain: unknown[];
  columns: string[];
  order: string;
  context: Dict;
}) {
  return buildExportRequest({
    model: options.model,
    scope: options.scope,
    selectedIds: options.selectedIds,
    domain: options.domain,
    columns: options.columns,
    order: options.order,
    context: options.context,
  });
}

export function resolveBatchExportNoContent(options: {
  contentB64Raw: unknown;
}): boolean {
  return !String(options.contentB64Raw || '').trim();
}
