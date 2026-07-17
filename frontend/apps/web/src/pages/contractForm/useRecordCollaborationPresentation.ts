/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed, type ComputedRef, type Ref } from 'vue';
import type { ActionContract } from '@sc/schema';
import type { ContractV2NormalizedStore } from '../../app/contracts/v2';
import type { NativeChatterAction } from './types';
import type { ChatterTimelineEntry, CollaborationUserOption } from '../../api/chatter';
import type { PendingNativeAttachment } from './useNativeAttachmentRuntime';
import type { NativeCollaborationPanelListeners, NativeCollaborationPanelProps } from './NativeCollaborationPanel.vue';
import {
  activeChatterPlaceholder as activeChatterPlaceholderFromMode,
  activeChatterPostingLabel as activeChatterPostingLabelFromMode,
  activeChatterSubmitLabel as activeChatterSubmitLabelFromMode,
  nativeActivityFieldLabel,
  nativeAttachmentContractOrNull,
  nativeAttachmentLabel,
  nativeAttachmentLabelsFromContract,
  nativeAttachmentMaxBytes as nativeAttachmentMaxBytesFromContract,
  nativeChatterActionsFromContract,
  nativeCollaborationUnavailableMessage as nativeCollaborationUnavailableMessageFromState,
  resolveNativeAttachmentContract,
  resolveNativeChatterContract,
  resolveRuntimeCollaborationContract,
} from './collaborationContract';

type MutableRef<T = unknown> = Ref<T>;

export function useRecordCollaborationPresentation(context: {
  contract: Ref<ActionContract | null>;
  v2ContractStore: Ref<ContractV2NormalizedStore | null>;
  recordId: ComputedRef<number | null>;
  model: ComputedRef<string>;
  renderProfile: ComputedRef<string>;
  busy: ComputedRef<boolean>;
  activeChatterMode: MutableRef<string>;
  activeChatterLabel: MutableRef<string>;
  chatterDraft: MutableRef<string>;
  activitySummary: MutableRef<string>;
  activityDeadline: MutableRef<string>;
  activityNote: MutableRef<string>;
  collaborationUserQuery: MutableRef<string>;
  collaborationUserOptions: MutableRef<CollaborationUserOption[]>;
  collaborationUserChoices: ComputedRef<CollaborationUserOption[]>;
  collaborationUsersLoading: MutableRef<boolean>;
  selectedMentionUsers: ComputedRef<CollaborationUserOption[]>;
  activityAssigneeId: MutableRef<number>;
  chatterPosting: MutableRef<boolean>;
  chatterError: MutableRef<string>;
  chatterTimeline: MutableRef<ChatterTimelineEntry[]>;
  activityUpdatingIds: MutableRef<number[]>;
  attachmentError: MutableRef<string>;
  attachmentUploading: MutableRef<boolean>;
  pendingNativeAttachments: MutableRef<PendingNativeAttachment[]>;
  onNativeAttachmentSelected: (...args: any[]) => unknown;
  closeNativeChatterComposer: (...args: any[]) => unknown;
  loadCollaborationUsers: (...args: any[]) => unknown;
  openNativeChatterAction: (...args: any[]) => unknown;
  openNativeAttachment: (...args: any[]) => unknown;
  removeMentionUser: (...args: any[]) => unknown;
  removePendingNativeAttachment: (...args: any[]) => unknown;
  selectMentionUser: (...args: any[]) => unknown;
  sendNativeChatter: (...args: any[]) => unknown;
  updateNativeActivity: (...args: any[]) => unknown;
}) {
  const runtimeCollaborationContract = computed(() => resolveRuntimeCollaborationContract(
    context.v2ContractStore.value?.snapshot?.runtimeContract,
    (context.contract.value as Record<string, unknown> | null | undefined)?.runtimeContract,
  ));
  const nativeChatterContract = computed(() => resolveNativeChatterContract(
    context.contract.value?.views?.form,
    runtimeCollaborationContract.value,
  ));
  const nativeAttachmentContract = computed(() => resolveNativeAttachmentContract(
    context.contract.value?.views?.form,
    runtimeCollaborationContract.value,
  ));
  const nativeChatterActions = computed<NativeChatterAction[]>(() => nativeChatterActionsFromContract(nativeChatterContract.value, {
    recordId: context.recordId.value,
    model: context.model.value,
  }));
  const nativeAttachments = computed(() => nativeAttachmentContractOrNull(nativeAttachmentContract.value));
  const nativeChatterTitle = computed(() => String(nativeChatterContract.value?.label || '').trim());
  const nativeCollaborationTitle = computed(() => nativeChatterTitle.value || '协作日志');
  const nativeCollaborationUnavailableMessage = computed(() => nativeCollaborationUnavailableMessageFromState({
    recordId: context.recordId.value,
    model: context.model.value,
    renderProfile: context.renderProfile.value,
    hasAttachments: Boolean(nativeAttachments.value),
  }));
  const activeChatterSubmitLabel = computed(() => activeChatterSubmitLabelFromMode(context.activeChatterMode.value, context.activeChatterLabel.value));
  const activeChatterPostingLabel = computed(() => activeChatterPostingLabelFromMode(context.activeChatterMode.value));
  const activeChatterPlaceholder = computed(() => activeChatterPlaceholderFromMode(context.activeChatterMode.value));
  const activeChatterIsActivity = computed(() => context.activeChatterMode.value === 'activity');
  const activeActivityAction = computed(() => (
    nativeChatterActions.value.find((item) => item.mode === 'activity' && item.label === context.activeChatterLabel.value)
    || nativeChatterActions.value.find((item) => item.mode === 'activity')
    || null
  ));
  const activityFieldLabel = (name: string, fallback: string) => nativeActivityFieldLabel(activeActivityAction.value, name, fallback);
  const activitySummaryLabel = computed(() => activityFieldLabel('summary', '摘要'));
  const activityDeadlineLabel = computed(() => activityFieldLabel('date_deadline', '截止日期'));
  const activityNoteLabel = computed(() => activityFieldLabel('note', '备注'));
  const activitySummaryPlaceholder = computed(() => '填写需要跟进的计划事项');
  const activityNotePlaceholder = computed(() => '补充计划背景、办理要求或注意事项');
  const activityAssigneeOptions = computed(() => context.collaborationUserOptions.value);
  const activityAssigneeLabel = computed(() => activityFieldLabel('user_id', '指派给'));
  const isNativeChatterSubmitDisabled = computed(() => context.chatterPosting.value
    || (context.activeChatterMode.value === 'activity' ? !context.activitySummary.value.trim() : !context.chatterDraft.value.trim()));
  const nativeAttachmentLabels = computed<Record<string, string>>(() => nativeAttachmentLabelsFromContract(nativeAttachments.value));
  const resolveNativeAttachmentLabel = (key: string, fallback: string) => nativeAttachmentLabel(nativeAttachmentLabels.value, key, fallback);
  const nativeAttachmentUploadLabel = computed(() => resolveNativeAttachmentLabel('upload', '上传附件'));
  const nativeAttachmentUploadingLabel = computed(() => resolveNativeAttachmentLabel('uploading', '上传中...'));
  const nativeAttachmentViewLabel = computed(() => resolveNativeAttachmentLabel('view', '查看'));
  const nativeAttachmentMaxBytes = computed(() => nativeAttachmentMaxBytesFromContract(nativeAttachments.value));
  const nativeCollaborationPanelProps = computed<NativeCollaborationPanelProps>(() => ({
    actions: nativeChatterActions.value, activityAssigneeId: context.activityAssigneeId.value,
    activityAssigneeLabel: activityAssigneeLabel.value, activityAssigneeOptions: activityAssigneeOptions.value,
    activityDeadline: context.activityDeadline.value, activityDeadlineLabel: activityDeadlineLabel.value,
    activityNote: context.activityNote.value, activityNoteLabel: activityNoteLabel.value,
    activityNotePlaceholder: activityNotePlaceholder.value, activitySummary: context.activitySummary.value,
    activitySummaryLabel: activitySummaryLabel.value, activitySummaryPlaceholder: activitySummaryPlaceholder.value,
    activeIsActivity: activeChatterIsActivity.value, activeMode: context.activeChatterMode.value,
    activePlaceholder: activeChatterPlaceholder.value, activePostingLabel: activeChatterPostingLabel.value,
    activeSubmitLabel: activeChatterSubmitLabel.value, activityUpdatingIds: context.activityUpdatingIds.value,
    attachmentError: context.attachmentError.value, attachmentUploadLabel: nativeAttachmentUploadLabel.value,
    attachmentUploading: context.attachmentUploading.value, attachmentUploadingLabel: nativeAttachmentUploadingLabel.value,
    attachmentViewLabel: nativeAttachmentViewLabel.value, busy: context.busy.value, chatterDraft: context.chatterDraft.value,
    chatterError: context.chatterError.value, collaborationUserChoices: context.collaborationUserChoices.value,
    collaborationUserQuery: context.collaborationUserQuery.value, hasAttachments: Boolean(nativeAttachments.value),
    pendingAttachments: context.pendingNativeAttachments.value, posting: context.chatterPosting.value,
    selectedMentionUsers: context.selectedMentionUsers.value, submitDisabled: isNativeChatterSubmitDisabled.value,
    timeline: context.chatterTimeline.value, title: nativeCollaborationTitle.value,
    unavailableMessage: nativeCollaborationUnavailableMessage.value, usersLoading: context.collaborationUsersLoading.value,
  }));
  const nativeCollaborationPanelListeners: NativeCollaborationPanelListeners = {
    'attachment-selected': context.onNativeAttachmentSelected, 'close-composer': context.closeNativeChatterComposer,
    'load-users': context.loadCollaborationUsers, 'open-action': context.openNativeChatterAction,
    'open-attachment': context.openNativeAttachment, 'remove-mention-user': context.removeMentionUser,
    'remove-pending-attachment': context.removePendingNativeAttachment,
    'select-activity-assignee': (id) => { context.activityAssigneeId.value = id; },
    'select-mention-user': context.selectMentionUser, 'send-chatter': context.sendNativeChatter,
    'update-activity': context.updateNativeActivity, 'update:activityDeadline': (value) => { context.activityDeadline.value = value; },
    'update:activityNote': (value) => { context.activityNote.value = value; },
    'update:activitySummary': (value) => { context.activitySummary.value = value; },
    'update:chatterDraft': (value) => { context.chatterDraft.value = value; },
    'update:collaborationUserQuery': (value) => { context.collaborationUserQuery.value = value; },
  };
  return {
    activeActivityAction,
    nativeAttachmentMaxBytes,
    nativeChatterActions,
    nativeAttachments,
    nativeCollaborationPanelProps,
    nativeCollaborationPanelListeners,
    resolveNativeAttachmentLabel,
  };
}
