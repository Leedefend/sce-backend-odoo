#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ts = require('../../frontend/apps/web/node_modules/typescript');

const ROOT = path.resolve(__dirname, '..', '..');
const SOURCE = path.join(
  ROOT,
  'frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts',
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
      if (name.endsWith('routeQuery')) {
        return { buildEntryTargetRouteTarget: () => ({ name: 'action', query: {} }) };
      }
      throw new Error(`unexpected require: ${name}`);
    },
  };
  vm.runInNewContext(transpiled, sandbox, { filename: SOURCE });
  return module.exports;
}

function main() {
  const runtime = loadRuntime();
  if (runtime.stableActionContractId('  Project/Done ', 'fallback') !== 'Project.Done') {
    throw new Error('stableActionContractId must normalize spaces and slashes');
  }
  if (runtime.stableActionContractId('123', 'fallback') !== 'id.123') {
    throw new Error('stableActionContractId must prefix non-alpha ids');
  }

  const visible = runtime.applyActionViewV2ButtonStatus(
    { key: 'Project/Done', enabled: true, hint: '' },
    { 'btn.Project.Done': { visible: true, disabled: true, reasonCode: 'policy_blocked' } },
  );
  if (!visible || visible.enabled !== false || visible.hint !== 'policy_blocked') {
    throw new Error('applyActionViewV2ButtonStatus must apply disabled status by stable button id');
  }

  const hidden = runtime.applyActionViewV2ButtonStatus(
    { key: 'archive', enabled: true, hint: '' },
    { archive: { visible: false, disabled: false } },
  );
  if (hidden !== null) {
    throw new Error('applyActionViewV2ButtonStatus must remove invisible buttons');
  }

  const untouched = runtime.applyActionViewV2ButtonStatus(
    { key: 'open', enabled: true, hint: 'keep' },
    {},
  );
  if (!untouched || untouched.enabled !== true || untouched.hint !== 'keep') {
    throw new Error('applyActionViewV2ButtonStatus must preserve buttons without status');
  }

  console.log('[action_view_contract_action_runtime_smoke] PASS');
}

main();
