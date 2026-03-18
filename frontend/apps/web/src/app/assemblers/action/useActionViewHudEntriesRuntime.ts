type Dict = Record<string, unknown>;

type HudEntry = {
  label: string;
  value: unknown;
};

type UseActionViewHudEntriesRuntimeOptions = {
  buildHudEntriesInput: () => Dict;
};

export function useActionViewHudEntriesRuntime(options: UseActionViewHudEntriesRuntimeOptions) {
  function buildHudEntries(): HudEntry[] {
    const input = options.buildHudEntriesInput();
    return [
      { label: 'action_id', value: input.actionId || '-' },
      { label: 'menu_id', value: input.menuId || '-' },
      { label: 'scene_key', value: input.sceneKey || '-' },
      { label: 'model', value: input.model || '-' },
      { label: 'view_mode', value: input.viewMode || '-' },
      { label: 'contract_view_type', value: input.contractViewType || '-' },
      { label: 'contract_filter', value: input.activeContractFilterKey || '-' },
      { label: 'saved_filter', value: input.activeSavedFilterKey || '-' },
      { label: 'group_by', value: input.activeGroupByField || '-' },
      { label: 'group_offset', value: input.groupWindowOffset || 0 },
      { label: 'group_window_id', value: input.groupWindowId || '-' },
      { label: 'group_query_fp', value: input.groupQueryFingerprint || '-' },
      { label: 'group_window_digest', value: input.groupWindowDigest || '-' },
      { label: 'group_window_identity_key', value: input.groupWindowIdentityKey || '-' },
      { label: 'route_group_fp', value: input.routeGroupFp || '-' },
      { label: 'route_group_wid', value: input.routeGroupWid || '-' },
      { label: 'route_group_wdg', value: input.routeGroupWdg || '-' },
      { label: 'route_group_wik', value: input.routeGroupWik || '-' },
      { label: 'contract_actions', value: input.contractActionCount || 0 },
      { label: 'contract_limit', value: input.contractLimit || 0 },
      { label: 'contract_read', value: input.contractReadAllowed },
      { label: 'contract_warnings', value: input.contractWarningCount || 0 },
      { label: 'contract_degraded', value: input.contractDegraded },
      { label: 'order', value: input.sortLabel || '-' },
      { label: 'last_intent', value: input.lastIntent || '-' },
      { label: 'write_mode', value: input.lastWriteMode || '-' },
      { label: 'trace_id', value: input.traceId || input.lastTraceId || '-' },
      { label: 'latency_ms', value: input.lastLatencyMs ?? '-' },
      { label: 'route', value: input.routeFullPath || '' },
    ];
  }

  return {
    buildHudEntries,
  };
}
