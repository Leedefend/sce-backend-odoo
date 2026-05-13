export const LITE_PREVIEW_LEGACY_FALLBACK_MODE = 'legacy_default';

export type LitePreviewFallbackMode = typeof LITE_PREVIEW_LEGACY_FALLBACK_MODE;

export function isLitePreviewLegacyFallbackMode(value: unknown): value is LitePreviewFallbackMode {
  return value === LITE_PREVIEW_LEGACY_FALLBACK_MODE;
}
