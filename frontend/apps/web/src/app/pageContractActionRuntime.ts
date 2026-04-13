import type { LocationQueryRaw, Router } from 'vue-router';
import { getSceneByKey } from './resolvers/sceneRegistry';
import { buildSceneRegistryFallbackPath, normalizeLegacyWorkbenchPath } from './routeQuery';
import { normalizeRenderProfile, type RenderProfile } from './pageContract';

export type ContractActionDeps = {
  actionKey: string;
  router: Router;
  actionIntent: (key: string, fallback?: string) => string;
  actionTarget: (key: string) => Record<string, unknown>;
  query?: LocationQueryRaw;
  renderProfile?: RenderProfile;
  onRefresh?: () => Promise<void> | void;
  onOpenMenuFirstReachable?: () => Promise<boolean> | boolean;
  onFallback?: (actionKey: string) => Promise<boolean> | boolean;
};

export async function executePageContractAction(deps: ContractActionDeps): Promise<boolean> {
  const intent = deps.actionIntent(deps.actionKey, 'ui.contract');
  const target = deps.actionTarget(deps.actionKey);
  const kind = String(target.kind || '');
  const scene = String(target.scene_key || '');
  const query = deps.query || {};
  const renderProfile = normalizeRenderProfile(deps.renderProfile, 'edit');
  const visibleProfiles = Array.isArray(target.visible_profiles)
    ? target.visible_profiles.map((item) => String(item || '').trim().toLowerCase()).filter(Boolean)
    : [];
  if (visibleProfiles.length > 0 && !visibleProfiles.includes(renderProfile)) {
    return false;
  }

  const resolveScenePath = (sceneKey: string): string => {
    const sceneNode = getSceneByKey(sceneKey);
    if (!sceneNode) {
      return buildSceneRegistryFallbackPath({ sceneKey, label: sceneKey });
    }
    const rawPath = String(sceneNode?.target?.route || sceneNode?.route || `/s/${sceneKey}`).trim();
    return normalizeLegacyWorkbenchPath(rawPath) || `/s/${sceneKey}`;
  };

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
    if (path) {
      await deps.router.push({ path, query });
      return true;
    }
  }

  if (kind === 'scene.key') {
    if (!scene) return false;
    await deps.router.push({ path: resolveScenePath(scene), query });
    return true;
  }

  if (intent === 'ui.contract' && scene) {
    await deps.router.push({ path: resolveScenePath(scene), query });
    return true;
  }

  if (deps.onFallback) {
    const handled = await deps.onFallback(deps.actionKey);
    return handled === true;
  }

  return false;
}
