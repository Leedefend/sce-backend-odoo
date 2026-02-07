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
  const shouldReuseCurrent = Boolean(currentAction && Number(currentAction.action_id || 0) === Number(actionId || 0));
  const meta = shouldReuseCurrent ? currentAction : findActionMeta(menuTree, actionId);
  if (!meta) {
    throw new Error('action not found in menu tree');
  }
  const contract = await loadActionContract(actionId);
  return { meta, contract };
}
