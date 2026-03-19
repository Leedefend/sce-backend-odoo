import type { Ref } from 'vue';

type UseActionViewHeaderRuntimeOptions = {
  batchMessage: Ref<string>;
  pageText: (key: string, fallback: string) => string;
  syncRouteListState: (extra?: Record<string, unknown>) => void;
  load: () => Promise<void>;
  resolveReloadTriggerPlan: () => { shouldSyncRoute: boolean; shouldLoad: boolean };
  resolveFocusActionPushState: (input: { action: unknown; workspaceContextQuery: Record<string, unknown> }) => { target: unknown };
  resolveWorkspaceContextQuery: () => Record<string, unknown>;
  routerPush: (target: unknown) => Promise<unknown>;
  executePageContractAction: (input: {
    actionKey: string;
    router: unknown;
    actionIntent: unknown;
    actionTarget: unknown;
    query: Record<string, unknown>;
    onRefresh: () => void;
    onFallback: (key: string) => Promise<boolean>;
  }) => Promise<boolean>;
  router: unknown;
  pageActionIntent: Ref<unknown>;
  pageActionTarget: Ref<unknown>;
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
    const handled = await options.executePageContractAction({
      actionKey,
      router: options.router,
      actionIntent: options.pageActionIntent.value,
      actionTarget: options.pageActionTarget.value,
      query: options.resolveWorkspaceContextQuery(),
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
