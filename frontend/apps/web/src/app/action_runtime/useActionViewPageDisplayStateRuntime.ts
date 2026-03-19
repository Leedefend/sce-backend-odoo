import { computed, type ComputedRef, type Ref } from 'vue';
import type { RouteLocationNormalizedLoaded } from 'vue-router';

type Dict = Record<string, unknown>;

type ActionContractLike = {
  head?: {
    title?: string;
  };
  surface_policies?: {
    empty_reason?: string;
  };
};

type UseActionViewPageDisplayStateRuntimeOptions = {
  routeSceneLabel: Ref<string>;
  actionContract: Ref<ActionContractLike | null>;
  sceneContractV1: ComputedRef<Dict>;
  injectedTitle: ComputedRef<string>;
  actionMetaName: ComputedRef<string>;
  t: (key: string, fallback?: string) => string;
  searchTerm: Ref<string>;
  activeContractFilterKey: Ref<string>;
  errorMessage: ComputedRef<string>;
  route: RouteLocationNormalizedLoaded;
  isHudEnabled: (route: RouteLocationNormalizedLoaded) => boolean;
};

export function useActionViewPageDisplayStateRuntime(options: UseActionViewPageDisplayStateRuntimeOptions) {
  const pageTitle = computed(() => {
    if (options.routeSceneLabel.value) return options.routeSceneLabel.value;
    const contractTitle = String(options.actionContract.value?.head?.title || '').trim();
    if (contractTitle) return contractTitle;
    return options.injectedTitle.value || options.actionMetaName.value || options.t('page_title_fallback', '工作台');
  });

  const emptyReasonText = computed(() => {
    if (options.searchTerm.value.trim() || options.activeContractFilterKey.value) {
      return options.t('empty_reason_filter', '可能由当前筛选条件导致无数据，建议先清除筛选后重试。');
    }
    const fromSurfacePolicy = String(options.actionContract.value?.surface_policies?.empty_reason || '').trim();
    if (fromSurfacePolicy) return fromSurfacePolicy;
    const fromExtensions = String((options.sceneContractV1.value.extensions as Dict | undefined)?.empty_reason || '').trim();
    if (fromExtensions) return fromExtensions;
    return options.t('empty_reason_default', '');
  });

  const showHud = computed(() => options.isHudEnabled(options.route));

  return {
    pageTitle,
    emptyReasonText,
    showHud,
    errorMessage: options.errorMessage,
  };
}

