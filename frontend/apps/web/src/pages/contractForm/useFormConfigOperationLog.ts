import { computed, ref, watch } from 'vue';
import type { FormConfigOperationLogEntry } from './types';
import {
  appendFormConfigOperationLogEntry,
  buildFormConfigOperationLogStorageKey,
  createFormConfigOperationLogEntry,
  persistFormConfigOperationLogEntries,
  readFormConfigOperationLogEntries,
} from './formConfigHelpers';

type FormConfigOperationLogSource = {
  user: () => Record<string, unknown> | null | undefined;
  db: () => unknown;
  modelName: () => unknown;
  actionId: () => unknown;
  viewId: () => unknown;
  page: () => unknown;
  storage?: () => Storage | undefined;
};

export function useFormConfigOperationLog(source: FormConfigOperationLogSource) {
  const operationLog = ref<FormConfigOperationLogEntry[]>([]);
  const operatorName = computed(() => {
    const user = source.user() || {};
    return String(user.name || user.login || user.email || user.id || '当前用户').trim();
  });
  const storageKey = computed(() => {
    const user = source.user() || {};
    return buildFormConfigOperationLogStorageKey({
      db: source.db(),
      modelName: source.modelName(),
      actionId: source.actionId(),
      viewId: source.viewId(),
      page: source.page(),
      userId: user.id || user.login || operatorName.value,
    });
  });
  const storage = () => source.storage?.() || (typeof window === 'undefined' ? undefined : window.sessionStorage);

  function persist() {
    persistFormConfigOperationLogEntries(storageKey.value, operationLog.value, storage());
  }

  function hydrate() {
    operationLog.value = readFormConfigOperationLogEntries(storageKey.value, storage(), operatorName.value);
  }

  function appendOperation(
    action: string,
    summary: string,
    status: FormConfigOperationLogEntry['status'] = 'pending',
  ) {
    const entry = createFormConfigOperationLogEntry(action, summary, operatorName.value, status);
    if (!entry) return;
    operationLog.value = appendFormConfigOperationLogEntry(operationLog.value, entry);
    persist();
  }

  function markPendingOperations(status: Extract<FormConfigOperationLogEntry['status'], 'saved' | 'reverted'>) {
    const hasPending = operationLog.value.some((entry) => entry.status === 'pending');
    if (!hasPending) return;
    operationLog.value = operationLog.value.map((entry) => (
      entry.status === 'pending' ? { ...entry, status } : entry
    ));
    persist();
  }

  function clearOperationLog() {
    operationLog.value = [];
    persist();
  }

  watch(storageKey, hydrate, { immediate: true });

  return {
    operationLog,
    operatorName,
    storageKey,
    appendOperation,
    markPendingOperations,
    clearOperationLog,
  };
}
