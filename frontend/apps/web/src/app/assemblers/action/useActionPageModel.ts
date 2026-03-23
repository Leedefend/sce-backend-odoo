import { computed, unref, type MaybeRef } from 'vue';
import {
  toActionButtonVM,
  toAdvancedRowVM,
  toActionGroupVM,
  toChipVM,
  toProjectionMetricVM,
} from './actionPageAdapters';
import { resolveActionPageSections } from './actionPageSections';
import type {
  ActionPageStatus,
  ActionPageVM,
  FocusActionVM,
} from './actionPageVm';

type SurfaceIntentInput = {
  title: string;
  summary: string;
  actions: FocusActionVM[];
  emptyTitle: string;
  emptyHint: string;
  primaryAction: FocusActionVM;
  secondaryAction?: FocusActionVM;
};

type UseActionPageModelOptions = {
  page: {
    title: MaybeRef<string>;
    status: MaybeRef<ActionPageStatus>;
    statusLabel: MaybeRef<string>;
    subtitle: MaybeRef<string>;
    traceId: MaybeRef<string>;
    errorMessage: MaybeRef<string>;
    sceneKey: MaybeRef<string>;
    pageMode: MaybeRef<string>;
    viewMode: MaybeRef<string>;
    availableViewModes: MaybeRef<string[]>;
  };
  headerActions: MaybeRef<unknown[]>;
  routePreset: {
    label: MaybeRef<string>;
    source: MaybeRef<string>;
  };
  filters: {
    quickPrimary: MaybeRef<unknown[]>;
    quickOverflow: MaybeRef<unknown[]>;
    savedPrimary: MaybeRef<unknown[]>;
    savedOverflow: MaybeRef<unknown[]>;
    groupByPrimary: MaybeRef<unknown[]>;
    groupByOverflow: MaybeRef<unknown[]>;
  };
  focus: {
    surfaceIntent: MaybeRef<SurfaceIntentInput>;
  };
  strict: {
    missingSummary: MaybeRef<string>;
    defaultsSummary: MaybeRef<string>;
    title: MaybeRef<string>;
  };
  groupSummary: {
    items: MaybeRef<Array<Record<string, unknown>>>;
  };
  actions: {
    primary: MaybeRef<unknown[]>;
    overflowGroups: MaybeRef<unknown[]>;
  };
  content: {
    listSummaryItems: MaybeRef<unknown[]>;
    kanbanOverviewItems: MaybeRef<unknown[]>;
    advancedTitle: MaybeRef<string>;
    advancedHint: MaybeRef<string>;
    advancedRecords: MaybeRef<unknown[]>;
    resolveAdvancedRowTitle: (row: unknown) => string;
    resolveAdvancedRowMeta: (row: unknown) => string;
  };
  empty: {
    reasonText: MaybeRef<string>;
  };
  hud: {
    visible: MaybeRef<boolean>;
    title?: MaybeRef<string>;
    state: {
      actionId: MaybeRef<unknown>;
      menuId: MaybeRef<unknown>;
      sceneKey: MaybeRef<unknown>;
      model: MaybeRef<unknown>;
      viewMode: MaybeRef<unknown>;
      contractViewType: MaybeRef<unknown>;
      activeContractFilterKey: MaybeRef<unknown>;
      activeSavedFilterKey: MaybeRef<unknown>;
      activeGroupByField: MaybeRef<unknown>;
      groupWindowOffset: MaybeRef<unknown>;
      groupWindowId: MaybeRef<unknown>;
      groupQueryFingerprint: MaybeRef<unknown>;
      groupWindowDigest: MaybeRef<unknown>;
      groupWindowIdentityKey: MaybeRef<unknown>;
      routeGroupFp: MaybeRef<unknown>;
      routeGroupWid: MaybeRef<unknown>;
      routeGroupWdg: MaybeRef<unknown>;
      routeGroupWik: MaybeRef<unknown>;
      contractActionCount: MaybeRef<unknown>;
      contractLimit: MaybeRef<unknown>;
      contractReadAllowed: MaybeRef<unknown>;
      contractWarningCount: MaybeRef<unknown>;
      contractDegraded: MaybeRef<unknown>;
      sortLabel: MaybeRef<unknown>;
      lastIntent: MaybeRef<unknown>;
      lastWriteMode: MaybeRef<unknown>;
      traceId: MaybeRef<unknown>;
      lastTraceId: MaybeRef<unknown>;
      lastLatencyMs: MaybeRef<unknown>;
      routeFullPath: MaybeRef<unknown>;
    };
  };
};

function asText(value: unknown): string {
  return String(value || '').trim();
}

function asList(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function toAdvancedRowInput(row: unknown, idx: number) {
  const rowRecord = row && typeof row === 'object' ? (row as Record<string, unknown>) : {};
  const rowId = String(rowRecord.id || idx).trim() || String(idx);
  return {
    key: `adv-${idx}-${rowId}`,
    title: '',
    meta: '',
    row,
  };
}

function resolveContentKind(viewMode: string): 'list' | 'kanban' | 'advanced' {
  if (viewMode === 'tree') return 'list';
  if (viewMode === 'kanban') return 'kanban';
  return 'advanced';
}

function buildHudEntries(input: UseActionPageModelOptions['hud']['state']) {
  return [
    { label: 'action_id', value: unref(input.actionId) || '-' },
    { label: 'menu_id', value: unref(input.menuId) || '-' },
    { label: 'scene_key', value: unref(input.sceneKey) || '-' },
    { label: 'model', value: unref(input.model) || '-' },
    { label: 'view_mode', value: unref(input.viewMode) || '-' },
    { label: 'contract_view_type', value: unref(input.contractViewType) || '-' },
    { label: 'contract_filter', value: unref(input.activeContractFilterKey) || '-' },
    { label: 'saved_filter', value: unref(input.activeSavedFilterKey) || '-' },
    { label: 'group_by', value: unref(input.activeGroupByField) || '-' },
    { label: 'group_offset', value: unref(input.groupWindowOffset) || 0 },
    { label: 'group_window_id', value: unref(input.groupWindowId) || '-' },
    { label: 'group_query_fp', value: unref(input.groupQueryFingerprint) || '-' },
    { label: 'group_window_digest', value: unref(input.groupWindowDigest) || '-' },
    { label: 'group_window_identity_key', value: unref(input.groupWindowIdentityKey) || '-' },
    { label: 'route_group_fp', value: unref(input.routeGroupFp) || '-' },
    { label: 'route_group_wid', value: unref(input.routeGroupWid) || '-' },
    { label: 'route_group_wdg', value: unref(input.routeGroupWdg) || '-' },
    { label: 'route_group_wik', value: unref(input.routeGroupWik) || '-' },
    { label: 'contract_actions', value: unref(input.contractActionCount) || 0 },
    { label: 'contract_limit', value: unref(input.contractLimit) || 0 },
    { label: 'contract_read', value: unref(input.contractReadAllowed) },
    { label: 'contract_warnings', value: unref(input.contractWarningCount) || 0 },
    { label: 'contract_degraded', value: unref(input.contractDegraded) },
    { label: 'order', value: unref(input.sortLabel) || '-' },
    { label: 'last_intent', value: unref(input.lastIntent) || '-' },
    { label: 'write_mode', value: unref(input.lastWriteMode) || '-' },
    { label: 'trace_id', value: unref(input.traceId) || unref(input.lastTraceId) || '-' },
    { label: 'latency_ms', value: unref(input.lastLatencyMs) ?? '-' },
    { label: 'route', value: unref(input.routeFullPath) || '' },
  ];
}

export function useActionPageModel(options: UseActionPageModelOptions) {
  const vm = computed<ActionPageVM>(() => {
    const pageViewMode = asText(unref(options.page.viewMode));
    const contentKind = resolveContentKind(pageViewMode);

    const quickPrimary = asList(unref(options.filters.quickPrimary))
      .map((item) => toChipVM(item))
      .filter((item): item is NonNullable<ReturnType<typeof toChipVM>> => Boolean(item));
    const quickOverflow = asList(unref(options.filters.quickOverflow))
      .map((item) => toChipVM(item))
      .filter((item): item is NonNullable<ReturnType<typeof toChipVM>> => Boolean(item));

    const savedPrimary = asList(unref(options.filters.savedPrimary))
      .map((item) => toChipVM(item))
      .filter((item): item is NonNullable<ReturnType<typeof toChipVM>> => Boolean(item));
    const savedOverflow = asList(unref(options.filters.savedOverflow))
      .map((item) => toChipVM(item))
      .filter((item): item is NonNullable<ReturnType<typeof toChipVM>> => Boolean(item));

    const groupByPrimary = asList(unref(options.filters.groupByPrimary))
      .map((item) => toChipVM(item))
      .filter((item): item is NonNullable<ReturnType<typeof toChipVM>> => Boolean(item));
    const groupByOverflow = asList(unref(options.filters.groupByOverflow))
      .map((item) => toChipVM(item))
      .filter((item): item is NonNullable<ReturnType<typeof toChipVM>> => Boolean(item));

    const strictSummary = asText(unref(options.strict.missingSummary));
    const strictDefaults = asText(unref(options.strict.defaultsSummary));

    const sectionVisibility = resolveActionPageSections({
      showQuickFilters: quickPrimary.length > 0 || quickOverflow.length > 0,
      showSavedFilters: savedPrimary.length > 0 || savedOverflow.length > 0,
      showGroupBy: groupByPrimary.length > 0 || groupByOverflow.length > 0,
      showFocus: true,
      showStrictAlert: Boolean(strictSummary),
      showGroupSummary: asList(unref(options.groupSummary.items)).length > 0,
      showQuickActions:
        asList(unref(options.actions.primary)).length > 0
        || asList(unref(options.actions.overflowGroups)).length > 0,
      showHud: Boolean(unref(options.hud.visible)),
    });

    const focusIntent = unref(options.focus.surfaceIntent);

    const actionPrimary = asList(unref(options.actions.primary))
      .map((item) => toActionButtonVM(item))
      .filter((item): item is NonNullable<ReturnType<typeof toActionButtonVM>> => Boolean(item));
    const actionOverflowGroups = asList(unref(options.actions.overflowGroups))
      .map((item) => toActionGroupVM(item))
      .filter((item): item is NonNullable<ReturnType<typeof toActionGroupVM>> => Boolean(item));

    const listSummaryItems = asList(unref(options.content.listSummaryItems))
      .map((item) => toProjectionMetricVM(item))
      .filter((item): item is NonNullable<ReturnType<typeof toProjectionMetricVM>> => Boolean(item));
    const kanbanOverviewItems = asList(unref(options.content.kanbanOverviewItems))
      .map((item) => toProjectionMetricVM(item))
      .filter((item): item is NonNullable<ReturnType<typeof toProjectionMetricVM>> => Boolean(item));
    const advancedRows = asList(unref(options.content.advancedRecords))
      .slice(0, 20)
      .map((row, idx) => {
        const advancedRowInput = toAdvancedRowInput(row, idx);
        return toAdvancedRowVM({
          key: advancedRowInput.key,
          title: options.content.resolveAdvancedRowTitle(advancedRowInput.row),
          meta: options.content.resolveAdvancedRowMeta(advancedRowInput.row),
        });
      })
      .filter((item): item is NonNullable<ReturnType<typeof toAdvancedRowVM>> => Boolean(item));

    const routePresetLabel = asText(unref(options.routePreset.label));
    const routePresetSource = asText(unref(options.routePreset.source));

    return {
      page: {
        title: asText(unref(options.page.title)),
        status: unref(options.page.status),
        statusLabel: asText(unref(options.page.statusLabel)),
        subtitle: asText(unref(options.page.subtitle)),
        traceId: asText(unref(options.page.traceId)) || undefined,
        errorMessage: asText(unref(options.page.errorMessage)) || undefined,
        sceneKey: asText(unref(options.page.sceneKey)) || undefined,
        pageMode: asText(unref(options.page.pageMode)) || undefined,
        viewMode: pageViewMode,
        availableViewModes: asList(unref(options.page.availableViewModes)).map((item) => asText(item)).filter(Boolean),
      },
      header: {
        actions: asList(unref(options.headerActions))
          .map((item) => toActionButtonVM(item))
          .filter((item): item is NonNullable<ReturnType<typeof toActionButtonVM>> => Boolean(item)),
      },
      filters: {
        routePreset: routePresetLabel
          ? {
              label: routePresetLabel,
              source: routePresetSource || undefined,
              clearable: true,
            }
          : undefined,
        quickFilters: {
          visible: sectionVisibility.quickFilters,
          primary: quickPrimary,
          overflow: quickOverflow,
        },
        savedFilters: {
          visible: sectionVisibility.savedFilters,
          primary: savedPrimary,
          overflow: savedOverflow,
        },
        groupBy: {
          visible: sectionVisibility.groupBy,
          primary: groupByPrimary,
          overflow: groupByOverflow,
        },
      },
      focus: {
        title: asText(focusIntent.title),
        summary: asText(focusIntent.summary),
        actions: Array.isArray(focusIntent.actions) ? focusIntent.actions : [],
      },
      strictAlert: sectionVisibility.strictAlert
        ? {
            title: asText(unref(options.strict.title)),
            summary: strictSummary,
            defaultsSummary: strictDefaults || undefined,
          }
        : undefined,
      groupSummary: sectionVisibility.groupSummary
        ? {
            visible: true,
            items: asList(unref(options.groupSummary.items)) as Array<Record<string, unknown>>,
          }
        : undefined,
      actions: {
        primary: actionPrimary,
        overflowGroups: actionOverflowGroups,
      },
      content: {
        kind: contentKind,
        list: contentKind === 'list' ? { summaryItems: listSummaryItems } : undefined,
        kanban: contentKind === 'kanban' ? { overviewItems: kanbanOverviewItems } : undefined,
        advanced: contentKind === 'advanced'
          ? {
              title: asText(unref(options.content.advancedTitle)),
              hint: asText(unref(options.content.advancedHint)),
              rows: advancedRows,
            }
          : undefined,
      },
      empty: unref(options.page.status) === 'empty'
        ? {
            title: asText(focusIntent.emptyTitle),
            hint: asText(focusIntent.emptyHint),
            reason: asText(unref(options.empty.reasonText)) || undefined,
            primaryAction: focusIntent.primaryAction,
            secondaryAction: focusIntent.secondaryAction,
          }
        : undefined,
      hud: {
        visible: Boolean(unref(options.hud.visible)) && sectionVisibility.hud,
        title: asText(unref(options.hud.title)) || 'View Context',
        entries: buildHudEntries(options.hud.state),
      },
      sections: sectionVisibility,
    };
  });

  return { vm };
}
