import { ref, type Ref } from 'vue';
import type { ActionViewBatchRequest } from './actionViewBatchArtifactsRuntime';

export type BatchDetailLine = { text: string; actionRaw?: string; actionLabel?: string };

export type ActionViewBatchRuntimeState = {
  batchMessage: Ref<string>;
  batchDetails: Ref<BatchDetailLine[]>;
  failedCsvFileName: Ref<string>;
  failedCsvContentB64: Ref<string>;
  batchFailedOffset: Ref<number>;
  batchFailedLimit: Ref<number>;
  batchHasMoreFailures: Ref<boolean>;
  lastBatchRequest: Ref<ActionViewBatchRequest | null>;
  batchBusy: Ref<boolean>;
};

export type ActionViewBatchRuntimeCapsule = {
  state: ActionViewBatchRuntimeState;
};

export function createActionViewBatchRuntimeState(): ActionViewBatchRuntimeState {
  return {
    batchMessage: ref(''),
    batchDetails: ref<BatchDetailLine[]>([]),
    failedCsvFileName: ref(''),
    failedCsvContentB64: ref(''),
    batchFailedOffset: ref(0),
    batchFailedLimit: ref(12),
    batchHasMoreFailures: ref(false),
    lastBatchRequest: ref<ActionViewBatchRequest | null>(null),
    batchBusy: ref(false),
  };
}

export function createActionViewBatchRuntimeCapsule(): ActionViewBatchRuntimeCapsule {
  return {
    state: createActionViewBatchRuntimeState(),
  };
}
