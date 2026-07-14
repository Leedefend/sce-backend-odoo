#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ts = require('../../frontend/apps/web/node_modules/typescript');

const ROOT = path.resolve(__dirname, '..', '..');
const SOURCE = path.join(
  ROOT,
  'frontend/apps/web/src/app/runtime/actionViewRouteRuntime.ts',
);

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
      if (name.endsWith('navigationContext')) {
        return { pickContractNavQuery: (_current, patch) => ({ ...patch }) };
      }
      if (name.endsWith('workspaceContext')) {
        return { stripWorkspaceContext: (query) => ({ ...(query || {}) }) };
      }
      if (name.endsWith('actionViewGroupWindowRuntime')) {
        return { serializeGroupPageOffsets: () => '' };
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
  const normalize = runtime.normalizeActivityRuntimeRouteQuery;
  if (typeof normalize !== 'function') {
    throw new Error('normalizeActivityRuntimeRouteQuery must be exported');
  }

  assertDeepEqual(
    normalize({
      search: '  abc  ',
      active_filter: 'active',
      saved_filter: 'mine',
      group_by: 'project_id',
      group_sort: 'DESC',
      group_page: ['  a:1 ', '', 'b:2'],
      ignored: 'drop',
    }),
    {
      search: 'abc',
      active_filter: 'active',
      saved_filter: 'mine',
      group_by: 'project_id',
      group_sort: 'DESC',
      group_page: ['a:1', 'b:2'],
    },
    'whitelist and trim route query',
  );

  assertDeepEqual(
    normalize({
      q: '  free text ',
      active_filter: 'deleted',
      group_sort: 'sideways',
      group_offset: 5,
      group_fp: ' fp ',
    }),
    {
      q: 'free text',
      group_offset: '5',
      group_fp: 'fp',
    },
    'drop invalid active filter and group sort',
  );

  assertDeepEqual(
    normalize({
      search: '',
      group_collapsed: [' ', 'group-a'],
      group_wid: null,
      group_wdg: undefined,
      group_wik: ' key ',
    }),
    {
      group_collapsed: ['group-a'],
      group_wik: 'key',
    },
    'drop empty scalar and array values',
  );

  console.log('[action_view_route_runtime_smoke] PASS');
}

main();
