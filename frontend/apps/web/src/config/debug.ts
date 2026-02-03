import type { RouteLocationNormalizedLoaded } from 'vue-router';

export function isHudEnabled(route: RouteLocationNormalizedLoaded) {
  if (import.meta.env.DEV) {
    return true;
  }
  return route.query.hud === '1';
}
