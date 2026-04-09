type Dict = Record<string, unknown>;

export function resolveActionViewAdvancedTitle(options: {
  strictContractMode: boolean;
  strictAdvancedViewContract: Dict;
  viewMode: string;
  pageText: (key: string, fallback: string) => string;
}): string {
  const labels: Record<string, string> = {
    pivot: options.pageText('advanced_title_pivot', '数据透视视图'),
    graph: options.pageText('advanced_title_graph', '图表视图'),
    calendar: options.pageText('advanced_title_calendar', '日历视图'),
    gantt: options.pageText('advanced_title_gantt', '甘特视图'),
    activity: options.pageText('advanced_title_activity', '活动视图'),
    dashboard: options.pageText('advanced_title_dashboard', '仪表板视图'),
  };
  const fallbackTitle = labels[options.viewMode] || options.pageText('advanced_title_default', '高级视图');
  if (options.strictContractMode) {
    const title = String(options.strictAdvancedViewContract.title || '').trim();
    return title || fallbackTitle;
  }
  return fallbackTitle;
}

export function resolveActionViewAdvancedHint(options: {
  strictContractMode: boolean;
  strictAdvancedViewContract: Dict;
  viewMode: string;
  pageText: (key: string, fallback: string) => string;
}): string {
  const hints: Record<string, string> = {
    pivot: options.pageText('advanced_hint_pivot', '当前为可读降级视图，可查看核心统计记录并继续下钻到列表/表单。'),
    graph: options.pageText('advanced_hint_graph', '当前为可读降级视图，可查看核心指标记录并继续下钻到列表/表单。'),
    calendar: options.pageText('advanced_hint_calendar', '当前为可读降级视图，可查看时间相关记录并继续下钻到列表/表单。'),
    gantt: options.pageText('advanced_hint_gantt', '当前为可读降级视图，可查看进度相关记录并继续下钻到列表/表单。'),
    activity: options.pageText('advanced_hint_activity', '当前为可读降级视图，可查看活动记录并继续下钻到列表/表单。'),
    dashboard: options.pageText('advanced_hint_dashboard', '当前为可读降级视图，可查看关键记录并继续下钻到列表/表单。'),
  };
  const fallbackHint = hints[options.viewMode] || options.pageText('advanced_hint_default', '当前视图使用可读降级渲染。');
  if (options.strictContractMode) {
    const hint = String(options.strictAdvancedViewContract.hint || '').trim();
    return hint || fallbackHint;
  }
  return fallbackHint;
}
