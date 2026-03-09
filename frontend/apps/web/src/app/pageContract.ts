import { computed } from 'vue';
import { useSessionStore, type PageContract } from '../stores/session';

function asText(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

type SectionTag = 'header' | 'section' | 'details' | 'div' | '';
type SectionConfig = { enabled: boolean; order: number; tag: SectionTag; open: boolean | null };

export function usePageContract(pageKey: string) {
  const session = useSessionStore();
  const contract = computed<PageContract>(() => session.pageContracts?.[pageKey] || {});
  const texts = computed<Record<string, unknown>>(() => {
    const raw = contract.value?.texts;
    return raw && typeof raw === 'object' ? raw : {};
  });
  const sections = computed<Map<string, SectionConfig>>(() => {
    const raw = Array.isArray(contract.value?.sections) ? contract.value.sections : [];
    const map = new Map<string, SectionConfig>();
    raw.forEach((item, idx) => {
      const key = asText(item?.key);
      if (!key) return;
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

  function actionText(key: string, fallback: string): string {
    const value = asText(actions.value[key]);
    return value || fallback;
  }

  return { contract, text, sectionEnabled, sectionStyle, sectionOpenDefault, actionText };
}
