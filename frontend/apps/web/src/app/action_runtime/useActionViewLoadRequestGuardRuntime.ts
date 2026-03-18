import type { Ref } from 'vue';

type ApplyLoadRequestBlockedStateOptions = {
  blocked: boolean;
  message: string;
  statusInput: string;
  setError: (error: Error, fallbackMessage?: string) => void;
  deriveListStatus: (input: string) => 'loading' | 'ok' | 'empty' | 'error';
  statusRef: Ref<'loading' | 'ok' | 'empty' | 'error'>;
};

export function useActionViewLoadRequestGuardRuntime() {
  function applyLoadRequestBlockedState(options: ApplyLoadRequestBlockedStateOptions): boolean {
    const {
      blocked,
      message,
      statusInput,
      setError,
      deriveListStatus,
      statusRef,
    } = options;
    if (!blocked) {
      return false;
    }
    setError(new Error(message), message);
    statusRef.value = deriveListStatus(statusInput);
    return true;
  }

  return {
    applyLoadRequestBlockedState,
  };
}

