<template>
  <main class="login-page sc-page">
    <section class="login-layout">
      <section class="brand-panel" aria-label="平台介绍">
        <p class="brand-title">{{ pageText('brand_name', config.appBrand.name) }}</p>
        <p class="brand-subtitle">{{ pageText('brand_subtitle', config.appBrand.subtitle) }}</p>
        <p class="brand-slogan">{{ pageText('brand_slogan', config.appBrand.slogan) }}</p>

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
            class="ghost sc-btn sc-btn-ghost sc-btn-sm"
            :disabled="loading"
            @click="executeHeaderAction(action.key)"
          >
            {{ action.label || action.key }}
          </button>
        </section>

        <section
          v-if="pageSectionEnabled('card', true) && pageSectionTagIs('card', 'section')"
          class="login-card sc-panel"
          :style="pageSectionStyle('card')"
        >
          <header class="brand-header">
            <span class="product-badge">{{ config.appBrand.productBadge }}</span>
            <p class="brand-kicker">{{ config.appBrand.kicker }}</p>
            <h1>{{ pageText('title', loginTitleFallback) }}</h1>
          </header>

          <form
            v-if="pageSectionEnabled('form', true) && pageSectionTagIs('form', 'section')"
            class="sc-form"
            :style="pageSectionStyle('form')"
            @submit.prevent="onSubmit"
          >
            <label class="sc-form-label">
              {{ pageText('username_label', '账号') }}
              <input
                id="login-username"
                v-model="username"
                class="sc-input"
                autocomplete="username"
                :placeholder="pageText('username_placeholder', '请输入账号')"
                :disabled="loading"
                required
                :aria-invalid="Boolean(error)"
                :aria-describedby="error ? 'login-error' : undefined"
              />
            </label>
            <label class="sc-form-label">
              {{ pageText('password_label', '密码') }}
              <input
                id="login-password"
                v-model="password"
                class="sc-input"
                type="password"
                autocomplete="current-password"
                :placeholder="pageText('password_placeholder', '请输入密码')"
                :disabled="loading"
                required
                :aria-invalid="Boolean(error)"
                :aria-describedby="error ? 'login-error' : undefined"
              />
            </label>
            <label class="sc-form-label">
              {{ pageText('db_label', '数据库') }}
              <input
                v-model="dbName"
                class="sc-input"
                autocomplete="off"
                :placeholder="pageText('db_placeholder', '请输入数据库名（如 sc_minimal）')"
                :disabled="dbInputDisabled"
              />
            </label>
            <p
              v-if="pageSectionEnabled('error', true) && pageSectionTagIs('error', 'section') && error"
              id="login-error"
              class="error sc-alert sc-alert-danger"
              role="alert"
              :style="pageSectionStyle('error')"
            >
              {{ error }}
            </p>
            <button class="submit sc-btn sc-btn-primary" type="submit" :disabled="loading">{{ loading ? pageText('submit_loading', '系统正在登录，请稍候…') : pageText('submit_idle', '登录') }}</button>
          </form>
        </section>
      </section>
    </section>

    <footer class="page-footer">
      <p>{{ config.appBrand.footerPrimary }}</p>
      <p>{{ config.appBrand.footerSecondary }}</p>
    </footer>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import { isConfiguredDbPinned, isPlatformAdminEntryRuntime, resolveConfiguredDb } from '../services/dbContext';
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
  resolveConfiguredDb(String(config.odooDb || '').trim()),
);
const loading = ref(false);
const error = ref('');
const headerActions = computed(() => pageGlobalActions.value);
const dbInputDisabled = computed(() => loading.value || isConfiguredDbPinned());
const loginTitleFallback = computed(() => isPlatformAdminEntryRuntime() ? '平台管理员登录' : '登录');
const capabilityItems = computed(() => [
  { key: 'project', icon: '📊', label: pageText('capability_project', config.appBrand.capabilities.project) },
  { key: 'contract_cost', icon: '📑', label: pageText('capability_contract_cost', config.appBrand.capabilities.contractCost) },
  { key: 'fund', icon: '💰', label: pageText('capability_fund', config.appBrand.capabilities.fund) },
  { key: 'risk', icon: '⚠', label: pageText('capability_risk', config.appBrand.capabilities.risk) },
]);
const valueLines = computed(() => config.appBrand.valueLines.map((line, index) => pageText(`value_line_${index + 1}`, line)));

watch([username, password], () => {
  if (error.value) error.value = '';
});

watch(
  () => route.fullPath,
  () => {
    if (!loading.value) {
      dbName.value = resolveConfiguredDb(String(config.odooDb || '').trim());
    }
  },
);

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
      : isPlatformAdminEntryRuntime() ? '/?platform_admin=1' : session.resolveLandingPath('/');
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
  --ink: var(--sc-app-text-primary);
  --muted: var(--sc-app-text-secondary);
  --accent: var(--sc-semantic-surface-interactive);
  min-height: 100vh;
  display: grid;
  place-items: center;
  gap: 18px;
  background: var(--sc-app-bg);
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
  transition: border-color 120ms ease, transform 120ms ease;
}

.ghost:hover:not(:disabled) {
  border-color: var(--sc-app-border-strong);
  transform: translateY(-1px);
}

.login-card {
  width: 100%;
  padding: 32px;
  display: grid;
  gap: 18px;
}

.brand-header {
  display: grid;
  gap: 8px;
}

.product-badge {
  width: fit-content;
  padding: calc(var(--sc-component-badge-padding-y) * 1px) calc(var(--sc-component-badge-padding-x) * 1px);
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-badge-radius);
  background: var(--sc-app-subtle-bg);
  color: var(--sc-app-text-secondary);
  font-size: 11px;
  letter-spacing: 0;
  font-weight: 500;
}

.brand-kicker {
  margin: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  letter-spacing: 0.5px;
}

h1 {
  margin: 0;
  font-size: 20px;
  color: var(--sc-app-text-secondary);
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
  color: var(--sc-app-text-secondary);
  font-size: 14px;
}

.value-list li::before {
  content: '▣';
  color: var(--sc-semantic-surface-interactive);
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
  color: var(--sc-app-text-secondary);
  font-weight: 500;
}

input {
  padding: 11px 12px;
  border: 1px solid var(--sc-app-border-strong);
  border-radius: var(--sc-component-input-radius);
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  transition: border-color 120ms ease, box-shadow 120ms ease;
}

input:focus-visible {
  border-color: var(--sc-semantic-surface-interactive);
  box-shadow: 0 0 0 3px var(--sc-app-focus-ring);
  outline: none;
}

.submit {
  min-height: 44px;
  padding: 11px 14px;
  font-weight: 600;
  font-size: 16px;
  transition: transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
}

.submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--sc-semantic-shadow-popover);
}

.error {
  font-size: 13px;
}

.capability-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 6px;
}

.capability-card {
  border-radius: var(--sc-component-card-radius);
  border: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
  box-shadow: var(--sc-app-shadow);
  color: var(--sc-app-text-primary);
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
  color: var(--sc-semantic-surface-interactive);
}

.page-footer {
  text-align: center;
  color: var(--sc-app-text-secondary);
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
