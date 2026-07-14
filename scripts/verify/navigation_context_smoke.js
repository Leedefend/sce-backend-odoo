#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ts = require('../../frontend/apps/web/node_modules/typescript');

const ROOT = path.resolve(__dirname, '..', '..');
const SOURCE = path.join(ROOT, 'frontend/apps/web/src/app/navigationContext.ts');

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
  vm.runInNewContext(transpiled, { module, exports: module.exports }, { filename: SOURCE });
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
  assertDeepEqual(
    runtime.buildBusinessCategoryCreateNavQuery({
      categoryCode: 'project',
      option: {
        label: '项目办理',
        categoryId: 18,
        defaultValues: {
          project_id: 7,
          active: true,
          ignored_object: { id: 1 },
          ignored_array: [1],
          ignored_null: null,
        },
      },
      fallbackLabel: 'fallback',
    }),
    {
      current_business_category_code: 'project',
      default_business_category_code: 'project',
      current_business_category_label: '项目办理',
      default_business_category_label: '项目办理',
      ctx_source: 'business_category_create_picker',
      default_business_category_id: '18',
      default_project_id: '7',
      default_active: 'true',
    },
    'business category create query',
  );

  assertDeepEqual(
    runtime.buildBusinessCategoryCreateNavQuery({ categoryCode: '  ', fallbackLabel: 'fallback' }),
    undefined,
    'empty category code',
  );

  console.log('[navigation_context_smoke] PASS');
}

main();
