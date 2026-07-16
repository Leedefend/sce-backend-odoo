<template>
  <PageHeaderTemplate :title="title" :subtitle="subtitle || undefined" :hide-title="hideTitle">
    <template #meta>
      <p v-if="showHud" class="meta">model={{ model }} · id={{ recordIdDisplay }} · action={{ actionId || '-' }}</p>
      <p v-if="showHud && contractMetaLine" class="meta">{{ contractMetaLine }}</p>
    </template>
    <template #status>
      <template v-if="intakeMode">
        <p class="header-status-item">当前进度：{{ intakeRequiredSummary }}</p>
        <p class="header-status-item" :class="{ 'header-status-item--danger': intakeMissingSummary !== '无' }">缺少：{{ intakeMissingSummary }}</p>
      </template>
      <section v-else-if="statusbar.visible" class="native-statusbar native-statusbar--header" aria-label="业务状态">
        <button
          v-for="item in statusbar.states"
          :key="String(item.value)"
          type="button"
          class="native-statusbar-step"
          :class="{ 'native-statusbar-step--active': statusbar.current === String(item.value), 'native-statusbar-step--done': statusbar.reachedValues.includes(String(item.value)) }"
          :disabled="busy || statusbar.readonly"
          @click="$emit('set-status', String(item.value))"
        >{{ item.label }}</button>
      </section>
    </template>
    <template #actions>
      <span class="contract-header-action-label">办理操作</span>
      <button v-if="!intakeMode" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy" type="button" @click="$emit('back')">返回列表</button>
      <button v-if="showReturn" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy" @click="$emit('return-workbench')">返回工作台</button>
      <button v-if="showDraftSave" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="draftSaveDisabled" @click="$emit('save-draft')">{{ draftSaveLabel }}</button>
      <button v-if="showPrimaryFormAction" class="sc-btn sc-btn-primary sc-btn-sm" :disabled="primaryFormActionDisabled" @click="$emit('run-primary')">{{ submitLabel }}</button>
      <button v-for="action in directActions" :key="`hdr-${action.key}`" :class="buttonClass(action)" :disabled="busy || !action.enabled" :title="action.hint" @click="$emit('run-action', action)">{{ action.label }}</button>
      <details v-if="overflowActions.length" class="contract-header-more-actions">
        <summary class="sc-btn sc-btn-ghost sc-btn-sm">更多操作</summary>
        <div><button v-for="action in overflowActions" :key="`hdr-more-${action.key}`" :class="buttonClass(action)" :disabled="busy || !action.enabled" :title="action.hint" @click="$emit('run-action', action)">{{ action.label }}</button></div>
      </details>
      <span v-if="configActions.length" class="contract-header-action-separator" aria-hidden="true" />
      <button v-for="action in configActions" :key="`hdr-config-${action.key}`" class="sc-btn sc-btn-ghost sc-btn-sm contract-header-config-action" :disabled="busy || !action.enabled" :title="action.hint" @click="$emit('run-action', action)">{{ action.label }}</button>
      <button v-if="showDiscard" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy" @click="$emit('discard')">{{ discardLabel }}</button>
      <button v-if="showDebug && !intakeMode" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy || !contractPresent" @click="$emit('copy')">复制配置</button>
      <button v-if="showDebug && !intakeMode" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy || !contractPresent" @click="$emit('export')">导出配置</button>
      <button v-if="showDebug && !intakeMode" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy" @click="$emit('reload')">{{ reloadLabel }}</button>
    </template>
  </PageHeaderTemplate>
</template>

<script setup lang="ts">
import PageHeaderTemplate from '../../components/template/PageHeader.vue';
import type { ContractAction, NativeStatusbarVm } from './types';

defineProps<{
  title: string; subtitle: string; hideTitle: boolean; showHud: boolean; model: string; recordIdDisplay: string;
  actionId: number | null; contractMetaLine: string; intakeMode: boolean; intakeRequiredSummary: string;
  intakeMissingSummary: string; statusbar: NativeStatusbarVm; busy: boolean; showReturn: boolean;
  showDraftSave: boolean; draftSaveDisabled: boolean; draftSaveLabel: string; showPrimaryFormAction: boolean;
  primaryFormActionDisabled: boolean; submitLabel: string; directActions: ContractAction[]; overflowActions: ContractAction[];
  configActions: ContractAction[]; showDiscard: boolean; showDebug: boolean; contractPresent: boolean;
  discardLabel: string; reloadLabel: string;
}>();

defineEmits<{
  back: []; 'set-status': [value: string]; 'return-workbench': []; 'save-draft': []; 'run-primary': [];
  'run-action': [action: ContractAction]; discard: []; copy: []; export: []; reload: [];
}>();

function buttonClass(action: ContractAction) {
  return ['sc-btn', 'sc-btn-sm', action.destructive ? 'sc-btn-danger' : action.presentationTier === 'primary' || action.semantic === 'primary_action' ? 'sc-btn-primary' : 'sc-btn-ghost'];
}
</script>

<style scoped>
.contract-header-action-label { display: inline-flex; align-items: center; min-height: 28px; padding: 0 7px; color: var(--sc-app-text-secondary); font-size: 11px; font-weight: 600; white-space: nowrap; }
.contract-header-action-separator { align-self: center; width: 1px; height: 16px; background: var(--sc-app-border); }
.contract-header-more-actions { position: relative; }
.contract-header-more-actions > summary { list-style: none; cursor: pointer; }
.contract-header-more-actions > summary::-webkit-details-marker { display: none; }
.contract-header-more-actions > div { position: absolute; z-index: 30; top: calc(100% + 6px); right: 0; display: grid; min-width: 180px; gap: 6px; padding: 8px; border: 1px solid var(--sc-app-border); border-radius: var(--sc-component-panel-radius); background: var(--sc-app-panel); box-shadow: var(--sc-product-shadow-overlay); }
.contract-header-config-action { color: var(--sc-semantic-text-muted); }
.native-statusbar--header .native-statusbar-step { min-width: 68px; min-height: 30px; padding: 0 10px; }
</style>
