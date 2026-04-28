import type { Ref } from 'vue';

type Dict = Record<string, unknown>;

type ContractActionSelection = 'none' | 'single' | 'multi';

type MutationPayload = {
  payload_schema?: {
    required?: string[];
  };
  type?: string;
  model?: string;
  operation?: string;
  [key: string]: unknown;
};

type ContractActionButtonLike = {
  key: string;
  label?: string;
  enabled?: boolean;
  kind?: string;
  actionId?: number;
  url?: string;
  target?: string;
  mutation?: MutationPayload;
  model?: string;
  context?: Dict;
  methodName?: string;
  selection?: ContractActionSelection;
  refreshPolicy?: Dict;
};

type UseActionViewActionRuntimeOptions = {
  selectedIds: Ref<number[]>;
  batchBusy: Ref<boolean>;
  batchMessage: Ref<string>;
  pageText: (key: string, fallback: string) => string;
  load: () => Promise<void>;
  sessionLoadAppInit: () => Promise<void>;
  recordIntentTrace: (payload: { intent: string; writeMode: string; latencyMs?: number }) => void;
  resolveActionContextRecordId: () => number | null;
  resolveOpenNavigation: (input: { actionId?: number; url?: string }) => { kind: 'action' | 'url' | 'none'; actionId?: number; url: string };
  buildRouteTarget: (nextActionId: number) => unknown;
  routerPush: (target: unknown) => Promise<unknown>;
  resolveNavigationUrl: (url: string) => string;
  openWindow: (url: string, target: string) => void;
  resolveMissingOpenTargetMessage: (text: (key: string, fallback: string) => string) => string;
  resolveExecIds: (input: { selectedIds: number[]; contextRecordId: number | null }) => number[];
  resolveRunIds: (ids: number[]) => number[];
  resolveCounters: (input: { successCount: number; failureCount: number; ok: boolean }) => { successCount: number; failureCount: number };
  resolveDoneMessage: (input: { successCount: number; failureCount: number; text: (key: string, fallback: string) => string }) => string;
  resolveRequiresRecordContextMessage: (text: (key: string, fallback: string) => string) => string;
  resolveSelectionBlockMessage: (input: { selection: ContractActionSelection; selectedCount: number; text: (key: string, fallback: string) => string }) => string;
  resolveMissingModelMessage: (text: (key: string, fallback: string) => string) => string;
  executeProjectionRefresh: (options: any) => Promise<void>;
  executeSceneMutation: (options: any) => Promise<unknown>;
  executeButton: (payload: any) => Promise<unknown>;
  buildButtonRequest: (input: {
    model: string;
    recordId: number;
    methodName?: string;
    actionKey: string;
    kind: string;
    context?: Dict;
  }) => Dict;
  resolveResponseActionId: (response: unknown) => number | null;
  shouldNavigate: (input: { nextActionId: number | null }) => boolean;
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
  const modelName = String(action.mutation?.model || action.model || '').trim().toLowerCase();
  if (modelName === 'project.risk.action' && !context.risk_action_id) {
    context.risk_action_id = recordId;
  }
  if ((modelName === 'finance.payment.request' || modelName === 'payment.request') && !context.id) {
    context.id = recordId;
  }
  return context;
}

export function useActionViewActionRuntime(options: UseActionViewActionRuntimeOptions) {
  async function applyActionRefreshPolicy(policy?: Dict) {
    if (!policy || !Array.isArray(policy.on_success) || !policy.on_success.length) {
      await options.load();
      return;
    }
    await options.executeProjectionRefresh({
      policy,
      refreshScene: async () => {
        await options.load();
      },
      refreshWorkbench: async () => {
        await options.sessionLoadAppInit();
      },
      refreshRoleSurface: async () => {
        await options.sessionLoadAppInit();
      },
      recordTrace: ({ intent, writeMode, latencyMs }) => {
        options.recordIntentTrace({ intent, writeMode, latencyMs });
      },
    });
  }

  async function runContractAction(action: ContractActionButtonLike) {
    if (action.enabled === false) return;
    const kind = String(action.kind || '').trim();
    const selection = action.selection || 'none';
    if (kind === 'open') {
      const openNavigation = options.resolveOpenNavigation({ actionId: action.actionId, url: action.url });
      if (openNavigation.kind === 'action' && openNavigation.actionId) {
        await options.routerPush(options.buildRouteTarget(openNavigation.actionId));
        return;
      }
      if (openNavigation.kind === 'url') {
        const navUrl = options.resolveNavigationUrl(openNavigation.url);
        options.openWindow(navUrl, action.target === 'self' ? '_self' : '_blank');
        return;
      }
      options.batchMessage.value = options.resolveMissingOpenTargetMessage(options.pageText);
      return;
    }

    if (action.mutation) {
      const ids = resolveSelectedIdsForAction(selection, options.selectedIds.value);
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
          await applyActionRefreshPolicy(action.refreshPolicy);
        }
      } finally {
        options.batchBusy.value = false;
      }
      return;
    }

    const ids = resolveSelectedIdsForAction(selection, options.selectedIds.value);
    const selectionMessage = options.resolveSelectionBlockMessage({
      selection,
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
            kind,
            context: action.context,
          }));
          const nextActionId = options.resolveResponseActionId(response);
          if (options.shouldNavigate({ nextActionId })) {
            await options.routerPush(options.buildRouteTarget(Number(nextActionId || 0)));
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
    applyActionRefreshPolicy,
    runContractAction,
  };
}
