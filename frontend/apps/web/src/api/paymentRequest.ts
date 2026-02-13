import { intentRequestRaw } from './intents';

export interface PaymentRequestActionSurfaceItem {
  key: string;
  label: string;
  intent?: string;
  method?: string;
  required_params?: string[];
  allowed: boolean;
  reason_code?: string;
  state_required?: string[];
  execute_intent?: string;
  execute_params?: {
    id?: number;
    action?: string;
  };
  idempotency_required?: boolean;
  requires_reason?: boolean;
}

export interface PaymentRequestActionSurfaceData {
  reason_code?: string;
  payment_request?: {
    id: number;
    name?: string;
    state?: string;
    type?: string;
  };
  actions?: PaymentRequestActionSurfaceItem[];
}

export interface PaymentRequestExecuteResult {
  success?: boolean;
  reason_code?: string;
  message?: string;
  intent_action?: string;
  request_id?: string;
  idempotency_key?: string;
  idempotency_fingerprint?: string;
  idempotent_replay?: boolean;
}

export async function fetchPaymentRequestAvailableActions(paymentRequestId: number) {
  const response = await intentRequestRaw<PaymentRequestActionSurfaceData>({
    intent: 'payment.request.available_actions',
    params: { id: paymentRequestId },
  });
  return {
    traceId: response.traceId,
    data: response.data,
  };
}

export async function executePaymentRequestAction(options: {
  paymentRequestId: number;
  action: string;
  reason?: string;
  requestId?: string;
}) {
  const requestId =
    options.requestId ||
    `ui_pay_req_${options.action}_${options.paymentRequestId}_${Date.now()}`;
  const payload: Record<string, unknown> = {
    id: options.paymentRequestId,
    action: options.action,
    request_id: requestId,
  };
  const reason = String(options.reason || '').trim();
  if (reason) {
    payload.reason = reason;
  }
  const response = await intentRequestRaw<PaymentRequestExecuteResult>({
    intent: 'payment.request.execute',
    params: payload,
  });
  return {
    traceId: response.traceId,
    data: response.data,
  };
}
