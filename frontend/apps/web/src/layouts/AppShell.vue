<template>
  <div
    class="shell layout-shell"
    :class="{ 'layout-shell--sidebar-compact': compactSidebarEnabled }"
    data-component="LayoutShell"
    :data-layout-kind="activeLayout.kind"
    :data-sidebar-mode="activeLayout.sidebar"
    :data-header-mode="activeLayout.header"
  >
    <aside class="sidebar sidebar-nav" :class="[sidebarClass, { 'sidebar--delivery-compact': compactSidebarEnabled }]" data-component="SidebarNav">
      <div class="brand">
        <div class="logo">SC</div>
        <div>
          <p class="title">{{ rootTitle }}</p>
          <p class="subtitle">{{ sidebarSubtitle }}</p>
        </div>
      </div>

      <p v-if="!compactSidebarEnabled" class="enterprise-line">当前企业：{{ enterpriseLabel }}</p>

      <div v-if="!compactSidebarEnabled" class="role-surface">
        <p class="role-label">当前角色：{{ roleLabel }}</p>
        <div v-if="!compactSidebarEnabled" class="role-actions">
          <button class="ghost mini" @click="openRoleLanding">进入工作台</button>
          <button class="ghost mini" @click="router.push('/my-work')">我的工作</button>
          <button v-if="showReleaseOperatorEntry" class="ghost mini" @click="router.push('/release/operator')">发布控制</button>
        </div>
        <div v-if="roleMenus.length && !compactSidebarEnabled" class="role-menus">
          <button
            v-for="menu in roleMenus"
            :key="`role-menu-${menu.id}`"
            class="role-menu-item"
            @click="openRoleMenu(menu.id)"
          >
            {{ normalizeDeliveryText(menu.label) }}
          </button>
        </div>
      </div>

      <div class="nav-shell">
        <div class="search">
          <input v-model="query" type="search" placeholder="搜索菜单..." />
        </div>

        <div v-if="showReleaseSummary" class="release-summary">
          <span class="release-summary__chip release-summary__chip--stable">
            正式发布 {{ stableGroupCount }} 组 / {{ stableLeafCount }} 项
          </span>
          <span class="release-summary__chip release-summary__chip--preview">
            原生预发布 {{ nativePreviewGroupCount }} 组 / {{ nativePreviewLeafCount }} 项
          </span>
        </div>

        <div class="menu">
          <MenuTree
            :nodes="filteredMenu"
            :active-menu-id="activeMenuId"
            @select="handleSelect"
          />
        </div>
      </div>

      <div class="footer">
        <button v-if="showRefresh" class="ghost" @click="refreshInit">刷新</button>
        <button class="ghost" @click="logout">退出登录</button>
      </div>
    </aside>

    <section class="content" :class="{ 'content--scene-compact': sceneHeaderMinimal, 'content--flat-action': hideTopbarForActionList }">
      <header
        v-if="!hideTopbarForActionList"
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
          <p v-if="!useMinimalTopbar && sceneHeaderMinimal" class="scene-anchor-line">{{ sceneHeaderAnchorLine }}</p>
          <h1 v-if="!useMinimalTopbar && !sceneHeaderMinimal" class="headline">{{ pageTitle }}</h1>
          <p v-if="!useMinimalTopbar && !sceneHeaderMinimal && topbarSubtitle" class="headline-subtitle">{{ topbarSubtitle }}</p>
        </div>
      </header>

      <StatusPanel
        v-if="initStatus === 'loading'"
        title="正在初始化工作台..."
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
import { isDeliveryModeEnabled, isHudEnabled } from '../config/debug';
import { parseSceneKeyFromQuery } from '../app/routeQuery';
import { buildRuntimeNavigationRegistry } from '../app/navigationRegistry';
import { useNavigationMenu } from '../composables/useNavigationMenu';
import type { ExplainedMenuNode } from '../types/navigation';
import {
  exportSuggestedActionTraces,
  getLatestSuggestedActionTrace,
  getTraceUpdateEventName,
  rankSuggestedActionKinds,
  summarizeSuggestedActionTraceFilter,
} from '../services/trace';

type UnknownDict = Record<string, unknown>;

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

const session = useSessionStore();
const route = useRoute();
const router = useRouter();
const query = ref('');
const navigationMenu = useNavigationMenu();

const releaseNavigationMeta = computed(() => asDict(session.deliveryEngineV1?.meta));
const roleSurface = computed(() => session.roleSurface);
const navigationTree = computed(() => navigationMenu.tree.value);
const rootNode = computed(() => (navigationTree.value.length === 1 ? navigationTree.value[0] : null));
const menuNodes = computed(() => rootNode.value?.children ?? navigationTree.value);
const menuCount = computed(() => menuNodes.value.length);
const nativePreviewGroupKey = computed(() => asText(releaseNavigationMeta.value?.native_preview_group_key) || '');
const stableGroupCount = computed(() => asInteger(releaseNavigationMeta.value?.stable_group_count) || 0);
const nativePreviewGroupCount = computed(() => asInteger(releaseNavigationMeta.value?.native_preview_group_count) || 0);
const stableLeafCount = computed(() => asInteger(releaseNavigationMeta.value?.stable_leaf_count) || 0);
const nativePreviewLeafCount = computed(() => asInteger(releaseNavigationMeta.value?.native_preview_leaf_count) || 0);
const showReleaseSummary = computed(() => false);
const rootTitle = computed(() => {
  const root = rootNode.value;
  return normalizeDeliveryText(root?.name || '智能工程协作平台');
});
const userName = computed(() => session.user?.name ?? '访客');
const enterpriseLabel = computed(() => {
  const enablementName = String(session.enterpriseEnablement?.current_company_name || '').trim();
  if (enablementName) return enablementName;
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
const roleLandingPath = computed(() => session.resolveLandingPath('/'));
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
  return metaSceneKey || parseSceneKeyFromQuery(route.query as LocationQueryRaw);
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
const compactActionShellEnabled = computed(() => String(import.meta.env.VITE_ACTION_SHELL_COMPACT || '1').trim() !== '0');
const hideTopbarForActionList = computed(() => {
  if (!compactActionShellEnabled.value) return false;
  return route.name === 'action' || route.name === 'model-form' || route.name === 'record';
});
const compactSidebarEnabled = computed(() => String(import.meta.env.VITE_SIDEBAR_COMPACT || '1').trim() !== '0');
const useMinimalTopbar = computed(() => route.name === 'workbench' || route.name === 'home');
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
  const menuPath = findMenuPath(navigationTree.value, menuId);
  const node = menuPath[menuPath.length - 1];
  return node?.name || '';
});

const hudEnabled = computed(() => isHudEnabled(route));
const isDeliveryMode = computed(() => isDeliveryModeEnabled());
const showReleaseOperatorEntry = computed(() => {
  const roleCode = String(roleSurface.value?.role_code || '').trim().toLowerCase();
  return ['pm', 'executive', 'admin'].includes(roleCode);
});

function normalizeDeliveryText(input: string) {
  const source = String(input || '').trim();
  if (!source) return '';
  return source.replace(/\s*\(\d+\)\s*$/g, '');
}

function resolveDeliveryRoleLabel(roleLabelRaw: string, roleCodeRaw: string) {
  const normalizedLabel = normalizeDeliveryText(roleLabelRaw);
  if (/[^\u0020-\u007e]/.test(normalizedLabel) && normalizedLabel) return normalizedLabel;
  const code = String(roleCodeRaw || '').trim().toLowerCase();
  if (normalizedLabel) return normalizedLabel;
  if (code) return normalizeDeliveryText(code.toUpperCase());
  return '负责人';
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
  const routeName = String(route.name || '').trim();
  const routeModel = asText(route.params.model);
  if (routeName === 'record') {
    if (routeModel === 'project.project') {
      return '项目详情';
    }
    if (routeModel) {
      return `${routeModel} 详情`;
    }
  }
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
  return '工作台';
});

const topbarSubtitle = computed(() => {
  return String(route.meta?.sceneSubtitle || '').trim();
});

const sceneHeaderMinimal = computed(() => String(route.meta?.sceneHeaderMode || '').trim() === 'minimal');

const sceneHeaderAnchorLine = computed(() => {
  return sceneHeaderMinimal.value ? String(route.meta?.sceneAnchorLine || '').trim() : '';
});

provide('pageTitle', pageTitle);
const showHud = computed(() => hudEnabled.value && !isDeliveryMode.value);
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
  showExtractionStats.value = String(route.query.hud_stats || '').trim() === '1';
  if (typeof window === 'undefined') return;
  window.addEventListener(getTraceUpdateEventName(), handleTraceUpdate as (event: Event) => void);
  handleTraceUpdate();
  navigationMenu.loadNavigation().catch(async () => {
    try {
      await session.loadAppInit();
      await navigationMenu.loadNavigation(true);
    } catch {
      // keep shell stable; error state is exposed by navigation composable
    }
  });
});

onUnmounted(() => {
  if (typeof window === 'undefined') return;
  window.removeEventListener(getTraceUpdateEventName(), handleTraceUpdate as (event: Event) => void);
});

function findMenuPath(nodes: ExplainedMenuNode[], menuId?: number): ExplainedMenuNode[] {
  if (!menuId) {
    return [];
  }
  const walk = (items: ExplainedMenuNode[], parents: ExplainedMenuNode[] = []): ExplainedMenuNode[] | null => {
    for (const node of items) {
      const nextParents = [...parents, node];
      if (node.menu_id === menuId) {
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
  return walk(navigationTree.value, []) || [];
}

function parseSceneKeyFromPath(path: string): string {
  const matched = String(path || '').match(/^\/s\/([^/?#]+)/);
  return matched?.[1] ? decodeURIComponent(matched[1]) : '';
}

function parseActionIdFromPath(path: string): number | undefined {
  const actionMatched = String(path || '').match(/^\/(?:a|native\/action)\/(\d+)/);
  return actionMatched?.[1] ? asInteger(actionMatched[1]) : undefined;
}

const currentRouteContext = computed(() => {
  const menuId = asInteger(route.query.menu_id) || asInteger(route.params.menuId);
  const sceneKey = String(routeSceneKey.value || parseSceneKeyFromPath(route.path) || '').trim();
  const actionId = parseActionIdFromPath(route.path);
  const fullPath = String(route.fullPath || route.path || '').trim();
  return {
    menuId,
    sceneKey,
    actionId,
    fullPath,
  };
});

function matchesActiveNode(node: ExplainedMenuNode): boolean {
  const active = node.active_match || {};
  const menuId = asInteger(active.menu_id);
  const sceneKey = asText(active.scene_key);
  const actionId = asInteger(active.action_id);
  const routePrefix = asText(active.route_prefix);
  const current = currentRouteContext.value;
  if (menuId && current.menuId && menuId === current.menuId) return true;
  if (sceneKey && current.sceneKey && sceneKey === current.sceneKey) return true;
  if (actionId && current.actionId && actionId === current.actionId) return true;
  if (routePrefix && current.fullPath && current.fullPath.startsWith(routePrefix)) return true;
  return false;
}

function findActiveMenuId(nodes: ExplainedMenuNode[]): number | undefined {
  const walk = (items: ExplainedMenuNode[]): number | undefined => {
    for (const node of items) {
      if (matchesActiveNode(node)) {
        return asInteger(node.menu_id);
      }
      if (node.children?.length) {
        const found = walk(node.children);
        if (found) return found;
      }
    }
    return undefined;
  };
  return walk(nodes);
}

const breadcrumb = computed(() => {
  const crumbs: Array<{ label: string; to?: string }> = [];
  const menuId = activeMenuId.value;
      const menuPath = findMenuPath(navigationTree.value, menuId);
  if (menuPath.length) {
    menuPath.forEach((node) => {
      const label = node.name || '菜单';
      const routePath = node.is_clickable && node.target_type !== 'directory' && node.target_type !== 'unavailable'
        ? asText(node.route)
        : undefined;
      crumbs.push({ label, to: routePath });
    });
  }
  if (route.name === 'action') {
    const label = session.currentAction?.name || `动作 ${route.params.actionId ?? ''}`.trim();
    crumbs.push({ label });
  }
  if (route.name === 'record') {
    const recordModel = asText(route.params.model);
    const recordId = String(route.params.id ?? '').trim();
    const recordLabel = recordModel === 'project.project'
      ? '项目详情'
      : `记录 ${recordId}`.trim();
    crumbs.push({ label: recordLabel });
  }
  if (!crumbs.length) {
    crumbs.push({ label: '工作台' });
  }
  return crumbs;
});

const showRefresh = computed(
  () => !isDeliveryMode.value && (import.meta.env.DEV || localStorage.getItem('DEBUG_INTENT') === '1'),
);

const activeMenuId = computed(() => {
  return findActiveMenuId(navigationTree.value);
});

function filterNodes(nodes: ExplainedMenuNode[], q: string): ExplainedMenuNode[] {
  const term = q.trim().toLowerCase();
  if (!term) {
    return nodes;
  }
  const matches = (node: ExplainedMenuNode) => {
    const label = node.name || '';
    return label.toLowerCase().includes(term);
  };
  const walk = (items: ExplainedMenuNode[]): ExplainedMenuNode[] => {
    return items
      .map((node) => {
        const children = node.children ? walk(node.children) : [];
        if (matches(node) || children.length) {
          return { ...node, children };
        }
        return null;
      })
      .filter(Boolean) as ExplainedMenuNode[];
  };
  return walk(nodes);
}

const filteredMenu = computed(() => filterNodes(menuNodes.value, query.value));
const roleMenus = computed(() => {
  const allow = new Set(roleSurface.value?.menu_xmlids || []);
  if (!allow.size) return [];
  const found: Array<{ id: number; label: string }> = [];
  const seen = new Set<number>();
  const walk = (nodes: ExplainedMenuNode[]) => {
    for (const node of nodes) {
      const xmlid = String(node.key || '').trim();
      const id = Number(node.menu_id || 0);
      if (xmlid && allow.has(xmlid) && id && !seen.has(id)) {
        seen.add(id);
        found.push({ id, label: node.name || `菜单 ${id}` });
      }
      if (node.children?.length) {
        walk(node.children);
      }
    }
  };
  walk(navigationTree.value);
  return found.slice(0, 6);
});

function navigateByExplainedMenuNode(node: ExplainedMenuNode) {
  if (!node.is_clickable) {
    return;
  }
  if (node.target_type === 'directory' || node.target_type === 'unavailable') {
    return;
  }
  const routePath = asText(node.route);
  if (!routePath) {
    return;
  }
  router.push(routePath).catch(() => {});
}

function handleSelect(node: ExplainedMenuNode) {
  navigateByExplainedMenuNode(node);
}

function findMenuNodeById(nodes: ExplainedMenuNode[], menuId: number): ExplainedMenuNode | null {
  const walk = (items: ExplainedMenuNode[]): ExplainedMenuNode | null => {
    for (const node of items) {
      if (node.menu_id === menuId) {
        return node;
      }
      if (node.children?.length) {
        const found = walk(node.children);
        if (found) return found;
      }
    }
    return null;
  };
  return walk(nodes);
}

function openRoleLanding() {
  router.push(roleLandingPath.value).catch(() => {});
}

function openRoleMenu(menuId: number) {
  const node = findMenuNodeById(navigationTree.value, menuId);
  if (!node) {
    return;
  }
  navigateByExplainedMenuNode(node);
}

async function refreshInit() {
  await session.loadAppInit();
  await navigationMenu.loadNavigation(true);
}

async function logout() {
  await session.logout();
  router.push('/login');
}
</script>

<style scoped>
.shell {
  --surface: #f6f3ef;
  --ink: #161616;
  --muted: #6b7280;
  --accent: #2f3a5f;
  --accent-2: #e07a5f;
  --panel: #ffffff;
  --layout-divider: #e5e7eb;
  min-height: 100vh;
  height: 100vh;
  overflow: hidden;
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  background: linear-gradient(180deg, #f8fafc 0%, #f3f5f8 100%);
  color: var(--ink);
  font-family: "Inter", "PingFang SC", "Microsoft YaHei", "Noto Sans SC", system-ui, sans-serif;
}

.layout-shell--sidebar-compact {
  grid-template-columns: 198px minmax(0, 1fr);
}

.sidebar {
  padding: 18px 14px 14px;
  display: grid;
  grid-template-rows: auto auto auto minmax(0, 1fr) auto;
  gap: 10px;
  border-right: 1px solid #e5e7eb;
  background: transparent;
  height: 100vh;
  overflow: hidden;
  position: sticky;
  top: 0;
  align-self: start;
}

.sidebar--delivery-compact {
  padding: 12px 10px 10px;
  gap: 8px;
}

.sidebar--delivery-compact .brand {
  padding: 0 1px 4px;
}

.sidebar--delivery-compact .logo {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  font-size: 11px;
}

.sidebar--delivery-compact .title {
  font-size: 14px;
}

.sidebar--delivery-compact .subtitle {
  font-size: 10px;
}

.sidebar--delivery-compact .role-surface {
  padding: 0 2px;
}

.sidebar--delivery-compact :deep(.label) {
  padding: 5px 8px;
  font-size: 13px;
}

.sidebar--delivery-compact :deep(.tree) {
  gap: 1px;
  margin-left: 0 !important;
  padding-left: 0 !important;
  border-left: 0 !important;
}

.sidebar--delivery-compact :deep(.node) {
  gap: 3px;
}

.sidebar--delivery-compact :deep(.toggle),
.sidebar--delivery-compact :deep(.toggle-spacer) {
  width: 14px;
  flex-basis: 14px;
}

.sidebar--delivery-compact :deep(.label .badge) {
  display: none;
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
  padding: 0 2px 6px;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  border-bottom: 1px solid #e5e7eb;
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
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 6px;
  min-height: 0;
  overflow: hidden;
}

.release-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.release-summary__chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.release-summary__chip--stable {
  background: #e8f1ff;
  color: #2454a6;
}

.release-summary__chip--preview {
  background: #fff2d8;
  color: #9a5a00;
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

.role-menus {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.role-menu-item {
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.84);
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 500;
  color: #334155;
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
  padding: 24px 32px;
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 14px;
  min-width: 0;
  height: 100vh;
  overflow: auto;
  overscroll-behavior: contain;
  background: #f8fafc;
}

.content--scene-compact {
  gap: 6px;
  padding: 24px 32px;
}

.content--flat-action {
  grid-template-rows: 1fr;
  gap: 8px;
  padding-top: 14px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--panel);
  border-radius: 16px;
  padding: 20px 24px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.08);
}

.topbar-main {
  min-width: 0;
}

.topbar--compact {
  padding: 12px 18px;
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
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}

.headline {
  margin: 6px 0 0;
  font-size: 30px;
  line-height: 1.15;
  font-weight: 700;
}

.headline-subtitle {
  margin: 6px 0 0;
  font-size: 12px;
  color: #94a3b8;
}

.breadcrumb {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
}

.crumb {
  background: transparent;
  border: 1px solid transparent;
  padding: 4px 8px;
  border-radius: 9px;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0;
  text-transform: uppercase;
  color: #64748b;
  cursor: pointer;
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
