import { computed, type Ref } from 'vue';

type UseActionViewTemplateStateRuntimeOptions = {
  status: Ref<'idle' | 'loading' | 'ok' | 'empty' | 'error'>;
  batchBusy: Ref<boolean>;
};

export function useActionViewTemplateStateRuntime(options: UseActionViewTemplateStateRuntimeOptions) {
  const isUiBusy = computed(() => options.status.value === 'loading' || options.batchBusy.value);

  function isViewModeDisabled(input: { mode: string; currentViewMode: string }): boolean {
    return isUiBusy.value || input.mode === input.currentViewMode;
  }

  function isBusyDisabled(): boolean {
    return isUiBusy.value;
  }

  function isContractActionDisabled(input: { enabled?: boolean }): boolean {
    return !input.enabled || isUiBusy.value;
  }

  return {
    isUiBusy,
    isViewModeDisabled,
    isBusyDisabled,
    isContractActionDisabled,
  };
}
