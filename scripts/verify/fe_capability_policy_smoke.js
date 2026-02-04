#!/usr/bin/env node
'use strict';

const path = require('path');
const { pathToFileURL } = require('url');

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

async function main() {
  const modulePath = pathToFileURL(
    path.resolve(__dirname, '../../frontend/apps/web/src/app/capabilityPolicyCore.js'),
  ).href;
  const policy = await import(modulePath);
  const { evaluateCapabilityPolicy, capabilityTooltip } = policy;

  const base = evaluateCapabilityPolicy({ required: ['cap.a'], available: ['cap.a', 'cap.b'] });
  assert(base.state === 'enabled', 'expected enabled when capabilities satisfied');

  const missing = evaluateCapabilityPolicy({ required: ['cap.a'], available: ['cap.b'] });
  assert(missing.state === 'disabled_capability', 'expected disabled_capability');
  assert(missing.missing.includes('cap.a'), 'expected missing cap.a');
  assert(capabilityTooltip(missing).includes('Missing capabilities'), 'expected missing tooltip');

  const perm = evaluateCapabilityPolicy({ required: [], available: [], groups: ['g1'], userGroups: ['g2'] });
  assert(perm.state === 'disabled_permission', 'expected disabled_permission when groups mismatch');
  assert(capabilityTooltip(perm) === 'Permission required', 'expected permission tooltip');

  console.log('[fe_capability_policy_smoke] PASS');
}

main().catch((err) => {
  console.error(`[fe_capability_policy_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
