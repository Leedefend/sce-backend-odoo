<template>
  <section class="menu-view">
    <section v-if="headerActions.length" class="menu-actions">
      <button
        v-for="action in headerActions"
        :key="`menu-header-${action.key}`"
        class="ghost"
        :disabled="loading"
        @click="executeHeaderAction(action.key)"
      >
        {{ action.label || action.key }}
      </button>
    </section>
    <StatusPanel
      v-if="pageSectionEnabled('status_loading', true) && pageSectionTagIs('status_loading', 'section') && loading"
      :title="pageText('loading_title', '正在打开菜单')"
      variant="info"
      :style="pageSectionStyle('status_loading')"
    />
    <StatusPanel
      v-else-if="pageSectionEnabled('status_info', true) && pageSectionTagIs('status_info', 'section') && info"
      :title="pageText('info_title', '菜单分组')"
      :message="info"
      variant="info"
      :style="pageSectionStyle('status_info')"
    />
    <StatusPanel
      v-else-if="pageSectionEnabled('status_error', true) && pageSectionTagIs('status_error', 'section') && error"
      :title="pageText('error_title', '菜单打开失败')"
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
import { buildBusinessEntryNavQuery, pickContractNavQuery } from '../app/navigationContext';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import { buildCanonicalSceneRouteTarget, buildEntryTargetRouteTarget } from '../app/routeQuery';
import { getSceneByKey } from '../app/resolvers/sceneRegistry';
import { isBusinessConfigurationAction, isMenuConfigurationAction, resolveActionWebRoute, resolveActionWebRouteQuery } from '../services/action_service';

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

function resolveCarryQuery(extra?: Record<string, unknown>) {
  return pickContractNavQuery(route.query as Record<string, unknown>, extra);
}

function resolveMenuCarryQuery(meta?: Record<string, unknown> | null, extra?: Record<string, unknown>) {
  return resolveCarryQuery({
    ...buildBusinessEntryNavQuery(meta || {}),
    ...(extra || {}),
  });
}

function isRootContainerMenu(menuId: number): boolean {
  const tree = session.menuTree || [];
  if (tree.length !== 1) return false;
  const root = tree[0];
  const rootId = Number(root?.menu_id || root?.id || 0);
  return rootId > 0 && rootId === menuId && Boolean(root?.children?.length);
}

async function resolve() {
  loading.value = true;
  error.value = '';
  info.value = '';
  try {
    const menuId = Number(route.params.menuId);
    if (!menuId) {
      throw new Error(pageText('error_invalid_menu_id', '菜单地址无效'));
    }
    if (isRootContainerMenu(menuId)) {
      await router.replace('/');
      return;
    }
    const result = resolveMenuAction(session.menuTree, menuId);
    if (result.kind === 'leaf') {
      const entryTarget = result.meta?.entry_target && typeof result.meta.entry_target === 'object'
        ? result.meta.entry_target as Record<string, unknown>
        : null;
      const policy = evaluateCapabilityPolicy({ source: result.node?.meta, available: session.capabilities });
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
      if (isMenuConfigurationAction(result.meta)) {
        await router.replace({
          path: '/admin/menu-config',
          query: resolveMenuCarryQuery(result.meta, { menu_id: menuId, action_id: result.meta.action_id }),
        });
        return;
      }
      if (isBusinessConfigurationAction(result.meta)) {
        await router.replace({
          path: resolveActionWebRoute(result.meta) || '/admin/business-config',
          query: resolveMenuCarryQuery(result.meta, {
            ...resolveActionWebRouteQuery(result.meta),
            menu_id: menuId,
            action_id: result.meta.action_id,
          }),
        });
        return;
      }
      if (entryTarget) {
        await router.replace(buildEntryTargetRouteTarget(entryTarget, {
          query: resolveMenuCarryQuery(result.meta),
          menuId,
          actionId: result.meta.action_id,
        }) as never);
        return;
      }
      await router.replace({
        name: 'action',
        params: { actionId: result.meta.action_id },
        query: resolveMenuCarryQuery(result.meta, { menu_id: menuId, action_id: result.meta.action_id }),
      });
      return;
    }
    if (result.kind === 'redirect') {
      if (result.target.entry_target) {
        await router.replace(buildEntryTargetRouteTarget(result.target.entry_target, {
          query: resolveMenuCarryQuery(result.target.meta),
          menuId: result.target.menu_id,
          actionId: result.target.action_id,
        }) as never);
        return;
      }
      if (result.target.scene_key) {
        const sceneKey = String(result.target.scene_key || '').trim();
        await router.replace(buildCanonicalSceneRouteTarget(sceneKey, {
          scene: getSceneByKey(sceneKey),
          query: resolveMenuCarryQuery(result.target.meta),
          menuId: result.target.menu_id,
          actionId: result.target.action_id,
        }));
        return;
      }
      if (result.target.action_id) {
        if (isMenuConfigurationAction(result.target.meta)) {
          await router.replace({
            path: '/admin/menu-config',
            query: resolveMenuCarryQuery(result.target.meta, { menu_id: result.target.menu_id, action_id: result.target.action_id }),
          });
          return;
        }
        if (isBusinessConfigurationAction(result.target.meta)) {
          await router.replace({
            path: resolveActionWebRoute(result.target.meta) || '/admin/business-config',
            query: resolveMenuCarryQuery(result.target.meta, {
              ...resolveActionWebRouteQuery(result.target.meta),
              menu_id: result.target.menu_id,
              action_id: result.target.action_id,
            }),
          });
          return;
        }
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
        await router.replace({
          name: 'action',
          params: { actionId: result.target.action_id },
          query: resolveMenuCarryQuery(result.target.meta, { menu_id: result.target.menu_id, action_id: result.target.action_id }),
        });
        return;
      }
    }
    if (result.kind === 'group' || (result.kind === 'broken' && result.reason === 'menu has no action')) {
      const label = result.node?.title || result.node?.name || result.node?.label || '当前菜单';
      await router.replace({
        name: 'workbench',
        query: { menu_id: menuId, reason: ErrorCodes.NAV_MENU_NO_ACTION, label },
      });
      return;
    }
    if (result.kind === 'broken') {
      error.value = result.reason || pageText('error_resolve_failed', '菜单打开失败');
      return;
    }
    error.value = pageText('error_resolve_failed', '菜单打开失败');
  } catch (err) {
    error.value = err instanceof Error ? err.message : pageText('error_resolve_failed', '菜单打开失败');
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
    error.value = pageText('error_resolve_failed', '菜单打开失败');
  }
}

watch(
  () => route.params.menuId,
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
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 8px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  cursor: pointer;
}
</style>
