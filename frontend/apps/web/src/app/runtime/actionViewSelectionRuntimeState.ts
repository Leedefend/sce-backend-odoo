import { ref, type Ref } from 'vue';

export type ActionViewSelectionRuntimeState = {
  selectedAssigneeId: Ref<number | null>;
  selectedIds: Ref<number[]>;
};

export type ActionViewSelectionRuntimeCapsule = {
  state: ActionViewSelectionRuntimeState;
};

export function createActionViewSelectionRuntimeState(): ActionViewSelectionRuntimeState {
  return {
    selectedAssigneeId: ref<number | null>(null),
    selectedIds: ref<number[]>([]),
  };
}

export function createActionViewSelectionRuntimeCapsule(): ActionViewSelectionRuntimeCapsule {
  return {
    state: createActionViewSelectionRuntimeState(),
  };
}
