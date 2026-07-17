import { computed, ref } from 'vue';
import {
  discardBusinessConfigChangeSet,
  openBusinessConfigChangeSet,
  previewBusinessConfigChangeSet,
  publishBusinessConfigChangeSet,
  rollbackBusinessConfigChangeSet,
  stageBusinessConfigChangeSetItem,
  validateBusinessConfigChangeSet,
  type BusinessConfigChangeSet,
  type StageBusinessConfigChangeSetItemParams,
} from '../../api/businessConfig';

function requestId(prefix: string) {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return `${prefix}-${crypto.randomUUID()}`;
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function publishFailureMessage(changeSet: BusinessConfigChangeSet) {
  const firstError = changeSet.items
    .flatMap((item) => item.validation_result?.errors || [])
    .find((message) => String(message || '').trim());
  return String(firstError || changeSet.failure_message || '变更集校验未通过，请修正后重试');
}

export function useBusinessConfigDraftSession(roleKey: () => string) {
  const changeSet = ref<BusinessConfigChangeSet | null>(null);
  const loading = ref(false);
  const publishing = ref(false);
  const previewing = ref(false);
  const error = ref('');

  const changeSetToken = computed(() => changeSet.value?.token || '');
  const changeSetItemCount = computed(() => Number(changeSet.value?.item_count || 0));
  const hasUnifiedDraft = computed(() => changeSetItemCount.value > 0 && !['published', 'discarded', 'superseded'].includes(changeSet.value?.state || ''));

  async function ensureChangeSet() {
    if (changeSet.value && !['published', 'discarded', 'superseded'].includes(changeSet.value.state)) return changeSet.value;
    loading.value = true;
    error.value = '';
    try {
      changeSet.value = await openBusinessConfigChangeSet({ role_key: roleKey() || undefined });
      return changeSet.value;
    } finally {
      loading.value = false;
    }
  }

  async function stageItem(params: Omit<StageBusinessConfigChangeSetItemParams, 'change_set_token'>) {
    const current = await ensureChangeSet();
    changeSet.value = await stageBusinessConfigChangeSetItem({ ...params, change_set_token: current.token });
    return changeSet.value;
  }

  async function validateDraft() {
    const current = await ensureChangeSet();
    changeSet.value = await validateBusinessConfigChangeSet({ change_set_token: current.token, role_key: roleKey() || undefined });
    return changeSet.value;
  }

  async function previewDraft(device = 'desktop') {
    const current = await ensureChangeSet();
    previewing.value = true;
    error.value = '';
    try {
      changeSet.value = await previewBusinessConfigChangeSet({ change_set_token: current.token, role_key: roleKey() || undefined, device });
      return changeSet.value;
    } finally {
      previewing.value = false;
    }
  }

  async function publishDraft() {
    const validated = await validateDraft();
    if (validated.state !== 'ready') {
      error.value = publishFailureMessage(validated);
      throw new Error(error.value);
    }
    publishing.value = true;
    error.value = '';
    try {
      changeSet.value = await publishBusinessConfigChangeSet({
        change_set_token: validated.token,
        role_key: roleKey() || undefined,
        request_id: requestId('publish'),
      });
      const publishResult = changeSet.value.publish_result || {};
      if (
        changeSet.value.state !== 'published'
        || publishResult.ok !== true
        || publishResult.runtime_verified !== true
      ) {
        error.value = changeSet.value.failure_message || '发布结果未通过运行态验证';
        throw new Error(error.value);
      }
      return changeSet.value;
    } finally {
      publishing.value = false;
    }
  }

  async function rollbackPublished() {
    if (!changeSet.value) return null;
    changeSet.value = await rollbackBusinessConfigChangeSet({
      change_set_token: changeSet.value.token,
      role_key: roleKey() || undefined,
      request_id: requestId('rollback'),
    });
    return changeSet.value;
  }

  async function discardDraft() {
    if (!changeSet.value) return null;
    changeSet.value = await discardBusinessConfigChangeSet({ change_set_token: changeSet.value.token, role_key: roleKey() || undefined });
    return changeSet.value;
  }

  function resetScope() {
    changeSet.value = null;
    error.value = '';
  }

  return {
    changeSet,
    changeSetToken,
    changeSetItemCount,
    hasUnifiedDraft,
    loading,
    publishing,
    previewing,
    error,
    ensureChangeSet,
    stageItem,
    validateDraft,
    previewDraft,
    publishDraft,
    rollbackPublished,
    discardDraft,
    resetScope,
  };
}
