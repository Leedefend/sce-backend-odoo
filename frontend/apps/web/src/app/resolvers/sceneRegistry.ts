import { SCENES } from '../../config/scenes';
import { validateSceneRegistry } from './sceneRegistryCore';

export interface SceneTarget {
  menu_id?: number;
  action_id?: number;
  model?: string;
  view_mode?: string;
  record_id?: number | string;
  route?: string;
}

export interface SceneTile {
  key?: string;
  title?: string;
  subtitle?: string;
  icon?: string;
  route?: string;
  intent?: string;
  payload?: Record<string, unknown>;
  capabilities?: string[];
  required_capabilities?: string[];
  requiredCapabilities?: string[];
}

export interface Scene {
  key: string;
  label: string;
  icon?: string;
  route: string;
  target: SceneTarget;
  capabilities?: string[];
  breadcrumbs?: Array<{ label: string; to?: string }>;
  tiles?: SceneTile[];
}

let sceneRegistry: Scene[] = [];
let errors: Array<{ index: number; key?: string | null; route?: string | null; issues: string[] }> = [];

function coerceSceneSource(source: Scene[]) {
  return source
    .map((scene) => {
      if (scene && typeof scene === 'object' && 'key' in scene && 'route' in scene) {
        return scene;
      }
      const raw = scene as unknown as { code?: string; name?: string; tiles?: SceneTile[] };
      if (raw?.code) {
        const route = `/s/${raw.code}`;
        return {
          key: raw.code,
          label: raw.name || raw.code,
          route,
          target: { route: `/workbench?scene=${raw.code}` },
          tiles: raw.tiles ?? [],
        } as Scene;
      }
      return null;
    })
    .filter((scene): scene is Scene => Boolean(scene));
}

function buildSceneRegistry(source: Scene[]) {
  const normalized = coerceSceneSource(source);
  const validation = validateSceneRegistry(normalized as Scene[]);
  const nextErrors = validation.errors as Array<{ index: number; key?: string | null; route?: string | null; issues: string[] }>;
  if (nextErrors.length) {
    // eslint-disable-next-line no-console
    console.warn('[scene-registry] invalid scenes detected', nextErrors);
  }
  errors = nextErrors;
  sceneRegistry = validation.validScenes as Scene[];
  return sceneRegistry;
}

buildSceneRegistry(SCENES as Scene[]);

export function getSceneRegistryDiagnostics() {
  return { errors };
}

export function setSceneRegistry(scenes?: Scene[] | null) {
  const source = Array.isArray(scenes) && scenes.length ? scenes : (SCENES as Scene[]);
  return buildSceneRegistry(source);
}

export function getSceneByKey(key: string) {
  return sceneRegistry.find((scene) => scene.key === key) || null;
}

export function getSceneRegistry() {
  return sceneRegistry;
}
