#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const file = path.resolve(__dirname, '../../frontend/apps/web/src/app/resolvers/sceneRegistry.ts');
const src = fs.readFileSync(file, 'utf8');

function assertContains(label, snippet) {
  if (!src.includes(snippet)) {
    throw new Error(`${label} missing`);
  }
}

function assertNotContains(label, snippet) {
  if (src.includes(snippet)) {
    throw new Error(`${label} should not exist`);
  }
}

function main() {
  assertContains('raw.target passthrough', 'raw.target && typeof raw.target === \'object\'');
  assertContains('raw.layout passthrough', 'layout: normalizeSceneLayout(raw.layout)');
  assertContains('fallback route kept', 'route: `/workbench?scene=${raw.code}`');
  assertNotContains('forced workbench target', 'target: { route: `/workbench?scene=${raw.code}` },');
  console.log('[fe_scene_registry_coerce_smoke] PASS');
}

try {
  main();
} catch (err) {
  console.error(`[fe_scene_registry_coerce_smoke] FAIL: ${err.message}`);
  process.exit(1);
}

