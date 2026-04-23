type ActionContractMetaShape = {
  head?: {
    view_type?: string;
    res_id?: number | string;
    context?: unknown;
  };
  ui_contract?: {
    head?: { view_type?: string };
    view_type?: string;
  };
  view_type?: string;
};

export function resolveActionViewType(meta: unknown, contract: unknown): string {
  const typedContract = contract as ActionContractMetaShape;
  const nestedContract = (typedContract.ui_contract || {}) as ActionContractMetaShape;
  const fromHead = String(typedContract.head?.view_type || nestedContract.head?.view_type || '').trim();
  if (fromHead) return fromHead;
  const fromContract = String(typedContract.view_type || nestedContract.view_type || '').trim();
  if (fromContract) return fromContract;
  const metaViewModes = (meta as { view_modes?: unknown } | null)?.view_modes;
  if (Array.isArray(metaViewModes) && metaViewModes.length) {
    const normalized = metaViewModes
      .map((item) => String(item || '').trim())
      .filter(Boolean)
      .join(',');
    if (normalized) return normalized;
  }
  return '';
}

export function parseNumericId(raw: unknown): number | null {
  if (typeof raw === 'number' && Number.isFinite(raw) && raw > 0) return raw;
  if (typeof raw === 'string' && raw.trim()) {
    const parsed = Number(raw.trim());
    if (Number.isFinite(parsed) && parsed > 0) return parsed;
  }
  return null;
}

export function extractActionResId(contract: unknown, routeQuery: Record<string, unknown>): number | null {
  const typed = contract as ActionContractMetaShape;
  const routeResId = parseNumericId(routeQuery.res_id);
  if (routeResId) return routeResId;
  const headResId = parseNumericId(typed.head?.res_id);
  if (headResId) return headResId;
  const headContext = typed.head?.context;
  if (headContext && typeof headContext === 'object' && !Array.isArray(headContext)) {
    const ctx = headContext as Record<string, unknown>;
    const activeId = parseNumericId(ctx.active_id);
    if (activeId) return activeId;
    const defaultResId = parseNumericId(ctx.default_res_id);
    if (defaultResId) return defaultResId;
  }
  return null;
}
