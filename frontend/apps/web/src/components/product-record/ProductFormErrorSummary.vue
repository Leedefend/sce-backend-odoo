<template>
  <section v-if="errors.length || conflict" class="product-form-errors" role="alert" aria-labelledby="product-form-errors-title" tabindex="-1">
    <h2 id="product-form-errors-title">{{ conflict ? '记录已被其他操作更新' : '请检查以下内容' }}</h2>
    <p v-if="conflict">当前页面保留了你的输入。继续编辑前，请先加载最新数据。</p>
    <ul v-if="errors.length">
      <li v-for="(error, index) in errors" :key="`${index}-${error}`">
        <button type="button" @click="$emit('focus-error', error)">{{ error }}</button>
      </li>
    </ul>
    <button v-if="conflict" type="button" class="sc-btn sc-btn-secondary" @click="$emit('reload-latest')">加载最新数据</button>
  </section>
</template>

<script setup lang="ts">
defineProps<{ errors: string[]; conflict?: boolean }>();
defineEmits<{ 'focus-error': [message: string]; 'reload-latest': [] }>();
</script>

<style scoped>
.product-form-errors { display: grid; gap: 10px; padding: var(--sc-product-space-2); border: 1px solid var(--sc-app-danger-border); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-danger-bg); color: var(--sc-app-danger-text); }
.product-form-errors h2, .product-form-errors p, .product-form-errors ul { margin: 0; }
.product-form-errors h2 { font-size: 17px; }
.product-form-errors ul { display: grid; gap: 4px; padding-left: 20px; }
.product-form-errors li button { padding: 2px 0; border: 0; background: transparent; color: inherit; text-align: left; text-decoration: underline; cursor: pointer; }
.product-form-errors > .sc-btn { justify-self: start; }
</style>
