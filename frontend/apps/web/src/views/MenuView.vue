<template>
  <section class="menu-view">
    <section v-if="headerActions.length" class="menu-actions">
      <button
        v-for="action in headerActions"
        :key="`menu-header-${action.key}`"
        class="ghost"
        :disabled="loading || action.disabled"
        :title="action.disabledReason || ''"
        @click="executeHeaderAction(action.key)"
      >
        {{ action.label || action.key }}
      </button>
    </section>
    <StatusPanel
      v-if="pageSectionEnabled('status_loading', true) && pageSectionTagIs('status_loading', 'section') && loading"
      :title="pageText('loading_title', 'Resolving menu...')"
      variant="info"
      :style="pageSectionStyle('status_loading')"
    />
    <StatusPanel
      v-else-if="pageSectionEnabled('status_info', true) && pageSectionTagIs('status_info', 'section') && info"
      :title="pageText('info_title', 'Menu group')"
      :message="info"
      variant="info"
      :style="pageSectionStyle('status_info')"
    />
    <StatusPanel
      v-else-if="pageSectionEnabled('status_error', true) && pageSectionTagIs('status_error', 'section') && error"
      :title="pageText('error_title', 'Menu resolve failed')"
      :message="error"
      variant="error"
      :style="pageSectionStyle('status_error')"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import { resolveMenuAction } from '../app/resolvers/menuResolver';
import StatusPanel from '../components/StatusPanel.vue';
import { ErrorCodes } from '../app/error_codes';
import { evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { pickContractNavQuery } from '../app/navigationContext';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import { findSceneByEntryAuthority, getSceneByKey } from '../app/resolvers/sceneRegistry';
import { buildSceneRegistryFallbackPath, parseSceneKeyFromQuery } from '../app/routeQuery';
import { PROJECT_INITIATION_MENU_XMLID, PROJECT_INTAKE_SCENE_KEY } from '../app/projectCreationBaseline';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const error = ref('');
const info = ref('');
const loading = ref(true);
const pageContract = usePageContract('menu');
const pageText = pageContract.text;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const headerActions = computed(() => pageGlobalActions.value);
const activeMenuTree = computed(() => {
  return session.releaseNavigationTree.length ? session.releaseNavigationTree : session.menuTree;
});

function resolveMenuAcrossNavigationTrees(menuId: number) {
  const primary = resolveMenuAction(activeMenuTree.value, menuId);
  if (primary.kind !== 'broken' || !session.releaseNavigationTree.length) {
    return primary;
  }
  if (primary.reason && primary.reason !== 'menu not found') {
    return primary;
  }
  return resolveMenuAction(session.menuTree, menuId);
}

function resolveCarryQuery(extra?: Record<string, unknown>) {
  return pickContractNavQuery(route.query as Record<string, unknown>, extra);
}

async function replaceToWorkbenchMissingScene(payload?: Record<string, unknown>) {
  await router.replace({
    name: 'workbench',
    query: resolveCarryQuery({
      reason: ErrorCodes.CONTRACT_CONTEXT_MISSING,
      ...(payload || {}),
    }),
  });
}

function resolveMenuXmlid(node: { meta?: unknown; xmlid?: unknown } | null | undefined) {
  if (!node || typeof node !== 'object') return '';
  const meta = node.meta && typeof node.meta === 'object'
    ? node.meta as Record<string, unknown>
    : {};
  return String(node.xmlid || meta.menu_xmlid || '').trim();
}

function normalizeMenuSceneKey(sceneKey: unknown) {
  const normalized = String(sceneKey || '').trim();
  if (normalized === 'project.initiation') {
    return PROJECT_INTAKE_SCENE_KEY;
  }
  return normalized;
}

function resolveSceneLocationFromSceneKey(sceneKey: unknown, menuId?: number, menuXmlid?: string, label?: string) {
  const normalizedSceneKey = normalizeMenuSceneKey(sceneKey);
  if (!normalizedSceneKey) return null;
  void menuId;
  void menuXmlid;
  if (getSceneByKey(normalizedSceneKey)) {
    return {
      path: `/s/${normalizedSceneKey}`,
      query: resolveCarryQuery({
        scene_key: normalizedSceneKey,
        menu_id: undefined,
        menu_xmlid: undefined,
        action_id: undefined,
      }),
    };
  }
  return buildSceneRegistryFallbackPath({
    sceneKey: normalizedSceneKey,
    menuId: Number(menuId || 0) || undefined,
    label: label || normalizedSceneKey,
  });
}

function resolveSceneLocationFromAction(actionId: number, menuId?: number, menuXmlid?: string) {
  const scene = findSceneByEntryAuthority({
    actionId,
    menuId: Number(menuId || 0),
  });
  if (!scene) return null;
  void menuXmlid;
  return {
    path: scene.route || `/s/${scene.key}`,
    query: resolveCarryQuery({
      scene_key: scene.key,
      menu_id: undefined,
      menu_xmlid: undefined,
      action_id: undefined,
    }),
  };
}

function isProjectIntakeMenuNode(node: { meta?: unknown } | null | undefined) {
  const meta = node?.meta && typeof node.meta === 'object'
    ? node.meta as Record<string, unknown>
    : {};
  const sceneKey = normalizeMenuSceneKey(meta.scene_key);
  if (sceneKey === PROJECT_INTAKE_SCENE_KEY) {
    return true;
  }
  const menuXmlid = String(meta.menu_xmlid || '').trim();
  return menuXmlid === PROJECT_INITIATION_MENU_XMLID;
}

async function resolve() {
  loading.value = true;
  error.value = '';
  info.value = '';
  try {
    const menuId = Number(route.params.menuId);
    if (!menuId) {
      throw new Error(pageText('error_invalid_menu_id', 'invalid menu id'));
    }
    const result = resolveMenuAcrossNavigationTrees(menuId);
    if (result.kind === 'leaf') {
      if (isProjectIntakeMenuNode(result.node)) {
        await router.replace({
          path: `/s/${PROJECT_INTAKE_SCENE_KEY}`,
          query: resolveCarryQuery({
            scene_key: PROJECT_INTAKE_SCENE_KEY,
            menu_id: undefined,
            action_id: undefined,
          }),
        });
        return;
      }
      const policy = evaluateCapabilityPolicy({ source: result.node?.meta as Record<string, unknown> | undefined, available: session.capabilities });
      if (policy.state !== 'enabled') {
        await router.replace({
          name: 'workbench',
          query: {
            menu_id: menuId,
            action_id: result.meta.action_id,
            reason: ErrorCodes.CAPABILITY_MISSING,
            missing: policy.missing.join(','),
          },
        });
        return;
      }
      session.setActionMeta(result.meta);
      const menuXmlid = resolveMenuXmlid(result.node as { meta?: unknown; xmlid?: unknown } | null | undefined);
      const carriedSceneKey = parseSceneKeyFromQuery(route.query as Record<string, unknown>);
      const nodeSceneLocation = resolveSceneLocationFromSceneKey(
        carriedSceneKey || (result.node?.meta as Record<string, unknown> | undefined)?.scene_key,
        menuId,
        menuXmlid || undefined,
        result.node?.title || result.node?.name || result.node?.label || '',
      );
      if (nodeSceneLocation) {
        await router.replace(nodeSceneLocation);
        return;
      }
      const sceneLocation = resolveSceneLocationFromAction(result.meta.action_id, menuId, menuXmlid || undefined);
      if (sceneLocation) {
        await router.replace(sceneLocation);
        return;
      }
      await replaceToWorkbenchMissingScene({
        diag: 'menu_leaf_missing_scene_identity',
        menu_id: menuId,
        menu_xmlid: menuXmlid || undefined,
        action_id: result.meta.action_id,
      });
      return;
    }
    if (result.kind === 'redirect') {
      const targetSceneKey = normalizeMenuSceneKey(result.target.scene_key);
      if (targetSceneKey) {
        const directSceneLocation = resolveSceneLocationFromSceneKey(
          targetSceneKey,
          result.target.menu_id,
          String(result.target.meta?.menu_xmlid || '').trim() || undefined,
          result.node?.title || result.node?.name || result.node?.label || targetSceneKey,
        );
        if (directSceneLocation) {
          await router.replace(directSceneLocation);
          return;
        }
        if (!getSceneByKey(targetSceneKey)) {
          if (result.target.action_id) {
            const policy = evaluateCapabilityPolicy({ source: result.target.meta, available: session.capabilities });
            if (policy.state !== 'enabled') {
              await router.replace({
                name: 'workbench',
                query: {
                  menu_id: result.target.menu_id,
                  action_id: result.target.action_id,
                  reason: ErrorCodes.CAPABILITY_MISSING,
                  missing: policy.missing.join(','),
                },
              });
              return;
            }
            if (result.target.meta) {
              session.setActionMeta(result.target.meta);
            }
            const sceneLocation = resolveSceneLocationFromAction(
              result.target.action_id,
              result.target.menu_id,
              String(result.target.meta?.menu_xmlid || '').trim() || undefined,
            );
            if (sceneLocation) {
              await router.replace(sceneLocation);
              return;
            }
          }
          const targetRoute = String(result.target.route || '').trim();
          if (targetRoute) {
            await router.replace({
              path: targetRoute,
              query: resolveCarryQuery({
                menu_id: result.target.menu_id,
                scene_key: targetSceneKey,
              }),
            });
            return;
          }
          await router.replace(
            buildSceneRegistryFallbackPath({
              sceneKey: targetSceneKey,
              menuId: result.target.menu_id,
              label: result.node?.title || result.node?.name || result.node?.label || targetSceneKey,
            }),
          );
          return;
        }
        await router.replace({
          path: `/s/${targetSceneKey}`,
          query: resolveCarryQuery({
            scene_key: targetSceneKey,
            menu_id: undefined,
            menu_xmlid: undefined,
            action_id: undefined,
          }),
        });
        return;
      }
      if (result.target.action_id) {
        const policy = evaluateCapabilityPolicy({ source: result.target.meta, available: session.capabilities });
        if (policy.state !== 'enabled') {
          await router.replace({
            name: 'workbench',
            query: {
              menu_id: result.target.menu_id,
              action_id: result.target.action_id,
              reason: ErrorCodes.CAPABILITY_MISSING,
              missing: policy.missing.join(','),
            },
          });
          return;
        }
        if (result.target.meta) {
          session.setActionMeta(result.target.meta);
        }
        const sceneLocation = resolveSceneLocationFromAction(
          result.target.action_id,
          result.target.menu_id,
          String(result.target.meta?.menu_xmlid || '').trim() || undefined,
        );
        if (sceneLocation) {
          await router.replace(sceneLocation);
          return;
        }
        await replaceToWorkbenchMissingScene({
          diag: 'menu_redirect_missing_scene_identity',
          menu_id: result.target.menu_id,
          menu_xmlid: String(result.target.meta?.menu_xmlid || '').trim() || undefined,
          action_id: result.target.action_id,
        });
        return;
      }
    }
    if (result.kind === 'group' || (result.kind === 'broken' && result.reason === 'menu has no action')) {
      const label = result.node?.title || result.node?.name || result.node?.label || 'This menu';
      await router.replace({
        name: 'workbench',
        query: { menu_id: menuId, reason: ErrorCodes.NAV_MENU_NO_ACTION, label },
      });
      return;
    }
    if (result.kind === 'broken') {
      error.value = result.reason || pageText('error_resolve_failed', 'resolve menu failed');
      return;
    }
    error.value = pageText('error_resolve_failed', 'resolve menu failed');
  } catch (err) {
    error.value = err instanceof Error ? err.message : pageText('error_resolve_failed', 'resolve menu failed');
  } finally {
    loading.value = false;
  }
}

async function executeHeaderAction(actionKey: string) {
  const matched = headerActions.value.find((item) => item.key === actionKey);
  if (matched?.disabled) {
    return;
  }
  const handled = await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: resolveCarryQuery(),
    onRefresh: resolve,
    onFallback: async (key) => {
      if (key === 'open_workbench' || key === 'open_landing') {
        await router.replace('/');
        return true;
      }
      return false;
    },
  });
  if (!handled) {
    error.value = pageText('error_resolve_failed', 'resolve menu failed');
  }
}

watch(
  () => [
    route.params.menuId,
    session.initStatus,
    session.releaseNavigationTree.length,
    session.menuTree.length,
  ],
  () => {
    resolve();
  },
  { immediate: true }
);
</script>
<style scoped>
.menu-view {
  padding: 12px;
}

.menu-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.ghost {
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  color: #111827;
  cursor: pointer;
}
</style>
