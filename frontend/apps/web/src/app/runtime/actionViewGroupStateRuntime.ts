export type ActionViewGroupSharedState = {
  activeGroupSummaryKey: string;
  activeGroupSummaryDomain: unknown[];
  groupWindowOffset: number;
  groupWindowPrevOffset: number | null;
  groupWindowNextOffset: number | null;
  groupWindowCount: number;
  groupWindowTotal: number | null;
  groupWindowStart: number | null;
  groupWindowEnd: number | null;
  groupWindowId: string;
  groupQueryFingerprint: string;
  groupWindowDigest: string;
  groupWindowIdentityKey: string;
  groupPageOffsets: Record<string, number>;
  showMoreGroupBy: boolean;
  collapsedGroupKeys: string[];
};

export function buildGroupSharedResetState(
  overrides: Partial<ActionViewGroupSharedState> = {},
): ActionViewGroupSharedState {
  return {
    activeGroupSummaryKey: '',
    activeGroupSummaryDomain: [],
    groupWindowOffset: 0,
    groupWindowPrevOffset: null,
    groupWindowNextOffset: null,
    groupWindowCount: 0,
    groupWindowTotal: null,
    groupWindowStart: null,
    groupWindowEnd: null,
    groupWindowId: '',
    groupQueryFingerprint: '',
    groupWindowDigest: '',
    groupWindowIdentityKey: '',
    groupPageOffsets: {},
    showMoreGroupBy: false,
    collapsedGroupKeys: [],
    ...overrides,
  };
}

export function buildGroupWindowMoveState(nextOffset: number): Partial<ActionViewGroupSharedState> {
  return {
    groupWindowOffset: Math.max(0, Math.trunc(nextOffset || 0)),
    groupWindowId: '',
    groupWindowDigest: '',
    groupWindowIdentityKey: '',
    collapsedGroupKeys: [],
    groupPageOffsets: {},
  };
}
