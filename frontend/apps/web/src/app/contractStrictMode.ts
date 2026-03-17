const PILOT_SCENES = new Set([
  'workspace.home',
  'workspace_home',
  'finance.payment_requests',
  'risk.center',
  'project.management',
]);

function asDict(value: unknown): Record<string, unknown> {
  return (value && typeof value === 'object' && !Array.isArray(value))
    ? (value as Record<string, unknown>)
    : {};
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value.trim().toLowerCase() : '';
}

function normalizeSceneKey(sceneKey: unknown): string {
  const key = asText(sceneKey);
  if (!key) return '';
  if (key.startsWith('/s/')) return key.replace('/s/', '');
  return key;
}

function resolveRuntimePolicy(sceneReadyEntry: unknown): Record<string, unknown> {
  const entry = asDict(sceneReadyEntry);
  const meta = asDict(entry.meta);
  const scene = asDict(entry.scene);
  return asDict(entry.runtime_policy || meta.runtime_policy || scene.runtime_policy);
}

function resolveSceneTier(sceneReadyEntry: unknown, runtimePolicy: Record<string, unknown>): string {
  const entry = asDict(sceneReadyEntry);
  const meta = asDict(entry.meta);
  const scene = asDict(entry.scene);
  return asText(
    runtimePolicy.scene_tier
    || entry.scene_tier
    || meta.scene_tier
    || scene.tier,
  );
}

export function isCoreSceneStrictMode(sceneKey: unknown, sceneReadyEntry?: unknown): boolean {
  const runtimePolicy = resolveRuntimePolicy(sceneReadyEntry);
  if (typeof runtimePolicy.strict_contract_mode === 'boolean') {
    return Boolean(runtimePolicy.strict_contract_mode);
  }

  const tier = resolveSceneTier(sceneReadyEntry, runtimePolicy);
  if (tier === 'core') return true;

  const key = normalizeSceneKey(sceneKey);
  if (!key) return false;

  const hasBackendTierSignal = Boolean(tier);
  if (hasBackendTierSignal) {
    return false;
  }

  return PILOT_SCENES.has(key);
}
