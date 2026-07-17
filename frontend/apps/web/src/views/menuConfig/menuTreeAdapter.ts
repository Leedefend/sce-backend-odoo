import type { NavNode } from '@sc/schema';
import type { MenuConfigMenu, MenuConfigPayload } from '../../api/menuConfig';

export type MenuConfigNavNode = NavNode & {
  action_id?: number | string;
  model?: string;
  config_menu_id?: number | string;
  configurable?: boolean;
  config_ref?: { model?: string; id?: number | string };
  meta?: NavNode['meta'] & {
    config_menu_id?: number | string;
    configurable?: boolean;
    config_ref?: { model?: string; id?: number | string };
  };
};
export type RuntimeMenuConfigGroup = MenuConfigMenu & { runtime_group?: boolean };
type MenuConfigTreeNode = MenuConfigMenu & { menu_config_missing?: boolean };

export function createMenuTreeAdapter(options: {
  isMenuConfigSurfaceMenu: (menu: MenuConfigMenu) => boolean;
  scopedNavigationTree: () => NavNode[];
}) {
  const { isMenuConfigSurfaceMenu, scopedNavigationTree } = options;
  function navMenuId(node: NavNode) {
    return Number(node.menu_id || node.meta?.menu_id || node.id || 0);
  }

  function navConfigMenuId(node: MenuConfigNavNode) {
    const meta = node.meta || {};
    const configRef = node.config_ref || meta.config_ref || {};
    const configRefModel = String(configRef.model || 'ir.ui.menu').trim();
    const candidates = [
      node.config_menu_id,
      meta.config_menu_id,
      configRefModel === 'ir.ui.menu' ? configRef.id : 0,
      node.configurable === false || meta.configurable === false ? 0 : navMenuId(node),
    ];
    for (const candidate of candidates) {
      const menuId = Number(candidate || 0);
      if (Number.isFinite(menuId) && menuId > 0) return menuId;
    }
    return 0;
  }

  function navMenuLabel(node: NavNode) {
    return String(node.title || node.name || node.label || '').trim();
  }

  function buildTreeFromNavigation(
    navNodes: NavNode[],
    menuById: Map<number, MenuConfigMenu>,
    usedMenuIds = new Set<number>(),
  ): MenuConfigMenu[] {
    return navNodes.flatMap((node) => {
      const configMenuId = navConfigMenuId(node as MenuConfigNavNode);
      const runtimeNodeId = navMenuId(node);
      const label = navMenuLabel(node);
      let menu = menuById.get(configMenuId);
      if (menu && usedMenuIds.has(menu.id)) {
        menu = undefined;
      }
      if (!menu) {
        const children = Array.isArray(node.children)
          ? buildTreeFromNavigation(node.children as NavNode[], menuById, usedMenuIds)
          : [];
        if (!children.length || !label || !runtimeNodeId) return children;
        return [{
          id: runtimeNodeId,
          menu_id: runtimeNodeId,
          name: label,
          display_name: label,
          complete_name: label,
          parent_id: 0,
          parent_name: '',
          sequence: Number(node.sequence ?? node.meta?.sequence ?? 0),
          action: '',
          web_icon: '',
          xmlid: '__runtime_group__',
          group_ids: [],
          group_names: [],
          runtime_group: true,
          children,
        } as RuntimeMenuConfigGroup];
      }
      usedMenuIds.add(menu.id);
      return [{
        ...menu,
        name: label || menu.name,
        display_name: label || menu.display_name,
        sequence: Number(node.sequence ?? node.meta?.sequence ?? menu.sequence ?? 0),
        children: Array.isArray(node.children)
          ? buildTreeFromNavigation(node.children as NavNode[], menuById, usedMenuIds)
          : [],
      }];
    });
  }

  function markHandlingMembership(items: MenuConfigMenu[], usedMenuIds: Set<number>): MenuConfigMenu[] {
    return items.map((item) => {
      const menuId = Number(item.id || 0);
      const children = item.children?.length ? markHandlingMembership(item.children, usedMenuIds) : [];
      if (!menuId || usedMenuIds.has(menuId)) {
        return { ...item, children };
      }
      return { ...item, children, menu_config_missing: true } as MenuConfigTreeNode;
    });
  }

  function filterMenuConfigSurfaceTree(items: MenuConfigMenu[]): MenuConfigMenu[] {
    return items.flatMap((item) => {
      const children = item.children?.length ? filterMenuConfigSurfaceTree(item.children) : [];
      if (isMenuConfigSurfaceMenu(item) || children.length) {
        return [{ ...item, children }];
      }
      return [];
    });
  }

  function mergeNavigationAndConfigTrees(navigationTree: MenuConfigMenu[], configTree: MenuConfigMenu[], usedMenuIds: Set<number>) {
    if (!navigationTree.length) {
      return filterMenuConfigSurfaceTree(markHandlingMembership(configTree, usedMenuIds));
    }
    return navigationTree;
  }

  function runtimeNavigationTreeFromPayload(payload: MenuConfigPayload) {
    return Array.isArray(payload.runtime?.tree) ? (payload.runtime.tree as NavNode[]) : [];
  }

  function collectNavigationMenuIds() {
    const ids: number[] = [];
    const seen = new Set<number>();
    const walk = (items: Array<{ menu_id?: number; id?: number; children?: unknown[] }>) => {
      items.forEach((item) => {
        const menuId = navConfigMenuId(item as MenuConfigNavNode);
        if (Number.isFinite(menuId) && menuId > 0 && !seen.has(menuId)) {
          seen.add(menuId);
          ids.push(menuId);
        }
        if (Array.isArray(item.children)) {
          walk(item.children as Array<{ menu_id?: number; id?: number; children?: unknown[] }>);
        }
      });
    };
    walk(scopedNavigationTree());
    return ids;
  }
  return {
    navMenuId,
    navMenuLabel,
    buildTreeFromNavigation,
    mergeNavigationAndConfigTrees,
    runtimeNavigationTreeFromPayload,
    collectNavigationMenuIds,
  };
}
