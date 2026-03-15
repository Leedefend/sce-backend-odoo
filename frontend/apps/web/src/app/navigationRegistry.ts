import type { Scene } from './resolvers/sceneRegistry';
import type { CapabilityRuntimeMeta } from '../stores/session';

export type NavigationEntrySource = 'scene' | 'capability';

export interface RuntimeNavigationEntry {
  registryKey: string;
  entrySource: NavigationEntrySource;
  sceneKey?: string;
  capabilityKey?: string;
  title: string;
  groupKey?: string;
}

export interface RuntimeNavigationRegistry {
  entries: RuntimeNavigationEntry[];
  sceneEntries: RuntimeNavigationEntry[];
  capabilityEntries: RuntimeNavigationEntry[];
}

function asText(value: unknown): string {
  return String(value ?? '').trim();
}

function isProductSceneKey(sceneKey: string): boolean {
  const key = sceneKey.trim().toLowerCase();
  if (!key) return false;
  if (key.startsWith('default')) return false;
  return !key.includes('__pkg');
}

function resolveSceneTitle(scene: Scene): string {
  const title = asText(scene.label);
  if (title) return title;
  return asText(scene.key);
}

export function buildRuntimeNavigationRegistry(params: {
  scenes: Scene[];
  capabilityCatalog: Record<string, CapabilityRuntimeMeta>;
}): RuntimeNavigationRegistry {
  const sceneEntries: RuntimeNavigationEntry[] = [];
  const capabilityEntries: RuntimeNavigationEntry[] = [];
  const sceneKeys = new Set<string>();
  const capabilityKeys = new Set<string>();

  for (const scene of params.scenes || []) {
    const sceneKey = asText(scene.key);
    if (!sceneKey || !isProductSceneKey(sceneKey) || sceneKeys.has(sceneKey)) continue;
    sceneKeys.add(sceneKey);
    sceneEntries.push({
      registryKey: `nav.scene::${sceneKey}`,
      entrySource: 'scene',
      sceneKey,
      title: resolveSceneTitle(scene),
    });
  }

  const catalog = params.capabilityCatalog || {};
  Object.entries(catalog).forEach(([capabilityKey, meta]) => {
    const key = asText(capabilityKey);
    if (!key || capabilityKeys.has(key)) return;
    capabilityKeys.add(key);
    capabilityEntries.push({
      registryKey: `nav.capability::${key}`,
      entrySource: 'capability',
      capabilityKey: key,
      title: asText(meta?.label) || key,
      groupKey: asText(meta?.group_key),
      sceneKey: sceneEntries[0]?.sceneKey,
    });
  });

  return {
    entries: [...sceneEntries, ...capabilityEntries],
    sceneEntries,
    capabilityEntries,
  };
}
