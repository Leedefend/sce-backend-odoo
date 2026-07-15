'use strict';

const { URL } = require('url');

const ONLINE_CONFIRM_VALUE = 'ONLINE_CAPTURE_AUTHORIZED';
const PLACEHOLDERS = new Set(['', '...', 'changeme', 'example', 'password', 'placeholder', 'redacted', 'username']);

function clean(value) {
  return String(value || '').trim();
}

function origin(value) {
  try {
    const parsed = new URL(clean(value));
    if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password || parsed.search || parsed.hash) return '';
    return parsed.origin.toLowerCase();
  } catch {
    return '';
  }
}

function isPlaceholder(value) {
  const normalized = clean(value).toLowerCase();
  return PLACEHOLDERS.has(normalized)
    || normalized.startsWith('<')
    || normalized.startsWith('${')
    || normalized.includes('provided-via-secret');
}

function requireOnlineCapture(system, env = process.env) {
  const contract = system === 'scbsly'
    ? { base: 'SCBSLY_BASE_URL', username: 'SCBSLY_USERNAME', password: 'SCBSLY_PASSWORD' }
    : { base: 'OLD_SCBS_BASE_URL', username: 'OLD_SCBS_USERNAME', password: 'OLD_SCBS_PASSWORD' };
  const reasons = [];
  if (clean(env.SCBS_CAPTURE_MODE).toLowerCase() !== 'online') reasons.push(`online_mode_required:${system}`);
  if (clean(env.SCBS_ONLINE_CAPTURE_CONFIRM) !== ONLINE_CONFIRM_VALUE) reasons.push('missing_or_invalid:SCBS_ONLINE_CAPTURE_CONFIRM');
  for (const name of [contract.base, contract.username, contract.password]) {
    if (!clean(env[name])) reasons.push(`missing:${name}`);
  }
  for (const name of [contract.username, contract.password]) {
    if (clean(env[name]) && isPlaceholder(env[name])) reasons.push(`placeholder:${name}`);
  }
  const requestedOrigin = origin(env[contract.base]);
  const allowed = new Set(clean(env.SCBS_CAPTURE_DESTINATION_ALLOWLIST).split(',').map(origin).filter(Boolean));
  if (!requestedOrigin) reasons.push(`invalid:${contract.base}`);
  else if (!allowed.has(requestedOrigin)) reasons.push(`destination_not_allowed:${contract.base}`);
  if (reasons.length) {
    const error = new Error(`online capture preflight failed: ${reasons.join(', ')}`);
    error.code = 78;
    error.reasons = reasons;
    throw error;
  }
  return {
    baseUrl: clean(env[contract.base]).replace(/\/$/, ''),
    username: clean(env[contract.username]),
    password: clean(env[contract.password]),
  };
}

module.exports = { ONLINE_CONFIRM_VALUE, requireOnlineCapture };
