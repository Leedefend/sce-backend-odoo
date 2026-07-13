import type { FormRuntimeStateEvent, FormRuntimeStatusRefs } from './runtimeStateProtocol';
import { INITIAL_FORM_RUNTIME_STATE, reduceFormRuntimeState } from './runtimeStateReducer';

type FormRuntimeStatusEvent = Extract<FormRuntimeStateEvent, { kind: 'status' }>;

export function applyFormRuntimeStatusEvent(
  refs: FormRuntimeStatusRefs,
  event: FormRuntimeStatusEvent,
) {
  const next = reduceFormRuntimeState({
    ...INITIAL_FORM_RUNTIME_STATE,
    status: refs.status.value,
    errorMessage: refs.errorMessage.value,
  }, event);
  refs.status.value = next.status;
  refs.errorMessage.value = next.errorMessage;
}
