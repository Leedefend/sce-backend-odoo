import { ref, type Ref } from 'vue';
import type { ActionViewGroupSharedState } from './actionViewGroupStateRuntime';

export type GroupSummaryItem = {
  key: string;
  label: string;
  count: number;
  domain: unknown[];
  value?: unknown;
};

export type GroupedRow = {
  key: string;
  label: string;
  count: number;
  sampleRows: Array<Record<string, unknown>>;
  domain?: unknown[];
  pageOffset: number;
  pageLimit: number;
  pageCurrent?: number;
  pageTotal?: number;
  pageRangeStart?: number;
  pageRangeEnd?: number;
  pageWindow?: { start?: number; end?: number };
  pageHasPrev?: boolean;
  pageHasNext?: boolean;
  pageSyncedFromServer?: boolean;
  loading?: boolean;
};

export type ActionViewGroupRuntimeState = {
  groupSummaryItems: Ref<GroupSummaryItem[]>;
  groupedRows: Ref<GroupedRow[]>;
  groupSampleLimit: Ref<number>;
  groupSort: Ref<'asc' | 'desc'>;
  collapsedGroupKeys: Ref<string[]>;
  groupPageOffsets: Ref<Record<string, number>>;
  activeGroupSummaryKey: Ref<string>;
  activeGroupSummaryDomain: Ref<unknown[]>;
  groupWindowOffset: Ref<number>;
  groupWindowCount: Ref<number>;
  groupWindowTotal: Ref<number | null>;
  groupWindowStart: Ref<number | null>;
  groupWindowEnd: Ref<number | null>;
  groupWindowId: Ref<string>;
  groupQueryFingerprint: Ref<string>;
  groupWindowDigest: Ref<string>;
  groupWindowIdentityKey: Ref<string>;
  groupWindowPrevOffset: Ref<number | null>;
  groupWindowNextOffset: Ref<number | null>;
  showMoreGroupBy: Ref<boolean>;
};

export type ActionViewGroupRuntimeCapsule = {
  state: ActionViewGroupRuntimeState;
  applySharedState: (state: Partial<ActionViewGroupSharedState>) => void;
};

export function createActionViewGroupRuntimeState(): ActionViewGroupRuntimeState {
  return {
    groupSummaryItems: ref<GroupSummaryItem[]>([]),
    groupedRows: ref<GroupedRow[]>([]),
    groupSampleLimit: ref(3),
    groupSort: ref<'asc' | 'desc'>('desc'),
    collapsedGroupKeys: ref<string[]>([]),
    groupPageOffsets: ref<Record<string, number>>({}),
    activeGroupSummaryKey: ref(''),
    activeGroupSummaryDomain: ref<unknown[]>([]),
    groupWindowOffset: ref(0),
    groupWindowCount: ref(0),
    groupWindowTotal: ref<number | null>(null),
    groupWindowStart: ref<number | null>(null),
    groupWindowEnd: ref<number | null>(null),
    groupWindowId: ref(''),
    groupQueryFingerprint: ref(''),
    groupWindowDigest: ref(''),
    groupWindowIdentityKey: ref(''),
    groupWindowPrevOffset: ref<number | null>(null),
    groupWindowNextOffset: ref<number | null>(null),
    showMoreGroupBy: ref(false),
  };
}

export function applyActionViewGroupSharedState(
  target: ActionViewGroupRuntimeState,
  state: Partial<ActionViewGroupSharedState>,
): void {
  if (state.activeGroupSummaryKey !== undefined) target.activeGroupSummaryKey.value = state.activeGroupSummaryKey;
  if (state.activeGroupSummaryDomain !== undefined) target.activeGroupSummaryDomain.value = state.activeGroupSummaryDomain;
  if (state.groupWindowOffset !== undefined) target.groupWindowOffset.value = state.groupWindowOffset;
  if (state.groupWindowPrevOffset !== undefined) target.groupWindowPrevOffset.value = state.groupWindowPrevOffset;
  if (state.groupWindowNextOffset !== undefined) target.groupWindowNextOffset.value = state.groupWindowNextOffset;
  if (state.groupWindowCount !== undefined) target.groupWindowCount.value = state.groupWindowCount;
  if (state.groupWindowTotal !== undefined) target.groupWindowTotal.value = state.groupWindowTotal;
  if (state.groupWindowStart !== undefined) target.groupWindowStart.value = state.groupWindowStart;
  if (state.groupWindowEnd !== undefined) target.groupWindowEnd.value = state.groupWindowEnd;
  if (state.groupWindowId !== undefined) target.groupWindowId.value = state.groupWindowId;
  if (state.groupQueryFingerprint !== undefined) target.groupQueryFingerprint.value = state.groupQueryFingerprint;
  if (state.groupWindowDigest !== undefined) target.groupWindowDigest.value = state.groupWindowDigest;
  if (state.groupWindowIdentityKey !== undefined) target.groupWindowIdentityKey.value = state.groupWindowIdentityKey;
  if (state.groupPageOffsets !== undefined) target.groupPageOffsets.value = state.groupPageOffsets;
  if (state.showMoreGroupBy !== undefined) target.showMoreGroupBy.value = state.showMoreGroupBy;
  if (state.collapsedGroupKeys !== undefined) target.collapsedGroupKeys.value = state.collapsedGroupKeys;
}

export function createActionViewGroupRuntimeCapsule(): ActionViewGroupRuntimeCapsule {
  const state = createActionViewGroupRuntimeState();
  return {
    state,
    applySharedState: (nextState) => applyActionViewGroupSharedState(state, nextState),
  };
}
