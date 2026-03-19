import { computed, type ComputedRef, type Ref } from 'vue';

type Dict = Record<string, unknown>;

type ActionContractLike = {
  surface_policies?: {
    kind?: unknown;
  };
};

type UseActionViewSurfaceDisplayRuntimeOptions = {
  sortValue: Ref<string>;
  sceneContractV1: ComputedRef<Dict>;
  strictContractMode: Ref<boolean>;
  strictSurfaceContract: Ref<Dict>;
  actionContract: Ref<ActionContractLike | null>;
  resolveActionViewSurfaceKind: (input: Dict) => string;
};

export function useActionViewSurfaceDisplayRuntime(options: UseActionViewSurfaceDisplayRuntimeOptions) {
  const sortLabel = computed(() => options.sortValue.value || 'id asc');

  const surfaceKind = computed(() => {
    const extensions = (options.sceneContractV1.value.extensions as Dict | undefined) || {};
    return options.resolveActionViewSurfaceKind({
      strictContractMode: options.strictContractMode.value,
      strictSurfaceContract: options.strictSurfaceContract.value,
      contractSurfaceKind: options.actionContract.value?.surface_policies?.kind,
      extensionSurfaceKind: extensions.surface_kind,
    });
  });

  return {
    sortLabel,
    surfaceKind,
  };
}

