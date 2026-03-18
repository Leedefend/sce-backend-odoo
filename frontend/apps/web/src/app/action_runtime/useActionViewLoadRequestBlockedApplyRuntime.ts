import type { Ref } from 'vue';

type ApplyLoadRequestBlockedStateFn = (input: {
  blocked: boolean;
  message: string;
  statusInput: string;
  setError: (error: Error, fallbackMessage?: string) => void;
  deriveListStatus: (input: string) => 'loading' | 'ok' | 'empty' | 'error';
  statusRef: Ref<'loading' | 'ok' | 'empty' | 'error'>;
}) => boolean;

type UseActionViewLoadRequestBlockedApplyRuntimeOptions = {
  applyLoadRequestBlockedState: ApplyLoadRequestBlockedStateFn;
  setError: (error: Error, fallbackMessage?: string) => void;
  deriveListStatus: (input: string) => 'loading' | 'ok' | 'empty' | 'error';
  statusRef: Ref<'loading' | 'ok' | 'empty' | 'error'>;
};

export function useActionViewLoadRequestBlockedApplyRuntime(options: UseActionViewLoadRequestBlockedApplyRuntimeOptions) {
  function applyLoadRequestBlocked(input: { blocked: boolean; message: string; statusInput: string }): boolean {
    return options.applyLoadRequestBlockedState({
      ...input,
      setError: options.setError,
      deriveListStatus: options.deriveListStatus,
      statusRef: options.statusRef,
    });
  }

  return {
    applyLoadRequestBlocked,
  };
}

