type Dict = Record<string, unknown>;

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
  groupWindowOffset: number;
  groupSampleLimit: number;
  contractLimit: number;
  groupPageOffsets: Record<string, number>;
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
  };
  resolveLoadPreflightFieldFlags: (input: Dict) => { hasActiveField: boolean; hasAssigneeField: boolean };
  loadAssigneeOptions: () => Promise<void>;
  resolveLoadRequestedFieldsApplyState: (input: Dict) => { requestedFields: string[] };
  resolveLoadMissingTreeColumnsErrorState: (input: Dict) => Dict;
  resolveLoadMissingColumnsApplyState: (input: Dict) => { shouldBlock: boolean; message: string; statusInput: string };
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
  hasActiveFieldRef: { value: boolean };
  hasAssigneeFieldRef: { value: boolean };
};

type ExecuteLoadDataRequestResult =
  | {
      blocked: true;
      message: string;
      statusInput: string;
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

export function useActionViewLoadRequestRuntime() {
  async function executeLoadDataRequest(options: ExecuteLoadDataRequestOptions): Promise<ExecuteLoadDataRequestResult> {
    const contractColumns = options.convergeColumnsForSurface(
      options.extractColumnsFromContract(options.contract, options.sceneReadyColumns),
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

    const fieldFlags = options.resolveLoadPreflightFieldFlags({
      fieldMapRaw: options.typedContract.fields || {},
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
      effectiveFilterDomainRaw: options.resolveEffectiveFilterDomainRaw(),
      activeGroupByField: options.activeGroupByField,
      groupWindowOffset: options.groupWindowOffset,
      groupSampleLimit: options.groupSampleLimit,
      contractLimit: options.contractLimit,
      groupPageOffsets: options.groupPageOffsets,
      requestContext,
      requestContextRaw,
      searchTerm: options.searchTerm,
      order: options.sortLabel,
    });
    const result = await options.listRecordsRaw(requestPayload);

    return {
      blocked: false,
      result,
      contractColumns,
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

