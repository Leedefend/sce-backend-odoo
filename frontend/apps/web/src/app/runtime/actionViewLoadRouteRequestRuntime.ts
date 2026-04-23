import { buildActionViewGroupRouteSyncPayload } from './actionViewGroupRouteSyncRuntime';
import { buildGroupWindowRouteSyncPlan, mergeGroupWindowSyncPatches } from './actionViewGroupWindowRuntime';
import { buildActionViewListRequest } from './actionViewLoadRequestRuntime';

type Dict = Record<string, unknown>;

export function resolveLoadListDomainState(options: {
  metaDomainRaw: unknown;
  sceneFiltersRaw: unknown;
  effectiveFilterDomain: unknown[];
  mergeSceneDomainFn: (base: unknown, sceneFilters: unknown) => unknown[];
  mergeActiveFilterDomainFn: (base: unknown) => unknown[];
}): {
  baseDomain: unknown[];
  activeDomain: unknown[];
} {
  const baseDomain = options.mergeSceneDomainFn(
    options.mergeSceneDomainFn(options.metaDomainRaw, options.sceneFiltersRaw),
    options.effectiveFilterDomain,
  );
  return {
    baseDomain,
    activeDomain: options.mergeActiveFilterDomainFn(baseDomain),
  };
}

export function resolveLoadListContextState(options: {
  metaContextRaw: unknown;
  effectiveRequestContext: Dict;
  effectiveRequestContextRaw: string;
  mergeContextFn: (base: Record<string, unknown> | string | undefined, extra?: Record<string, unknown>) => Dict;
}): {
  requestContext: Dict;
  requestContextRaw: string;
} {
  return {
    requestContext: options.mergeContextFn(options.metaContextRaw as Record<string, unknown> | string | undefined, options.effectiveRequestContext),
    requestContextRaw: options.effectiveRequestContextRaw,
  };
}

export function resolveLoadListRequestPayload(options: {
  model: string;
  requestedFields: string[];
  domain: unknown[];
  domainRaw: unknown;
  activeGroupByField: string;
  listOffset: number;
  groupWindowOffset: number;
  groupSampleLimit: number;
  contractLimit: number;
  groupPageOffsets: Record<string, number>;
  context: Dict;
  contextRaw: string;
  searchTerm: string;
  order: string;
}): Dict {
  return buildActionViewListRequest({
    model: options.model,
    requestedFields: options.requestedFields,
    domain: options.domain,
    domainRaw: options.domainRaw,
    activeGroupByField: options.activeGroupByField,
    listOffset: options.listOffset,
    groupWindowOffset: options.groupWindowOffset,
    groupSampleLimit: options.groupSampleLimit,
    contractLimit: options.contractLimit,
    groupPageOffsets: options.groupPageOffsets,
    context: options.context,
    contextRaw: options.contextRaw,
    searchTerm: options.searchTerm,
    order: options.order,
  });
}

export function resolveLoadGroupRouteSyncPlan(options: {
  activeGroupByField: string;
  effectiveGroupOffset: number;
  routeSnapshot: {
    groupFingerprint: string;
    groupWindowId: string;
    groupWindowDigest: string;
    groupWindowIdentityKey: string;
  };
  responseGroupFingerprint: string;
  groupWindowId: string;
  groupWindowDigest: string;
  groupWindowIdentityKey: string;
}): {
  resetPatch: Dict | null;
  syncPatches: Dict[];
} {
  return buildGroupWindowRouteSyncPlan(buildActionViewGroupRouteSyncPayload({
    activeGroupByField: options.activeGroupByField,
    effectiveGroupOffset: options.effectiveGroupOffset,
    routeSnapshot: options.routeSnapshot,
    responseGroupFingerprint: options.responseGroupFingerprint,
    groupWindowId: options.groupWindowId,
    groupWindowDigest: options.groupWindowDigest,
    groupWindowIdentityKey: options.groupWindowIdentityKey,
  }));
}

export function resolveLoadGroupRouteSyncPatch(options: {
  syncPatches: Dict[];
}): Dict | null {
  return mergeGroupWindowSyncPatches(options.syncPatches);
}
