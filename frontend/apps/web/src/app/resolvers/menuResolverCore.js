export function resolveMenuActionCore(menuTree, menuId) {
  const node = findMenuNode(menuTree, menuId);
  if (!node) {
    return { kind: 'broken', node: null, reason: 'menu not found' };
  }
  const ownMenuId = node.menu_id || node.id;
  const ownSceneKey = node.scene_key || node.sceneKey || node.meta?.scene_key;
  if (ownSceneKey && ownMenuId) {
    return {
      kind: 'redirect',
      node,
      target: {
        menu_id: ownMenuId,
        scene_key: ownSceneKey,
        action_id: node.meta?.action_id,
        route: node.meta?.route,
        meta: node.meta,
        node,
      },
    };
  }
  if (node.meta && node.meta.action_id) {
    return { kind: 'leaf', meta: node.meta, node };
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
    const sceneKey = node.scene_key || node.sceneKey || node.meta?.scene_key;
    if (sceneKey) {
      return {
        menu_id: menuId,
        scene_key: sceneKey,
        node,
      };
    }
    if (node.meta && node.meta.action_id) {
      return {
        menu_id: menuId,
        action_id: node.meta.action_id,
        meta: node.meta,
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
  const expected = Number(menuId || 0);
  for (const node of nodes) {
    const nodeMenuId = Number(node?.menu_id || 0);
    const nodeId = Number(node?.id || 0);
    if (node && ((expected > 0 && nodeMenuId === expected) || (expected > 0 && nodeId === expected))) {
      return node;
    }
    if (node && Array.isArray(node.children) && node.children.length) {
      const found = findMenuNode(node.children, expected);
      if (found) {
        return found;
      }
    }
  }
  return null;
}
