import { computed } from 'vue';
import { useSessionStore, type PageContract } from '../stores/session';

function asText(value: unknown): string {
  return typeof value === 'string' ? value : '';
}
function asTextList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((item) => asText(item)).filter(Boolean)
    : [];
}

type SectionTag = 'header' | 'section' | 'details' | 'div' | '';
type SectionConfig = { enabled: boolean; order: number; tag: SectionTag; open: boolean | null };
type GlobalActionConfig = { key: string; label: string; intent: string };

export function usePageContract(pageKey: string) {
  const session = useSessionStore();
  const contract = computed<PageContract>(() => session.pageContracts?.[pageKey] || {});
  const texts = computed<Record<string, unknown>>(() => {
    const raw = contract.value?.texts;
    return raw && typeof raw === 'object' ? raw : {};
  });
  const orchestrationDataSources = computed<Record<string, unknown>>(() => {
    const raw = contract.value?.page_orchestration_v1?.data_sources;
    return raw && typeof raw === 'object' ? raw as Record<string, unknown> : {};
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
    const raw = hasV1Zones
      ? fromV1
      : (Array.isArray(contract.value?.sections) ? contract.value.sections : []);
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
  const orchestrationActions = computed<Record<string, unknown>>(() => {
    const raw = contract.value?.page_orchestration_v1?.action_schema;
    if (!raw || typeof raw !== 'object') return {};
    const actionsRow = (raw as Record<string, unknown>).actions;
    return actionsRow && typeof actionsRow === 'object' ? actionsRow as Record<string, unknown> : {};
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
    if (!page || typeof page !== 'object') return [];
    const raw = (page as Record<string, unknown>).global_actions;
    if (!Array.isArray(raw)) return [];
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
    if (!row || typeof row !== 'object') return fallback;
    const intent = asText((row as Record<string, unknown>).intent);
    return intent || fallback;
  }

  function actionTarget(key: string): Record<string, unknown> {
    const row = orchestrationActions.value[key];
    if (!row || typeof row !== 'object') return {};
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
  };
}
