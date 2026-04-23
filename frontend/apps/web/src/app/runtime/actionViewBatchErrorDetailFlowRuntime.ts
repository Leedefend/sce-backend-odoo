type BatchErrorFallback = {
  model: string;
  op: string;
  label: string;
};

export function resolveBatchActionErrorFallback(options: {
  targetModel: string;
  action: 'archive' | 'activate' | 'delete';
  resolveActionLabel: (action: 'archive' | 'activate' | 'delete') => string;
}): BatchErrorFallback {
  return {
    model: options.targetModel,
    op: options.action,
    label: options.resolveActionLabel(options.action),
  };
}

export function resolveBatchAssignErrorFallback(options: {
  targetModel: string;
  text: (key: string, fallback?: string) => string;
}): BatchErrorFallback {
  return {
    model: options.targetModel,
    op: 'assign',
    label: options.text('batch_label_assign', '批量指派'),
  };
}

export function resolveBatchExportErrorFallback(options: {
  targetModel: string;
  text: (key: string, fallback?: string) => string;
}): BatchErrorFallback {
  return {
    model: options.targetModel,
    op: 'export_csv',
    label: options.text('batch_label_export', '批量导出'),
  };
}

export function resolveBatchLoadMoreErrorFallback(options: {
  model: string;
  action: string;
  text: (key: string, fallback?: string) => string;
}): BatchErrorFallback {
  return {
    model: options.model,
    op: options.action,
    label: options.text('batch_label_load_more_failed', '加载更多失败'),
  };
}

export function resolveBatchErrorDetailLines(options: {
  err: unknown;
  text: (key: string, fallback?: string) => string;
  fallback: BatchErrorFallback;
  buildBatchErrorLine: (input: {
    err: unknown;
    text: (key: string, fallback?: string) => string;
    resolveHint: (input: { suggestedAction: unknown; reasonCode: unknown; retryable: unknown }) => string;
    fallback: BatchErrorFallback;
  }) => string;
  resolveHint: (input: { suggestedAction: unknown; reasonCode: unknown; retryable: unknown }) => string;
}): Array<{ text: string }> {
  return [{
    text: options.buildBatchErrorLine({
      err: options.err,
      text: options.text,
      resolveHint: options.resolveHint,
      fallback: options.fallback,
    }),
  }];
}
