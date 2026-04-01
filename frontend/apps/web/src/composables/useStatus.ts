import { ref } from 'vue';
import { ApiError } from '../api/client';
import { describeSuggestedAction } from './useSuggestedAction';

export interface StatusError {
  message: string;
  code?: number | string;
  traceId?: string;
  hint?: string;
  kind?: string;
  errorCategory?: string;
  retryable?: boolean;
  reasonCode?: string;
  suggestedAction?: string;
  details?: Record<string, unknown>;
}

export interface StatusCopy {
  title: string;
  message: string;
  hint?: string;
}

type EmptyCopyContext = {
  primaryActionLabel?: string;
};

export function resolveSuggestedAction(
  suggestedAction?: string,
  reasonCode?: string,
  retryable?: boolean,
): string {
  const hintByAction = describeSuggestedAction(suggestedAction).hint;
  if (hintByAction) return hintByAction;

  const code = String(reasonCode || '').toUpperCase();
  if (code.includes('PERMISSION') || code.includes('FORBIDDEN')) return 'Check role permissions or contact an administrator.';
  if (code.includes('NOT_FOUND')) return 'Refresh the list because the record may be removed or hidden.';
  if (code.includes('CONFLICT')) return 'Reload current data and retry with latest version.';
  if (code.includes('NETWORK')) return 'Check network connectivity and retry.';

  if (retryable === true) return 'This failure is retryable. Try again now or after a short delay.';
  if (retryable === false) return 'This failure is non-retryable. Resolve data/permission issues first.';
  return '';
}

export function buildStatusError(err: unknown, fallbackMessage: string, kind?: string): StatusError {
  if (err instanceof ApiError) {
    const code = err.status;
    const suggestedAction = err.suggestedAction || resolveSuggestedAction(undefined, err.reasonCode, err.retryable);
    return {
      message: err.message,
      code,
      traceId: err.traceId,
      hint: err.hint || getHint(code, err.kind, err.errorCategory, err.retryable),
      kind: kind || err.kind,
      errorCategory: err.errorCategory,
      retryable: err.retryable,
      reasonCode: err.reasonCode,
      suggestedAction: suggestedAction || undefined,
      details: err.details,
    };
  }
  const message = err instanceof Error ? err.message : fallbackMessage;
  return { message, kind };
}

function normalizeCode(code?: number | string) {
  if (typeof code === 'number') return code;
  if (typeof code === 'string') {
    const parsed = Number(code);
    return Number.isNaN(parsed) ? undefined : parsed;
  }
  return undefined;
}

function normalizeCategory(category?: string): string {
  return String(category || '')
    .trim()
    .toLowerCase();
}

function mergeHint(...parts: Array<string | undefined>): string | undefined {
  const text = parts
    .map((part) => String(part || '').trim())
    .filter(Boolean)
    .join(' ');
  return text || undefined;
}

function errorContextHint(err?: StatusError | null): string {
  const model = String(err?.details?.model || '').trim();
  const op = String(err?.details?.op || '').trim().toLowerCase();
  const reasonCode = String(err?.reasonCode || '').trim().toUpperCase();
  const scope = [model, op].filter(Boolean).join('/');
  if (!scope && !reasonCode) return '';
  if (scope && reasonCode) return `Context: ${scope} [${reasonCode}].`;
  if (scope) return `Context: ${scope}.`;
  return `Context: [${reasonCode}].`;
}

function getHint(code?: number | string, kind?: string, errorCategory?: string, retryable?: boolean): string {
  const numericCode = normalizeCode(code);
  const category = normalizeCategory(errorCategory);
  if (category === 'auth') return 'Login session may be invalid or expired. Please login again.';
  if (category === 'permission') return 'Access is restricted. Verify your role/capabilities and retry.';
  if (category === 'validation') return 'Submitted parameters are invalid. Fix input and retry.';
  if (category === 'conflict') return 'Data changed on server. Reload latest data and retry.';
  if (category === 'business') return 'Business rules blocked this action. Resolve the blocker and retry.';
  if (category === 'system') return 'Backend service exception occurred. Retry later or contact support.';
  if (retryable === true) return 'This failure is retryable. Try again now or after a short delay.';
  if (retryable === false) return 'This failure is non-retryable. Resolve data/permission issues first.';
  if (kind === 'network' || numericCode === 0) return 'Check network connectivity and API availability.';
  if (numericCode === 401) return 'Session expired. Please login again.';
  if (numericCode === 403) return 'Check access rights for current role.';
  if (numericCode === 404) return 'Resource not found or not visible for current user.';
  if (numericCode === 409) return 'Record changed on server. Reload and retry.';
  if (numericCode && numericCode >= 500) return 'Server encountered an exception. Retry later or contact support.';
  return '';
}

export function resolveErrorCopy(err: StatusError | null, fallbackMessage = 'Request failed'): StatusCopy {
  const code = normalizeCode(err?.code);
  const category = normalizeCategory(err?.errorCategory);
  const hint = err?.hint || getHint(err?.code, err?.kind, err?.errorCategory, err?.retryable);
  const contextHint = errorContextHint(err);
  if (category === 'auth') {
    return {
      title: 'Authentication required',
      message: 'Login state is invalid for this action.',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (category === 'permission') {
    return {
      title: 'Permission denied',
      message: 'Current role cannot perform this operation.',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (category === 'validation') {
    return {
      title: 'Invalid request',
      message: 'Request parameters failed backend validation.',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (category === 'conflict') {
    return {
      title: 'Write conflict',
      message: 'Backend rejected stale data. Reload and retry.',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (category === 'business') {
    return {
      title: 'Business rule blocked',
      message: 'Operation violates current business constraints.',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (category === 'system') {
    return {
      title: 'System exception',
      message: 'Backend failed to process this request.',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (err?.kind === 'network' || code === 0) {
    return {
      title: 'Network error',
      message: 'Unable to reach backend service. Please check network or service health.',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (code === 401) {
    return {
      title: 'Authentication required',
      message: 'Login session is invalid. Please sign in again.',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (code === 403) {
    return {
      title: 'Permission denied',
      message: 'You do not have permission to perform this action.',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (code === 404) {
    return {
      title: 'Resource not found',
      message: 'Requested resource is missing or no longer accessible.',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (code === 409) {
    return {
      title: 'Write conflict',
      message: 'Record was updated by someone else. Reload before retrying.',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (code && code >= 500) {
    return {
      title: 'System exception',
      message: 'Backend failed to process this request. Please retry shortly.',
      hint: mergeHint(hint, contextHint),
    };
  }
  return {
    title: 'Request failed',
    message: err?.message || fallbackMessage,
    hint: mergeHint(hint, contextHint),
  };
}

export function resolveEmptyCopy(
  type: 'list' | 'card' | 'record' | 'my_work' = 'list',
  context?: EmptyCopyContext,
): StatusCopy {
  if (type === 'record') {
    return { title: 'No data', message: 'Record not found or not readable.' };
  }
  if (type === 'my_work') {
    return { title: 'No work items', message: 'No pending items in this section.' };
  }
  if (type === 'card') {
    return { title: 'No data', message: 'No cards returned for this action.' };
  }
  const actionLabel = String(context?.primaryActionLabel || '').trim();
  if (actionLabel) {
    return {
      title: '暂无数据',
      message: `点击右上角“${actionLabel}”开始下一步。`,
    };
  }
  return { title: 'No data', message: 'No records returned for this action.' };
}

export function useStatus() {
  const error = ref<StatusError | null>(null);

  function clearError() {
    error.value = null;
  }

  function setError(err: unknown, fallbackMessage: string, kind?: string) {
    error.value = buildStatusError(err, fallbackMessage, kind);
  }

  return { error, clearError, setError };
}
