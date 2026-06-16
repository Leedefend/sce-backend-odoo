type ResolveActionContextInput = {
  routeQuery: Record<string, unknown>;
  menuActionId?: number | null;
  menuActionModel?: string;
  currentActionId?: number | null;
  currentActionModel?: string;
  model: string;
};

export function resolveActionIdFromContext(input: ResolveActionContextInput): number | null {
  const {
    routeQuery,
    menuActionId,
    menuActionModel,
    currentActionId,
    currentActionModel,
    model,
  } = input;
  const fromQuery = toPositiveInt(routeQuery.action_id);
  if (fromQuery) return fromQuery;
  const fromMenu = toPositiveInt(menuActionId);
  if (fromMenu) {
    const normalizedMenuModel = String(menuActionModel || '').trim();
    if (!normalizedMenuModel || normalizedMenuModel === model) {
      return fromMenu;
    }
  }
  const fromCurrent = toPositiveInt(currentActionId);
  if (fromCurrent) {
    const normalizedCurrentModel = String(currentActionModel || '').trim();
    if (!normalizedCurrentModel || normalizedCurrentModel === model) {
      return fromCurrent;
    }
  }
  return null;
}

function toPositiveInt(raw: unknown): number | null {
  const parsed = Number(raw || 0);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}
