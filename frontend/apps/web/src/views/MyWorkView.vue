<template>
  <section class="my-work">
    <header class="hero">
      <div>
        <h2>我的工作</h2>
        <p>统一查看待我处理、我负责、@我的、我关注的事项。</p>
      </div>
      <div class="actions">
        <button class="secondary" @click="load">刷新</button>
      </div>
    </header>

    <StatusPanel v-if="loading" title="加载我的工作中..." variant="info" />
    <StatusPanel
      v-else-if="errorText"
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="statusError?.traceId || undefined"
      :error-code="statusError?.code"
      :hint="errorCopy.hint"
      variant="error"
      :on-retry="load"
    />
    <p v-if="!loading && !errorText && actionFeedback" class="action-feedback" :class="{ error: actionFeedbackError }">
      {{ actionFeedback }}
    </p>
    <div v-if="!loading && !errorText && retryFailedIds.length" class="retry-bar">
      <span>失败待办 {{ retryFailedIds.length }} 条</span>
      <button class="link-btn done-btn" @click="retryFailedTodos">重试失败项</button>
      <button class="link-btn secondary-btn" @click="clearRetryFailed">忽略</button>
    </div>
    <template v-if="!loading && !errorText">
      <section class="summary-grid">
        <article
          v-for="item in summary"
          :key="item.key"
          class="summary-card"
          :class="{ active: activeSection === item.key }"
          @click="selectSection(item.key)"
        >
          <p class="label">{{ item.label }}</p>
          <p class="count">{{ item.count }}</p>
        </article>
      </section>

      <section class="tabs">
        <button
          v-for="sec in sections"
          :key="sec.key"
          type="button"
          class="tab"
          :class="{ active: activeSection === sec.key }"
          @click="activeSection = sec.key"
        >
          {{ sec.label }}
        </button>
      </section>

      <section v-if="todoSelectionIds.length" class="batch-bar">
        <span>已选 {{ todoSelectionIds.length }} 条待办</span>
        <button class="link-btn done-btn" :disabled="loading" @click="completeSelectedTodos">批量完成</button>
        <button class="link-btn secondary-btn" :disabled="loading" @click="clearTodoSelection">清空</button>
      </section>

      <section class="table-wrap">
        <table>
          <thead>
            <tr>
              <th class="cell-select">
                <input
                  type="checkbox"
                  :checked="allTodoSelected"
                  :disabled="loading || !currentTodoRows.length"
                  @change="toggleAllTodoSelection($event)"
                />
              </th>
              <th>分区</th>
              <th>事项</th>
              <th>模型</th>
              <th>动作</th>
              <th>原因码</th>
              <th>截止日</th>
              <th>入口</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!filteredItems.length">
              <td colspan="8" class="empty">{{ emptyCopy.message }}</td>
            </tr>
            <tr v-for="item in filteredItems" :key="`${item.section || 'all'}-${item.id}`">
              <td class="cell-select">
                <input
                  v-if="isCompletableTodo(item)"
                  type="checkbox"
                  :checked="todoSelectionIdSet.has(item.id)"
                  :disabled="loading"
                  @change="toggleTodoSelection(item.id, $event)"
                />
              </td>
              <td>{{ item.section_label || '-' }}</td>
              <td>{{ item.title || '-' }}</td>
              <td>{{ item.model || '-' }}</td>
              <td>{{ item.action_label || '-' }}</td>
              <td>{{ item.reason_code || '-' }}</td>
              <td>{{ item.deadline || '-' }}</td>
              <td>
                <button
                  v-if="item.section === 'todo' && item.source === 'mail.activity'"
                  class="link-btn done-btn"
                  :disabled="loading"
                  @click="completeItem(item)"
                >
                  完成待办
                </button>
                <button class="link-btn" @click="openRecord(item)">打开记录</button>
                <button class="link-btn secondary-btn" @click="openScene(item.scene_key)">进入场景</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ApiError } from '../api/client';
import { completeMyWorkItem, completeMyWorkItemsBatch, fetchMyWorkSummary, type MyWorkRecordItem, type MyWorkSection, type MyWorkSummaryItem } from '../api/myWork';
import StatusPanel from '../components/StatusPanel.vue';
import { resolveEmptyCopy, resolveErrorCopy, type StatusError } from '../composables/useStatus';

const router = useRouter();

const loading = ref(false);
const errorText = ref('');
const statusError = ref<StatusError | null>(null);
const sections = ref<MyWorkSection[]>([]);
const summary = ref<MyWorkSummaryItem[]>([]);
const items = ref<MyWorkRecordItem[]>([]);
const activeSection = ref<string>('todo');
const todoSelectionIds = ref<number[]>([]);
const retryFailedIds = ref<number[]>([]);
const actionFeedback = ref('');
const actionFeedbackError = ref(false);
const errorCopy = computed(() => resolveErrorCopy(statusError.value, errorText.value || 'Failed to load my work'));
const emptyCopy = computed(() => resolveEmptyCopy('my_work'));
const todoSelectionIdSet = computed(() => new Set(todoSelectionIds.value));

const filteredItems = computed(() => {
  if (!sections.value.length) return items.value;
  const key = activeSection.value;
  if (!key) return items.value;
  return items.value.filter((item) => (item.section || '') === key);
});
const currentTodoRows = computed(() =>
  filteredItems.value.filter((item) => isCompletableTodo(item)).map((item) => item.id),
);
const allTodoSelected = computed(() => {
  if (!currentTodoRows.value.length) return false;
  return currentTodoRows.value.every((id) => todoSelectionIdSet.value.has(id));
});

async function load() {
  loading.value = true;
  errorText.value = '';
  statusError.value = null;
  try {
    const data = await fetchMyWorkSummary(80, 16);
    sections.value = Array.isArray(data.sections) ? data.sections : [];
    summary.value = Array.isArray(data.summary) ? data.summary : [];
    items.value = Array.isArray(data.items) ? data.items : [];
    todoSelectionIds.value = [];
    if (sections.value.length && !sections.value.find((sec) => sec.key === activeSection.value)) {
      activeSection.value = sections.value[0].key;
    }
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : '请求失败';
    if (err instanceof ApiError) {
      statusError.value = {
        message: err.message,
        traceId: err.traceId,
        code: err.status,
        hint: err.hint,
        kind: err.kind,
        reasonCode: err.reasonCode,
      };
    } else {
      statusError.value = { message: errorText.value };
    }
  } finally {
    loading.value = false;
  }
}

function selectSection(key: string) {
  if (!key) return;
  activeSection.value = key;
}

function openScene(sceneKey: string) {
  if (!sceneKey) return;
  router.push({ path: `/s/${sceneKey}` }).catch(() => {});
}

function openRecord(item: MyWorkRecordItem) {
  if (item.model && item.record_id) {
    router.push({ path: `/r/${item.model}/${item.record_id}` }).catch(() => {});
    return;
  }
  openScene(item.scene_key);
}

function isCompletableTodo(item: MyWorkRecordItem) {
  return item.section === 'todo' && item.source === 'mail.activity';
}

function toggleTodoSelection(id: number, event: Event) {
  const checked = Boolean((event.target as HTMLInputElement | null)?.checked);
  const next = new Set(todoSelectionIds.value);
  if (checked) next.add(id);
  else next.delete(id);
  todoSelectionIds.value = Array.from(next);
}

function toggleAllTodoSelection(event: Event) {
  const checked = Boolean((event.target as HTMLInputElement | null)?.checked);
  if (!checked) {
    todoSelectionIds.value = todoSelectionIds.value.filter((id) => !currentTodoRows.value.includes(id));
    return;
  }
  const merged = new Set(todoSelectionIds.value);
  currentTodoRows.value.forEach((id) => merged.add(id));
  todoSelectionIds.value = Array.from(merged);
}

function clearTodoSelection() {
  todoSelectionIds.value = [];
}

function clearRetryFailed() {
  retryFailedIds.value = [];
}

async function completeItem(item: MyWorkRecordItem) {
  if (!item?.id || !item?.source) return;
  loading.value = true;
  actionFeedback.value = '';
  actionFeedbackError.value = false;
  retryFailedIds.value = [];
  try {
    const result = await completeMyWorkItem({
      id: item.id,
      source: item.source,
      note: 'Completed from my-work UI.',
    });
    actionFeedback.value = result.message || '待办已完成';
    actionFeedbackError.value = false;
    await load();
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : '完成待办失败';
    if (err instanceof ApiError) {
      statusError.value = {
        message: err.message,
        traceId: err.traceId,
        code: err.status,
        hint: err.hint,
        kind: err.kind,
        reasonCode: err.reasonCode,
      };
    }
  } finally {
    loading.value = false;
  }
}

async function completeSelectedTodos() {
  if (!todoSelectionIds.value.length) return;
  if (!window.confirm(`确认批量完成 ${todoSelectionIds.value.length} 条待办？`)) return;
  loading.value = true;
  errorText.value = '';
  statusError.value = null;
  actionFeedback.value = '';
  actionFeedbackError.value = false;
  retryFailedIds.value = [];
  try {
    const result = await completeMyWorkItemsBatch({
      ids: [...todoSelectionIds.value],
      source: 'mail.activity',
      note: 'Completed from my-work batch action.',
    });
    if (!result.success) {
      const first = result.failed_items?.[0];
      const failedPreview = (result.failed_items || [])
        .slice(0, 3)
        .map((item) => `#${item.id} ${item.reason_code}: ${item.message}`)
        .join('；');
      retryFailedIds.value = (result.failed_items || []).map((item) => item.id).filter((id) => Number.isFinite(id) && id > 0);
      actionFeedback.value = `批量完成部分失败：${result.done_count} 成功，${result.failed_count} 失败${
        first ? `（${failedPreview}）` : ''
      }`;
      actionFeedbackError.value = true;
    } else {
      actionFeedback.value = `批量完成成功：${result.done_count} 条`;
      actionFeedbackError.value = false;
    }
    await load();
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : '批量完成待办失败';
    if (err instanceof ApiError) {
      statusError.value = {
        message: err.message,
        traceId: err.traceId,
        code: err.status,
        hint: err.hint,
        kind: err.kind,
        reasonCode: err.reasonCode,
      };
    }
  } finally {
    loading.value = false;
  }
}

async function retryFailedTodos() {
  if (!retryFailedIds.value.length) return;
  loading.value = true;
  errorText.value = '';
  statusError.value = null;
  try {
    const result = await completeMyWorkItemsBatch({
      ids: [...retryFailedIds.value],
      source: 'mail.activity',
      note: 'Retry failed items from my-work.',
    });
    if (!result.success) {
      const failedPreview = (result.failed_items || [])
        .slice(0, 3)
        .map((item) => `#${item.id} ${item.reason_code}: ${item.message}`)
        .join('；');
      retryFailedIds.value = (result.failed_items || []).map((item) => item.id).filter((id) => Number.isFinite(id) && id > 0);
      actionFeedback.value = `重试后仍有失败：${result.done_count} 成功，${result.failed_count} 失败（${failedPreview}）`;
      actionFeedbackError.value = true;
    } else {
      retryFailedIds.value = [];
      actionFeedback.value = `重试成功：${result.done_count} 条`;
      actionFeedbackError.value = false;
    }
    await load();
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : '重试失败项失败';
    if (err instanceof ApiError) {
      statusError.value = {
        message: err.message,
        traceId: err.traceId,
        code: err.status,
        hint: err.hint,
        kind: err.kind,
        reasonCode: err.reasonCode,
      };
    }
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.my-work {
  display: grid;
  gap: 16px;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 16px;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.1), rgba(37, 99, 235, 0.08));
}

.hero h2 {
  margin: 0 0 4px;
}

.hero p {
  margin: 0;
  color: #334155;
}

.secondary {
  border: 1px solid #93c5fd;
  border-radius: 8px;
  background: #eff6ff;
  color: #1e3a8a;
  padding: 8px 10px;
  cursor: pointer;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
}

.summary-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px;
  background: #fff;
  cursor: pointer;
}

.summary-card.active {
  border-color: #2563eb;
  box-shadow: inset 0 0 0 1px #2563eb;
}

.summary-card .label {
  margin: 0;
  color: #475569;
  font-size: 13px;
}

.summary-card .count {
  margin: 6px 0 0;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}

.tabs {
  display: flex;
  gap: 8px;
}

.tab {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: #fff;
  color: #334155;
  padding: 6px 10px;
  cursor: pointer;
}

.tab.active {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #1d4ed8;
}

.table-wrap {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.retry-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid #f1f5f9;
}

.cell-select {
  width: 36px;
  text-align: center;
}

th {
  font-size: 12px;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: #64748b;
}

.empty {
  text-align: center;
  color: #64748b;
  padding: 20px 0;
}

.link-btn {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  padding: 6px 10px;
  cursor: pointer;
}

.secondary-btn {
  margin-left: 8px;
}

.done-btn {
  border-color: #86efac;
  background: #f0fdf4;
  color: #166534;
  margin-right: 8px;
}

.action-feedback {
  margin: 0;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #bbf7d0;
  background: #f0fdf4;
  color: #166534;
}

.action-feedback.error {
  border-color: #fecaca;
  background: #fff1f2;
  color: #b91c1c;
}
</style>
