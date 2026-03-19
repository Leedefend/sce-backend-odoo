import type { Ref } from 'vue';

type Dict = Record<string, unknown>;

type ContinueResult = {
  kind: 'continue';
  contract: unknown;
  meta: Dict | null;
  typedContract: Dict;
  contractViewType: string;
  preferredViewMode: string;
  activeContractFilterKey: string;
  activeSavedFilterKey: string;
  activeGroupByField: string;
  contractReadAllowed: boolean;
  contractWarningCount: number;
  contractDegraded: boolean;
  contractLimit: number;
  resolvedModel: string;
  setMetaModel: string;
  sortValue: string;
};

type BlockedResult = {
  kind: 'blocked';
  message: string;
  statusInput: string;
};

type UseActionViewLoadPreflightApplyBoundRuntimeOptions = {
  applyLoadPreflightContinueState: (input: Dict) => {
    contract: unknown;
    meta: Dict | null;
    typedContract: Dict;
    resolvedModel: string;
  };
  applyLoadPreflightBlockedState: (input: Dict) => void;
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
  setActionMeta: (payload: Dict) => void;
  setError: (error: Error, fallbackMessage?: string) => void;
  deriveListStatus: (input: string) => 'loading' | 'ok' | 'empty' | 'error';
  statusRef: Ref<'loading' | 'ok' | 'empty' | 'error'>;
};

export function useActionViewLoadPreflightApplyBoundRuntime(options: UseActionViewLoadPreflightApplyBoundRuntimeOptions) {
  function applyLoadPreflightContinue(result: ContinueResult) {
    return options.applyLoadPreflightContinueState({
      result,
      contractViewTypeRef: options.contractViewTypeRef,
      actionContractRef: options.actionContractRef,
      preferredViewModeRef: options.preferredViewModeRef,
      activeContractFilterKeyRef: options.activeContractFilterKeyRef,
      activeSavedFilterKeyRef: options.activeSavedFilterKeyRef,
      activeGroupByFieldRef: options.activeGroupByFieldRef,
      contractReadAllowedRef: options.contractReadAllowedRef,
      contractWarningCountRef: options.contractWarningCountRef,
      contractDegradedRef: options.contractDegradedRef,
      contractLimitRef: options.contractLimitRef,
      sortValueRef: options.sortValueRef,
      resolvedModelRef: options.resolvedModelRef,
      setActionMeta: options.setActionMeta,
    });
  }

  function applyLoadPreflightBlocked(result: BlockedResult): void {
    options.applyLoadPreflightBlockedState({
      result,
      setError: options.setError,
      deriveListStatus: options.deriveListStatus,
      statusRef: options.statusRef,
    });
  }

  return {
    applyLoadPreflightContinue,
    applyLoadPreflightBlocked,
  };
}

