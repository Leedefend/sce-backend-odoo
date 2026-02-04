import { capabilityTooltip as capabilityTooltipCore, evaluateCapabilityPolicy as evaluateCapabilityPolicyCore } from './capabilityPolicyCore';

export type CapabilityPolicyState = 'enabled' | 'disabled_capability' | 'disabled_permission';

export type CapabilityPolicy = {
  state: CapabilityPolicyState;
  missing: string[];
};

export function evaluateCapabilityPolicy(options: {
  source?: unknown;
  required?: string[];
  available?: string[] | null;
  groups?: string[];
  userGroups?: string[];
}): CapabilityPolicy {
  return evaluateCapabilityPolicyCore(options) as CapabilityPolicy;
}

export function capabilityTooltip(policy: CapabilityPolicy) {
  return capabilityTooltipCore(policy);
}
