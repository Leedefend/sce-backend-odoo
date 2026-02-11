'use strict';

function extractTraceId(body) {
  if (!body || typeof body !== 'object') return '';
  const meta = body.meta && typeof body.meta === 'object' ? body.meta : {};
  return String(meta.trace_id || meta.traceId || body.trace_id || body.traceId || '');
}

function assertIntentEnvelope(resp, intentName, options) {
  const opts = options || {};
  const requireTrace = opts.requireTrace !== false;
  const allowMetaIntentAliases = Array.isArray(opts.allowMetaIntentAliases) ? opts.allowMetaIntentAliases : [];

  if (!resp || resp.status >= 400) {
    const status = resp && typeof resp.status !== 'undefined' ? resp.status : 0;
    throw new Error(intentName + ' failed: status=' + status);
  }
  if (!resp.body || typeof resp.body !== 'object') {
    throw new Error(intentName + ' missing response body');
  }
  if (resp.body.ok !== true) {
    throw new Error(intentName + ' missing ok=true envelope');
  }

  const traceId = extractTraceId(resp.body);
  if (requireTrace && !traceId) {
    throw new Error(intentName + ' missing meta.trace_id');
  }

  const meta = resp.body.meta && typeof resp.body.meta === 'object' ? resp.body.meta : {};
  const metaIntent = String(meta.intent || '');
  if (metaIntent) {
    const allowed = [intentName].concat(allowMetaIntentAliases);
    if (allowed.indexOf(metaIntent) < 0) {
      throw new Error(intentName + ' meta.intent mismatch: ' + metaIntent);
    }
  }

  return {
    traceId: traceId,
  };
}

module.exports = {
  extractTraceId,
  assertIntentEnvelope,
};
