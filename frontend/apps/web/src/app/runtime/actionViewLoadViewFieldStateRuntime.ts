type KanbanProfile = {
  titleField: string;
  primaryFields: string[];
  secondaryFields: string[];
  statusFields: string[];
  metricFields: string[];
  quickActionCount: number;
};

type ListProfileLike = {
  columns?: string[];
};

export function resolveLoadKanbanFieldApplyState(options: {
  kanbanContractFields: string[];
  fallbackKanbanFields: string[];
  kanbanProfile: KanbanProfile;
  advancedContractFields: string[];
  uniqueFieldsFn: (fields: string[]) => string[];
}): {
  advancedFields: string[];
  kanbanFields: string[];
  kanbanTitleFieldHint: string;
  kanbanPrimaryFields: string[];
  kanbanSecondaryFields: string[];
  kanbanStatusFields: string[];
  kanbanMetricFields: string[];
  kanbanQuickActionCount: number;
} {
  const effectiveKanbanFields = options.kanbanContractFields.length
    ? options.kanbanContractFields
    : options.uniqueFieldsFn([...options.fallbackKanbanFields, 'id', 'name']);
  return {
    advancedFields: options.advancedContractFields,
    kanbanFields: effectiveKanbanFields,
    kanbanTitleFieldHint: options.kanbanProfile.titleField,
    kanbanPrimaryFields: options.uniqueFieldsFn(
      [...options.kanbanProfile.primaryFields].filter((name) => effectiveKanbanFields.includes(name)),
    ),
    kanbanSecondaryFields: options.uniqueFieldsFn(
      [...options.kanbanProfile.secondaryFields].filter((name) => effectiveKanbanFields.includes(name)),
    ),
    kanbanStatusFields: options.uniqueFieldsFn(
      [...options.kanbanProfile.statusFields].filter((name) => effectiveKanbanFields.includes(name)),
    ),
    kanbanMetricFields: options.uniqueFieldsFn(
      [...options.kanbanProfile.metricFields].filter((name) => effectiveKanbanFields.includes(name)),
    ),
    kanbanQuickActionCount: Number(options.kanbanProfile.quickActionCount || 0),
  };
}

export function resolveLoadRequestedFieldsApplyState(options: {
  viewMode: string;
  kanbanFields: string[];
  contractColumns: string[];
  listProfile: ListProfileLike;
  advancedFields: string[];
  resolveRequestedFieldsFn: (columns: string[], listProfile: ListProfileLike) => string[];
}): {
  requestedFields: string[];
} {
  if (options.viewMode === 'kanban') {
    return { requestedFields: options.kanbanFields };
  }
  if (options.viewMode === 'tree') {
    return {
      requestedFields: options.resolveRequestedFieldsFn(options.contractColumns, options.listProfile),
    };
  }
  return { requestedFields: options.advancedFields };
}

export function resolveLoadMissingColumnsApplyState(options: {
  missingColumnsState: { message: string; recordsLength: number } | null;
  currentErrorMessage: string;
}): {
  shouldBlock: boolean;
  message: string;
  statusInput: { error: string; recordsLength: number };
} {
  if (!options.missingColumnsState) {
    return {
      shouldBlock: false,
      message: '',
      statusInput: {
        error: options.currentErrorMessage,
        recordsLength: 0,
      },
    };
  }
  return {
    shouldBlock: true,
    message: options.missingColumnsState.message,
    statusInput: {
      error: options.currentErrorMessage,
      recordsLength: options.missingColumnsState.recordsLength,
    },
  };
}
