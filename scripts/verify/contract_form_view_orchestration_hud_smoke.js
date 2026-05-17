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

assertContains('const viewOrchestrationHudSummary = computed(', 'missing view orchestration HUD summary');
assertContains("label: 'view_orchestration_applied'", 'HUD must show whether orchestration applied');
assertContains("label: 'view_orchestration_contracts'", 'HUD must show applied orchestration contract count');
assertContains("label: 'view_orchestration_names'", 'HUD must show applied orchestration contract names');
assertContains("label: 'legacy_policy_overlay'", 'HUD must show legacy field policy overlay state');

console.log('[contract_form_view_orchestration_hud_smoke] PASS');
