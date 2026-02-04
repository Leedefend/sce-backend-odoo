export function resolveMenuActionCore(menuTree, menuId) {
  const node = findMenuNode(menuTree, menuId);
  if (!node) {
    return { kind: 'broken', node: null, reason: 'menu not found' };
  }
  if (node.meta && node.meta.action_id) {
    return { kind: 'leaf', meta: node.meta, node };
  }
  if (node.children && node.children.length) {
    return { kind: 'group', node };
  }
  return { kind: 'broken', node, reason: 'menu has no action' };
}

function findMenuNode(nodes, menuId) {
  if (!Array.isArray(nodes)) {
    return null;
  }
  for (const node of nodes) {
    if (node && (node.menu_id === menuId || node.id === menuId)) {
      return node;
    }
    if (node && Array.isArray(node.children) && node.children.length) {
      const found = findMenuNode(node.children, menuId);
      if (found) {
        return found;
      }
    }
  }
  return null;
}
