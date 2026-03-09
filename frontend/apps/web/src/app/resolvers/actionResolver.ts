import type { NavMeta, NavNode } from '@sc/schema';
import { findActionMeta } from '../menu';
import { loadActionContract } from '../../api/contract';

export interface ActionResolution {
  meta: NavMeta;
  contract: Awaited<ReturnType<typeof loadActionContract>>;
}

export async function resolveAction(
  menuTree: NavNode[],
  actionId: number,
  currentAction?: NavMeta | null,
): Promise<ActionResolution> {
  const currentMatches = Boolean(currentAction && Number(currentAction.action_id || 0) === Number(actionId || 0));
  const metaFromMenu = findActionMeta(menuTree, actionId);
  // Always prefer menuTree meta to avoid stale/incomplete currentAction snapshots.
  const meta = metaFromMenu || (currentMatches ? currentAction : null);
  if (!meta) {
    throw new Error('action not found in menu tree');
  }
  const contract = await loadActionContract(actionId);
  return { meta, contract };
}
