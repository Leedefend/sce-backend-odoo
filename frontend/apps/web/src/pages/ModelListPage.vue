<template>
  <main class="page">
    <StatusPanel
      title="Legacy List Route"
      message="This route has been redirected to contract-driven ActionView."
      variant="info"
    />
  </main>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { ErrorCodes } from '../app/error_codes';
import { parseSceneKeyFromQuery } from '../app/routeQuery';
import { findSceneByEntryAuthority } from '../app/resolvers/sceneRegistry';

const route = useRoute();
const router = useRouter();

onMounted(() => {
  const actionId = Number(route.query.action_id || 0);
  const menuId = Number(route.query.menu_id || 0);
  const sceneKey = parseSceneKeyFromQuery(route.query as LocationQueryRaw);
  const scene = findSceneByEntryAuthority({
    sceneKey,
    actionId: Number.isFinite(actionId) ? actionId : 0,
    menuId: Number.isFinite(menuId) ? menuId : 0,
    model: route.query.model,
    viewMode: route.query.view_mode,
  });
  const query = route.query as LocationQueryRaw;
  if (scene) {
    router.replace({
      path: scene.route || `/s/${scene.key}`,
      query: {
        ...query,
        scene_key: scene.key,
        action_id: Number.isFinite(actionId) && actionId > 0 ? actionId : (scene.target.action_id || undefined),
        menu_id: Number.isFinite(menuId) && menuId > 0 ? menuId : (scene.target.menu_id || undefined),
      },
    }).catch(() => {});
    return;
  }
  router
    .replace({
      name: 'workbench',
      query: {
        ...query,
        reason: ErrorCodes.CONTRACT_CONTEXT_MISSING,
        diag: Number.isFinite(actionId) && actionId > 0
          ? 'legacy_list_route_missing_scene_identity'
          : 'legacy_route_missing_action_id',
        action_id: Number.isFinite(actionId) && actionId > 0 ? actionId : undefined,
        menu_id: Number.isFinite(menuId) && menuId > 0 ? menuId : undefined,
      },
    })
    .catch(() => {});
});
</script>

<style scoped>
.page {
  padding: 12px;
}
</style>
