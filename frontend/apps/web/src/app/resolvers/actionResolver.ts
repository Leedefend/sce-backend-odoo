import type { NavMeta, NavNode } from '@sc/schema';
import { findActionMeta } from '../menu';
import { loadActionContract } from '../../api/contract';

export interface ActionResolution {
  meta: NavMeta;
  contract: Awaited<ReturnType<typeof loadActionContract>>;
}

function splitViewModes(raw: unknown): string[] {
  if (Array.isArray(raw)) {
    return raw
      .map((item) => String(item || '').trim().toLowerCase())
      .filter(Boolean);
  }
  return String(raw || '')
    .split(',')
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

function collectViewModesFromViewsBlock(raw: unknown): string[] {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    return [];
  }
  const views = raw as Record<string, unknown>;
  const supported = ['tree', 'list', 'kanban', 'pivot', 'graph', 'calendar', 'gantt', 'activity', 'dashboard'];
  const out: string[] = [];
  const seen = new Set<string>();
  supported.forEach((key) => {
    const block = views[key];
    if (!block) return;
    const normalized = key === 'list' ? 'tree' : key;
    if (seen.has(normalized)) return;
    seen.add(normalized);
    out.push(normalized);
  });
  return out;
}

function resolveNestedContract(contract: unknown): Record<string, unknown> {
  if (!contract || typeof contract !== 'object' || Array.isArray(contract)) return {};
  const row = contract as Record<string, unknown>;
  const nested = row.ui_contract;
  if (nested && typeof nested === 'object' && !Array.isArray(nested)) {
    return nested as Record<string, unknown>;
  }
  return row;
}

function resolveMetaFromContract(contract: unknown, actionId: number): NavMeta {
  const normalized = resolveNestedContract(contract);
  const head = (normalized.head && typeof normalized.head === 'object' && !Array.isArray(normalized.head))
    ? (normalized.head as Record<string, unknown>)
    : {};
  const views = (normalized.views && typeof normalized.views === 'object' && !Array.isArray(normalized.views))
    ? (normalized.views as Record<string, unknown>)
    : {};
  const treeView = (views.tree && typeof views.tree === 'object' && !Array.isArray(views.tree))
    ? (views.tree as Record<string, unknown>)
    : {};
  const formView = (views.form && typeof views.form === 'object' && !Array.isArray(views.form))
    ? (views.form as Record<string, unknown>)
    : {};
  const kanbanView = (views.kanban && typeof views.kanban === 'object' && !Array.isArray(views.kanban))
    ? (views.kanban as Record<string, unknown>)
    : {};
  const model = String(
    head.model
      || normalized.model
      || treeView.model
      || formView.model
      || kanbanView.model
      || '',
  ).trim();
  const viewModes = splitViewModes(head.view_type || normalized.view_type || '');
  const derivedViewModes = viewModes.length ? viewModes : collectViewModesFromViewsBlock(views);
  const name = String(head.title || normalized.name || '').trim();
  const actionType = String(normalized.action_type || head.action_type || 'ir.actions.act_window').trim();
  const out: NavMeta = {
    action_id: Number(actionId || 0),
    action_type: actionType || 'ir.actions.act_window',
  };
  if (head.domain !== undefined) {
    out.domain = head.domain as unknown as string;
  }
  if (head.context !== undefined) {
    out.context = head.context as unknown as string;
  }
  if (head.order !== undefined) {
    (out as Record<string, unknown>).order = String(head.order || '');
  }
  if (model) out.model = model;
  if (name) out.name = name;
  if (derivedViewModes.length) {
    out.view_modes = derivedViewModes;
    out.views = derivedViewModes.map((mode) => [0, mode]) as Array<[number, string]>;
  }
  return out;
}

function mergeMeta(base: NavMeta | null, fallback: NavMeta): NavMeta {
  const merged: NavMeta = { ...(base || {}), ...fallback };
  // Preserve authoritative fields from existing meta when present.
  if (base?.action_type) merged.action_type = base.action_type;
  if (base?.menu_id) merged.menu_id = base.menu_id;
  if (base?.menu_xmlid) merged.menu_xmlid = base.menu_xmlid;
  if (base?.groups_xmlids?.length) merged.groups_xmlids = base.groups_xmlids;
  if (base?.model) merged.model = base.model;
  const baseModes = splitViewModes(base?.view_modes || []);
  if (baseModes.length) {
    merged.view_modes = baseModes;
  } else if (fallback.view_modes?.length) {
    merged.view_modes = fallback.view_modes;
  }
  if (Array.isArray(base?.views) && base.views.length) {
    merged.views = base.views;
  } else if (Array.isArray(fallback.views) && fallback.views.length) {
    merged.views = fallback.views;
  }
  return merged;
}

export async function resolveAction(
  menuTree: NavNode[],
  actionId: number,
  currentAction?: NavMeta | null,
): Promise<ActionResolution> {
  const contract = await loadActionContract(actionId);
  const currentMatches = Boolean(currentAction && Number(currentAction.action_id || 0) === Number(actionId || 0));
  const metaFromMenu = findActionMeta(menuTree, actionId);
  // Always prefer menuTree meta to avoid stale/incomplete currentAction snapshots.
  const seedMeta = metaFromMenu || (currentMatches ? currentAction : null);
  const fallbackMeta = resolveMetaFromContract(contract, actionId);
  const meta = mergeMeta(seedMeta, fallbackMeta);
  if (!meta.action_id) {
    meta.action_id = Number(actionId || 0);
  }
  return { meta, contract };
}
