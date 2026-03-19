import { computed, type Ref } from 'vue';

type Dict = Record<string, unknown>;

type UseActionViewAdvancedDisplayRuntimeOptions = {
  strictContractMode: Ref<boolean>;
  strictAdvancedViewContract: Ref<Dict>;
  viewMode: Ref<string>;
  pageText: (key: string, fallback?: string) => string;
  resolveActionViewAdvancedTitle: (input: Dict) => string;
  resolveActionViewAdvancedHint: (input: Dict) => string;
};

export function useActionViewAdvancedDisplayRuntime(options: UseActionViewAdvancedDisplayRuntimeOptions) {
  const advancedViewTitle = computed(() => {
    return options.resolveActionViewAdvancedTitle({
      strictContractMode: options.strictContractMode.value,
      strictAdvancedViewContract: options.strictAdvancedViewContract.value,
      viewMode: options.viewMode.value,
      pageText: options.pageText,
    });
  });

  const advancedViewHint = computed(() => {
    return options.resolveActionViewAdvancedHint({
      strictContractMode: options.strictContractMode.value,
      strictAdvancedViewContract: options.strictAdvancedViewContract.value,
      viewMode: options.viewMode.value,
      pageText: options.pageText,
    });
  });

  return {
    advancedViewTitle,
    advancedViewHint,
  };
}

