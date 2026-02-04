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
  const modulePath = path.resolve(__dirname, '../../frontend/apps/web/src/app/resolvers/menuResolverCore.js');
  const moduleUrl = pathToFileURL(modulePath).href;
  const { resolveMenuActionCore } = await import(moduleUrl);

  let ok = true;

  const menuTree = [
    { menu_id: 1, name: 'Root', children: [
      { menu_id: 2, name: 'Group', children: [{ menu_id: 3, name: 'Leaf', meta: { action_id: 99 } }] },
      { menu_id: 4, name: 'Broken' },
    ] },
  ];

  const leaf = resolveMenuActionCore(menuTree, 3);
  ok = assertEqual('Leaf kind', leaf.kind, 'leaf') && ok;

  const group = resolveMenuActionCore(menuTree, 2);
  ok = assertEqual('Group kind', group.kind, 'group') && ok;

  const broken = resolveMenuActionCore(menuTree, 4);
  ok = assertEqual('Broken kind', broken.kind, 'broken') && ok;
  ok = assertEqual('Broken reason', broken.reason, 'menu has no action') && ok;

  if (!ok) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`FAIL: ${err.message}`);
  process.exit(1);
});
