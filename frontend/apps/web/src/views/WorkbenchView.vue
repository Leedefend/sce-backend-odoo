<template>
  <section class="workbench">
    <header class="header">
      <div>
        <p v-if="showHud" class="diagnostic">Diagnostic surface only — not product UI.</p>
        <h2>页面暂时无法打开</h2>
        <p class="meta">我们已为你保留可继续操作的入口。</p>
        <p v-if="hasContext" class="context-line">
          推荐上下文：{{ workspaceContextSummary }}
          <button class="ghost mini" @click="clearWorkspaceContext">清除</button>
        </p>
      </div>
      <div class="actions">
        <button class="ghost" @click="goToProjects">返回工作台</button>
        <button class="ghost" @click="openFirstReachableMenu">打开菜单</button>
        <button class="ghost" @click="refresh">刷新</button>
      </div>
    </header>

    <StatusPanel
      title="页面暂时无法打开"
      :message="message"
      :variant="panelVariant"
    />

    <section v-if="showTiles" class="tiles">
      <button
        v-for="tile in tiles"
        :key="tile.key || tile.title"
        class="tile"
        :class="{ disabled: tile.policy.state !== 'enabled' }"
        :title="tile.tooltip"
        type="button"
        @click="handleTileClick(tile)"
      >
        <div class="tile-icon">{{ tile.icon || '•' }}</div>
        <div class="tile-body">
          <div class="tile-title">{{ tile.title || tile.key }}</div>
          <div class="tile-subtitle">{{ tile.subtitle || '' }}</div>
        </div>
      </button>
    </section>

    <div v-if="showHud" class="details">
      <div class="detail">
        <span class="label">Reason</span>
        <span class="value">{{ reasonLabel }}</span>
      </div>
      <div class="detail">
        <span class="label">Menu</span>
        <span class="value">{{ menuId || 'N/A' }}</span>
      </div>
      <div v-if="showHud" class="detail">
        <span class="label">Action</span>
        <span class="value">{{ actionId || 'N/A' }}</span>
      </div>
      <div class="detail">
        <span class="label">Route</span>
        <span class="value">{{ route.fullPath }}</span>
      </div>
      <div v-if="diag" class="detail">
        <span class="label">Diag</span>
        <span class="value">{{ diag }}</span>
      </div>
      <div v-if="showHud && diagActionType" class="detail">
        <span class="label">Action Type</span>
        <span class="value">{{ diagActionType }}</span>
      </div>
      <div v-if="showHud && diagContractType" class="detail">
        <span class="label">Contract Type</span>
        <span class="value">{{ diagContractType }}</span>
      </div>
      <div v-if="showHud && diagContractUrl" class="detail">
        <span class="label">Contract URL</span>
        <span class="value">{{ diagContractUrl }}</span>
      </div>
      <div v-if="showHud && diagMetaUrl" class="detail">
        <span class="label">Meta URL</span>
        <span class="value">{{ diagMetaUrl }}</span>
      </div>
      <div v-if="showHud" class="detail">
        <span class="label">Last Intent</span>
        <span class="value">{{ lastIntent || 'N/A' }}</span>
      </div>
      <div v-if="showHud" class="detail">
        <span class="label">Trace</span>
        <span class="value">
          {{ lastTraceId || 'N/A' }}
          <button v-if="lastTraceId" class="ghost mini" @click="copyTrace">Copy</button>
        </span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { ErrorCodes } from '../app/error_codes';
import { useSessionStore } from '../stores/session';
import { isHudEnabled } from '../config/debug';
import { capabilityTooltip, evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { hasWorkspaceContext as hasWorkspaceContextValue, readWorkspaceContext, stripWorkspaceContext } from '../app/workspaceContext';
import type { Scene } from '../app/resolvers/sceneRegistry';
import type { NavNode } from '@sc/schema';

type UnknownDict = Record<string, unknown>;

interface WorkbenchTile {
  key?: string;
  title?: string;
  subtitle?: string;
  icon?: string;
  scene_key?: string;
  sceneKey?: string;
  route?: string;
  payload?: {
    scene_key?: string;
    sceneKey?: string;
    action_id?: number;
    menu_id?: number;
    model?: string;
    record_id?: number;
  };
}

interface TilePolicy {
  state?: string;
  missing?: string[];
}

interface EnrichedWorkbenchTile extends WorkbenchTile {
  policy: TilePolicy;
  tooltip: string;
}

function asObject(value: unknown): UnknownDict | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null;
  }
  return value as UnknownDict;
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function resolveSceneCode(scene: Scene): string {
  return asText(asObject(scene)?.code);
}

function resolveTileScene(tile: WorkbenchTile): string {
  return (
    asText(tile.scene_key) ||
    asText(tile.sceneKey) ||
    asText(tile.payload?.scene_key) ||
    asText(tile.payload?.sceneKey)
  );
}

// Workbench is a diagnostic-only surface and must not be used as product UI.
const route = useRoute();
const router = useRouter();

const reason = computed(() => String(route.query.reason || ''));
const menuId = computed(() => Number(route.query.menu_id || 0) || undefined);
const actionId = computed(() => Number(route.query.action_id || 0) || undefined);
const sceneKey = computed(() => String(route.query.scene || route.query.scene_key || route.query.sceneKey || ''));
const session = useSessionStore();
const showHud = computed(() => isHudEnabled(route));
const lastTraceId = computed(() => session.lastTraceId || '');
const lastIntent = computed(() => session.lastIntent || '');
const diag = computed(() => String(route.query.diag || ''));
const diagActionType = computed(() => String(route.query.diag_action_type || ''));
const diagContractType = computed(() => String(route.query.diag_contract_type || ''));
const diagContractUrl = computed(() => String(route.query.diag_contract_url || ''));
const diagMetaUrl = computed(() => String(route.query.diag_meta_url || ''));
const workspaceContextQuery = computed(() => {
  return readWorkspaceContext(route.query as Record<string, unknown>);
});
const hasContext = computed(() => hasWorkspaceContextValue(workspaceContextQuery.value));
const workspaceContextSummary = computed(() => {
  const parts = [];
  if (workspaceContextQuery.value.preset) parts.push(`preset=${workspaceContextQuery.value.preset}`);
  if (workspaceContextQuery.value.search) parts.push(`search=${workspaceContextQuery.value.search}`);
  if (workspaceContextQuery.value.ctx_source) parts.push(`source=${workspaceContextQuery.value.ctx_source}`);
  return parts.join(' · ');
});
const scene = computed<Scene | null>(() => {
  if (!sceneKey.value) return null;
  return (
    session.scenes.find((item) => item.key === sceneKey.value || resolveSceneCode(item) === sceneKey.value) || null
  );
});
const showTiles = computed(() => reason.value === ErrorCodes.CAPABILITY_MISSING && tiles.value.length > 0);
const tiles = computed<EnrichedWorkbenchTile[]>(() => {
  const rawTiles = Array.isArray(scene.value?.tiles) ? (scene.value?.tiles as WorkbenchTile[]) : [];
  if (!Array.isArray(rawTiles)) return [];
  return rawTiles.map((tile) => {
    const policy = evaluateCapabilityPolicy({ source: tile, available: session.capabilities });
    return {
      ...tile,
      policy,
      tooltip: capabilityTooltip(policy),
    };
  });
});

const reasonLabel = computed(() => {
  switch (reason.value) {
    case ErrorCodes.NAV_MENU_NO_ACTION:
      return 'Menu group (no action)';
    case ErrorCodes.ACT_NO_MODEL:
      return 'Action has no model';
    case ErrorCodes.ACT_UNSUPPORTED_TYPE:
      return 'Action type not supported';
    case ErrorCodes.CAPABILITY_MISSING:
      return 'Capability missing';
    default:
      return reason.value || 'Unknown';
  }
});

const message = computed(() => {
  switch (reason.value) {
    case ErrorCodes.NAV_MENU_NO_ACTION:
      return 'This menu is a directory and no reachable submenu is available.';
    case ErrorCodes.ACT_NO_MODEL:
      return 'This action opens a custom workspace without a model.';
    case ErrorCodes.ACT_UNSUPPORTED_TYPE:
      return 'This action type is not yet supported in the portal shell.';
    case ErrorCodes.CAPABILITY_MISSING:
      return 'This capability is not enabled for your account.';
    default:
      return 'Return to home or open the menu to continue.';
  }
});

const panelVariant = computed(() => {
  if (reason.value === ErrorCodes.CAPABILITY_MISSING) {
    return 'forbidden_capability';
  }
  return 'error';
});

const firstReachableMenuId = computed(() => findFirstReachableMenuId(session.menuTree));

function refresh() {
  window.location.reload();
}

async function goToProjects() {
  await router.push({ path: '/s/projects.list', query: workspaceContextQuery.value });
}

async function openFirstReachableMenu() {
  if (firstReachableMenuId.value) {
    await router.push({ path: `/m/${firstReachableMenuId.value}`, query: workspaceContextQuery.value });
    return;
  }
  await goToProjects();
}

async function handleTileClick(tile: EnrichedWorkbenchTile) {
  const explicitScene = resolveTileScene(tile);
  if (explicitScene) {
    await router.push({ path: `/s/${explicitScene}`, query: workspaceContextQuery.value });
    return;
  }
  if (tile.policy?.state === 'disabled_capability') {
    await router.replace({
      name: 'workbench',
      query: {
        reason: ErrorCodes.CAPABILITY_MISSING,
        scene: sceneKey.value || undefined,
        missing: (tile.policy.missing || []).join(',') || undefined,
      },
    });
    return;
  }
  if (tile.route) {
    await router.push({ path: String(tile.route), query: workspaceContextQuery.value });
    return;
  }
  const payload = tile.payload || {};
  if (payload.action_id) {
    await router.push({
      path: `/a/${payload.action_id}`,
      query: { menu_id: payload.menu_id || undefined, ...workspaceContextQuery.value },
    });
    return;
  }
  if (payload.model && payload.record_id) {
    await router.push({
      path: `/r/${payload.model}/${payload.record_id}`,
      query: {
        menu_id: payload.menu_id || undefined,
        action_id: payload.action_id || undefined,
        ...workspaceContextQuery.value,
      },
    });
  }
}

async function copyTrace() {
  if (!lastTraceId.value) return;
  try {
    await navigator.clipboard.writeText(lastTraceId.value);
  } catch {
    // noop
  }
}

function clearWorkspaceContext() {
  const nextQuery = stripWorkspaceContext(route.query as Record<string, unknown>);
  router.replace({ path: route.path, query: nextQuery }).catch(() => {});
}

function resolveNodeSceneKey(node: NavNode): string {
  return asText((node as NavNode & { scene_key?: string; sceneKey?: string }).scene_key)
    || asText((node as NavNode & { scene_key?: string; sceneKey?: string }).sceneKey)
    || asText(node.meta?.scene_key);
}

function findFirstReachableMenuId(nodes: NavNode[]): number | null {
  if (!Array.isArray(nodes)) {
    return null;
  }
  for (const node of nodes) {
    if (!node) {
      continue;
    }
    const menuId = Number(node.menu_id || node.id || 0) || 0;
    if (menuId) {
      if (node.meta?.action_id) {
        return menuId;
      }
      if (resolveNodeSceneKey(node)) {
        return menuId;
      }
    }
    const nested = findFirstReachableMenuId(node.children || []);
    if (nested) {
      return nested;
    }
  }
  return null;
}
</script>

<style scoped>
.workbench {
  display: grid;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions {
  display: flex;
  gap: 8px;
}

.meta {
  color: #64748b;
  font-size: 14px;
}

.diagnostic {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #b45309;
}

.context-line {
  margin: 8px 0 0;
  color: #334155;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.tiles {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.tile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 14px;
  background: white;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 12px 20px rgba(15, 23, 42, 0.08);
  text-align: left;
  cursor: pointer;
}

.tile.disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.tile-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.08);
  display: grid;
  place-items: center;
  font-weight: 700;
  color: #334155;
}

.tile-title {
  font-weight: 600;
  color: #0f172a;
}

.tile-subtitle {
  font-size: 12px;
  color: #64748b;
}

.detail {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 4px;
}

.ghost.mini {
  margin-left: 8px;
  padding: 4px 8px;
  font-size: 12px;
}

.label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #94a3b8;
}

.value {
  font-weight: 600;
}

.ghost {
  background: transparent;
  color: #111827;
  border: 1px solid rgba(15, 23, 42, 0.12);
  padding: 10px 14px;
  border-radius: 10px;
  cursor: pointer;
}
</style>
