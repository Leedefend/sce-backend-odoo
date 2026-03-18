type Dict = Record<string, unknown>;

type UseActionViewLoadCatchPhaseRuntimeOptions = {
  handleActionViewLoadCatch: (input: Dict) => void;
  staticInput: Dict;
};

type ExecuteLoadCatchPhaseOptions = {
  input: Dict;
};

export function useActionViewLoadCatchPhaseRuntime(options: UseActionViewLoadCatchPhaseRuntimeOptions) {
  function executeLoadCatchPhase(payload: ExecuteLoadCatchPhaseOptions): void {
    options.handleActionViewLoadCatch({
      ...payload.input,
      ...options.staticInput,
    });
  }

  return {
    executeLoadCatchPhase,
  };
}

