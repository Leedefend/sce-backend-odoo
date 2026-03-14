import type { SemanticProgress, SemanticTone } from './pageOrchestration';

export type HomeSemantic = {
  zone: string;
  focus: boolean;
  tone: SemanticTone;
  progress: SemanticProgress;
};

function toText(value: unknown): string {
  const text = String(value ?? '').trim();
  if (!text || text.toLowerCase() === 'undefined' || text.toLowerCase() === 'null') return '';
  return text;
}

function toBlockRows(raw: unknown): Record<string, unknown>[] {
  const source = Array.isArray(raw) ? raw : [];
  return source
    .map((item) => (item && typeof item === 'object' ? item as Record<string, unknown> : null))
    .filter((item): item is Record<string, unknown> => Boolean(item));
}

function resolveSectionKey(block: Record<string, unknown>): string {
  const sourcePath = toText(block.source_path);
  const sectionKey = toText(block.section_key);
  if (sectionKey) return sectionKey;
  if (!sourcePath) return '';
  return sourcePath.split('.')[0] || '';
}

export function flattenHomeOrchestrationBlocks(
  pageOrchestrationV1: Record<string, unknown>,
  pageOrchestrationLegacy: Record<string, unknown>,
  dataSources: Record<string, unknown>,
): Record<string, unknown>[] {
  const zones = Array.isArray(pageOrchestrationV1.zones)
    ? pageOrchestrationV1.zones
    : [];
  const hasV1Zones = zones.length > 0;
  const flattenedV1: Record<string, unknown>[] = [];

  zones.forEach((zone) => {
    if (!zone || typeof zone !== 'object') return;
    const zoneRow = zone as Record<string, unknown>;
    const zoneType = toText(zoneRow.zone_type);
    const blocks = toBlockRows(zoneRow.blocks);
    blocks.forEach((blockRow) => {
      const sectionKey = toText(blockRow.section_key);
      const dataSourceKey = toText(blockRow.data_source);
      if (!sectionKey || !dataSourceKey) return;
      const dataSource = dataSources[dataSourceKey];
      if (!dataSource || typeof dataSource !== 'object') return;
      const sourceType = toText((dataSource as Record<string, unknown>).source_type);
      if (!sourceType) return;
      flattenedV1.push({
        ...blockRow,
        zone: toText(blockRow.zone) || zoneType || 'support',
      });
    });
  });

  if (hasV1Zones) return flattenedV1;
  return toBlockRows(pageOrchestrationLegacy.blocks);
}

export function deriveHomeSectionMaps(
  blocks: Record<string, unknown>[],
  normalizeTone: (value: unknown, fallback?: SemanticTone) => SemanticTone,
  normalizeProgress: (value: unknown, fallback?: SemanticProgress) => SemanticProgress,
): {
  orderMap: Map<string, number>;
  semanticMap: Map<string, HomeSemantic>;
} {
  const orderMap = new Map<string, number>();
  const semanticMap = new Map<string, HomeSemantic>();

  blocks.forEach((block, idx) => {
    const visible = typeof block.visible === 'boolean' ? block.visible : true;
    if (!visible) return;

    const sectionKey = resolveSectionKey(block);
    if (!sectionKey) return;

    if (!orderMap.has(sectionKey)) {
      const orderRaw = Number(block.order);
      const order = Number.isFinite(orderRaw) && orderRaw > 0 ? Math.trunc(orderRaw) : idx + 1;
      orderMap.set(sectionKey, order);
    }

    if (!semanticMap.has(sectionKey)) {
      semanticMap.set(sectionKey, {
        zone: toText(block.zone) || 'support',
        focus: block.focus === true,
        tone: normalizeTone(block.tone, 'neutral'),
        progress: normalizeProgress(block.progress, 'running'),
      });
    }
  });

  return { orderMap, semanticMap };
}

