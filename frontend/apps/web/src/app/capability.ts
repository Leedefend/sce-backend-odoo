import {
  checkCapabilities as checkCapabilitiesCore,
  getRequiredCapabilities as getRequiredCapabilitiesCore,
  normalizeCapabilities as normalizeCapabilitiesCore,
} from './capabilityCore';

export interface CapabilityCheck {
  ok: boolean;
  missing: string[];
}

export function normalizeCapabilities(input: unknown): string[] {
  return normalizeCapabilitiesCore(input);
}

export function getRequiredCapabilities(source: unknown): string[] {
  return getRequiredCapabilitiesCore(source);
}

export function checkCapabilities(required: unknown, available: string[] | null | undefined): CapabilityCheck {
  return checkCapabilitiesCore(required, available);
}
