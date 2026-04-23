import {
  mapBatchFailureDetailLines,
  resolveBatchDetailLinesMerge,
  resolveBatchFailureCsvState,
  resolveBatchFailurePagingState,
  resolveBatchFailurePreviewRows,
  type ActionViewBatchDetailLine,
} from './actionViewBatchArtifactsRuntime';

type Dict = Record<string, unknown>;

export function resolveBatchFailurePreviewState(result: Dict): Array<Record<string, unknown>> {
  return resolveBatchFailurePreviewRows(result);
}

export function resolveBatchFailureLinesState(options: {
  preview: Array<Record<string, unknown>>;
  resolveHint: (row: {
    suggested_action?: string;
    reason_code?: string;
    retryable?: boolean;
  }) => string;
  resolveActionMeta: (row: {
    suggested_action?: string;
  }) => {
    canRun: boolean;
    raw: string;
    label: string;
  };
  retryableText: string;
  nonRetryableText: string;
}): ActionViewBatchDetailLine[] {
  return mapBatchFailureDetailLines({
    preview: options.preview,
    resolveHint: options.resolveHint,
    resolveActionMeta: options.resolveActionMeta,
    retryableText: options.retryableText,
    nonRetryableText: options.nonRetryableText,
  });
}

export function resolveBatchFailureDetailMergeState(options: {
  append: boolean;
  previous: ActionViewBatchDetailLine[];
  next: ActionViewBatchDetailLine[];
}): ActionViewBatchDetailLine[] {
  return resolveBatchDetailLinesMerge({
    append: options.append,
    previous: options.previous,
    next: options.next,
  });
}

export function resolveBatchFailurePagingApplyState(options: {
  result: Dict;
  previewLength: number;
}): {
  nextFailedOffset: number;
  nextFailedLimit: number;
  hasMoreFailures: boolean;
} {
  return resolveBatchFailurePagingState({
    result: options.result,
    previewLength: options.previewLength,
  });
}

export function resolveBatchFailureCsvApplyState(options: {
  result: Dict;
  previousFileName: string;
  previousContentB64: string;
}): {
  fileName: string;
  contentB64: string;
} {
  return resolveBatchFailureCsvState({
    result: options.result,
    previousFileName: options.previousFileName,
    previousContentB64: options.previousContentB64,
  });
}
