<template>
  <header
    class="template-page-header sc-product-page-header"
    :class="{ 'template-page-header--title-hidden': hideTitle }"
    data-component="PageHeader"
  >
    <div class="template-page-header-main">
      <h1 v-if="!hideTitle">{{ title }}</h1>
      <p v-if="!hideTitle && subtitle" class="template-page-subtitle">{{ subtitle }}</p>
      <slot name="meta" />
    </div>
    <div v-if="$slots.status" class="template-page-header-status">
      <slot name="status" />
    </div>
    <div v-if="$slots.actions" class="template-page-header-actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
  hideTitle?: boolean;
}>();
</script>

<style scoped>
.template-page-header {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
  border-bottom: 1px solid var(--sc-app-border);
  padding: 4px 0 6px;
  margin-bottom: 6px;
  min-width: 0;
}

.template-page-header-main {
  display: grid;
  gap: 0;
  min-width: 0;
}

.template-page-header-main h1 {
  margin: 0;
  color: var(--sc-app-text-primary);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
  overflow-wrap: anywhere;
}

.template-page-subtitle {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--sc-semantic-text-muted);
}

.template-page-header-status {
  display: grid;
  gap: 4px;
  margin-left: auto;
  text-align: right;
  min-width: 240px;
  padding-top: 3px;
}

.template-page-header-status:empty {
  display: none;
}

.template-page-header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.template-page-header-actions:empty {
  display: none;
}

.template-page-header--title-hidden .template-page-header-main {
  display: none;
}

@media (max-width: 860px) {
  .template-page-header {
    flex-direction: column;
  }

  .template-page-header-status {
    width: 100%;
    margin-left: 0;
    text-align: left;
    min-width: 0;
  }

  .template-page-header-main h1 {
    font-size: 20px;
  }
}
</style>
