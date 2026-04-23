type WorkbenchTargetBuilder = (payload: Record<string, unknown>) => unknown;
type WorkbenchQueryResolver = (code: string, payload: Record<string, unknown>) => Record<string, unknown>;

export function resolveCapabilityMissingRedirectTarget(options: {
  capabilityMissingCode: string;
  guardPayload: Record<string, unknown> | null;
  buildWorkbenchRouteTargetFn: WorkbenchTargetBuilder;
  resolveWorkbenchQueryFn: WorkbenchQueryResolver;
}): unknown | null {
  if (!options.guardPayload) return null;
  return options.buildWorkbenchRouteTargetFn(
    options.resolveWorkbenchQueryFn(options.capabilityMissingCode, options.guardPayload),
  );
}

export function resolveMissingModelRedirectTarget(options: {
  missingModelRedirect: { code: string; payload: Record<string, unknown> } | null;
  buildWorkbenchRouteTargetFn: WorkbenchTargetBuilder;
  resolveWorkbenchQueryFn: WorkbenchQueryResolver;
}): unknown | null {
  if (!options.missingModelRedirect) return null;
  return options.buildWorkbenchRouteTargetFn(
    options.resolveWorkbenchQueryFn(options.missingModelRedirect.code, options.missingModelRedirect.payload),
  );
}

export function resolveLoadMissingActionApplyState(options: {
  missingActionState: { message: string; recordsLength: number };
  currentErrorMessage: string;
}): {
  message: string;
  statusInput: { error: string; recordsLength: number };
} {
  return {
    message: options.missingActionState.message,
    statusInput: {
      error: options.currentErrorMessage,
      recordsLength: options.missingActionState.recordsLength,
    },
  };
}

export function resolveLoadMissingViewTypeApplyState(options: {
  missingViewTypeState: { message: string; recordsLength: number };
  currentErrorMessage: string;
}): {
  message: string;
  statusInput: { error: string; recordsLength: number };
} {
  return {
    message: options.missingViewTypeState.message,
    statusInput: {
      error: options.currentErrorMessage,
      recordsLength: options.missingViewTypeState.recordsLength,
    },
  };
}

export function resolveLoadMissingResolvedModelApplyState(options: {
  missingModelErrorState: { message: string; statusError: string; statusRecordsLength: number };
  currentErrorMessage: string;
}): {
  message: string;
  statusInput: { error: string; recordsLength: number };
} {
  return {
    message: options.missingModelErrorState.message,
    statusInput: {
      error: options.currentErrorMessage || options.missingModelErrorState.statusError,
      recordsLength: options.missingModelErrorState.statusRecordsLength,
    },
  };
}
