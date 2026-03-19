import type { Ref } from 'vue';

type StatusInput = { error: string; recordsLength: number };

type ApplyLoadRequestBlockedStateFn = (input: {
  blocked: boolean;
  message: string;
  statusInput: StatusInput;
  setError: (error: Error, fallbackMessage?: string) => void;
  deriveListStatus: (input: StatusInput) => 'loading' | 'ok' | 'empty' | 'error';
  statusRef: Ref<'loading' | 'ok' | 'empty' | 'error'>;
}) => boolean;

type UseActionViewLoadRequestBlockedApplyRuntimeOptions = {
  applyLoadRequestBlockedState: ApplyLoadRequestBlockedStateFn;
  setError: (error: Error, fallbackMessage?: string) => void;
  deriveListStatus: (input: StatusInput) => 'loading' | 'ok' | 'empty' | 'error';
  statusRef: Ref<'loading' | 'ok' | 'empty' | 'error'>;
};

export function useActionViewLoadRequestBlockedApplyRuntime(options: UseActionViewLoadRequestBlockedApplyRuntimeOptions) {
  function applyLoadRequestBlocked(input: { blocked: boolean; message: string; statusInput: StatusInput }): boolean {
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
