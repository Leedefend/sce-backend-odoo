import { ref } from 'vue';

export type EditTxState = 'idle' | 'editing' | 'saving' | 'saved' | 'error';

export type EditTxMeta = {
  txId: string;
  startedAt: number | null;
  lastTraceId: string;
  lastErrorCode: string;
};

function generateTxId() {
  return `tx_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function extractErrorCode(err: unknown): string {
  if (!err || typeof err !== 'object') return '';
  const raw = err as { code?: unknown; message?: unknown };
  if (raw.code != null && String(raw.code).trim()) {
    return String(raw.code);
  }
  if (raw.message != null && String(raw.message).trim()) {
    return String(raw.message);
  }
  return '';
}

export function useEditTx() {
  const state = ref<EditTxState>('idle');
  const meta = ref<EditTxMeta>({
    txId: '',
    startedAt: null,
    lastTraceId: '',
    lastErrorCode: '',
  });

  function beginEdit() {
    state.value = 'editing';
    meta.value.txId = generateTxId();
    meta.value.startedAt = Date.now();
    meta.value.lastErrorCode = '';
  }

  function cancelEdit() {
    state.value = 'idle';
    meta.value.txId = '';
    meta.value.startedAt = null;
    meta.value.lastErrorCode = '';
  }

  async function save<T>(fn: () => Promise<T>) {
    state.value = 'saving';
    meta.value.lastErrorCode = '';
    try {
      const result = await fn();
      state.value = 'saved';
      return result;
    } catch (err: unknown) {
      state.value = 'error';
      meta.value.lastErrorCode = extractErrorCode(err);
      throw err;
    }
  }

  function markSaved(traceId?: string) {
    state.value = 'saved';
    if (traceId) {
      meta.value.lastTraceId = traceId;
    }
  }

  function markError(code?: string) {
    state.value = 'error';
    if (code) {
      meta.value.lastErrorCode = code;
    }
  }

  function reset() {
    state.value = 'idle';
    meta.value = {
      txId: '',
      startedAt: null,
      lastTraceId: '',
      lastErrorCode: '',
    };
  }

  return {
    state,
    meta,
    beginEdit,
    cancelEdit,
    save,
    markSaved,
    markError,
    reset,
  };
}
