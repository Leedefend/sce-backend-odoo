<template>
  <section class="capability-matrix-page">
    <section v-if="loading" class="status-wrap">
      <StatusPanel title="加载能力矩阵中..." variant="info" />
    </section>
    <section v-else-if="errorText" class="status-wrap">
      <StatusPanel title="能力矩阵加载失败" :message="errorText" :trace-id="traceId || undefined" variant="error" />
    </section>
    <section v-else class="page-shell">
      <header class="hero-card">
        <div>
          <p class="eyebrow">治理配置</p>
          <h1>能力矩阵</h1>
          <p class="hero-subtitle">按能力分组查看当前账号可用入口、只读能力和待后续补位项。</p>
          <p class="hero-trace">Trace {{ traceId || '-' }}</p>
        </div>
        <div class="hero-actions">
          <button type="button" class="secondary" @click="load">刷新</button>
          <button type="button" class="ghost" @click="router.push('/')">回工作台</button>
          <button type="button" class="ghost" @click="router.push('/s/project.management')">项目驾驶舱</button>
        </div>
      </header>

      <section class="summary-grid">
        <article class="summary-card">
          <span class="summary-label">能力组数</span>
          <strong class="summary-value">{{ sections.length }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">能力总数</span>
          <strong class="summary-value">{{ totalCount }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">可进入</span>
          <strong class="summary-value ready">{{ allowedCount }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">受限 / 待补位</span>
          <strong class="summary-value blocked">{{ deniedCount }}</strong>
        </article>
      </section>

      <section v-if="!sections.length" class="empty-wrap">
        <StatusPanel title="暂无能力入口" message="当前账号没有可展示的能力矩阵条目。" variant="info" />
      </section>

      <section v-else class="section-list">
        <article v-for="section in sections" :key="section.key" class="section-card">
          <header class="section-header">
            <div>
              <p class="section-kicker">{{ section.key }}</p>
              <h2>{{ section.label }}</h2>
            </div>
            <span class="section-count">{{ section.items.length }} 项</span>
          </header>

          <div class="item-grid">
            <button
              v-for="item in section.items"
              :key="item.key"
              type="button"
              class="item-card"
              :class="{ disabled: !item.allowed }"
              :disabled="!item.allowed && !item.target_url && !item.scene_key"
              @click="openItem(item)"
            >
              <div class="item-head">
                <strong>{{ item.label || item.key }}</strong>
                <span class="state-chip" :class="stateClass(item)">{{ stateText(item) }}</span>
              </div>
              <p class="item-desc">{{ item.desc || '未提供说明' }}</p>
              <p class="item-meta">
                <span v-if="item.scene_key">scene={{ item.scene_key }}</span>
                <span v-else-if="item.target_url">{{ item.target_url }}</span>
                <span v-else>暂无跳转目标</span>
              </p>
              <p v-if="item.deny_reason?.length" class="item-reason">原因：{{ item.deny_reason.join(' / ') }}</p>
            </button>
          </div>
        </article>
      </section>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import {
  fetchCapabilityMatrix,
  type CapabilityMatrixItem,
  type CapabilityMatrixSection,
} from '../api/capabilityMatrix';

const router = useRouter();
const loading = ref(false);
const errorText = ref('');
const traceId = ref('');
const sections = ref<CapabilityMatrixSection[]>([]);

const totalCount = computed(() => sections.value.reduce((sum, section) => sum + section.items.length, 0));
const allowedCount = computed(() => sections.value.reduce((sum, section) => sum + section.items.filter((item) => item.allowed).length, 0));
const deniedCount = computed(() => Math.max(totalCount.value - allowedCount.value, 0));

function normalizePortalPath(url: string) {
  const raw = String(url || '').trim();
  if (raw === '/portal/capability-matrix') return '/s/portal.capability_matrix';
  if (raw === '/portal/lifecycle') return '/s/project.management';
  if (raw === '/portal/dashboard') return '/';
  return raw;
}

function isInternalRoute(url: string) {
  return (
    url === '/'
    || url.startsWith('/s/')
    || url.startsWith('/a/')
    || url.startsWith('/m/')
    || url.startsWith('/r/')
    || url.startsWith('/f/')
  );
}

function stateText(item: CapabilityMatrixItem) {
  const state = String(item.capability_state || '').toLowerCase();
  if (!item.allowed || state === 'deny') return '受限';
  if (state === 'readonly') return '只读';
  if (state === 'pending') return '待开放';
  if (state === 'coming_soon') return '建设中';
  return '可进入';
}

function stateClass(item: CapabilityMatrixItem) {
  const state = String(item.capability_state || '').toLowerCase();
  if (!item.allowed || state === 'deny') return 'blocked';
  if (state === 'readonly') return 'readonly';
  if (state === 'pending' || state === 'coming_soon') return 'preview';
  return 'ready';
}

async function openItem(item: CapabilityMatrixItem) {
  const rawTarget = String(item.target_url || '').trim();
  const normalizedTarget = normalizePortalPath(rawTarget);
  if (normalizedTarget && isInternalRoute(normalizedTarget)) {
    await router.push(normalizedTarget);
    return;
  }
  if (normalizedTarget.startsWith('http://') || normalizedTarget.startsWith('https://')) {
    window.open(normalizedTarget, '_blank', 'noopener,noreferrer');
    return;
  }
  if (item.scene_key) {
    await router.push(`/s/${item.scene_key}`);
  }
}

async function load() {
  loading.value = true;
  errorText.value = '';
  try {
    const response = await fetchCapabilityMatrix();
    sections.value = Array.isArray(response.data.sections) ? response.data.sections : [];
    traceId.value = response.traceId;
  } catch (error) {
    errorText.value = error instanceof Error ? error.message : '能力矩阵加载失败';
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void load();
});
</script>

<style scoped>
.capability-matrix-page {
  padding: 20px;
}

.status-wrap,
.empty-wrap {
  max-width: 1200px;
  margin: 0 auto;
}

.page-shell {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-card,
.summary-card,
.section-card {
  border: 1px solid #d9e3f0;
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
}

.hero-card {
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.eyebrow,
.section-kicker,
.hero-trace {
  margin: 0;
  color: #5b6b83;
  font-size: 12px;
}

.hero-card h1,
.section-card h2 {
  margin: 6px 0 8px;
  color: #10233c;
}

.hero-subtitle,
.item-desc,
.item-meta,
.item-reason {
  margin: 0;
  color: #42556f;
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.secondary,
.ghost {
  border-radius: 999px;
  padding: 10px 14px;
  font-weight: 600;
  cursor: pointer;
}

.secondary {
  border: 1px solid #173a63;
  background: #173a63;
  color: #fff;
}

.ghost {
  border: 1px solid #c7d4e6;
  background: #fff;
  color: #173a63;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-card {
  padding: 18px 20px;
}

.summary-label {
  display: block;
  color: #60728c;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 28px;
  line-height: 1;
  color: #10233c;
}

.summary-value.ready {
  color: #0d7a43;
}

.summary-value.blocked {
  color: #9a3412;
}

.section-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section-card {
  padding: 18px 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
}

.section-count {
  color: #5b6b83;
  font-size: 13px;
}

.item-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.item-card {
  text-align: left;
  border: 1px solid #d9e3f0;
  border-radius: 14px;
  padding: 14px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 10px;
  cursor: pointer;
}

.item-card.disabled {
  background: #f8fafc;
}

.item-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.state-chip {
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
  font-weight: 700;
}

.state-chip.ready {
  background: #dcfce7;
  color: #166534;
}

.state-chip.readonly {
  background: #dbeafe;
  color: #1d4ed8;
}

.state-chip.preview {
  background: #fef3c7;
  color: #92400e;
}

.state-chip.blocked {
  background: #fee2e2;
  color: #b91c1c;
}

@media (max-width: 960px) {
  .hero-card {
    flex-direction: column;
  }

  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .capability-matrix-page {
    padding: 14px;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
