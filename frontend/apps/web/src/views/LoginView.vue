<template>
  <main class="login-page">
    <div class="login-bg-orb login-bg-orb--left" aria-hidden="true"></div>
    <div class="login-bg-orb login-bg-orb--right" aria-hidden="true"></div>
    <div class="login-bg-grid" aria-hidden="true"></div>

    <section class="login-layout">
      <section class="brand-panel" aria-label="平台介绍">
        <p class="brand-title">{{ pageText('brand_name', '智能施工企业管理平台') }}</p>
        <p class="brand-subtitle">{{ pageText('brand_subtitle', '工程项目全生命周期管理系统') }}</p>
        <p class="brand-slogan">{{ pageText('brand_slogan', '让项目透明 · 让合同可控 · 让资金协同 · 让风险可预警') }}</p>

        <ul class="value-list" aria-label="价值主张">
          <li v-for="line in valueLines" :key="line">{{ line }}</li>
        </ul>

        <section class="capability-strip" aria-label="系统核心能力">
          <div v-for="capability in capabilityItems" :key="capability.key" class="capability-card">
            <span class="capability-icon" aria-hidden="true">{{ capability.icon }}</span>
            <span>{{ capability.label }}</span>
          </div>
        </section>
      </section>

      <section class="auth-panel">
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
          class="login-card"
          :style="pageSectionStyle('card')"
        >
          <header class="brand-header">
            <span class="product-badge">SCEMS · v1.0</span>
            <p class="brand-kicker">智能建造 · 企业级管理</p>
            <h1>{{ pageText('title', '登录') }}</h1>
          </header>

          <form
            v-if="pageSectionEnabled('form', true) && pageSectionTagIs('form', 'section')"
            :style="pageSectionStyle('form')"
            @submit.prevent="onSubmit"
          >
            <label>
              {{ pageText('username_label', '账号') }}
              <input
                v-model="username"
                autocomplete="username"
                :placeholder="pageText('username_placeholder', '请输入账号')"
                :disabled="loading"
                required
              />
            </label>
            <label>
              {{ pageText('password_label', '密码') }}
              <input
                v-model="password"
                type="password"
                autocomplete="current-password"
                :placeholder="pageText('password_placeholder', '请输入密码')"
                :disabled="loading"
                required
              />
            </label>
            <label>
              {{ pageText('db_label', '数据库') }}
              <input
                v-model="dbName"
                autocomplete="off"
                :placeholder="pageText('db_placeholder', '请输入数据库名（如 sc_minimal）')"
                :disabled="loading"
              />
            </label>
            <p
              v-if="pageSectionEnabled('error', true) && pageSectionTagIs('error', 'section') && error"
              class="error"
              :style="pageSectionStyle('error')"
            >
              {{ error }}
            </p>
            <button class="submit" type="submit" :disabled="loading">{{ loading ? pageText('submit_loading', '系统正在登录，请稍候…') : pageText('submit_idle', '登录') }}</button>
          </form>
        </section>
      </section>
    </section>

    <footer class="page-footer">
      <p>© 2025 SCEMS Platform</p>
      <p>Smart Construction Enterprise Management System</p>
    </footer>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import { resolveActiveDb } from '../services/dbContext';
import { config } from '../config';
import { normalizeLegacyWorkbenchPath } from '../app/routeQuery';

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
const dbName = ref(
  config.odooDbPinned
    ? String(config.odooDb || '').trim()
    : resolveActiveDb(String(config.odooDb || '').trim()),
);
const loading = ref(false);
const error = ref('');
const headerActions = computed(() => pageGlobalActions.value);
const capabilityItems = computed(() => [
  { key: 'project', icon: '📊', label: pageText('capability_project', '项目全过程管理') },
  { key: 'contract_cost', icon: '📑', label: pageText('capability_contract_cost', '合同成本联动') },
  { key: 'fund', icon: '💰', label: pageText('capability_fund', '资金支付协同') },
  { key: 'risk', icon: '⚠', label: pageText('capability_risk', '风险预警驾驶舱') },
]);
const valueLines = computed(() => [
  pageText('value_line_1', '让项目透明'),
  pageText('value_line_2', '让合同可控'),
  pageText('value_line_3', '让资金协同'),
  pageText('value_line_4', '让风险可预警'),
]);

watch([username, password], () => {
  if (error.value) error.value = '';
});

function normalizeLoginError(err: unknown): string {
  const fallback = pageText('error_login_failed', '登录失败，请稍后重试');
  if (!(err instanceof Error)) return fallback;
  const raw = String(err.message || '').trim();
  const lower = raw.toLowerCase();
  if (!raw) return fallback;
  if (lower.includes('invalid') || lower.includes('wrong') || lower.includes('password') || lower.includes('401')) {
    return pageText('error_invalid_credentials', '账号或密码错误，请重新输入');
  }
  if (lower.includes('timeout') || lower.includes('network') || lower.includes('failed to fetch')) {
    return pageText('error_network', '网络异常，请稍后重试');
  }
  return fallback;
}

async function onSubmit() {
  error.value = '';
  loading.value = true;
  try {
    await session.login(username.value, password.value, dbName.value);
    await session.loadAppInit();
    const rawRedirect = typeof route.query.redirect === 'string' ? route.query.redirect : '';
    const isLikelyUnboundActionRoute =
      /^\/(f|a|r)\//.test(rawRedirect)
      && !/[?&](action_id|menu_id|scene_key|scene)=/.test(rawRedirect);
    const normalizedRedirect = normalizeLegacyWorkbenchPath(rawRedirect);
    const redirect = (normalizedRedirect && !isLikelyUnboundActionRoute)
      ? normalizedRedirect
      : session.resolveLandingPath('/');
    await router.push(redirect);
  } catch (err) {
    error.value = normalizeLoginError(err);
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
    error.value = pageText('error_login_failed', '登录失败，请稍后重试');
  }
}
</script>

<style scoped>
.login-page {
  --ink: #161616;
  --muted: #6b7280;
  --accent: #2f3a5f;
  min-height: 100vh;
  display: grid;
  place-items: center;
  gap: 18px;
  background: radial-gradient(circle at 12% 12%, #f7e9dc 0%, #f6f3ef 42%, #eef1f7 100%);
  color: var(--ink);
  font-family: "Space Grotesk", "IBM Plex Sans", system-ui, sans-serif;
  padding: 30px 16px;
  position: relative;
  overflow: hidden;
}

.login-layout {
  width: min(1180px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 420px);
  gap: clamp(28px, 5vw, 80px);
  align-items: center;
  position: relative;
  z-index: 1;
}

.brand-panel {
  display: grid;
  gap: 0;
  max-width: 620px;
  padding-left: clamp(20px, 4.5vw, 60px);
}

.login-bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(to right, rgba(47, 58, 95, 0.035) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(47, 58, 95, 0.03) 1px, transparent 1px);
  background-size: 54px 54px;
  opacity: 0.7;
  mask-image: radial-gradient(circle at 36% 50%, rgba(0, 0, 0, 0.62), rgba(0, 0, 0, 0.1) 70%, rgba(0, 0, 0, 0));
  pointer-events: none;
}

.login-bg-orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(2px);
  opacity: 0.32;
  pointer-events: none;
}

.login-bg-orb--left {
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(224, 122, 95, 0.3) 0%, rgba(224, 122, 95, 0) 72%);
  top: -130px;
  left: -130px;
}

.login-bg-orb--right {
  width: 460px;
  height: 460px;
  background: radial-gradient(circle, rgba(47, 58, 95, 0.2) 0%, rgba(47, 58, 95, 0) 72%);
  right: -180px;
  bottom: -180px;
}

.auth-panel {
  width: 100%;
  display: grid;
  justify-items: end;
}

.page-actions {
  width: 100%;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.ghost {
  padding: 8px 12px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.86);
  color: #0f172a;
  cursor: pointer;
  transition: border-color 120ms ease, transform 120ms ease;
}

.ghost:hover:not(:disabled) {
  border-color: rgba(47, 58, 95, 0.4);
  transform: translateY(-1px);
}

.ghost:disabled {
  opacity: 0.56;
  cursor: not-allowed;
}

.login-card {
  width: 100%;
  background: rgba(255, 255, 255, 0.94);
  padding: 32px;
  border-radius: 18px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(15, 23, 42, 0.06);
  display: grid;
  gap: 18px;
}

.brand-header {
  display: grid;
  gap: 8px;
}

.product-badge {
  width: fit-content;
  padding: 4px 8px;
  border: 1px solid rgba(100, 116, 139, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  color: #64748b;
  font-size: 11px;
  letter-spacing: 0.3px;
  font-weight: 500;
}

.brand-kicker {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  letter-spacing: 0.5px;
}

h1 {
  margin: 0;
  font-size: 20px;
  color: #475569;
  font-weight: 500;
}

.brand-title {
  margin: 0 0 12px;
  color: var(--accent);
  font-weight: 600;
  font-size: 32px;
  line-height: 1.2;
}

.brand-subtitle,
.brand-slogan {
  margin: 0;
  color: var(--muted);
  font-size: 16px;
  line-height: 1.45;
}

.brand-slogan {
  margin-top: 20px;
  margin-bottom: 24px;
  font-size: 15px;
}

.value-list {
  margin: 2px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 6px;
  color: #475569;
  font-size: 14px;
}

.value-list li::before {
  content: '▣';
  color: rgba(47, 58, 95, 0.7);
  margin-right: 8px;
}

form {
  display: grid;
  gap: 14px;
}

label {
  display: grid;
  gap: 6px;
  font-size: 12px;
  color: #334155;
  font-weight: 500;
}

input {
  padding: 11px 12px;
  border: 1px solid #d5d9e7;
  border-radius: 10px;
  background: #fff;
  transition: border-color 120ms ease, box-shadow 120ms ease;
}

input:focus-visible {
  border-color: rgba(47, 58, 95, 0.54);
  box-shadow: 0 0 0 3px rgba(47, 58, 95, 0.14);
  outline: none;
}

.submit {
  min-height: 44px;
  padding: 11px 14px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #2f3a5f, #1f2b48);
  color: white;
  cursor: pointer;
  font-weight: 600;
  font-size: 16px;
  transition: transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
}

.submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(47, 58, 95, 0.2);
}

.submit:disabled {
  opacity: 0.68;
  cursor: not-allowed;
}

.error {
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  padding: 9px 10px;
  font-size: 13px;
}

.capability-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 6px;
}

.capability-card {
  border-radius: 14px;
  border: 1px solid rgba(47, 58, 95, 0.14);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
  color: #334155;
  font-size: 14px;
  font-weight: 600;
  padding: 11px 13px;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 10px;
}

.capability-icon {
  width: 20px;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  color: rgba(47, 58, 95, 0.86);
}

.page-footer {
  text-align: center;
  color: rgba(71, 85, 105, 0.9);
  font-size: 12px;
  line-height: 1.45;
  position: relative;
  z-index: 1;
}

.page-footer p {
  margin: 0;
}

@media (max-width: 920px) {
  .login-layout {
    grid-template-columns: 1fr;
    gap: 18px;
  }

  .auth-panel {
    justify-items: stretch;
  }
}

@media (max-width: 640px) {
  .login-page {
    padding: 16px 10px 18px;
  }

  .brand-panel {
    gap: 0;
    padding-left: 0;
  }

  .brand-title {
    font-size: 26px;
  }

  .brand-subtitle,
  .brand-slogan {
    font-size: 14px;
  }

  .login-card {
    padding: 22px;
    border-radius: 16px;
  }

  h1 {
    font-size: 19px;
  }

  .capability-strip {
    grid-template-columns: 1fr;
  }
}
</style>
