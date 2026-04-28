import type { Ref } from 'vue';
import {
  mergeRequestContext,
  mergeActiveFilter,
  resolveEffectiveFilterContext as resolveEffectiveFilterContextRuntime,
  resolveEffectiveFilterContextRaw as resolveEffectiveFilterContextRawRuntime,
  resolveEffectiveFilterDomain as resolveEffectiveFilterDomainRuntime,
  resolveEffectiveFilterDomainRaw as resolveEffectiveFilterDomainRawRuntime,
  resolveEffectiveRequestContext as resolveEffectiveRequestContextRuntime,
  resolveEffectiveRequestContextRaw as resolveEffectiveRequestContextRawRuntime,
  resolveFilterContext,
  resolveFilterContextRaw,
  resolveFilterDomain,
  resolveFilterDomainRaw,
  resolveGroupByContext as resolveGroupByContextRuntime,
  resolveGroupByContextRaw as resolveGroupByContextRawRuntime,
} from '../runtime/actionViewRequestRuntime';

type Dict = Record<string, unknown>;

type FilterChip = {
  key: string;
  domain: unknown[];
  domainRaw: string;
  context: Dict;
  contextRaw: string;
};

type GroupByChip = {
  field: string;
  context: Dict;
  contextRaw: string;
};

type UseActionViewRequestContextRuntimeOptions = {
  routeContextRaw: () => string;
  menuId: Ref<number | null>;
  hasActiveField: Ref<boolean>;
  filterValue: Ref<'all' | 'active' | 'archived'>;
  contractFilterChips: Ref<FilterChip[]>;
  activeContractFilterKey: Ref<string>;
  contractSavedFilterChips: Ref<FilterChip[]>;
  activeSavedFilterKey: Ref<string>;
  activeCustomFilterDomain: Ref<unknown[]>;
  activeGroupSummaryDomain: Ref<unknown[]>;
  contractGroupByChips: Ref<GroupByChip[]>;
  activeGroupByField: Ref<string>;
};

function parseContextRaw(raw: unknown): Dict {
  if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
    return { ...(raw as Dict) };
  }
  const text = String(raw || '').trim();
  if (!text) return {};
  try {
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Dict;
    }
  } catch {
    return {};
  }
  return {};
}

export function useActionViewRequestContextRuntime(options: UseActionViewRequestContextRuntimeOptions) {
  function resolveContractFilterDomain() {
    return resolveFilterDomain(options.contractFilterChips.value, options.activeContractFilterKey.value);
  }

  function resolveContractFilterDomainRaw() {
    return resolveFilterDomainRaw(options.contractFilterChips.value, options.activeContractFilterKey.value);
  }

  function resolveContractFilterContext() {
    return resolveFilterContext(options.contractFilterChips.value, options.activeContractFilterKey.value);
  }

  function resolveContractFilterContextRaw() {
    return resolveFilterContextRaw(options.contractFilterChips.value, options.activeContractFilterKey.value);
  }

  function resolveSavedFilterDomain() {
    return resolveFilterDomain(options.contractSavedFilterChips.value, options.activeSavedFilterKey.value);
  }

  function resolveSavedFilterDomainRaw() {
    return resolveFilterDomainRaw(options.contractSavedFilterChips.value, options.activeSavedFilterKey.value);
  }

  function resolveSavedFilterContext() {
    return resolveFilterContext(options.contractSavedFilterChips.value, options.activeSavedFilterKey.value);
  }

  function resolveSavedFilterContextRaw() {
    return resolveFilterContextRaw(options.contractSavedFilterChips.value, options.activeSavedFilterKey.value);
  }

  function resolveEffectiveFilterDomain() {
    return resolveEffectiveFilterDomainRuntime(
      resolveContractFilterDomain(),
      resolveSavedFilterDomain(),
      Array.isArray(options.activeCustomFilterDomain.value) ? options.activeCustomFilterDomain.value : [],
      Array.isArray(options.activeGroupSummaryDomain.value) ? options.activeGroupSummaryDomain.value : [],
    );
  }

  function resolveEffectiveFilterDomainRaw() {
    return resolveEffectiveFilterDomainRawRuntime(resolveContractFilterDomainRaw(), resolveSavedFilterDomainRaw());
  }

  function resolveEffectiveFilterContext() {
    return resolveEffectiveFilterContextRuntime(resolveContractFilterContext(), resolveSavedFilterContext());
  }

  function resolveEffectiveFilterContextRaw() {
    return resolveEffectiveFilterContextRawRuntime(resolveContractFilterContextRaw(), resolveSavedFilterContextRaw());
  }

  function resolveGroupByContext() {
    return resolveGroupByContextRuntime(options.contractGroupByChips.value, options.activeGroupByField.value);
  }

  function resolveGroupByContextRaw() {
    return resolveGroupByContextRawRuntime(options.contractGroupByChips.value, options.activeGroupByField.value);
  }

  function resolveEffectiveRequestContext() {
    return resolveEffectiveRequestContextRuntime(resolveEffectiveFilterContext(), resolveGroupByContext());
  }

  function resolveEffectiveRequestContextRaw() {
    return resolveEffectiveRequestContextRawRuntime(resolveEffectiveFilterContextRaw(), resolveGroupByContextRaw());
  }

  function mergeContext(base: Dict | string | undefined, extra?: Dict) {
    return mergeRequestContext({
      base,
      extra,
      routeContext: {},
      menuId: options.menuId.value,
    });
  }

  function mergeActiveFilterDomain(base: unknown) {
    return mergeActiveFilter(base, {
      hasActiveField: options.hasActiveField.value,
      filterValue: options.filterValue.value,
    });
  }

  return {
    resolveContractFilterDomain,
    resolveContractFilterDomainRaw,
    resolveContractFilterContext,
    resolveContractFilterContextRaw,
    resolveSavedFilterDomain,
    resolveSavedFilterDomainRaw,
    resolveSavedFilterContext,
    resolveSavedFilterContextRaw,
    resolveEffectiveFilterDomain,
    resolveEffectiveFilterDomainRaw,
    resolveEffectiveFilterContext,
    resolveEffectiveFilterContextRaw,
    resolveGroupByContext,
    resolveGroupByContextRaw,
    resolveEffectiveRequestContext,
    resolveEffectiveRequestContextRaw,
    mergeContext,
    mergeActiveFilterDomain,
  };
}
