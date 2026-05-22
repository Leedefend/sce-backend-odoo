/* eslint-disable @typescript-eslint/no-unused-vars */
import type { LocationQueryRaw, Router } from 'vue-router';
import { getSceneByKey } from './resolvers/sceneRegistry';
import { buildCanonicalSceneRouteTarget } from './routeQuery';

export type ContractActionDeps = {
  actionKey: string;
  router: Router;
  actionIntent: (key: string, fallback?: string) => string;
  actionTarget: (key: string) => Record<string, unknown>;
  query?: LocationQueryRaw;
  onRefresh?: () => Promise<void> | void;
  onOpenMenuFirstReachable?: () => Promise<boolean> | boolean;
  onFallback?: (actionKey: string) => Promise<boolean> | boolean;
};

export async function executePageContractAction(deps: ContractActionDeps): Promise<boolean> {
  const target = deps.actionTarget(deps.actionKey);
  const kind = String(target.kind || '');
  const scene = String(target.scene_key || '');
  const intent = deps.actionIntent(deps.actionKey, '');
  const query = deps.query || {};

  if (kind === 'page.refresh') {
    if (deps.onRefresh) await deps.onRefresh();
    return true;
  }

  if (kind === 'menu.first_reachable') {
    if (deps.onOpenMenuFirstReachable) {
      const handled = await deps.onOpenMenuFirstReachable();
      return handled === true;
    }
    return false;
  }

  if (kind === 'route.path') {
    const path = String(target.path || '');
    if (!path) return false;
    await deps.router.push({ path, query });
    return true;
  }

  if (kind === 'scene.key') {
    if (!scene) return false;
    const sceneNode = getSceneByKey(scene);
    await deps.router.push(buildCanonicalSceneRouteTarget(scene, {
      scene: sceneNode,
      query,
      menuId: sceneNode?.target?.menu_id,
      actionId: sceneNode?.target?.action_id,
    }));
    return true;
  }

  if (intent === 'ui.contract' && scene) {
    const sceneNode = getSceneByKey(scene);
    await deps.router.push(buildCanonicalSceneRouteTarget(scene, {
      scene: sceneNode,
      query,
      menuId: sceneNode?.target?.menu_id,
      actionId: sceneNode?.target?.action_id,
    }));
    return true;
  }

  if (deps.onFallback) {
    const handled = await deps.onFallback(deps.actionKey);
    return handled === true;
  }

  return false;
}
