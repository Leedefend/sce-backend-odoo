type ResolveSuggestedActionFn = (
  suggestedAction: unknown,
  reasonCode: unknown,
  retryable: unknown,
) => string;

type DescribeSuggestedActionFn = (
  suggestedAction: unknown,
  options: {
    hasRetryHandler: boolean;
    hasActionHandler: boolean;
  },
) => {
  canRun: boolean;
  parsed: { raw: string };
  label: string;
};

type TextFn = (key: string, fallback?: string) => string;

export function resolveBatchFailureHintResolver(options: {
  resolveSuggestedActionFn: ResolveSuggestedActionFn;
}): (row: { suggested_action?: unknown; reason_code?: unknown; retryable?: unknown }) => string {
  return (row) => options.resolveSuggestedActionFn(row.suggested_action, row.reason_code, row.retryable);
}

export function resolveBatchErrorHintResolver(options: {
  resolveSuggestedActionFn: ResolveSuggestedActionFn;
}): (input: { suggestedAction?: unknown; reasonCode?: unknown; retryable?: unknown }) => string {
  return (input) => options.resolveSuggestedActionFn(input.suggestedAction, input.reasonCode, input.retryable);
}

export function resolveBatchFailureActionMetaResolver(options: {
  describeSuggestedActionFn: DescribeSuggestedActionFn;
  hasRetryHandler: boolean;
  hasActionHandler: boolean;
}): (row: { suggested_action?: unknown }) => { canRun: boolean; raw: string; label: string } {
  return (row) => {
    const action = options.describeSuggestedActionFn(row.suggested_action, {
      hasRetryHandler: options.hasRetryHandler,
      hasActionHandler: options.hasActionHandler,
    });
    return {
      canRun: action.canRun,
      raw: action.parsed.raw,
      label: action.label,
    };
  };
}

export function resolveBatchRetryTagTexts(options: {
  text: TextFn;
}): {
  retryableText: string;
  nonRetryableText: string;
} {
  return {
    retryableText: options.text('retry_tag_retryable', '可重试'),
    nonRetryableText: options.text('retry_tag_non_retryable', '不可重试'),
  };
}
