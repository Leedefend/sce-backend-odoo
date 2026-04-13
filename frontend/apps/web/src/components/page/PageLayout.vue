<template>
  <section class="page-layout">
    <header v-if="$slots.header" class="page-layout-header">
      <slot name="header" />
    </header>
    <section v-if="$slots.toolbar" class="page-layout-toolbar">
      <slot name="toolbar" />
    </section>
    <section v-if="$slots.filter" class="page-layout-filter">
      <slot name="filter" />
    </section>
    <section class="page-layout-content">
      <slot name="content" />
    </section>
    <footer v-if="$slots.feedback" class="page-layout-feedback">
      <slot name="feedback" />
    </footer>
  </section>
</template>

<style scoped>
.page-layout {
  display: grid;
  gap: 16px;
}

.page-layout-header,
.page-layout-toolbar,
.page-layout-filter,
.page-layout-content,
.page-layout-feedback {
  min-width: 0;
}
</style>
