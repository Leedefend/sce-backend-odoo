import type { Ref } from 'vue';

type UseActionViewTemplateInteractionRuntimeOptions = {
  showMoreContractFilters: Ref<boolean>;
  showMoreSavedFilters: Ref<boolean>;
  showMoreGroupBy: Ref<boolean>;
  showMoreContractActions: Ref<boolean>;
};

export function useActionViewTemplateInteractionRuntime(options: UseActionViewTemplateInteractionRuntimeOptions) {
  function toggleMoreContractFilters(): void {
    options.showMoreContractFilters.value = !options.showMoreContractFilters.value;
  }

  function toggleMoreSavedFilters(): void {
    options.showMoreSavedFilters.value = !options.showMoreSavedFilters.value;
  }

  function toggleMoreGroupBy(): void {
    options.showMoreGroupBy.value = !options.showMoreGroupBy.value;
  }

  function toggleMoreContractActions(): void {
    options.showMoreContractActions.value = !options.showMoreContractActions.value;
  }

  return {
    toggleMoreContractFilters,
    toggleMoreSavedFilters,
    toggleMoreGroupBy,
    toggleMoreContractActions,
  };
}

