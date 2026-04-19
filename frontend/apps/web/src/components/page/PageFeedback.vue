<template>
  <section class="page-feedback">
    <slot />
  </section>
</template>

<style scoped>
.page-feedback {
  min-height: 24px;
  display: grid;
  gap: var(--ui-space-3);
}

.page-feedback :deep(> *) {
  width: min(100%, var(--ui-page-max-width));
  margin: 0 auto;
}
</style>
