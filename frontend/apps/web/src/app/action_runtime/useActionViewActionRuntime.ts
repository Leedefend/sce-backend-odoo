import type { Ref } from 'vue';
import type { ExecuteButtonRequest } from '@sc/schema';
import type { MutationContract } from '../sceneActionProtocol';

type Dict = Record<string, unknown>;

type ContractActionSelection = 'none' | 'single' | 'multi';

type MutationPayload = MutationContract;

type ContractActionButtonLike = {
  key: string;
  label?: string;
  enabled: boolean;
  kind: string;
  actionId?: number;
  url?: string;
  target?: string;
  mutation?: MutationPayload;
  model?: string;
  context?: Dict;
  methodName?: string;
  selection: ContractActionSelection;
  refreshPolicy?: Dict;
};

type UseActionViewActionRuntimeOptions = {
  selectedIds: Ref<number[]>;
  batchBusy: Ref<boolean>;
  batchMessage: Ref<string>;
  pageText: (key: string, fallback: string) => string;
  load: () => Promise<void>;
  resolveActionContextRecordId: () => number | null;
  resolveExecIds: (input: { selectedIds: number[]; contextRecordId: number | null }) => number[];
  resolveRunIds: (ids: number[]) => number[];
  resolveCounters: (input: { successCount: number; failureCount: number; ok: boolean }) => { successCount: number; failureCount: number };
  resolveDoneMessage: (input: { successCount: number; failureCount: number; text: (key: string, fallback: string) => string }) => string;
  resolveRequiresRecordContextMessage: (text: (key: string, fallback: string) => string) => string;
  resolveSelectionBlockMessage: (input: { selection: ContractActionSelection; selectedCount: number; text: (key: string, fallback: string) => string }) => string;
  resolveMissingModelMessage: (text: (key: string, fallback: string) => string) => string;
  applyActionRefreshPolicy: (policy?: Dict) => Promise<void>;
  runOpenAction: (input: { actionId?: number; url?: string; target?: string }) => Promise<{ handled: boolean; message?: string }>;
  executeSceneMutation: (options: {
    mutation: MutationPayload;
    actionKey: string;
    recordId: number | null;
    model?: string;
    context: Dict;
  }) => Promise<unknown>;
  executeButton: (payload: ExecuteButtonRequest) => Promise<unknown>;
  buildButtonRequest: (input: {
    model: string;
    recordId: number;
    methodName?: string;
    actionKey: string;
    kind: string;
    context?: Dict;
  }) => ExecuteButtonRequest;
  navigateByResponse: (response: unknown) => Promise<boolean>;
};

function resolveSelectedIdsForAction(selection: ContractActionSelection, selectedIds: number[]) {
  if (selection === 'none') return [];
  if (selection === 'single') {
    return selectedIds.length === 1 ? [selectedIds[0]] : [];
  }
  return selectedIds.length ? [...selectedIds] : [];
}

function mutationRequiresRecordContext(action: ContractActionButtonLike) {
  const required = Array.isArray(action.mutation?.payload_schema?.required)
    ? action.mutation?.payload_schema?.required
    : [];
  const requiredKeys = required.map((item) => String(item || '').trim().toLowerCase());
  return requiredKeys.includes('record_id')
    || requiredKeys.includes('id')
    || requiredKeys.includes('risk_action_id');
}

function buildMutationContext(action: ContractActionButtonLike, recordId: number) {
  const context = { ...(action.context || {}) } as Dict;
  const required = Array.isArray(action.mutation?.payload_schema?.required)
    ? action.mutation?.payload_schema?.required
    : [];
  const requiredKeys = required.map((item) => String(item || '').trim().toLowerCase()).filter(Boolean);
  const idLikeKey = requiredKeys.find((item) => item === 'id' || item === 'record_id' || item.endsWith('_id')) || 'id';
  if (recordId > 0 && !context[idLikeKey]) {
    context[idLikeKey] = recordId;
  }
  return context;
}

export function useActionViewActionRuntime(options: UseActionViewActionRuntimeOptions) {
  async function runContractAction(action: ContractActionButtonLike) {
    if (!action.enabled) return;
    if (action.kind === 'open') {
      const openActionResult = await options.runOpenAction({
        actionId: action.actionId,
        url: action.url,
        target: action.target,
      });
      if (openActionResult.handled) {
        return;
      }
      options.batchMessage.value = openActionResult.message || '';
      return;
    }

    if (action.mutation) {
      const ids = resolveSelectedIdsForAction(action.selection, options.selectedIds.value);
      const contextRecordId = options.resolveActionContextRecordId();
      const execIds = options.resolveExecIds({ selectedIds: ids, contextRecordId });
      if (!execIds.length && mutationRequiresRecordContext(action)) {
        options.batchMessage.value = options.resolveRequiresRecordContextMessage(options.pageText);
        return;
      }

      options.batchBusy.value = true;
      try {
        let successCount = 0;
        let failureCount = 0;
        const runIds = options.resolveRunIds(execIds);
        for (const id of runIds) {
          try {
            await options.executeSceneMutation({
              mutation: action.mutation,
              actionKey: action.key,
              recordId: id > 0 ? id : null,
              model: action.model,
              context: buildMutationContext(action, id),
            });
            ({ successCount, failureCount } = options.resolveCounters({
              successCount,
              failureCount,
              ok: true,
            }));
          } catch {
            ({ successCount, failureCount } = options.resolveCounters({
              successCount,
              failureCount,
              ok: false,
            }));
          }
        }
        options.batchMessage.value = options.resolveDoneMessage({ successCount, failureCount, text: options.pageText });
        if (successCount > 0) {
          await options.applyActionRefreshPolicy(action.refreshPolicy);
        }
      } finally {
        options.batchBusy.value = false;
      }
      return;
    }

    const ids = resolveSelectedIdsForAction(action.selection, options.selectedIds.value);
    const selectionMessage = options.resolveSelectionBlockMessage({
      selection: action.selection,
      selectedCount: ids.length,
      text: options.pageText,
    });
    if (selectionMessage) {
      options.batchMessage.value = selectionMessage;
      return;
    }
    if (!action.model) {
      options.batchMessage.value = options.resolveMissingModelMessage(options.pageText);
      return;
    }
    const contextRecordId = options.resolveActionContextRecordId();
    const execIds = options.resolveExecIds({ selectedIds: ids, contextRecordId });
    if (!execIds.length) {
      options.batchMessage.value = options.resolveRequiresRecordContextMessage(options.pageText);
      return;
    }

    options.batchBusy.value = true;
    try {
      let successCount = 0;
      let failureCount = 0;
        for (const id of execIds) {
          try {
            const response = await options.executeButton(options.buildButtonRequest({
            model: action.model,
            recordId: id,
            methodName: action.methodName,
            actionKey: action.key,
              kind: action.kind,
              context: action.context,
            }));
          if (await options.navigateByResponse(response)) {
            return;
          }
          ({ successCount, failureCount } = options.resolveCounters({
            successCount,
            failureCount,
            ok: true,
          }));
        } catch {
          ({ successCount, failureCount } = options.resolveCounters({
            successCount,
            failureCount,
            ok: false,
          }));
        }
      }
      options.batchMessage.value = options.resolveDoneMessage({ successCount, failureCount, text: options.pageText });
      if (successCount > 0) {
        await options.load();
      }
    } finally {
      options.batchBusy.value = false;
    }
  }

  return {
    runContractAction,
  };
}
