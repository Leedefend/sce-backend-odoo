import { resolveUnifiedPageContractV2PrimaryDataSource } from '../contracts/unifiedPageContractV2';

type Dict = Record<string, unknown>;
type StatusInput = { error: string; recordsLength: number };

type ExecuteLoadDataRequestOptions = {
  contract: unknown;
  typedContract: {
    fields?: Record<string, unknown>;
  };
  viewMode: string;
  sceneReadyColumns: string[];
  listProfile: unknown;
  resolvedModel: string;
  actionId: number;
  searchTerm: string;
  sortLabel: string;
  activeGroupByField: string;
  listOffset: number;
  groupWindowOffset: number;
  groupSampleLimit: number;
  contractLimit: number;
  groupPageOffsets: Record<string, number>;
  routeDomainRaw?: unknown;
  routeContextRaw?: unknown;
  resolveEffectiveFilterDomainRaw: () => string;
  resolveEffectiveFilterDomain: () => unknown[];
  resolveEffectiveRequestContext: () => Dict;
  resolveEffectiveRequestContextRaw: () => string;
  mergeSceneDomain: (left: unknown[] | undefined, right: unknown[] | undefined) => unknown[];
  mergeActiveFilterDomain: (base: unknown[] | undefined, active: unknown[] | undefined) => unknown[];
  mergeContext: (left: Dict, right: Dict) => Dict;
  metaDomainRaw: unknown;
  sceneFiltersRaw: unknown;
  metaContextRaw: unknown;
  extractColumnsFromContract: (contract: unknown, fallbackColumns: string[]) => string[];
  convergeColumnsForSurface: (rawColumns: string[], fields: Record<string, unknown>) => string[];
  extractKanbanFields: (contract: unknown) => string[];
  extractKanbanProfile: (contract: unknown) => Record<string, unknown>;
  extractAdvancedViewFields: (contract: unknown, viewMode: string) => string[];
  resolveRequestedFields: (columns: string[], listProfile: unknown) => string[];
  uniqueFields: (fields: string[]) => string[];
  resolveLoadKanbanFieldApplyState: (input: Dict) => {
    advancedFields: string[];
    kanbanFields: string[];
    kanbanTitleFieldHint: string;
    kanbanPrimaryFields: string[];
    kanbanSecondaryFields: string[];
    kanbanStatusFields: string[];
    kanbanMetricFields: string[];
    kanbanQuickActionCount: number;
  };
  resolveLoadPreflightFieldFlags: (input: Dict) => { hasActiveField: boolean; hasAssigneeField: boolean };
  loadAssigneeOptions: () => Promise<void>;
  resolveLoadRequestedFieldsApplyState: (input: Dict) => { requestedFields: string[] };
  resolveLoadMissingTreeColumnsErrorState: (input: Dict) => Dict;
  resolveLoadMissingColumnsApplyState: (input: Dict) => { shouldBlock: boolean; message: string; statusInput: StatusInput };
  resolveLoadDomainStateApply: (input: Dict) => { baseDomain: unknown[]; activeDomain: unknown[] };
  resolveLoadContextStateApply: (input: Dict) => { requestContext: Dict; requestContextRaw: string };
  resolveLoadRequestPayloadState: (input: Dict) => Dict;
  listRecordsRaw: (payload: Dict) => Promise<Dict>;
  currentErrorMessage: () => string;
  warn: (message: string, payload: Dict) => void;
  advancedFieldsRef: { value: string[] };
  kanbanFieldsRef: { value: string[] };
  kanbanTitleFieldHintRef: { value: string };
  kanbanPrimaryFieldsRef: { value: string[] };
  kanbanSecondaryFieldsRef: { value: string[] };
  kanbanStatusFieldsRef: { value: string[] };
  kanbanMetricFieldsRef: { value: string[] };
  kanbanQuickActionCountRef: { value: number };
  hasActiveFieldRef: { value: boolean };
  hasAssigneeFieldRef: { value: boolean };
};

type ExecuteLoadDataRequestResult =
  | {
      blocked: true;
      message: string;
      statusInput: StatusInput;
    }
  | {
      blocked: false;
      result: Dict;
      contractColumns: string[];
      requestedFields: string[];
      baseDomain: unknown[];
      activeDomain: unknown[];
      requestContext: Dict;
      requestContextRaw: string;
      requestPayload: Dict;
    };

function readRouteQueryValue(key: string): string {
  if (typeof window === 'undefined') return '';
  try {
    return String(new URLSearchParams(window.location.search).get(key) || '').trim();
  } catch {
    return '';
  }
}

export function useActionViewLoadRequestRuntime() {
  async function executeLoadDataRequest(options: ExecuteLoadDataRequestOptions): Promise<ExecuteLoadDataRequestResult> {
    const profileColumns = (
      options.listProfile
      && typeof options.listProfile === 'object'
      && Array.isArray((options.listProfile as { columns?: unknown[] }).columns)
    )
      ? ((options.listProfile as { columns?: unknown[] }).columns || []).map((item) => String(item || '').trim()).filter(Boolean)
      : [];
    const contractColumns = options.convergeColumnsForSurface(
      options.extractColumnsFromContract(options.contract, profileColumns),
      options.typedContract.fields || {},
    );
    const kanbanContractFields = options.extractKanbanFields(options.contract);
    const kanbanProfile = options.extractKanbanProfile(options.contract);
    const advancedContractFields = options.extractAdvancedViewFields(options.contract, options.viewMode);
    const fallbackKanbanFields = options.resolveRequestedFields(contractColumns, options.listProfile);
    const kanbanFieldState = options.resolveLoadKanbanFieldApplyState({
      kanbanContractFields,
      fallbackKanbanFields,
      kanbanProfile,
      advancedContractFields,
      uniqueFieldsFn: options.uniqueFields,
    });
    options.advancedFieldsRef.value = kanbanFieldState.advancedFields;
    options.kanbanFieldsRef.value = kanbanFieldState.kanbanFields;
    options.kanbanTitleFieldHintRef.value = kanbanFieldState.kanbanTitleFieldHint;
    options.kanbanPrimaryFieldsRef.value = kanbanFieldState.kanbanPrimaryFields;
    options.kanbanSecondaryFieldsRef.value = kanbanFieldState.kanbanSecondaryFields;
    options.kanbanStatusFieldsRef.value = kanbanFieldState.kanbanStatusFields;
    options.kanbanMetricFieldsRef.value = kanbanFieldState.kanbanMetricFields;
    options.kanbanQuickActionCountRef.value = kanbanFieldState.kanbanQuickActionCount;

    const fieldFlags = options.resolveLoadPreflightFieldFlags({
      listProfileRaw: options.listProfile,
    });
    options.hasActiveFieldRef.value = fieldFlags.hasActiveField;
    options.hasAssigneeFieldRef.value = fieldFlags.hasAssigneeField;
    await options.loadAssigneeOptions();

    if (options.viewMode === 'kanban' && !kanbanContractFields.length) {
      options.warn('[contract] missing kanban fields; fallback to list/profile fields', {
        actionId: options.actionId,
        model: options.resolvedModel,
        fallbackFieldCount: kanbanFieldState.kanbanFields.length,
      });
    }

    const requestedFieldState = options.resolveLoadRequestedFieldsApplyState({
      viewMode: options.viewMode,
      kanbanFields: kanbanFieldState.kanbanFields,
      contractColumns,
      listProfile: options.listProfile,
      advancedFields: kanbanFieldState.advancedFields,
      resolveRequestedFieldsFn: options.resolveRequestedFields,
    });
    const requestedFields = requestedFieldState.requestedFields;

    const missingColumnsState = options.resolveLoadMissingTreeColumnsErrorState({
      viewMode: options.viewMode,
      contractColumns,
    });
    const missingColumnsApplyState = options.resolveLoadMissingColumnsApplyState({
      missingColumnsState,
      currentErrorMessage: options.currentErrorMessage(),
    });
    if (missingColumnsApplyState.shouldBlock) {
      return {
        blocked: true,
        message: missingColumnsApplyState.message,
        statusInput: missingColumnsApplyState.statusInput,
      };
    }

    const domainState = options.resolveLoadDomainStateApply({
      metaDomainRaw: options.metaDomainRaw,
      sceneFiltersRaw: options.sceneFiltersRaw,
      effectiveFilterDomain: options.resolveEffectiveFilterDomain(),
      mergeSceneDomainFn: options.mergeSceneDomain,
      mergeActiveFilterDomainFn: options.mergeActiveFilterDomain,
    });
    const baseDomain = domainState.baseDomain;
    const activeDomain = domainState.activeDomain;

    const contextState = options.resolveLoadContextStateApply({
      metaContextRaw: options.metaContextRaw,
      effectiveRequestContext: options.resolveEffectiveRequestContext(),
      effectiveRequestContextRaw: options.resolveEffectiveRequestContextRaw(),
      mergeContextFn: options.mergeContext,
    });
    const requestContext = contextState.requestContext;
    const requestContextRaw = contextState.requestContextRaw;

    const requestPayload = options.resolveLoadRequestPayloadState({
      model: options.resolvedModel,
      requestedFields,
      activeDomain,
      effectiveFilterDomainRaw: String(options.routeDomainRaw || '').trim()
        || readRouteQueryValue('domain_raw')
        || options.resolveEffectiveFilterDomainRaw(),
      activeGroupByField: options.activeGroupByField,
      listOffset: options.listOffset,
      groupWindowOffset: options.groupWindowOffset,
      groupSampleLimit: options.groupSampleLimit,
      contractLimit: options.contractLimit,
      groupPageOffsets: options.groupPageOffsets,
      requestContext,
      requestContextRaw: String(options.routeContextRaw || '').trim()
        || readRouteQueryValue('context_raw')
        || requestContextRaw,
      searchTerm: options.searchTerm,
      order: options.sortLabel,
    });
    const v2PrimarySource = resolveUnifiedPageContractV2PrimaryDataSource(options.contract);
    const v2PrimaryParams = (v2PrimarySource.params && typeof v2PrimarySource.params === 'object' && !Array.isArray(v2PrimarySource.params))
      ? v2PrimarySource.params as Dict
      : {};
    const sourceDomainRaw = String(v2PrimaryParams.domain_raw || v2PrimaryParams.domainRaw || '').trim();
    if (sourceDomainRaw && !String(requestPayload.domain_raw || '').trim()) {
      requestPayload.domain_raw = sourceDomainRaw;
    }
    const sourceContextRaw = String(v2PrimaryParams.context_raw || v2PrimaryParams.contextRaw || '').trim();
    if (sourceContextRaw && !String(requestPayload.context_raw || '').trim()) {
      requestPayload.context_raw = sourceContextRaw;
    }
    if (Array.isArray(v2PrimaryParams.domain) && !(Array.isArray(requestPayload.domain) && requestPayload.domain.length)) {
      requestPayload.domain = v2PrimaryParams.domain;
    }
    if (v2PrimaryParams.context && typeof v2PrimaryParams.context === 'object' && !Array.isArray(v2PrimaryParams.context)) {
      requestPayload.context = {
        ...(v2PrimaryParams.context as Dict),
        ...((requestPayload.context && typeof requestPayload.context === 'object' && !Array.isArray(requestPayload.context)) ? requestPayload.context as Dict : {}),
      };
    }
    const result = await options.listRecordsRaw(requestPayload);
    const resolvedContractColumns = options.uniqueFields([
      ...contractColumns,
      ...requestedFields,
    ]);

    return {
      blocked: false,
      result,
      contractColumns: resolvedContractColumns,
      requestedFields,
      baseDomain,
      activeDomain,
      requestContext,
      requestContextRaw,
      requestPayload,
    };
  }

  return {
    executeLoadDataRequest,
  };
}
