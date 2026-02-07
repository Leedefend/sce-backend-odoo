#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const TARGET = 'frontend/apps/web/src/layouts/AppShell.vue';

function resolveRoot() {
  const candidates = [
    process.env.REPO_ROOT,
    path.resolve(__dirname, '../..'),
    process.cwd(),
  ].filter(Boolean);
  for (const root of candidates) {
    const probe = path.join(root, TARGET);
    if (fs.existsSync(probe)) {
      return root;
    }
  }
  return candidates[0] || process.cwd();
}

const ROOT = resolveRoot();

function readFile(rel) {
  return fs.readFileSync(path.join(ROOT, rel), 'utf8');
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function main() {
  const appShell = readFile(TARGET);

  const forbidden = ['User:', 'DB:', 'Nav v'];
  const hits = forbidden.filter((token) => appShell.includes(token));
  assert(hits.length === 0, `AppShell must not render system meta in UI: ${hits.join(', ')}`);

  console.log('[fe_list_shell_no_meta_smoke] PASS system meta hidden');
}

try {
  main();
} catch (err) {
  console.error(`[fe_list_shell_no_meta_smoke] FAIL: ${err.message}`);
  process.exit(1);
}
