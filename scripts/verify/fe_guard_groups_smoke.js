#!/usr/bin/env node
'use strict';

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function safeIncludes(arr, value) {
  return asArray(arr).includes(value);
}

function getGroups(obj) {
  if (!obj) return [];
  return asArray(obj.groups ?? obj.group_xmlids);
}

function assertEqual(label, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (!ok) {
    throw new Error(`${label} expected=${JSON.stringify(expected)} actual=${JSON.stringify(actual)}`);
  }
  console.log(`PASS: ${label}`);
}

function main() {
  assertEqual('asArray(undefined)', asArray(undefined), []);
  assertEqual('asArray(null)', asArray(null), []);
  assertEqual('asArray([1])', asArray([1]), [1]);
  assertEqual('safeIncludes(undefined,false)', safeIncludes(undefined, 'x'), false);
  assertEqual('safeIncludes([a],a)', safeIncludes(['a'], 'a'), true);
  assertEqual('getGroups(undefined)', getGroups(undefined), []);
  assertEqual('getGroups(groups)', getGroups({ groups: ['g1'] }), ['g1']);
  assertEqual('getGroups(group_xmlids)', getGroups({ group_xmlids: ['g2'] }), ['g2']);
}

try {
  main();
} catch (err) {
  console.error(`FAIL: ${err.message}`);
  process.exit(1);
}
