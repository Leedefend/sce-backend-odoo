<template>
  <main class="page">
    <section class="card">
      <h1>Resolving menu...</h1>
      <p v-if="error" class="error">{{ error }}</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import { resolveMenu } from '../app/menu';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const error = ref('');

onMounted(async () => {
  try {
    const menuId = Number(route.params.menuId);
    if (!menuId) {
      throw new Error('invalid menu id');
    }
    const meta = resolveMenu(session.menuTree, menuId);
    session.setActionMeta(meta);
    await router.replace(`/a/${meta.action_id}`);
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'resolve menu failed';
  }
});
</script>

<style scoped>
.page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: #f8fafc;
  font-family: "IBM Plex Sans", system-ui, sans-serif;
}

.card {
  width: min(420px, 92vw);
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
}

.error {
  color: #dc2626;
}
</style>
