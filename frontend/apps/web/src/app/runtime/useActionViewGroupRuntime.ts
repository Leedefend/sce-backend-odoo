import type { Ref } from 'vue';
import {
  buildClearGroupSummaryPatch,
  buildClearGroupSummaryState,
  buildGroupSummaryPickPatch,
  buildGroupSummaryPickState,
  buildGroupWindowMovePatch,
  buildOpenGroupedRowsPatch,
  buildOpenGroupedRowsState,
  resolveGroupCollapsedTransition,
  resolveGroupSampleLimitTransition,
  resolveGroupSortTransition,
  resolveGroupWindowMoveTarget,
} from './actionViewGroupDrilldownRuntime';
import { buildGroupWindowMoveState, type ActionViewGroupSharedState } from './actionViewGroupStateRuntime';
import type { GroupSummaryItem } from './actionViewGroupRuntimeState';
import type { SceneListProfile } from '../resolvers/sceneRegistry';

type SyncRouteFn = (patch: Record<string, unknown>) => void;

export function useActionViewGroupRuntime(options: {
  activeGroupSummaryKey: Ref<string>;
  activeGroupSummaryDomain: Ref<unknown[]>;
  activeGroupByField: Ref<string>;
  searchTerm: Ref<string>;
  listOffset: Ref<number>;
  listLimitOverride: Ref<number>;
  contractLimit: Ref<number>;
  groupWindowOffset: Ref<number>;
  groupWindowPrevOffset: Ref<number | null>;
  groupWindowNextOffset: Ref<number | null>;
  groupSampleLimit: Ref<number>;
  groupSort: Ref<'asc' | 'desc'>;
  listProfile: Ref<SceneListProfile | null>;
  collapsedGroupKeys: Ref<string[]>;
  groupPageOffsets: Ref<Record<string, number>>;
  syncRouteStateAndReload: SyncRouteFn;
  syncRouteListState: SyncRouteFn;
  applyRoutePatchAndReload: SyncRouteFn;
  applyGroupSharedState: (state: Partial<ActionViewGroupSharedState>) => void;
}): {
  handleGroupSummaryPick: (item: GroupSummaryItem) => void;
  handleOpenGroupedRows: (group: { key: string; label: string; count: number; domain?: unknown[] }) => void;
  clearGroupSummaryDrilldown: () => void;
  handleGroupWindowPrev: () => void;
  handleGroupWindowNext: () => void;
  handleGroupSampleLimitChange: (limit: number) => void;
  handleGroupSortChange: (next: 'asc' | 'desc') => void;
  handleGroupCollapsedChange: (keys: string[]) => void;
} {
  const handleGroupSummaryPick = (item: GroupSummaryItem) => {
    if (!item) return;
    const nextState = buildGroupSummaryPickState(item);
    options.activeGroupSummaryKey.value = nextState.activeGroupSummaryKey;
    options.activeGroupSummaryDomain.value = nextState.activeGroupSummaryDomain;
    options.searchTerm.value = nextState.searchTerm;
    options.groupWindowOffset.value = nextState.groupWindowOffset;
    options.syncRouteStateAndReload(buildGroupSummaryPickPatch(options.searchTerm.value, item.label || ''));
  };

  const handleOpenGroupedRows = (group: { key: string; label: string; count: number; domain?: unknown[] }) => {
    const nextState = buildOpenGroupedRowsState(group);
    options.activeGroupSummaryKey.value = nextState.activeGroupSummaryKey;
    options.activeGroupSummaryDomain.value = nextState.activeGroupSummaryDomain;
    options.activeGroupByField.value = '';
    options.searchTerm.value = nextState.searchTerm;
    options.listOffset.value = 0;
    const drilldownLimit = Math.min(200, Math.max(20, Math.trunc(Number(group.count || 0))));
    options.listLimitOverride.value = drilldownLimit;
    options.contractLimit.value = drilldownLimit;
    options.groupWindowOffset.value = nextState.groupWindowOffset;
    options.applyRoutePatchAndReload(buildOpenGroupedRowsPatch(group.label || ''));
  };

  const clearGroupSummaryDrilldown = () => {
    const nextState = buildClearGroupSummaryState();
    options.activeGroupSummaryKey.value = nextState.activeGroupSummaryKey;
    options.activeGroupSummaryDomain.value = nextState.activeGroupSummaryDomain;
    options.searchTerm.value = nextState.searchTerm;
    options.groupWindowOffset.value = nextState.groupWindowOffset;
    options.applyRoutePatchAndReload(buildClearGroupSummaryPatch());
  };

  const handleGroupWindowMove = (direction: 'prev' | 'next') => {
    const nextOffset = resolveGroupWindowMoveTarget({
      prevOffset: options.groupWindowPrevOffset.value,
      nextOffset: options.groupWindowNextOffset.value,
      direction,
    });
    if (nextOffset === null) return;
    options.applyGroupSharedState(buildGroupWindowMoveState(nextOffset));
    options.syncRouteStateAndReload(buildGroupWindowMovePatch(options.groupWindowOffset.value));
  };

  const handleGroupSampleLimitChange = (limit: number) => {
    const transition = resolveGroupSampleLimitTransition(limit, {
      sampleLimits: options.listProfile.value?.grouping?.sample_limits,
      defaultSampleLimit: options.listProfile.value?.grouping?.default_sample_limit,
    });
    if (transition.normalizedLimit === null || !transition.patch) return;
    options.groupSampleLimit.value = transition.normalizedLimit;
    if (transition.resetGroupWindowOffset) options.groupWindowOffset.value = 0;
    if (transition.resetGroupPageOffsets) options.groupPageOffsets.value = {};
    options.syncRouteStateAndReload(transition.patch);
  };

  const handleGroupSortChange = (next: 'asc' | 'desc') => {
    const transition = resolveGroupSortTransition(next, {
      sortDirections: options.listProfile.value?.grouping?.sort?.directions,
      defaultSort: options.listProfile.value?.grouping?.sort?.default_direction === 'asc'
        || options.listProfile.value?.grouping?.sort?.default_direction === 'desc'
        ? options.listProfile.value.grouping.sort.default_direction
        : undefined,
    });
    options.groupSort.value = transition.normalizedSort;
    options.syncRouteListState(transition.patch);
  };

  const handleGroupCollapsedChange = (keys: string[]) => {
    const transition = resolveGroupCollapsedTransition(keys);
    options.collapsedGroupKeys.value = transition.normalizedKeys;
    options.syncRouteListState(transition.patch);
  };

  return {
    handleGroupSummaryPick,
    handleOpenGroupedRows,
    clearGroupSummaryDrilldown,
    handleGroupWindowPrev: () => handleGroupWindowMove('prev'),
    handleGroupWindowNext: () => handleGroupWindowMove('next'),
    handleGroupSampleLimitChange,
    handleGroupSortChange,
    handleGroupCollapsedChange,
  };
}
