type Dict = Record<string, unknown>;

type UseActionViewLoadMainBoundRuntimeOptions = {
  buildLoadMainPhaseInput: (input: { startedAt: number }) => Dict;
  executeLoadMainPhase: (input: Dict) => Promise<{ stopped: boolean }>;
};

export function useActionViewLoadMainBoundRuntime(options: UseActionViewLoadMainBoundRuntimeOptions) {
  async function executeLoadMainBound(input: { startedAt: number }): Promise<{ stopped: boolean }> {
    return options.executeLoadMainPhase(options.buildLoadMainPhaseInput({ startedAt: input.startedAt }));
  }

  return {
    executeLoadMainBound,
  };
}

