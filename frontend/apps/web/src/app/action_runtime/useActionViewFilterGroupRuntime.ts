import type { Ref } from 'vue';
import {
  resolveContractFilterApplyState,
  resolveContractFilterClearState,
  resolveGroupByApplyState,
  resolveGroupByClearState,
  resolveNonEmptyControlKey,
  resolveSavedFilterClearState,
  resolveSavedFilterApplyState,
} from '../runtime/actionViewFilterGroupRuntime';
import { buildGroupByPatch, buildPresetFilterPatch, buildSavedFilterPatch } from '../runtime/actionViewRouteRuntime';
import { buildGroupSharedResetState, type ActionViewGroupSharedState } from '../runtime/actionViewGroupStateRuntime';

type UseActionViewFilterGroupRuntimeOptions = {
  activeContractFilterKey: Ref<string>;
  showMoreContractFilters: Ref<boolean>;
  activeSavedFilterKey: Ref<string>;
  showMoreSavedFilters: Ref<boolean>;
  activeGroupByField: Ref<string>;
  clearSelection: () => void;
  applyRoutePatchAndReload: (patch: Record<string, unknown>) => void;
  applyGroupSharedState: (state: Partial<ActionViewGroupSharedState>) => void;
};

export function useActionViewFilterGroupRuntime(options: UseActionViewFilterGroupRuntimeOptions) {
  function applyContractFilter(key: string) {
    const normalizedKey = resolveNonEmptyControlKey(key);
    if (!normalizedKey) return;
    const nextState = resolveContractFilterApplyState({
      key: normalizedKey,
      buildPatch: buildPresetFilterPatch,
    });
    options.activeContractFilterKey.value = nextState.activeContractFilterKey;
    options.showMoreContractFilters.value = nextState.showMoreContractFilters;
    if (nextState.shouldClearSelection) options.clearSelection();
    options.applyRoutePatchAndReload(nextState.routePatch);
  }

  function applySavedFilter(key: string) {
    const normalizedKey = resolveNonEmptyControlKey(key);
    if (!normalizedKey) return;
    const nextState = resolveSavedFilterApplyState({
      key: normalizedKey,
      buildPatch: buildSavedFilterPatch,
    });
    options.activeSavedFilterKey.value = nextState.activeSavedFilterKey;
    options.showMoreSavedFilters.value = nextState.showMoreSavedFilters;
    if (nextState.shouldClearSelection) options.clearSelection();
    options.applyRoutePatchAndReload(nextState.routePatch);
  }

  function clearContractFilter() {
    const nextState = resolveContractFilterClearState({
      buildPatch: buildPresetFilterPatch,
    });
    options.activeContractFilterKey.value = nextState.activeContractFilterKey;
    options.showMoreContractFilters.value = nextState.showMoreContractFilters;
    if (nextState.shouldClearSelection) options.clearSelection();
    options.applyRoutePatchAndReload(nextState.routePatch);
  }

  function clearSavedFilter() {
    const nextState = resolveSavedFilterClearState({
      buildPatch: buildSavedFilterPatch,
    });
    options.activeSavedFilterKey.value = nextState.activeSavedFilterKey;
    options.showMoreSavedFilters.value = nextState.showMoreSavedFilters;
    if (nextState.shouldClearSelection) options.clearSelection();
    options.applyRoutePatchAndReload(nextState.routePatch);
  }

  function applyGroupBy(field: string) {
    const normalizedField = resolveNonEmptyControlKey(field);
    if (!normalizedField) return;
    const nextState = resolveGroupByApplyState({
      field: normalizedField,
      buildPatch: buildGroupByPatch,
    });
    options.activeGroupByField.value = nextState.activeGroupByField;
    if (nextState.shouldResetGroupSharedState) {
      options.applyGroupSharedState(buildGroupSharedResetState());
    }
    if (nextState.shouldClearSelection) options.clearSelection();
    options.applyRoutePatchAndReload(nextState.routePatch);
  }

  function clearGroupBy() {
    const nextState = resolveGroupByClearState({
      buildPatch: buildGroupByPatch,
    });
    options.activeGroupByField.value = nextState.activeGroupByField;
    if (nextState.shouldResetGroupSharedState) {
      options.applyGroupSharedState(buildGroupSharedResetState());
    }
    if (nextState.shouldClearSelection) options.clearSelection();
    options.applyRoutePatchAndReload(nextState.routePatch);
  }

  return {
    applyContractFilter,
    applySavedFilter,
    clearContractFilter,
    clearSavedFilter,
    applyGroupBy,
    clearGroupBy,
  };
}

