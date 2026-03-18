type Dict = Record<string, unknown>;

type BeginLoadOptions = {
  applyActionViewLoadResetState: (input: Dict) => void;
  resetInput: Dict;
  clearError: () => void;
  actionId: { value: number };
  resolveLoadMissingActionIdErrorState: () => Dict;
  resolveLoadMissingActionApplyState: (input: { missingActionState: Dict; currentErrorMessage: string }) => {
    message: string;
    statusInput: string;
  };
  currentErrorMessage: () => string;
  setError: (error: Error, message: string) => void;
  deriveListStatus: (statusInput: string) => 'idle' | 'loading' | 'ok' | 'empty' | 'error';
  status: { value: 'idle' | 'loading' | 'ok' | 'empty' | 'error' };
};

type CatchLoadOptions = {
  err: unknown;
  startedAt: number;
  setError: (error: unknown, fallback: string) => void;
  errorMessage: () => string;
  errorTraceId: () => string;
  resolveLoadCatchState: (input: { errorMessage: string; traceId: string; startedAt: number }) => Dict;
  resolveLoadCatchListTotalState: (input: { catchState: Dict }) => number | null;
  resolveLoadCatchProjectScopeState: (input: { catchState: Dict }) => Dict;
  resolveLoadCatchTraceApplyState: (input: { catchState: Dict }) => { traceId: string };
  resolveLoadCatchStatusApplyInput: (input: { catchState: Dict }) => string;
  resolveLoadCatchLatencyState: (input: { catchState: Dict }) => number | null;
  deriveListStatus: (statusInput: string) => 'idle' | 'loading' | 'ok' | 'empty' | 'error';
  listTotalCount: { value: number | null };
  projectScopeTotals: { value: Record<string, number> };
  projectScopeMetrics: { value: Array<Record<string, unknown>> };
  traceId: { value: string };
  lastTraceId: { value: string };
  status: { value: 'idle' | 'loading' | 'ok' | 'empty' | 'error' };
  lastLatencyMs: { value: number | null };
};

export function useActionViewLoadLifecycleRuntime() {
  function beginActionViewLoad(options: BeginLoadOptions): { startedAt: number; shouldReturn: boolean } {
    options.applyActionViewLoadResetState(options.resetInput);
    options.clearError();
    const startedAt = Date.now();

    if (!options.actionId.value) {
      const missingActionState = options.resolveLoadMissingActionIdErrorState();
      const missingActionApplyState = options.resolveLoadMissingActionApplyState({
        missingActionState,
        currentErrorMessage: options.currentErrorMessage(),
      });
      options.setError(new Error(missingActionApplyState.message), missingActionApplyState.message);
      options.status.value = options.deriveListStatus(missingActionApplyState.statusInput);
      return { startedAt, shouldReturn: true };
    }

    return { startedAt, shouldReturn: false };
  }

  function handleActionViewLoadCatch(options: CatchLoadOptions) {
    options.setError(options.err, 'failed to load list');
    const catchState = options.resolveLoadCatchState({
      errorMessage: options.errorMessage(),
      traceId: options.errorTraceId(),
      startedAt: options.startedAt,
    });

    options.listTotalCount.value = options.resolveLoadCatchListTotalState({ catchState });

    const scopeState = options.resolveLoadCatchProjectScopeState({ catchState });
    options.projectScopeTotals.value = (scopeState.projectScopeTotals as Record<string, number>) || {};
    options.projectScopeMetrics.value = (scopeState.projectScopeMetrics as Array<Record<string, unknown>>) || [];

    const traceState = options.resolveLoadCatchTraceApplyState({ catchState });
    const statusInput = options.resolveLoadCatchStatusApplyInput({ catchState });
    options.traceId.value = traceState.traceId;
    options.lastTraceId.value = traceState.traceId;
    options.status.value = options.deriveListStatus(statusInput);

    options.lastLatencyMs.value = options.resolveLoadCatchLatencyState({ catchState });
  }

  return {
    beginActionViewLoad,
    handleActionViewLoadCatch,
  };
}

