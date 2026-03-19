type Dict = Record<string, unknown>;

type LoadRequestResult = {
  blocked: boolean;
  message: string;
  statusInput: string;
  result?: Dict;
  contractColumns?: string[];
  requestedFields?: string[];
  baseDomain?: unknown[];
  activeDomain?: unknown[];
  requestContext?: Dict;
  requestContextRaw?: string;
  requestPayload?: Dict;
};

type ExecuteLoadRequestPhaseOptions = {
  executeLoadDataRequest: (input: Dict) => Promise<LoadRequestResult>;
  input: Dict;
  applyLoadRequestBlockedState: (input: {
    blocked: boolean;
    message: string;
    statusInput: string;
  }) => boolean;
};

type ExecuteLoadRequestPhaseResult =
  | { blocked: true }
  | {
      blocked: false;
      result: Dict;
      contractColumns: string[];
      baseDomain: unknown[];
      activeDomain: unknown[];
      requestContext: Dict;
      requestContextRaw: string;
      requestPayload: Dict;
    };

export function useActionViewLoadRequestPhaseRuntime() {
  async function executeLoadRequestPhase(options: ExecuteLoadRequestPhaseOptions): Promise<ExecuteLoadRequestPhaseResult> {
    const loadRequestResult = await options.executeLoadDataRequest(options.input);
    if (options.applyLoadRequestBlockedState({
      blocked: loadRequestResult.blocked,
      message: String(loadRequestResult.message || ''),
      statusInput: String(loadRequestResult.statusInput || ''),
    })) {
      return { blocked: true };
    }

    return {
      blocked: false,
      result: (loadRequestResult.result || {}) as Dict,
      contractColumns: Array.isArray(loadRequestResult.contractColumns) ? loadRequestResult.contractColumns : [],
      baseDomain: Array.isArray(loadRequestResult.baseDomain) ? loadRequestResult.baseDomain : [],
      activeDomain: Array.isArray(loadRequestResult.activeDomain) ? loadRequestResult.activeDomain : [],
      requestContext: (loadRequestResult.requestContext || {}) as Dict,
      requestContextRaw: String(loadRequestResult.requestContextRaw || ''),
      requestPayload: (loadRequestResult.requestPayload || {}) as Dict,
    };
  }

  return {
    executeLoadRequestPhase,
  };
}
