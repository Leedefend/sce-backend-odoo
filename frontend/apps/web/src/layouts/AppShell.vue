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
        <div class="logo">SC</div>
        <div>
          <p class="title">{{ rootTitle }}</p>
          <p class="subtitle">{{ sidebarSubtitle }}</p>
        </div>
      </div>

      <p class="enterprise-line">当前企业：{{ enterpriseLabel }}</p>

      <div class="role-surface">
        <p class="role-label">当前角色：{{ roleLabel }}</p>
        <div class="role-actions">
          <button class="ghost mini" @click="openRoleLanding">进入工作台</button>
          <button class="ghost mini" @click="router.push('/my-work')">我的工作</button>
        </div>
        <div v-if="roleMenus.length" class="role-menus">
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
        <button v-if="showRefresh" class="ghost" @click="refreshInit">刷新</button>
        <button class="ghost" @click="logout">退出登录</button>
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
import { resolveMenuAction } from '../app/resolvers/menuResolver';
import { isDeliveryModeEnabled, isHudEnabled } from '../config/debug';
import { normalizeLegacyWorkbenchPath, parseSceneKeyFromQuery } from '../app/routeQuery';
import { buildRuntimeNavigationRegistry } from '../app/navigationRegistry';
import type { NavNode } from '@sc/schema';
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

const menuTree = computed(() => session.menuTree);
const roleSurface = computed(() => session.roleSurface);
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
const roleLandingPath = computed(() => session.resolveLandingPath('/'));
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
  return '工作台';
});

const topbarSubtitle = computed(() => {
  const sceneKey = String(routeSceneKey.value || '').trim();
  if (sceneKey === 'projects.intake') {
    return '创建项目 · 填写基础信息完成立项';
  }
  return '';
});

const sceneHeaderMinimal = computed(() => String(routeSceneKey.value || '').trim() === 'projects.intake');

const sceneHeaderAnchorLine = computed(() => {
  if (!sceneHeaderMinimal.value) return '';
  return '项目立项 / 创建项目';
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
});

onUnmounted(() => {
  if (typeof window === 'undefined') return;
  window.removeEventListener(getTraceUpdateEventName(), handleTraceUpdate as (event: Event) => void);
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

const breadcrumb = computed(() => {
  const crumbs: Array<{ label: string; to?: string }> = [];
  const menuId = activeMenuId.value;
  const menuPath = findMenuPath(menuTree.value, menuId);
  if (menuPath.length) {
    menuPath.forEach((node) => {
      const label = node.title || node.name || node.label || '菜单';
      const id = node.menu_id ?? node.id;
      if (id) {
        crumbs.push({ label, to: `/m/${id}` });
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
    crumbs.push({ label: '工作台' });
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
const roleMenus = computed(() => {
  const allow = new Set(roleSurface.value?.menu_xmlids || []);
  if (!allow.size) return [];
  const found: Array<{ id: number; label: string }> = [];
  const seen = new Set<number>();
  const walk = (nodes: NavNode[]) => {
    for (const node of nodes) {
      const xmlid = (node as NavNode & { xmlid?: string }).xmlid || node.meta?.menu_xmlid;
      const id = Number(node.menu_id || node.id || 0);
      if (xmlid && allow.has(xmlid) && id && !seen.has(id)) {
        seen.add(id);
        found.push({ id, label: node.title || node.name || node.label || `菜单 ${id}` });
      }
      if (node.children?.length) {
        walk(node.children);
      }
    }
  };
  walk(menuTree.value);
  return found.slice(0, 6);
});

function handleSelect(node: NavNode) {
  if (!node.menu_id && node.id) {
    node.menu_id = node.id as number;
  }
  const targetMenuId = Number(node.menu_id || node.id || 0);
  if (targetMenuId <= 0) return;
  const resolved = resolveMenuAction(menuTree.value, targetMenuId);
  if (resolved.kind === 'redirect' && resolved.target?.scene_key) {
    const sceneKey = String(resolved.target.scene_key || '').trim();
    const scene = sceneKey ? getSceneByKey(sceneKey) : null;
    if (sceneKey && scene) {
      const rawPath = String(scene.target?.route || scene.route || `/s/${sceneKey}`).trim();
      const resolvedPath = normalizeLegacyWorkbenchPath(rawPath) || `/s/${sceneKey}`;
      router.push({ path: resolvedPath, query: { menu_id: targetMenuId } }).catch(() => {});
      return;
    }
  }
  router.push(`/m/${targetMenuId}`).catch(() => {});
}

function openRoleLanding() {
  router.push(roleLandingPath.value).catch(() => {});
}

function openRoleMenu(menuId: number) {
  router.push(`/m/${menuId}`).catch(() => {});
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
