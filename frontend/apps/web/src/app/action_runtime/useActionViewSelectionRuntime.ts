import type { Ref } from 'vue';
import {
  resolveAssigneeSelectionState,
  resolveClearSelectionState,
  resolveIfMatchMapState,
  resolveToggleSelectionAllState,
  resolveToggleSelectionState,
} from '../runtime/actionViewSelectionStateRuntime';
import { resolveBatchIdempotencyKey, resolveBatchIdempotencyPayload } from '../runtime/actionViewBatchRequestSeedRuntime';

type UseActionViewSelectionRuntimeOptions = {
  selectedIds: Ref<number[]>;
  selectedAssigneeId: Ref<number | null>;
  records: Ref<Record<string, unknown>[]>;
  resolveTargetModel: () => string;
};

export function useActionViewSelectionRuntime(options: UseActionViewSelectionRuntimeOptions) {
  function clearSelection() {
    options.selectedIds.value = resolveClearSelectionState();
  }

  function handleAssigneeChange(assigneeId: number | null) {
    options.selectedAssigneeId.value = resolveAssigneeSelectionState({ assigneeId });
  }

  function handleToggleSelection(id: number, selected: boolean) {
    options.selectedIds.value = resolveToggleSelectionState({
      selectedIds: options.selectedIds.value,
      id,
      selected,
    });
  }

  function handleToggleSelectionAll(ids: number[], selected: boolean) {
    options.selectedIds.value = resolveToggleSelectionAllState({
      selectedIds: options.selectedIds.value,
      ids,
      selected,
    });
  }

  function buildIfMatchMap(ids: number[]) {
    return resolveIfMatchMapState({
      ids,
      records: options.records.value,
    });
  }

  function buildIdempotencyKey(action: string, ids: number[], extra: Record<string, unknown> = {}) {
    const payload = resolveBatchIdempotencyPayload({
      model: options.resolveTargetModel(),
      action,
      ids,
      extra,
    });
    return resolveBatchIdempotencyKey({ payload });
  }

  return {
    clearSelection,
    handleAssigneeChange,
    handleToggleSelection,
    handleToggleSelectionAll,
    buildIfMatchMap,
    buildIdempotencyKey,
  };
}
