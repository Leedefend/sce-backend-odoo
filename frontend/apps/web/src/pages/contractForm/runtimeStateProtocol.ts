import type { Ref } from 'vue';

export type FormRuntimeStatus = 'loading' | 'ok' | 'error';
export type FormRuntimeBusyKind = 'save' | 'action' | null;
export type FormSubmissionFeedbackKind = 'success' | 'warn' | 'error';
export type FormSubmissionFeedback = {
  kind: FormSubmissionFeedbackKind;
  message: string;
} | null;

export type FormRuntimeStatusRefs = {
  status: Ref<FormRuntimeStatus>;
  errorMessage: Ref<string>;
};

export type FormRuntimeBusyRefs = {
  busyKind: Ref<FormRuntimeBusyKind>;
};

export type FormRuntimeFeedbackRefs = {
  submissionFeedback: Ref<FormSubmissionFeedback>;
  validationErrors: Ref<string[]>;
  showOne2manyErrors?: Ref<boolean>;
};

export type FormRuntimeStateRefs =
  & FormRuntimeStatusRefs
  & FormRuntimeBusyRefs
  & Partial<FormRuntimeFeedbackRefs>;

export type FormRuntimeTransactionName =
  | 'saveRecord'
  | 'runAction'
  | 'runOnchangeRoundtrip'
  | 'primaryAction'
  | 'formConfig'
  | 'inlinePolicy'
  | 'contractMode';

export type FormRuntimeStateEvent =
  | { kind: 'begin'; transaction: FormRuntimeTransactionName; busyKind: Exclude<FormRuntimeBusyKind, null> }
  | { kind: 'end'; transaction: FormRuntimeTransactionName }
  | { kind: 'status'; transaction: FormRuntimeTransactionName; status: FormRuntimeStatus; errorMessage?: string }
  | { kind: 'validation'; transaction: FormRuntimeTransactionName; errors: string[]; showOne2manyErrors?: boolean }
  | { kind: 'feedback'; transaction: FormRuntimeTransactionName; feedback: FormSubmissionFeedback };

export const FORM_RUNTIME_TRANSACTIONS: readonly FormRuntimeTransactionName[] = [
  'saveRecord',
  'runAction',
  'runOnchangeRoundtrip',
  'primaryAction',
  'formConfig',
  'inlinePolicy',
  'contractMode',
];
