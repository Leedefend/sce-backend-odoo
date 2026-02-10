<template>
  <div
    class="shell"
    :data-layout-kind="activeLayout.kind"
    :data-sidebar-mode="activeLayout.sidebar"
    :data-header-mode="activeLayout.header"
  >
    <aside class="sidebar" :class="sidebarClass">
      <div class="brand">
        <div class="logo">SC</div>
        <div>
          <p class="title">{{ rootTitle }}</p>
          <p class="subtitle">{{ userName }}</p>
        </div>
      </div>

      <div class="search">
        <input v-model="query" type="search" placeholder="Search menu..." />
      </div>

      <div class="menu">
        <MenuTree
          :nodes="filteredMenu"
          :active-menu-id="activeMenuId"
          :capabilities="capabilities"
          @select="handleSelect"
        />
      </div>

      <div class="footer">
        <button v-if="showRefresh" class="ghost" @click="refreshInit">Refresh init</button>
        <button class="ghost" @click="logout">Logout</button>
      </div>
    </aside>

    <section class="content">
      <header class="topbar" :class="{ 'topbar--compact': activeLayout.header === 'compact' }">
        <div>
          <p class="eyebrow">Portal Shell v0.7 · UX Hardening</p>
          <div class="breadcrumb">
            <button
              v-for="(item, index) in breadcrumb"
              :key="`${item.label}-${index}`"
              class="crumb"
              :class="{ active: index === breadcrumb.length - 1 }"
              @click="item.to && router.push(item.to)"
              :disabled="!item.to"
            >
              {{ item.label }}
            </button>
          </div>
          <h1 class="headline">{{ pageTitle }}</h1>
        </div>
      </header>

      <StatusPanel
        v-if="initStatus === 'loading'"
        title="Initializing app shell..."
        variant="info"
      />
      <StatusPanel
        v-else-if="initStatus === 'error'"
        title="Initialization failed"
        :message="initError || 'Unknown error'"
        :trace-id="initTraceId || undefined"
        variant="error"
        :on-retry="refreshInit"
      />
      <StatusPanel
        v-else-if="showSceneErrors"
        title="Scene registry invalid"
        :message="sceneErrorMessage"
        variant="error"
      />
      <StatusPanel
        v-else-if="initStatus === 'ready' && !menuCount"
        title="No navigation data"
        message="Menu tree is empty. Try refreshing app init."
        variant="error"
        :on-retry="refreshInit"
      />

      <div v-else class="router-host">
        <slot />
      </div>

      <DevContextPanel
        :visible="showHud"
        title="Page Context"
        :entries="hudEntries"
        :actions="hudActions"
        :message="hudMessage"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, provide, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import MenuTree from '../components/MenuTree.vue';
import StatusPanel from '../components/StatusPanel.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import { useSessionStore } from '../stores/session';
import { getSceneByKey, getSceneRegistryDiagnostics, resolveSceneLayout } from '../app/resolvers/sceneRegistry';
import { isHudEnabled } from '../config/debug';
import type { NavNode } from '@sc/schema';
import {
  exportSuggestedActionTraces,
  getLatestSuggestedActionTrace,
  getTraceUpdateEventName,
  rankSuggestedActionKinds,
} from '../services/trace';

const session = useSessionStore();
const route = useRoute();
const router = useRouter();
const query = ref('');

const menuTree = computed(() => session.menuTree);
const rootNode = computed(() => (menuTree.value.length === 1 ? menuTree.value[0] : null));
const menuNodes = computed(() => rootNode.value?.children ?? menuTree.value);
const menuCount = computed(() => menuNodes.value.length);
const rootTitle = computed(() => {
  const root = rootNode.value;
  return root?.title || root?.name || root?.label || 'Smart Construction';
});
const userName = computed(() => session.user?.name ?? 'Guest');
const capabilities = computed(() => session.capabilities);
const effectiveDb = computed(() => (session.initMeta as any)?.effective_db ?? 'N/A');
const navVersion = computed(() => {
  const meta = session.initMeta as any;
  return meta?.nav_version ?? meta?.nav_meta?.menu ?? meta?.parts?.nav ?? 'N/A';
});
const suggestedActionStamp = ref(0);
const hudMessage = ref('');

const initStatus = computed(() => session.initStatus);
const initError = computed(() => session.initError);
const initTraceId = computed(() => session.initTraceId);
const showSceneErrors = computed(() => import.meta.env.DEV && sceneRegistryErrors.length > 0);
const sceneRegistryErrors = getSceneRegistryDiagnostics().errors;
const activeLayout = computed(() => {
  const sceneKey = route.meta?.sceneKey as string | undefined;
  const scene = sceneKey ? getSceneByKey(sceneKey) : null;
  return resolveSceneLayout(scene);
});
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
  return `Scene registry validation failed: ${sample.join(' | ')}${suffix}`;
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

const pageTitle = computed(() => {
  const sceneKey = route.meta?.sceneKey as string | undefined;
  if (sceneKey) {
    const scene = getSceneByKey(sceneKey);
    if (scene?.label) {
      return scene.label;
    }
  }
  if (menuLabel.value) {
    return menuLabel.value;
  }
  if (session.currentAction?.name) {
    return session.currentAction.name;
  }
  const modelLabel = (session.currentAction as any)?.model_label || (session.currentAction as any)?.model;
  if (modelLabel) {
    return modelLabel;
  }
  if (route.name === 'workbench') {
    return 'Navigation issue';
  }
  if (route.name === 'record') {
    return 'Record';
  }
  return 'Workspace';
});

provide('pageTitle', pageTitle);
const showHud = computed(() => isHudEnabled(route));
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
const hudEntries = computed(() => [
  { label: 'scene_key', value: (route.meta?.sceneKey as string | undefined) || '-' },
  { label: 'menu_id', value: activeMenuId.value || '-' },
  { label: 'menu_label', value: menuLabel.value || '-' },
  { label: 'route', value: route.fullPath },
  { label: 'user', value: userName.value || '-' },
  { label: 'db', value: effectiveDb.value || '-' },
  { label: 'nav_version', value: navVersion.value || '-' },
  { label: 'sa_kind', value: latestSuggestedAction.value?.suggested_action_kind || '-' },
  { label: 'sa_success', value: String(latestSuggestedAction.value?.suggested_action_success ?? '-') },
  { label: 'sa_ts', value: latestSuggestedActionTs.value },
]);
const defaultKindActions = ['open_record', 'copy_trace', 'refresh'];
const hudActions = computed(() => [
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
    const sinceLabel =
      typeof filter.since_ts === 'number' && Number.isFinite(filter.since_ts) && filter.since_ts > 0
        ? `since_ts=${Math.floor(filter.since_ts)}`
        : '';
    const details = [suffix, filter.kind ? `kind=${filter.kind}` : '', filter.success === true ? 'success=true' : '', sinceLabel]
      .filter(Boolean)
      .join(', ');
    hudMessage.value = `Exported suggested_action traces (${details}).`;
  } catch {
    hudMessage.value = 'Failed to export suggested_action traces.';
  }
}

onMounted(() => {
  if (typeof window === 'undefined') return;
  window.addEventListener(getTraceUpdateEventName(), handleTraceUpdate as EventListener);
  handleTraceUpdate();
});

onUnmounted(() => {
  if (typeof window === 'undefined') return;
  window.removeEventListener(getTraceUpdateEventName(), handleTraceUpdate as EventListener);
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

const breadcrumb = computed(() => {
  const crumbs: Array<{ label: string; to?: string }> = [];
  const menuId = activeMenuId.value;
  const menuPath = findMenuPath(menuTree.value, menuId);
  if (menuPath.length) {
    menuPath.forEach((node) => {
      const label = node.title || node.name || node.label || 'Menu';
      const id = node.menu_id ?? node.id;
      if (id) {
        crumbs.push({ label, to: `/m/${id}` });
      }
    });
  }
  if (route.name === 'action') {
    const label = session.currentAction?.name || `Action ${route.params.actionId ?? ''}`.trim();
    crumbs.push({ label });
  }
  if (route.name === 'record') {
    const recordLabel = `Record ${route.params.id ?? ''}`.trim();
    crumbs.push({ label: recordLabel });
  }
  if (!crumbs.length) {
    crumbs.push({ label: 'Workspace' });
  }
  return crumbs;
});

const showRefresh = computed(() => import.meta.env.DEV || localStorage.getItem('DEBUG_INTENT') === '1');

const activeMenuId = computed(() => {
  if (route.name === 'menu') {
    return Number(route.params.menuId ?? 0) || undefined;
  }
  const fromQuery = Number(route.query.menu_id ?? 0);
  return fromQuery || undefined;
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

function handleSelect(node: NavNode) {
  if (!node.menu_id && node.id) {
    node.menu_id = node.id as number;
  }
  const sceneKey = (node as any).scene_key || (node as any).sceneKey || node.meta?.scene_key;
  if (sceneKey) {
    router.push({ path: `/s/${sceneKey}`, query: { menu_id: node.menu_id || undefined } }).catch(() => {});
    return;
  }
  if (node.menu_id) {
    router.push(`/m/${node.menu_id}`).catch(() => {});
  }
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
  min-height: 100vh;
  height: 100vh;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  background: radial-gradient(circle at top left, #f7e9dc 0%, #f6f3ef 45%, #eef1f7 100%);
  color: var(--ink);
  font-family: "Space Grotesk", "IBM Plex Sans", system-ui, sans-serif;
}

.sidebar {
  padding: 24px 18px;
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  gap: 16px;
  border-right: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  height: 100vh;
  overflow: hidden;
}

.sidebar--scroll {
  overflow: auto;
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
}

.logo {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, #2f3a5f, #1b263b);
  color: white;
  display: grid;
  place-items: center;
  font-weight: 700;
  letter-spacing: 1px;
}

.title {
  font-weight: 600;
  margin: 0;
}

.subtitle {
  margin: 0;
  font-size: 12px;
  color: var(--muted);
}

.search input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: white;
}

.menu {
  overflow: auto;
  padding-right: 4px;
  min-height: 0;
}

.footer {
  margin-top: auto;
  display: grid;
  gap: 8px;
}

.ghost {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: transparent;
  cursor: pointer;
  font-size: 12px;
}

.content {
  padding: 28px 32px;
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 18px;
  min-width: 0;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--panel);
  border-radius: 16px;
  padding: 18px 24px;
  box-shadow: 0 18px 32px rgba(15, 23, 42, 0.08);
}

.topbar--compact {
  padding: 12px 18px;
}

.topbar--compact .breadcrumb {
  display: none;
}

.topbar--compact .headline {
  font-size: 20px;
}

.eyebrow {
  margin: 0;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--muted);
}

.headline {
  margin: 4px 0 0;
  font-size: 24px;
}

.breadcrumb {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 0;
}

.crumb {
  background: transparent;
  border: none;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 12px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--muted);
  cursor: pointer;
}

.crumb.active {
  background: rgba(47, 58, 95, 0.12);
  color: var(--ink);
  font-weight: 600;
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
  }
  .sidebar {
    grid-row: 2;
    border-right: none;
    border-top: 1px solid rgba(15, 23, 42, 0.08);
    height: auto;
  }
}
</style>
