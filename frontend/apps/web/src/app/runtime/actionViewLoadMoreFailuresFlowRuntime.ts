import { buildLoadMoreFailuresRequest, resolveLoadMoreFailuresGuard } from './actionViewBatchArtifactsRuntime';
import { resolveBatchErrorDetailLines, resolveBatchLoadMoreErrorFallback } from './actionViewBatchErrorDetailFlowRuntime';

type BatchRequest = {
  model: string;
  action: 'archive' | 'activate' | 'assign';
  ids: number[];
  ifMatchMap: Record<number, string>;
  idempotencyKey: string;
  context: Record<string, unknown>;
  assigneeId?: number;
};

export function resolveLoadMoreFailuresGuardPlan(options: {
  hasMoreFailures: boolean;
  lastBatchRequest: BatchRequest | null;
}): { ok: boolean; request?: BatchRequest } {
  return resolveLoadMoreFailuresGuard({
    hasMoreFailures: options.hasMoreFailures,
    lastBatchRequest: options.lastBatchRequest,
  });
}

export function resolveLoadMoreFailuresRequestPayload(options: {
  request: BatchRequest;
  failedOffset: number;
  failedLimit: number;
}) {
  return buildLoadMoreFailuresRequest({
    request: options.request,
    failedOffset: options.failedOffset,
    failedLimit: options.failedLimit,
  });
}

export function resolveLoadMoreFailuresApplyPlan(): {
  append: boolean;
} {
  return { append: true };
}

export function resolveLoadMoreFailuresErrorFallback(options: {
  model: string;
  action: string;
  text: (key: string, fallback?: string) => string;
}) {
  return resolveBatchLoadMoreErrorFallback({
    model: options.model,
    action: options.action,
    text: options.text,
  });
}

export function resolveLoadMoreFailuresErrorDetails(options: {
  err: unknown;
  text: (key: string, fallback?: string) => string;
  fallback: { model: string; op: string; label: string };
  buildBatchErrorLine: (input: {
    err: unknown;
    text: (key: string, fallback?: string) => string;
    resolveHint: (input: { suggestedAction: unknown; reasonCode: unknown; retryable: unknown }) => string;
    fallback: { model: string; op: string; label: string };
  }) => string;
  resolveHint: (input: { suggestedAction: unknown; reasonCode: unknown; retryable: unknown }) => string;
}): Array<{ text: string }> {
  return resolveBatchErrorDetailLines({
    err: options.err,
    text: options.text,
    fallback: options.fallback,
    buildBatchErrorLine: options.buildBatchErrorLine,
    resolveHint: options.resolveHint,
  });
}
