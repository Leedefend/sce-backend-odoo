<template>
  <div
    class="shell layout-shell"
    data-component="LayoutShell"
    :data-layout-kind="activeLayout.kind"
    :data-sidebar-mode="activeLayout.sidebar"
    :data-header-mode="activeLayout.header"
  >
    <aside class="sidebar sidebar-nav" :class="sidebarClass" data-component="SidebarNav">
      <div class="brand">
        <div class="logo">{{ shellLogoText }}</div>
        <div>
          <p class="title">{{ rootTitle }}</p>
          <p class="subtitle">{{ sidebarSubtitle }}</p>
        </div>
      </div>

      <p class="enterprise-line">当前企业：{{ enterpriseLabel }}</p>

      <div v-if="showRecordContext" class="project-context" :class="{ 'project-context--disabled': !projectContextEnabled }">
        <div class="project-trigger-row">
          <button
            class="project-trigger"
            type="button"
            :disabled="!projectContextEnabled"
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
        <div v-if="projectMenuOpen && projectContextEnabled" class="project-dropdown" @click.stop>
          <input
            v-model="projectSearch"
            class="project-search sc-search"
            type="search"
            :placeholder="projectSearchPlaceholder"
            @input="queueProjectSearch"
            @keydown.enter.prevent="selectFirstProject"
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

      <div class="role-surface">
        <p class="role-label">当前角色：{{ roleLabel }}</p>
        <div class="role-actions">
          <button
            v-if="showRoleLandingAction"
            class="ghost mini"
            :title="roleLandingTitle"
            @click="openRoleLanding"
          >
            {{ roleLandingActionLabel }}
          </button>
          <button class="ghost mini" @click="router.push('/my-work')">我的工作</button>
        </div>
      </div>

      <div class="nav-shell">
        <div class="search">
          <input v-model="query" type="search" placeholder="搜索菜单..." />
        </div>

        <div class="menu">
          <MenuTree
            :nodes="filteredMenu"
            :active-menu-id="activeMenuId"
            :capabilities="capabilities"
            @select="handleSelect"
          />
        </div>
      </div>

      <div class="footer">
        <button v-if="showRefresh" class="ghost sc-btn sc-btn-ghost" @click="refreshInit">刷新</button>
        <button class="ghost sc-btn sc-btn-ghost" @click="logout">退出登录</button>
      </div>
    </aside>

    <section class="content" :class="{ 'content--scene-compact': sceneHeaderMinimal }">
      <header
        class="topbar"
        :class="{ 'topbar--compact': activeLayout.header === 'compact', 'topbar--minimal': useMinimalTopbar, 'topbar--scene-minimal': sceneHeaderMinimal }"
      >
        <div class="topbar-main">
          <p v-if="!useMinimalTopbar && !sceneHeaderMinimal" class="eyebrow">智能工程协作平台</p>
          <div v-if="!sceneHeaderMinimal" class="breadcrumb">
            <button
              v-for="(item, index) in breadcrumb"
              :key="`${item.label}-${index}`"
              class="crumb"
              :class="{ active: index === breadcrumb.length - 1 }"
              :disabled="!item.to"
              @click="item.to && router.push(item.to)"
            >
              {{ item.label }}
            </button>
          </div>
          <p v-if="!useMinimalTopbar && sceneHeaderMinimal && sceneHeaderAnchorLine" class="scene-anchor-line">{{ sceneHeaderAnchorLine }}</p>
          <h1 v-if="!useMinimalTopbar && !sceneHeaderMinimal" class="headline">{{ pageTitle }}</h1>
          <p v-if="!useMinimalTopbar && !sceneHeaderMinimal && topbarSubtitle" class="headline-subtitle">{{ topbarSubtitle }}</p>
        </div>
        <div class="topbar-actions">
          <button class="theme-switch sc-btn" type="button" @click="toggleTheme">主题：{{ themeLabel }}</button>
        </div>
      </header>

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
        v-else-if="initStatus === 'ready' && !menuCount"
        title="暂无导航数据"
        message="菜单树为空，请尝试刷新初始化。"
        variant="error"
        :on-retry="refreshInit"
      />

      <div v-else class="router-host">
        <slot />
      </div>

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
import { computed, onMounted, onUnmounted, provide, ref } from 'vue';
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router';
import MenuTree from '../components/MenuTree.vue';
import StatusPanel from '../components/StatusPanel.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import { useSessionStore } from '../stores/session';
import { getSceneByKey, getSceneRegistryDiagnostics, resolveSceneLayout } from '../app/resolvers/sceneRegistry';
import { resolveMenuAction } from '../app/resolvers/menuResolver';
import { isDeliveryModeEnabled, isHudEnabled } from '../config/debug';
import { buildCanonicalSceneRouteTarget, buildEntryTargetRouteTarget, parseSceneKeyFromQuery } from '../app/routeQuery';
import { buildRuntimeNavigationRegistry } from '../app/navigationRegistry';
import { applyTheme, nextTheme, persistTheme, type ScTheme } from '../styles/theme';
import { config } from '../config';
import type { NavNode, ProjectContextOption } from '@sc/schema';
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
const PROJECT_CONTEXT_CHANGED_EVENT = 'sc:project-context-changed';

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
const projectMenuOpen = ref(false);
const projectSearch = ref('');
const projectSearching = ref(false);
const projectError = ref('');
let projectSearchTimer: ReturnType<typeof setTimeout> | null = null;

const menuTree = computed(() => session.menuTree);
const roleSurface = computed(() => session.roleSurface);
const shellLogoText = computed(() => config.appBrand.shellLogoText || 'SC');
const rootNode = computed(() => (menuTree.value.length === 1 ? menuTree.value[0] : null));
const menuNodes = computed(() => rootNode.value?.children ?? menuTree.value);
const menuCount = computed(() => menuNodes.value.length);
const rootTitle = computed(() => {
  const root = rootNode.value;
  return normalizeDeliveryText(root?.title || root?.name || root?.label || '智能工程协作平台');
});
const userName = computed(() => session.user?.name ?? '访客');
const enterpriseLabel = computed(() => {
  const user = session.user as Record<string, unknown> | null;
  const company = user?.company;
  if (company && typeof company === 'object' && !Array.isArray(company)) {
    const nested = company as Record<string, unknown>;
    const name = String(nested.name || nested.display_name || '').trim();
    if (name) return name;
  }
  if (Array.isArray(company) && company.length >= 2) {
    const name = String(company[1] || '').trim();
    if (name) return name;
  }
  const directName = String(user?.company_name || '').trim();
  if (directName) return directName;
  return effectiveDb.value && effectiveDb.value !== 'N/A' ? effectiveDb.value : '默认企业';
});
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
  if (isDeliveryMode.value) {
    return resolveDeliveryRoleLabel(label, code);
  }
  if (label) return normalizeDeliveryText(label);
  if (code) return normalizeDeliveryText(code.toUpperCase());
  return '负责人';
});
const projectContext = computed(() => session.projectContext);
const projectContextEnabled = computed(() => Boolean(projectContext.value?.enabled));
const projectContextReasonCode = computed(() => String(projectContext.value?.reason_code || '').trim());
const showRecordContext = computed(() =>
  projectContextEnabled.value || projectContextReasonCode.value !== 'RECORD_CONTEXT_MODEL_NOT_INSTALLED'
);
const selectedProject = computed(() => projectContext.value?.selected ?? null);
const projectOptions = computed(() => projectContext.value?.options ?? []);
const recordContextLabel = computed(() =>
  String(projectContext.value?.selector?.label || '当前记录').trim() || '当前记录'
);
const recordContextEmptyText = computed(() => `无匹配${recordContextLabel.value.replace(/^当前/, '')}`);
const clearRecordContextTitle = computed(() => `清除${recordContextLabel.value}，显示全部记录`);
const currentProjectLabel = computed(() => {
  if (!projectContextEnabled.value) {
    return projectContext.value?.message || '未启用';
  }
  const selected = selectedProject.value;
  if (!selected) return '全部记录';
  return projectOptionLabel(selected);
});
const projectSearchPlaceholder = computed(() =>
  String(projectContext.value?.selector?.placeholder || '搜索项目名称').trim() || '搜索项目名称',
);
const roleLandingPath = computed(() => session.resolveLandingPath('/'));
const roleLandingActionLabel = computed(() => {
  const sceneKey = String(session.defaultRoute?.scene_key || roleSurface.value?.landing_scene_key || '').trim();
  if (sceneKey) {
    const scene = getSceneByKey(sceneKey);
    const label = String(scene?.label || '').trim();
    if (label && label !== '工作台' && label !== '角色首页') return label;
    if (label) return '角色首页';
  }
  const path = String(roleLandingPath.value || '').trim();
  if (path === '/' || path === '/home' || path === '/workbench' || path === '/s/workspace.home') return '角色首页';
  if (path === '/my-work' || path === '/s/my_work.workspace') return '我的工作';
  return '默认入口';
});
const roleLandingTitle = computed(() => `打开当前角色默认入口：${roleLandingActionLabel.value}`);
const showRoleLandingAction = computed(() => roleLandingActionLabel.value !== '角色首页');
const capabilities = computed(() => session.capabilities);
const initMeta = computed(() => asDict(session.initMeta));
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
const businessRouteUsesCompactTopbar = computed(() => route.name === 'action' || route.name === 'record');
const useMinimalTopbar = computed(() =>
  route.name === 'workbench'
  || route.name === 'home'
  || businessRouteUsesCompactTopbar.value,
);
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
  return source
    .replace(/\s*\(\d+\)\s*$/g, '')
    .replace(/^project\s*manager$/i, '项目经理')
    .replace(/^purchase\s*manager$/i, '采购经理')
    .replace(/^finance$/i, '财务主管')
    .replace(/^executive$/i, '管理层')
    .replace(/^ops$/i, '运维专员')
    .replace(/^admin$/i, '系统管理员');
}

function resolveDeliveryRoleLabel(roleLabelRaw: string, roleCodeRaw: string) {
  const normalizedLabel = normalizeDeliveryText(roleLabelRaw);
  if (/[^\u0020-\u007e]/.test(normalizedLabel) && normalizedLabel) return normalizedLabel;
  const code = String(roleCodeRaw || '').trim().toLowerCase();
  if (/pm|project/.test(code)) return '项目经理';
  if (/finance/.test(code)) return '财务主管';
  if (/purchase|material/.test(code)) return '采购经理';
  if (/executive|boss|leader/.test(code)) return '管理层';
  if (/ops|operation/.test(code)) return '运维专员';
  if (/admin/.test(code)) return '系统管理员';
  return normalizedLabel || '负责人';
}

function projectOptionLabel(option: ProjectContextOption | null | undefined) {
  if (!option) return '';
  return String(option.display_name || option.name || `记录 ${option.id}`).trim();
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
    void loadProjectOptions();
  }, 260);
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
  projectMenuOpen.value = false;
  await session.selectProjectContext(option);
  emitProjectContextChanged();
}

async function clearProjectSelection() {
  projectMenuOpen.value = false;
  await session.selectProjectContext(null);
  emitProjectContextChanged();
}

async function selectFirstProject() {
  const first = projectOptions.value[0];
  if (first) {
    await selectProject(first);
  }
}

function resolveActionBusinessTitle(action: unknown) {
  const source = asDict(action);
  if (!source) return '';
  const uiTitle = asText(source.ui_title);
  if (uiTitle) return uiTitle;
  const sceneTitle = asText(source.scene_title);
  if (sceneTitle) return sceneTitle;
  const menuTitle = asText(source.menu_title);
  if (menuTitle) return menuTitle;
  const actionName = asText(source.name);
  if (actionName) return actionName;
  return '';
}

const pageTitle = computed(() => {
  const sceneKey = routeSceneKey.value;
  if (sceneKey) {
    const scene = getSceneByKey(sceneKey);
    if (scene?.label) {
      return scene.label;
    }
  }
  if (menuLabel.value) {
    return menuLabel.value;
  }
  const actionBusinessTitle = resolveActionBusinessTitle(session.currentAction);
  if (actionBusinessTitle) {
    return actionBusinessTitle;
  }
  if (hudEnabled.value) {
    const currentAction = asDict(session.currentAction);
    const modelLabel = asText(currentAction?.model_label) || asText(currentAction?.model);
    if (modelLabel) {
      return modelLabel;
    }
  }
  if (route.name === 'workbench') {
    return '导航异常';
  }
  if (route.name === 'record') {
    return '记录';
  }
  return '角色首页';
});

const topbarSubtitle = computed(() => {
  const sceneKey = String(routeSceneKey.value || '').trim();
  if (sceneKey === 'projects.intake') {
    return '创建项目 · 填写基础信息完成立项';
  }
  return '';
});

const sceneHeaderMinimal = computed(() => [
  'projects.intake',
  'workspace.home',
  'dashboard.company',
].includes(String(routeSceneKey.value || '').trim()));

const sceneHeaderAnchorLine = computed(() => {
  if (!sceneHeaderMinimal.value) return '';
  if (String(routeSceneKey.value || '').trim() !== 'projects.intake') return '';
  return '项目立项 / 创建项目';
});

provide('pageTitle', pageTitle);
const showHud = computed(() => hudEnabled.value && !isDeliveryMode.value);
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

function emitProjectContextChanged() {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(PROJECT_CONTEXT_CHANGED_EVENT, {
    detail: {
      selected_project_id: selectedProject.value?.id || null,
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
  applyTheme(themeMode.value);
  showExtractionStats.value = String(route.query.hud_stats || '').trim() === '1';
  if (typeof window === 'undefined') return;
  window.addEventListener(getTraceUpdateEventName(), handleTraceUpdate as (event: Event) => void);
  window.addEventListener('click', closeProjectMenu);
  handleTraceUpdate();
});

onUnmounted(() => {
  if (typeof window === 'undefined') return;
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

function isRootContainerMenuId(menuId?: number): boolean {
  const root = rootNode.value;
  if (!root || !menuId) return false;
  const rootId = Number(root.menu_id || root.id || 0);
  return rootId > 0 && rootId === Number(menuId);
}

const breadcrumb = computed(() => {
  const crumbs: Array<{ label: string; to?: string }> = [];
  const menuId = activeMenuId.value;
  const menuPath = findMenuPath(menuTree.value, menuId);
  if (menuPath.length) {
    menuPath.forEach((node) => {
      const label = node.title || node.name || node.label || '菜单';
      const id = node.menu_id ?? node.id;
      if (id) {
        crumbs.push({ label, to: isRootContainerMenuId(Number(id)) ? undefined : `/m/${id}` });
      }
    });
  }
  if (route.name === 'action') {
    const label = session.currentAction?.name || `动作 ${route.params.actionId ?? ''}`.trim();
    crumbs.push({ label });
  }
  if (route.name === 'record') {
    const recordLabel = `记录 ${route.params.id ?? ''}`.trim();
    crumbs.push({ label: recordLabel });
  }
  if (!crumbs.length) {
    crumbs.push({ label: '角色首页' });
  }
  return crumbs;
});

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

const filteredMenu = computed(() => filterNodes(menuNodes.value, query.value));

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
  if (!node.menu_id && node.id) {
    node.menu_id = node.id as number;
  }
  const targetMenuId = Number(node.menu_id || node.id || 0);
  if (targetMenuId <= 0) return;
  const resolved = resolveMenuAction(menuTree.value, targetMenuId);
  const menuQuery = buildMenuSelectionQuery();
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
  router.push(`/m/${targetMenuId}`).catch(() => {});
}

function openRoleLanding() {
  router.push(roleLandingPath.value).catch(() => {});
}

async function refreshInit() {
  await session.loadAppInit();
}

async function logout() {
  await session.logout();
  router.push('/login');
}
</script>

<style scoped>
.shell {
  --surface: var(--sc-semantic-surface-page);
  --ink: var(--sc-semantic-text-primary);
  --muted: var(--sc-semantic-text-secondary);
  --accent: var(--sc-semantic-surface-interactive);
  --accent-2: #e07a5f;
  --panel: var(--sc-semantic-surface-panel);
  --layout-divider: #e5e7eb;
  min-height: 100vh;
  height: 100vh;
  overflow: hidden;
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  background: var(--sc-app-bg);
  color: var(--ink);
  font-family: "Inter", "PingFang SC", "Microsoft YaHei", "Noto Sans SC", system-ui, sans-serif;
}

.sidebar {
  padding: 18px 14px 14px;
  display: grid;
  grid-template-rows: auto auto auto auto minmax(0, 1fr) auto;
  gap: 10px;
  border-right: 1px solid var(--sc-app-border);
  background: transparent;
  height: 100vh;
  overflow: hidden;
  position: sticky;
  top: 0;
  align-self: start;
}

.sidebar--scroll {
  overflow: auto;
}

.brand {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 1px 2px 6px;
}

.enterprise-line {
  margin: 0;
  padding: 0 2px;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
}

.logo {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #2f3a5f, #1b263b);
  color: white;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.6px;
}

.title {
  font-weight: 700;
  font-size: 16px;
  line-height: 1.1;
  margin: 0;
  color: #0f172a;
}

.subtitle {
  margin: 0;
  font-size: 11px;
  color: #9ca3af;
}

.nav-shell {
  border: 0;
  border-radius: 0;
  background: transparent;
  padding: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 6px;
  min-height: 0;
  overflow: hidden;
}

.search input {
  width: 100%;
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  font-size: 13px;
  color: #0f172a;
}

.role-surface {
  padding: 8px 4px 10px;
  border-bottom: 1px solid #e5e7eb;
  border-radius: 0;
  border-left: 0;
  border-right: 0;
  border-top: 0;
  background: transparent;
  display: grid;
  gap: 6px;
}

.project-context {
  position: relative;
  padding: 0 0 6px;
  border-bottom: 1px solid #e5e7eb;
}

.project-trigger-row {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 18px;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.project-trigger {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  border: 0;
  background: transparent;
  padding: 0 2px;
  display: flex;
  gap: 2px;
  align-items: center;
  justify-content: flex-start;
  text-align: left;
  color: #64748b;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
}

.project-trigger span {
  flex: 0 0 auto;
}

.project-trigger strong {
  flex: 1 1 auto;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #334155;
  font-size: 12px;
  font-weight: 600;
}

.project-trigger:disabled {
  cursor: default;
  opacity: 0.7;
}

.project-clear-inline {
  width: 18px;
  height: 18px;
  min-width: 18px;
  border: 1px solid #cbd5e1;
  border-radius: 50%;
  background: #ffffff;
  color: #64748b;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.project-clear-inline:hover {
  border-color: #94a3b8;
  color: #0f172a;
  background: #f8fafc;
}

.project-dropdown {
  position: absolute;
  z-index: 30;
  top: 24px;
  left: 0;
  right: 0;
  display: grid;
  gap: 6px;
  padding: 8px;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.16);
}

.project-search {
  width: 100%;
  border: 1px solid #dbe3ef;
  border-radius: 6px;
  padding: 7px 8px;
  font-size: 12px;
  color: #0f172a;
}

.project-options {
  display: grid;
  gap: 2px;
  max-height: 220px;
  overflow: auto;
}

.project-option {
  border: 0;
  border-radius: 6px;
  background: transparent;
  padding: 7px 8px;
  display: grid;
  gap: 2px;
  text-align: left;
  cursor: pointer;
  color: #334155;
}

.project-option:hover,
.project-option.active {
  background: #eef2ff;
  color: #1e3a8a;
}

.project-option span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 600;
}

.project-option small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  color: #64748b;
}

.project-empty {
  margin: 0;
  padding: 8px;
  color: #94a3b8;
  font-size: 12px;
}

.role-label {
  margin: 0;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
}

.role-actions {
  display: flex;
  gap: 4px;
}

.menu {
  overflow: auto;
  padding-right: 2px;
  padding-top: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: stretch;
}

.footer {
  display: grid;
  gap: 6px;
  border-top: 1px solid #e5e7eb;
  padding-top: 8px;
  padding-bottom: calc(8px + env(safe-area-inset-bottom));
  background: transparent;
}

.ghost {
  padding: 7px 9px;
  border-radius: 6px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  color: #475569;
}

.content {
  padding: 10px 20px;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 6px;
  min-width: 0;
  height: 100vh;
  overflow: auto;
  overscroll-behavior: contain;
  background: #f8fafc;
}

.content--scene-compact {
  gap: 4px;
  padding: 10px 20px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  min-width: 0;
  background: var(--panel);
  border-radius: 10px;
  padding: 6px 10px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
}

.topbar-main {
  min-width: 0;
  flex: 1 1 320px;
}

.topbar--compact {
  padding: 6px 10px;
}

.topbar--scene-minimal {
  background: transparent;
  box-shadow: none;
  border: 0;
  border-radius: 0;
  padding: 0;
}

.scene-anchor-line {
  margin: 0;
  font-size: 12px;
  color: #94a3b8;
}

.topbar--compact .breadcrumb {
  display: none;
}

.topbar--compact .headline {
  font-size: 20px;
}

.topbar--minimal {
  background: transparent;
  box-shadow: none;
  border-radius: 0;
  border: none;
  padding: 0 2px;
}

.topbar--minimal .breadcrumb {
  margin: 0;
  gap: 6px;
}

.topbar--minimal .crumb {
  padding: 3px 6px;
  font-size: 13px;
  font-weight: 500;
  text-transform: none;
  letter-spacing: 0;
  color: #64748b;
}

.topbar--minimal .crumb.active {
  background: transparent;
  color: #334155;
  font-weight: 600;
}

.eyebrow {
  margin: 0;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}

.headline {
  margin: 2px 0 0;
  font-size: 20px;
  line-height: 1.12;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.headline-subtitle {
  margin: 2px 0 0;
  font-size: 11px;
  color: #94a3b8;
}

.breadcrumb {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 0;
  min-width: 0;
}

.crumb {
  background: transparent;
  border: 1px solid transparent;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0;
  text-transform: uppercase;
  color: #64748b;
  cursor: pointer;
  max-width: 100%;
  overflow-wrap: anywhere;
}

.crumb.active {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
}

.crumb:disabled {
  cursor: default;
  opacity: 0.6;
}

.router-host {
  min-height: 0;
  min-width: 0;
  overflow: visible;
}

@media (max-width: 960px) {
  .shell {
    grid-template-columns: 1fr;
    height: auto;
    min-height: 100vh;
    overflow: visible;
  }
  .sidebar {
    grid-row: 2;
    border-right: none;
    border-top: 1px solid rgba(15, 23, 42, 0.08);
    height: auto;
    position: static;
  }
  .content {
    height: auto;
    overflow: visible;
  }

}
</style>


.topbar-actions {
  display: flex;
  align-items: center;
}
.theme-switch {
  border: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  border-radius: 8px;
  padding: 6px 10px;
  cursor: pointer;
}
