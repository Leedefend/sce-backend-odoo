import {
  resolveBatchArtifactsReset,
  type ActionViewBatchDetailLine,
  type ActionViewBatchRequest,
} from './actionViewBatchArtifactsRuntime';
import { resolveBatchErrorDetailLines } from './actionViewBatchErrorDetailFlowRuntime';
import { resolveLoadMoreFailuresErrorDetails } from './actionViewLoadMoreFailuresFlowRuntime';

type TextFn = (key: string, fallback?: string) => string;

type HintInput = {
  suggestedAction: unknown;
  reasonCode: unknown;
  retryable: unknown;
};

type BatchErrorFallback = {
  model: string;
  op: string;
  label: string;
};

type BuildBatchErrorLine = (input: {
  err: unknown;
  text: TextFn;
  resolveHint: (input: HintInput) => string;
  fallback: BatchErrorFallback;
}) => string;

export function resolveBatchOperationResetState(options: {
  batchFailedLimit: number;
}) {
  return resolveBatchArtifactsReset({ batchFailedLimit: options.batchFailedLimit });
}

export function resolveBatchExportResetState(options: {
  batchFailedLimit: number;
}): {
  batchMessage: string;
  batchDetails: ActionViewBatchDetailLine[];
  failedCsvFileName: string;
  failedCsvContentB64: string;
} {
  const resetState = resolveBatchArtifactsReset({ batchFailedLimit: options.batchFailedLimit });
  return {
    batchMessage: resetState.batchMessage,
    batchDetails: resetState.batchDetails,
    failedCsvFileName: resetState.failedCsvFileName,
    failedCsvContentB64: resetState.failedCsvContentB64,
  };
}

export function resolveBatchFailureCatchState(options: {
  err: unknown;
  text: TextFn;
  buildBatchErrorLine: BuildBatchErrorLine;
  resolveHint: (input: HintInput) => string;
  fallback: BatchErrorFallback;
}): {
  batchDetails: ActionViewBatchDetailLine[];
  failedCsvFileName: string;
  failedCsvContentB64: string;
  batchFailedOffset: number;
  batchHasMoreFailures: boolean;
  lastBatchRequest: ActionViewBatchRequest | null;
} {
  return {
    batchDetails: resolveBatchErrorDetailLines({
      err: options.err,
      text: options.text,
      buildBatchErrorLine: options.buildBatchErrorLine,
      resolveHint: options.resolveHint,
      fallback: options.fallback,
    }),
    failedCsvFileName: '',
    failedCsvContentB64: '',
    batchFailedOffset: 0,
    batchHasMoreFailures: false,
    lastBatchRequest: null,
  };
}

export function resolveBatchExportCatchState(options: {
  err: unknown;
  text: TextFn;
  buildBatchErrorLine: BuildBatchErrorLine;
  resolveHint: (input: HintInput) => string;
  fallback: BatchErrorFallback;
}): {
  batchDetails: ActionViewBatchDetailLine[];
} {
  return {
    batchDetails: resolveBatchErrorDetailLines({
      err: options.err,
      text: options.text,
      buildBatchErrorLine: options.buildBatchErrorLine,
      resolveHint: options.resolveHint,
      fallback: options.fallback,
    }),
  };
}

export function resolveLoadMoreFailuresCatchState(options: {
  err: unknown;
  text: TextFn;
  buildBatchErrorLine: BuildBatchErrorLine;
  resolveHint: (input: HintInput) => string;
  fallback: BatchErrorFallback;
}): {
  batchDetails: ActionViewBatchDetailLine[];
} {
  return {
    batchDetails: resolveLoadMoreFailuresErrorDetails({
      err: options.err,
      text: options.text,
      buildBatchErrorLine: options.buildBatchErrorLine,
      resolveHint: options.resolveHint,
      fallback: options.fallback,
    }),
  };
}
