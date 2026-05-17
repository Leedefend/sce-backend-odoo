#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ts = require('../../frontend/apps/web/node_modules/typescript');

const ROOT = path.resolve(__dirname, '..', '..');
const SOURCE = path.join(
  ROOT,
  'frontend/apps/web/src/app/action_runtime/useActionViewContractShapeRuntime.ts',
);

function uniqueFields(fields) {
  const seen = new Set();
  const out = [];
  (fields || []).forEach((field) => {
    const name = String(field || '').trim();
    if (name && !seen.has(name)) {
      seen.add(name);
      out.push(name);
    }
  });
  return out;
}

function loadRuntime() {
  const source = fs.readFileSync(SOURCE, 'utf8');
  const transpiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      esModuleInterop: true,
    },
  }).outputText;
  const module = { exports: {} };
  const sandbox = {
    module,
    exports: module.exports,
    require: (name) => {
      if (name === 'vue') return { computed: (fn) => ({ value: fn() }) };
      if (name.endsWith('actionViewRequestRuntime')) return { uniqueFields };
      if (name.endsWith('unifiedPageContractV2')) {
        return {
          collectUnifiedPageContractV2FieldWidgets: () => [],
          collectUnifiedPageContractV2FieldStatus: () => ({}),
          resolveUnifiedPageContractV2: () => null,
        };
      }
      throw new Error(`unexpected require: ${name}`);
    },
  };
  vm.runInNewContext(transpiled, sandbox, { filename: SOURCE });
  return module.exports;
}

function assertDeepEqual(actual, expected, label) {
  const actualJson = JSON.stringify(actual);
  const expectedJson = JSON.stringify(expected);
  if (actualJson !== expectedJson) {
    throw new Error(`${label}: expected ${expectedJson}, got ${actualJson}`);
  }
}

function main() {
  const runtime = loadRuntime();
  const kanban = runtime.extractKanbanFieldsFromContract({
    views: {
      kanban: {
        kanban: {
          fields: ['name'],
          slots: { primary: ['email'], secondary: [{ field: 'phone' }] },
        },
      },
    },
  });
  assertDeepEqual(kanban, ['name', 'email', 'phone'], 'kanban nested fields and slots');

  const calendar = runtime.extractAdvancedViewFieldsFromContract({
    views: {
      calendar: {
        calendar: {
          date_start: 'planned_start',
          date_stop: 'planned_stop',
          resource_slots: { owner: 'user_id' },
          color_slots: { state: 'state' },
        },
      },
    },
  }, 'calendar');
  assertDeepEqual(
    calendar,
    ['planned_start', 'planned_stop', 'user_id', 'state', 'name', 'display_name', 'id'],
    'calendar advanced fields',
  );

  const dashboard = runtime.extractAdvancedViewFieldsFromContract({
    views: {
      dashboard: {
        dashboard: {
          cards: [{ field: 'project_id' }],
          metric_slots: { primary: ['amount_total'] },
          chart_slots: { trend: [{ field: 'date_order' }] },
          navigation_slots: { next: 'project.dashboard.enter' },
        },
      },
    },
  }, 'dashboard');
  assertDeepEqual(
    dashboard,
    ['project_id', 'amount_total', 'date_order', 'name', 'display_name', 'id'],
    'dashboard advanced fields',
  );

  console.log('[action_view_orchestration_contract_shape_smoke] PASS');
}

main();
