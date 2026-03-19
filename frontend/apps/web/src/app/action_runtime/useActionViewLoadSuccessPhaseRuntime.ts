type Dict = Record<string, unknown>;

type UseActionViewLoadSuccessPhaseRuntimeOptions = {
  applyLoadSuccess: (input: Dict) => Promise<void>;
  staticInput: Dict;
};

type ExecuteLoadSuccessPhaseOptions = {
  input: Dict;
};

export function useActionViewLoadSuccessPhaseRuntime(options: UseActionViewLoadSuccessPhaseRuntimeOptions) {
  async function executeLoadSuccessPhase(input: ExecuteLoadSuccessPhaseOptions): Promise<void> {
    await options.applyLoadSuccess({
      ...input.input,
      ...options.staticInput,
    });
  }

  return {
    executeLoadSuccessPhase,
  };
}
