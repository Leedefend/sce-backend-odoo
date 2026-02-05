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

export interface Scene {
  key: string;
  label: string;
  icon?: string;
  route: string;
  target: SceneTarget;
  capabilities?: string[];
  breadcrumbs?: Array<{ label: string; to?: string }>;
}

let sceneRegistry: Scene[] = [];
let errors: Array<{ index: number; key?: string | null; route?: string | null; issues: string[] }> = [];

function buildSceneRegistry(source: Scene[]) {
  const validation = validateSceneRegistry(source as Scene[]);
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
