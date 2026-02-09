export type ContractReasonCode = string;

export type ContractFailureMeta = {
  retryable?: boolean;
  error_category?: string;
  suggested_action?: string;
};

export type ContractReasonedFailure = {
  reason_code: ContractReasonCode;
  message: string;
  trace_id?: string;
} & ContractFailureMeta;

export type ContractIdempotencyMeta = {
  request_id?: string;
  idempotency_key?: string;
  idempotency_fingerprint?: string;
  idempotent_replay?: boolean;
  replay_window_expired?: boolean;
  idempotency_replay_reason_code?: ContractReasonCode;
  replay_from_audit_id?: number;
  replay_original_trace_id?: string;
  replay_age_ms?: number;
  replay_supported?: boolean;
  idempotency_deduplicated?: boolean;
  trace_id?: string;
};

export type ContractReasonCount = {
  reason_code: ContractReasonCode;
  count: number;
};
