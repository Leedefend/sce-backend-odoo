type ActionContractLoose = {
  data?: {
    type?: string;
    url?: string;
    target?: string;
  };
};

type UseActionViewActionMetaRuntimeOptions = {
  actionUnsupportedCode: string;
  configApiBaseUrl: string;
  menuId: { value: number | null };
  actionId: { value: number | null };
  buildWorkbenchRouteTarget: (input: { query: Record<string, unknown> }) => unknown;
  resolveWorkbenchQuery: (reason: string, payload?: { public?: Record<string, unknown>; diag?: Record<string, unknown> }) => Record<string, unknown>;
  buildPathRouteTarget: (path: string, query?: Record<string, unknown>) => unknown;
  resolveCarryQuery: (extra?: Record<string, unknown>) => Record<string, unknown>;
  resolveUrlUnsupportedRedirectState: (input: {
    actionUnsupportedCode: string;
    actionType: string;
    contractType: string;
    buildWorkbenchRouteTargetFn: (input: { query: Record<string, unknown> }) => unknown;
    resolveWorkbenchQueryFn: (reason: string, payload?: { public?: Record<string, unknown>; diag?: Record<string, unknown> }) => Record<string, unknown>;
  }) => { target: unknown };
  resolvePortalSelfRedirectState: (input: {
    menuId: number | null;
    actionId: number | null;
    buildPathRouteTargetFn: (path: string, query?: Record<string, unknown>) => unknown;
    resolveCarryQueryFn: (extra?: Record<string, unknown>) => Record<string, unknown>;
  }) => { target: unknown };
  routerReplace: (target: unknown) => Promise<unknown>;
  openWindow: (url: string, target: string) => void;
  assignLocation: (url: string) => void;
};

export function useActionViewActionMetaRuntime(options: UseActionViewActionMetaRuntimeOptions) {
  function getActionType(meta: unknown) {
    const raw = (meta as { type?: string; action_type?: string }) || {};
    return String(raw.type || raw.action_type || '').toLowerCase();
  }

  function isClientAction(meta: unknown) {
    const raw = meta as { tag?: string; type?: string; action_type?: string };
    const tag = String(raw?.tag || '').toLowerCase();
    const actionType = getActionType(meta);
    return actionType.includes('client') || tag.length > 0;
  }

  function isUrlAction(meta: unknown, contract: unknown) {
    const actionType = getActionType(meta);
    if (actionType.includes('act_url') || actionType.includes('url')) {
      return true;
    }
    const typed = contract as ActionContractLoose;
    const contractType = String(typed.data?.type || '').toLowerCase();
    return contractType === 'url_redirect';
  }

  function normalizeUrlTarget(target: unknown) {
    const raw = String(target || '').toLowerCase();
    if (raw === 'self' || raw === 'current' || raw === 'main') {
      return 'self';
    }
    return 'new';
  }

  function isShellRoute(url: string) {
    return (
      url === '/'
      || url.startsWith('/s/')
      || url.startsWith('/m/')
      || url.startsWith('/a/')
      || url.startsWith('/r/')
      || url.startsWith('/login')
      || url.startsWith('/admin/')
    );
  }

  function resolveNavigationUrl(url: string) {
    const raw = String(url || '').trim();
    if (!raw) {
      return '';
    }
    if (/^https?:\/\//i.test(raw)) {
      return raw;
    }
    if (!raw.startsWith('/')) {
      return raw;
    }
    try {
      return new URL(raw, options.configApiBaseUrl).toString();
    } catch {
      return raw;
    }
  }

  function isPortalPath(url: string) {
    return url.startsWith('/portal/');
  }

  function resolveActionUrl(meta: unknown, contract: unknown) {
    const metaTyped = (meta as { url?: string }) || {};
    const metaUrl = String(metaTyped.url || '').trim();
    if (metaUrl) {
      return metaUrl;
    }
    const typed = contract as ActionContractLoose;
    const contractUrl = String(typed.data?.url || '').trim();
    if (contractUrl) {
      return contractUrl;
    }
    return '';
  }

  async function redirectUrlAction(meta: unknown, contract: unknown) {
    const url = resolveActionUrl(meta, contract);
    if (!url) {
      const actionType = getActionType(meta);
      const typed = contract as ActionContractLoose;
      const contractType = String(typed.data?.type || '').toLowerCase();
      const unsupportedState = options.resolveUrlUnsupportedRedirectState({
        actionUnsupportedCode: options.actionUnsupportedCode,
        actionType,
        contractType,
        buildWorkbenchRouteTargetFn: options.buildWorkbenchRouteTarget,
        resolveWorkbenchQueryFn: options.resolveWorkbenchQuery,
      });
      await options.routerReplace(unsupportedState.target);
      return true;
    }

    const metaTyped = (meta as { target?: string }) || {};
    const typed = contract as ActionContractLoose;
    const target = normalizeUrlTarget(metaTyped.target || typed.data?.target);

    if (target === 'self' && isPortalPath(url)) {
      const portalSelfState = options.resolvePortalSelfRedirectState({
        menuId: options.menuId.value,
        actionId: options.actionId.value,
        buildPathRouteTargetFn: options.buildPathRouteTarget,
        resolveCarryQueryFn: options.resolveCarryQuery,
      });
      await options.routerReplace(portalSelfState.target);
      return true;
    }

    if (target === 'self' && url.startsWith('/')) {
      if (isShellRoute(url)) {
        await options.routerReplace(url);
      } else {
        options.assignLocation(resolveNavigationUrl(url));
      }
      return true;
    }

    const navUrl = resolveNavigationUrl(url);
    options.openWindow(navUrl, target === 'self' ? '_self' : '_blank');
    return true;
  }

  function isWindowAction(meta: unknown) {
    const actionType = getActionType(meta);
    return actionType.includes('act_window') || actionType.includes('window') || actionType === '';
  }

  return {
    getActionType,
    isClientAction,
    isUrlAction,
    normalizeUrlTarget,
    isShellRoute,
    resolveNavigationUrl,
    isPortalPath,
    resolveActionUrl,
    redirectUrlAction,
    isWindowAction,
  };
}
