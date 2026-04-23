type Dict = Record<string, unknown>;

export type ActionViewBatchRequest = {
  model: string;
  ids: number[];
  action: 'archive' | 'activate' | 'assign';
  assigneeId?: number;
  ifMatchMap: Record<number, string>;
  idempotencyKey: string;
  context: Record<string, unknown>;
};

export type ActionViewBatchDetailLine = {
  text: string;
  actionRaw?: string;
  actionLabel?: string;
};

type BatchFailurePreviewRow = {
  id?: number | string;
  reason_code?: string;
  message?: string;
  retryable?: boolean;
  suggested_action?: string;
};

type BatchFailureActionMeta = {
  canRun: boolean;
  raw: string;
  label: string;
};

export function resolveBatchFailurePreviewRows(result: Dict): Array<Record<string, unknown>> {
  return Array.isArray(result.failed_preview) ? (result.failed_preview as Array<Record<string, unknown>>) : [];
}

export function resolveBatchFailurePagingState(options: {
  result: Dict;
  previewLength: number;
}): {
  nextFailedOffset: number;
  nextFailedLimit: number;
  hasMoreFailures: boolean;
} {
  return {
    nextFailedOffset: Number(options.result.failed_page_offset || 0) + options.previewLength,
    nextFailedLimit: Number(options.result.failed_page_limit || 12) || 12,
    hasMoreFailures: Boolean(options.result.failed_has_more),
  };
}

export function resolveBatchFailureCsvState(options: {
  result: Dict;
  previousFileName: string;
  previousContentB64: string;
}): {
  fileName: string;
  contentB64: string;
} {
  const hasFileName = 'failed_csv_file_name' in options.result && Boolean(options.result.failed_csv_file_name);
  const hasContent = 'failed_csv_content_b64' in options.result && Boolean(options.result.failed_csv_content_b64);
  return {
    fileName: hasFileName ? String(options.result.failed_csv_file_name || '') : options.previousFileName,
    contentB64: hasContent ? String(options.result.failed_csv_content_b64 || '') : options.previousContentB64,
  };
}

export function resolveLoadMoreFailuresGuard(options: {
  hasMoreFailures: boolean;
  lastBatchRequest: ActionViewBatchRequest | null;
}): { ok: true; request: ActionViewBatchRequest } | { ok: false } {
  const request = options.lastBatchRequest;
  if (!options.hasMoreFailures || !request) return { ok: false };
  return { ok: true, request };
}

export function buildLoadMoreFailuresRequest(options: {
  request: ActionViewBatchRequest;
  failedLimit: number;
  failedOffset: number;
}): Record<string, unknown> {
  return {
    model: options.request.model,
    ids: options.request.ids,
    action: options.request.action,
    assigneeId: options.request.assigneeId,
    ifMatchMap: options.request.ifMatchMap,
    idempotencyKey: options.request.idempotencyKey,
    failedPreviewLimit: options.failedLimit,
    failedOffset: options.failedOffset,
    failedLimit: options.failedLimit,
    exportFailedCsv: false,
    context: options.request.context,
  };
}

export function resolveBatchFailureRetryTag(options: {
  retryable: boolean | undefined;
  retryableText: string;
  nonRetryableText: string;
}): string {
  if (options.retryable === true) return options.retryableText;
  if (options.retryable === false) return options.nonRetryableText;
  return '';
}

export function mapBatchFailureDetailLines(options: {
  preview: Array<Record<string, unknown>>;
  resolveHint: (row: BatchFailurePreviewRow) => string;
  resolveActionMeta: (row: BatchFailurePreviewRow) => BatchFailureActionMeta;
  retryableText: string;
  nonRetryableText: string;
}): ActionViewBatchDetailLine[] {
  return options.preview.map((rawRow) => {
    const row = rawRow as BatchFailurePreviewRow;
    const hint = options.resolveHint(row);
    const retryTag = resolveBatchFailureRetryTag({
      retryable: row.retryable,
      retryableText: options.retryableText,
      nonRetryableText: options.nonRetryableText,
    });
    const text = [`#${row.id || ''} ${row.reason_code || ''}: ${row.message || ''}`, retryTag, hint].filter(Boolean).join(' | ');
    const actionMeta = options.resolveActionMeta(row);
    return {
      text,
      actionRaw: actionMeta.canRun ? actionMeta.raw : '',
      actionLabel: actionMeta.label,
    };
  });
}

export function resolveBatchDetailLinesMerge(options: {
  append: boolean;
  previous: ActionViewBatchDetailLine[];
  next: ActionViewBatchDetailLine[];
}): ActionViewBatchDetailLine[] {
  if (!options.append) return options.next;
  return [...options.previous, ...options.next];
}

export function resolveBatchArtifactsReset(options: {
  batchFailedLimit: number;
}): {
  batchMessage: string;
  batchDetails: ActionViewBatchDetailLine[];
  failedCsvFileName: string;
  failedCsvContentB64: string;
  batchFailedOffset: number;
  batchFailedLimit: number;
  batchHasMoreFailures: boolean;
  lastBatchRequest: ActionViewBatchRequest | null;
} {
  return {
    batchMessage: '',
    batchDetails: [],
    failedCsvFileName: '',
    failedCsvContentB64: '',
    batchFailedOffset: 0,
    batchFailedLimit: options.batchFailedLimit,
    batchHasMoreFailures: false,
    lastBatchRequest: null,
  };
}
