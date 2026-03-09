<template>
  <main class="page">
    <section v-if="headerActions.length" class="page-actions">
      <button
        v-for="action in headerActions"
        :key="`login-header-${action.key}`"
        class="ghost"
        :disabled="loading"
        @click="executeHeaderAction(action.key)"
      >
        {{ action.label || action.key }}
      </button>
    </section>
    <section
      v-if="pageSectionEnabled('card', true) && pageSectionTagIs('card', 'section')"
      class="card"
      :style="pageSectionStyle('card')"
    >
      <h1>{{ pageText('title', 'Login') }}</h1>
      <form
        v-if="pageSectionEnabled('form', true) && pageSectionTagIs('form', 'section')"
        :style="pageSectionStyle('form')"
        @submit.prevent="onSubmit"
      >
        <label>
          {{ pageText('username_label', 'Username') }}
          <input v-model="username" autocomplete="username" />
        </label>
        <label>
          {{ pageText('password_label', 'Password') }}
          <input v-model="password" type="password" autocomplete="current-password" />
        </label>
        <button type="submit" :disabled="loading">{{ loading ? pageText('submit_loading', 'Signing in...') : pageText('submit_idle', 'Sign in') }}</button>
        <p
          v-if="pageSectionEnabled('error', true) && pageSectionTagIs('error', 'section') && error"
          class="error"
          :style="pageSectionStyle('error')"
        >
          {{ error }}
        </p>
      </form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';

const router = useRouter();
const route = useRoute();
const session = useSessionStore();
const pageContract = usePageContract('login');
const pageText = pageContract.text;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;

const username = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');
const headerActions = computed(() => pageGlobalActions.value);

async function onSubmit() {
  error.value = '';
  loading.value = true;
  try {
    await session.login(username.value, password.value);
    await session.loadAppInit();
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : session.resolveLandingPath('/');
    await router.push(redirect);
  } catch (err) {
    error.value = err instanceof Error ? err.message : pageText('error_login_failed', 'Login failed');
  } finally {
    loading.value = false;
  }
}

async function executeHeaderAction(actionKey: string) {
  const handled = await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: {},
    onRefresh: async () => {
      error.value = '';
      username.value = '';
      password.value = '';
    },
    onFallback: async (key) => {
      if (key === 'open_landing' || key === 'open_workbench') {
        await router.push('/');
        return true;
      }
      return false;
    },
  });
  if (!handled) {
    error.value = pageText('error_login_failed', 'Login failed');
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  display: grid;
  gap: 12px;
  place-items: center;
  background: #f8fafc;
  font-family: "IBM Plex Sans", system-ui, sans-serif;
}

.page-actions {
  width: min(420px, 92vw);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ghost {
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  color: #111827;
  cursor: pointer;
}

.card {
  width: min(420px, 92vw);
  background: white;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
}

form {
  display: grid;
  gap: 16px;
}

label {
  display: grid;
  gap: 8px;
  font-size: 14px;
  color: #334155;
}

input {
  padding: 10px 12px;
  border: 1px solid #cbd5f5;
  border-radius: 8px;
}

button {
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
  background: #111827;
  color: white;
  cursor: pointer;
}

.error {
  color: #dc2626;
  font-size: 13px;
}
</style>
