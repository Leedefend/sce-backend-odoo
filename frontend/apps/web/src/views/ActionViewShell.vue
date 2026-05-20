<template>
  <MenuConfigView v-if="isMenuConfig" />
  <ActionView v-else />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import ActionView from './ActionView.vue';
import MenuConfigView from './MenuConfigView.vue';
import { useSessionStore } from '../stores/session';
import { isMenuConfigurationAction } from '../services/action_service';

const session = useSessionStore();
const isMenuConfig = computed(() => isMenuConfigurationAction(session.currentAction));
</script>
