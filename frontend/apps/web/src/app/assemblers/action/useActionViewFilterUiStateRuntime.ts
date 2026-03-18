import { ref } from 'vue';

export function useActionViewFilterUiStateRuntime() {
  const activeContractFilterKey = ref('');
  const activeSavedFilterKey = ref('');
  const contractLimit = ref(40);
  const preferredViewMode = ref('');

  return {
    activeContractFilterKey,
    activeSavedFilterKey,
    contractLimit,
    preferredViewMode,
  };
}

