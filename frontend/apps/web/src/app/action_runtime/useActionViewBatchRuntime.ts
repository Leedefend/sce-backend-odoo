import type { Ref } from 'vue';

type BatchAction = 'archive' | 'activate' | 'delete';

type BatchRequestLike = {
  model: string;
  ids: number[];
  action: string;
  assigneeId?: number;
  ifMatchMap?: Record<number, string>;
  idempotencyKey?: string;
  context?: Record<string, unknown>;
};

type BatchErrorLine = { text: string; actionRaw?: string; actionLabel?: string };

type BatchCatchState = {
  batchMessage: string;
  batchDetails: BatchErrorLine[];
  failedCsvFileName: string;
  failedCsvContentB64: string;
  batchFailedOffset: number;
  batchHasMoreFailures: boolean;
  lastBatchRequest: BatchRequestLike | null;
};

type BatchResetState = BatchCatchState & {
  batchFailedLimit: number;
};

type UseActionViewBatchRuntimeOptions = {
  selectedIds: Ref<number[]>;
  selectedAssigneeId: Ref<number | null>;
  batchBusy: Ref<boolean>;
  batchMessage: Ref<string>;
  batchDetails: Ref<BatchErrorLine[]>;
  failedCsvFileName: Ref<string>;
  failedCsvContentB64: Ref<string>;
  batchFailedOffset: Ref<number>;
  batchFailedLimit: Ref<number>;
  batchHasMoreFailures: Ref<boolean>;
  lastBatchRequest: Ref<BatchRequestLike | null>;

  pageText: (key: string, fallback: string) => string;
  reportBatchError: (err: unknown, fallback: string) => void;
  buildBatchRequestContext: () => Record<string, unknown>;
  applyBatchSuccessReload: () => Promise<void>;
  downloadCsv: (filename: string, mimeType: string, contentB64: string) => void;

  resolveTargetModel: () => string;

  buildIfMatchMap: (ids: number[]) => Record<number, string>;
  buildIdempotencyKey: (action: string, ids: number[], extra?: Record<string, unknown>) => string;

  batchUpdateRecords: (payload: Record<string, unknown>) => Promise<Record<string, unknown>>;
  unlinkRecords: (payload: {
    model: string;
    ids: number[];
    context?: Record<string, unknown>;
    idempotencyKey?: string;
  }) => Promise<Record<string, unknown>>;
  exportRecordsCsv: (payload: Record<string, unknown>) => Promise<Record<string, unknown>>;

  buildBatchUpdateRequest: (payload: Record<string, unknown>) => Record<string, unknown>;
  buildBatchErrorLine: (payload: Record<string, unknown>) => BatchErrorLine;
  applyBatchFailureArtifacts: (result: Record<string, unknown>, plan?: Record<string, unknown>) => void;

  resolveBatchOperationResetState: (input: { batchFailedLimit: number }) => BatchResetState;
  resolveBatchActionTargetModel: (input: { resolvedModelRaw: string; routeModelRaw: string }) => string;
  resolveBatchActionDeleteMode: (input: { contractDeleteModeRaw: unknown }) => string;
  resolveBatchActionGuardDecision: (input: Record<string, unknown>) => { ok: boolean; reason?: string };
  resolveBatchActionGuardMessage: (input: { reason?: string; text: (key: string, fallback: string) => string }) => string;
  resolveBatchDeleteExecutionSeed: (input: {
    selectedIds: number[];
    buildIfMatchMap: (ids: number[]) => Record<number, string>;
    buildIdempotencyKey: (action: string, ids: number[], extra?: Record<string, unknown>) => string;
  }) => { requestAction: string; ifMatchMap: Record<number, string>; idempotencyKey: string };
  resolveBatchActionResultMessage: (input: Record<string, unknown>) => string;
  resolveBatchStandardExecutionSeed: (input: {
    action: BatchAction;
    selectedIds: number[];
    buildIfMatchMap: (ids: number[]) => Record<number, string>;
    buildIdempotencyKey: (action: string, ids: number[], extra?: Record<string, unknown>) => string;
  }) => { ifMatchMap: Record<number, string>; idempotencyKey: string };
  resolveBatchActionLastRequestState: (input: Record<string, unknown>) => BatchRequestLike;
  resolveBatchActionSuccessMessage: (input: Record<string, unknown>) => string;
  resolveBatchFailureCatchState: (input: Record<string, unknown>) => BatchCatchState;
  resolveBatchActionFailureFallback: (input: Record<string, unknown>) => Record<string, unknown>;
  resolveBatchAssignGuardDecision: (input: Record<string, unknown>) => { ok: boolean; reason?: string };
  resolveBatchAssignGuardMessage: (input: { reason?: string; text: (key: string, fallback: string) => string }) => string;
  resolveBatchAssignSeedState: (input: {
    selectedIds: number[];
    selectedAssigneeId: number;
    buildIfMatchMap: (ids: number[]) => Record<number, string>;
    buildIdempotencyKey: (action: string, ids: number[], extra?: Record<string, unknown>) => string;
  }) => { ifMatchMap: Record<number, string>; idempotencyKey: string; assigneeId: number };
  resolveBatchAssignResultMessage: (input: Record<string, unknown>) => string;
  resolveBatchAssignSuccessMessage: (input: Record<string, unknown>) => string;
  resolveBatchAssignFailureMessage: (text: (key: string, fallback: string) => string) => string;
  resolveBatchAssignErrorFallback: (input: Record<string, unknown>) => Record<string, unknown>;
  resolveBatchErrorHintResolver: (input: Record<string, unknown>) => (line: Record<string, unknown>) => string;
  resolveSuggestedAction: (suggestedAction: unknown, reasonCode: unknown, retryable: unknown) => string;

  resolveBatchExportResetState: (input: { batchFailedLimit: number }) => BatchResetState;
  resolveBatchExportTargetModel: (input: { resolvedModelRaw: string; routeModelRaw: string }) => string;
  resolveBatchExportGuardDecision: (input: Record<string, unknown>) => { ok: boolean; reason?: string };
  resolveExportGuardMessage: (input: { reason?: string; text: (key: string, fallback: string) => string }) => string;
  resolveBatchExportDomainState: (input: Record<string, unknown>) => unknown[];
  actionMetaDomain: () => unknown;
  sceneFilters: () => unknown;
  resolveEffectiveFilterDomain: () => unknown[];
  mergeSceneDomain: (base: unknown[], fallback?: unknown[]) => unknown[];
  mergeActiveFilterDomain: (base: unknown[], dynamic: unknown[]) => unknown[];
  columns: () => string[];
  sortLabel: () => string;
  resolveBatchExportRequestPayload: (input: Record<string, unknown>) => Record<string, unknown>;
  resolveBatchExportNoContent: (input: { contentB64Raw: unknown }) => boolean;
  resolveExportNoContentMessage: (text: (key: string, fallback: string) => string) => string;
  resolveExportDoneMessage: (input: Record<string, unknown>) => string;
  resolveExportFailedMessage: (text: (key: string, fallback: string) => string) => string;
  resolveBatchExportCatchState: (input: Record<string, unknown>) => BatchCatchState;
  resolveBatchExportErrorFallback: (input: Record<string, unknown>) => Record<string, unknown>;

  resolveLoadMoreFailuresGuardPlan: (input: Record<string, unknown>) => { ok: boolean; request: BatchRequestLike };
  resolveLoadMoreFailuresRequestPayload: (input: Record<string, unknown>) => Record<string, unknown>;
  resolveLoadMoreFailuresApplyPlan: () => Record<string, unknown>;
  resolveLoadMoreFailuresCatchState: (input: Record<string, unknown>) => BatchCatchState;
  resolveLoadMoreFailuresErrorFallback: (input: Record<string, unknown>) => Record<string, unknown>;

  hasActiveField: () => boolean;
  contractDeleteMode: () => unknown;
  resolvedModelRaw: () => string;
  routeModelRaw: () => string;
};

export function useActionViewBatchRuntime(options: UseActionViewBatchRuntimeOptions) {
  async function handleBatchAction(action: BatchAction) {
    const resetState = options.resolveBatchOperationResetState({ batchFailedLimit: options.batchFailedLimit.value });
    options.batchMessage.value = resetState.batchMessage;
    options.batchDetails.value = resetState.batchDetails;
    options.failedCsvFileName.value = resetState.failedCsvFileName;
    options.failedCsvContentB64.value = resetState.failedCsvContentB64;
    options.batchFailedOffset.value = resetState.batchFailedOffset;
    options.batchFailedLimit.value = resetState.batchFailedLimit;
    options.batchHasMoreFailures.value = resetState.batchHasMoreFailures;
    options.lastBatchRequest.value = resetState.lastBatchRequest;

    const targetModel = options.resolveBatchActionTargetModel({
      resolvedModelRaw: options.resolvedModelRaw(),
      routeModelRaw: options.routeModelRaw(),
    });
    const deleteMode = options.resolveBatchActionDeleteMode({
      contractDeleteModeRaw: options.contractDeleteMode(),
    });
    const actionGuard = options.resolveBatchActionGuardDecision({
      targetModel,
      selectedCount: options.selectedIds.value.length,
      action,
      hasActiveField: options.hasActiveField(),
      deleteMode,
    });
    if (!actionGuard.ok) {
      options.batchMessage.value = options.resolveBatchActionGuardMessage({ reason: actionGuard.reason, text: options.pageText });
      return;
    }

    options.batchBusy.value = true;
    try {
      if (action === 'delete') {
        const deleteSeed = options.resolveBatchDeleteExecutionSeed({
          selectedIds: options.selectedIds.value,
          buildIfMatchMap: options.buildIfMatchMap,
          buildIdempotencyKey: options.buildIdempotencyKey,
        });
        const requestContext = options.buildBatchRequestContext();
        const result = await options.unlinkRecords({
          model: targetModel,
          ids: options.selectedIds.value,
          idempotencyKey: deleteSeed.idempotencyKey,
          context: requestContext,
        });
        const succeeded = Array.isArray(result.ids) ? result.ids.length : options.selectedIds.value.length;
        options.batchMessage.value = options.resolveBatchActionResultMessage({
          action,
          idempotentReplay: Boolean(result.idempotent_replay),
          succeeded,
          failed: 0,
          text: options.pageText,
        });
        options.lastBatchRequest.value = {
          model: targetModel,
          ids: options.selectedIds.value,
          action: deleteSeed.requestAction,
          ifMatchMap: deleteSeed.ifMatchMap,
          idempotencyKey: deleteSeed.idempotencyKey,
          context: requestContext,
        };
        options.batchDetails.value = [];
        options.failedCsvFileName.value = '';
        options.failedCsvContentB64.value = '';
        options.batchFailedOffset.value = 0;
        options.batchHasMoreFailures.value = false;
        await options.applyBatchSuccessReload();
        return;
      }

      const standardSeed = options.resolveBatchStandardExecutionSeed({
        action,
        selectedIds: options.selectedIds.value,
        buildIfMatchMap: options.buildIfMatchMap,
        buildIdempotencyKey: options.buildIdempotencyKey,
      });
      const requestContext = options.buildBatchRequestContext();
      const result = await options.batchUpdateRecords(options.buildBatchUpdateRequest({
        model: targetModel,
        ids: options.selectedIds.value,
        action,
        ifMatchMap: standardSeed.ifMatchMap,
        idempotencyKey: standardSeed.idempotencyKey,
        context: requestContext,
      }));
      options.lastBatchRequest.value = options.resolveBatchActionLastRequestState({
        model: targetModel,
        ids: options.selectedIds.value,
        action,
        ifMatchMap: standardSeed.ifMatchMap,
        idempotencyKey: standardSeed.idempotencyKey,
        context: requestContext,
      });
      options.batchMessage.value = options.resolveBatchActionSuccessMessage({
        action,
        idempotentReplay: Boolean(result.idempotent_replay),
        succeeded: Number(result.succeeded || 0),
        failed: Number(result.failed || 0),
        text: options.pageText,
      });
      options.applyBatchFailureArtifacts(result);
      await options.applyBatchSuccessReload();
    } catch (err) {
      options.reportBatchError(err, 'batch update failed');
      const catchState = options.resolveBatchFailureCatchState({
        err,
        text: options.pageText,
        buildBatchErrorLine: options.buildBatchErrorLine,
        resolveHint: options.resolveBatchErrorHintResolver({ resolveSuggestedActionFn: options.resolveSuggestedAction }),
        fallback: options.resolveBatchActionFailureFallback({
          action,
          targetModel,
          text: options.pageText,
        }),
      });
      options.batchMessage.value = catchState.batchMessage;
      options.batchDetails.value = catchState.batchDetails;
      options.failedCsvFileName.value = catchState.failedCsvFileName;
      options.failedCsvContentB64.value = catchState.failedCsvContentB64;
      options.batchFailedOffset.value = catchState.batchFailedOffset;
      options.batchHasMoreFailures.value = catchState.batchHasMoreFailures;
      options.lastBatchRequest.value = catchState.lastBatchRequest;
    } finally {
      options.batchBusy.value = false;
    }
  }

  async function handleBatchAssign(assigneeId: number) {
    const targetModel = options.resolveTargetModel();
    const assignGuard = options.resolveBatchAssignGuardDecision({
      targetModel,
      selectedCount: options.selectedIds.value.length,
      assigneeId,
    });
    if (!assignGuard.ok) {
      options.batchMessage.value = options.resolveBatchAssignGuardMessage({ reason: assignGuard.reason, text: options.pageText });
      return;
    }
    options.batchBusy.value = true;
    try {
      const assignSeed = options.resolveBatchAssignSeedState({
        selectedIds: options.selectedIds.value,
        selectedAssigneeId: assigneeId,
        buildIfMatchMap: options.buildIfMatchMap,
        buildIdempotencyKey: options.buildIdempotencyKey,
      });
      const requestContext = options.buildBatchRequestContext();
      const result = await options.batchUpdateRecords(options.buildBatchUpdateRequest({
        model: targetModel,
        ids: options.selectedIds.value,
        action: 'assign',
        assigneeId: assignSeed.assigneeId,
        ifMatchMap: assignSeed.ifMatchMap,
        idempotencyKey: assignSeed.idempotencyKey,
        context: requestContext,
      }));
      options.lastBatchRequest.value = options.resolveBatchActionLastRequestState({
        model: targetModel,
        ids: options.selectedIds.value,
        action: 'assign',
        assigneeId: assignSeed.assigneeId,
        ifMatchMap: assignSeed.ifMatchMap,
        idempotencyKey: assignSeed.idempotencyKey,
        context: requestContext,
      });
      options.batchMessage.value = options.resolveBatchAssignResultMessage({
        idempotentReplay: Boolean(result.idempotent_replay),
        succeeded: Number(result.succeeded || 0),
        failed: Number(result.failed || 0),
        text: options.pageText,
      });
      options.applyBatchFailureArtifacts(result);
      options.selectedAssigneeId.value = null;
      await options.applyBatchSuccessReload();
    } catch (err) {
      options.reportBatchError(err, 'batch assign failed');
      options.batchMessage.value = options.resolveBatchAssignFailureMessage(options.pageText);
      const catchState = options.resolveBatchFailureCatchState({
        err,
        text: options.pageText,
        buildBatchErrorLine: options.buildBatchErrorLine,
        resolveHint: options.resolveBatchErrorHintResolver({ resolveSuggestedActionFn: options.resolveSuggestedAction }),
        fallback: options.resolveBatchAssignErrorFallback({
          targetModel,
          text: options.pageText,
        }),
      });
      options.batchDetails.value = catchState.batchDetails;
      options.failedCsvFileName.value = catchState.failedCsvFileName;
      options.failedCsvContentB64.value = catchState.failedCsvContentB64;
      options.batchFailedOffset.value = catchState.batchFailedOffset;
      options.batchHasMoreFailures.value = catchState.batchHasMoreFailures;
      options.lastBatchRequest.value = catchState.lastBatchRequest;
    } finally {
      options.batchBusy.value = false;
    }
  }

  async function exportByBackend(scope: 'selected' | 'all') {
    const resetState = options.resolveBatchExportResetState({ batchFailedLimit: options.batchFailedLimit.value });
    options.batchMessage.value = resetState.batchMessage;
    options.batchDetails.value = resetState.batchDetails;
    options.failedCsvFileName.value = resetState.failedCsvFileName;
    options.failedCsvContentB64.value = resetState.failedCsvContentB64;

    const targetModel = options.resolveBatchExportTargetModel({
      resolvedModelRaw: options.resolvedModelRaw(),
      routeModelRaw: options.routeModelRaw(),
    });
    const exportGuard = options.resolveBatchExportGuardDecision({
      targetModel,
      scope,
      selectedCount: options.selectedIds.value.length,
    });
    if (!exportGuard.ok) {
      options.batchMessage.value = options.resolveExportGuardMessage({ reason: exportGuard.reason, text: options.pageText });
      return;
    }

    options.batchBusy.value = true;
    try {
      const exportDomain = options.resolveBatchExportDomainState({
        actionMetaDomainRaw: options.actionMetaDomain(),
        sceneFiltersRaw: options.sceneFilters(),
        effectiveFilterDomain: options.resolveEffectiveFilterDomain(),
        mergeSceneDomainFn: options.mergeSceneDomain,
        mergeActiveFilterDomainFn: options.mergeActiveFilterDomain,
      });
      const result = await options.exportRecordsCsv(options.resolveBatchExportRequestPayload({
        model: targetModel,
        scope,
        selectedIds: options.selectedIds.value,
        domain: exportDomain,
        columns: options.columns(),
        order: options.sortLabel(),
        context: options.buildBatchRequestContext(),
      }));
      if (options.resolveBatchExportNoContent({ contentB64Raw: result.content_b64 })) {
        options.batchMessage.value = options.resolveExportNoContentMessage(options.pageText);
        return;
      }
      options.downloadCsv(result.file_name, result.mime_type, result.content_b64);
      options.batchMessage.value = options.resolveExportDoneMessage({ countRaw: result.count, text: options.pageText });
    } catch (err) {
      options.reportBatchError(err, 'batch export failed');
      options.batchMessage.value = options.resolveExportFailedMessage(options.pageText);
      const catchState = options.resolveBatchExportCatchState({
        err,
        text: options.pageText,
        buildBatchErrorLine: options.buildBatchErrorLine,
        resolveHint: options.resolveBatchErrorHintResolver({ resolveSuggestedActionFn: options.resolveSuggestedAction }),
        fallback: options.resolveBatchExportErrorFallback({
          targetModel,
          text: options.pageText,
        }),
      });
      options.batchDetails.value = catchState.batchDetails;
    } finally {
      options.batchBusy.value = false;
    }
  }

  function handleBatchExport(scope: 'selected' | 'all') {
    void exportByBackend(scope);
  }

  function handleDownloadFailedCsv() {
    if (!options.failedCsvContentB64.value) return;
    options.downloadCsv(options.failedCsvFileName.value || 'batch_failed.csv', 'text/csv', options.failedCsvContentB64.value);
  }

  async function handleLoadMoreFailures() {
    const loadMoreGuard = options.resolveLoadMoreFailuresGuardPlan({
      hasMoreFailures: options.batchHasMoreFailures.value,
      lastBatchRequest: options.lastBatchRequest.value,
    });
    if (!loadMoreGuard.ok) return;
    const req = loadMoreGuard.request;
    options.batchBusy.value = true;
    try {
      const result = await options.batchUpdateRecords(options.resolveLoadMoreFailuresRequestPayload({
        request: req,
        failedOffset: options.batchFailedOffset.value,
        failedLimit: options.batchFailedLimit.value,
      }));
      options.applyBatchFailureArtifacts(result, options.resolveLoadMoreFailuresApplyPlan());
    } catch (err) {
      options.reportBatchError(err, 'load more failures failed');
      const catchState = options.resolveLoadMoreFailuresCatchState({
        err,
        text: options.pageText,
        buildBatchErrorLine: options.buildBatchErrorLine,
        resolveHint: options.resolveBatchErrorHintResolver({ resolveSuggestedActionFn: options.resolveSuggestedAction }),
        fallback: options.resolveLoadMoreFailuresErrorFallback({
          model: req.model,
          action: req.action,
          text: options.pageText,
        }),
      });
      options.batchDetails.value = catchState.batchDetails;
    } finally {
      options.batchBusy.value = false;
    }
  }

  return {
    handleBatchAction,
    handleBatchAssign,
    handleBatchExport,
    handleDownloadFailedCsv,
    handleLoadMoreFailures,
  };
}
