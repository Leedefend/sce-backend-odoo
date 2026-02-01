import type { NavMeta, NavNode } from '@sc/schema';
import { findMenuNode } from '../menu';

export function resolveMenuAction(menuTree: NavNode[], menuId: number): NavMeta {
  const node = findMenuNode(menuTree, menuId);
  if (!node?.meta?.action_id) {
    throw new Error('menu has no action');
  }
  return node.meta;
}
