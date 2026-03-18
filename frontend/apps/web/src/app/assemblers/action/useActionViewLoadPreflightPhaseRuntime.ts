type Dict = Record<string, unknown>;

type ContinuePayload = {
  contract: unknown;
  meta: Dict | null;
  typedContract: Dict;
  resolvedModel: string;
};

type UseActionViewLoadPreflightPhaseRuntimeOptions = {
  executeLoadPreflight: (input: Dict) => Promise<Dict>;
  buildLoadPreflightInput: (input: Dict) => Dict;
  applyLoadPreflightBlocked: (input: { kind: 'blocked'; message: string; statusInput: string }) => void;
  applyLoadPreflightContinue: (input: Dict) => ContinuePayload;
  handleRedirect: (target: unknown) => Promise<void>;
};

type ExecuteLoadPreflightPhaseOptions = {
  input: Dict;
};

type ExecuteLoadPreflightPhaseResult =
  | { stopped: true }
  | ({ stopped: false } & ContinuePayload);

export function useActionViewLoadPreflightPhaseRuntime(options: UseActionViewLoadPreflightPhaseRuntimeOptions) {
  async function executeLoadPreflightPhase(input: ExecuteLoadPreflightPhaseOptions): Promise<ExecuteLoadPreflightPhaseResult> {
    const preflightResult = await options.executeLoadPreflight(options.buildLoadPreflightInput(input.input));
    const kind = String((preflightResult as Dict).kind || '');
    if (kind === 'redirect') {
      await options.handleRedirect((preflightResult as Dict).target);
      return { stopped: true };
    }
    if (kind === 'handled') {
      return { stopped: true };
    }
    if (kind === 'blocked') {
      options.applyLoadPreflightBlocked(preflightResult as { kind: 'blocked'; message: string; statusInput: string });
      return { stopped: true };
    }

    const continuePayload = options.applyLoadPreflightContinue(preflightResult);
    return {
      stopped: false,
      ...continuePayload,
    };
  }

  return {
    executeLoadPreflightPhase,
  };
}
