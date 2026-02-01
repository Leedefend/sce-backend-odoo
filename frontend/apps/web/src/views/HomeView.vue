<template>
  <main class="page">
    <section class="card">
      <header>
        <h1>App Initialized</h1>
        <p>User: {{ userName }}</p>
        <p class="meta">Menu items: {{ menuCount }}</p>
      </header>
      <div class="menu">
        <h2>Menu</h2>
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
</style>
