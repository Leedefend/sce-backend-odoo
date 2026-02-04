import type { NavMeta, NavNode } from '@sc/schema';
import { findMenuNode } from '../menu';

export type MenuResolveResult =
  | { kind: 'leaf'; meta: NavMeta; node: NavNode }
  | { kind: 'group'; node: NavNode }
  | { kind: 'broken'; node: NavNode | null; reason: string };

export function resolveMenuAction(menuTree: NavNode[], menuId: number): MenuResolveResult {
  const node = findMenuNode(menuTree, menuId);
  if (!node) {
    return { kind: 'broken', node: null, reason: 'menu not found' };
  }
  if (node.meta?.action_id) {
    return { kind: 'leaf', meta: node.meta, node };
  }
  if (node.children?.length) {
    return { kind: 'group', node };
  }
  return { kind: 'broken', node, reason: 'menu has no action' };
}
