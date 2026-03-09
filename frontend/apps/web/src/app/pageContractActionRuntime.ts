import type { Router } from 'vue-router';

export type ContractActionDeps = {
  actionKey: string;
  router: Router;
  actionIntent: (key: string, fallback?: string) => string;
  actionTarget: (key: string) => Record<string, unknown>;
  query?: Record<string, unknown>;
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

  if (intent === 'ui.contract' && scene) {
    await deps.router.push({ path: `/s/${scene}`, query });
    return true;
  }

  if (deps.onFallback) {
    const handled = await deps.onFallback(deps.actionKey);
    return handled === true;
  }

  return false;
}
