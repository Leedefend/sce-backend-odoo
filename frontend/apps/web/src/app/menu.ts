import type { NavMeta, NavNode } from '@sc/schema';

export function findMenuNode(nodes: NavNode[], menuId: number): NavNode | null {
  for (const node of nodes) {
    if (node.menu_id === menuId) {
      return node;
    }
    if (node.children?.length) {
      const found = findMenuNode(node.children, menuId);
      if (found) {
        return found;
      }
    }
  }
  return null;
}

export function findActionMeta(nodes: NavNode[], actionId: number): NavMeta | null {
  for (const node of nodes) {
    if (node.meta?.action_id === actionId) {
      return node.meta;
    }
    if (node.children?.length) {
      const found = findActionMeta(node.children, actionId);
      if (found) {
        return found;
      }
    }
  }
  return null;
}

export function resolveMenu(nodes: NavNode[], menuId: number): NavMeta {
  const node = findMenuNode(nodes, menuId);
  if (!node?.meta?.action_id) {
    throw new Error('menu has no action');
  }
  return node.meta;
}
