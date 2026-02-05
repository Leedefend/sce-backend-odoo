import type { RouteLocationNormalizedLoaded } from 'vue-router';

export function isHudEnabled(route: RouteLocationNormalizedLoaded) {
  if (!import.meta.env.DEV) {
    return false;
  }
  if (route.query.hud === '1') {
    return true;
  }
  return localStorage.getItem('__HUD__') === '1';
}
