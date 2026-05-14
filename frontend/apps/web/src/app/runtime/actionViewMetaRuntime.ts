import { resolveUnifiedPageContractV2 } from '../contracts/unifiedPageContractV2';

type ActionContractMetaShape = {
  head?: {
    view_type?: string;
    res_id?: number | string;
    context?: unknown;
  };
  view_type?: string;
};

function resolveFirstRenderableViewMode(value: unknown): string {
  const rawModes = Array.isArray(value)
    ? value
    : String(value || '').split(',');
  const modes = rawModes
    .map((item) => String(item || '').trim())
    .filter(Boolean);
  const supported = new Set(['tree', 'list', 'kanban', 'form']);
  return modes.find((mode) => supported.has(mode)) || modes[0] || '';
}

export function resolveActionViewType(meta: unknown, contract: unknown): string {
  const metaViewModes = (meta as { view_modes?: unknown } | null)?.view_modes;
  const normalizedMetaViewMode = resolveFirstRenderableViewMode(metaViewModes);
  const v2 = resolveUnifiedPageContractV2(contract);
  const v2ViewType = String(v2?.pageInfo?.viewType || '').trim();
  if (v2ViewType) {
    const normalizedV2ViewType = v2ViewType === 'list' ? 'tree' : v2ViewType;
    return normalizedV2ViewType;
  }
  const typedContract = contract as ActionContractMetaShape;
  const fromHead = String(typedContract.head?.view_type || '').trim();
  if (fromHead) return fromHead;
  const fromContract = String(typedContract.view_type || '').trim();
  if (fromContract) return fromContract;
  if (normalizedMetaViewMode) return normalizedMetaViewMode;
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
