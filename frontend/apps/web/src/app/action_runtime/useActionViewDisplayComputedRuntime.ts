import { computed, type Ref } from 'vue';

type UseActionViewDisplayComputedRuntimeOptions = {
  actionContract: Ref<Record<string, unknown> | null>;
  records: Ref<Array<Record<string, unknown>>>;
  sortLabel: Ref<string>;
  status: Ref<'idle' | 'loading' | 'ok' | 'empty' | 'error'>;
  listTotalCount: Ref<number | null>;
  pageText: (key: string, fallback: string) => string;
  buildListSortOptions: (contract: unknown, currentSort: string, fallbackLabel: string) => Array<{ label: string; value: string }>;
};

export function useActionViewDisplayComputedRuntime(options: UseActionViewDisplayComputedRuntimeOptions) {
  const sortOptions = computed(() => {
    return options.buildListSortOptions(
      options.actionContract.value,
      options.sortLabel.value,
      options.pageText('sort_option_contract_default', '契约默认排序'),
    );
  });

  const subtitle = computed(
    () =>
      `${options.records.value.length}${options.pageText('subtitle_records_suffix', ' 条记录')} · ${options.pageText('subtitle_sort_prefix', '排序：')}${options.sortLabel.value}`,
  );

  const statusLabel = computed(() => {
    if (options.status.value === 'loading') return options.pageText('status_loading', '加载中');
    if (options.status.value === 'error') return options.pageText('status_error', '加载失败');
    if (options.status.value === 'empty') return options.pageText('status_empty', '暂无数据');
    return options.pageText('status_ready', '已就绪');
  });

  const pageStatus = computed<'loading' | 'ok' | 'empty' | 'error'>(() =>
    options.status.value === 'idle' ? 'loading' : options.status.value,
  );

  const recordCount = computed(() => {
    if (options.listTotalCount.value !== null && Number.isFinite(options.listTotalCount.value)) {
      return Math.max(0, Math.trunc(options.listTotalCount.value));
    }
    return options.records.value.length;
  });

  return {
    sortOptions,
    subtitle,
    statusLabel,
    pageStatus,
    recordCount,
  };
}
