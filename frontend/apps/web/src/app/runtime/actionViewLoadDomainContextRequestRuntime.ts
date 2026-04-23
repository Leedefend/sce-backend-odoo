import {
  resolveLoadListContextState,
  resolveLoadListDomainState,
  resolveLoadListRequestPayload,
} from './actionViewLoadRouteRequestRuntime';

type Dict = Record<string, unknown>;

export function resolveLoadDomainStateApply(options: {
  metaDomainRaw: unknown;
  sceneFiltersRaw: unknown;
  effectiveFilterDomain: unknown[];
  mergeSceneDomainFn: (base: unknown, sceneFilters: unknown) => unknown[];
  mergeActiveFilterDomainFn: (base: unknown) => unknown[];
}): {
  baseDomain: unknown[];
  activeDomain: unknown[];
} {
  return resolveLoadListDomainState({
    metaDomainRaw: options.metaDomainRaw,
    sceneFiltersRaw: options.sceneFiltersRaw,
    effectiveFilterDomain: options.effectiveFilterDomain,
    mergeSceneDomainFn: options.mergeSceneDomainFn,
    mergeActiveFilterDomainFn: options.mergeActiveFilterDomainFn,
  });
}

export function resolveLoadContextStateApply(options: {
  metaContextRaw: unknown;
  effectiveRequestContext: Dict;
  effectiveRequestContextRaw: string;
  mergeContextFn: (base: Record<string, unknown> | string | undefined, extra?: Record<string, unknown>) => Dict;
}): {
  requestContext: Dict;
  requestContextRaw: string;
} {
  return resolveLoadListContextState({
    metaContextRaw: options.metaContextRaw,
    effectiveRequestContext: options.effectiveRequestContext,
    effectiveRequestContextRaw: options.effectiveRequestContextRaw,
    mergeContextFn: options.mergeContextFn,
  });
}

export function resolveLoadRequestPayloadState(options: {
  model: string;
  requestedFields: string[];
  activeDomain: unknown[];
  effectiveFilterDomainRaw: unknown;
  activeGroupByField: string;
  listOffset: number;
  groupWindowOffset: number;
  groupSampleLimit: number;
  contractLimit: number;
  groupPageOffsets: Record<string, number>;
  requestContext: Dict;
  requestContextRaw: string;
  searchTerm: string;
  order: string;
}): Dict {
  return resolveLoadListRequestPayload({
    model: options.model,
    requestedFields: options.requestedFields,
    domain: options.activeDomain,
    domainRaw: options.effectiveFilterDomainRaw,
    activeGroupByField: options.activeGroupByField,
    listOffset: options.listOffset,
    groupWindowOffset: options.groupWindowOffset,
    groupSampleLimit: options.groupSampleLimit,
    contractLimit: options.contractLimit,
    groupPageOffsets: options.groupPageOffsets,
    context: options.requestContext,
    contextRaw: options.requestContextRaw,
    searchTerm: options.searchTerm,
    order: options.order,
  });
}
