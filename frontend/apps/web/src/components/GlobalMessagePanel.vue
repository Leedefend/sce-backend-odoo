<template>
  <div class="global-message">
    <button
      class="global-message__trigger sc-btn sc-btn-sm"
      type="button"
      :class="{ active: open }"
      @click.stop="toggle"
    >
      消息
      <span v-if="unreadCount" class="global-message__badge sc-badge sc-badge-danger">{{ unreadCount }}</span>
    </button>

    <div v-if="open" class="global-message__backdrop" @click="close"></div>
    <aside v-if="open" class="global-message__panel sc-dialog" @click.stop>
      <header class="global-message__header">
        <div>
          <h2>消息</h2>
          <p>站内沟通与协作提醒</p>
        </div>
        <div class="global-message__header-actions">
          <button class="sc-btn sc-btn-primary sc-btn-sm" type="button" @click="startNewConversation">新建</button>
          <button class="global-message__icon sc-btn sc-btn-sm sc-btn-ghost" type="button" aria-label="关闭消息" @click="close">×</button>
        </div>
      </header>

      <main class="global-message__workspace">
        <section class="global-message__conversations sc-panel-flat">
          <div class="global-message__section-head">
            <span>最近会话</span>
            <button class="sc-btn sc-btn-sm sc-btn-ghost" type="button" :disabled="loadingConversations" @click="loadConversations">
              {{ loadingConversations ? '刷新中...' : '刷新' }}
            </button>
          </div>
          <div v-if="conversations.length" class="global-message__conversation-list sc-list">
            <button
              v-for="conversation in conversations"
              :key="conversation.key"
              class="global-message__conversation sc-list-item"
              type="button"
              :class="{ active: conversation.key === activeConversationKey && !composeMode }"
              @click="selectConversation(conversation)"
            >
              <span class="global-message__conversation-title">{{ conversation.title || '未命名会话' }}</span>
              <small>{{ conversation.latest_message?.body || '暂无消息' }}</small>
              <span v-if="conversation.unread_count" class="global-message__dot sc-badge sc-badge-danger">{{ conversation.unread_count }}</span>
            </button>
          </div>
          <p v-else class="global-message__empty sc-empty">{{ loadingConversations ? '会话加载中...' : '暂无会话' }}</p>
        </section>

        <section class="global-message__thread">
          <div class="global-message__thread-head">
            <div>
              <h3>{{ composeMode ? '新建消息' : activeConversation?.title || '选择会话' }}</h3>
              <p>{{ composeMode ? '选择接收人，输入内容后发送' : '当前会话' }}</p>
            </div>
          </div>

          <div v-if="composeMode" class="global-message__recipient-box">
            <label class="global-message__field">
              <span>接收人</span>
              <input
                ref="recipientInputRef"
                v-model="userQuery"
                class="sc-search"
                type="search"
                placeholder="搜索姓名、账号或邮箱"
                @focus="loadUsers"
                @input="queueUserSearch"
              />
            </label>
            <p class="global-message__compose-hint sc-muted">{{ composeHint }}</p>
            <div v-if="selectedUsers.length" class="global-message__chips">
              <button
                v-for="user in selectedUsers"
                :key="`global-msg-selected-${user.id}`"
                class="sc-tag"
                type="button"
                @click="removeUser(user.id)"
              >
                {{ user.name }} ×
              </button>
            </div>
            <div v-if="userOptions.length" class="global-message__options sc-list">
              <button
                v-for="user in userOptions"
                :key="`global-msg-user-${user.id}`"
                class="sc-list-item"
                type="button"
                :disabled="isSelected(user.id)"
                @click="selectUser(user)"
              >
                <strong>{{ user.name }}</strong>
                <small>{{ user.login || user.email || '内部用户' }}</small>
              </button>
            </div>
          </div>

          <div class="global-message__items">
            <article
              v-for="item in messages"
              :key="`global-message-${item.id}`"
              class="global-message__item"
              :class="{ 'global-message__item--outgoing': item.is_outgoing }"
            >
              <div class="global-message__meta">
                <strong>{{ item.author_name || '系统' }}</strong>
                <time>{{ formatTime(item.date) }}</time>
              </div>
              <p>{{ item.body }}</p>
            </article>
            <p v-if="!messages.length" class="global-message__empty sc-empty">
              {{ loadingMessages ? '消息加载中...' : composeMode ? '发送后将自动形成会话' : '请选择左侧会话' }}
            </p>
          </div>

          <footer class="global-message__composer">
            <textarea
              v-model="body"
              class="sc-input"
              rows="3"
              placeholder="输入沟通内容"
              :disabled="!composeMode && !activeConversation"
              @keydown.ctrl.enter.prevent="send"
              @keydown.meta.enter.prevent="send"
            ></textarea>
            <div class="global-message__composer-actions">
              <p v-if="error" class="global-message__error sc-alert sc-alert-danger">{{ error }}</p>
              <button class="sc-btn sc-btn-primary sc-btn-sm" type="button" :disabled="sending" @click="send">
                {{ sending ? '发送中...' : '发送' }}
              </button>
            </div>
          </footer>
        </section>
      </main>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue';
import { searchCollaborationUsers, type CollaborationUserOption } from '../api/chatter';
import {
  fetchGlobalConversations,
  fetchGlobalMessages,
  markGlobalMessagesRead,
  sendGlobalMessage,
  type GlobalMessageConversation,
  type GlobalMessageItem,
} from '../api/globalMessages';
import { useSessionStore } from '../stores/session';

const session = useSessionStore();
const open = ref(false);
const composeMode = ref(true);
const loadingConversations = ref(false);
const loadingMessages = ref(false);
const sending = ref(false);
const error = ref('');
const body = ref('');
const userQuery = ref('');
const userOptions = ref<CollaborationUserOption[]>([]);
const selectedUsers = ref<CollaborationUserOption[]>([]);
const conversations = ref<GlobalMessageConversation[]>([]);
const messages = ref<GlobalMessageItem[]>([]);
const activeConversationKey = ref('');
const recipientInputRef = ref<HTMLInputElement | null>(null);
const composeNonce = ref(0);
let userSearchTimer: ReturnType<typeof setTimeout> | null = null;
let pollTimer: ReturnType<typeof setInterval> | null = null;

const canUseMessages = computed(() => Boolean(session.token && session.initStatus === 'ready'));
const unreadCount = computed(() => conversations.value.reduce((sum, item) => sum + Number(item.unread_count || 0), 0));
const activeConversation = computed(() =>
  conversations.value.find((item) => item.key === activeConversationKey.value) || null,
);
const composeHint = computed(() =>
  composeNonce.value > 0 ? '请先选择接收人' : '选择接收人后发送第一条消息',
);
const activeRecipientUserIds = computed(() => {
  if (composeMode.value) {
    return selectedUsers.value.map((item) => Number(item.id)).filter(Boolean);
  }
  const currentUserId = Number(session.user?.id || 0);
  return (activeConversation.value?.participant_user_ids || [])
    .map((item) => Number(item))
    .filter((id) => id > 0 && id !== currentUserId);
});

function toggle() {
  open.value = !open.value;
}

function close() {
  open.value = false;
}

function isSelected(userId: number) {
  return selectedUsers.value.some((item) => Number(item.id) === Number(userId));
}

function selectUser(user: CollaborationUserOption) {
  if (isSelected(user.id)) return;
  selectedUsers.value = [...selectedUsers.value, user];
  userQuery.value = '';
}

function removeUser(userId: number) {
  selectedUsers.value = selectedUsers.value.filter((item) => Number(item.id) !== Number(userId));
}

function startNewConversation() {
  composeMode.value = true;
  activeConversationKey.value = '';
  messages.value = [];
  selectedUsers.value = [];
  body.value = '';
  userQuery.value = '';
  error.value = '';
  composeNonce.value += 1;
  void nextTick(() => {
    recipientInputRef.value?.focus();
  });
}

async function selectConversation(conversation: GlobalMessageConversation) {
  composeMode.value = false;
  activeConversationKey.value = conversation.key;
  selectedUsers.value = [];
  userQuery.value = '';
  await loadMessagesForConversation(conversation.key);
  await markRead(conversation.key);
}

async function loadUsers() {
  if (!canUseMessages.value) return;
  try {
    const result = await searchCollaborationUsers({ query: userQuery.value, limit: 12 });
    userOptions.value = result.items || [];
  } catch {
    userOptions.value = [];
  }
}

function queueUserSearch() {
  if (userSearchTimer) clearTimeout(userSearchTimer);
  userSearchTimer = setTimeout(() => {
    userSearchTimer = null;
    void loadUsers();
  }, 220);
}

async function loadConversations() {
  if (!canUseMessages.value) return;
  loadingConversations.value = true;
  try {
    const result = await fetchGlobalConversations({ limit: 40 });
    conversations.value = result.items || [];
    if (!composeMode.value && activeConversationKey.value && !conversations.value.some((item) => item.key === activeConversationKey.value)) {
      startNewConversation();
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '会话加载失败';
  } finally {
    loadingConversations.value = false;
  }
}

async function loadMessagesForConversation(conversationKey: string) {
  if (!canUseMessages.value || !conversationKey) return;
  loadingMessages.value = true;
  error.value = '';
  try {
    const result = await fetchGlobalMessages({ limit: 80, conversation_key: conversationKey });
    messages.value = result.items || [];
  } catch (err) {
    error.value = err instanceof Error ? err.message : '消息加载失败';
  } finally {
    loadingMessages.value = false;
  }
}

async function markRead(conversationKey: string) {
  if (!canUseMessages.value || !conversationKey) return;
  try {
    await markGlobalMessagesRead({ conversation_key: conversationKey });
    conversations.value = conversations.value.map((item) =>
      item.key === conversationKey ? { ...item, unread_count: 0 } : item,
    );
  } catch {
    // read state is non-critical for sending and viewing
  }
}

async function send() {
  if (!canUseMessages.value) {
    error.value = '当前会话未就绪';
    return;
  }
  const text = body.value.trim();
  const recipientIds = activeRecipientUserIds.value;
  if (!recipientIds.length) {
    error.value = composeMode.value ? '请选择接收人' : '当前会话缺少可回复对象';
    return;
  }
  if (!text) {
    error.value = '请输入消息内容';
    return;
  }
  sending.value = true;
  error.value = '';
  try {
    await sendGlobalMessage({ recipient_user_ids: recipientIds, body: text });
    body.value = '';
    await loadConversations();
    const targetConversation = composeMode.value
      ? conversations.value.find((item) => recipientIds.every((id) => item.participant_user_ids.includes(id)))
      : activeConversation.value;
    if (targetConversation) {
      composeMode.value = false;
      activeConversationKey.value = targetConversation.key;
      await loadMessagesForConversation(targetConversation.key);
      await markRead(targetConversation.key);
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '消息发送失败';
  } finally {
    sending.value = false;
  }
}

function formatTime(value: string) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

watch(open, (value) => {
  if (value) {
    void loadUsers();
    void loadConversations();
    if (activeConversationKey.value) void loadMessagesForConversation(activeConversationKey.value);
  }
});

watch(open, (value) => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
  pollTimer = setInterval(() => {
    void loadConversations();
    if (open.value && activeConversationKey.value) void loadMessagesForConversation(activeConversationKey.value);
  }, value ? 12000 : 30000);
}, { immediate: true });

onUnmounted(() => {
  if (userSearchTimer) clearTimeout(userSearchTimer);
  if (pollTimer) clearInterval(pollTimer);
});
</script>

<style scoped>
.global-message {
  position: relative;
}

.global-message__trigger {
  position: relative;
}

.global-message__trigger.active {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
}

.global-message__badge {
  margin-left: 4px;
}

.global-message__backdrop {
  position: fixed;
  inset: 0;
  z-index: 90;
  background: var(--sc-app-overlay);
}

.global-message__panel {
  position: fixed;
  top: 8px;
  right: 8px;
  z-index: 91;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  width: min(620px, calc(100vw - 16px));
  height: calc(100vh - 16px);
  padding: 0;
  border-radius: var(--sc-component-dialog-radius);
  border-right: none;
}

.global-message__header,
.global-message__header-actions,
.global-message__section-head,
.global-message__thread-head,
.global-message__meta,
.global-message__composer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.global-message__header {
  padding: 10px 12px;
  border-bottom: 1px solid var(--sc-app-border);
}

.global-message__header h2,
.global-message__header p,
.global-message__thread-head h3,
.global-message__thread-head p {
  margin: 0;
}

.global-message__header h2,
.global-message__thread-head h3 {
  font-size: 15px;
  line-height: 1.25;
}

.global-message__header p,
.global-message__thread-head p {
  margin-top: 4px;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.global-message__icon {
  width: 30px;
  height: 30px;
}

.global-message__workspace {
  min-height: 0;
  display: grid;
  grid-template-columns: 190px minmax(0, 1fr);
}

.global-message__conversations {
  min-height: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 8px;
  padding: 10px;
  border-right: 1px solid var(--sc-app-border);
  border-top: none;
  border-left: none;
  border-bottom: none;
  border-radius: 0;
}

.global-message__section-head {
  font-size: 12px;
  font-weight: 700;
}

.global-message__conversation.active {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
}

.global-message__conversation-list {
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 0;
  border-radius: var(--sc-component-table-radius);
}

.global-message__conversation {
  position: relative;
  display: grid;
  gap: 4px;
  width: 100%;
  border: none;
  border-left: 3px solid transparent;
  padding: 8px 9px 8px 8px;
  text-align: left;
  cursor: pointer;
}

.global-message__conversation-title {
  padding-right: 20px;
  font-size: 13px;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.global-message__conversation small {
  color: var(--sc-app-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.global-message__dot {
  position: absolute;
  top: 10px;
  right: 8px;
}

.global-message__thread {
  min-height: 0;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr) auto;
}

.global-message__thread-head {
  padding: 10px 12px;
  border-bottom: 1px solid var(--sc-app-border);
}

.global-message__recipient-box {
  display: grid;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--sc-app-border);
}

.global-message__compose-hint {
  margin: 0;
  font-size: 12px;
}

.global-message__field {
  display: grid;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--sc-app-text-secondary);
}

.global-message__field input,
.global-message__composer textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 10px;
  font: inherit;
}

.global-message__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.global-message__options {
  display: grid;
  gap: 0;
  max-height: 84px;
  overflow: auto;
}

.global-message__options button {
  display: grid;
  gap: 2px;
  width: 100%;
  border: none;
  padding: 7px 8px;
  text-align: left;
  cursor: pointer;
}

.global-message__options button:hover:not(:disabled) {
  background: var(--sc-app-hover-bg);
}

.global-message__options button:disabled {
  opacity: 0.45;
  cursor: default;
}

.global-message__options small {
  color: var(--sc-app-text-secondary);
  overflow-wrap: anywhere;
}

.global-message__items {
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 12px;
}

.global-message__item {
  max-width: 84%;
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-panel);
  padding: 8px;
}

.global-message__item--outgoing {
  align-self: flex-end;
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
}

.global-message__item p {
  margin: 8px 0 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: 13px;
  line-height: 1.5;
}

.global-message__meta {
  font-size: 12px;
}

.global-message__meta time {
  color: var(--sc-app-text-secondary);
}

.global-message__composer {
  display: grid;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid var(--sc-app-border);
}

.global-message__composer textarea {
  resize: vertical;
  min-height: 56px;
}

.global-message__error {
  margin: 0;
  font-size: 12px;
  padding: 8px 10px;
}

.global-message__empty {
  margin: 20px 0 0;
  font-size: 13px;
  align-self: start;
}

@media (max-width: 720px) {
  .global-message__panel {
    top: 0;
    right: 0;
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }

  .global-message__workspace {
    grid-template-columns: 1fr;
  }

  .global-message__conversations {
    max-height: 260px;
    border-right: none;
    border-bottom: 1px solid var(--sc-app-border);
  }
}
</style>
