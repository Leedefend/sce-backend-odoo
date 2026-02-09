import { ref } from 'vue';
import { ApiError } from '../api/client';

export interface StatusError {
  message: string;
  code?: number | string;
  traceId?: string;
  hint?: string;
  kind?: string;
  reasonCode?: string;
}

export interface StatusCopy {
  title: string;
  message: string;
  hint?: string;
}

function normalizeCode(code?: number | string) {
  if (typeof code === 'number') return code;
  if (typeof code === 'string') {
    const parsed = Number(code);
    return Number.isNaN(parsed) ? undefined : parsed;
  }
  return undefined;
}

function getHint(code?: number | string, kind?: string): string {
  const numericCode = normalizeCode(code);
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
  const hint = err?.hint || getHint(err?.code, err?.kind);
  if (err?.kind === 'network' || code === 0) {
    return {
      title: 'Network error',
      message: 'Unable to reach backend service. Please check network or service health.',
      hint: hint || undefined,
    };
  }
  if (code === 401) {
    return {
      title: 'Authentication required',
      message: 'Login session is invalid. Please sign in again.',
      hint: hint || undefined,
    };
  }
  if (code === 403) {
    return {
      title: 'Permission denied',
      message: 'You do not have permission to perform this action.',
      hint: hint || undefined,
    };
  }
  if (code === 404) {
    return {
      title: 'Resource not found',
      message: 'Requested resource is missing or no longer accessible.',
      hint: hint || undefined,
    };
  }
  if (code === 409) {
    return {
      title: 'Write conflict',
      message: 'Record was updated by someone else. Reload before retrying.',
      hint: hint || undefined,
    };
  }
  if (code && code >= 500) {
    return {
      title: 'System exception',
      message: 'Backend failed to process this request. Please retry shortly.',
      hint: hint || undefined,
    };
  }
  return {
    title: 'Request failed',
    message: err?.message || fallbackMessage,
    hint: hint || undefined,
  };
}

export function resolveEmptyCopy(type: 'list' | 'card' | 'record' | 'my_work' = 'list'): StatusCopy {
  if (type === 'record') {
    return { title: 'No data', message: 'Record not found or not readable.' };
  }
  if (type === 'my_work') {
    return { title: 'No work items', message: 'No pending items in this section.' };
  }
  if (type === 'card') {
    return { title: 'No data', message: 'No cards returned for this action.' };
  }
  return { title: 'No data', message: 'No records returned for this action.' };
}

export function useStatus() {
  const error = ref<StatusError | null>(null);

  function clearError() {
    error.value = null;
  }

  function setError(err: unknown, fallbackMessage: string, kind?: string) {
    if (err instanceof ApiError) {
      const code = err.status;
      error.value = {
        message: err.message,
        code,
        traceId: err.traceId,
        hint: err.hint || getHint(code, err.kind),
        kind: kind || err.kind,
        reasonCode: err.reasonCode,
      };
      return;
    }
    const message = err instanceof Error ? err.message : fallbackMessage;
    error.value = { message, kind };
  }

  return { error, clearError, setError };
}
