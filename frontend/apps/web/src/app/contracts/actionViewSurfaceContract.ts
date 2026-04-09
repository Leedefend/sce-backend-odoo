type Dict = Record<string, unknown>;

export type FocusNavAction = {
  label: string;
  to: string;
  query?: Record<string, string>;
};

export type SurfaceIntent = {
  title: string;
  summary: string;
  actions: FocusNavAction[];
  emptyTitle: string;
  emptyHint: string;
  primaryAction: FocusNavAction;
  secondaryAction?: FocusNavAction;
};

export type SurfaceIntentContract = {
  title?: string;
  summary?: string;
  actions?: FocusNavAction[];
  empty_title?: string;
  empty_hint?: string;
  primary_action?: FocusNavAction;
  secondary_action?: FocusNavAction;
};

function asDict(value: unknown): Dict {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  return value as Dict;
}

function parseViewModes(raw: unknown): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  const push = (value: unknown) => {
    const mode = normalizeActionViewMode(value);
    if (!mode || seen.has(mode)) return;
    seen.add(mode);
    out.push(mode);
  };
  if (Array.isArray(raw)) {
    raw.forEach(push);
    return out;
  }
  String(raw || '').split(',').forEach(push);
  return out;
}

function parseMetaViews(raw: unknown): string[] {
  if (!Array.isArray(raw)) return [];
  const out: string[] = [];
  const seen = new Set<string>();
  raw.forEach((entry) => {
    if (!Array.isArray(entry) || entry.length < 2) return;
    const mode = normalizeActionViewMode(entry[1]);
    if (!mode || seen.has(mode) || mode === 'form') return;
    seen.add(mode);
    out.push(mode);
  });
  return out;
}

function collectContractViewModes(contract: Dict | null): string[] {
  if (!contract) return [];
  const out: string[] = [];
  const seen = new Set<string>();
  const addMode = (raw: unknown) => {
    const mode = normalizeActionViewMode(raw);
    if (!mode || seen.has(mode)) return;
    seen.add(mode);
    out.push(mode);
  };
  const addModes = (raw: unknown) => {
    parseViewModes(raw).forEach((mode) => addMode(mode));
  };

  const head = asDict(contract.head);
  const uiContract = asDict(contract.ui_contract);
  const uiHead = asDict(uiContract.head);
  addModes(head.view_type);
  addModes(contract.view_type);
  addModes(uiHead.view_type);
  addModes(uiContract.view_type);

  const views = asDict(contract.views);
  const nestedViews = asDict(uiContract.views);
  if (views.tree || views.list || nestedViews.tree || nestedViews.list) addMode('tree');
  if (views.kanban || nestedViews.kanban) addMode('kanban');
  if (views.pivot || nestedViews.pivot) addMode('pivot');
  if (views.graph || nestedViews.graph) addMode('graph');
  if (views.calendar || nestedViews.calendar) addMode('calendar');
  if (views.gantt || nestedViews.gantt) addMode('gantt');
  if (views.activity || nestedViews.activity) addMode('activity');
  if (views.dashboard || nestedViews.dashboard) addMode('dashboard');
  return out;
}

export function normalizeActionViewMode(raw: unknown): string {
  const mode = String(raw || '').trim().toLowerCase();
  if (!mode) return '';
  if (mode === 'list') return 'tree';
  return mode;
}

export function resolveActionViewAvailableModes(options: {
  contractViewTypeRaw: unknown;
  metaViewModesRaw: unknown;
  metaViewsRaw?: unknown;
  contract: Dict | null;
}): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  const addMode = (raw: unknown) => {
    const mode = normalizeActionViewMode(raw);
    if (!mode || seen.has(mode)) return;
    seen.add(mode);
    out.push(mode);
  };
  const addModes = (raw: unknown) => {
    parseViewModes(raw).forEach((mode) => addMode(mode));
  };
  addModes(options.contractViewTypeRaw);
  addModes(options.metaViewModesRaw);
  parseMetaViews(options.metaViewsRaw).forEach((mode) => addMode(mode));
  collectContractViewModes(options.contract).forEach((mode) => addMode(mode));
  return out;
}

export function resolveActionViewModeLabel(options: {
  mode: string;
  strictContractMode: boolean;
  strictLabelMap: Record<string, string>;
  pageText: (key: string, fallback: string) => string;
}): string {
  const normalized = normalizeActionViewMode(options.mode);
  const strictLabel = options.strictLabelMap[normalized];
  if (options.strictContractMode && strictLabel) return strictLabel;
  if (normalized === 'tree') return options.pageText('view_mode_tree', '列表');
  if (normalized === 'form') return options.pageText('view_mode_form', '表单');
  if (normalized === 'kanban') return options.pageText('view_mode_kanban', '看板');
  if (normalized === 'pivot') return options.pageText('view_mode_pivot', '透视');
  if (normalized === 'graph') return options.pageText('view_mode_graph', '图表');
  if (normalized === 'calendar') return options.pageText('view_mode_calendar', '日历');
  if (normalized === 'gantt') return options.pageText('view_mode_gantt', '甘特');
  if (normalized === 'activity') return options.pageText('view_mode_activity', '活动');
  if (normalized === 'dashboard') return options.pageText('view_mode_dashboard', '仪表板');
  return options.mode;
}

export function resolveActionViewSurfaceIntent(options: {
  strictContractMode: boolean;
  strictSurfaceContract: Dict;
  contractSurfaceIntent: SurfaceIntentContract;
  sceneKey: string;
  pageText: (key: string, fallback: string) => string;
}): SurfaceIntent {
  const intentSource = options.strictContractMode
    ? asDict(options.strictSurfaceContract.intent)
    : asDict(options.contractSurfaceIntent);
  const primaryAction = asDict(intentSource.primary_action);
  const secondaryAction = asDict(intentSource.secondary_action);
  const actions = Array.isArray(intentSource.actions) ? (intentSource.actions as FocusNavAction[]) : [];

  return {
    title: String(intentSource.title || '').trim() || options.pageText('intent_title_default', '业务列表'),
    summary: String(intentSource.summary || '').trim() || options.pageText('intent_summary_default', '请通过契约动作继续处理。'),
    actions,
    emptyTitle: String(intentSource.empty_title || '').trim() || options.pageText('empty_title_default', '暂无可展示内容'),
    emptyHint: String(intentSource.empty_hint || '').trim() || options.pageText('empty_hint_default', ''),
    primaryAction: {
      label: String(primaryAction.label || '').trim() || options.pageText('primary_action_default', '去我的工作'),
      to: String(primaryAction.target || '/my-work'),
    },
    secondaryAction: Object.keys(secondaryAction).length
      ? {
          label: String(secondaryAction.label || '').trim() || options.pageText('secondary_action_default', '进入场景'),
          to: String(secondaryAction.target || `/s/${options.sceneKey || ''}`),
        }
      : undefined,
  };
}
