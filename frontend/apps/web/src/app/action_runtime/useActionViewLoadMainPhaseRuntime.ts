type Dict = Record<string, unknown>;
type StatusInput = { error: string; recordsLength: number };

type PreflightResult = {
  stopped: boolean;
  contract?: unknown;
  meta?: Dict | null;
  typedContract?: Dict;
  resolvedModel?: string;
};

type RequestResult = {
  blocked: boolean;
  result?: Dict;
  contractColumns?: string[];
  baseDomain?: unknown[];
  requestContext?: Dict;
  requestContextRaw?: string;
};

type ExecuteLoadMainPhaseOptions = {
  startedAt: number;
  actionId: number;
  actionMeta: Dict | null;
  routeQueryMap: Dict;
  viewMode: string;
  searchTerm: string;
  sortLabel: string;
  activeGroupByField: string;
  listOffset: number;
  groupWindowOffset: number;
  groupSampleLimit: number;
  contractLimit: number;
  groupPageOffsets: Record<string, number>;
  sceneFiltersRaw: unknown;
  executeLoadPreflightPhase: (input: { input: Dict }) => Promise<PreflightResult>;
  executeLoadRequestPhase: (input: {
    executeLoadDataRequest: (payload: Dict) => Promise<RequestResult>;
    input: Dict;
    applyLoadRequestBlockedState: (input: { blocked: boolean; message: string; statusInput: StatusInput }) => boolean;
  }) => Promise<RequestResult>;
  executeLoadDataRequest: (payload: Dict) => Promise<RequestResult>;
  buildLoadRequestInput: (input: Dict) => Dict;
  buildLoadRequestDynamicInput: (input: Dict) => Dict;
  resolveLoadDynamicState?: () => Partial<{
    viewMode: string;
    searchTerm: string;
    sortLabel: string;
    activeGroupByField: string;
    listOffset: number;
    groupWindowOffset: number;
    groupSampleLimit: number;
    contractLimit: number;
    groupPageOffsets: Record<string, number>;
  }>;
  applyLoadRequestBlocked: (input: { blocked: boolean; message: string; statusInput: StatusInput }) => boolean;
  executeLoadSuccessPhase: (input: { input: Dict }) => Promise<void>;
  executeLoadCatchPhase: (input: { input: Dict }) => void;
  buildLoadSuccessDynamicInput: (input: Dict) => Dict;
  buildLoadSuccessPhaseInput: (input: Dict) => Dict;
};

export function useActionViewLoadMainPhaseRuntime() {
  async function executeLoadMainPhase(options: ExecuteLoadMainPhaseOptions): Promise<{ stopped: boolean }> {
    try {
      const preflightPhaseResult = await options.executeLoadPreflightPhase({
        input: {
          actionId: options.actionId,
          actionMeta: options.actionMeta,
          routeQueryMap: options.routeQueryMap,
        },
      });
      if (preflightPhaseResult.stopped) {
        return { stopped: true };
      }

      const currentState = options.resolveLoadDynamicState?.() || {};
      const requestViewMode = currentState.viewMode ?? options.viewMode;
      const requestSearchTerm = currentState.searchTerm ?? options.searchTerm;
      const requestSortLabel = currentState.sortLabel ?? options.sortLabel;
      const requestActiveGroupByField = currentState.activeGroupByField ?? options.activeGroupByField;
      const requestListOffset = currentState.listOffset ?? options.listOffset;
      const requestGroupWindowOffset = currentState.groupWindowOffset ?? options.groupWindowOffset;
      const requestGroupSampleLimit = currentState.groupSampleLimit ?? options.groupSampleLimit;
      const requestContractLimit = currentState.contractLimit ?? options.contractLimit;
      const requestGroupPageOffsets = currentState.groupPageOffsets ?? options.groupPageOffsets;

      const loadRequestPhaseResult = await options.executeLoadRequestPhase({
        executeLoadDataRequest: options.executeLoadDataRequest,
        input: options.buildLoadRequestInput({
          ...options.buildLoadRequestDynamicInput({
            contract: preflightPhaseResult.contract,
            typedContract: preflightPhaseResult.typedContract,
            viewMode: requestViewMode,
            resolvedModel: preflightPhaseResult.resolvedModel,
            searchTerm: requestSearchTerm,
            sortLabel: requestSortLabel,
            activeGroupByField: requestActiveGroupByField,
            listOffset: requestListOffset,
            groupWindowOffset: requestGroupWindowOffset,
            groupSampleLimit: requestGroupSampleLimit,
            contractLimit: requestContractLimit,
            groupPageOffsets: requestGroupPageOffsets,
            metaDomainRaw: (preflightPhaseResult.meta || {}).domain,
            sceneFiltersRaw: options.sceneFiltersRaw,
            metaContextRaw: (preflightPhaseResult.meta || {}).context,
          }),
        }),
        applyLoadRequestBlockedState: options.applyLoadRequestBlocked,
      });
      if (loadRequestPhaseResult.blocked) {
        return { stopped: true };
      }

      await options.executeLoadSuccessPhase({
        input: options.buildLoadSuccessDynamicInput({
          ...options.buildLoadSuccessPhaseInput({
            result: loadRequestPhaseResult.result || {},
            contractColumns: Array.isArray(loadRequestPhaseResult.contractColumns) ? loadRequestPhaseResult.contractColumns : [],
            baseDomain: Array.isArray(loadRequestPhaseResult.baseDomain) ? loadRequestPhaseResult.baseDomain : [],
            requestContext: (loadRequestPhaseResult.requestContext || {}) as Dict,
            requestContextRaw: String(loadRequestPhaseResult.requestContextRaw || ''),
            startedAt: options.startedAt,
            resolvedModel: String(preflightPhaseResult.resolvedModel || ''),
          }),
        }),
      });

      return { stopped: false };
    } catch (err) {
      options.executeLoadCatchPhase({
        input: {
          err,
          startedAt: options.startedAt,
        },
      });
      return { stopped: true };
    }
  }

  return {
    executeLoadMainPhase,
  };
}
