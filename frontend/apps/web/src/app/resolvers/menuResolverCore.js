export function resolveMenuActionCore(menuTree, menuId) {
  const node = findMenuNode(menuTree, menuId);
  if (!node) {
    return { kind: 'broken', node: null, reason: 'menu not found' };
  }
  const ownMenuId = node.menu_id || node.id;
  const ownSceneKey = resolveSceneKey(node);
  const ownActionId = resolveActionId(node);
  if (shouldUseSceneRoute(node, ownActionId) && ownSceneKey && ownMenuId) {
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
  if (ownActionId) {
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
    const actionId = resolveActionId(node);
    const sceneKey = resolveSceneKey(node);
    if (shouldUseSceneRoute(node, actionId) && sceneKey) {
      return {
        menu_id: menuId,
        scene_key: sceneKey,
        node,
      };
    }
    if (actionId) {
      return {
        menu_id: menuId,
        action_id: actionId,
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

function resolveActionId(node) {
  const actionId = Number(node?.meta?.action_id || 0);
  return Number.isFinite(actionId) && actionId > 0 ? actionId : 0;
}

function resolveSceneKey(node) {
  return node?.scene_key || node?.sceneKey || node?.meta?.scene_key || '';
}

function shouldUseSceneRoute(node, actionId) {
  const explicitSceneKey = resolveSceneKey(node);
  if (!explicitSceneKey) {
    return false;
  }
  const sceneSource = String(node?.meta?.scene_source || '').trim().toLowerCase();
  const actionType = String(node?.meta?.action_type || '').trim().toLowerCase();
  if (sceneSource === 'scene_contract' || actionType === 'scene.contract') {
    return true;
  }
  return false;
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
