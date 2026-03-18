type Dict = Record<string, unknown>;

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
  groupWindowOffset: number;
  groupSampleLimit: number;
  contractLimit: number;
  groupPageOffsets: Record<string, number>;
  sceneFiltersRaw: unknown;
  executeLoadPreflightPhase: (input: { input: Dict }) => Promise<PreflightResult>;
  executeLoadRequestPhase: (input: {
    executeLoadDataRequest: (payload: Dict) => Promise<RequestResult>;
    input: Dict;
    applyLoadRequestBlockedState: (input: { blocked: boolean; message: string; statusInput: string }) => boolean;
  }) => Promise<RequestResult>;
  executeLoadDataRequest: (payload: Dict) => Promise<RequestResult>;
  buildLoadRequestInput: (input: Dict) => Dict;
  buildLoadRequestDynamicInput: (input: Dict) => Dict;
  applyLoadRequestBlocked: (input: { blocked: boolean; message: string; statusInput: string }) => boolean;
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

      const loadRequestPhaseResult = await options.executeLoadRequestPhase({
        executeLoadDataRequest: options.executeLoadDataRequest,
        input: options.buildLoadRequestInput({
          ...options.buildLoadRequestDynamicInput({
            contract: preflightPhaseResult.contract,
            typedContract: preflightPhaseResult.typedContract,
            viewMode: options.viewMode,
            resolvedModel: preflightPhaseResult.resolvedModel,
            searchTerm: options.searchTerm,
            sortLabel: options.sortLabel,
            activeGroupByField: options.activeGroupByField,
            groupWindowOffset: options.groupWindowOffset,
            groupSampleLimit: options.groupSampleLimit,
            contractLimit: options.contractLimit,
            groupPageOffsets: options.groupPageOffsets,
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
