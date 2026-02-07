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
  status?: string;
  state?: 'READY' | 'LOCKED' | 'PREVIEW' | string;
  reason?: string;
  reason_code?: string;
  route?: string;
  intent?: string;
  payload?: Record<string, unknown>;
  capabilities?: string[];
  required_capabilities?: string[];
  requiredCapabilities?: string[];
}

export interface SceneListProfile {
  columns?: string[];
  hidden_columns?: string[];
  column_labels?: Record<string, string>;
  row_primary?: string;
  row_secondary?: string;
}

export interface SceneLayout {
  kind: 'list' | 'record' | 'workspace' | 'ledger';
  sidebar: 'fixed' | 'scroll';
  header: 'compact' | 'full';
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
  list_profile?: SceneListProfile;
  filters?: unknown[];
  default_sort?: string;
  layout?: SceneLayout;
}

export const DEFAULT_SCENE_LAYOUT: SceneLayout = {
  kind: 'workspace',
  sidebar: 'fixed',
  header: 'full',
};

let sceneRegistry: Scene[] = [];
let errors: Array<{ index: number; key?: string | null; route?: string | null; issues: string[] }> = [];

function normalizeSceneLayout(layout?: Partial<SceneLayout> | null): SceneLayout {
  if (!layout || typeof layout !== 'object') {
    return { ...DEFAULT_SCENE_LAYOUT };
  }
  return {
    kind: layout?.kind ?? DEFAULT_SCENE_LAYOUT.kind,
    sidebar: layout?.sidebar ?? DEFAULT_SCENE_LAYOUT.sidebar,
    header: layout?.header ?? DEFAULT_SCENE_LAYOUT.header,
  };
}

function coerceSceneSource(source: Scene[]) {
  return source
    .map((scene) => {
      if (scene && typeof scene === 'object' && 'key' in scene && 'route' in scene) {
        return { ...scene, layout: normalizeSceneLayout(scene.layout) };
      }
      const raw = scene as unknown as {
        code?: string;
        name?: string;
        route?: string;
        target?: SceneTarget;
        layout?: Partial<SceneLayout>;
        icon?: string;
        capabilities?: string[];
        breadcrumbs?: Array<{ label: string; to?: string }>;
        tiles?: SceneTile[];
        list_profile?: SceneListProfile;
        filters?: unknown[];
        default_sort?: string;
      };
      if (raw?.code) {
        const route = raw.route || `/s/${raw.code}`;
        const target =
          raw.target && typeof raw.target === 'object' && (
            raw.target.action_id ||
            raw.target.menu_id ||
            raw.target.model ||
            raw.target.route
          )
            ? raw.target
            : { route: `/workbench?scene=${raw.code}` };
        return {
          key: raw.code,
          label: raw.name || raw.code,
          icon: raw.icon,
          route,
          target,
          capabilities: raw.capabilities ?? [],
          breadcrumbs: raw.breadcrumbs ?? [],
          tiles: raw.tiles ?? [],
          list_profile: raw.list_profile,
          filters: raw.filters,
          default_sort: raw.default_sort,
          layout: normalizeSceneLayout(raw.layout),
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

export function resolveSceneLayout(scene?: Scene | null) {
  return normalizeSceneLayout(scene?.layout);
}
