<template>
  <section class="business-config-context business-config-header sc-product-page-header" aria-label="页面设计上下文">
    <ScPageHeader
      eyebrow="页面设计"
      :title="pageLabel || '选择一个业务页面开始配置'"
      subtitle="在同一工作台完成配置、检查、保存和运行态验证"
    >
      <template #actions>
        <ScButton
          variant="secondary"
          :disabled="!canOpenCurrentPage"
          @click="$emit('openCurrentEffectivePage')"
        >
          打开当前生效页面
        </ScButton>
        <ScButton variant="ghost" @click="$emit('toggleDeveloperTools')">
          {{ developerToolsOpen ? '收起开发者工具' : '开发者工具' }}
        </ScButton>
      </template>
    </ScPageHeader>
    <dl class="business-config-context__facts">
      <div><dt>适用公司</dt><dd>{{ companyLabel || '当前公司' }}</dd></div>
      <div><dt>适用角色</dt><dd>{{ roleLabel || '当前管理员角色' }}</dd></div>
      <div><dt>当前生效版本</dt><dd>{{ versionLabel }}</dd></div>
      <div>
        <dt>编辑状态</dt>
        <dd><ScStatusBadge :label="dirty ? '有未保存修改' : '当前已保存'" :semantic="dirty ? 'warning' : 'success'" /></dd>
      </div>
    </dl>
    <div v-if="$slots.actions" class="business-config-context__actions"><slot name="actions" /></div>
  </section>
</template>

<script setup lang="ts">
import ScButton from '../../components/design-system/ScButton.vue';
import ScPageHeader from '../../components/design-system/ScPageHeader.vue';
import ScStatusBadge from '../../components/design-system/ScStatusBadge.vue';

defineProps<{
  pageLabel: string;
  companyLabel: string;
  roleLabel: string;
  versionLabel: string;
  dirty: boolean;
  canOpenCurrentPage: boolean;
  developerToolsOpen: boolean;
}>();

defineEmits<{
  openCurrentEffectivePage: [];
  toggleDeveloperTools: [];
}>();
</script>

<style scoped>
.business-config-context { display: grid; gap: var(--sc-product-space-3); padding: var(--sc-product-space-3); background: var(--sc-app-panel); border-bottom: 1px solid var(--sc-app-border); }
.business-config-context__facts { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--sc-product-space-2); margin: 0; }
.business-config-context__facts div { min-width: 0; display: grid; gap: var(--sc-product-space-1); }
.business-config-context__facts dt { color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.business-config-context__facts dd { min-width: 0; margin: 0; color: var(--sc-app-text-primary); font-weight: 600; overflow-wrap: anywhere; }
.business-config-context__actions { display: flex; flex-wrap: wrap; gap: var(--sc-product-space-2); }
@media (max-width: 900px) { .business-config-context__facts { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 480px) { .business-config-context__facts { grid-template-columns: 1fr; } }
</style>
