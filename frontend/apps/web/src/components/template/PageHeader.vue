<template>
  <header class="template-page-header" data-component="PageHeader">
    <div class="template-page-header-main">
      <h1>{{ title }}</h1>
      <p v-if="subtitle" class="template-page-subtitle">{{ subtitle }}</p>
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
}>();
</script>

<style scoped>
.template-page-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 12px;
  margin-bottom: 16px;
}

.template-page-header-main {
  display: grid;
  gap: 0;
}

.template-page-header-main h1 {
  margin: 0;
  font-size: 36px;
  line-height: 1.12;
}

.template-page-subtitle {
  margin: 2px 0 0;
  font-size: 12px;
  color: #94a3b8;
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
    font-size: 30px;
  }
}
</style>
