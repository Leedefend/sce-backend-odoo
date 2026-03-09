import { computed } from 'vue';
import { useSessionStore, type PageContract } from '../stores/session';

function asText(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

export function usePageContract(pageKey: string) {
  const session = useSessionStore();
  const contract = computed<PageContract>(() => session.pageContracts?.[pageKey] || {});
  const texts = computed<Record<string, unknown>>(() => {
    const raw = contract.value?.texts;
    return raw && typeof raw === 'object' ? raw : {};
  });
  const sections = computed<Map<string, boolean>>(() => {
    const raw = Array.isArray(contract.value?.sections) ? contract.value.sections : [];
    const map = new Map<string, boolean>();
    raw.forEach((item) => {
      const key = asText(item?.key);
      if (!key) return;
      map.set(key, item?.enabled !== false);
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
    return sections.value.get(key) ?? fallback;
  }

  function actionText(key: string, fallback: string): string {
    const value = asText(actions.value[key]);
    return value || fallback;
  }

  return { contract, text, sectionEnabled, actionText };
}
