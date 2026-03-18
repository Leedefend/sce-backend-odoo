export type ActionPageStatus = 'loading' | 'ok' | 'empty' | 'error';

export type FocusActionVM = {
  label: string;
  to: string;
  query?: Record<string, string>;
};

export type ChipVM = {
  key: string;
  label: string;
};

export type ChipGroupVM = {
  visible: boolean;
  primary: ChipVM[];
  overflow: ChipVM[];
};

export type ActionButtonVM = {
  key: string;
  label: string;
  enabled?: boolean;
  hint?: string;
};

export type ActionGroupVM = {
  key: string;
  label: string;
  actions: ActionButtonVM[];
};

export type ProjectionMetricVM = {
  key: string;
  label: string;
  value: string;
  tone: string;
};

export type GroupSummaryVM = {
  visible: boolean;
  items: Array<Record<string, unknown>>;
};

export type ListContentVM = {
  summaryItems: ProjectionMetricVM[];
};

export type KanbanContentVM = {
  overviewItems: ProjectionMetricVM[];
};

export type AdvancedContentVM = {
  title: string;
  hint: string;
};

export type ActionPageVM = {
  page: {
    title: string;
    status: ActionPageStatus;
    statusLabel: string;
    subtitle: string;
    traceId?: string;
    errorMessage?: string;
    sceneKey?: string;
    pageMode?: string;
    viewMode: string;
    availableViewModes: string[];
  };
  header: {
    actions: ActionButtonVM[];
  };
  filters: {
    routePreset?: {
      label: string;
      source?: string;
      clearable: boolean;
    };
    quickFilters: ChipGroupVM;
    savedFilters: ChipGroupVM;
    groupBy: ChipGroupVM;
  };
  focus: {
    title: string;
    summary: string;
    actions: FocusActionVM[];
  };
  strictAlert?: {
    title: string;
    summary: string;
    defaultsSummary?: string;
  };
  groupSummary?: GroupSummaryVM;
  actions: {
    primary: ActionButtonVM[];
    overflowGroups: ActionGroupVM[];
  };
  content: {
    kind: 'list' | 'kanban' | 'advanced';
    list?: ListContentVM;
    kanban?: KanbanContentVM;
    advanced?: AdvancedContentVM;
  };
  empty?: {
    title: string;
    hint: string;
    reason?: string;
    primaryAction: FocusActionVM;
    secondaryAction?: FocusActionVM;
  };
  hud?: {
    visible: boolean;
    title: string;
    entries: Array<{ label: string; value: unknown }>;
  };
  sections: {
    quickFilters: boolean;
    savedFilters: boolean;
    groupBy: boolean;
    focus: boolean;
    strictAlert: boolean;
    groupSummary: boolean;
    quickActions: boolean;
    hud: boolean;
  };
};
