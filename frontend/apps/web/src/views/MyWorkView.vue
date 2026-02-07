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
    <template v-else>
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

      <section class="table-wrap">
        <table>
          <thead>
            <tr>
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
              <td colspan="7" class="empty">{{ emptyCopy.message }}</td>
            </tr>
            <tr v-for="item in filteredItems" :key="`${item.section || 'all'}-${item.id}`">
              <td>{{ item.section_label || '-' }}</td>
              <td>{{ item.title || '-' }}</td>
              <td>{{ item.model || '-' }}</td>
              <td>{{ item.action_label || '-' }}</td>
              <td>{{ item.reason_code || '-' }}</td>
              <td>{{ item.deadline || '-' }}</td>
              <td>
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
import { fetchMyWorkSummary, type MyWorkRecordItem, type MyWorkSection, type MyWorkSummaryItem } from '../api/myWork';
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
const errorCopy = computed(() => resolveErrorCopy(statusError.value, errorText.value || 'Failed to load my work'));
const emptyCopy = computed(() => resolveEmptyCopy('my_work'));

const filteredItems = computed(() => {
  if (!sections.value.length) return items.value;
  const key = activeSection.value;
  if (!key) return items.value;
  return items.value.filter((item) => (item.section || '') === key);
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
</style>
