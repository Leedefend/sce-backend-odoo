<template>
  <ScPanel class="business-config-change-set" data-business-config-change-set="v1">
    <div class="change-set-heading">
      <div>
        <p class="eyebrow">待发布变更</p>
        <h2>{{ title }}</h2>
      </div>
      <ScStatusBadge :label="statusLabel" :semantic="statusSemantic" />
    </div>
    <p v-if="!changeSet?.item_count" class="muted">表单、列表、搜索、分析和菜单的可逆修改会汇总到这里。</p>
    <ul v-else class="change-set-items">
      <li v-for="item in changeSet.items" :key="item.id">
        <strong>{{ typeLabel(item.config_type) }}</strong>
        <span>{{ summary(item) }}</span>
        <ScStatusBadge
          :label="item.validation_result?.ok === false ? '检查失败' : item.risk_level === 'high' ? '高影响' : '可逆'"
          :semantic="item.validation_result?.ok === false ? 'danger' : item.risk_level === 'high' ? 'warning' : 'default'"
        />
      </li>
    </ul>
    <div v-if="changeSet?.failure_message" class="status error">{{ changeSet.failure_message }}</div>
    <div class="change-set-actions">
      <ScButton variant="ghost" :disabled="busy || !changeSet?.item_count" @click="$emit('validate')">检查全部变化</ScButton>
      <ScButton variant="secondary" :disabled="busy || !changeSet?.item_count" @click="$emit('preview')">预览当前草稿</ScButton>
      <ScButton :disabled="busy || !changeSet?.item_count" @click="$emit('publish')">{{ publishing ? '发布中…' : '发布全部可逆配置' }}</ScButton>
      <ScButton v-if="changeSet?.state === 'published'" variant="danger" :disabled="busy" @click="$emit('rollback')">按批次回滚</ScButton>
      <ScButton v-else variant="ghost" :disabled="busy || !changeSet" @click="$emit('discard')">放弃草稿</ScButton>
    </div>
    <details class="high-risk-boundary">
      <summary>独立高风险操作</summary>
      <p>自定义字段、新增原生菜单、审批规则、批量补齐和跨环境整改不属于当前批量发布，需要单独确认。</p>
    </details>
  </ScPanel>
  <BusinessConfigDraftPreview :preview="changeSet?.preview || null" @device="$emit('preview', $event)" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import ScButton from '../../components/design-system/ScButton.vue';
import ScPanel from '../../components/design-system/ScPanel.vue';
import ScStatusBadge from '../../components/design-system/ScStatusBadge.vue';
import BusinessConfigDraftPreview from './BusinessConfigDraftPreview.vue';
import type { BusinessConfigChangeSet, BusinessConfigChangeSetItem } from '../../api/businessConfig';

const props = defineProps<{ changeSet: BusinessConfigChangeSet | null; busy?: boolean; publishing?: boolean }>();
defineEmits<{ validate: []; preview: [device?: 'desktop' | 'tablet' | 'mobile']; publish: []; rollback: []; discard: [] }>();

const title = computed(() => props.changeSet?.item_count ? `${props.changeSet.item_count} 项可逆配置` : '当前没有未发布修改');
const statusLabel = computed(() => ({
  draft: '有未发布修改', validating: '正在检查', ready: '可以发布', publishing: '发布中', published: '已发布', failed: '检查失败', discarded: '已放弃', superseded: '已回滚',
}[props.changeSet?.state || 'draft']));
const statusSemantic = computed<'default' | 'success' | 'danger'>(() => props.changeSet?.state === 'failed' ? 'danger' : props.changeSet?.state === 'ready' ? 'success' : 'default');
function typeLabel(value: string) { return ({ form: '表单', list: '列表', search: '搜索', analysis: '分析', menu: '菜单' } as Record<string, string>)[value] || '配置'; }
function summary(item: BusinessConfigChangeSetItem) {
  const value = item.diff_summary || {};
  return String(value.summary || value.label || item.target_key || '配置已修改');
}
</script>
