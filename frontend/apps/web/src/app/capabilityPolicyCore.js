import { checkCapabilities, getRequiredCapabilities } from './capabilityCore.js';

export function evaluateCapabilityPolicy(options = {}) {
  const requiredCaps = options.required ?? getRequiredCapabilities(options.source);
  const capCheck = checkCapabilities(requiredCaps, options.available);
  if (!capCheck.ok) {
    return { state: 'disabled_capability', missing: capCheck.missing };
  }
  const groups = Array.isArray(options.groups) ? options.groups : [];
  const userGroups = Array.isArray(options.userGroups) ? options.userGroups : [];
  if (groups.length && !groups.some((g) => userGroups.includes(g))) {
    return { state: 'disabled_permission', missing: [] };
  }
  return { state: 'enabled', missing: [] };
}

export function capabilityTooltip(policy) {
  if (policy.state === 'disabled_capability') {
    return `Missing capabilities: ${policy.missing.join(', ')}`;
  }
  if (policy.state === 'disabled_permission') {
    return 'Permission required';
  }
  return '';
}
