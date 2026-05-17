#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const SOURCE = path.join(ROOT, 'frontend/apps/web/src/pages/ContractFormPage.vue');
const source = fs.readFileSync(SOURCE, 'utf8');

function assertContains(token, message) {
  if (!source.includes(token)) {
    throw new Error(message);
  }
}

assertContains('function buildLowCodeViewOrchestration()', 'missing low-code view orchestration builder');
assertContains('view_orchestration: buildLowCodeViewOrchestration()', 'low-code save must persist view_orchestration');
assertContains('collectLowCodeLayoutFromViewOrchestration', 'low-code load must hydrate from view_orchestration');
assertContains("views.form = {", 'low-code orchestration must build form view spec');
assertContains("views.tree = {", 'low-code orchestration must build tree view spec');
assertContains("views.kanban = {", 'low-code orchestration must build kanban view spec');

console.log('[contract_form_lowcode_orchestration_smoke] PASS');
