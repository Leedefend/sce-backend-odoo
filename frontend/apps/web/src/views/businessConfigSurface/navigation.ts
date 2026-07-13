function navNodeMenuId(node: Record<string, unknown>) {
  const meta = node.meta && typeof node.meta === 'object' ? node.meta as Record<string, unknown> : {};
  for (const candidate of [node.menu_id, meta.menu_id, node.id]) {
    const parsed = Number(candidate || 0);
    if (Number.isInteger(parsed) && parsed > 0) return parsed;
  }
  return 0;
}

function navNodeActionId(node: Record<string, unknown>) {
  const meta = node.meta && typeof node.meta === 'object' ? node.meta as Record<string, unknown> : {};
  for (const candidate of [node.action_id, meta.action_id]) {
    const parsed = Number(candidate || 0);
    if (Number.isInteger(parsed) && parsed > 0) return parsed;
  }
  return 0;
}

function navNodeModel(node: Record<string, unknown>) {
  const meta = node.meta && typeof node.meta === 'object' ? node.meta as Record<string, unknown> : {};
  return String(node.model || meta.model || '').trim();
}

function navNodeLabel(node: Record<string, unknown>) {
  const meta = node.meta && typeof node.meta === 'object' ? node.meta as Record<string, unknown> : {};
  return String(node.name || node.label || node.title || meta.name || meta.label || '').trim();
}

export function findMenuConfigNavigationEntry(
  items: unknown[],
  menuConfigPolicyModel: string,
): { menuId: number; actionId: number } | null {
  for (const item of Array.isArray(items) ? items : []) {
    if (!item || typeof item !== 'object') continue;
    const node = item as Record<string, unknown>;
    const model = navNodeModel(node);
    const label = navNodeLabel(node);
    const menuId = navNodeMenuId(node);
    const actionId = navNodeActionId(node);
    if (label === '菜单配置' && model === menuConfigPolicyModel && menuId && actionId) {
      return { menuId, actionId };
    }
    const childMatch = findMenuConfigNavigationEntry(
      Array.isArray(node.children) ? node.children : [],
      menuConfigPolicyModel,
    );
    if (childMatch) return childMatch;
  }
  return null;
}
