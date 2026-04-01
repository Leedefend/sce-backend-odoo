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
      { label: '动作 ID', value: input.actionId || '-' },
      { label: '菜单 ID', value: input.menuId || '-' },
      { label: '场景键', value: input.sceneKey || '-' },
      { label: '模型', value: input.model || '-' },
      { label: '视图模式', value: input.viewMode || '-' },
      { label: '契约视图类型', value: input.contractViewType || '-' },
      { label: '当前契约筛选', value: input.activeContractFilterKey || '-' },
      { label: '当前已保存筛选', value: input.activeSavedFilterKey || '-' },
      { label: '当前分组字段', value: input.activeGroupByField || '-' },
      { label: '分组窗口偏移', value: input.groupWindowOffset || 0 },
      { label: '分组窗口 ID', value: input.groupWindowId || '-' },
      { label: '分组查询指纹', value: input.groupQueryFingerprint || '-' },
      { label: '分组窗口摘要', value: input.groupWindowDigest || '-' },
      { label: '分组窗口身份键', value: input.groupWindowIdentityKey || '-' },
      { label: '路由分组指纹', value: input.routeGroupFp || '-' },
      { label: '路由分组窗口 ID', value: input.routeGroupWid || '-' },
      { label: '路由分组摘要', value: input.routeGroupWdg || '-' },
      { label: '路由分组身份键', value: input.routeGroupWik || '-' },
      { label: '契约动作数', value: input.contractActionCount || 0 },
      { label: '契约限制数', value: input.contractLimit || 0 },
      { label: '契约可读', value: input.contractReadAllowed },
      { label: '契约告警数', value: input.contractWarningCount || 0 },
      { label: '契约降级', value: input.contractDegraded },
      { label: '当前排序', value: input.sortLabel || '-' },
      { label: '最近意图', value: input.lastIntent || '-' },
      { label: '写入模式', value: input.lastWriteMode || '-' },
      { label: '追踪 ID', value: input.traceId || input.lastTraceId || '-' },
      { label: '耗时毫秒', value: input.lastLatencyMs ?? '-' },
      { label: '当前路由', value: input.routeFullPath || '' },
    ];
  }

  return {
    buildHudEntries,
  };
}
