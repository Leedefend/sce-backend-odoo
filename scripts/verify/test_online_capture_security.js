#!/usr/bin/env node
'use strict';

const assert = require('assert');
const { ONLINE_CONFIRM_VALUE, requireOnlineCapture } = require('./online_capture_security');

function baseEnv() {
  return {
    SCBS_CAPTURE_MODE: 'online',
    SCBS_ONLINE_CAPTURE_CONFIRM: ONLINE_CONFIRM_VALUE,
    SCBS_CAPTURE_DESTINATION_ALLOWLIST: 'http://127.0.0.1:18999',
    OLD_SCBS_BASE_URL: 'http://127.0.0.1:18999/capture',
    OLD_SCBS_USERNAME: 'local-fixture-user',
    OLD_SCBS_PASSWORD: 'local-fixture-secret',
  };
}

assert.throws(() => requireOnlineCapture('scbs', {}), /online_mode_required:scbs/);

const missingPassword = baseEnv();
delete missingPassword.OLD_SCBS_PASSWORD;
assert.throws(() => requireOnlineCapture('scbs', missingPassword), /missing:OLD_SCBS_PASSWORD/);

const placeholder = baseEnv();
placeholder.OLD_SCBS_PASSWORD = '<provided-via-secret-environment>';
assert.throws(() => requireOnlineCapture('scbs', placeholder), /placeholder:OLD_SCBS_PASSWORD/);

const config = requireOnlineCapture('scbs', baseEnv());
assert.strictEqual(config.baseUrl, 'http://127.0.0.1:18999/capture');
assert.strictEqual(config.username, 'local-fixture-user');

const crossSystem = baseEnv();
crossSystem.SCBSLY_BASE_URL = crossSystem.OLD_SCBS_BASE_URL;
assert.throws(() => requireOnlineCapture('scbsly', crossSystem), /missing:SCBSLY_USERNAME/);

process.stdout.write('online capture JavaScript security tests passed\n');
