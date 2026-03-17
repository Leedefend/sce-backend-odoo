const CORE_SCENES = new Set([
  'workspace.home',
  'workspace_home',
  'finance.payment_requests',
  'risk.center',
  'project.management',
]);

function normalizeSceneKey(sceneKey: unknown): string {
  return typeof sceneKey === 'string' ? sceneKey.trim().toLowerCase() : '';
}

export function isCoreSceneStrictMode(sceneKey: unknown): boolean {
  const key = normalizeSceneKey(sceneKey);
  if (!key) return false;
  if (CORE_SCENES.has(key)) return true;
  if (key.startsWith('/s/')) return CORE_SCENES.has(key.replace('/s/', ''));
  return false;
}
