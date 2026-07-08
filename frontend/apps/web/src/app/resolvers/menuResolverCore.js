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
        action_id: ownActionId || undefined,
        scene_key: ownSceneKey,
        entry_target: resolveEntryTarget(node),
        node,
      },
    };
  }
  if (ownActionId) {
    return { kind: 'leaf', meta: resolveActionMeta(node), node };
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
        action_id: actionId || undefined,
        scene_key: sceneKey,
        entry_target: resolveEntryTarget(node),
        node,
      };
    }
    if (actionId) {
      return {
        menu_id: menuId,
        action_id: actionId,
        meta: resolveActionMeta(node),
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
  const actionId = Number(node?.meta?.action_id || node?.action_id || node?.native_action_id || 0);
  return Number.isFinite(actionId) && actionId > 0 ? actionId : 0;
}

function resolveActionMeta(node) {
  const meta = node?.meta && typeof node.meta === 'object' ? { ...node.meta } : {};
  const actionMeta = node?.action_meta && typeof node.action_meta === 'object' ? node.action_meta : {};
  const actionId = resolveActionId(node);
  if (actionId && !meta.action_id) meta.action_id = actionId;
  if (!meta.model) meta.model = node?.model || node?.native_model || actionMeta.res_model || '';
  if (!meta.view_modes) {
    const rawViewMode = node?.view_mode || node?.native_view_mode || actionMeta.view_mode || '';
    meta.view_modes = Array.isArray(rawViewMode)
      ? rawViewMode
      : String(rawViewMode || '').split(',').map((item) => item.trim()).filter(Boolean);
  }
  if (!meta.name) meta.name = node?.name || node?.label || node?.title || '';
  if (!meta.menu_id) meta.menu_id = node?.menu_id || node?.id || 0;
  return meta;
}

function resolveSceneKey(node) {
  return resolveSceneEntryTarget(node)?.scene_key || node?.scene_key || node?.sceneKey || node?.meta?.scene_key || '';
}

function resolveEntryTarget(node) {
  const entryTarget = node?.meta?.entry_target || node?.entry_target;
  if (entryTarget && typeof entryTarget === 'object' && String(entryTarget.type || '').trim()) {
    return entryTarget;
  }
  return null;
}

function resolveSceneEntryTarget(node) {
  const entryTarget = resolveEntryTarget(node);
  if (entryTarget && String(entryTarget.type || '') === 'scene' && entryTarget.scene_key) {
    return entryTarget;
  }
  return null;
}

function shouldUseSceneRoute(node, actionId) {
  if (resolveSceneEntryTarget(node)) {
    return true;
  }
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
