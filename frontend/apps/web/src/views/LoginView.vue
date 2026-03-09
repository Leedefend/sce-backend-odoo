<template>
  <main class="page">
    <section v-if="pageSectionEnabled('card', true)" class="card" :style="pageSectionStyle('card')">
      <h1>{{ pageText('title', 'Login') }}</h1>
      <form v-if="pageSectionEnabled('form', true)" :style="pageSectionStyle('form')" @submit.prevent="onSubmit">
        <label>
          {{ pageText('username_label', 'Username') }}
          <input v-model="username" autocomplete="username" />
        </label>
        <label>
          {{ pageText('password_label', 'Password') }}
          <input v-model="password" type="password" autocomplete="current-password" />
        </label>
        <button type="submit" :disabled="loading">{{ loading ? pageText('submit_loading', 'Signing in...') : pageText('submit_idle', 'Sign in') }}</button>
        <p v-if="pageSectionEnabled('error', true) && error" class="error" :style="pageSectionStyle('error')">{{ error }}</p>
      </form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import { usePageContract } from '../app/pageContract';

const router = useRouter();
const route = useRoute();
const session = useSessionStore();
const pageContract = usePageContract('login');
const pageText = pageContract.text;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;

const username = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

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
