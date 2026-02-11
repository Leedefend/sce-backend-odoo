'use strict';

function isModelMissing(resp) {
  const msg = String((((resp || {}).body || {}).error || {}).message || '');
  return (
    msg.includes('未知模型') ||
    msg.toLowerCase().includes('unknown model') ||
    /^'[a-z0-9_.]+'$/i.test(msg.trim())
  );
}

async function probeModels(requestJson, intentUrl, authHeaders, models) {
  const available = [];
  const missing = [];
  const results = [];
  for (const model of models || []) {
    const resp = await requestJson(
      intentUrl,
      {
        intent: 'api.data',
        params: {
          op: 'list',
          model: model,
          fields: ['id'],
          domain: [],
          limit: 1,
        },
      },
      authHeaders
    );
    const miss = isModelMissing(resp);
    if (miss) missing.push(model);
    else available.push(model);
    results.push({
      model: model,
      status: resp && typeof resp.status === 'number' ? resp.status : 0,
      missing: miss,
      ok: !!(resp && resp.body && resp.body.ok === true),
    });
  }
  return { available, missing, results };
}

function assertRequiredModels(strictEnabled, requiredAny, available, label) {
  if (!strictEnabled) return;
  const ok = (requiredAny || []).some((m) => (available || []).indexOf(m) >= 0);
  if (!ok) {
    throw new Error((label || 'strict check') + ' model unavailable: ' + (requiredAny || []).join(', '));
  }
}

module.exports = {
  isModelMissing,
  probeModels,
  assertRequiredModels,
};
