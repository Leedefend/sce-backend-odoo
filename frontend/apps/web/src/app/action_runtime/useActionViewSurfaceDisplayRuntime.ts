import { computed, type Ref } from 'vue';
import { resolveUnifiedPageContractV2SurfacePolicies } from '../contracts/unifiedPageContractV2';

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
    const surfacePolicies = resolveUnifiedPageContractV2SurfacePolicies(options.actionContract.value);
    return options.resolveActionViewSurfaceKind({
      strictContractMode: options.strictContractMode.value,
      strictSurfaceContract: options.strictSurfaceContract.value,
      contractSurfaceKind: surfacePolicies.kind,
      extensionSurfaceKind: '',
    });
  });

  return {
    sortLabel,
    surfaceKind,
  };
}
