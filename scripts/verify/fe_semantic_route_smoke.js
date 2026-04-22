#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

function assertEqual(label, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (!ok) {
    console.error(`FAIL: ${label} -> expected=${JSON.stringify(expected)} actual=${JSON.stringify(actual)}`);
    return false;
  }
  console.log(`PASS: ${label}`);
  return true;
}

function assertIncludes(label, haystack, needle) {
  const ok = String(haystack || '').includes(String(needle || ''));
  if (!ok) {
    console.error(`FAIL: ${label} -> missing=${JSON.stringify(needle)}`);
    return false;
  }
  console.log(`PASS: ${label}`);
  return true;
}

async function main() {
  const file = path.resolve(__dirname, '../../frontend/apps/web/src/app/resolvers/sceneRegistry.ts');
  const text = fs.readFileSync(file, 'utf-8');
  let ok = true;

  ok = assertIncludes('scene registry runtime file present', text, 'const SCENE_ROUTE_OVERRIDES') && ok;
  ok = assertIncludes('my_work override key', text, "'my_work.workspace': '/my-work'") && ok;
  ok = assertIncludes('resolveSceneRoute exists', text, 'function resolveSceneRoute(code: string, route: string): string') && ok;
  ok = assertIncludes('legacy compat route detection exists', text, 'function isLegacyCompatRoute(route: unknown): boolean') && ok;
  ok = assertIncludes('legacy compat routes degrade to semantic default route', text, 'isLegacyCompatRoute(legacyRoute) ? defaultRoute : resolvedRoute') && ok;
  ok = assertIncludes('public entry route is preferred before legacy route', text, 'const rawRoute = publicEntryRoute || legacyRoute || defaultRoute;') && ok;
  ok = assertIncludes('unified home scene keys include workspace home', text, "const UNIFIED_HOME_SCENE_KEYS = new Set(['workspace.home', 'portal.dashboard', 'my_work.workspace']);") && ok;
  ok = assertIncludes('unified home routes include semantic and override routes', text, "const UNIFIED_HOME_ROUTES = new Set(['/', '/my-work', '/s/workspace.home', '/s/portal.dashboard']);") && ok;
  ok = assertIncludes('delivery source still coerces semantic route from raw code', text, 'const route = resolveSceneRoute(raw.code, raw.route || `/s/${raw.code}`);') && ok;
  ok = assertIncludes('target route also flows through semantic route override', text, 'route: resolveSceneRoute(raw.code, String(raw.target.route || route))') && ok;
  ok = assertIncludes('entry target is parsed from runtime payload', text, 'const entryTarget = readSceneEntryTarget(targetRow.entry_target);') && ok;

  if (!ok) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`FAIL: ${err.message}`);
  process.exit(1);
});
