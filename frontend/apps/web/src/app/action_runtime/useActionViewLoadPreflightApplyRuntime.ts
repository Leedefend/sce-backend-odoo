import type { Ref } from 'vue';
import type { ExecuteLoadPreflightResult } from './useActionViewLoadPreflightRuntime';

type ContinueResult = Extract<ExecuteLoadPreflightResult, { kind: 'continue' }>;
type BlockedResult = Extract<ExecuteLoadPreflightResult, { kind: 'blocked' }>;

type ApplyPreflightContinueOptions = {
  result: ContinueResult;
  contractViewTypeRef: Ref<string>;
  actionContractRef: Ref<unknown>;
  preferredViewModeRef: Ref<string>;
  activeContractFilterKeyRef: Ref<string>;
  activeSavedFilterKeyRef: Ref<string>;
  activeGroupByFieldRef: Ref<string>;
  contractReadAllowedRef: Ref<boolean>;
  contractWarningCountRef: Ref<number>;
  contractDegradedRef: Ref<boolean>;
  contractLimitRef: Ref<number>;
  sortValueRef: Ref<string>;
  resolvedModelRef: Ref<string>;
  setActionMeta: (payload: Record<string, unknown>) => void;
};

type ApplyPreflightBlockedOptions = {
  result: BlockedResult;
  setError: (error: Error, fallbackMessage?: string) => void;
  deriveListStatus: (input: unknown) => 'idle' | 'loading' | 'ok' | 'empty' | 'error';
  statusRef: Ref<'idle' | 'loading' | 'ok' | 'empty' | 'error'>;
};

export function useActionViewLoadPreflightApplyRuntime() {
  function applyLoadPreflightContinueState(options: ApplyPreflightContinueOptions): {
    contract: unknown;
    meta: Record<string, unknown> | null;
    typedContract: Record<string, unknown>;
    resolvedModel: string;
  } {
    const {
      result,
      contractViewTypeRef,
      actionContractRef,
      preferredViewModeRef,
      activeContractFilterKeyRef,
      activeSavedFilterKeyRef,
      activeGroupByFieldRef,
      contractReadAllowedRef,
      contractWarningCountRef,
      contractDegradedRef,
      contractLimitRef,
      sortValueRef,
      resolvedModelRef,
      setActionMeta,
    } = options;

    contractViewTypeRef.value = result.contractViewType;
    actionContractRef.value = result.typedContract;
    preferredViewModeRef.value = result.preferredViewMode;
    activeContractFilterKeyRef.value = result.activeContractFilterKey;
    activeSavedFilterKeyRef.value = result.activeSavedFilterKey;
    activeGroupByFieldRef.value = result.activeGroupByField;
    contractReadAllowedRef.value = result.contractReadAllowed;
    contractWarningCountRef.value = result.contractWarningCount;
    contractDegradedRef.value = result.contractDegraded;
    contractLimitRef.value = result.contractLimit;
    sortValueRef.value = result.sortValue;
    resolvedModelRef.value = result.resolvedModel || '';
    if (result.meta && result.setMetaModel) {
      setActionMeta({ ...result.meta, model: result.setMetaModel });
    }

    return {
      contract: result.contract,
      meta: result.meta,
      typedContract: result.typedContract,
      resolvedModel: result.resolvedModel,
    };
  }

  function applyLoadPreflightBlockedState(options: ApplyPreflightBlockedOptions): void {
    const {
      result,
      setError,
      deriveListStatus,
      statusRef,
    } = options;
    setError(new Error(result.message), result.message);
    statusRef.value = deriveListStatus(result.statusInput);
  }

  return {
    applyLoadPreflightContinueState,
    applyLoadPreflightBlockedState,
  };
}
