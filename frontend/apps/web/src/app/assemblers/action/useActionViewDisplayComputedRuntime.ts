import { computed, type Ref } from 'vue';

type UseActionViewDisplayComputedRuntimeOptions = {
  surfaceKind: Ref<string>;
  records: Ref<Array<Record<string, unknown>>>;
  sortLabel: Ref<string>;
  status: Ref<'idle' | 'loading' | 'ok' | 'empty' | 'error'>;
  listTotalCount: Ref<number | null>;
  pageText: (key: string, fallback: string) => string;
};

export function useActionViewDisplayComputedRuntime(options: UseActionViewDisplayComputedRuntimeOptions) {
  const sortOptions = computed(() => {
    if (options.surfaceKind.value === 'risk' || options.surfaceKind.value === 'cost') {
      return [
        { label: options.pageText('sort_option_priority_deadline', '优先级↓ / 截止日↑'), value: 'priority desc,deadline asc,write_date desc' },
        { label: options.pageText('sort_option_deadline_updated', '截止日↑ / 更新时间↓'), value: 'deadline asc,write_date desc' },
        { label: options.pageText('sort_option_updated_id', '更新时间↓ / ID↓'), value: 'write_date desc,id desc' },
      ];
    }
    return [
      { label: options.pageText('sort_option_updated_name_asc', '更新时间↓ / 名称↑'), value: 'write_date desc,name asc' },
      { label: options.pageText('sort_option_updated_asc_name_asc', '更新时间↑ / 名称↑'), value: 'write_date asc,name asc' },
      { label: options.pageText('sort_option_name_updated', '名称↑ / 更新时间↓'), value: 'name asc,write_date desc' },
      { label: options.pageText('sort_option_name_desc_updated', '名称↓ / 更新时间↓'), value: 'name desc,write_date desc' },
    ];
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

