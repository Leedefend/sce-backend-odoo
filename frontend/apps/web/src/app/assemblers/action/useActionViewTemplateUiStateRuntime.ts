import { ref } from 'vue';

export function useActionViewTemplateUiStateRuntime() {
  const showMoreContractActions = ref(false);
  const showMoreContractFilters = ref(false);
  const showMoreSavedFilters = ref(false);

  return {
    showMoreContractActions,
    showMoreContractFilters,
    showMoreSavedFilters,
  };
}

