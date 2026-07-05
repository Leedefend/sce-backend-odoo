/* eslint-disable @typescript-eslint/no-explicit-any */
import type { Ref } from 'vue';
import type { LocationQueryRaw, Router } from 'vue-router';

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
    router: Router;
    actionIntent: (key: string, fallback?: string) => string;
    actionTarget: (key: string) => Record<string, unknown>;
    query: LocationQueryRaw;
    onRefresh: () => void;
    onFallback: (key: string) => Promise<boolean>;
  }) => Promise<boolean>;
  router: Router;
  pageActionIntent: (key: string, fallback?: string) => string;
  pageActionTarget: (key: string) => Record<string, unknown>;
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
          openFocusAction({ to: '/my-work', query: { section: 'todo', search: '风险' } });
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
