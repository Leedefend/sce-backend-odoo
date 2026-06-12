/* eslint-disable @typescript-eslint/no-unused-vars */
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
  routeDomainRaw: () => string;
  routeContextRaw: () => string;
  routeContext?: () => Dict;
  menuId: Ref<number | null>;
  activeField: Ref<string>;
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
    return [
      options.routeDomainRaw(),
      resolveEffectiveFilterDomainRawRuntime(resolveContractFilterDomainRaw(), resolveSavedFilterDomainRaw()),
    ].map((item) => String(item || '').trim()).filter(Boolean).join(' && ');
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
    return {
      ...(options.routeContext ? options.routeContext() : {}),
      ...resolveEffectiveRequestContextRuntime(resolveEffectiveFilterContext(), resolveGroupByContext()),
    };
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
      activeField: options.activeField.value,
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
