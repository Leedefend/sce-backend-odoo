import { computed, unref, type MaybeRef } from 'vue';
import { isCoreSceneStrictMode } from '../contractStrictMode';

type Dict = Record<string, unknown>;

type StrictContractBundleOptions = {
  sceneKey: MaybeRef<unknown>;
  sceneReadyEntry: MaybeRef<Dict | null | undefined>;
  pageText: (key: string, fallback: string) => string;
};

function asDict(value: unknown): Dict {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  return value as Dict;
}

function asUniqueStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  const uniq = new Set<string>();
  value.forEach((item) => {
    const row = String(item || '').trim();
    if (!row) return;
    uniq.add(row);
  });
  return Array.from(uniq);
}

export function useActionViewStrictContractBundle(options: StrictContractBundleOptions) {
  const strictContractMode = computed(() => {
    const sceneKey = unref(options.sceneKey);
    const sceneReadyEntry = unref(options.sceneReadyEntry);
    return isCoreSceneStrictMode(sceneKey, sceneReadyEntry);
  });

  const strictSceneReadyEntry = computed<Dict>(() => asDict(unref(options.sceneReadyEntry)));

  const strictSurfaceContract = computed<Dict>(() => asDict(strictSceneReadyEntry.value.surface));
  const strictProjectionContract = computed<Dict>(() => asDict(strictSceneReadyEntry.value.projection));
  const strictAdvancedViewContract = computed<Dict>(() => asDict(strictSceneReadyEntry.value.advanced_view));

  const strictContractGuard = computed<Dict>(() => {
    const direct = asDict(strictSceneReadyEntry.value.contract_guard);
    if (Object.keys(direct).length) return direct;
    const meta = asDict(strictSceneReadyEntry.value.meta);
    return asDict(meta.contract_guard);
  });

  const strictContractMissingPaths = computed<string[]>(() => {
    if (!strictContractMode.value) return [];
    return asUniqueStringList(strictContractGuard.value.missing);
  });

  const strictContractDefaultsApplied = computed<string[]>(() => {
    if (!strictContractMode.value) return [];
    return asUniqueStringList(strictContractGuard.value.defaults_applied);
  });

  const strictContractMissingSummary = computed(() => {
    if (!strictContractMode.value) return '';
    const missing = strictContractMissingPaths.value;
    if (!missing.length) return '';
    return `${options.pageText('strict_contract_missing_summary_prefix', '严格模式检测到后端契约缺口：')}${missing.join(', ')}`;
  });

  const strictContractDefaultsSummary = computed(() => {
    if (!strictContractMode.value) return '';
    const defaults = strictContractDefaultsApplied.value;
    if (!defaults.length) return '';
    return `${options.pageText('strict_contract_missing_defaults_prefix', '当前由后端兜底补齐：')}${defaults.join(', ')}`;
  });

  const strictViewModeLabelMap = computed<Record<string, string>>(() => {
    const rows = Array.isArray(strictSceneReadyEntry.value.view_modes)
      ? (strictSceneReadyEntry.value.view_modes as Array<Record<string, unknown>>)
      : [];
    return rows.reduce<Record<string, string>>((acc, row) => {
      const key = String(row.key || '').trim().toLowerCase();
      const label = String(row.label || '').trim();
      if (key && label) acc[key] = label;
      return acc;
    }, {});
  });

  return {
    strictContractMode,
    strictSurfaceContract,
    strictProjectionContract,
    strictContractGuard,
    strictContractMissingPaths,
    strictContractDefaultsApplied,
    strictContractMissingSummary,
    strictContractDefaultsSummary,
    strictAdvancedViewContract,
    strictViewModeLabelMap,
  };
}
