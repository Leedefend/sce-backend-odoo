#!/usr/bin/env node
'use strict';

const path = require('path');

const modulePath = path.resolve(__dirname, '../../frontend/apps/web/src/app/view_state.js');
// eslint-disable-next-line import/no-dynamic-require, global-require
const { deriveListStatus, deriveRecordStatus } = require(modulePath);

function assertEqual(label, actual, expected) {
  if (actual !== expected) {
    console.error(`FAIL: ${label} -> expected=${expected} actual=${actual}`);
    return false;
  }
  console.log(`PASS: ${label}`);
  return true;
}

let ok = true;

ok = assertEqual('Action ok', deriveListStatus({ error: '', recordsLength: 3 }), 'ok') && ok;
ok = assertEqual('Action empty', deriveListStatus({ error: '', recordsLength: 0 }), 'empty') && ok;
ok = assertEqual('Action error', deriveListStatus({ error: 'boom', recordsLength: 0 }), 'error') && ok;

ok = assertEqual('Record ok', deriveRecordStatus({ error: '', fieldsLength: 5 }), 'ok') && ok;
ok = assertEqual('Record empty', deriveRecordStatus({ error: '', fieldsLength: 0 }), 'empty') && ok;
ok = assertEqual('Record error', deriveRecordStatus({ error: 'boom', fieldsLength: 0 }), 'error') && ok;

if (!ok) {
  process.exit(1);
}
