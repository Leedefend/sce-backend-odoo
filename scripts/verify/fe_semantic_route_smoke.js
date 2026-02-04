#!/usr/bin/env node
'use strict';

const path = require('path');
const { pathToFileURL } = require('url');

function assertEqual(label, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (!ok) {
    console.error(`FAIL: ${label} -> expected=${JSON.stringify(expected)} actual=${JSON.stringify(actual)}`);
    return false;
  }
  console.log(`PASS: ${label}`);
  return true;
}

async function main() {
  const modulePath = path.resolve(__dirname, '../../frontend/apps/web/src/config/scenesCore.js');
  const moduleUrl = pathToFileURL(modulePath).href;
  const { SCENES } = await import(moduleUrl);

  const byKey = new Map(SCENES.map((scene) => [scene.key, scene]));
  let ok = true;

  ok = assertEqual('scene projects route', byKey.get('projects')?.route, '/projects') && ok;
  ok = assertEqual('scene project-record route', byKey.get('project-record')?.route, '/projects/:id') && ok;

  if (!ok) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`FAIL: ${err.message}`);
  process.exit(1);
});
