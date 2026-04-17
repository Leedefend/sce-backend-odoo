import type { Ref } from 'vue';
import type { LocationQueryRaw } from 'vue-router';
import type { ContractActionDeps } from '../pageContractActionRuntime';

type UseActionViewHeaderRuntimeOptions = {
  batchMessage: Ref<string>;
  pageText: (key: string, fallback: string) => string;
  syncRouteListState: (extra?: Record<string, unknown>) => void;
  load: () => Promise<void>;
  resolveReloadTriggerPlan: () => { shouldSyncRoute: boolean; shouldLoad: boolean };
  resolveFocusActionPushState: (input: { action: unknown; workspaceContextQuery: Record<string, unknown> }) => { target: unknown };
  resolveWorkspaceContextQuery: () => Record<string, unknown>;
  routerPush: (target: unknown) => Promise<unknown>;
  executePageContractAction: (input: ContractActionDeps) => Promise<boolean>;
  router: ContractActionDeps['router'];
  pageActionIntent: (key: string, fallback?: string) => string;
  pageActionTarget: (key: string) => Record<string, unknown>;
  isHeaderActionDisabled?: (actionKey: string) => boolean;
  onHeaderActionBlocked?: (actionKey: string) => void;
};

export function useActionViewHeaderRuntime(options: UseActionViewHeaderRuntimeOptions) {
  function reload() {
    const triggerPlan = options.resolveReloadTriggerPlan();
    if (triggerPlan.shouldSyncRoute) options.syncRouteListState();
    if (triggerPlan.shouldLoad) void options.load();
  }

  function openFocusAction(action: unknown) {
    const pushState = options.resolveFocusActionPushState({
      action,
      workspaceContextQuery: options.resolveWorkspaceContextQuery(),
    });
    options.routerPush(pushState.target).catch(() => {});
  }

  async function executeHeaderAction(actionKey: string) {
    if (options.isHeaderActionDisabled?.(actionKey)) {
      options.onHeaderActionBlocked?.(actionKey);
      return;
    }
    const handled = await options.executePageContractAction({
      actionKey,
      router: options.router,
      actionIntent: options.pageActionIntent,
      actionTarget: options.pageActionTarget,
      query: options.resolveWorkspaceContextQuery() as LocationQueryRaw,
      onRefresh: reload,
      onFallback: async (key) => {
        if (key === 'open_my_work') {
          openFocusAction('/my-work');
          return true;
        }
        if (key === 'open_risk_dashboard') {
          openFocusAction('/s/projects.dashboard');
          return true;
        }
        if (key === 'open_workbench' || key === 'open_landing') {
          openFocusAction('/my-work');
          return true;
        }
        if (key === 'refresh_page' || key === 'refresh') {
          reload();
          return true;
        }
        return false;
      },
    });
    if (!handled) {
      options.batchMessage.value = options.pageText('error_fallback', '操作暂不可用');
    }
  }

  return {
    reload,
    openFocusAction,
    executeHeaderAction,
  };
}
