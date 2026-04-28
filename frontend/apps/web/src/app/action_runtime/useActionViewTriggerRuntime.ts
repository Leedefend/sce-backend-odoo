import type { Ref } from 'vue';
import {
  resolveFilterTriggerPlan,
  resolveSearchTriggerPlan,
  resolveSortTriggerPlan,
  resolveTriggerGroupWindowOffset,
} from '../runtime/actionViewLoadTriggerRuntime';

type FilterValue = 'all' | 'active' | 'archived';

type UseActionViewTriggerRuntimeOptions = {
  searchTerm: Ref<string>;
  sortValue: Ref<string>;
  filterValue: Ref<FilterValue>;
  listOffset: Ref<number>;
  groupWindowOffset: Ref<number>;
  syncRouteListState: () => void;
  load: () => Promise<void>;
  clearSelection: () => void;
};

export function useActionViewTriggerRuntime(options: UseActionViewTriggerRuntimeOptions) {
  function handleSearch(value: string) {
    const triggerPlan = resolveSearchTriggerPlan({ value });
    if (triggerPlan.nextSearchTerm !== null) options.searchTerm.value = triggerPlan.nextSearchTerm;
    options.listOffset.value = 0;
    options.groupWindowOffset.value = resolveTriggerGroupWindowOffset({
      nextGroupWindowOffset: triggerPlan.nextGroupWindowOffset,
      currentGroupWindowOffset: options.groupWindowOffset.value,
    });
    if (triggerPlan.shouldSyncRoute) options.syncRouteListState();
    if (triggerPlan.shouldLoad) void options.load();
  }

  function handleSort(value: string) {
    const triggerPlan = resolveSortTriggerPlan({ value });
    if (triggerPlan.nextSortValue !== null) options.sortValue.value = triggerPlan.nextSortValue;
    options.listOffset.value = 0;
    options.groupWindowOffset.value = resolveTriggerGroupWindowOffset({
      nextGroupWindowOffset: triggerPlan.nextGroupWindowOffset,
      currentGroupWindowOffset: options.groupWindowOffset.value,
    });
    if (triggerPlan.shouldSyncRoute) options.syncRouteListState();
    if (triggerPlan.shouldLoad) void options.load();
  }

  function handleFilter(value: FilterValue) {
    const triggerPlan = resolveFilterTriggerPlan({ value });
    if (triggerPlan.nextFilterValue !== null) options.filterValue.value = triggerPlan.nextFilterValue;
    options.listOffset.value = 0;
    options.groupWindowOffset.value = resolveTriggerGroupWindowOffset({
      nextGroupWindowOffset: triggerPlan.nextGroupWindowOffset,
      currentGroupWindowOffset: options.groupWindowOffset.value,
    });
    if (triggerPlan.shouldClearSelection) options.clearSelection();
    if (triggerPlan.shouldSyncRoute) options.syncRouteListState();
    if (triggerPlan.shouldLoad) void options.load();
  }

  return {
    handleSearch,
    handleSort,
    handleFilter,
  };
}
