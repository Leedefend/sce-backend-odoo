import { computed, type Ref } from 'vue';

type Dict = Record<string, unknown>;

type UseActionViewContentDisplayRuntimeOptions = {
  strictProjectionContract: Ref<Dict>;
  mapProjectionMetricItems: (items: unknown, fallbackPrefix: string) => Array<Record<string, unknown>>;
  kanbanTitleFieldHint: Ref<string>;
  kanbanFields: Ref<string[]>;
};

export function useActionViewContentDisplayRuntime(options: UseActionViewContentDisplayRuntimeOptions) {
  const ledgerOverviewItems = computed(() => {
    return options.mapProjectionMetricItems(options.strictProjectionContract.value.overview_strip, 'overview');
  });

  const listSummaryItems = computed(() => {
    return options.mapProjectionMetricItems(options.strictProjectionContract.value.summary_items, 'summary');
  });

  const kanbanTitleField = computed(() => {
    if (options.kanbanTitleFieldHint.value && options.kanbanFields.value.includes(options.kanbanTitleFieldHint.value)) {
      return options.kanbanTitleFieldHint.value;
    }
    const candidates = ['display_name', 'name'];
    const found = candidates.find((field) => options.kanbanFields.value.includes(field));
    return found || options.kanbanFields.value[0] || 'id';
  });

  return {
    ledgerOverviewItems,
    listSummaryItems,
    kanbanTitleField,
  };
}

