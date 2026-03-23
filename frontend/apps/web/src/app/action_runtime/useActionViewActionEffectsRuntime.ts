type Dict = Record<string, unknown>;

type UseActionViewActionEffectsRuntimeOptions = {
  load: () => Promise<void>;
  sessionLoadAppInit: () => Promise<void>;
  recordIntentTrace: (payload: { intent: string; writeMode: string; latencyMs?: number }) => void;
  resolveOpenNavigation: (input: { actionId?: number; url?: string }) => { kind: 'action' | 'url' | 'none'; actionId?: number; url: string };
  buildRouteTarget: (nextActionId: number) => unknown;
  routerPush: (target: unknown) => Promise<unknown>;
  resolveNavigationUrl: (url: string) => string;
  openWindow: (url: string, target: string) => void;
  pageText: (key: string, fallback: string) => string;
  resolveMissingOpenTargetMessage: (text: (key: string, fallback: string) => string) => string;
  executeProjectionRefresh: (options: {
    policy: Dict;
    refreshScene: () => Promise<void>;
    refreshWorkbench: () => Promise<void>;
    refreshRoleSurface: () => Promise<void>;
    recordTrace: (payload: { intent: string; writeMode: string; latencyMs?: number }) => void;
  }) => Promise<void>;
  resolveResponseActionId: (response: unknown) => number | null;
  shouldNavigate: (input: { nextActionId: number | null }) => boolean;
};

type OpenActionInput = {
  actionId?: number;
  url?: string;
  target?: string;
};

type OpenActionResult =
  | { handled: true }
  | { handled: false; message: string };

export function useActionViewActionEffectsRuntime(options: UseActionViewActionEffectsRuntimeOptions) {
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

  async function runOpenAction(input: OpenActionInput): Promise<OpenActionResult> {
    const openNavigation = options.resolveOpenNavigation({ actionId: input.actionId, url: input.url });
    if (openNavigation.kind === 'action' && openNavigation.actionId) {
      await options.routerPush(options.buildRouteTarget(openNavigation.actionId));
      return { handled: true };
    }
    if (openNavigation.kind === 'url') {
      const navUrl = options.resolveNavigationUrl(openNavigation.url);
      options.openWindow(navUrl, input.target === 'self' ? '_self' : '_blank');
      return { handled: true };
    }
    return {
      handled: false,
      message: options.resolveMissingOpenTargetMessage(options.pageText),
    };
  }

  async function navigateByResponse(response: unknown): Promise<boolean> {
    const nextActionId = options.resolveResponseActionId(response);
    if (!options.shouldNavigate({ nextActionId })) {
      return false;
    }
    await options.routerPush(options.buildRouteTarget(Number(nextActionId || 0)));
    return true;
  }

  return {
    applyActionRefreshPolicy,
    runOpenAction,
    navigateByResponse,
  };
}
