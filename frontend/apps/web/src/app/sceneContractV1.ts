import type { PageOrchestrationContract } from './pageOrchestration';

type SceneContractNormalizeOptions = {
  pageType?: string;
  layoutMode?: string;
};

function toText(value: unknown): string {
  if (typeof value === 'string') return value;
  if (value === null || value === undefined) return '';
  return String(value);
}

function toObject(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? value as Record<string, unknown> : {};
}

export function normalizeSceneContractV1ToPageContract(
  raw: unknown,
  options: SceneContractNormalizeOptions = {},
): PageOrchestrationContract {
  if (!raw || typeof raw !== 'object') return {} as PageOrchestrationContract;
  const source = raw as Record<string, unknown>;
  if (toText(source.contract_version) !== 'v1') return {} as PageOrchestrationContract;

  const zones = Array.isArray(source.zones) ? source.zones as Array<Record<string, unknown>> : [];
  const blocks = source.blocks && typeof source.blocks === 'object'
    ? source.blocks as Record<string, Record<string, unknown>>
    : {};
  if (!zones.length || !Object.keys(blocks).length) return {} as PageOrchestrationContract;

  const normalizedZones = zones.map((zone, zoneIndex) => {
    const blockKeys = Array.isArray(zone.block_keys) ? zone.block_keys : [];
    const normalizedBlocks = blockKeys
      .map((key, blockIndex) => {
        const blockKey = toText(key).trim();
        const block = (blockKey ? blocks[blockKey] : {}) || {};
        return {
          key: blockKey || `block_${zoneIndex + 1}_${blockIndex + 1}`,
          block_type: toText(block.block_type || block.type || 'record_summary'),
          title: toText(block.title || blockKey),
          priority: Number(block.priority || (100 - blockIndex)),
          data_source: toText(block.data_source || `ds_${blockKey || `${zoneIndex + 1}_${blockIndex + 1}`}`),
          section_key: toText(block.section_key),
          source_path: toText(block.source_path),
          zone: toText(block.zone || zone.zone_type),
          visible: block.visible !== false,
          focus: block.focus === true,
        };
      })
      .filter((row) => toText(row.key).trim());
    return {
      key: toText(zone.key || `zone_${zoneIndex + 1}`),
      title: toText(zone.title),
      zone_type: toText(zone.zone_type || 'secondary'),
      display_mode: toText(zone.display_mode || 'stack'),
      priority: Number(zone.priority || 0),
      blocks: normalizedBlocks,
    };
  });

  const page = toObject(source.page);
  const scene = toObject(source.scene);
  return {
    contract_version: 'page_orchestration_v1',
    scene_key: toText(scene.scene_key),
    page: {
      key: toText(page.key),
      title: toText(page.title),
      page_type: options.pageType || 'workspace',
      layout_mode: options.layoutMode || 'workspace',
    },
    zones: normalizedZones,
  } as PageOrchestrationContract;
}

export function resolvePageOrchestrationContractFromSceneV1(
  sceneContractV1Raw: unknown,
  pageOrchestrationV1Raw: unknown,
  options: SceneContractNormalizeOptions = {},
): PageOrchestrationContract {
  const normalized = normalizeSceneContractV1ToPageContract(sceneContractV1Raw, options);
  if (Array.isArray(normalized.zones) && normalized.zones.length > 0) {
    return normalized;
  }
  return pageOrchestrationV1Raw && typeof pageOrchestrationV1Raw === 'object'
    ? pageOrchestrationV1Raw as PageOrchestrationContract
    : {} as PageOrchestrationContract;
}

