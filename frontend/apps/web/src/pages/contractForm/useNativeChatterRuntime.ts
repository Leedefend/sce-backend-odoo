import { computed, ref } from 'vue';
import {
  fetchChatterTimeline,
  postChatterMessage,
  scheduleChatterActivity,
  searchCollaborationUsers,
  updateChatterActivity,
  type ChatterTimelineEntry,
  type CollaborationUserOption,
} from '../../api/chatter';
import type { NativeChatterAction } from './types';

function nextBusinessDateInputValue() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function activityEntryId(entry: ChatterTimelineEntry) {
  return Number(entry.activity?.id || entry.id || 0);
}

export function useNativeChatterRuntime(params: {
  model: () => string;
  recordId: () => number;
  activeActivityAction: () => NativeChatterAction | null;
}) {
  const activeMode = ref('');
  const activeLabel = ref('');
  const draft = ref('');
  const activitySummary = ref('');
  const activityDeadline = ref('');
  const activityNote = ref('');
  const userQuery = ref('');
  const userOptions = ref<CollaborationUserOption[]>([]);
  const usersLoading = ref(false);
  const selectedMentionUserIds = ref<number[]>([]);
  const activityAssigneeId = ref(0);
  const posting = ref(false);
  const loading = ref(false);
  const error = ref('');
  const timeline = ref<ChatterTimelineEntry[]>([]);
  const activityUpdatingIds = ref<number[]>([]);

  const selectedMentionUsers = computed(() => {
    const selected = new Set(selectedMentionUserIds.value);
    return userOptions.value.filter((item) => selected.has(Number(item.id || 0)));
  });
  const userChoices = computed(() => {
    const selected = new Set(selectedMentionUserIds.value);
    return userOptions.value.filter((item) => !selected.has(Number(item.id || 0)));
  });

  function clearForRecordLoad() {
    error.value = '';
    timeline.value = [];
  }

  function closeComposer() {
    activeMode.value = '';
    activeLabel.value = '';
    draft.value = '';
    activitySummary.value = '';
    activityDeadline.value = '';
    activityNote.value = '';
    selectedMentionUserIds.value = [];
    activityAssigneeId.value = 0;
    userQuery.value = '';
  }

  async function loadTimeline(targetResId = params.recordId(), targetModel = params.model()) {
    if (!targetResId || !targetModel) return;
    loading.value = true;
    try {
      const response = await fetchChatterTimeline({
        model: targetModel,
        res_id: targetResId,
        limit: 12,
        include_audit: false,
      });
      timeline.value = Array.isArray(response.items) ? response.items : [];
    } catch (err) {
      error.value = err instanceof Error ? err.message : '协作记录加载失败';
    } finally {
      loading.value = false;
    }
  }

  async function loadUsers(query = userQuery.value) {
    usersLoading.value = true;
    try {
      const response = await searchCollaborationUsers({ query, limit: 20 });
      const items = Array.isArray(response.items) ? response.items : [];
      const merged = new Map<number, CollaborationUserOption>();
      userOptions.value.forEach((item) => {
        const id = Number(item.id || 0);
        if (id) merged.set(id, item);
      });
      items.forEach((item) => {
        const id = Number(item.id || 0);
        if (id) merged.set(id, item);
      });
      userOptions.value = Array.from(merged.values());
    } catch (err) {
      error.value = err instanceof Error ? err.message : '协作人员加载失败';
    } finally {
      usersLoading.value = false;
    }
  }

  function selectMentionUser(user: CollaborationUserOption) {
    const id = Number(user.id || 0);
    if (!id || selectedMentionUserIds.value.includes(id)) return;
    selectedMentionUserIds.value = [...selectedMentionUserIds.value, id];
    userQuery.value = '';
  }

  function removeMentionUser(id: number) {
    selectedMentionUserIds.value = selectedMentionUserIds.value.filter((item) => Number(item) !== Number(id));
  }

  async function openAction(action: NativeChatterAction) {
    if (!action.enabled) return;
    error.value = '';
    const mode = action.mode || action.intent;
    if (mode === 'message' || mode === 'note' || mode === 'activity') {
      activeMode.value = mode;
      activeLabel.value = action.label;
      if (mode === 'activity' && !activityDeadline.value) activityDeadline.value = nextBusinessDateInputValue();
      if (!timeline.value.length && !loading.value) await loadTimeline();
      if (!userOptions.value.length && !usersLoading.value) await loadUsers('');
      return;
    }
    activeMode.value = '';
    activeLabel.value = action.label;
    error.value = `${action.label} 缺少可执行配置`;
  }

  async function scheduleActivity() {
    const summary = activitySummary.value.trim();
    if (!summary) {
      error.value = '请填写计划事项';
      return;
    }
    const recordId = params.recordId();
    const model = params.model();
    if (!recordId || !model || posting.value) return;
    const action = params.activeActivityAction();
    posting.value = true;
    error.value = '';
    try {
      await scheduleChatterActivity({
        model,
        res_id: recordId,
        summary,
        note: activityNote.value.trim(),
        date_deadline: activityDeadline.value,
        activity_type_xmlid: String(action?.payload?.activity_type_xmlid || '').trim() || undefined,
        user_id: activityAssigneeId.value || undefined,
      });
      activitySummary.value = '';
      activityDeadline.value = '';
      activityNote.value = '';
      activityAssigneeId.value = 0;
      error.value = '';
      await loadTimeline();
    } catch (err) {
      error.value = err instanceof Error ? err.message : '计划事项创建失败';
    } finally {
      posting.value = false;
    }
  }

  async function send() {
    if (activeMode.value === 'activity') {
      await scheduleActivity();
      return;
    }
    const body = draft.value.trim();
    const recordId = params.recordId();
    const model = params.model();
    if (!body || !recordId || !model || posting.value) return;
    posting.value = true;
    error.value = '';
    try {
      await postChatterMessage({
        model,
        res_id: recordId,
        body,
        subject: activeLabel.value,
        mode: activeMode.value === 'note' ? 'note' : 'message',
        mention_user_ids: selectedMentionUserIds.value,
      });
      draft.value = '';
      selectedMentionUserIds.value = [];
      error.value = '';
      await loadTimeline();
    } catch (err) {
      error.value = err instanceof Error ? err.message : '协作消息发送失败';
    } finally {
      posting.value = false;
    }
  }

  function isActivityUpdating(entry: ChatterTimelineEntry) {
    const id = activityEntryId(entry);
    return Boolean(id && activityUpdatingIds.value.includes(id));
  }

  async function updateActivity(entry: ChatterTimelineEntry, action: 'done' | 'cancel') {
    const activityId = activityEntryId(entry);
    const recordId = params.recordId();
    const model = params.model();
    if (!activityId || !recordId || !model || isActivityUpdating(entry)) return;
    activityUpdatingIds.value = [...activityUpdatingIds.value, activityId];
    error.value = '';
    try {
      await updateChatterActivity({
        model,
        res_id: recordId,
        activity_id: activityId,
        action,
        note: action === 'done' ? '计划已完成。' : '计划已取消。',
      });
      await loadTimeline();
    } catch (err) {
      error.value = err instanceof Error ? err.message : action === 'done' ? '完成计划失败' : '取消计划失败';
    } finally {
      activityUpdatingIds.value = activityUpdatingIds.value.filter((id) => id !== activityId);
    }
  }

  return {
    activeMode,
    activeLabel,
    draft,
    activitySummary,
    activityDeadline,
    activityNote,
    userQuery,
    userOptions,
    usersLoading,
    selectedMentionUserIds,
    selectedMentionUsers,
    userChoices,
    activityAssigneeId,
    posting,
    loading,
    error,
    timeline,
    activityUpdatingIds,
    clearForRecordLoad,
    closeComposer,
    loadTimeline,
    loadUsers,
    selectMentionUser,
    removeMentionUser,
    openAction,
    send,
    updateActivity,
  };
}
