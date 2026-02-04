import { ref } from 'vue';
import { ApiError } from '../api/client';

export interface StatusError {
  message: string;
  code?: number | string;
  traceId?: string;
  hint?: string;
  kind?: string;
}

function getHint(code?: number | string): string {
  if (code === 401) return 'Check login session and token.';
  if (code === 403) return 'Check access rights for this menu.';
  if (code === 404) return 'Resource not found or menu is missing.';
  return '';
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
        hint: getHint(code),
        kind,
      };
      return;
    }
    const message = err instanceof Error ? err.message : fallbackMessage;
    error.value = { message, kind };
  }

  return { error, clearError, setError };
}
