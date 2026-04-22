import type { NavMeta, NavNode } from '@sc/schema';
import { resolveMenuActionCore } from './menuResolverCore';
import { findSceneByEntryAuthority } from './sceneRegistry';

export type MenuResolveResult =
  | { kind: 'leaf'; meta: NavMeta; node: NavNode }
  | {
      kind: 'redirect';
      node: NavNode;
      target: { menu_id: number; action_id?: number; scene_key?: string; route?: string; meta?: NavMeta; node?: NavNode };
    }
  | { kind: 'group'; node: NavNode }
  | { kind: 'broken'; node: NavNode | null; reason: string };

export function resolveMenuAction(menuTree: NavNode[], menuId: number): MenuResolveResult {
  return resolveMenuActionCore(menuTree, menuId) as MenuResolveResult;
}

export function resolveScenePathFromMenuResolve(result: MenuResolveResult, menuId: number) {
  if (result.kind === 'redirect' && result.target.scene_key) {
    const sceneKey = String(result.target.scene_key || '').trim();
    if (sceneKey) {
      return {
        sceneKey,
        path: `/s/${sceneKey}`,
        menuId: Number(result.target.menu_id || menuId) || menuId,
        actionId: undefined,
      };
    }
  }
  const actionId = result.kind === 'leaf'
    ? Number(result.meta.action_id || 0)
    : Number(result.kind === 'redirect' ? result.target.action_id || 0 : 0);
  const resolvedMenuId = result.kind === 'leaf'
    ? menuId
    : Number(result.kind === 'redirect' ? result.target.menu_id || menuId : menuId);
  if (actionId > 0) {
    const scene = findSceneByEntryAuthority({
      actionId,
      menuId: resolvedMenuId,
    });
    if (scene) {
      return {
        sceneKey: scene.key,
        path: scene.route || `/s/${scene.key}`,
        menuId: resolvedMenuId,
        actionId: undefined,
      };
    }
  }
  return null;
}
