<template>
  <RouterView v-slot="{ Component, route }">
    <AppShell v-if="route.meta?.layout === 'shell'">
      <KeepAlive :max="6">
        <component
          :is="Component"
          v-if="activityCacheKey(route)"
          :key="activityCacheKey(route)"
        />
      </KeepAlive>
      <component
        :is="Component"
        v-if="!activityCacheKey(route)"
        :key="route.fullPath"
      />
    </AppShell>
    <component :is="Component" v-else />
  </RouterView>
</template>

<script setup lang="ts">
import type { RouteLocationNormalizedLoaded } from 'vue-router';
import AppShell from './layouts/AppShell.vue';
import { useSessionStore } from './stores/session';

const session = useSessionStore();

function routeText(value: unknown): string {
  if (Array.isArray(value)) return String(value[0] || '').trim();
  return String(value || '').trim();
}

function activityRouteKey(route: RouteLocationNormalizedLoaded): string {
  if (route.name === 'action') {
    const actionId = routeText(route.params.actionId || route.query.action_id);
    const menuId = routeText(route.query.menu_id);
    return actionId ? `action:${actionId}:menu:${menuId || '0'}` : '';
  }
  if (route.name === 'record' || route.name === 'model-form') {
    const model = routeText(route.params.model);
    const recordId = routeText(route.params.id);
    return model && recordId && recordId !== 'new' ? `record:${model}:${recordId}` : '';
  }
  if (route.name === 'scene' || route.name === 'projects-intake' || String(route.name || '').startsWith('scene-')) {
    const sceneKey = routeText(route.params.sceneKey || route.meta?.sceneKey || route.query.scene_key || route.query.scene);
    if (!sceneKey || sceneKey === 'workspace.home') return '';
    return `scene:${sceneKey}`;
  }
  if (route.name === 'my-work' || route.name === 'scene-my-work') return 'workspace:my-work';
  return '';
}

function activityCacheKey(route: RouteLocationNormalizedLoaded): string {
  const routeKey = activityRouteKey(route);
  if (!routeKey) return '';
  const epoch = Number(session.activityPageCacheEpochs[routeKey] || 0);
  return `activity:${routeKey}:${epoch}`;
}
</script>
