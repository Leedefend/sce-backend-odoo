import type {
  FormRuntimeBusyKind,
  FormRuntimeStateEvent,
  FormRuntimeStatus,
  FormSubmissionFeedback,
} from './runtimeStateProtocol';

export type FormRuntimeStateSnapshot = {
  status: FormRuntimeStatus;
  busyKind: FormRuntimeBusyKind;
  errorMessage: string;
  validationErrors: string[];
  showOne2manyErrors: boolean;
  submissionFeedback: FormSubmissionFeedback;
};

export const INITIAL_FORM_RUNTIME_STATE: FormRuntimeStateSnapshot = {
  status: 'loading',
  busyKind: null,
  errorMessage: '',
  validationErrors: [],
  showOne2manyErrors: false,
  submissionFeedback: null,
};

export function reduceFormRuntimeState(
  state: FormRuntimeStateSnapshot,
  event: FormRuntimeStateEvent,
): FormRuntimeStateSnapshot {
  if (event.kind === 'begin') {
    return { ...state, busyKind: event.busyKind };
  }
  if (event.kind === 'end') {
    return { ...state, busyKind: null };
  }
  if (event.kind === 'status') {
    return {
      ...state,
      status: event.status,
      errorMessage: event.errorMessage ?? (event.status === 'error' ? state.errorMessage : ''),
    };
  }
  if (event.kind === 'validation') {
    return {
      ...state,
      validationErrors: event.errors.slice(),
      showOne2manyErrors: Boolean(event.showOne2manyErrors),
    };
  }
  if (event.kind === 'feedback') {
    return { ...state, submissionFeedback: event.feedback };
  }
  return state;
}

export function reduceFormRuntimeStateEvents(
  initialState: FormRuntimeStateSnapshot,
  events: FormRuntimeStateEvent[],
): FormRuntimeStateSnapshot {
  return events.reduce((state, event) => reduceFormRuntimeState(state, event), initialState);
}
