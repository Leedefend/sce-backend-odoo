<template>
  <section
    class="financial-workspace__status product-record-status"
    :data-state="state.value"
    :data-semantic="state.semantic || 'default'"
    data-product-record-status
    aria-label="当前业务状态"
  >
    <div>
      <span class="product-record-status__label">当前状态</span>
      <strong>{{ state.label || '未标注' }}</strong>
    </div>
    <p v-if="state.description">{{ state.description }}</p>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  state: { value: string; label: string; semantic?: string; description?: string };
}>();
</script>

<style scoped>
.product-record-status { display: flex; align-items: center; justify-content: space-between; gap: var(--sc-product-space-2); padding: var(--sc-product-space-2); border: 1px solid var(--sc-app-border); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-subtle-bg); }
.product-record-status > div { display: grid; gap: 2px; }
.product-record-status__label { color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.product-record-status strong { font-size: 17px; }
.product-record-status p { max-width: 560px; margin: 0; color: var(--sc-app-text-secondary); }
.product-record-status[data-semantic="success"] { border-color: var(--sc-app-success-border); background: var(--sc-app-success-bg); }
.product-record-status[data-semantic="warning"] { border-color: var(--sc-app-warning-border); background: var(--sc-app-warning-bg); }
.product-record-status[data-semantic="danger"] { border-color: var(--sc-app-danger-border); background: var(--sc-app-danger-bg); }
@media (max-width: 600px) { .product-record-status { align-items: stretch; flex-direction: column; } }
</style>
