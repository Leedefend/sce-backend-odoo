<template>
  <section class="block native-chatter-block">
    <h3>{{ title }}</h3>
    <p v-if="unavailableMessage" class="native-chatter-empty">{{ unavailableMessage }}</p>
    <div v-else class="chips">
      <button
        v-for="action in actions"
        :key="`chatter-${action.key}`"
        class="chip-btn"
        type="button"
        :disabled="busy || posting || !action.enabled"
        :title="action.hint"
        @click="$emit('open-action', action)"
      >
        {{ action.label }}
      </button>
    </div>
    <section v-if="!unavailableMessage && activeMode" class="native-chatter-compose">
      <template v-if="activeIsActivity">
        <label class="native-chatter-field">
          <span>{{ activityAssigneeLabel }}</span>
          <select
            class="input"
            :value="activityAssigneeId || ''"
            :disabled="posting || usersLoading"
            @change="emitActivityAssignee"
          >
            <option value="">当前用户</option>
            <option v-for="user in activityAssigneeOptions" :key="`activity-user-${user.id}`" :value="user.id">
              {{ collaborationUserLabel(user) }}
            </option>
          </select>
        </label>
        <label class="native-chatter-field">
          <span>{{ activitySummaryLabel }}</span>
          <input
            class="input"
            type="text"
            :value="activitySummary"
            :placeholder="activitySummaryPlaceholder"
            :disabled="posting"
            @input="$emit('update:activitySummary', inputValue($event))"
          />
        </label>
        <label class="native-chatter-field">
          <span>{{ activityDeadlineLabel }}</span>
          <input
            class="input"
            type="date"
            :value="activityDeadline"
            :disabled="posting"
            @input="$emit('update:activityDeadline', inputValue($event))"
          />
        </label>
        <label class="native-chatter-field">
          <span>{{ activityNoteLabel }}</span>
          <textarea
            class="native-chatter-input"
            :value="activityNote"
            :placeholder="activityNotePlaceholder"
            :disabled="posting"
            @input="$emit('update:activityNote', inputValue($event))"
          />
        </label>
      </template>
      <template v-else>
        <label class="native-chatter-field">
          <span>提醒对象</span>
          <input
            class="input"
            type="text"
            :value="collaborationUserQuery"
            :disabled="posting || usersLoading"
            placeholder="搜索姓名或账号"
            @input="emitCollaborationUserQuery"
          />
        </label>
        <div v-if="selectedMentionUsers.length" class="native-collab-selected">
          <button
            v-for="user in selectedMentionUsers"
            :key="`mention-selected-${user.id}`"
            class="chip-btn"
            type="button"
            :disabled="posting"
            @click="$emit('remove-mention-user', user.id)"
          >
            @{{ collaborationUserLabel(user) }} x
          </button>
        </div>
        <div v-if="collaborationUserChoices.length" class="native-collab-options">
          <button
            v-for="user in collaborationUserChoices.slice(0, 6)"
            :key="`mention-choice-${user.id}`"
            class="ghost mini"
            type="button"
            :disabled="posting"
            @click="$emit('select-mention-user', user)"
          >
            @{{ collaborationUserLabel(user) }}
          </button>
        </div>
        <textarea
          class="native-chatter-input"
          :value="chatterDraft"
          :placeholder="activePlaceholder"
          :disabled="posting"
          @input="$emit('update:chatterDraft', inputValue($event))"
        />
      </template>
      <div class="native-chatter-compose-actions">
        <button class="primary" type="button" :disabled="submitDisabled" @click="$emit('send-chatter')">
          {{ posting ? activePostingLabel : activeSubmitLabel }}
        </button>
        <button class="ghost" type="button" :disabled="posting" @click="$emit('close-composer')">取消</button>
      </div>
    </section>
    <p v-if="chatterError" class="validation-error native-chatter-message">{{ chatterError }}</p>
    <section v-if="hasAttachments" class="native-attachment-tools">
      <label class="chip-btn native-attachment-upload">
        {{ attachmentUploading ? attachmentUploadingLabel : attachmentUploadLabel }}
        <input type="file" :disabled="attachmentUploading" @change="$emit('attachment-selected', $event)" />
      </label>
      <p v-if="attachmentError" class="validation-error native-chatter-message">{{ attachmentError }}</p>
    </section>
    <ul v-if="pendingAttachments.length" class="native-pending-attachments">
      <li v-for="item in pendingAttachments" :key="item.key">
        <span>{{ item.name }}</span>
        <button
          class="ghost native-attachment-download"
          type="button"
          :disabled="attachmentUploading"
          @click="$emit('remove-pending-attachment', item.key)"
        >
          移除
        </button>
      </li>
    </ul>
    <ul v-if="!unavailableMessage && timeline.length" class="native-chatter-timeline">
      <li v-for="entry in timeline" :key="entry.key" class="native-chatter-entry">
        <span class="native-chatter-type">{{ entry.typeLabel }}</span>
        <span class="native-chatter-body">{{ entry.type === 'activity' ? entry.title : (entry.body || entry.title) }}</span>
        <span class="native-chatter-meta">{{ entry.meta }}</span>
        <div v-if="entry.type === 'activity'" class="native-chatter-entry-actions">
          <button
            v-if="entry.activity?.can_complete"
            class="ghost native-chatter-entry-action"
            type="button"
            :disabled="isActivityUpdating(entry)"
            @click="$emit('update-activity', entry, 'done')"
          >
            完成
          </button>
          <button
            v-if="entry.activity?.can_cancel"
            class="ghost native-chatter-entry-action"
            type="button"
            :disabled="isActivityUpdating(entry)"
            @click="$emit('update-activity', entry, 'cancel')"
          >
            取消
          </button>
        </div>
        <button
          v-if="entry.type === 'attachment' && entry.attachment"
          class="ghost native-attachment-download"
          type="button"
          @click="$emit('open-attachment', entry.attachment)"
        >
          {{ attachmentViewLabel }}
        </button>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import type { ChatterTimelineEntry, CollaborationUserOption } from '../../api/chatter';
import type { NativeChatterAction } from './types';

type PendingNativeAttachment = {
  key: string;
  name: string;
  size: number;
  file: File;
};

export type NativeCollaborationPanelProps = {
  title: string;
  unavailableMessage: string;
  actions: NativeChatterAction[];
  busy: boolean;
  posting: boolean;
  usersLoading: boolean;
  activeMode: string;
  activeIsActivity: boolean;
  activePlaceholder: string;
  activeSubmitLabel: string;
  activePostingLabel: string;
  chatterDraft: string;
  collaborationUserQuery: string;
  selectedMentionUsers: CollaborationUserOption[];
  collaborationUserChoices: CollaborationUserOption[];
  activityAssigneeOptions: CollaborationUserOption[];
  activityAssigneeId: number;
  activityAssigneeLabel: string;
  activitySummary: string;
  activityDeadline: string;
  activityNote: string;
  activitySummaryLabel: string;
  activityDeadlineLabel: string;
  activityNoteLabel: string;
  activitySummaryPlaceholder: string;
  activityNotePlaceholder: string;
  submitDisabled: boolean;
  chatterError: string;
  hasAttachments: boolean;
  attachmentUploading: boolean;
  attachmentUploadLabel: string;
  attachmentUploadingLabel: string;
  attachmentViewLabel: string;
  attachmentError: string;
  pendingAttachments: PendingNativeAttachment[];
  timeline: ChatterTimelineEntry[];
  activityUpdatingIds: number[];
};

export type NativeCollaborationPanelListeners = {
  'open-action': (action: NativeChatterAction) => void;
  'update:chatterDraft': (value: string) => void;
  'update:collaborationUserQuery': (value: string) => void;
  'load-users': (query: string) => void;
  'select-mention-user': (user: CollaborationUserOption) => void;
  'remove-mention-user': (id: number) => void;
  'select-activity-assignee': (id: number) => void;
  'update:activitySummary': (value: string) => void;
  'update:activityDeadline': (value: string) => void;
  'update:activityNote': (value: string) => void;
  'send-chatter': () => void;
  'close-composer': () => void;
  'attachment-selected': (event: Event) => void;
  'remove-pending-attachment': (key: string) => void;
  'update-activity': (entry: ChatterTimelineEntry, action: 'done' | 'cancel') => void;
  'open-attachment': (attachment: NonNullable<ChatterTimelineEntry['attachment']>) => void;
};

const props = defineProps<NativeCollaborationPanelProps>();

const emit = defineEmits<{
  'open-action': [action: NativeChatterAction];
  'update:chatterDraft': [value: string];
  'update:collaborationUserQuery': [value: string];
  'load-users': [query: string];
  'select-mention-user': [user: CollaborationUserOption];
  'remove-mention-user': [id: number];
  'select-activity-assignee': [id: number];
  'update:activitySummary': [value: string];
  'update:activityDeadline': [value: string];
  'update:activityNote': [value: string];
  'send-chatter': [];
  'close-composer': [];
  'attachment-selected': [event: Event];
  'remove-pending-attachment': [key: string];
  'update-activity': [entry: ChatterTimelineEntry, action: 'done' | 'cancel'];
  'open-attachment': [attachment: NonNullable<ChatterTimelineEntry['attachment']>];
}>();

function inputValue(event: Event) {
  return String((event.target as HTMLInputElement | HTMLTextAreaElement).value || '');
}

function emitCollaborationUserQuery(event: Event) {
  const value = inputValue(event);
  emit('update:collaborationUserQuery', value);
  emit('load-users', value);
}

function emitActivityAssignee(event: Event) {
  const value = Number((event.target as HTMLSelectElement).value || 0);
  emit('select-activity-assignee', Number.isFinite(value) && value > 0 ? value : 0);
}

function collaborationUserLabel(user: CollaborationUserOption) {
  return String(user.name || user.login || user.email || user.id || '').trim();
}

function activityEntryId(entry: ChatterTimelineEntry) {
  return Number(entry.activity?.id || entry.id || 0);
}

function isActivityUpdating(entry: ChatterTimelineEntry) {
  const id = activityEntryId(entry);
  return Boolean(id && props.activityUpdatingIds.includes(id));
}
</script>

<style scoped src="./NativeCollaborationPanel.css"></style>
