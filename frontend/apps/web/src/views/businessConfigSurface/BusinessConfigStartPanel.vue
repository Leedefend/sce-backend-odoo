<template>
  <section class="workbench-start sc-product-main-surface" data-lowcode-workbench-ia="start">
    <div class="workbench-start-main">
      <div class="workbench-start-lead">
        <div class="workbench-start-copy">
          <span>当前范围</span>
          <strong>{{ selectedPageLabel || currentModel || '未选择业务页面' }}</strong>
          <em>{{ startScopeSummary }}</em>
        </div>
        <div class="workbench-start-actions">
          <button type="button" class="ghost primary" :disabled="scanLoading" @click="$emit('scanSystemRootCoverage')">
            {{ scanLoading ? '读取中...' : '选择业务页面' }}
          </button>
          <button type="button" class="ghost" :disabled="!previewRoutePath" @click="$emit('previewSelectedRuntimeRoute')">预览页面</button>
        </div>
      </div>
      <div v-if="currentModel && sections.length" class="workbench-start-config">
        <div class="selected-page-overview">
          <div>
            <span>正在配置</span>
            <strong>{{ selectedPageLabel || currentModel }}</strong>
          </div>
          <div class="selected-page-overview-side">
            <div class="selected-page-overview-meta">
              <span>页面配置</span>
              <span>{{ startScopeSummary }}</span>
            </div>
          </div>
        </div>
        <div class="section-grid section-grid--start" data-lowcode-config-task-grid="v1">
          <article v-for="section in sections" :key="`start-${section.key}`" class="config-card" data-lowcode-config-task-card="v1">
            <div class="config-card-head">
              <div>
                <span>{{ sectionTaskKindLabel(section.key) }}</span>
                <h2>{{ sectionDisplayLabel(section.key, section.label) }}</h2>
              </div>
              <strong class="config-status-badge" :class="{ 'config-status--empty': !section.contract_count }">{{ sectionStatusLabel(section.key, section.contract_count) }}</strong>
            </div>
            <div class="config-task-impact">
              <span>{{ sectionPrimaryCopy(section.key) }}</span>
              <em>{{ sectionImpactText(section.key) }}</em>
            </div>
            <div class="config-card-meta" data-lowcode-config-task-meta="v1">
              <span>{{ advancedPanelOpen ? boundaryLabel(section.boundary) : sectionHelpLabel(section.key) }}</span>
              <span>{{ sectionTaskCoverageText(section.key, section.contract_count) }}</span>
            </div>
            <div class="config-card-actions">
              <button
                v-if="section.key === 'form' || section.key === 'list_search' || section.key === 'analysis'"
                type="button"
                class="ghost small"
                :disabled="!currentModel || versionsLoading"
                @click="$emit('loadVersions', section.key)"
              >
                {{ versionsLoading ? '读取中...' : '版本记录' }}
              </button>
              <button
                v-if="section.key === 'list_search'"
                type="button"
                class="ghost small"
                :disabled="!currentModel || listSearchBusy"
                @click="$emit('loadListSearchConfig')"
              >
                {{ listSearchBusy ? '读取中...' : sectionPrimaryActionLabel(section.key) }}
              </button>
              <button
                v-else-if="section.key === 'form'"
                type="button"
                class="ghost small primary"
                :disabled="!canOpenDesigner"
                @click="$emit('openFormConfig')"
              >
                {{ sectionPrimaryActionLabel(section.key) }}
              </button>
              <button
                v-else-if="section.key === 'menu'"
                type="button"
                class="ghost small"
                @click="$emit('openMenuConfig')"
              >
                {{ sectionPrimaryActionLabel(section.key) }}
              </button>
              <button
                v-if="section.key === 'menu'"
                type="button"
                class="ghost small"
                @click="$emit('openCreateMenuConfig')"
              >
                新增菜单
              </button>
              <button
                v-else-if="section.key === 'analysis'"
                type="button"
                class="ghost small"
                :disabled="!currentModel || listSearchBusy"
                @click="$emit('loadAnalysisConfig')"
              >
                {{ listSearchBusy ? '读取中...' : sectionPrimaryActionLabel(section.key) }}
              </button>
              <button
                v-else-if="section.key === 'approval'"
                type="button"
                class="ghost small primary"
                :disabled="!currentModel || approvalLoading"
                @click="$emit('loadApprovalConfig')"
              >
                {{ approvalLoading ? '读取中...' : sectionPrimaryActionLabel(section.key) }}
              </button>
            </div>
          </article>
        </div>
      </div>
    </div>
    <aside v-if="showStatus" class="workbench-start-status" data-lowcode-delivery-readiness="low_code_delivery_readiness.v1">
      <div class="delivery-readiness-head">
        <div>
          <span>交付状态</span>
          <strong>{{ deliveryReadinessStatusText }}</strong>
        </div>
        <em>{{ visibleDeliveryReadinessProgressText }}</em>
      </div>
      <div class="delivery-readiness-grid delivery-readiness-grid--compact">
        <button
          v-for="item in visibleDeliveryReadinessItems"
          :key="item.id"
          type="button"
          class="delivery-readiness-item"
          :class="{ 'delivery-readiness-item--pending': item.status !== 'ready' }"
          @click="$emit('runDeliveryReadinessAction', item)"
        >
          <span>{{ item.label }}</span>
          <strong>{{ deliveryReadinessItemStatusText(item) }}</strong>
          <em>{{ deliveryReadinessItemMetaText(item) }}</em>
        </button>
      </div>
      <div v-if="!visibleDeliveryReadinessItems.length" class="workbench-status-empty">状态读取中</div>
    </aside>
  </section>
</template>

<script setup lang="ts">
import type { BusinessConfigSurfacePayload } from '../../api/businessConfig';

type SurfaceSection = BusinessConfigSurfacePayload['sections'][number];
type DeliveryItem = NonNullable<BusinessConfigSurfacePayload['delivery_readiness']>['items'][number];

defineProps<{
  selectedPageLabel: string;
  currentModel: string;
  startScopeSummary: string;
  scanLoading: boolean;
  previewRoutePath: string;
  sections: SurfaceSection[];
  advancedPanelOpen: boolean;
  versionsLoading: boolean;
  listSearchBusy: boolean;
  approvalLoading: boolean;
  canOpenDesigner: boolean;
  showStatus: boolean;
  deliveryReadinessStatusText: string;
  visibleDeliveryReadinessProgressText: string;
  visibleDeliveryReadinessItems: DeliveryItem[];
  sectionTaskKindLabel: (sectionKey: string) => string;
  sectionDisplayLabel: (sectionKey: string, fallback: string) => string;
  sectionStatusLabel: (sectionKey: string, contractCount: number) => string;
  sectionPrimaryCopy: (sectionKey: string) => string;
  sectionImpactText: (sectionKey: string) => string;
  boundaryLabel: (boundary: unknown) => string;
  sectionHelpLabel: (sectionKey: string) => string;
  sectionTaskCoverageText: (sectionKey: string, contractCount: number) => string;
  sectionPrimaryActionLabel: (sectionKey: string) => string;
  deliveryReadinessItemStatusText: (item: DeliveryItem) => string;
  deliveryReadinessItemMetaText: (item: DeliveryItem) => string;
}>();

defineEmits<{
  scanSystemRootCoverage: [];
  previewSelectedRuntimeRoute: [];
  loadVersions: [sectionKey: string];
  loadListSearchConfig: [];
  openFormConfig: [];
  openMenuConfig: [];
  openCreateMenuConfig: [];
  loadAnalysisConfig: [];
  loadApprovalConfig: [];
  runDeliveryReadinessAction: [item: DeliveryItem];
}>();
</script>
