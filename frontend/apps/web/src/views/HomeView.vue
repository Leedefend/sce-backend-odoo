<template>
  <main class="page">
    <section class="card">
      <header>
        <h1>App Initialized</h1>
        <p>User: {{ userName }}</p>
        <p class="meta">Menu items: {{ menuCount }}</p>
      </header>
      <div class="menu">
        <h2>Menu ({{ menuCount }} items)</h2>
        <!-- 简单测试：直接显示菜单项名称 -->
        <div v-if="menuCount > 0" class="simple-menu">
          <h3>简单菜单列表（测试用）</h3>
          <div v-for="(item, index) in menuTree" :key="item.key || index" class="menu-item">
            <strong>{{ index + 1 }}.</strong> 
            {{ item.title || item.name || item.label || 'Unnamed' }}
            <span class="menu-id">(ID: {{ item.menu_id }})</span>
            <span v-if="item.children?.length" class="children-count"> - {{ item.children.length }} 个子菜单</span>
            <span v-else class="children-count"> - 无子菜单</span>
          </div>
        </div>
        <MenuTree :nodes="menuTree" @select="handleSelect" />
        <div v-if="menuCount === 0" class="empty">
          <p>No menu data received. Check app.init response.</p>
          <div class="debug-actions">
            <button class="secondary" @click="reloadApp">Reload App Init</button>
            <button class="secondary" @click="fetchNav">Fetch Nav</button>
            <button class="secondary" @click="dumpMenu">Dump Menu</button>
          </div>
        </div>
      </div>
      <button class="logout" @click="logout">Logout</button>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import MenuTree from '../components/MenuTree.vue';
import { openAction } from '../services/action_service';

const router = useRouter();
const session = useSessionStore();

const userName = computed(() => session.user?.name ?? 'unknown');
const menuTree = computed(() => session.menuTree);
const menuCount = computed(() => menuTree.value.length);

function handleSelect(node: { meta?: { action_id?: number } } & { menu_id?: number }) {
  if (node.meta?.action_id) {
    openAction(router, node.meta, node.menu_id);
  }
}

async function reloadApp() {
  await session.loadAppInit();
}

async function fetchNav() {
  await session.loadNavFallback();
}

function dumpMenu() {
  // eslint-disable-next-line no-console
  console.info('[debug] menuTree', session.menuTree);
  // 详细打印每个菜单项
  session.menuTree.forEach((item, index) => {
    console.info(`[debug] Menu item ${index}:`, {
      key: item.key,
      name: item.name,
      label: item.label,
      title: item.title,
      menu_id: item.menu_id,
      id: (item as any).id,
      children: item.children?.length || 0,
      meta: item.meta
    });
  });
  
  // 同时打印从 app.init 返回的原始 nav 数据
  console.info('[debug] Full app.init response nav data:', JSON.stringify(session.menuTree, null, 2));
}

async function logout() {
  await session.logout();
  router.push('/login');
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: #f3f4f6;
  font-family: "IBM Plex Sans", system-ui, sans-serif;
}

.card {
  width: min(720px, 92vw);
  background: white;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
  display: grid;
  gap: 16px;
}

.menu {
  border-top: 1px solid #e2e8f0;
  padding-top: 12px;
  display: grid;
  gap: 12px;
}

.logout {
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
  background: #1f2937;
  color: white;
  cursor: pointer;
}

.meta {
  color: #64748b;
  font-size: 14px;
}

.empty {
  border: 1px dashed #cbd5f5;
  padding: 12px;
  border-radius: 12px;
  background: #f8fafc;
  color: #475569;
  font-size: 14px;
}

.debug-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.secondary {
  padding: 8px 12px;
  border: 1px solid #cbd5f5;
  border-radius: 10px;
  background: white;
  cursor: pointer;
  color: #1f2937;
}

.simple-menu {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
  background: #f8fafc;
}

.menu-item {
  padding: 6px 0;
  border-bottom: 1px solid #e2e8f0;
}

.menu-item:last-child {
  border-bottom: none;
}

.simple-menu h3 {
  margin-top: 0;
  margin-bottom: 12px;
  color: #334155;
  font-size: 16px;
}

.menu-id {
  font-size: 12px;
  color: #64748b;
  margin-left: 8px;
}

.children-count {
  font-size: 12px;
  color: #94a3b8;
  font-style: italic;
}
</style>
