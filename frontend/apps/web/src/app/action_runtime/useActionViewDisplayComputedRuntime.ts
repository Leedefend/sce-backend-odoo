import { computed, type Ref } from 'vue';

type UseActionViewDisplayComputedRuntimeOptions = {
  surfaceKind: Ref<string>;
  records: Ref<Array<Record<string, unknown>>>;
  sortDisplayLabel: Ref<string>;
  sortSourceLabel: Ref<string>;
  status: Ref<'idle' | 'loading' | 'ok' | 'empty' | 'error'>;
  listTotalCount: Ref<number | null>;
  pageText: (key: string, fallback: string) => string;
};

export function useActionViewDisplayComputedRuntime(options: UseActionViewDisplayComputedRuntimeOptions) {
  const sortOptions = computed(() => []);

  const subtitle = computed(
    () => {
      const sortSource = String(options.sortSourceLabel.value || '').trim();
      const sortPrefix = sortSource ? `${sortSource}：` : options.pageText('subtitle_sort_prefix', '排序：');
      return `${options.records.value.length}${options.pageText('subtitle_records_suffix', ' 条记录')} · ${sortPrefix}${options.sortDisplayLabel.value}`;
    },
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
