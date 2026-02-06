export function resolveMenuActionCore(menuTree, menuId) {
  const node = findMenuNode(menuTree, menuId);
  if (!node) {
    return { kind: 'broken', node: null, reason: 'menu not found' };
  }
  const ownMenuId = node.menu_id || node.id;
  if (node.meta && node.meta.action_id) {
    return { kind: 'leaf', meta: node.meta, node };
  }
  const ownSceneKey = node.scene_key || node.sceneKey || node.meta?.scene_key;
  if (ownSceneKey && ownMenuId) {
    return {
      kind: 'redirect',
      node,
      target: {
        menu_id: ownMenuId,
        scene_key: ownSceneKey,
        node,
      },
    };
  }
  if (node.children && node.children.length) {
    const target = findFirstResolvableTarget(node.children);
    if (target) {
      return { kind: 'redirect', node, target };
    }
    return { kind: 'group', node };
  }
  return { kind: 'broken', node, reason: 'menu has no action' };
}

function findFirstResolvableTarget(nodes) {
  if (!Array.isArray(nodes)) {
    return null;
  }
  for (const node of nodes) {
    if (!node) {
      continue;
    }
    const menuId = node.menu_id || node.id;
    if (!menuId) {
      continue;
    }
    if (node.meta && node.meta.action_id) {
      return {
        menu_id: menuId,
        action_id: node.meta.action_id,
        meta: node.meta,
        node,
      };
    }
    const sceneKey = node.scene_key || node.sceneKey || node.meta?.scene_key;
    if (sceneKey) {
      return {
        menu_id: menuId,
        scene_key: sceneKey,
        node,
      };
    }
    if (Array.isArray(node.children) && node.children.length) {
      const nested = findFirstResolvableTarget(node.children);
      if (nested) {
        return nested;
      }
    }
  }
  return null;
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
