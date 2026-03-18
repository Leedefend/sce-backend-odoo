type Dict = Record<string, unknown>;

type BeginResult = {
  startedAt: number;
  shouldReturn: boolean;
};

type UseActionViewLoadBeginPhaseRuntimeOptions = {
  beginActionViewLoad: (input: Dict) => BeginResult;
  buildLoadBeginInput: (input: Dict) => Dict;
};

export function useActionViewLoadBeginPhaseRuntime(options: UseActionViewLoadBeginPhaseRuntimeOptions) {
  function executeLoadBeginPhase(input: { input: Dict }): BeginResult {
    return options.beginActionViewLoad(options.buildLoadBeginInput(input.input));
  }

  return {
    executeLoadBeginPhase,
  };
}

