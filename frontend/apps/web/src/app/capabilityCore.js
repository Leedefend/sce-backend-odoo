export function normalizeCapabilities(input) {
  if (Array.isArray(input)) {
    return input.filter((item) => typeof item === 'string' && item.trim().length > 0);
  }
  if (typeof input === 'string' && input.trim().length > 0) {
    return [input.trim()];
  }
  return [];
}

export function getRequiredCapabilities(source) {
  if (!source || typeof source !== 'object') {
    return [];
  }
  const raw = source;
  return [
    ...normalizeCapabilities(raw.capabilities),
    ...normalizeCapabilities(raw.required_capabilities),
    ...normalizeCapabilities(raw.requiredCapabilities),
  ];
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

export function checkCapabilities(required, available) {
  const requiredCaps = normalizeCapabilities(required);
  const availableCaps = asArray(available);
  const missing = requiredCaps.filter((cap) => !availableCaps.includes(cap));
  return { ok: missing.length === 0, missing };
}
