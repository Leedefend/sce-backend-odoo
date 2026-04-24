import { computed, type Ref } from 'vue';

type ActionContractLike = {
  surface_policies?: {
    kind?: unknown;
  };
};

type UseActionViewSurfaceDisplayRuntimeOptions = {
  sortValue: Ref<string>;
  strictContractMode: Ref<boolean>;
  strictSurfaceContract: Ref<Record<string, unknown>>;
  actionContract: Ref<ActionContractLike | null>;
  resolveActionViewSurfaceKind: (input: Record<string, unknown>) => string;
};

export function useActionViewSurfaceDisplayRuntime(options: UseActionViewSurfaceDisplayRuntimeOptions) {
  const sortLabel = computed(() => options.sortValue.value || 'id asc');

  const surfaceKind = computed(() => {
    return options.resolveActionViewSurfaceKind({
      strictContractMode: options.strictContractMode.value,
      strictSurfaceContract: options.strictSurfaceContract.value,
      contractSurfaceKind: options.actionContract.value?.surface_policies?.kind,
      extensionSurfaceKind: '',
    });
  });

  return {
    sortLabel,
    surfaceKind,
  };
}
