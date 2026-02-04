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
  const modulePath = path.resolve(__dirname, '../../frontend/apps/web/src/app/capabilityCore.js');
  const moduleUrl = pathToFileURL(modulePath).href;
  const { checkCapabilities } = await import(moduleUrl);

  let ok = true;

  const allow = checkCapabilities(['cap.project', 'cap.cost'], ['cap.project', 'cap.cost']);
  ok = assertEqual('capabilities ok', allow.ok, true) && ok;

  const missing = checkCapabilities(['cap.project', 'cap.cost'], ['cap.project']);
  ok = assertEqual('capabilities missing ok=false', missing.ok, false) && ok;
  ok = assertEqual('capabilities missing list', missing.missing, ['cap.cost']) && ok;

  if (!ok) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`FAIL: ${err.message}`);
  process.exit(1);
});
