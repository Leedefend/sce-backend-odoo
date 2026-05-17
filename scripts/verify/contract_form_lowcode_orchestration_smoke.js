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
assertContains('function lowCodeScopedContractName(', 'missing scoped low-code contract name builder');
assertContains('view_orchestration:${modelName}:form:action:', 'low-code contract name must include action/view scope');
assertContains('view_orchestration: buildLowCodeViewOrchestration()', 'low-code save must persist view_orchestration');
assertContains("view_type: 'form'", 'low-code save must persist form view_type scope');
assertContains("params: { ...base, model: modelName, view_type: 'form' }", 'low-code contract list must use current form scope');
assertContains("params: { ...base, model: modelName, name, view_type: 'form' }", 'low-code contract get must use current form scope');
assertContains("params: { ...base, name, model: modelName, view_type: 'form' }", 'low-code publish/rollback must use current form scope');
assertContains('collectLowCodeLayoutFromViewOrchestration', 'low-code load must hydrate from view_orchestration');
assertContains("views.form = {", 'low-code orchestration must build form view spec');
assertContains("views.tree = {", 'low-code orchestration must build tree view spec');
assertContains("views.kanban = {", 'low-code orchestration must build kanban view spec');

console.log('[contract_form_lowcode_orchestration_smoke] PASS');
