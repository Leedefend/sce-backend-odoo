import type { RouteLocationRaw } from 'vue-router';
import { pickContractNavQuery } from './navigationContext';
import { findSceneByEntryAuthority } from './resolvers/sceneRegistry';

type SceneFirstLocationOptions = {
  sourceQuery: Record<string, unknown>;
  sceneKey?: string;
  actionId?: number | string;
  menuId?: number | string;
  model?: string;
  recordId?: number | string;
  viewMode?: string;
  extraQuery?: Record<string, unknown>;
};

function normalizePositiveInt(value: unknown): number | undefined {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return undefined;
  }
  return Math.trunc(numeric);
}

export function resolveSceneFirstActionLocation(
  options: Omit<SceneFirstLocationOptions, 'recordId'>,
): RouteLocationRaw | null {
  const currentSceneKey = String(options.sceneKey || '').trim();
  const actionId = normalizePositiveInt(options.actionId);
  const menuId = normalizePositiveInt(options.menuId);
  const model = String(options.model || '').trim();
  const viewMode = String(options.viewMode || '').trim();
  const scene = findSceneByEntryAuthority({
    sceneKey: currentSceneKey,
    actionId,
    menuId,
    model: model || undefined,
    viewMode: viewMode || undefined,
  }) || findSceneByEntryAuthority({
    actionId,
    menuId,
    model: model || undefined,
    viewMode: viewMode || undefined,
  });
  if (!scene) {
    return null;
  }
  return {
    path: scene.route || `/s/${scene.key}`,
    query: pickContractNavQuery(options.sourceQuery, {
      action_id: actionId || scene.target.action_id || undefined,
      menu_id: menuId || scene.target.menu_id || undefined,
      scene_key: scene.key,
      model: model || undefined,
      view_mode: viewMode || undefined,
      ...(options.extraQuery || {}),
    }),
  };
}

export function resolveSceneFirstFormOrRecordLocation(
  options: SceneFirstLocationOptions,
): RouteLocationRaw | null {
  const currentSceneKey = String(options.sceneKey || '').trim();
  const actionId = normalizePositiveInt(options.actionId);
  const menuId = normalizePositiveInt(options.menuId);
  const model = String(options.model || '').trim();
  const recordId = normalizePositiveInt(options.recordId);
  const scene = findSceneByEntryAuthority({
    sceneKey: currentSceneKey,
    actionId,
    menuId,
    model: model || undefined,
    recordId,
  }) || findSceneByEntryAuthority({
    actionId,
    menuId,
    model: model || undefined,
    recordId,
  });
  if (!scene) {
    return null;
  }
  return {
    path: scene.route || `/s/${scene.key}`,
    query: pickContractNavQuery(options.sourceQuery, {
      action_id: actionId || scene.target.action_id || undefined,
      menu_id: menuId || scene.target.menu_id || undefined,
      scene_key: scene.key,
      model: model || undefined,
      record_id: recordId || undefined,
      ...(options.extraQuery || {}),
    }),
  };
}
