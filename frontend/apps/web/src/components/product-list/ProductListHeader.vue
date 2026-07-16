<template>
  <header class="product-list-header sc-product-page-toolbar">
    <div class="product-list-header__identity">
      <h2>{{ title }}</h2>
      <p v-if="subtitle">{{ subtitle }}</p>
    </div>
    <div class="product-list-header__tools">
      <slot />
    </div>
    <form v-if="showSearch" class="product-list-header__search" role="search" @submit.prevent="$emit('search-submit')">
      <label>
        <span class="sc-visually-hidden">{{ searchLabel }}</span>
        <input
          type="search"
          :value="searchValue"
          :disabled="loading"
          :placeholder="searchPlaceholder"
          @compositionstart="$emit('composition-start')"
          @compositionend="$emit('composition-end', $event)"
          @input="$emit('search-input', $event)"
        />
      </label>
      <button type="submit" class="pagination-btn" :disabled="loading">{{ searchLabel }}</button>
      <button v-if="searchValue" type="button" class="pagination-btn ghost" :disabled="loading" @click="$emit('search-clear')">清除</button>
    </form>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
  loading: boolean;
  showSearch: boolean;
  searchValue: string;
  searchLabel: string;
  searchPlaceholder: string;
}>();

defineEmits<{
  'search-input': [event: Event];
  'search-submit': [];
  'search-clear': [];
  'composition-start': [];
  'composition-end': [event: CompositionEvent];
}>();
</script>

<style scoped>
.product-list-header {
  display: grid;
  grid-template-columns: minmax(180px, auto) minmax(0, 1fr);
  gap: var(--sc-product-space-2);
  align-items: start;
}
.product-list-header__identity h2,
.product-list-header__identity p { margin: 0; }
.product-list-header__identity p { margin-top: 4px; color: var(--sc-app-text-secondary); }
.product-list-header__tools { min-width: 0; }
.product-list-header__search { grid-column: 1 / -1; display: flex; gap: var(--sc-product-space-1); align-items: center; }
.product-list-header__search label { min-width: 0; flex: 1; }
.product-list-header__search input { width: 100%; min-height: var(--sc-product-control-height); padding: 0 12px; border: 1px solid var(--sc-app-border); border-radius: var(--sc-product-radius-control); background: var(--sc-app-panel); color: var(--sc-app-text-primary); }
@media (max-width: 720px) {
  .product-list-header { grid-template-columns: 1fr; }
  .product-list-header__search { grid-column: 1; display: grid; grid-template-columns: minmax(0, 1fr) auto; }
  .product-list-header__search .ghost { grid-column: 1 / -1; justify-self: start; }
}
</style>
