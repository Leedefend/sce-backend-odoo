#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const TARGETS = [
  'frontend/apps/web/src/layouts/AppShell.vue',
  'frontend/apps/web/src/views/ActionView.vue',
  'frontend/apps/web/src/pages/ListPage.vue',
  'frontend/apps/web/src/pages/KanbanPage.vue',
];

function resolveRoot() {
  const candidates = [
    process.env.REPO_ROOT,
    path.resolve(__dirname, '../..'),
    path.resolve(__dirname, '../../..'),
    '/mnt',
    '/mnt/sc-backend-odoo',
    '/mnt/e/sc-backend-odoo',
  ].filter(Boolean);
  for (const root of candidates) {
    const probe = path.join(root, TARGETS[0]);
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
  const appShell = readFile(TARGETS[0]);
  const actionView = readFile(TARGETS[1]);
  const listPage = readFile(TARGETS[2]);
  const kanbanPage = readFile(TARGETS[3]);

  assert(appShell.includes('const pageTitle = computed'), 'AppShell missing pageTitle computed');
  assert(appShell.includes('{{ pageTitle }}'), 'AppShell headline must use pageTitle');

  assert(!actionView.includes('<header class="header">'), 'ActionView should not render its own header');
  assert(!listPage.includes('<h2>{{ title }}</h2>'), 'ListPage must not render direct H2 title');
  assert(!kanbanPage.includes('<h2>{{ title }}</h2>'), 'KanbanPage must not render direct H2 title');

  console.log('[fe_list_shell_title_smoke] PASS title source checks');
}

try {
  main();
} catch (err) {
  console.error(`[fe_list_shell_title_smoke] FAIL: ${err.message}`);
  process.exit(1);
}
