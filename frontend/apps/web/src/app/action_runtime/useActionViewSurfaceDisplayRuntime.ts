import { computed, type ComputedRef, type Ref } from 'vue';

type Dict = Record<string, unknown>;

type ActionContractLike = {
  surface_policies?: {
    kind?: unknown;
  };
};

type UseActionViewSurfaceDisplayRuntimeOptions = {
  sortValue: Ref<string>;
  nativeDefaultSort: Ref<string>;
  contractColumnLabels: Ref<Record<string, string>>;
  sceneContractV1: ComputedRef<Dict>;
  strictContractMode: Ref<boolean>;
  strictSurfaceContract: Ref<Dict>;
  actionContract: Ref<ActionContractLike | null>;
  resolveActionViewSurfaceKind: (input: Dict) => string;
};

const COMMON_FIELD_LABELS: Record<string, string> = {
  id: '编号',
  name: '名称',
  display_name: '名称',
  create_date: '创建时间',
  write_date: '更新时间',
  create_uid: '创建人',
  write_uid: '更新人',
  active: '启用状态',
  sequence: '序号',
  state: '状态',
};

function resolveFieldDisplayLabel(field: string, labels: Record<string, string>): string {
  const normalized = String(field || '').trim();
  if (!normalized) return '';
  const contractLabel = String(labels[normalized] || '').trim();
  if (contractLabel) return contractLabel;
  const fallback = String(COMMON_FIELD_LABELS[normalized] || '').trim();
  if (fallback) return fallback;
  return normalized;
}

export function useActionViewSurfaceDisplayRuntime(options: UseActionViewSurfaceDisplayRuntimeOptions) {
  const sortLabel = computed(() => String(options.sortValue.value || '').trim() || 'id asc');
  const sortDisplayLabel = computed(() => {
    const raw = String(options.sortValue.value || '').trim() || 'id asc';
    const firstClause = raw.split(',')[0]?.trim() || raw;
    const parts = firstClause.split(/\s+/).filter(Boolean);
    const field = String(parts[0] || '').trim();
    const direction = String(parts[1] || '').trim().toLowerCase();
    if (!field) return raw;
    const fieldLabel = resolveFieldDisplayLabel(field, options.contractColumnLabels.value);
    if (direction === 'desc') return `${fieldLabel} 降序`;
    if (direction === 'asc') return `${fieldLabel} 升序`;
    return fieldLabel;
  });
  const sortSourceLabel = computed(() => {
    const current = String(options.sortValue.value || '').trim();
    const nativeDefault = String(options.nativeDefaultSort.value || '').trim();
    if (!current) return '';
    if (nativeDefault && current === nativeDefault) return '原生默认排序';
    return '当前排序';
  });

  const surfaceKind = computed(() => {
    const extensions = (options.sceneContractV1.value.extensions as Dict | undefined) || {};
    return options.resolveActionViewSurfaceKind({
      strictContractMode: options.strictContractMode.value,
      strictSurfaceContract: options.strictSurfaceContract.value,
      contractSurfaceKind: options.actionContract.value?.surface_policies?.kind,
      extensionSurfaceKind: extensions.surface_kind,
    });
  });

  return {
    sortLabel,
    sortDisplayLabel,
    sortSourceLabel,
    surfaceKind,
  };
}
