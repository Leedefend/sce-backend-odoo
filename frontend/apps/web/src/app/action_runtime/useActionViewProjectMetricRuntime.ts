import type { Ref } from 'vue';
import type { SceneListProfile } from '../resolvers/sceneRegistry';

type ListColumnMetricOption = {
  name: string;
  selection?: Array<{ value: string; label: string }>;
  toneByValue?: Record<string, string>;
};

function normalizeCellRawValue(value: unknown) {
  if (Array.isArray(value)) {
    if (value.length > 1 && value[1] !== null && value[1] !== undefined) return value[1];
    if (value.length) return value[0];
  }
  return value;
}

export function useActionViewProjectMetricRuntime(options: {
  listProfile: Ref<SceneListProfile | null>;
  listColumnOptions: Ref<ListColumnMetricOption[]>;
}) {
  function metricFields() {
    const fields = Array.isArray(options.listProfile.value?.metric_fields)
      ? options.listProfile.value?.metric_fields || []
      : [];
    return fields.map((item) => String(item || '').trim()).filter(Boolean);
  }

  function resolveProjectStateCell(row: Record<string, unknown>) {
    const statusField = String(options.listProfile.value?.status_field || '').trim();
    if (!statusField) return { text: '', tone: 'neutral' };
    const column = options.listColumnOptions.value.find((item) => item.name === statusField);
    const raw = normalizeCellRawValue(row[statusField]);
    const key = String(raw ?? '').trim();
    const selectionLabel = key && Array.isArray(column?.selection)
      ? column.selection.find((item) => item.value === key)?.label || ''
      : '';
    return {
      text: selectionLabel || key,
      tone: key ? (column?.toneByValue?.[key] || 'neutral') : 'neutral',
    };
  }

  function resolveProjectAmount(row: Record<string, unknown>) {
    for (const field of metricFields()) {
      const candidate = row[field];
      const amount = Number(candidate);
      if (Number.isFinite(amount) && amount > 0) return amount;
    }
    return 0;
  }

  function isCompletedState(_stateText: string, tone: string) {
    return tone === 'success';
  }

  return {
    metricFields,
    resolveProjectStateCell,
    resolveProjectAmount,
    isCompletedState,
  };
}
