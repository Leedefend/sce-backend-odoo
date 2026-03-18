import type { Ref } from 'vue';
import { normalizeGroupPageOffset, serializeGroupPageOffsets } from '../runtime/actionViewGroupWindowRuntime';
import { buildGroupedRowsListRequest, resolveGroupedPageFields } from '../runtime/actionViewGroupedRowsRuntime';
import {
  applyGroupedRowsPageChangeFailure,
  applyGroupedRowsHydrateResults,
  applyGroupedRowsPageChangeSuccess,
  resolveGroupedRowsHydrateGuard,
  resolveGroupedRowsPageChangeGuard,
  resolveGroupedRowsHydrateKeys,
  resolveGroupedRowsHydratePageState,
  resolveGroupedRowsHydrateUpdateFailure,
  resolveGroupedRowsHydrateUpdateSuccess,
  resolveGroupedRowsPageDomain,
  resolveGroupedRowsPageOffsetState,
  resolveGroupedRowsPagePayloadRows,
  resolveGroupedRowsHydrateCandidates,
  resolveGroupedRowsPageChangeTarget,
  setGroupedRowsLoadingByKeys,
} from '../runtime/actionViewGroupedRowsInteractionRuntime';
import { hasGroupedRouteOffsetChanged, normalizeGroupedRouteCollections } from '../runtime/actionViewGroupedRouteNormalizeRuntime';
import {
  resolveGroupedRouteInactiveResetPlan,
  resolveGroupedRouteLocalState,
  resolveGroupedRouteSyncPlan,
} from '../runtime/actionViewGroupedRouteStateRuntime';
import { resolveActionViewRouteSnapshot } from '../runtime/actionViewRouteRuntime';

type Dict = Record<string, unknown>;

type UseActionViewGroupedRowsRuntimeOptions = {
  activeGroupByField: Ref<string>;
  groupWindowOffset: Ref<number>;
  collapsedGroupKeys: Ref<string[]>;
  groupPageOffsets: Ref<Record<string, number>>;
  groupedRows: Ref<any[]>;
  groupSummaryItems: Ref<any[]>;
  activeGroupSummaryKey: Ref<string>;
  activeGroupSummaryDomain: Ref<unknown[]>;
  groupSampleLimit: Ref<number>;
  columns: Ref<string[]>;
  listProfile: Ref<any>;
  sortLabel: Ref<string>;
  routeQueryMap: Ref<any>;
  resolvedModelRef: Ref<string>;
  modelRef: Ref<any>;
  actionMetaContext: () => Dict | undefined;
  resolveEffectiveRequestContext: () => Dict;
  resolveEffectiveRequestContextRaw: () => string;
  mergeContext: (base: Dict | string | undefined, extra?: Dict) => Dict;
  syncRouteListState: (extra?: Record<string, unknown>) => void;
  listRecordsRaw: (payload: Dict) => Promise<any>;
};

export function useActionViewGroupedRowsRuntime(options: UseActionViewGroupedRowsRuntimeOptions) {
  async function handleGroupedRowsPageChange(group: {
    key: string;
    label: string;
    count: number;
    domain?: unknown[];
    offset: number;
    limit: number;
  }) {
    if (!group?.key) return;
    const pageTarget = resolveGroupedRowsPageChangeTarget({
      rows: options.groupedRows.value,
      groupKey: group.key,
      requestedOffset: group.offset,
      requestedLimit: group.limit,
      sampleLimitFallback: options.groupSampleLimit.value,
      normalizeOffset: normalizeGroupPageOffset,
    });
    const targetModel = options.resolvedModelRef.value || options.modelRef.value;
    const pageChangeGuard = resolveGroupedRowsPageChangeGuard({
      groupKey: group?.key || '',
      found: pageTarget.found,
      shouldSkip: pageTarget.shouldSkip,
      targetModel,
    });
    if (!pageChangeGuard.ok) return;
    options.groupedRows.value = setGroupedRowsLoadingByKeys(options.groupedRows.value, new Set([group.key]));
    try {
      const result = await options.listRecordsRaw(buildGroupedRowsListRequest({
        model: targetModel,
        fields: resolveGroupedPageFields({
          contractFields: options.columns.value,
          profile: options.listProfile.value,
          fallbackColumns: options.columns.value,
        }),
        domain: resolveGroupedRowsPageDomain(group.domain),
        context: options.mergeContext(options.actionMetaContext(), options.resolveEffectiveRequestContext()),
        contextRaw: options.resolveEffectiveRequestContextRaw(),
        limit: pageTarget.pageLimit,
        offset: pageTarget.nextOffset,
        order: options.sortLabel.value,
      }));
      const rows = resolveGroupedRowsPagePayloadRows(result.data);
      options.groupedRows.value = applyGroupedRowsPageChangeSuccess({
        rows: options.groupedRows.value,
        groupKey: group.key,
        payloadRows: rows,
        nextOffset: pageTarget.nextOffset,
        pageLimit: pageTarget.pageLimit,
        totalCount: Number(pageTarget.found.count || 0),
      });
      const pageOffsetState = resolveGroupedRowsPageOffsetState({
        groupPageOffsets: options.groupPageOffsets.value,
        groupKey: group.key,
        nextOffset: pageTarget.nextOffset,
        serializeGroupPageOffsets,
      });
      options.groupPageOffsets.value = pageOffsetState.nextGroupPageOffsets;
      options.syncRouteListState({ group_page: pageOffsetState.groupPageQueryValue });
    } catch {
      options.groupedRows.value = applyGroupedRowsPageChangeFailure({
        rows: options.groupedRows.value,
        groupKey: group.key,
      });
    }
  }

  async function hydrateGroupedRowsByOffset() {
    const targetModel = options.resolvedModelRef.value || options.modelRef.value;
    const candidates = resolveGroupedRowsHydrateCandidates(options.groupedRows.value);
    const guard = resolveGroupedRowsHydrateGuard({
      targetModel,
      candidatesLength: candidates.length,
    });
    if (!guard.ok) return;
    const keys = resolveGroupedRowsHydrateKeys(candidates);
    options.groupedRows.value = setGroupedRowsLoadingByKeys(options.groupedRows.value, keys);
    const fields = resolveGroupedPageFields({
      contractFields: options.columns.value,
      profile: options.listProfile.value,
      fallbackColumns: options.columns.value,
    });
    const updates = await Promise.all(
      candidates.map(async (item) => {
        try {
          const pageState = resolveGroupedRowsHydratePageState({
            pageLimitRaw: item.pageLimit,
            pageOffsetRaw: item.pageOffset,
            countRaw: item.count,
            sampleLimitFallback: options.groupSampleLimit.value,
            normalizeOffset: normalizeGroupPageOffset,
          });
          const result = await options.listRecordsRaw(buildGroupedRowsListRequest({
            model: targetModel,
            fields,
            domain: Array.isArray(item.domain) ? item.domain : [],
            context: options.mergeContext(options.actionMetaContext(), options.resolveEffectiveRequestContext()),
            contextRaw: options.resolveEffectiveRequestContextRaw(),
            limit: pageState.limit,
            offset: pageState.offset,
            order: options.sortLabel.value,
          }));
          return resolveGroupedRowsHydrateUpdateSuccess({
            key: item.key,
            resultDataRaw: result.data,
          });
        } catch {
          return resolveGroupedRowsHydrateUpdateFailure({ key: item.key });
        }
      }),
    );
    options.groupedRows.value = applyGroupedRowsHydrateResults({ rows: options.groupedRows.value, updates });
  }

  function normalizeGroupedRouteState() {
    const inactiveResetPlan = resolveGroupedRouteInactiveResetPlan({
      activeGroupByField: options.activeGroupByField.value,
      groupWindowOffset: options.groupWindowOffset.value,
      collapsedGroupKeys: options.collapsedGroupKeys.value,
      groupPageOffsets: options.groupPageOffsets.value,
    });
    if (inactiveResetPlan.shouldReset) {
      if (inactiveResetPlan.resetGroupWindowOffset) {
        options.groupWindowOffset.value = 0;
        options.syncRouteListState(inactiveResetPlan.offsetPatch);
      }
      if (inactiveResetPlan.resetCollapsedGroupKeys) {
        options.collapsedGroupKeys.value = [];
        options.syncRouteListState(inactiveResetPlan.collapsedPatch);
      }
      if (inactiveResetPlan.resetGroupPageOffsets) {
        options.groupPageOffsets.value = {};
        options.syncRouteListState(inactiveResetPlan.pagesPatch);
      }
      return;
    }
    if (!options.activeGroupByField.value) {
      return;
    }
    const routeSnapshot = resolveActionViewRouteSnapshot(options.routeQueryMap.value);
    const routeGroupValue = routeSnapshot.groupValue;
    const normalizeInput: any = {
      groupedRows: options.groupedRows.value,
      groupSummaryItems: options.groupSummaryItems.value,
      collapsedGroupKeys: options.collapsedGroupKeys.value,
      groupPageOffsets: options.groupPageOffsets.value,
      routeGroupValue,
      groupSampleLimit: options.groupSampleLimit.value,
    };
    const {
      normalizedCollapsed,
      normalizedGroupPages,
      collapsedChanged,
      groupPageChanged,
      groupValueExists,
    } = normalizeGroupedRouteCollections(normalizeInput);
    const localState = resolveGroupedRouteLocalState({
      groupValueExists,
      currentActiveGroupSummaryKey: options.activeGroupSummaryKey.value,
      currentActiveGroupSummaryDomain: options.activeGroupSummaryDomain.value,
      normalizedCollapsed,
      normalizedGroupPages,
    });
    options.activeGroupSummaryKey.value = localState.activeGroupSummaryKey;
    options.activeGroupSummaryDomain.value = localState.activeGroupSummaryDomain;
    options.collapsedGroupKeys.value = localState.collapsedGroupKeys;
    options.groupPageOffsets.value = localState.groupPageOffsets;
    const syncPlan = resolveGroupedRouteSyncPlan({
      normalizedCollapsed,
      normalizedGroupPages,
      groupWindowOffset: options.groupWindowOffset.value,
      groupValueExists,
      collapsedChanged,
      groupPageChanged,
      routeGroupOffsetRaw: String(routeSnapshot.groupOffsetRaw || ''),
      hasOffsetChanged: hasGroupedRouteOffsetChanged,
    });
    if (syncPlan.shouldSync) {
      options.syncRouteListState(syncPlan.nextState);
    }
  }

  return {
    handleGroupedRowsPageChange,
    hydrateGroupedRowsByOffset,
    normalizeGroupedRouteState,
  };
}
