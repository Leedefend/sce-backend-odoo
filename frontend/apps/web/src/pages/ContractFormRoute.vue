<template>
  <ContractFormPage :key="routeIdentity" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import ContractFormPage from './ContractFormPage.vue';

const route = useRoute();
const routeIdentity = computed(() => [
  String(route.params.model || ''),
  String(route.params.id || ''),
  String(route.query.action_id || ''),
  String(route.query.menu_id || ''),
  String(route.query.company_id || ''),
].join(':'));
</script>
