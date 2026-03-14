export type SectionTag = 'header' | 'section' | 'details' | 'div';

export type SectionLayoutConfig = {
  enabled: boolean;
  tag: SectionTag | '';
  open: boolean | null;
};

function toText(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

export function buildSectionLayoutMap(rawSections: unknown): Map<string, SectionLayoutConfig> {
  const source = Array.isArray(rawSections) ? rawSections : [];
  const map = new Map<string, SectionLayoutConfig>();
  source.forEach((item) => {
    if (!item || typeof item !== 'object') return;
    const row = item as Record<string, unknown>;
    const key = toText(row.key).trim();
    if (!key) return;
    const tagRaw = toText(row.tag).toLowerCase();
    const tag = (
      tagRaw === 'header'
      || tagRaw === 'section'
      || tagRaw === 'details'
      || tagRaw === 'div'
    ) ? tagRaw : '';
    map.set(key, {
      enabled: row.enabled === true,
      tag,
      open: typeof row.open === 'boolean' ? row.open : null,
    });
  });
  return map;
}

export function sectionEnabled(sectionMap: Map<string, SectionLayoutConfig>, key: string, fallback = true): boolean {
  if (!sectionMap.size) return fallback;
  return sectionMap.get(key)?.enabled ?? fallback;
}

export function sectionTagIs(
  sectionMap: Map<string, SectionLayoutConfig>,
  key: string,
  expected: SectionTag,
  fallback = true,
): boolean {
  if (!sectionMap.size) return fallback;
  return sectionMap.get(key)?.tag === expected;
}

export function sectionOpenDefault(
  sectionMap: Map<string, SectionLayoutConfig>,
  key: string,
  fallback = false,
): boolean {
  if (!sectionMap.size) return fallback;
  return sectionMap.get(key)?.open === true;
}

