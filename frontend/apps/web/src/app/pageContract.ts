import { computed, watchEffect } from 'vue';
import { useSessionStore, type PageContract, type SceneConsumerRuntime } from '../stores/session';

function asText(value: unknown): string {
  return typeof value === 'string' ? value : '';
}
function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? value as Record<string, unknown> : {};
}
function asTextList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((item) => asText(item)).filter(Boolean)
    : [];
}

type SectionTag = 'header' | 'section' | 'details' | 'div' | '';
type SectionConfig = { enabled: boolean; order: number; tag: SectionTag; open: boolean | null };
type GlobalActionConfig = { key: string; label: string; intent: string };

function contractLooksStale(pageKey: string, contract: unknown): boolean {
  const normalizedPageKey = asText(pageKey).trim().toLowerCase();
  const row = contract && typeof contract === 'object' ? contract as Record<string, unknown> : {};
  const orchestration = row.page_orchestration_v1 && typeof row.page_orchestration_v1 === 'object'
    ? row.page_orchestration_v1 as Record<string, unknown>
    : {};
  const sceneContractV1 = row.scene_contract_v1 && typeof row.scene_contract_v1 === 'object'
    ? row.scene_contract_v1 as Record<string, unknown>
    : {};
  const page = orchestration.page && typeof orchestration.page === 'object'
    ? orchestration.page as Record<string, unknown>
    : {};
  const zones = Array.isArray(orchestration.zones) ? orchestration.zones : [];
  if (normalizedPageKey !== 'my_work') return false;
  const title = asText(page.title).trim();
  const leaked = new Set(['页面头部', '主体内容', '辅助信息', '扩展信息', 'hero', 'todo_focus', 'list_main', 'my_work-primary']);
  const staleHeroTitles = new Set(['我的工作']);
  if (!Object.keys(orchestration).length || zones.length === 0) return true;
  if (leaked.has(title)) return true;
  for (const zone of zones) {
    const zoneRow = zone && typeof zone === 'object' ? zone as Record<string, unknown> : {};
    const zoneTitle = asText(zoneRow.title).trim();
    const zoneDesc = asText(zoneRow.description).trim();
    if (leaked.has(zoneTitle) || leaked.has(zoneDesc)) return true;
    const blocks = Array.isArray(zoneRow.blocks) ? zoneRow.blocks : [];
    for (const block of blocks) {
      const blockRow = block && typeof block === 'object' ? block as Record<string, unknown> : {};
      const blockTitle = asText(blockRow.title).trim();
      if (leaked.has(blockTitle) || staleHeroTitles.has(blockTitle)) return true;
    }
  }
  const sceneZones = Array.isArray(sceneContractV1.zones) ? sceneContractV1.zones : [];
  for (const zone of sceneZones) {
    const zoneRow = zone && typeof zone === 'object' ? zone as Record<string, unknown> : {};
    const zoneKey = asText(zoneRow.key || zoneRow.zone_key).trim();
    const zoneTitle = asText(zoneRow.title || zoneRow.label).trim();
    if (leaked.has(zoneKey) || leaked.has(zoneTitle)) return true;
  }
  return false;
}

export function usePageContract(pageKey: string) {
  const session = useSessionStore();
  const normalizedPageKey = asText(pageKey).trim().toLowerCase();
  watchEffect(() => {
    if (!normalizedPageKey || !session.token) return;
    const cached = session.pageContracts?.[normalizedPageKey];
    const shouldForceRefresh = contractLooksStale(normalizedPageKey, cached);
    if (cached && Object.keys(cached).length > 0 && !shouldForceRefresh) return;
    void session.ensurePageContract(normalizedPageKey, shouldForceRefresh).catch(() => {});
  });
  const contract = computed<PageContract>(() => session.pageContracts?.[normalizedPageKey] || {});
  const sceneContractV1 = computed<Record<string, unknown>>(() => {
    const raw = contract.value?.scene_contract_v1;
    if (!raw || typeof raw !== 'object') return {};
    if (asText((raw as Record<string, unknown>).contract_version) !== 'v1') return {};
    return raw as Record<string, unknown>;
  });
  const texts = computed<Record<string, unknown>>(() => {
    const raw = contract.value?.texts;
    return raw && typeof raw === 'object' ? raw : {};
  });
  const orchestrationDataSources = computed<Record<string, unknown>>(() => {
    const raw = contract.value?.page_orchestration_v1?.data_sources;
    if (raw && typeof raw === 'object') return raw as Record<string, unknown>;
    const extensionSources = asRecord(sceneContractV1.value.extensions).data_sources;
    return extensionSources && typeof extensionSources === 'object'
      ? extensionSources as Record<string, unknown>
      : {};
  });
  const sections = computed<Map<string, SectionConfig>>(() => {
    const fromV1: Array<Record<string, unknown>> = [];
    const orchestrationV1 = contract.value?.page_orchestration_v1;
    const zones = Array.isArray(orchestrationV1?.zones) ? orchestrationV1.zones : [];
    const hasV1Zones = zones.length > 0;
    const dataSourcesRow = orchestrationDataSources.value;
    zones.forEach((zone) => {
      if (!zone || typeof zone !== 'object') return;
      const zoneRow = zone as Record<string, unknown>;
      const blocks = Array.isArray(zoneRow.blocks) ? zoneRow.blocks : [];
      blocks.forEach((block) => {
        if (!block || typeof block !== 'object') return;
        const row = block as Record<string, unknown>;
        const sectionKey = asText(row.section_key);
        if (!sectionKey) return;
        const dataSourceKey = asText(row.data_source);
        if (!dataSourceKey) return;
        const dataSource = dataSourcesRow[dataSourceKey];
        if (!dataSource || typeof dataSource !== 'object') return;
        const sourceType = asText((dataSource as Record<string, unknown>).source_type);
        if (!sourceType) return;
        const payload = (row.payload && typeof row.payload === 'object') ? row.payload as Record<string, unknown> : {};
        const tag = asText(payload.tag) || 'section';
        const priorityRaw = Number(row.priority);
        const order = Number.isFinite(priorityRaw) && priorityRaw > 0 ? Math.max(1, 101 - Math.trunc(priorityRaw)) : 999;
        fromV1.push({
          key: sectionKey,
          enabled: payload.enabled !== false,
          order,
          tag,
          open: payload.open === true,
        });
      });
    });
    const fromSceneV1: Array<Record<string, unknown>> = [];
    const sceneZones = Array.isArray(sceneContractV1.value.zones)
      ? sceneContractV1.value.zones as Array<Record<string, unknown>>
      : [];
    sceneZones.forEach((zone, idx) => {
      if (!zone || typeof zone !== 'object') return;
      const zoneKey = asText(zone.key || zone.zone_key).trim();
      if (!zoneKey) return;
      const priorityRaw = Number(zone.priority);
      const order = Number.isFinite(priorityRaw) && priorityRaw > 0
        ? Math.max(1, 101 - Math.trunc(priorityRaw))
        : (idx + 1);
      fromSceneV1.push({
        key: zoneKey,
        enabled: true,
        order,
        tag: 'section',
      });
    });
    const raw = hasV1Zones
      ? fromV1
      : (
        fromSceneV1.length
          ? fromSceneV1
          : (Array.isArray(contract.value?.sections) ? contract.value.sections : [])
      );
    const map = new Map<string, SectionConfig>();
    raw.forEach((item, idx) => {
      const key = asText(item?.key);
      if (!key) return;
      if (map.has(key)) return;
      const row = (item && typeof item === 'object') ? item as Record<string, unknown> : {};
      const tagRaw = asText(row.tag).toLowerCase();
      const tag: SectionTag = (
        tagRaw === 'header'
        || tagRaw === 'section'
        || tagRaw === 'details'
        || tagRaw === 'div'
      ) ? tagRaw : '';
      const orderRaw = Number(row.order);
      map.set(key, {
        enabled: row.enabled === true,
        order: Number.isFinite(orderRaw) && orderRaw > 0 ? Math.trunc(orderRaw) : idx + 1,
        tag,
        open: typeof row.open === 'boolean' ? row.open : null,
      });
    });
    return map;
  });
  const actions = computed<Record<string, unknown>>(() => {
    const raw = contract.value?.actions;
    return raw && typeof raw === 'object' ? raw : {};
  });
  const consumerRuntime = computed<SceneConsumerRuntime>(() => {
    const diagnostics = contract.value?.scene_contract_v1?.diagnostics;
    if (!diagnostics || typeof diagnostics !== 'object') return {};
    const runtime = (diagnostics as Record<string, unknown>).consumer_runtime;
    return runtime && typeof runtime === 'object' ? runtime as SceneConsumerRuntime : {};
  });
  const sceneActionSchema = computed<Record<string, Record<string, unknown>>>(() => {
    const rawActions = asRecord(sceneContractV1.value.actions);
    const map: Record<string, Record<string, unknown>> = {};
    ['primary_actions', 'secondary_actions', 'contextual_actions', 'danger_actions', 'recommended_actions'].forEach((group) => {
      const rows = rawActions[group];
      if (!Array.isArray(rows)) return;
      rows.forEach((item) => {
        const row = asRecord(item);
        const key = asText(row.key).trim();
        if (!key || map[key]) return;
        map[key] = {
          ...row,
          group,
        };
      });
    });
    return map;
  });
  const orchestrationActions = computed<Record<string, unknown>>(() => {
    const raw = contract.value?.page_orchestration_v1?.action_schema;
    if (!raw || typeof raw !== 'object') return {};
    const actionsRow = (raw as Record<string, unknown>).actions;
    if (actionsRow && typeof actionsRow === 'object') {
      return actionsRow as Record<string, unknown>;
    }
    return sceneActionSchema.value as Record<string, unknown>;
  });
  const runtimeRoleCode = computed(() => {
    const fromSurface = asText(session.roleSurface?.role_code);
    if (fromSurface) return fromSurface;
    const page = contract.value?.page_orchestration_v1?.page;
    const context = page && typeof page === 'object' ? (page as Record<string, unknown>).context : null;
    if (context && typeof context === 'object') {
      return asText((context as Record<string, unknown>).role_code);
    }
    return '';
  });
  const globalActions = computed<GlobalActionConfig[]>(() => {
    const page = contract.value?.page_orchestration_v1?.page;
    const raw = page && typeof page === 'object'
      ? (page as Record<string, unknown>).global_actions
      : null;
    if (Array.isArray(raw)) {
      const result: GlobalActionConfig[] = [];
      raw.forEach((item) => {
        if (!item || typeof item !== 'object') return;
        const row = item as Record<string, unknown>;
        const key = asText(row.key);
        if (!key) return;
        if (!actionVisible(key)) return;
        const label = asText(row.label) || actionText(key, key);
        const intent = asText(row.intent) || actionIntent(key, 'ui.contract');
        result.push({ key, label, intent });
      });
      return result;
    }
    const result: GlobalActionConfig[] = [];
    ['primary_actions', 'recommended_actions'].forEach((group) => {
      const rows = asRecord(sceneContractV1.value.actions)[group];
      if (!Array.isArray(rows)) return;
      rows.forEach((item) => {
        const row = asRecord(item);
        const key = asText(row.key);
        if (!key || !actionVisible(key)) return;
        result.push({
          key,
          label: asText(row.label) || actionText(key, key),
          intent: asText(row.intent) || actionIntent(key, 'ui.contract'),
        });
      });
    });
    return result;
  });

  function text(key: string, fallback: string): string {
    const value = asText(texts.value[key]);
    return value || fallback;
  }

  function sectionEnabled(key: string, fallback = true): boolean {
    if (!sections.value.size) return fallback;
    return sections.value.get(key)?.enabled ?? fallback;
  }

  function sectionStyle(key: string): Record<string, string> {
    const section = sections.value.get(key);
    if (!section || !section.order) return {};
    return { order: String(section.order) };
  }

  function sectionOpenDefault(key: string, fallback = false): boolean {
    if (!sections.value.size) return fallback;
    return sections.value.get(key)?.open === true;
  }

  function sectionTagIs(key: string, expected: Exclude<SectionTag, ''>, fallback = true): boolean {
    if (!sections.value.size) return fallback;
    return sections.value.get(key)?.tag === expected;
  }

  function actionText(key: string, fallback: string): string {
    const value = asText(actions.value[key]);
    if (value) return value;
    const row = orchestrationActions.value[key];
    if (row && typeof row === 'object') {
      const label = asText((row as Record<string, unknown>).label);
      if (label) return label;
    }
    return fallback;
  }

  function actionIntent(key: string, fallback = ''): string {
    const row = orchestrationActions.value[key];
    if (!row || typeof row !== 'object') {
      const sceneRow = sceneActionSchema.value[key];
      if (!sceneRow) return fallback;
      const sceneIntent = asText(sceneRow.intent);
      return sceneIntent || fallback;
    }
    const intent = asText((row as Record<string, unknown>).intent);
    return intent || fallback;
  }

  function actionTarget(key: string): Record<string, unknown> {
    const row = orchestrationActions.value[key];
    if (!row || typeof row !== 'object') {
      return asRecord(sceneActionSchema.value[key]?.target);
    }
    const target = (row as Record<string, unknown>).target;
    return target && typeof target === 'object' ? target as Record<string, unknown> : {};
  }

  function actionVisible(key: string): boolean {
    const row = orchestrationActions.value[key];
    if (!row || typeof row !== 'object') return true;
    const visibility = (row as Record<string, unknown>).visibility;
    if (!visibility || typeof visibility !== 'object') return true;
    const visibilityRow = visibility as Record<string, unknown>;
    const roles = asTextList(visibilityRow.roles);
    const capabilities = asTextList(visibilityRow.capabilities);
    const roleCode = runtimeRoleCode.value;
    if (roles.length && roleCode && !roles.includes(roleCode)) return false;
    if (capabilities.length) {
      const enabled = new Set((session.capabilities || []).map((item) => asText(item)).filter(Boolean));
      const hasAny = capabilities.some((keyName) => enabled.has(keyName));
      if (!hasAny) return false;
    }
    return true;
  }

  function dataSourceSpec(key: string): Record<string, unknown> {
    const row = orchestrationDataSources.value[key];
    return row && typeof row === 'object' ? row as Record<string, unknown> : {};
  }

  function dataSourceType(key: string): string {
    const row = dataSourceSpec(key);
    return asText(row.source_type);
  }

  function hasDataSource(key: string): boolean {
    return Object.keys(dataSourceSpec(key)).length > 0;
  }

  function consumerRuntimeStatus(): string {
    return asText(consumerRuntime.value.runtime_page_status) || asText(consumerRuntime.value.page_status);
  }

  function consumerRuntimeBridgeAligned(): boolean {
    const bridge = asRecord(consumerRuntime.value.bridge_alignment);
    if (!Object.keys(bridge).length) return true;
    return Object.values(bridge).every((value) => value !== false);
  }

  return {
    contract,
    text,
    sectionEnabled,
    sectionStyle,
    sectionOpenDefault,
    sectionTagIs,
    actionText,
    actionIntent,
    actionTarget,
    actionVisible,
    dataSourceSpec,
    dataSourceType,
    hasDataSource,
    globalActions,
    consumerRuntime,
    consumerRuntimeStatus,
    consumerRuntimeBridgeAligned,
  };
}
