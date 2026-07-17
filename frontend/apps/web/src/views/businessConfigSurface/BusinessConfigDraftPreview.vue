<template>
  <ScPanel v-if="preview" class="business-config-draft-preview" aria-label="当前草稿效果">
    <header>
      <div><p class="eyebrow">当前草稿效果</p><h2>{{ deviceLabel }}</h2></div>
      <ScStatusBadge label="仅创建者可见" semantic="info" />
    </header>
    <p class="muted">此预览读取临时变更集，不改变线上合同、版本或其他用户页面；令牌到期后自动失效。</p>
    <div class="preview-devices" role="group" aria-label="预览设备">
      <ScButton v-for="option in devices" :key="option.value" :variant="preview.device === option.value ? 'primary' : 'ghost'" @click="$emit('device', option.value)">{{ option.label }}</ScButton>
      <ScButton variant="primary" :disabled="!runtimePreviewItem" @click="openRuntimePreview">打开草稿运行页</ScButton>
    </div>
    <div class="preview-canvas" :class="`preview-canvas--${preview.device}`">
      <article v-for="item in preview.items" :key="item.id" class="preview-item">
        <header><strong>{{ typeLabel(item.config_type) }}</strong><span>{{ item.diff_summary?.summary || '配置已修改' }}</span></header>
        <dl>
          <div><dt>当前线上</dt><dd>版本 {{ item.current_version || '尚未配置' }}</dd></div>
          <div><dt>当前草稿</dt><dd>{{ draftSummary(item) }}</dd></div>
        </dl>
      </article>
    </div>
  </ScPanel>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import ScButton from '../../components/design-system/ScButton.vue';
import ScPanel from '../../components/design-system/ScPanel.vue';
import ScStatusBadge from '../../components/design-system/ScStatusBadge.vue';
import type { BusinessConfigChangeSet, BusinessConfigChangeSetItem } from '../../api/businessConfig';

const props = defineProps<{ preview: BusinessConfigChangeSet['preview'] | null }>();
defineEmits<{ device: [value: 'desktop' | 'tablet' | 'mobile'] }>();
const devices = [{ value: 'desktop', label: '桌面' }, { value: 'tablet', label: '平板' }, { value: 'mobile', label: '手机' }] as const;
const deviceLabel = computed(() => devices.find((item) => item.value === props.preview?.device)?.label || '桌面');
const runtimePreviewItem = computed(() => props.preview?.items.find((item) => Number(item.action_id || 0) > 0) || null);
function openRuntimePreview() {
  const item = runtimePreviewItem.value;
  const preview = props.preview;
  if (!item || !preview) return;
  const query = new URLSearchParams({ preview_token: preview.token, preview_role_key: preview.role_key || '' });
  if (item.view_type) query.set('view_mode', item.view_type === 'list' ? 'tree' : item.view_type);
  window.open(`/a/${Number(item.action_id)}?${query.toString()}`, '_blank', 'noopener,noreferrer');
}
function typeLabel(value: string) { return ({ form: '表单', list: '列表', search: '搜索', analysis: '分析', menu: '菜单' } as Record<string, string>)[value] || '配置'; }
function draftSummary(item: BusinessConfigChangeSetItem) {
  const orchestration = item.draft_payload?.view_orchestration as Record<string, unknown> | undefined;
  const views = orchestration?.views as Record<string, Record<string, unknown>> | undefined;
  const view = views?.[item.view_type];
  const rows = (item.draft_payload?.rows as unknown[] | undefined) || [];
  if (rows.length) return `${rows.length} 项菜单规则`;
  for (const key of ['fields', 'columns', 'filters', 'measures', 'dimensions']) {
    const values = view?.[key]; if (Array.isArray(values)) return `${values.length} 项${typeLabel(item.config_type)}配置`;
  }
  return '已通过正式布局契约校验';
}
</script>
