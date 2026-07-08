<template>
  <MenuConfigView v-if="isMenuConfig" />
  <ActionView v-else />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import ActionView from './ActionView.vue';
import MenuConfigView from './MenuConfigView.vue';
import { useSessionStore } from '../stores/session';
import { isMenuConfigurationAction } from '../services/action_service';

const session = useSessionStore();
const route = useRoute();

function positiveInteger(value: unknown): number {
  const parsed = Number(value || 0);
  if (!Number.isFinite(parsed) || parsed <= 0) return 0;
  return Math.trunc(parsed);
}

const isMenuConfig = computed(() => {
  const routeActionId = positiveInteger(route.params.actionId || route.query.action_id);
  const currentActionId = positiveInteger(session.currentAction?.action_id || session.currentAction?.id);
  return routeActionId > 0
    && currentActionId === routeActionId
    && isMenuConfigurationAction(session.currentAction);
});
</script>
