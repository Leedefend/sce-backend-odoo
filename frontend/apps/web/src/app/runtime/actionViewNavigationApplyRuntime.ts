type Dict = Record<string, unknown>;

type WorkbenchTargetBuilder = (query: Dict) => unknown;
type WorkbenchQueryResolver = (code: string, payload: Dict) => Dict;
type PathTargetBuilder = (path: string, query: Dict) => unknown;

export function resolveReplaceCurrentRouteState(options: {
  routePath: string;
  query: Dict;
}): {
  target: { path: string; query: Dict };
} {
  return {
    target: {
      path: options.routePath,
      query: options.query,
    },
  };
}

export function resolveFocusActionPushState(options: {
  action: { to: string; query?: Dict } | string;
  workspaceContextQuery: Dict;
}): {
  target: { path: string; query?: Dict };
} {
  const path = typeof options.action === 'string' ? options.action : options.action.to;
  const query = typeof options.action === 'string' ? undefined : options.action.query;
  return {
    target: {
      path,
      query: query ? { ...options.workspaceContextQuery, ...query } : undefined,
    },
  };
}

export function resolveRowClickPushState(options: {
  routeTarget: unknown;
}): {
  shouldNavigate: boolean;
  target: unknown;
} {
  return {
    shouldNavigate: Boolean(options.routeTarget),
    target: options.routeTarget,
  };
}

export function resolveUrlUnsupportedRedirectState(options: {
  actionUnsupportedCode: string;
  actionType: string;
  contractType: string;
  buildWorkbenchRouteTargetFn: WorkbenchTargetBuilder;
  resolveWorkbenchQueryFn: WorkbenchQueryResolver;
}): {
  target: unknown;
} {
  const payload = {
    diag: {
      diag: 'act_url_empty',
      diag_action_type: options.actionType || undefined,
      diag_contract_type: options.contractType || undefined,
    },
  };
  return {
    target: options.buildWorkbenchRouteTargetFn(
      options.resolveWorkbenchQueryFn(options.actionUnsupportedCode, payload),
    ),
  };
}

export function resolvePortalSelfRedirectState(options: {
  menuId: number;
  actionId: number;
  url?: string;
  buildPathRouteTargetFn: PathTargetBuilder;
  resolveCarryQueryFn: (extra?: Dict) => Dict;
}): {
  target: unknown;
} {
  const normalizedUrl = String(options.url || '').trim().toLowerCase();
  let path = '/';
  if (normalizedUrl === '/portal/capability-matrix') {
    path = '/s/portal.capability_matrix';
  }
  return {
    target: options.buildPathRouteTargetFn(
      path,
      options.resolveCarryQueryFn({
        menu_id: options.menuId || undefined,
        action_id: options.actionId || undefined,
      }),
    ),
  };
}
