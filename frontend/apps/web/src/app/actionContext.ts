import type { NavMeta, NavNode } from '@sc/schema';

type ResolveActionContextInput = {
  routeQuery: Record<string, unknown>;
  currentActionId?: number | null;
  currentActionModel?: string;
  menuTree: NavNode[];
  model: string;
  preferredMode?: 'form' | 'tree' | 'kanban' | '';
};

export function resolveActionIdFromContext(input: ResolveActionContextInput): number | null {
  const {
    routeQuery,
    currentActionId,
    currentActionModel,
    menuTree,
    model,
    preferredMode = '',
  } = input;
  const fromQuery = toPositiveInt(routeQuery.action_id);
  if (fromQuery) return fromQuery;
  const fromCurrent = toPositiveInt(currentActionId);
  if (fromCurrent) {
    const normalizedCurrentModel = String(currentActionModel || '').trim();
    if (!normalizedCurrentModel || normalizedCurrentModel === model) {
      return fromCurrent;
    }
  }
  return findActionIdByModel(menuTree, model, preferredMode);
}

export function findActionIdByModel(
  nodes: NavNode[],
  targetModel: string,
  _preferredMode: 'form' | 'tree' | 'kanban' | '' = '',
): number | null {
  if (!targetModel) return null;
  const stack = [...nodes];
  while (stack.length) {
    const node = stack.shift();
    if (!node) continue;
    const meta = (node.meta || {}) as NavMeta;
    const modelName = String(meta.model || '').trim();
    const actionId = toPositiveInt(meta.action_id);
    if (modelName === targetModel && actionId) {
      return actionId;
    }
    if (Array.isArray(node.children) && node.children.length) {
      stack.push(...node.children);
    }
  }
  return null;
}

function toPositiveInt(raw: unknown): number | null {
  const parsed = Number(raw || 0);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}
