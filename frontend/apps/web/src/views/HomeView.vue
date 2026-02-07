<template>
  <section class="capability-home">
    <header class="hero">
      <div>
        <h2>能力目录</h2>
        <p class="lead">选择你要完成的工作，直接进入场景。</p>
      </div>
      <div class="view-toggle">
        <button class="my-work-btn" @click="router.push({ path: '/my-work' })">我的工作</button>
        <button
          v-if="isAdmin"
          class="my-work-btn"
          @click="router.push({ path: '/admin/usage-analytics' })"
        >
          使用分析
        </button>
        <button :class="{ active: viewMode === 'card' }" @click="viewMode = 'card'">卡片</button>
        <button :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">列表</button>
      </div>
    </header>

    <div v-if="!entries.length" class="empty">
      <p>当前账号暂无可用能力。</p>
    </div>

    <div v-else :class="viewMode === 'card' ? 'cards' : 'list'">
      <article
        v-for="entry in entries"
        :key="entry.id"
        class="entry"
        :class="`state-${entry.state.toLowerCase()}`"
      >
        <div class="entry-main">
          <p class="title-row">
            <span class="title">{{ entry.title }}</span>
            <span class="state">{{ entry.state }}</span>
          </p>
          <p class="subtitle" :title="entry.reason || entry.subtitle">{{ entry.subtitle || '无说明' }}</p>
          <p v-if="entry.state === 'LOCKED'" class="lock-reason">
            {{ entry.reason || lockReasonLabel(entry.reasonCode) }}
          </p>
        </div>
        <button
          class="open-btn"
          :disabled="entry.state === 'LOCKED'"
          :title="entry.reason || ''"
          @click="openScene(entry)"
        >
          进入
        </button>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import { trackCapabilityOpen } from '../api/usage';

type EntryState = 'READY' | 'LOCKED' | 'PREVIEW';
type CapabilityEntry = {
  id: string;
  key: string;
  title: string;
  subtitle: string;
  sceneKey: string;
  status: string;
  state: EntryState;
  reason: string;
  reasonCode: string;
};

const router = useRouter();
const session = useSessionStore();
const viewMode = ref<'card' | 'list'>('card');
const isAdmin = computed(() => {
  const groups = session.user?.groups_xmlids || [];
  return groups.includes('base.group_system') || groups.includes('smart_construction_core.group_sc_cap_config_admin');
});

function mapState(rawState: string | undefined, status: string): EntryState {
  const state = String(rawState || '').toUpperCase();
  if (state === 'READY' || state === 'LOCKED' || state === 'PREVIEW') {
    return state;
  }
  return status === 'ga' ? 'READY' : 'PREVIEW';
}

const entries = computed<CapabilityEntry[]>(() => {
  const list: CapabilityEntry[] = [];
  session.scenes.forEach((scene, sceneIndex) => {
    const tiles = Array.isArray(scene.tiles) ? scene.tiles : [];
    tiles.forEach((tile, tileIndex) => {
      const key = String(tile.key || '');
      if (!key) return;
      const status = String((tile as { status?: string }).status || 'alpha').toLowerCase();
      const reason = String((tile as { reason?: string }).reason || '');
      const reasonCode = String((tile as { reason_code?: string }).reason_code || '');
      const state = mapState((tile as { state?: string }).state, status);
      list.push({
        id: `${scene.key}-${key}-${sceneIndex}-${tileIndex}`,
        key,
        title: String(tile.title || key),
        subtitle: String(tile.subtitle || ''),
        sceneKey: scene.key,
        status,
        state,
        reason,
        reasonCode,
      });
    });
  });
  return list;
});

function lockReasonLabel(reasonCode: string) {
  const code = String(reasonCode || '').toUpperCase();
  if (code === 'PERMISSION_DENIED') return '权限不足';
  if (code === 'FEATURE_DISABLED') return '订阅未开通';
  if (code === 'ROLE_SCOPE_MISMATCH') return '角色范围不匹配';
  if (code === 'CAPABILITY_SCOPE_MISSING') return '缺少前置能力';
  if (code === 'CAPABILITY_SCOPE_CYCLE') return '能力依赖异常';
  return '当前不可用';
}

async function openScene(entry: CapabilityEntry) {
  if (entry.state === 'LOCKED') return;
  void trackCapabilityOpen(entry.key).catch(() => {});
  await router.push({ path: `/s/${entry.sceneKey}` });
}
</script>

<style scoped>
.capability-home {
  display: grid;
  gap: 16px;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 12px;
  padding: 20px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(21, 128, 61, 0.08), rgba(2, 132, 199, 0.12));
}

.hero h2 {
  margin: 0 0 4px;
  font-size: 24px;
}

.lead {
  margin: 0;
  color: #4b5563;
}

.view-toggle {
  display: inline-flex;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  overflow: hidden;
}

.view-toggle button {
  border: 0;
  background: #f8fafc;
  color: #1f2937;
  padding: 8px 12px;
  cursor: pointer;
}

.view-toggle button.active {
  background: #1d4ed8;
  color: white;
}

.my-work-btn {
  border-right: 1px solid #d1d5db !important;
}

.empty {
  padding: 24px;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  background: #f8fafc;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.list {
  display: grid;
  gap: 10px;
}

.entry {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 12px;
  padding: 14px;
}

.entry-main {
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 6px 0;
}

.title {
  font-weight: 600;
}

.state {
  font-size: 12px;
  border-radius: 999px;
  padding: 2px 8px;
  border: 1px solid currentColor;
}

.subtitle {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lock-reason {
  margin: 6px 0 0;
  color: #b91c1c;
  font-size: 12px;
}

.open-btn {
  align-self: center;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  padding: 6px 10px;
  cursor: pointer;
}

.open-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.state-ready .state {
  color: #166534;
}

.state-preview .state {
  color: #92400e;
}

.state-locked .state {
  color: #b91c1c;
}
</style>
