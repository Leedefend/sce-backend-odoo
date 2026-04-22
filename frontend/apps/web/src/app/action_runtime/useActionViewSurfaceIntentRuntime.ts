import { computed, type ComputedRef, type Ref } from 'vue';

type Dict = Record<string, unknown>;

type ActionContractLike = {
  surface_policies?: {
    intent_profile?: unknown;
  };
};

type UseActionViewSurfaceIntentRuntimeOptions = {
  actionContract: Ref<ActionContractLike | null>;
  sceneContractV1: ComputedRef<Dict>;
  strictContractMode: Ref<boolean>;
  strictSurfaceContract: Ref<Dict>;
  sceneKey: Ref<string>;
  pageText: (key: string, fallback?: string) => string;
  resolveActionViewSurfaceIntent: (input: Dict) => unknown;
};

export function useActionViewSurfaceIntentRuntime(options: UseActionViewSurfaceIntentRuntimeOptions) {
  const contractSurfaceIntent = computed<Dict>(() => {
    const fromSurfacePolicies = options.actionContract.value?.surface_policies?.intent_profile;
    if (fromSurfacePolicies && typeof fromSurfacePolicies === 'object' && !Array.isArray(fromSurfacePolicies)) {
      return fromSurfacePolicies as Dict;
    }
    return {};
  });

  const surfaceIntent = computed(() => {
    return options.resolveActionViewSurfaceIntent({
      strictContractMode: options.strictContractMode.value,
      strictSurfaceContract: options.strictSurfaceContract.value,
      contractSurfaceIntent: contractSurfaceIntent.value,
      sceneKey: options.sceneKey.value,
      pageText: options.pageText,
    });
  });

  return {
    contractSurfaceIntent,
    surfaceIntent,
  };
}
