import type { Ref } from 'vue';

type BatchDetailLine = { text: string; actionRaw?: string; actionLabel?: string };

type UseActionViewBatchArtifactGlueRuntimeOptions = {
  batchDetails: Ref<BatchDetailLine[]>;
  batchFailedOffset: Ref<number>;
  batchFailedLimit: Ref<number>;
  batchHasMoreFailures: Ref<boolean>;
  failedCsvFileName: Ref<string>;
  failedCsvContentB64: Ref<string>;
  pageText: (key: string, fallback: string) => string;
  resolveSuggestedAction: (raw?: string) => string;
  describeSuggestedAction: (raw?: string) => string;
  runSuggestedAction: (raw?: string, options?: { onRetry?: () => void }) => void;
  reload: () => void;
  resolveBatchFailurePreviewState: (result: Record<string, unknown>) => Array<Record<string, unknown>>;
  resolveBatchRetryTagTexts: (input: { text: (key: string, fallback: string) => string }) => {
    retryableText: string;
    nonRetryableText: string;
  };
  resolveBatchFailureLinesState: (input: {
    preview: Array<Record<string, unknown>>;
    resolveHint: (row: Record<string, unknown>) => string;
    resolveActionMeta: (row: Record<string, unknown>) => Record<string, unknown>;
    retryableText: string;
    nonRetryableText: string;
  }) => BatchDetailLine[];
  resolveBatchFailureHintResolver: (input: { resolveSuggestedActionFn: (raw?: string) => string }) => (row: Record<string, unknown>) => string;
  resolveBatchFailureActionMetaResolver: (input: {
    describeSuggestedActionFn: (raw?: string) => string;
    hasRetryHandler: boolean;
    hasActionHandler: boolean;
  }) => (row: Record<string, unknown>) => Record<string, unknown>;
  resolveBatchFailureDetailMergeState: (input: {
    append: boolean;
    previous: BatchDetailLine[];
    next: BatchDetailLine[];
  }) => BatchDetailLine[];
  resolveBatchFailurePagingApplyState: (input: {
    result: Record<string, unknown>;
    previewLength: number;
  }) => {
    nextFailedOffset: number;
    nextFailedLimit: number;
    hasMoreFailures: boolean;
  };
  resolveBatchFailureCsvApplyState: (input: {
    result: Record<string, unknown>;
    previousFileName: string;
    previousContentB64: string;
  }) => {
    fileName: string;
    contentB64: string;
  };
};

export function useActionViewBatchArtifactGlueRuntime(options: UseActionViewBatchArtifactGlueRuntimeOptions) {
  function downloadCsvBase64(filename: string, mimeType: string, contentB64: string) {
    if (!contentB64) return;
    const binary = atob(contentB64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: mimeType || 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || 'export.csv';
    link.click();
    URL.revokeObjectURL(url);
  }

  function applyBatchFailureArtifacts(result: {
    failed_preview?: Array<{ id: number; reason_code: string; message: string; retryable?: boolean; suggested_action?: string }>;
    failed_page_offset?: number;
    failed_page_limit?: number;
    failed_has_more?: boolean;
    failed_truncated?: number;
    failed_csv_file_name?: string;
    failed_csv_content_b64?: string;
  }, runtimeOptions?: { append?: boolean }) {
    const preview = options.resolveBatchFailurePreviewState(result as Record<string, unknown>);
    const retryTagTexts = options.resolveBatchRetryTagTexts({ text: options.pageText });
    const lines: BatchDetailLine[] = options.resolveBatchFailureLinesState({
      preview,
      resolveHint: options.resolveBatchFailureHintResolver({
        resolveSuggestedActionFn: options.resolveSuggestedAction,
      }),
      resolveActionMeta: options.resolveBatchFailureActionMetaResolver({
        describeSuggestedActionFn: options.describeSuggestedAction,
        hasRetryHandler: true,
        hasActionHandler: false,
      }),
      retryableText: retryTagTexts.retryableText,
      nonRetryableText: retryTagTexts.nonRetryableText,
    });
    options.batchDetails.value = options.resolveBatchFailureDetailMergeState({
      append: Boolean(runtimeOptions?.append),
      previous: options.batchDetails.value,
      next: lines,
    });
    const pagingState = options.resolveBatchFailurePagingApplyState({
      result: result as Record<string, unknown>,
      previewLength: preview.length,
    });
    options.batchFailedOffset.value = pagingState.nextFailedOffset;
    options.batchFailedLimit.value = pagingState.nextFailedLimit;
    options.batchHasMoreFailures.value = pagingState.hasMoreFailures;
    const csvState = options.resolveBatchFailureCsvApplyState({
      result: result as Record<string, unknown>,
      previousFileName: options.failedCsvFileName.value,
      previousContentB64: options.failedCsvContentB64.value,
    });
    options.failedCsvFileName.value = csvState.fileName;
    options.failedCsvContentB64.value = csvState.contentB64;
  }

  function handleBatchDetailAction(actionRaw: string) {
    options.runSuggestedAction(actionRaw, { onRetry: options.reload });
  }

  return {
    downloadCsvBase64,
    applyBatchFailureArtifacts,
    handleBatchDetailAction,
  };
}

