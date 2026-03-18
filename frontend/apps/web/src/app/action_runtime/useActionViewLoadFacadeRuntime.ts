type ExecuteLoadResult = {
  stopped: boolean;
};

type UseActionViewLoadFacadeRuntimeOptions = {
  executeLoad: () => Promise<ExecuteLoadResult>;
};

export function useActionViewLoadFacadeRuntime(options: UseActionViewLoadFacadeRuntimeOptions) {
  async function loadPage(): Promise<void> {
    const loadMainPhaseResult = await options.executeLoad();
    if (loadMainPhaseResult.stopped) {
      return;
    }
  }

  return {
    loadPage,
  };
}
