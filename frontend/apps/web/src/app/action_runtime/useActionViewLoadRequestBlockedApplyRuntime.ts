import type { Ref } from 'vue';

type StatusInput = { error: string; recordsLength: number };

type ApplyLoadRequestBlockedStateFn = (input: {
  blocked: boolean;
  message: string;
  statusInput: StatusInput;
  setError: (error: Error, fallbackMessage?: string) => void;
  deriveListStatus: (input: StatusInput) => string;
  statusRef: Ref<string>;
}) => boolean;

type UseActionViewLoadRequestBlockedApplyRuntimeOptions = {
  applyLoadRequestBlockedState: ApplyLoadRequestBlockedStateFn;
  setError: (error: Error, fallbackMessage?: string) => void;
  deriveListStatus: (input: StatusInput) => string;
  statusRef: Ref<string>;
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
