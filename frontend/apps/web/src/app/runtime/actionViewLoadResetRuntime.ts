import type { Ref } from 'vue';

export function buildActionViewLoadUiResetState(): {
  showMoreContractActions: boolean;
  showMoreSavedFilters: boolean;
  showMoreGroupBy: boolean;
  status: 'loading';
  traceId: string;
  lastIntent: string;
  lastWriteMode: string;
  lastLatencyMs: number | null;
} {
  return {
    showMoreContractActions: false,
    showMoreSavedFilters: false,
    showMoreGroupBy: false,
    status: 'loading',
    traceId: '',
    lastIntent: 'api.data.list',
    lastWriteMode: 'read',
    lastLatencyMs: null,
  };
}

export function buildActionViewLoadContractResetState(): {
  contractViewType: string;
  actionContract: null;
  resolvedModelRef: string;
  contractLimit: number;
} {
  return {
    contractViewType: '',
    actionContract: null,
    resolvedModelRef: '',
    contractLimit: 40,
  };
}

export function buildActionViewLoadDataResetState(): {
  records: Array<Record<string, unknown>>;
  groupedRows: Array<Record<string, unknown>>;
  groupSummaryItems: Array<Record<string, unknown>>;
} {
  return {
    records: [],
    groupedRows: [],
    groupSummaryItems: [],
  };
}

export function buildActionViewLoadGroupWindowResetState(): {
  groupWindowCount: number;
  groupWindowTotal: number | null;
  groupWindowStart: number | null;
  groupWindowEnd: number | null;
  groupWindowId: string;
  groupQueryFingerprint: string;
  groupWindowDigest: string;
  groupWindowIdentityKey: string;
  groupWindowPrevOffset: number | null;
  groupWindowNextOffset: number | null;
} {
  return {
    groupWindowCount: 0,
    groupWindowTotal: null,
    groupWindowStart: null,
    groupWindowEnd: null,
    groupWindowId: '',
    groupQueryFingerprint: '',
    groupWindowDigest: '',
    groupWindowIdentityKey: '',
    groupWindowPrevOffset: null,
    groupWindowNextOffset: null,
  };
}

export function buildActionViewLoadViewFieldResetState(): {
  columns: string[];
  kanbanFields: string[];
  kanbanPrimaryFields: string[];
  kanbanSecondaryFields: string[];
  kanbanStatusFields: string[];
  kanbanTitleFieldHint: string;
  advancedFields: string[];
} {
  return {
    columns: [],
    kanbanFields: [],
    kanbanPrimaryFields: [],
    kanbanSecondaryFields: [],
    kanbanStatusFields: [],
    kanbanTitleFieldHint: '',
    advancedFields: [],
  };
}

export function applyActionViewLoadResetState(options: {
  showMoreContractActions: Ref<boolean>;
  showMoreSavedFilters: Ref<boolean>;
  showMoreGroupBy: Ref<boolean>;
  status: Ref<'idle' | 'loading' | 'ok' | 'empty' | 'error'>;
  traceId: Ref<string>;
  lastIntent: Ref<string>;
  lastWriteMode: Ref<string>;
  lastLatencyMs: Ref<number | null>;
  contractViewType: Ref<string>;
  actionContract: Ref<unknown>;
  resolvedModelRef: Ref<string>;
  contractLimit: Ref<number>;
  records: Ref<Array<Record<string, unknown>>>;
  groupedRows: Ref<Array<Record<string, unknown>>>;
  groupSummaryItems: Ref<Array<Record<string, unknown>>>;
  groupWindowCount: Ref<number>;
  groupWindowTotal: Ref<number | null>;
  groupWindowStart: Ref<number | null>;
  groupWindowEnd: Ref<number | null>;
  groupWindowId: Ref<string>;
  groupQueryFingerprint: Ref<string>;
  groupWindowDigest: Ref<string>;
  groupWindowIdentityKey: Ref<string>;
  groupWindowPrevOffset: Ref<number | null>;
  groupWindowNextOffset: Ref<number | null>;
  columns: Ref<string[]>;
  kanbanFields: Ref<string[]>;
  kanbanPrimaryFields: Ref<string[]>;
  kanbanSecondaryFields: Ref<string[]>;
  kanbanStatusFields: Ref<string[]>;
  kanbanTitleFieldHint: Ref<string>;
  advancedFields: Ref<string[]>;
}): void {
  const ui = buildActionViewLoadUiResetState();
  const contract = buildActionViewLoadContractResetState();
  const data = buildActionViewLoadDataResetState();
  const group = buildActionViewLoadGroupWindowResetState();
  const fields = buildActionViewLoadViewFieldResetState();

  options.showMoreContractActions.value = ui.showMoreContractActions;
  options.showMoreSavedFilters.value = ui.showMoreSavedFilters;
  options.showMoreGroupBy.value = ui.showMoreGroupBy;
  options.status.value = ui.status;
  options.traceId.value = ui.traceId;
  options.lastIntent.value = ui.lastIntent;
  options.lastWriteMode.value = ui.lastWriteMode;
  options.lastLatencyMs.value = ui.lastLatencyMs;

  options.contractViewType.value = contract.contractViewType;
  options.actionContract.value = contract.actionContract;
  options.resolvedModelRef.value = contract.resolvedModelRef;
  options.contractLimit.value = contract.contractLimit;

  options.records.value = data.records;
  options.groupedRows.value = data.groupedRows;
  options.groupSummaryItems.value = data.groupSummaryItems;

  options.groupWindowCount.value = group.groupWindowCount;
  options.groupWindowTotal.value = group.groupWindowTotal;
  options.groupWindowStart.value = group.groupWindowStart;
  options.groupWindowEnd.value = group.groupWindowEnd;
  options.groupWindowId.value = group.groupWindowId;
  options.groupQueryFingerprint.value = group.groupQueryFingerprint;
  options.groupWindowDigest.value = group.groupWindowDigest;
  options.groupWindowIdentityKey.value = group.groupWindowIdentityKey;
  options.groupWindowPrevOffset.value = group.groupWindowPrevOffset;
  options.groupWindowNextOffset.value = group.groupWindowNextOffset;

  options.columns.value = fields.columns;
  options.kanbanFields.value = fields.kanbanFields;
  options.kanbanPrimaryFields.value = fields.kanbanPrimaryFields;
  options.kanbanSecondaryFields.value = fields.kanbanSecondaryFields;
  options.kanbanStatusFields.value = fields.kanbanStatusFields;
  options.kanbanTitleFieldHint.value = fields.kanbanTitleFieldHint;
  options.advancedFields.value = fields.advancedFields;
}

