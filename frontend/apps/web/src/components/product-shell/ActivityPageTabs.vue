<template>
  <nav v-if="pages.length" class="activity-tabs" :aria-label="label">
    <div v-for="page in pages" :key="page.key" class="activity-tab" :class="{active:page.key===activeKey}">
      <button class="activity-tab-main" type="button" :title="page.title" @click="$emit('activate',page)"><span>{{ page.title }}</span></button>
      <button class="activity-tab-close" type="button" :aria-label="`${closeLabel} ${page.title}`" :title="`${closeLabel} ${page.title}`" @click.stop="$emit('close',page)">×</button>
    </div>
  </nav>
</template>
<script setup lang="ts">import type { ActivityPage } from '../../stores/session'; withDefaults(defineProps<{pages:ActivityPage[];activeKey:string;label?:string;closeLabel?:string}>(),{label:'活动页面',closeLabel:'关闭'}); defineEmits<{activate:[page:ActivityPage];close:[page:ActivityPage]}>();</script>
<style scoped>
.activity-tabs{display:flex;align-items:center;gap:4px;min-width:0;overflow-x:auto;overflow-y:hidden;padding:0 2px 1px;scrollbar-width:thin}.activity-tab{flex:0 1 152px;min-width:104px;max-width:200px;display:grid;grid-template-columns:minmax(0,1fr) 18px;align-items:center;border:1px solid var(--sc-app-border);border-radius:var(--sc-product-radius-control);background:var(--sc-app-panel);color:var(--sc-app-text-secondary);overflow:hidden}.activity-tab.active{border-color:var(--sc-app-info-border);background:var(--sc-app-info-bg);color:var(--sc-app-info-text)}.activity-tab-main,.activity-tab-close{min-width:0;height:26px;border:0;background:transparent;color:inherit;cursor:pointer}.activity-tab-main{padding:0 4px 0 6px;text-align:left;font-size:11px;font-weight:600}.activity-tab-main span{display:block;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.activity-tab-close{width:18px;padding:0;font-size:var(--sc-product-text-sm);line-height:1;opacity:.7}.activity-tab-close:hover{opacity:1;background:var(--sc-app-danger-bg)}@media(max-width:760px){.activity-tabs{display:none}}
</style>
