<template>
  <header :class="['template-page-header', { 'template-page-header--compact': compact }]" data-component="PageHeader">
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
  compact?: boolean;
}>();
</script>

<style scoped>
.template-page-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  border: 1px solid rgba(203, 213, 225, 0.92);
  border-radius: 20px;
  padding: 18px 20px;
  margin-bottom: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94));
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

.template-page-header-main {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.template-page-header-main h1 {
  margin: 0;
  font-size: 34px;
  line-height: 1.12;
  color: #0f172a;
}

.template-page-header--compact {
  padding: 12px 0 10px;
  margin-bottom: 12px;
  gap: 10px;
  border: 0;
  border-bottom: 1px solid #e5e7eb;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.template-page-header--compact .template-page-header-main h1 {
  font-size: 22px;
  line-height: 1.22;
}

.template-page-header--compact .template-page-subtitle {
  margin-top: 0;
  font-size: 11px;
}

.template-page-subtitle {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

.template-page-header-status {
  display: grid;
  gap: 8px;
  margin-left: auto;
  min-width: 280px;
}

.template-page-header-status:empty {
  display: none;
}

.template-page-header-status :deep(.header-status-cards) {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.template-page-header-status :deep(.header-status-card) {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid rgba(203, 213, 225, 0.85);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
}

.template-page-header-status :deep(.header-status-card__label) {
  font-size: 11px;
  color: #64748b;
}

.template-page-header-status :deep(.header-status-card__value) {
  font-size: 13px;
  line-height: 1.35;
  color: #0f172a;
}

.template-page-header-status :deep(.header-status-card--status) {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.template-page-header-status :deep(.header-status-card--action) {
  background: #f8fafc;
}

.template-page-header-status :deep(.header-status-card--warning) {
  background: #fffbeb;
  border-color: #fde68a;
}

.template-page-header-status :deep(.header-status-card--support) {
  background: #f8fafc;
}

.template-page-header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
  align-items: center;
}

.template-page-header-actions:empty {
  display: none;
}

.template-page-header-actions :deep(button) {
  min-height: 38px;
  border-radius: 10px;
  padding: 0 14px;
}

@media (max-width: 860px) {
  .template-page-header {
    flex-direction: column;
  }

  .template-page-header-status {
    width: 100%;
    margin-left: 0;
    min-width: 0;
  }

  .template-page-header-status :deep(.header-status-cards) {
    grid-template-columns: 1fr;
  }

  .template-page-header-main h1 {
    font-size: 30px;
  }
}
</style>
