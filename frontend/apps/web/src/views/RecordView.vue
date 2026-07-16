<template>
  <ContractFormPage data-record-view-compatibility-delegate />
</template>

<script setup lang="ts">
/**
 * Compatibility-only entry.
 *
 * Product record routes are owned by ContractFormPage. Keeping this tiny
 * delegate prevents internal imports from reviving the retired parallel
 * record runtime while all identity, access, relationship and state handling
 * stays on the single authoritative page path.
 */
import ContractFormPage from '../pages/ContractFormPage.vue';
</script>
