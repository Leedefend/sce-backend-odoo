<template>
  <main class="page">
    <section class="card">
      <header>
        <h1>App Initialized</h1>
        <p>User: {{ userName }}</p>
      </header>
      <div class="menu">
        <h2>Menu</h2>
        <ul>
          <li v-for="node in menuTree" :key="node.key">
            <button @click="openMenu(node.menu_id)">{{ node.label }}</button>
          </li>
        </ul>
      </div>
      <button class="logout" @click="logout">Logout</button>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';

const router = useRouter();
const session = useSessionStore();

const userName = computed(() => session.user?.name ?? 'unknown');
const menuTree = computed(() => session.menuTree.slice(0, 8));

function openMenu(menuId?: number) {
  if (!menuId) {
    return;
  }
  router.push(`/m/${menuId}`);
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
  width: min(520px, 92vw);
  background: white;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
  display: grid;
  gap: 16px;
}

.menu ul {
  display: grid;
  gap: 8px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.menu button {
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  cursor: pointer;
}

.logout {
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
  background: #1f2937;
  color: white;
  cursor: pointer;
}
</style>
