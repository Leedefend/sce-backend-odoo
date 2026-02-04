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

const validation = validateSceneRegistry(SCENES as Scene[]);
const errors = validation.errors as Array<{ index: number; key?: string | null; route?: string | null; issues: string[] }>;

if (errors.length) {
  // eslint-disable-next-line no-console
  console.warn('[scene-registry] invalid scenes detected', errors);
}

export const sceneRegistry = validation.validScenes as Scene[];

export function getSceneRegistryDiagnostics() {
  return { errors };
}

export function getSceneByKey(key: string) {
  return sceneRegistry.find((scene) => scene.key === key) || null;
}
