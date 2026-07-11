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
      { label: '操作编号', value: input.actionId || '-' },
      { label: '菜单编号', value: input.menuId || '-' },
      { label: '场景编码', value: input.sceneKey || '-' },
      { label: '业务对象', value: input.model || '-' },
      { label: '视图模式', value: input.viewMode || '-' },
      { label: '配置视图', value: input.contractViewType || '-' },
      { label: '配置筛选', value: input.activeContractFilterKey || '-' },
      { label: '已保存筛选', value: input.activeSavedFilterKey || '-' },
      { label: '分组字段', value: input.activeGroupByField || '-' },
      { label: '分组偏移', value: input.groupWindowOffset || 0 },
      { label: '分组窗口', value: input.groupWindowId || '-' },
      { label: '分组查询指纹', value: input.groupQueryFingerprint || '-' },
      { label: '分组窗口摘要', value: input.groupWindowDigest || '-' },
      { label: '分组窗口身份', value: input.groupWindowIdentityKey || '-' },
      { label: '路由分组指纹', value: input.routeGroupFp || '-' },
      { label: '路由分组窗口', value: input.routeGroupWid || '-' },
      { label: '路由分组摘要', value: input.routeGroupWdg || '-' },
      { label: '路由分组身份', value: input.routeGroupWik || '-' },
      { label: '配置操作数', value: input.contractActionCount || 0 },
      { label: '配置分页数', value: input.contractLimit || 0 },
      { label: '允许读取', value: input.contractReadAllowed },
      { label: '配置提醒数', value: input.contractWarningCount || 0 },
      { label: '配置补充状态', value: input.contractDegraded },
      { label: '排序', value: input.sortLabel || '-' },
      { label: '最近意图', value: input.lastIntent || '-' },
      { label: '写入模式', value: input.lastWriteMode || '-' },
      { label: '处理编号', value: input.traceId || input.lastTraceId || '-' },
      { label: '耗时', value: input.lastLatencyMs ?? '-' },
      { label: '当前路由', value: input.routeFullPath || '' },
    ];
  }

  return {
    buildHudEntries,
  };
}
