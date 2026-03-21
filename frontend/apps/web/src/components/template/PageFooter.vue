<template>
  <section class="template-page-footer" data-component="PageFooter">
    <p v-if="hint" class="template-page-footer-hint">{{ hint }}</p>
    <div class="template-page-footer-actions">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  hint?: string;
}>(), {
  hint: '',
});
</script>

<style scoped>
.template-page-footer {
  grid-column: 1 / -1;
  border: 0;
  border-top: 1px solid #e5e7eb;
  border-radius: 0;
  margin-top: 8px;
  padding: 10px 0;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  box-sizing: border-box;
  position: sticky;
  bottom: 0;
  z-index: 6;
}

.template-page-footer-hint {
  margin: 0;
  font-size: 12px;
  color: #64748b;
  flex: 1 1 360px;
  min-width: 240px;
}

.template-page-footer-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.template-page-footer-actions :slotted(button) {
  min-width: 116px;
  min-height: 38px;
  white-space: nowrap;
}

@media (max-width: 860px) {
  .template-page-footer {
    align-items: stretch;
  }

  .template-page-footer-hint {
    min-width: 0;
    flex: 1 1 100%;
  }

  .template-page-footer-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
