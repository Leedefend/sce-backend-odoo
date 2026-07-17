<template>
  <div
    class="shell layout-shell"
    data-component="LayoutShell"
    :class="{
      'shell--configuration': isConfigurationRoute,
      'shell--sidebar-hidden': !mobileViewport && sidebarHidden,
      'shell--mobile-sidebar-open': mobileViewport && mobileSidebarOpen,
    }"
    :data-layout-kind="activeLayout.kind"
    :data-sidebar-mode="activeLayout.sidebar"
    :data-header-mode="activeLayout.header"
    :data-page-identity-source="pageIdentity.identity.value.source"
    :data-page-identity-title="pageTitle"
  >
    <a class="skip-link" href="#main-content">跳至主要内容</a>
    <aside v-if="sidebarVisible" id="primary-sidebar" class="sidebar sidebar-nav" :class="sidebarClass" data-component="SidebarNav" aria-label="主导航">
      <ProductIdentity
        :logo-text="shellLogoText"
        :title="rootTitle"
        :subtitle="sidebarSubtitle"
        :show-close="mobileViewport"
        @close="closeMobileSidebar"
      />

      <div v-if="showRecordContext" class="project-context" :class="{ 'project-context--disabled': !projectContextEnabled }">
        <div class="project-trigger-row">
          <button
            class="project-trigger"
            type="button"
            :disabled="!projectContextEnabled"
            :aria-expanded="projectMenuOpen"
            aria-controls="project-context-menu"
            @click.stop="toggleProjectMenu"
          >
            <span>{{ recordContextLabel }}：</span>
            <strong>{{ currentProjectLabel }}</strong>
          </button>
          <button
            v-if="selectedProject"
            class="project-clear-inline"
            type="button"
            :title="clearRecordContextTitle"
            :aria-label="clearRecordContextTitle"
            @click.stop="clearProjectSelection"
          >
            ×
          </button>
        </div>
        <div v-if="companyOptions.length || operationOptions.length" class="business-scope-controls">
          <label v-if="companyOptions.length" class="business-scope-field">
            <span>公司</span>
            <select aria-label="当前公司" :value="selectedCompanyId || ''" :disabled="companyOptions.length <= 1" @change="changeCompanyScope">
              <option
                v-for="company in companyOptions"
                :key="`company-${company.company_id}`"
                :value="company.company_id"
              >
                {{ company.company_name || `公司 ${company.company_id}` }}
              </option>
            </select>
          </label>
          <div v-if="operationOptions.length" class="business-scope-segments" role="group" :aria-label="recordContextLabel">
            <button
              v-for="operation in operationOptions"
              :key="`operation-${operation.operation_strategy || 'all'}`"
              type="button"
              :class="{ active: operation.operation_strategy === selectedOperationStrategy }"
              :disabled="operation.disabled"
              :title="operation.disabled_reason || operationScopeLabel(operation)"
              @click.stop="changeOperationScope(operation.operation_strategy)"
            >
              {{ operationScopeLabel(operation) }}
            </button>
          </div>
        </div>
        <div v-if="projectMenuOpen && projectContextEnabled" id="project-context-menu" class="project-dropdown" @click.stop>
          <input
            v-model="projectSearch"
            class="project-search sc-search"
            type="search"
            :aria-label="projectSearchPlaceholder"
            :placeholder="projectSearchPlaceholder"
            @input="queueProjectSearch"
            @keydown.enter.prevent="submitProjectSearch"
          />
          <div class="project-options">
            <button
              v-for="option in projectOptions"
              :key="`project-${option.id}`"
              class="project-option sc-list-item"
              :class="{ active: option.id === selectedProject?.id }"
              type="button"
              @click="selectProject(option)"
            >
              <span>{{ projectOptionLabel(option) }}</span>
              <small v-if="option.code">{{ option.code }}</small>
            </button>
            <p v-if="projectSearching" class="project-empty">搜索中...</p>
            <p v-else-if="projectError" class="project-empty">{{ projectError }}</p>
            <p v-else-if="!projectOptions.length" class="project-empty">{{ recordContextEmptyText }}</p>
          </div>
        </div>
      </div>

      <div v-if="showPublishedApps" class="published-apps" data-platform-app-catalog="true">
        <div class="published-apps__header">
          <span>平台发布</span>
          <small v-if="appCatalogLoading">同步中</small>
        </div>
        <div class="published-apps__list">
          <button
            v-for="app in visiblePublishedApps"
            :key="app.key"
            class="published-app"
            :class="{ active: app.appId === activeAppId, 'published-app--loading': app.appId === openingAppId }"
            type="button"
            :disabled="Boolean(openingAppId)"
            @click="openPublishedApp(app)"
          >
            <span class="published-app__mark">{{ appMark(app) }}</span>
            <span class="published-app__label">{{ app.label }}</span>
            <small v-if="appBadge(app)">{{ appBadge(app) }}</small>
          </button>
        </div>
      </div>

      <div class="nav-shell">
        <div class="menu">
          <PrimaryNavigation
            :nodes="filteredMenu"
            :active-menu-id="activeMenuId"
            :capabilities="capabilities"
            :active-path="route.path"
            :search="query"
            @select="handleSelect"
            @navigate="pushRoute"
            @update:search="query = $event"
          />
        </div>
      </div>

      <div class="footer">
        <button v-if="showRefresh" class="ghost sc-btn sc-btn-ghost" @click="refreshInit">刷新</button>
        <button class="ghost sc-btn sc-btn-ghost" @click="logout">退出登录</button>
      </div>
    </aside>
    <button
      v-if="mobileViewport && mobileSidebarOpen"
      class="mobile-sidebar-backdrop"
      type="button"
      aria-label="关闭导航遮罩"
      @click="closeMobileSidebar"
    />

    <section
      class="content"
      :class="{ 'content--with-activity-tabs': activityPages.length }"
    >
      <header
        class="topbar sc-toolbar"
        :class="{ 'topbar--compact': activeLayout.header === 'compact', 'topbar--minimal': useMinimalTopbar }"
      >
        <div class="topbar-main">
          <p v-if="!useMinimalTopbar" class="eyebrow">{{ config.appBrand.name }}</p>
          <div class="topbar-title-row">
            <div class="breadcrumb">
              <button
                v-for="(item, index) in displayBreadcrumb"
                :key="`${item.label}-${index}`"
                class="crumb"
                :class="{ active: index === displayBreadcrumb.length - 1 }"
                :disabled="!item.to"
                :aria-current="index === displayBreadcrumb.length - 1 ? 'page' : undefined"
                @click="item.to && router.push(item.to)"
              >
                {{ item.label }}
              </button>
            </div>
            <h1 v-if="showTopbarHeadline" class="headline">{{ pageTitle }}</h1>
          </div>
          <p v-if="!useMinimalTopbar && topbarSubtitle" class="headline-subtitle">{{ topbarSubtitle }}</p>
        </div>
        <div class="topbar-actions">
          <div class="topbar-context" aria-label="当前工作上下文">
            <span>{{ roleLabel }}</span>
          </div>
          <GlobalMessagePanel />
          <button
            v-if="showMobileWorkShortcut"
            class="mobile-work-shortcut sc-btn sc-btn-sm"
            type="button"
            @click="router.push('/my-work')"
          >
            我的工作
          </button>
          <button
            ref="sidebarToggleButton"
            class="sidebar-toggle sc-btn sc-btn-sm"
            type="button"
            aria-controls="primary-sidebar"
            :aria-expanded="sidebarVisible"
            @click="toggleSidebar"
          >
            {{ mobileViewport ? (mobileSidebarOpen ? '关闭菜单' : '菜单') : (sidebarHidden ? '显示侧边栏' : '隐藏侧边栏') }}
          </button>
          <button
            v-if="isConfigurationRoute"
            class="config-return sc-btn sc-btn-sm"
            type="button"
            @click="returnToBusinessSurface"
          >
            返回业务办理
          </button>
          <button class="theme-switch sc-btn sc-btn-sm" type="button" @click="toggleTheme">主题：{{ themeLabel }}</button>
        </div>
      </header>

      <ActivityPageTabs
        :pages="activityPages"
        :active-key="activeActivityPageKey"
        @activate="activateActivityPage"
        @close="closeActivityPage"
      />

      <StatusPanel
        v-if="initStatus === 'loading'"
        title="正在初始化角色首页..."
        variant="info"
      />
      <StatusPanel
        v-else-if="initStatus === 'error'"
        title="初始化失败"
        :message="initError || '未知错误'"
        :trace-id="initTraceId || undefined"
        variant="error"
        :on-retry="refreshInit"
      />
      <StatusPanel
        v-else-if="showSceneErrors"
        title="场景注册异常"
        :message="sceneErrorMessage"
        variant="error"
      />
      <StatusPanel
        v-else-if="initStatus === 'ready' && !menuCount && !routeAllowsEmptyMenu"
        title="暂无导航数据"
        message="菜单树为空，请尝试刷新初始化。"
        variant="error"
        :on-retry="refreshInit"
      />

      <main v-else id="main-content" class="router-host" tabindex="-1">
        <slot />
      </main>

      <DevContextPanel
        :visible="showHud"
        title="页面上下文"
        :entries="hudEntries"
        :actions="hudActions"
        :message="hudMessage"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, provide, ref, watch } from 'vue';
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router';
import PrimaryNavigation from '../components/product-shell/PrimaryNavigation.vue';
import ProductIdentity from '../components/product-shell/ProductIdentity.vue';
import ActivityPageTabs from '../components/product-shell/ActivityPageTabs.vue';
import StatusPanel from '../components/StatusPanel.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import GlobalMessagePanel from '../components/GlobalMessagePanel.vue';
import { useSessionStore, type ActivityPage } from '../stores/session';
import { intentRequest } from '../api/intents';
import { getSceneByKey, getSceneRegistryDiagnostics, resolveSceneLayout } from '../app/resolvers/sceneRegistry';
import { resolveMenuAction } from '../app/resolvers/menuResolver';
import { isDeliveryModeEnabled, isHudEnabled } from '../config/debug';
import { buildCanonicalSceneRouteTarget, buildEntryTargetRouteTarget, parseSceneKeyFromQuery } from '../app/routeQuery';
import { buildRuntimeNavigationRegistry } from '../app/navigationRegistry';
import { clearPageIdentity, usePageIdentityRuntime } from '../app/pageIdentityRuntime';
import { applyTheme, nextTheme, persistTheme, type ScTheme } from '../styles/theme';
import { config } from '../config';
import { openAction } from '../services/action_service';
import type { BusinessScopeOperationOption, NavNode, ProjectContextOption } from '@sc/schema';
import {
  exportSuggestedActionTraces,
  getLatestSuggestedActionTrace,
  getTraceUpdateEventName,
  rankSuggestedActionKinds,
  summarizeSuggestedActionTraceFilter,
} from '../services/trace';

type UnknownDict = Record<string, unknown>;
type SceneAwareNavNode = NavNode & {
  scene_key?: string;
  sceneKey?: string;
};
type PublishedApp = {
  key: string;
  label: string;
  appId: string;
  category: string;
  badges: Record<string, unknown>;
};
const PROJECT_CONTEXT_CHANGED_EVENT = 'sc:project-context-changed';
const SIDEBAR_HIDDEN_STORAGE_KEY = 'sc_shell_sidebar_hidden';

function asDict(value: unknown): UnknownDict | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null;
  }
  return value as UnknownDict;
}

function asText(value: unknown): string | undefined {
  return typeof value === 'string' && value.trim() ? value : undefined;
}

function asInteger(value: unknown): number | undefined {
  if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
    return Math.trunc(value);
  }
  const text = String(value ?? '').trim();
  if (!text) return undefined;
  const parsed = Number(text);
  if (Number.isFinite(parsed) && parsed > 0) {
    return Math.trunc(parsed);
  }
  return undefined;
}

function stripRoleFromIdentity(identity: string, role: string): string {
  const source = String(identity || '').trim();
  const roleText = String(role || '').trim();
  if (!source || !roleText) return source;
  const escapedRole = roleText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const removedRole = source
    .replace(new RegExp(`[-_· ]*${escapedRole}$`, 'i'), '')
    .replace(new RegExp(`^${escapedRole}[-_· ]*`, 'i'), '')
    .trim();
  return removedRole;
}

function resolveSceneKeyFromNode(node: NavNode): string | undefined {
  const sceneNode = node as SceneAwareNavNode;
  return asText(sceneNode.scene_key) || asText(sceneNode.sceneKey) || asText(node.meta?.scene_key);
}

const session = useSessionStore();
const route = useRoute();
const router = useRouter();
const query = ref('');
const sidebarHidden = ref(false);
const mobileViewport = ref(false);
const mobileSidebarOpen = ref(false);
const sidebarToggleButton = ref<HTMLButtonElement | null>(null);
const projectMenuOpen = ref(false);
const projectSearch = ref('');
const projectSearching = ref(false);
const projectError = ref('');
const appCatalog = ref<PublishedApp[]>([]);
const appCatalogLoading = ref(false);
const appCatalogError = ref('');
const openingAppId = ref('');
let projectSearchTimer: ReturnType<typeof setTimeout> | null = null;
let mobileMediaQuery: MediaQueryList | null = null;

const menuTree = computed(() => session.menuTree);
const roleSurface = computed(() => session.roleSurface);
const shellLogoText = computed(() => config.appBrand.shellLogoText || 'SC');
const rootNode = computed(() => (menuTree.value.length === 1 ? menuTree.value[0] : null));
const menuNodes = computed(() => rootNode.value?.children ?? menuTree.value);
const visibleMenuNodes = computed(() => menuNodes.value);
const menuCount = computed(() => visibleMenuNodes.value.length);
const routeAllowsEmptyMenu = computed(() => route.meta?.adminOnly === true || route.path.startsWith('/admin/'));
const rootTitle = computed(() => {
  const root = rootNode.value;
  const rawTitle = normalizeDeliveryText(root?.title || root?.name || root?.label || '');
  if (!rawTitle || rawTitle === '系统菜单') return config.appBrand.name || '业务工作平台';
  return rawTitle;
});
const userName = computed(() => session.user?.name ?? '访客');
const sidebarSubtitle = computed(() => {
  if (!isDeliveryMode.value) return userName.value;
  const raw = String(userName.value || '').trim();
  if (!raw) return roleLabel.value;
  const stripped = stripRoleFromIdentity(raw, roleLabel.value);
  if (!stripped) return 'Demo账号';
  return normalizeDeliveryText(stripped);
});
const roleLabel = computed(() => {
  const label = String(roleSurface.value?.role_label || '').trim();
  const code = String(roleSurface.value?.role_code || '').trim();
  if (label) return normalizeDeliveryText(label);
  if (code) return normalizeDeliveryText(code.toUpperCase());
  return '当前用户';
});
const projectContext = computed(() => session.projectContext);
const projectContextEnabled = computed(() => Boolean(projectContext.value?.enabled));
const projectContextReasonCode = computed(() => String(projectContext.value?.reason_code || '').trim());
const showRecordContext = computed(() =>
  projectContextEnabled.value || projectContextReasonCode.value !== 'RECORD_CONTEXT_MODEL_NOT_INSTALLED'
);
const selectedProject = computed(() => projectContext.value?.selected ?? null);
const projectOptions = computed(() => projectContext.value?.options ?? []);
const companyOptions = computed(() => projectContext.value?.company_options ?? []);
const operationOptions = computed(() => projectContext.value?.operation_options ?? []);
const selectedCompanyId = computed(() =>
  Number(projectContext.value?.company_id || selectedProject.value?.company_id || 0) || 0,
);
const selectedOperationStrategy = computed(() =>
  String(projectContext.value?.operation_strategy || '').trim(),
);
const recordContextLabel = computed(() =>
  String(projectContext.value?.selector?.label || '当前范围').trim() || '当前范围'
);
const recordContextSubject = computed(() => recordContextLabel.value.replace(/^当前/, '') || '记录');
const recordContextAllLabel = computed(() => String(projectContext.value?.selector?.all_label || '全部').trim() || '全部');
const recordContextEmptyText = computed(() => `无匹配${recordContextSubject.value}`);
const clearRecordContextTitle = computed(() => `清除${recordContextLabel.value}，显示${recordContextAllLabel.value}`);
const currentProjectLabel = computed(() => {
  if (!projectContextEnabled.value) {
    return projectContext.value?.message || '未启用';
  }
  const selected = selectedProject.value;
  if (!selected) return recordContextAllLabel.value;
  return projectNameLabel(selected);
});
const projectSearchPlaceholder = computed(() =>
  String(projectContext.value?.selector?.placeholder || `搜索${recordContextSubject.value}名称`).trim()
    || `搜索${recordContextSubject.value}名称`,
);
const roleLandingPath = computed(() => session.resolveLandingPath('/'));
const capabilities = computed(() => session.capabilities);
const initMeta = computed(() => asDict(session.initMeta));
const isPlatformAdmin = computed(() => session.user?.is_platform_admin === true);
const visiblePublishedApps = computed(() => (isPlatformAdmin.value ? appCatalog.value : []));
const showPublishedApps = computed(() => isPlatformAdmin.value && (visiblePublishedApps.value.length > 0 || appCatalogLoading.value));
const activeAppId = computed(() => {
  return String(route.meta?.appId || '').trim();
});
const effectiveDb = computed(() => asText(initMeta.value?.effective_db) ?? 'N/A');
const navVersion = computed(() => {
  const meta = initMeta.value;
  const navMeta = asDict(meta?.nav_meta);
  const parts = asDict(meta?.parts);
  return asText(meta?.nav_version) || asText(navMeta?.menu) || asText(parts?.nav) || 'N/A';
});
const suggestedActionStamp = ref(0);
const hudMessage = ref('');
const showExtractionStats = ref(false);

const initStatus = computed(() => session.initStatus);
const initError = computed(() => session.initError);
const initTraceId = computed(() => session.initTraceId);
const showSceneErrors = computed(() => import.meta.env.DEV && sceneRegistryErrors.length > 0);
const sceneRegistryErrors = getSceneRegistryDiagnostics().errors;
const routeSceneKey = computed(() => {
  const metaSceneKey = route.meta?.sceneKey as string | undefined;
  const paramSceneKey = typeof route.params.sceneKey === 'string' ? route.params.sceneKey : '';
  return metaSceneKey || paramSceneKey || parseSceneKeyFromQuery(route.query as LocationQueryRaw);
});
const routeScene = computed(() => {
  const key = routeSceneKey.value;
  if (!key) return null;
  return getSceneByKey(key);
});
const routeSceneCapabilityKeys = computed(() => {
  const scene = routeScene.value as { capabilities?: unknown } | null;
  if (!scene || !Array.isArray(scene.capabilities)) return [];
  return scene.capabilities.map((item) => String(item || "").trim()).filter(Boolean);
});
const routeSceneCapabilityGroups = computed(() => {
  const catalog = session.capabilityCatalog || {};
  const groups = new Set<string>();
  routeSceneCapabilityKeys.value.forEach((key) => {
    const meta = catalog[key];
    const groupKey = String(meta?.group_key || "").trim();
    if (groupKey) groups.add(groupKey);
  });
  return [...groups];
});
const activeLayout = computed(() => {
  const sceneKey = routeSceneKey.value;
  const scene = sceneKey ? getSceneByKey(sceneKey) : null;
  return resolveSceneLayout(scene);
});
const businessRouteUsesCompactTopbar = computed(() => ['action', 'record', 'model-form'].includes(String(route.name || '')));
const useMinimalTopbar = computed(() =>
  route.name === 'workbench'
  || route.name === 'home'
  || isConfigurationRoute.value
  || businessRouteUsesCompactTopbar.value,
);
const compactRouteKeepsHeadline = computed(() => [
  'action',
  'menu',
  'record',
  'model-form',
  'access-denied',
  'not-found',
].includes(String(route.name || '')));
const showTopbarHeadline = computed(() => !useMinimalTopbar.value || compactRouteKeepsHeadline.value);
const sidebarClass = computed(() =>
  activeLayout.value.sidebar === 'scroll' ? 'sidebar--scroll' : 'sidebar--fixed'
);
const sceneErrorMessage = computed(() => {
  if (!sceneRegistryErrors.length) {
    return '';
  }
  const sample = sceneRegistryErrors.slice(0, 3).map((err) => {
    const key = err.key ? `key=${err.key}` : `index=${err.index}`;
    return `${key} (${err.issues.join(', ')})`;
  });
  const suffix = sceneRegistryErrors.length > 3 ? ` +${sceneRegistryErrors.length - 3} more` : '';
  return `场景注册校验失败：${sample.join(' | ')}${suffix}`;
});

const menuLabel = computed(() => {
  const menuId = activeMenuId.value;
  if (!menuId) {
    return '';
  }
  const menuPath = findMenuPath(menuTree.value, menuId);
  const node = menuPath[menuPath.length - 1];
  return node?.title || node?.name || node?.label || '';
});

const hudEnabled = computed(() => isHudEnabled(route));
const isDeliveryMode = computed(() => isDeliveryModeEnabled());

function normalizeDeliveryText(input: string) {
  const source = String(input || '').trim();
  if (!source) return '';
  return source.replace(/\s*\(\d+\)\s*$/g, '');
}

function projectOptionLabel(option: ProjectContextOption | null | undefined) {
  if (!option) return '';
  const label = projectNameLabel(option);
  const scope = String(option.operation_strategy_label || option.operation_strategy || '').trim();
  return scope ? `${label} · ${scope}` : label;
}

function projectNameLabel(option: ProjectContextOption | null | undefined) {
  if (!option) return '';
  return String(option.display_name || option.name || `记录 ${option.id}`).trim();
}

function operationScopeLabel(option: BusinessScopeOperationOption | null | undefined) {
  return String(option?.operation_strategy_label || option?.operation_strategy || '').trim() || '全部';
}

function normalizePublishedApps(raw: unknown): PublishedApp[] {
  const row = asDict(raw);
  const source = Array.isArray(row?.apps) ? row.apps : [];
  return source
    .map((item, index) => {
      const app = asDict(item) || {};
      const meta = asDict(app.meta) || {};
      const appId = asText(meta.app_id) || String(app.key || '').replace(/^app:/, '').trim();
      const key = asText(app.key) || `app:${appId || index + 1}`;
      const label = resolvePublishedAppLabel(appId, asText(app.label), key);
      return {
        key,
        label,
        appId,
        category: asText(meta.category) || '',
        badges: asDict(app.badges) || {},
      };
    })
    .filter((app) => app.appId && app.label);
}

function resolvePublishedAppLabel(appId: string, rawLabel: string | undefined, key: string) {
  const backendLabel = String(rawLabel || '').trim();
  return backendLabel || String(appId || '').trim() || key;
}

async function loadPublishedApps() {
  if (!session.token || session.initStatus !== 'ready' || session.user?.is_platform_admin !== true) {
    appCatalog.value = [];
    appCatalogLoading.value = false;
    return;
  }
  appCatalogLoading.value = true;
  appCatalogError.value = '';
  try {
    const result = await intentRequest<unknown>({
      intent: 'app.catalog',
      params: { scene: 'web' },
      silentErrors: true,
    });
    appCatalog.value = normalizePublishedApps(result);
  } catch (err) {
    appCatalog.value = [];
    appCatalogError.value = err instanceof Error ? err.message : '平台应用目录不可用';
  } finally {
    appCatalogLoading.value = false;
  }
}

function appMark(app: PublishedApp) {
  const label = String(app.label || '').trim();
  return label.slice(0, 1) || '应';
}

function appBadge(app: PublishedApp) {
  const todo = Number(app.badges.todo || 0);
  if (Number.isFinite(todo) && todo > 0) return String(Math.trunc(todo));
  return '';
}

function pushRoute(path: string) {
  if (!path) return;
  router.push(path).catch(() => {});
}

function openAppTarget(target: unknown, fallbackAppId: string) {
  const data = asDict(target);
  if (!data) return;
  const subject = String(data.subject || '').trim();
  const routePath = asText(data.route);
  if (subject === 'ui.contract' && routePath) {
    pushRoute(routePath);
    return;
  }
  if (subject === 'menu') {
    const menuId = asInteger(data.id) || asInteger(data.menu_id);
    if (menuId) pushRoute(`/m/${menuId}`);
    return;
  }
  const actionId = asInteger(data.action_id) || asInteger(data.id);
  if (subject === 'action' || actionId) {
    openAction(router, data as never, undefined);
    return;
  }
  if (fallbackAppId === 'workspace') {
    pushRoute('/');
  }
}

async function openPublishedApp(app: PublishedApp) {
  const appId = String(app.appId || '').trim();
  if (!appId || openingAppId.value) return;
  openingAppId.value = appId;
  try {
    const result = await intentRequest<unknown>({
      intent: 'app.open',
      params: {
        app: appId,
        client_type: 'web',
      },
    });
    openAppTarget(result, appId);
  } catch (err) {
    appCatalogError.value = err instanceof Error ? err.message : '应用打开失败';
  } finally {
    openingAppId.value = '';
  }
}

async function loadProjectOptions() {
  if (!projectContextEnabled.value) return;
  projectSearching.value = true;
  projectError.value = '';
  try {
    await session.searchProjectContext(projectSearch.value);
  } catch (err) {
    projectError.value = err instanceof Error ? err.message : '记录搜索失败';
  } finally {
    projectSearching.value = false;
  }
}

function queueProjectSearch() {
  if (projectSearchTimer) {
    clearTimeout(projectSearchTimer);
  }
  projectSearchTimer = setTimeout(() => {
    projectSearchTimer = null;
    void loadProjectOptions();
  }, 260);
}

async function submitProjectSearch(event: KeyboardEvent) {
  if (event.isComposing) return;
  const target = event.currentTarget;
  if (target instanceof HTMLInputElement) {
    projectSearch.value = target.value;
  }
  if (projectSearchTimer) {
    clearTimeout(projectSearchTimer);
    projectSearchTimer = null;
  }
  await loadProjectOptions();
}

async function toggleProjectMenu() {
  if (!projectContextEnabled.value) return;
  projectMenuOpen.value = !projectMenuOpen.value;
  if (projectMenuOpen.value) {
    projectSearch.value = '';
    await loadProjectOptions();
  }
}

async function selectProject(option: ProjectContextOption) {
  const previousProjectId = Number(selectedProject.value?.id || 0) || 0;
  const nextProjectId = Number(option?.id || 0) || 0;
  projectMenuOpen.value = false;
  if (previousProjectId === nextProjectId) return;
  await session.selectProjectContext(option);
  emitProjectContextChanged(previousProjectId);
}

async function changeCompanyScope(event: Event) {
  const target = event.currentTarget;
  if (!(target instanceof HTMLSelectElement)) return;
  const companyId = Number(target.value || 0) || null;
  const previousProjectId = Number(selectedProject.value?.id || 0) || 0;
  const applied = await session.selectBusinessScope({
    company_id: companyId,
    operation_strategy: selectedOperationStrategy.value,
  });
  if (applied === false) return;
  emitProjectContextChanged(previousProjectId, true);
}

async function changeOperationScope(operationStrategy: string) {
  const normalized = String(operationStrategy || '').trim();
  if (normalized === selectedOperationStrategy.value) return;
  const previousProjectId = Number(selectedProject.value?.id || 0) || 0;
  const applied = await session.selectBusinessScope({
    company_id: selectedCompanyId.value || null,
    operation_strategy: normalized,
  });
  if (applied === false) return;
  emitProjectContextChanged(previousProjectId, true);
}

async function clearProjectSelection() {
  const previousProjectId = Number(selectedProject.value?.id || 0) || 0;
  projectMenuOpen.value = false;
  if (!previousProjectId) return;
  await session.selectProjectContext(null);
  emitProjectContextChanged(previousProjectId);
}

const pageIdentity = usePageIdentityRuntime();
const pageTitle = computed(() => pageIdentity.title.value);
const topbarSubtitle = computed(() => pageIdentity.subtitle.value);

provide('pageTitle', pageTitle);
const showHud = computed(() => isPlatformAdmin.value && hudEnabled.value && !isDeliveryMode.value);
const themeMode = ref<ScTheme>('system');
const themeLabel = computed(() => (themeMode.value === 'system' ? '跟随系统' : themeMode.value === 'dark' ? '暗色' : '亮色'));

function loadThemeMode(): ScTheme {
  try {
    const raw = localStorage.getItem('sc_theme');
    if (raw === 'light' || raw === 'dark' || raw === 'system') return raw;
  } catch {
    // ignore
  }
  return 'system';
}

function toggleTheme(): void {
  themeMode.value = nextTheme(themeMode.value);
  persistTheme(themeMode.value);
}

function loadSidebarHidden(): boolean {
  try {
    return localStorage.getItem(SIDEBAR_HIDDEN_STORAGE_KEY) === '1';
  } catch {
    return false;
  }
}

function persistSidebarHidden(hidden: boolean): void {
  try {
    localStorage.setItem(SIDEBAR_HIDDEN_STORAGE_KEY, hidden ? '1' : '0');
  } catch {
    // ignore
  }
}

const sidebarVisible = computed(() => mobileViewport.value ? mobileSidebarOpen.value : !sidebarHidden.value);
const showMobileWorkShortcut = computed(() => mobileViewport.value && !['my-work', 'scene-my-work'].includes(String(route.name || '')));

async function closeMobileSidebar(): Promise<void> {
  const wasOpen = mobileSidebarOpen.value;
  mobileSidebarOpen.value = false;
  if (wasOpen) {
    await nextTick();
    sidebarToggleButton.value?.focus();
  }
}

function syncMobileViewport(event?: MediaQueryListEvent): void {
  const matches = event?.matches ?? mobileMediaQuery?.matches ?? false;
  mobileViewport.value = matches;
  if (!matches) mobileSidebarOpen.value = false;
}

function handleShellEscape(event: KeyboardEvent): void {
  if (event.key === 'Escape' && mobileSidebarOpen.value) closeMobileSidebar();
}

function toggleSidebar(): void {
  if (mobileViewport.value) {
    mobileSidebarOpen.value = !mobileSidebarOpen.value;
    return;
  }
  sidebarHidden.value = !sidebarHidden.value;
  persistSidebarHidden(sidebarHidden.value);
}

const runtimeNavigationRegistry = computed(() =>
  buildRuntimeNavigationRegistry({
    scenes: session.scenes || [],
    capabilityCatalog: session.capabilityCatalog || {},
  })
);
const currentEntrySource = computed(() => {
  if (routeSceneKey.value) return 'scene';
  if (route.name === 'action' || route.name === 'record') return 'capability';
  return '-';
});
const roleSceneCoverage = computed(() => {
  const candidates = Array.isArray(roleSurface.value?.scene_candidates) ? roleSurface.value?.scene_candidates || [] : [];
  const normalizedCandidates = candidates.map((item) => String(item || '').trim()).filter(Boolean);
  const sceneSet = new Set(runtimeNavigationRegistry.value.sceneEntries.map((entry) => String(entry.sceneKey || '').trim()).filter(Boolean));
  const matched = normalizedCandidates.filter((key) => sceneSet.has(key));
  const missing = normalizedCandidates.filter((key) => !sceneSet.has(key));
  return {
    total: normalizedCandidates.length,
    matchedCount: matched.length,
    missingCount: missing.length,
    missingPreview: missing.slice(0, 6).join(',') || '-',
  };
});
const latestSuggestedAction = computed(() => {
  const stamp = suggestedActionStamp.value;
  void stamp;
  return getLatestSuggestedActionTrace();
});
const latestSuggestedActionTs = computed(() => {
  const ts = latestSuggestedAction.value?.ts;
  if (!ts) return '-';
  try {
    return new Date(ts).toISOString();
  } catch {
    return String(ts);
  }
});
const extractionStats = computed(() => {
  const workspace = (session.workspaceHome && typeof session.workspaceHome === 'object')
    ? session.workspaceHome as Record<string, unknown>
    : {};
  const diagnostics = (workspace.diagnostics && typeof workspace.diagnostics === 'object')
    ? workspace.diagnostics as Record<string, unknown>
    : {};
  const stats = (diagnostics.extraction_stats && typeof diagnostics.extraction_stats === 'object')
    ? diagnostics.extraction_stats as Record<string, unknown>
    : {};
  return stats;
});

const sceneGovernanceSnapshot = computed(() => {
  const value = session.sceneGovernanceV1;
  if (!value || typeof value !== 'object') {
    return null;
  }
  return value as Record<string, unknown>;
});

const sceneGovernanceGatesSummary = computed(() => {
  const gates = asDict(sceneGovernanceSnapshot.value?.gates);
  if (!gates) return '-';
  return [
    `orchestrator=${Boolean(gates.orchestrator_applied)}`,
    `governance=${Boolean(gates.governance_applied)}`,
    `delivery=${Boolean(gates.delivery_policy_applied)}`,
    `nav_policy_ok=${Boolean(gates.nav_policy_validation_ok)}`,
    `auto_degrade=${Boolean(gates.auto_degrade_triggered)}`,
  ].join(' | ');
});

const sceneGovernanceReasonsSummary = computed(() => {
  const reasons = asDict(sceneGovernanceSnapshot.value?.reasons);
  if (!reasons) return '-';
  const autoCodes = Array.isArray(reasons.auto_degrade_reason_codes)
    ? reasons.auto_degrade_reason_codes.map((item) => String(item || '')).filter(Boolean)
    : [];
  const resolveCodes = Array.isArray(reasons.resolve_error_codes)
    ? reasons.resolve_error_codes.map((item) => String(item || '')).filter(Boolean)
    : [];
  return `auto=[${autoCodes.join(',') || '-'}] resolve=[${resolveCodes.join(',') || '-'}]`;
});

const sceneGovernanceConsumptionSummary = computed(() => {
  const consumption = asDict(sceneGovernanceSnapshot.value?.scene_ready_consumption);
  if (!consumption) return '-';
  const enabled = Boolean(consumption.enabled);
  const sceneTypes = Number(consumption.scene_type_count || 0);
  const scenes = Number(consumption.scene_count || 0);
  const aggregate = asDict(consumption.aggregate);
  const baseRate = asDict(aggregate?.base_fact_consumption_rate);
  const surfaceRate = asDict(aggregate?.surface_nonempty_rate);
  const searchBase = Number(baseRate?.search || 0).toFixed(2);
  const actionSurface = Number(surfaceRate?.action_surface || 0).toFixed(2);
  return `enabled=${enabled} types=${sceneTypes} scenes=${scenes} base.search=${searchBase} surface.action=${actionSurface}`;
});

const hudEntries = computed(() => {
  const entries = [
  { label: 'scene_key', value: routeSceneKey.value || '-' },
  { label: 'entry_source', value: currentEntrySource.value },
  { label: 'nav_entry_total', value: runtimeNavigationRegistry.value.entries.length || 0 },
  { label: 'nav_scene_entries', value: runtimeNavigationRegistry.value.sceneEntries.length || 0 },
  { label: 'nav_cap_entries', value: runtimeNavigationRegistry.value.capabilityEntries.length || 0 },
  { label: 'role_scene_candidates', value: roleSceneCoverage.value.total || 0 },
  { label: 'role_scene_matched', value: roleSceneCoverage.value.matchedCount || 0 },
  { label: 'role_scene_missing', value: roleSceneCoverage.value.missingCount || 0 },
  { label: 'role_scene_missing_keys', value: roleSceneCoverage.value.missingPreview },
  { label: 'role_scope', value: String(roleSurface.value?.role_code || '-') },
  { label: 'requested_surface', value: String(route.query.surface || '-') },
  { label: 'scene_capability_count', value: routeSceneCapabilityKeys.value.length || 0 },
  { label: 'scene_capabilities', value: routeSceneCapabilityKeys.value.slice(0, 8).join(',') || '-' },
  { label: 'scene_capability_groups', value: routeSceneCapabilityGroups.value.join(',') || '-' },
  { label: 'menu_id', value: activeMenuId.value || '-' },
  { label: 'menu_label', value: menuLabel.value || '-' },
  { label: 'route', value: route.fullPath },
  { label: 'user', value: userName.value || '-' },
  { label: 'db', value: effectiveDb.value || '-' },
  { label: 'nav_version', value: navVersion.value || '-' },
  { label: 'model', value: asText(asDict(session.currentAction)?.model) || '-' },
  { label: 'sa_kind', value: latestSuggestedAction.value?.suggested_action_kind || '-' },
  { label: 'sa_success', value: String(latestSuggestedAction.value?.suggested_action_success ?? '-') },
  { label: 'sa_ts', value: latestSuggestedActionTs.value },
  ];
  if (sceneGovernanceSnapshot.value) {
    entries.push(
      { label: 'governance.scene_channel', value: String(sceneGovernanceSnapshot.value.scene_channel || '-') },
      { label: 'governance.runtime_source', value: String(sceneGovernanceSnapshot.value.runtime_source || '-') },
      { label: 'governance.gates', value: sceneGovernanceGatesSummary.value },
      { label: 'governance.reasons', value: sceneGovernanceReasonsSummary.value },
      { label: 'governance.scene_ready_consumption', value: sceneGovernanceConsumptionSummary.value },
    );
  }
  if (showExtractionStats.value) {
    entries.push(
      { label: 'extract.business_collections', value: String(extractionStats.value.business_collections ?? '-') },
      { label: 'extract.business_rows_total', value: String(extractionStats.value.business_rows_total ?? '-') },
      { label: 'extract.today_business', value: String(extractionStats.value.today_actions_business ?? '-') },
      { label: 'extract.today_fallback', value: String(extractionStats.value.today_actions_fallback ?? '-') },
      { label: 'extract.risk_business', value: String(extractionStats.value.risk_actions_business ?? '-') },
      { label: 'extract.risk_fallback', value: String(extractionStats.value.risk_actions_fallback ?? '-') },
    );
  }
  return entries;
});
const defaultKindActions = ['open_record', 'copy_trace', 'refresh'];
const hudActions = computed(() => [
  {
    key: 'toggle-extract-stats',
    label: showExtractionStats.value ? 'Hide extract stats' : 'Show extract stats',
    onClick: () => {
      showExtractionStats.value = !showExtractionStats.value;
      hudMessage.value = showExtractionStats.value
        ? 'Extraction stats are visible in HUD.'
        : 'Extraction stats are hidden.';
    },
  },
  { key: 'export-sa-all', label: 'Export SA all', onClick: () => exportSuggestedActionJson() },
  { key: 'export-sa-ok', label: 'Export SA ok', onClick: () => exportSuggestedActionJson({ success: true }, 'ok') },
  { key: 'export-sa-fail', label: 'Export SA fail', onClick: () => exportSuggestedActionJson({ success: false }, 'fail') },
  { key: 'export-sa-1h', label: 'Export SA 1h', onClick: () => exportSuggestedActionJson({ since_ts: sinceTsFromHours(1) }, '1h') },
  { key: 'export-sa-24h', label: 'Export SA 24h', onClick: () => exportSuggestedActionJson({ since_ts: sinceTsFromHours(24) }, '24h') },
  ...resolveKindExportActions(),
]);

function resolveKindExportActions() {
  const rankedKinds = rankSuggestedActionKinds(3).map((item) => item.kind);
  const chosenKinds = [...new Set([...rankedKinds, ...defaultKindActions])].slice(0, 3);
  return chosenKinds.map((kind) => ({
    key: `export-sa-kind-${kind}`,
    label: `Export SA ${kind}`,
    onClick: () => exportSuggestedActionJson({ kind }, `kind-${kind}`),
  }));
}

function handleTraceUpdate() {
  suggestedActionStamp.value = Date.now();
}

function closeProjectMenu() {
  projectMenuOpen.value = false;
}

function emitProjectContextChanged(previousProjectId = 0, scopeChanged = false) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(PROJECT_CONTEXT_CHANGED_EVENT, {
    detail: {
      previous_project_id: previousProjectId || null,
      selected_project_id: selectedProject.value?.id || null,
      scope_changed: scopeChanged,
    },
  }));
}

function downloadTextAsFile(filename: string, content: string, mimeType = 'application/json') {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function sanitizeExportSuffix(value: string) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'all';
}

function sinceTsFromHours(hours: number) {
  const safeHours = Math.max(1, Number(hours || 1));
  return Date.now() - safeHours * 60 * 60 * 1000;
}

function exportSuggestedActionJson(filter: { success?: boolean; kind?: string; since_ts?: number } = {}, suffix = 'all') {
  try {
    const content = exportSuggestedActionTraces({ ...filter, limit: 200 });
    const now = new Date().toISOString().replace(/[:.]/g, '-');
    downloadTextAsFile(`suggested-action-traces-${sanitizeExportSuffix(suffix)}-${now}.json`, content);
    const filterSummary = summarizeSuggestedActionTraceFilter(filter);
    const details = [suffix, filterSummary].filter(Boolean).join(', ');
    hudMessage.value = `Exported suggested_action traces (${details}).`;
  } catch {
    hudMessage.value = 'Failed to export suggested_action traces.';
  }
}

onMounted(() => {
  themeMode.value = loadThemeMode();
  sidebarHidden.value = loadSidebarHidden();
  applyTheme(themeMode.value);
  showExtractionStats.value = String(route.query.hud_stats || '').trim() === '1';
  void loadPublishedApps();
  if (typeof window === 'undefined') return;
  mobileMediaQuery = window.matchMedia('(max-width: 960px)');
  syncMobileViewport();
  mobileMediaQuery.addEventListener('change', syncMobileViewport);
  window.addEventListener('keydown', handleShellEscape);
  window.addEventListener(getTraceUpdateEventName(), handleTraceUpdate as (event: Event) => void);
  window.addEventListener('click', closeProjectMenu);
  handleTraceUpdate();
});

watch(
  () => [session.initStatus, session.token, session.projectContext?.selected?.id],
  () => {
    void loadPublishedApps();
  },
);

onUnmounted(() => {
  if (typeof window === 'undefined') return;
  mobileMediaQuery?.removeEventListener('change', syncMobileViewport);
  mobileMediaQuery = null;
  window.removeEventListener('keydown', handleShellEscape);
  window.removeEventListener(getTraceUpdateEventName(), handleTraceUpdate as (event: Event) => void);
  window.removeEventListener('click', closeProjectMenu);
  if (projectSearchTimer) {
    clearTimeout(projectSearchTimer);
    projectSearchTimer = null;
  }
});

function findMenuPath(nodes: NavNode[], menuId?: number): NavNode[] {
  if (!menuId) {
    return [];
  }
  const walk = (items: NavNode[], parents: NavNode[] = []): NavNode[] | null => {
    for (const node of items) {
      const nextParents = [...parents, node];
      if (node.menu_id === menuId || node.id === menuId) {
        return nextParents;
      }
      if (node.children?.length) {
        const found = walk(node.children, nextParents);
        if (found) {
          return found;
        }
      }
    }
    return null;
  };
  return walk(menuTree.value, []) || [];
}

function findMenuIdBySceneKey(nodes: NavNode[], sceneKey?: string): number | undefined {
  const target = String(sceneKey || '').trim();
  if (!target) return undefined;
  const walk = (items: NavNode[]): number | undefined => {
    for (const node of items) {
      const currentSceneKey = resolveSceneKeyFromNode(node);
      if (currentSceneKey === target) {
        return asInteger(node.menu_id) || asInteger(node.id);
      }
      if (node.children?.length) {
        const matched = walk(node.children);
        if (matched) return matched;
      }
    }
    return undefined;
  };
  return walk(nodes);
}

const displayBreadcrumb = computed(() => pageIdentity.breadcrumbs.value);

const showRefresh = computed(
  () => !isDeliveryMode.value && (import.meta.env.DEV || localStorage.getItem('DEBUG_INTENT') === '1'),
);

const activeMenuId = computed(() => {
  if (route.name === 'menu') {
    return Number(route.params.menuId ?? 0) || undefined;
  }
  const fromQuery = asInteger(route.query.menu_id);
  if (fromQuery) return fromQuery;

  const activeSceneKey = String(routeSceneKey.value || '').trim();
  const fromScene = findMenuIdBySceneKey(menuTree.value, activeSceneKey);
  if (fromScene) return fromScene;

  return undefined;
});

function filterNodes(nodes: NavNode[], q: string): NavNode[] {
  const term = q.trim().toLowerCase();
  if (!term) {
    return nodes;
  }
  const matches = (node: NavNode) => {
    const label = node.title || node.name || node.label || '';
    return label.toLowerCase().includes(term);
  };
  const walk = (items: NavNode[]): NavNode[] => {
    return items
      .map((node) => {
        const children = node.children ? walk(node.children) : [];
        if (matches(node) || children.length) {
          return { ...node, children };
        }
        return null;
      })
      .filter(Boolean) as NavNode[];
  };
  return walk(nodes);
}

const filteredMenu = computed(() => filterNodes(visibleMenuNodes.value, query.value));
const isConfigurationRoute = computed(() => route.path.startsWith('/admin/'));
const activityPages = computed(() => (isConfigurationRoute.value ? [] : session.activityPages));
const activeActivityPageKey = computed(() => (isConfigurationRoute.value ? '' : session.activeActivityPageKey));

function buildMenuSelectionQuery(): LocationQueryRaw {
  const next: LocationQueryRaw = {};
  const passthroughKeys = ['db', 'debug', 'hud_stats'];
  passthroughKeys.forEach((key) => {
    const value = route.query[key];
    if (value !== undefined && value !== null && value !== '') {
      next[key] = value;
    }
  });
  return next;
}

function handleSelect(node: NavNode) {
  closeMobileSidebar();
  if (!node.menu_id && node.id) {
    node.menu_id = node.id as number;
  }
  const targetMenuId = Number(node.menu_id || node.id || 0);
  const menuQuery = buildMenuSelectionQuery();
  if (targetMenuId <= 0) return;
  const resolved = resolveMenuAction(menuTree.value, targetMenuId);
  if (resolved.kind === 'redirect') {
    const entryTarget = asDict(resolved.target?.entry_target);
    if (entryTarget) {
      router.push(buildEntryTargetRouteTarget(entryTarget, {
        query: menuQuery,
        menuId: targetMenuId,
        actionId: resolved.target?.action_id,
      })).catch(() => {});
      return;
    }
  }
  if (resolved.kind === 'redirect' && resolved.target?.scene_key) {
    const sceneKey = String(resolved.target.scene_key || '').trim();
    const scene = sceneKey ? getSceneByKey(sceneKey) : null;
    if (sceneKey && scene) {
      router.push(buildCanonicalSceneRouteTarget(sceneKey, {
        scene,
        query: menuQuery,
        menuId: targetMenuId,
        actionId: resolved.target.action_id || scene.target?.action_id,
      })).catch(() => {});
      return;
    }
  }
  if (resolved.kind === 'redirect' && resolved.target?.meta?.action_id) {
    openAction(router, resolved.target.meta as never, targetMenuId);
    return;
  }
  if (resolved.kind === 'leaf' && resolved.meta?.action_id) {
    openAction(router, resolved.meta as never, targetMenuId);
    return;
  }
  router.push(`/m/${targetMenuId}`).catch(() => {});
}

function returnToBusinessSurface() {
  router.push(roleLandingPath.value || '/').catch(() => {});
}

function resolveActivityPageRoute(page: ActivityPage): string {
  const baseRoute = String(page.route || '').trim();
  if (!baseRoute || !page.runtime_query || !Object.keys(page.runtime_query).length) return baseRoute;
  const [beforeHash, hashText = ''] = baseRoute.split('#', 2);
  const [path, queryText = ''] = beforeHash.split('?', 2);
  const params = new URLSearchParams(queryText);
  Object.entries(page.runtime_query).forEach(([key, raw]) => {
    params.delete(key);
    const values = Array.isArray(raw) ? raw : [raw];
    values.forEach((value) => {
      const text = String(value || '').trim();
      if (text) params.append(key, text);
    });
  });
  const nextQuery = params.toString();
  const hash = hashText ? `#${hashText}` : '';
  return `${path}${nextQuery ? `?${nextQuery}` : ''}${hash}`;
}

async function activateActivityPage(page: ActivityPage) {
  if (!page?.key || !page.route) return;
  await session.applyActivityProjectContext(page.project_context);
  const targetRoute = resolveActivityPageRoute(page);
  if (route.fullPath !== targetRoute) {
    await router.push(targetRoute).catch(() => {});
  }
  session.markActivityPageActive(page.key);
}

async function closeActivityPage(page: ActivityPage) {
  if (!page?.key) return;
  const wasActive = page.key === activeActivityPageKey.value;
  const nextPage = session.closeActivityPage(page.key);
  if (!wasActive) return;
  if (nextPage) {
    await activateActivityPage(nextPage);
    return;
  }
  await router.push(roleLandingPath.value || '/').catch(() => {});
}

async function refreshInit() {
  await session.loadAppInit();
}

async function logout() {
  await session.logout();
  clearPageIdentity();
  router.push('/login');
}
</script>

<style scoped src="./AppShell.css"></style>
