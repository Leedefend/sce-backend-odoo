import type { RouteLocationNormalizedLoaded } from 'vue-router';
import { firstQueryValue } from '../app/routeQuery';

function isTruthyHudValue(raw: unknown) {
  const value = String(raw || '').trim().toLowerCase();
  return value === '1' || value === 'true';
}

function extractHudFromRawSearch(rawSearch: string) {
  const search = String(rawSearch || '').trim();
  if (!search) return '';
  const matched = search.match(/(?:^|[?&])hud=([^&]+)/i);
  if (matched && matched[1]) {
    try {
      return decodeURIComponent(matched[1]);
    } catch {
      return matched[1];
    }
  }
  return '';
}

function extractHudFromSceneQuery(sceneQuery: unknown) {
  const scene = String(firstQueryValue(sceneQuery) || '').trim();
  if (!scene || !scene.includes('?')) return '';
  const [, nestedQuery] = scene.split('?', 2);
  if (!nestedQuery) return '';
  const nestedParams = new URLSearchParams(nestedQuery);
  return String(nestedParams.get('hud') || '').trim();
}

export function isHudEnabled(route: RouteLocationNormalizedLoaded) {
  const directHud = firstQueryValue(route.query.hud);
  const nestedHud = extractHudFromSceneQuery(route.query.scene);
  const rawHud =
    typeof window !== 'undefined' ? extractHudFromRawSearch(window.location.search) : '';
  return (
    import.meta.env.DEV ||
    isTruthyHudValue(directHud) ||
    isTruthyHudValue(nestedHud) ||
    isTruthyHudValue(rawHud) ||
    localStorage.getItem('__HUD__') === '1'
  );
}
