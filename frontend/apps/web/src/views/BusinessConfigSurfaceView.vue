<template>
  <section v-if="pageSectionsReady" class="business-config-page" :style="pageSectionStyle('root')" :data-contract-sections="pageSectionsFingerprint">
    <header class="business-config-header">
      <div>
        <p class="eyebrow">低代码页面设计器</p>
        <h1>{{ designerTitle }}</h1>
      </div>
      <div class="header-actions">
        <button
          v-for="action in pageGlobalActions"
          :key="action.key"
          type="button"
          class="ghost"
          :disabled="action.disabled"
          @click="executeGlobalPageAction(action.key)"
        >
          {{ action.label }}
        </button>
        <button type="button" class="ghost primary" :disabled="!canOpenDesigner" @click="openFormConfig">
          {{ headerDesignerButtonLabel }}
        </button>
        <button type="button" class="ghost" :disabled="scanLoading" @click="scanSystemRootCoverage">
          {{ scanLoading ? '读取中...' : '选择业务页面' }}
        </button>
        <button type="button" class="ghost" :disabled="loading" @click="advancedPanelOpen = !advancedPanelOpen">
          高级设置
        </button>
      </div>
    </header>

    <div v-if="error" class="status error">{{ error }}</div>
    <div v-else-if="message.text" class="status ok">
      <span>{{ message.text }}</span>
      <small v-if="advancedPanelOpen && message.detail">{{ message.detail }}</small>
    </div>

    <section v-if="!coverageScan" class="workbench-start" data-lowcode-workbench-ia="start">
      <div class="workbench-start-main">
        <div class="workbench-start-lead">
          <div class="workbench-start-copy">
            <span>当前范围</span>
            <strong>{{ selectedPageLabel || currentModel || '未选择业务页面' }}</strong>
            <em>{{ startScopeSummary }}</em>
          </div>
          <div class="workbench-start-actions">
            <button type="button" class="ghost primary" :disabled="scanLoading" @click="scanSystemRootCoverage">
              {{ scanLoading ? '读取中...' : '选择业务页面' }}
            </button>
            <button type="button" class="ghost" :disabled="!canOpenDesigner" @click="openFormConfig">
              {{ headerDesignerButtonLabel }}
            </button>
            <button type="button" class="ghost" :disabled="!previewRouteTarget.path" @click="previewSelectedRuntimeRoute">预览页面</button>
          </div>
        </div>
        <div v-if="currentModel && visibleConfigSections.length" class="workbench-start-config">
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
            <article v-for="section in visibleConfigSections" :key="`start-${section.key}`" class="config-card" data-lowcode-config-task-card="v1">
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
                  @click="loadVersions(section.key)"
                >
                  {{ versionsLoading ? '读取中...' : '版本记录' }}
                </button>
                <button
                  v-if="section.key === 'list_search'"
                  type="button"
                  class="ghost small"
                  :disabled="!currentModel || listSearchBusy"
                  @click="loadListSearchConfig"
                >
                  {{ listSearchBusy ? '读取中...' : sectionPrimaryActionLabel(section.key) }}
                </button>
                <button
                  v-else-if="section.key === 'form'"
                  type="button"
                  class="ghost small primary"
                  :disabled="!canOpenDesigner"
                  @click="openFormConfig"
                >
                  {{ sectionPrimaryActionLabel(section.key) }}
                </button>
                <button
                  v-else-if="section.key === 'menu'"
                  type="button"
                  class="ghost small"
                  @click="openMenuConfig"
                >
                  {{ sectionPrimaryActionLabel(section.key) }}
                </button>
                <button
                  v-if="section.key === 'menu'"
                  type="button"
                  class="ghost small"
                  @click="openCreateMenuConfig"
                >
                  新增菜单
                </button>
                <button
                  v-else-if="section.key === 'analysis'"
                  type="button"
                  class="ghost small"
                  :disabled="!currentModel || listSearchBusy"
                  @click="loadAnalysisConfig"
                >
                  {{ listSearchBusy ? '读取中...' : sectionPrimaryActionLabel(section.key) }}
                </button>
                <button
                  v-else-if="section.key === 'approval'"
                  type="button"
                  class="ghost small primary"
                  :disabled="!currentModel || approvalLoading"
                  @click="loadApprovalConfig"
                >
                  {{ approvalLoading ? '读取中...' : sectionPrimaryActionLabel(section.key) }}
                </button>
              </div>
            </article>
          </div>
        </div>
      </div>
      <aside v-if="surface" class="workbench-start-status" data-lowcode-delivery-readiness="low_code_delivery_readiness.v1">
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
            @click="runDeliveryReadinessAction(item)"
          >
            <span>{{ item.label }}</span>
            <strong>{{ deliveryReadinessItemStatusText(item) }}</strong>
            <em>{{ deliveryReadinessItemMetaText(item) }}</em>
          </button>
        </div>
        <div v-if="!visibleDeliveryReadinessItems.length" class="workbench-status-empty">状态读取中</div>
      </aside>
    </section>

    <section v-if="advancedPanelOpen" class="scope-panel">
      <label>
        <span>业务对象</span>
        <input v-model="scopeModel" type="text" placeholder="res.partner" />
      </label>
      <label>
        <span>页面ID</span>
        <input v-model.number="scopeActionId" type="number" min="0" />
      </label>
      <label>
        <span>视图ID</span>
        <input v-model.number="scopeViewId" type="number" min="0" />
      </label>
      <label>
        <span>角色编码</span>
        <input v-model="scopeRoleKey" type="text" placeholder="可选 role_key" />
      </label>
      <button type="button" class="ghost small" :disabled="loading" @click="applyScopeAndLoad">读取配置对象</button>
    </section>

    <section v-if="loading" class="loading-state">正在读取配置能力...</section>
    <section v-if="coverageScan" class="scan-panel">
      <div class="scan-toolbar">
        <label class="page-search">
          <span>页面搜索</span>
          <input v-model="pageSearch" type="search" placeholder="输入页面名称" />
        </label>
        <div class="page-type-tabs" role="group" aria-label="页面类型筛选">
          <button
            v-for="option in pageTypeOptions"
            :key="option.key"
            type="button"
            :class="{ active: pageTypeFilter === option.key }"
            @click="pageTypeFilter = option.key"
          >
            {{ option.label }}
          </button>
        </div>
        <label v-if="advancedPanelOpen" class="scan-toggle">
          <input v-model="showOnlyIssues" type="checkbox" />
          <span>只看需处理</span>
        </label>
        <button v-if="advancedPanelOpen" type="button" class="ghost small" @click="copyCoverageSummary">
          复制配置摘要
        </button>
        <button
          v-if="advancedPanelOpen"
          type="button"
          class="ghost small"
          :disabled="scanLoading || listSearchSaving || !coverageBatchBootstrapRows.length"
          @click="bootstrapCoverageMissing"
        >
          {{ listSearchSaving ? '生成中...' : '批量补齐配置' }}
        </button>
      </div>
      <div class="scan-summary">
        <span>业务页面 {{ coverageScan.summary.action_count }}</span>
        <span>当前显示 {{ visibleCoverageRows.length }}</span>
        <span v-if="advancedPanelOpen">{{ coverageScopeLabel }}</span>
        <span v-if="advancedPanelOpen && coverageScan.summary.user_preference_count">已有个人设置 {{ coverageScan.summary.user_preference_count }}</span>
        <span v-if="advancedPanelOpen">配置状态 {{ overallStatusLabel(coverageScan.summary.overall_status) }}</span>
        <span v-if="advancedPanelOpen">需处理 {{ coverageIssueRows.length }}</span>
        <span v-for="item in advancedPanelOpen ? remediationSummaryItems : []" :key="item.code">
          {{ item.label }} {{ item.count }}
        </span>
      </div>
      <div class="config-workspace" data-lowcode-workbench-ia="three-column">
        <aside class="page-picker-panel" aria-label="业务页面列表">
          <div class="page-picker-head">
            <div>
              <span>业务页面目录</span>
              <strong>{{ visibleCoverageRows.length }} 个匹配页面</strong>
            </div>
            <em>{{ selectedCoverageRow?.name || selectedPageLabel || '未选择' }}</em>
          </div>
          <div v-if="visibleCoverageRows.length" class="scan-list">
            <div
              v-for="row in visibleCoverageRows"
              :key="coverageRowKey(row)"
              class="scan-row"
              :class="{ 'scan-row--selected': coverageRowMatchesScope(row), 'scan-row--clickable': !coverageRowMatchesScope(row) }"
              role="button"
              tabindex="0"
              @click="focusScanRow(row)"
              @keydown.enter.prevent="focusScanRow(row)"
              @keydown.space.prevent="focusScanRow(row)"
            >
              <div class="scan-row-main">
                <strong :title="row.name || row.model">{{ row.name || row.model }}</strong>
                <span v-if="advancedPanelOpen">{{ row.model }}</span>
              </div>
              <div class="scan-row-meta">
                <span>{{ pageViewModeText(row) }}</span>
                <span>{{ rowCoverageProgressText(row) }}</span>
                <span v-if="rowActionHintText(row)">{{ rowActionHintText(row) }}</span>
                <span>{{ pageDesignStatus(row) }}</span>
                <span v-if="advancedPanelOpen && row.user_preference_count">已有个人设置 {{ row.user_preference_count }}</span>
                <span v-if="advancedPanelOpen">{{ runtimeEvidenceText(row) }}</span>
                <span v-if="advancedPanelOpen && runtimeReasonText(row)">原因 {{ runtimeReasonText(row) }}</span>
              </div>
              <div v-if="advancedPanelOpen" class="scan-row-admin-actions">
                <span>{{ severityLabel(row.severity) }}</span>
                <span v-if="row.missing_view_types.length">需补 {{ row.missing_view_types.map(viewTypeLabel).join('、') }}</span>
                <span v-if="row.runtime_missing_view_types.length">运行时未命中 {{ row.runtime_missing_view_types.map(viewTypeLabel).join('、') }}</span>
              </div>
              <div class="scan-row-actions">
                <button
                  v-for="action in advancedPanelOpen ? visibleRowRemediationActions(row) : []"
                  :key="`row-remediation-${coverageRowKey(row)}-${action.code}`"
                  type="button"
                  class="ghost small"
                  :disabled="listSearchSaving || versionsLoading"
                  @click.stop="runRemediationAction(row, action)"
                >
                  {{ action.label }}
                </button>
                <span v-if="coverageRowMatchesScope(row)" class="scan-row-current">当前配置</span>
                <button v-else type="button" class="ghost small" @click.stop="focusScanRow(row)">选择</button>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">当前没有匹配的业务页面，可调整搜索条件或取消“只看需处理”。</div>
        </aside>

        <section v-if="(!loading || surface) && (currentModel || visibleConfigSections.length)" class="page-config-panel" aria-label="已选页面配置">
          <div class="selected-page-overview">
            <div>
              <span>正在配置</span>
              <strong>{{ selectedCoverageRow?.name || selectedPageLabel || currentModel || '当前页面' }}</strong>
            </div>
            <div class="selected-page-overview-side">
              <div class="selected-page-overview-meta">
                <span>{{ selectedCoverageRow ? pageViewModeText(selectedCoverageRow) : '页面配置' }}</span>
                <span v-if="selectedCoverageRow">{{ rowCoverageProgressText(selectedCoverageRow) }}</span>
                <span v-if="selectedCoverageRow">{{ pageDesignStatus(selectedCoverageRow) }}</span>
              </div>
              <button
                type="button"
                class="ghost small"
                :disabled="!previewRouteTarget.path"
                @click="previewSelectedRuntimeRoute"
              >
                预览页面
              </button>
            </div>
          </div>
          <div class="section-grid" data-lowcode-config-task-grid="v1">
            <article v-for="section in visibleConfigSections" :key="section.key" class="config-card" data-lowcode-config-task-card="v1">
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
                  @click="loadVersions(section.key)"
                >
                  {{ versionsLoading ? '读取中...' : '版本记录' }}
                </button>
                <button
                  v-if="section.key === 'list_search'"
                  type="button"
                  class="ghost small"
                  :disabled="!currentModel || listSearchBusy"
                  @click="loadListSearchConfig"
                >
                  {{ listSearchBusy ? '读取中...' : sectionPrimaryActionLabel(section.key) }}
                </button>
                <button
                  v-else-if="section.key === 'form'"
                  type="button"
                  class="ghost small primary"
                  :disabled="!canOpenDesigner"
                  @click="openFormConfig"
                >
                  {{ sectionPrimaryActionLabel(section.key) }}
                </button>
                <button
                  v-else-if="section.key === 'menu'"
                  type="button"
                  class="ghost small"
                  @click="openMenuConfig"
                >
                  {{ sectionPrimaryActionLabel(section.key) }}
                </button>
                <button
                  v-if="section.key === 'menu'"
                  type="button"
                  class="ghost small"
                  @click="openCreateMenuConfig"
                >
                  新增菜单
                </button>
                <button
                  v-else-if="section.key === 'analysis'"
                  type="button"
                  class="ghost small"
                  :disabled="!currentModel || listSearchBusy"
                  @click="loadAnalysisConfig"
                >
                  {{ listSearchBusy ? '读取中...' : sectionPrimaryActionLabel(section.key) }}
                </button>
                <button
                  v-else-if="section.key === 'approval'"
                  type="button"
                  class="ghost small primary"
                  :disabled="!currentModel || approvalLoading"
                  @click="loadApprovalConfig"
                >
                  {{ approvalLoading ? '读取中...' : sectionPrimaryActionLabel(section.key) }}
                </button>
                <button
                  v-if="section.key === 'approval' && section.route?.path"
                  type="button"
                  class="ghost small"
                  @click="openApprovalConfig(section)"
                >
                  更多规则
                </button>
              </div>
            </article>
          </div>
        </section>
        <aside v-if="surface" class="workbench-status-rail" aria-label="交付状态" data-lowcode-delivery-readiness="low_code_delivery_readiness.v1">
          <div class="delivery-readiness-head">
            <div>
              <span>交付状态</span>
              <strong>{{ deliveryReadinessStatusText }}</strong>
            </div>
            <em>{{ visibleDeliveryReadinessProgressText }}</em>
          </div>
          <div class="delivery-readiness-grid delivery-readiness-grid--rail">
            <button
              v-for="item in visibleDeliveryReadinessItems"
              :key="`rail-${item.id}`"
              type="button"
              class="delivery-readiness-item"
              :class="{ 'delivery-readiness-item--pending': item.status !== 'ready' }"
              @click="runDeliveryReadinessAction(item)"
            >
              <span>{{ item.label }}</span>
              <strong>{{ deliveryReadinessItemStatusText(item) }}</strong>
              <em>{{ deliveryReadinessItemMetaText(item) }}</em>
            </button>
          </div>
          <div v-if="!visibleDeliveryReadinessItems.length" class="workbench-status-empty">状态读取中</div>
          <div v-if="snapshotSummary" class="workbench-status-snapshot">
            <span>配置快照</span>
            <strong>{{ snapshotSummary.contract_count }}</strong>
            <em>已发布 {{ snapshotSummary.status_counts?.published || 0 }}</em>
          </div>
        </aside>
      </div>
    </section>
    <section v-if="advancedPanelOpen && coverageScan" class="scan-panel scan-panel--admin">
      <div class="scan-toolbar">
        <strong>配置检查明细</strong>
        <span v-if="snapshotSummary">{{ snapshotSummaryText }}</span>
      </div>
      <div class="scan-list">
        <div v-for="row in visibleCoverageRows" :key="`admin-${coverageRowKey(row)}`" class="scan-row">
          <strong>{{ row.name || row.model }}</strong>
          <span>{{ severityLabel(row.severity) }}</span>
          <span>{{ row.model }}</span>
          <span>{{ row.view_mode || '-' }}</span>
          <span>菜单 {{ row.menu_count }}</span>
          <span v-if="row.user_preference_count">个人设置 {{ row.user_preference_count }} · {{ boundaryLabel(row.user_preference_boundary) }}</span>
          <span v-if="row.missing_view_types.length">需补 {{ row.missing_view_types.map(viewTypeLabel).join('、') }}</span>
          <span v-else>配置完整</span>
          <span v-if="row.runtime_missing_view_types.length">运行时未命中 {{ row.runtime_missing_view_types.map(viewTypeLabel).join('、') }}</span>
          <span v-else>运行时完整</span>
          <span>{{ runtimeEvidenceText(row) }}</span>
          <span v-if="runtimeReasonText(row)">原因 {{ runtimeReasonText(row) }}</span>
          <button
            v-for="action in row.remediation_actions"
            :key="`admin-${coverageRowKey(row)}-${action.code}`"
            type="button"
            class="link-button"
            @click="runRemediationAction(row, action)"
          >
            {{ action.label }}
          </button>
          <button
            type="button"
            class="link-button"
            :disabled="!row.runtime_route?.path"
            @click="openRuntimeRoute(row)"
          >
            预览页面
          </button>
          <button type="button" class="link-button" @click="focusScanRow(row)">选择此页面</button>
        </div>
      </div>
    </section>
    <section v-if="advancedPanelOpen" class="scan-panel snapshot-compare-panel">
      <div class="scan-toolbar">
        <strong>跨环境快照对比</strong>
        <span v-if="snapshotCompareResult">{{ snapshotCompareSummary }}</span>
        <button type="button" class="ghost small" :disabled="snapshotExportLoading" @click="downloadSnapshot">
          {{ snapshotExportLoading ? '导出中...' : '下载当前快照' }}
        </button>
        <button type="button" class="ghost small" :disabled="snapshotCompareLoading || !snapshotCompareText.trim()" @click="compareSnapshot">
          {{ snapshotCompareLoading ? '对比中...' : '对比快照' }}
        </button>
        <button type="button" class="ghost small" :disabled="!snapshotCompareResult" @click="downloadSnapshotRemediationPlan">
          下载整改清单
        </button>
      </div>
      <textarea
        v-model="snapshotCompareText"
        class="snapshot-input"
        rows="5"
        placeholder="粘贴 make verify.business_config.snapshot 导出的 JSON"
      ></textarea>
      <div v-if="snapshotCompareResult" class="snapshot-remediation-summary">
        <span>{{ snapshotRemediationSummary }}</span>
      </div>
      <div v-if="snapshotCompareResult" class="snapshot-diff-list">
        <div v-for="item in snapshotCompareChangedRows" :key="item.key" class="snapshot-diff-row">
          <strong>{{ item.name || item.model }}</strong>
          <span>{{ viewTypeLabel(item.view_type) }}</span>
          <span>版本 {{ item.previous_version_no }} -> {{ item.current_version_no }}</span>
          <span>{{ item.previous_status || '-' }} -> {{ item.current_status || '-' }}</span>
        </div>
        <div v-for="item in snapshotCompareAddedRows" :key="`added-${item.model}-${item.view_type}-${item.action_id}-${item.name}`" class="snapshot-diff-row">
          <strong>{{ item.name || item.model }}</strong>
          <span>新增</span>
          <span>{{ viewTypeLabel(item.view_type) }}</span>
          <span>版本 {{ item.version_no }}</span>
        </div>
        <div v-for="item in snapshotCompareRemovedRows" :key="`removed-${item.model}-${item.view_type}-${item.action_id}-${item.name}`" class="snapshot-diff-row">
          <strong>{{ item.name || item.model }}</strong>
          <span>移除</span>
          <span>{{ viewTypeLabel(item.view_type) }}</span>
          <span>版本 {{ item.version_no }}</span>
        </div>
      </div>
    </section>
    <section v-if="approvalPanelOpen" class="edit-panel config-editor-panel approval-panel">
      <div class="edit-panel-head">
        <div>
          <h2>审批规则</h2>
          <p>{{ approvalPolicyLabel }}</p>
        </div>
        <button type="button" class="ghost small" :disabled="approvalLoading" @click="approvalPanelOpen = false">
          关闭
        </button>
      </div>
      <aside class="approval-rule-panel" aria-label="审批规则设置">
        <div class="approval-guide">
          <strong>审批配置怎么生效</strong>
          <span>{{ approvalEffectGuideText }}</span>
        </div>
        <div class="approval-rule-head">
          <strong>规则开关</strong>
          <span>{{ approvalRuntimeText }}</span>
        </div>
        <div class="approval-config-grid">
          <label class="approval-toggle">
            <input v-model="approvalForm.approval_required" type="checkbox" @change="onApprovalRequiredChange" />
            <span>启用审批</span>
          </label>
          <label>
            <span>审批方式</span>
            <select v-model="approvalForm.mode" :disabled="!approvalForm.approval_required">
              <option
                v-for="option in approvalModeOptions"
                :key="option.value"
                :value="option.value"
                :disabled="approvalForm.approval_required && option.value === 'none'"
              >
                {{ option.label }}
              </option>
            </select>
          </label>
          <label>
            <span>默认审批岗位</span>
            <select v-model="approvalForm.manager_scope_key" :disabled="!approvalForm.approval_required">
              <option value="">暂不指定</option>
              <option v-for="option in approvalScopeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
        </div>
        <div class="edit-meta approval-rule-summary">
          <span>当前步骤：{{ activeApprovalStepCount }} 个</span>
          <span>保存状态：{{ hasApprovalDraftChanges ? '有未保存调整' : '已同步' }}</span>
          <span v-if="advancedPanelOpen">生效来源：{{ boundaryLabel(approvalAudit?.boundary || 'industry_policy_runtime') }}</span>
          <span v-if="hasApprovalDraftChanges" class="edit-dirty">配置已调整，可保存</span>
        </div>
        <div class="approval-impact-summary">
          <strong>{{ hasApprovalDraftChanges ? '本次调整' : '当前规则' }}</strong>
          <span>{{ approvalImpactSummaryText }}</span>
        </div>
      </aside>
      <section class="approval-steps" :class="{ 'approval-steps--disabled': !approvalForm.approval_required }">
        <header>
          <div>
            <strong>审批步骤编排</strong>
            <span>{{ approvalForm.approval_required ? `${activeApprovalStepCount} 个启用步骤，拖动整行调整顺序` : '启用审批后配置办理节点' }}</span>
          </div>
          <button type="button" class="ghost small" :disabled="approvalLoading || !approvalForm.approval_required" @click="addApprovalStep">
            添加步骤
          </button>
        </header>
        <div v-if="approvalSteps.length" class="approval-step-table" role="table" aria-label="审批步骤">
          <div class="approval-step-table-head" role="row">
            <span>序号</span>
            <span>步骤名称</span>
            <span>审批岗位</span>
            <span>金额下限</span>
            <span>金额上限</span>
            <span>操作</span>
          </div>
          <div
            v-for="(step, index) in approvalSteps"
            :key="step.key"
            class="approval-step-row"
            :class="{
              'approval-step-row--dragging': approvalStepDragIndex === index,
              'approval-step-row--drop-target': approvalStepDropIndex === index && approvalStepDragIndex !== index,
            }"
            role="row"
            :draggable="approvalForm.approval_required"
            :aria-label="`拖动第${index + 1}步调整顺序`"
            @dragstart="startApprovalStepDrag(index, $event)"
            @dragover.prevent
            @dragenter.prevent="approvalStepDropIndex = index"
            @drop.prevent="dropApprovalStep(index)"
            @dragend="clearApprovalStepDrag"
          >
            <span class="approval-step-seq">{{ index + 1 }}</span>
            <div class="approval-step-cell">
              <input v-model="step.name" type="text" placeholder="例如：合同中心审核" :disabled="!approvalForm.approval_required" :aria-label="`第${index + 1}步名称`" />
            </div>
            <div class="approval-step-cell">
              <select v-model="step.approval_scope_key" :disabled="!approvalForm.approval_required" :aria-label="`第${index + 1}步审批岗位`">
                <option value="">请选择</option>
                <option v-for="option in approvalScopeOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
            <div class="approval-step-cell">
              <input v-model="step.amount_min" type="number" min="0" step="0.01" placeholder="不限制" :disabled="!approvalForm.approval_required" :aria-label="`第${index + 1}步金额下限`" />
            </div>
            <div class="approval-step-cell">
              <input v-model="step.amount_max" type="number" min="0" step="0.01" placeholder="不限制" :disabled="!approvalForm.approval_required" :aria-label="`第${index + 1}步金额上限`" />
            </div>
            <div class="approval-step-actions">
              <button type="button" title="移除" :disabled="approvalLoading || !approvalForm.approval_required" @click="removeApprovalStep(index)">×</button>
            </div>
          </div>
        </div>
        <div v-else class="approval-step-empty">
          当前没有审批步骤，启用审批后可添加办理节点。
          <button type="button" class="ghost small" :disabled="approvalLoading" @click="enableApprovalWithDefaultStep">启用并添加步骤</button>
        </div>
        <div v-if="approvalValidationMessage" class="approval-validation">{{ approvalValidationMessage }}</div>
      </section>
      <div class="edit-panel-actions">
        <button type="button" class="ghost small primary" :disabled="approvalLoading || !canSaveApprovalDraft" @click="saveApprovalConfig">
          {{ approvalLoading ? '保存中...' : '保存审批设置' }}
        </button>
        <button type="button" class="ghost small" :disabled="approvalLoading || !hasApprovalDraftChanges" @click="resetApprovalDraft">
          还原
        </button>
        <button type="button" class="ghost small" :disabled="!approvalSection?.route?.path" @click="approvalSection && openApprovalConfig(approvalSection)">
          更多规则
        </button>
      </div>
    </section>

    <section v-if="versionsPanelOpen" class="version-panel">
      <div class="edit-panel-head">
        <div>
          <h2>{{ versionTitle }}</h2>
          <p>{{ versionPanelDescription }}</p>
        </div>
        <button type="button" class="ghost small" :disabled="versionsLoading" @click="versionsPanelOpen = false">
          关闭
        </button>
      </div>
      <div class="version-guide">
        <strong>{{ versionPanelGuide.title }}</strong>
        <span>{{ versionPanelGuide.body }}</span>
      </div>
      <div v-if="!versionContracts.length" class="empty-state">{{ versionEmptyText }}</div>
      <div v-else class="version-list">
        <article v-for="contract in versionContracts" :key="contract.id" class="version-card">
          <div class="version-card-head">
            <div class="version-card-title">
              <strong>{{ viewTypeLabel(contract.view_type) }}</strong>
              <span>{{ versionContractDisplayName(contract) }}</span>
              <em>{{ versionContractImpactText(contract) }}</em>
            </div>
            <div class="version-card-actions">
              <span class="version-current-badge">当前生效 v{{ contract.version_no }}</span>
              <button
                type="button"
                class="ghost small"
                :disabled="versionsLoading || listSearchSaving || contract.versions.length < 2"
                @click="rollbackContractFromWorkbench(contract)"
              >
                {{ versionRollbackButtonLabel(contract) }}
              </button>
            </div>
          </div>
          <div class="version-summary">
            <span>表单字段 {{ contract.summary.form_field_count }}</span>
            <span>列表列 {{ contract.summary.list_column_count }}</span>
            <span>筛选 {{ contract.summary.search_filter_count }}</span>
            <span>分组 {{ contract.summary.search_group_by_count }}</span>
            <span v-if="contract.summary.analysis_item_count">分析项 {{ contract.summary.analysis_item_count }}</span>
          </div>
          <div class="version-decision-note">
            <span>{{ versionContractDecisionText(contract) }}</span>
          </div>
          <div v-if="contract.summary.analysis_items?.length" class="analysis-summary-list">
            <span v-for="item in contract.summary.analysis_items.slice(0, 12)" :key="item">{{ analysisItemLabel(item) }}</span>
          </div>
          <div class="version-rows">
            <div
              v-for="version in contract.versions"
              :key="version.id"
              class="version-row"
              :class="{ 'version-row--current': version.version_no === contract.version_no }"
            >
              <span class="version-row-no">v{{ version.version_no }}</span>
              <span>{{ version.version_no === contract.version_no ? '当前生效' : versionStatusLabel(version.status) }}</span>
              <span>保存人 {{ version.created_by || '-' }}</span>
              <span>{{ versionSummaryText(version.summary) }}</span>
              <span class="version-row-delta">{{ versionDeltaText(contract.summary, version.summary, version.version_no === contract.version_no) }}</span>
              <button
                type="button"
                class="link-button"
                :disabled="versionsLoading || listSearchSaving || version.version_no === contract.version_no"
                @click="rollbackContractFromWorkbench(contract, version.version_no)"
              >
                {{ version.version_no === contract.version_no ? '当前版本' : '恢复此版本' }}
              </button>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section v-if="analysisPanelOpen" class="edit-panel config-editor-panel">
      <div class="edit-panel-head">
        <div>
          <h2>分析视图设置</h2>
          <p>选择这个页面默认用于统计分析的指标和维度。</p>
        </div>
        <div class="edit-panel-actions">
          <button type="button" class="ghost small primary" :disabled="listSearchSaving || !previewRouteTarget.path" @click="previewAnalysisConfig">
            {{ hasAnalysisDraftChanges ? (listSearchSaving ? '保存中...' : '保存并预览') : '预览页面' }}
          </button>
          <button type="button" class="ghost small" :disabled="listSearchSaving || !hasAnalysisDraftChanges" @click="saveAnalysisConfig">
            {{ listSearchSaving ? '保存中...' : '保存设置' }}
          </button>
          <button type="button" class="ghost small" :disabled="listSearchSaving || !hasAnalysisDraftChanges" @click="resetAnalysisDraft">
            放弃调整
          </button>
        </div>
      </div>
      <div class="list-search-tabs" role="group" aria-label="分析视图配置类型">
        <button
          v-for="tab in analysisEditorTabs"
          :key="tab.key"
          type="button"
          :class="{ active: activeAnalysisEditor === tab.key }"
          @click="setActiveAnalysisEditor(tab.key)"
        >
          <span>{{ tab.label }}</span>
          <em>{{ analysisEditorCount(tab.key) }}</em>
        </button>
      </div>
      <div class="edit-grid edit-grid--single">
        <section class="field-chip-editor">
          <header>
            <strong>{{ analysisEditorLabel(activeAnalysisEditor) }}</strong>
            <span>{{ analysisEditorCount(activeAnalysisEditor) }} 项</span>
          </header>
          <label v-if="activeAnalysisEditor === 'graphMeasure' || activeAnalysisEditor === 'graphDimension'" class="inline-select">
            图表类型
            <select v-model="graphType">
              <option value="bar">柱状图</option>
              <option value="line">折线图</option>
              <option value="pie">饼图</option>
            </select>
          </label>
          <div class="field-chip-list">
            <span
              v-for="(name, index) in parseNames(analysisEditorState(activeAnalysisEditor).text.value)"
              :key="`analysis-${activeAnalysisEditor}-${name}`"
              class="field-chip"
              :class="{
                'field-chip--dragging': isAnalysisChipDragging(activeAnalysisEditor, name),
                'field-chip--drop-target': isAnalysisChipDropTarget(activeAnalysisEditor, name),
              }"
              :title="fieldHelpText(name)"
              @dragover.prevent="hoverAnalysisChipDrop(activeAnalysisEditor, name)"
              @drop.prevent="dropAnalysisChip(activeAnalysisEditor, name)"
              @dragend="clearChipDrag"
            >
              <span
                class="field-chip-handle"
                draggable="true"
                role="button"
                tabindex="0"
                :aria-label="`拖动${fieldDisplayLabel(name)}调整顺序`"
                @dragstart.stop="startAnalysisChipDrag(activeAnalysisEditor, name, $event)"
                @dragend.stop="clearChipDrag"
              >⋮⋮</span>
              {{ fieldDisplayLabel(name) }}
              <button type="button" title="上移" :disabled="index === 0" @click="moveAnalysisName(activeAnalysisEditor, name, -1)">↑</button>
              <button type="button" title="下移" :disabled="index === parseNames(analysisEditorState(activeAnalysisEditor).text.value).length - 1" @click="moveAnalysisName(activeAnalysisEditor, name, 1)">↓</button>
              <button type="button" title="移除" @click="removeAnalysisName(activeAnalysisEditor, name)">×</button>
            </span>
          </div>
          <input
            v-model="analysisFieldOptionSearch"
            class="field-option-search"
            type="search"
            placeholder="搜索可选字段"
          />
          <div class="field-option-summary">
            <span>可添加字段 {{ analysisFieldOptionCandidates().length }}，当前显示 {{ availableAnalysisFieldOptions.length }}</span>
            <button
              type="button"
              class="link-button"
              :disabled="!availableAnalysisFieldOptions.length"
              @click="addVisibleAnalysisOptions(activeAnalysisEditor)"
            >
              添加当前显示字段
            </button>
          </div>
          <div v-if="availableAnalysisFieldOptions.length" class="field-option-pool">
            <button
              v-for="field in availableAnalysisFieldOptions"
              :key="`analysis-option-${activeAnalysisEditor}-${field.name}`"
              type="button"
              :title="fieldOptionHelpText(field)"
              @click="addAnalysisName(activeAnalysisEditor, field.name)"
            >
              {{ fieldOptionLabel(field) }}
            </button>
          </div>
          <form v-if="advancedPanelOpen" class="field-chip-add" @submit.prevent="addAnalysisName(activeAnalysisEditor)">
            <input
              :value="analysisEditorState(activeAnalysisEditor).draft.value"
              type="text"
              placeholder="输入字段名"
              @input="setAnalysisDraftFromEvent(activeAnalysisEditor, $event)"
            />
            <button type="submit" class="ghost small">添加</button>
          </form>
        </section>
      </div>
      <div class="edit-meta">
        <span v-if="hasAnalysisDraftChanges" class="edit-dirty">配置已调整，可保存并预览效果</span>
        <span v-if="advancedPanelOpen">生效来源：{{ boundaryLabel(analysisAudit?.business_config_boundary || 'business_contract') }}</span>
      </div>
    </section>

    <section v-if="listSearchPanelOpen" class="edit-panel config-editor-panel">
      <div class="edit-panel-head">
        <div>
          <h2>列表与搜索设置</h2>
          <p>{{ listSearchPanelDescription }}</p>
        </div>
        <div class="edit-panel-actions">
          <button type="button" class="ghost small primary" :disabled="listSearchSaving || !previewRouteTarget.path" @click="previewListSearchConfig">
            {{ hasListSearchDraftChanges ? (listSearchSaving ? '保存中...' : '保存并预览') : '预览页面' }}
          </button>
          <button type="button" class="ghost small" :disabled="listSearchSaving || !hasListSearchDraftChanges" @click="saveListSearchConfig">
            {{ listSearchSaving ? '保存中...' : '保存设置' }}
          </button>
          <button type="button" class="ghost small" :disabled="listSearchSaving || !hasListSearchDraftChanges" @click="resetListSearchDraft">
            放弃调整
          </button>
        </div>
      </div>
      <div class="list-search-tabs" role="group" aria-label="列表搜索配置类型">
        <button
          v-for="tab in listSearchEditorTabs"
          :key="tab.key"
          type="button"
          :class="{ active: activeListSearchEditor === tab.key }"
          @click="setActiveListSearchEditor(tab.key)"
        >
          <span>{{ tab.label }}</span>
          <em>{{ listSearchEditorCount(tab.key) }}</em>
        </button>
      </div>
      <div class="edit-grid edit-grid--single">
        <section v-if="activeListSearchEditor === 'list'" class="field-chip-editor">
          <header>
            <strong>默认列表列</strong>
            <span>{{ parseNames(listColumnsText).length }} 项</span>
          </header>
          <div class="field-chip-list">
            <span
              v-for="(name, index) in parseNames(listColumnsText)"
              :key="`list-${name}`"
              class="field-chip"
              :class="{
                'field-chip--dragging': isListSearchChipDragging('list', name),
                'field-chip--drop-target': isListSearchChipDropTarget('list', name),
              }"
              :title="fieldHelpText(name)"
              @dragover.prevent="hoverListSearchChipDrop('list', name)"
              @drop.prevent="dropListSearchChip('list', name)"
              @dragend="clearChipDrag"
            >
              <span
                class="field-chip-handle"
                draggable="true"
                role="button"
                tabindex="0"
                :aria-label="`拖动${fieldDisplayLabel(name)}调整顺序`"
                @dragstart.stop="startListSearchChipDrag('list', name, $event)"
                @dragend.stop="clearChipDrag"
              >⋮⋮</span>
              {{ fieldDisplayLabel(name) }}
              <button type="button" title="上移" :disabled="index === 0" @click="moveListSearchName('list', name, -1)">↑</button>
              <button type="button" title="下移" :disabled="index === parseNames(listColumnsText).length - 1" @click="moveListSearchName('list', name, 1)">↓</button>
              <button type="button" title="移除" @click="removeListSearchName('list', name)">×</button>
            </span>
          </div>
          <form v-if="advancedPanelOpen" class="field-chip-add" @submit.prevent="addListSearchName('list')">
            <input v-model="listColumnDraft" type="text" placeholder="输入字段名" />
            <button type="submit" class="ghost small">添加</button>
          </form>
          <input
            v-if="availableListFieldOptions.length || listFieldOptionSearch"
            v-model="listFieldOptionSearch"
            class="field-option-search"
            type="search"
            placeholder="搜索可选字段"
          />
          <div class="field-option-summary">
            <span>可添加字段 {{ fieldOptionAvailableCount('list') }}，当前显示 {{ availableListFieldOptions.length }}</span>
            <button
              type="button"
              class="link-button"
              :disabled="!availableListFieldOptions.length"
              @click="addVisibleListSearchOptions('list')"
            >
              添加当前显示字段
            </button>
          </div>
          <div v-if="availableListFieldOptions.length" class="field-option-pool">
            <button
              v-for="field in availableListFieldOptions"
              :key="`list-option-${field.name}`"
              type="button"
              :title="fieldOptionHelpText(field)"
              @click="addListSearchName('list', field.name)"
            >
              {{ fieldOptionLabel(field) }}
            </button>
          </div>
        </section>
        <section v-if="activeListSearchEditor === 'filter'" class="field-chip-editor">
          <header>
            <strong>搜索筛选字段</strong>
            <span>{{ parseNames(searchFiltersText).length }} 项</span>
          </header>
          <div class="field-chip-list">
            <span
              v-for="(name, index) in parseNames(searchFiltersText)"
              :key="`filter-${name}`"
              class="field-chip"
              :class="{
                'field-chip--dragging': isListSearchChipDragging('filter', name),
                'field-chip--drop-target': isListSearchChipDropTarget('filter', name),
              }"
              :title="fieldHelpText(name)"
              @dragover.prevent="hoverListSearchChipDrop('filter', name)"
              @drop.prevent="dropListSearchChip('filter', name)"
              @dragend="clearChipDrag"
            >
              <span
                class="field-chip-handle"
                draggable="true"
                role="button"
                tabindex="0"
                :aria-label="`拖动${fieldDisplayLabel(name)}调整顺序`"
                @dragstart.stop="startListSearchChipDrag('filter', name, $event)"
                @dragend.stop="clearChipDrag"
              >⋮⋮</span>
              {{ fieldDisplayLabel(name) }}
              <button type="button" title="上移" :disabled="index === 0" @click="moveListSearchName('filter', name, -1)">↑</button>
              <button type="button" title="下移" :disabled="index === parseNames(searchFiltersText).length - 1" @click="moveListSearchName('filter', name, 1)">↓</button>
              <button type="button" title="移除" @click="removeListSearchName('filter', name)">×</button>
            </span>
          </div>
          <form v-if="advancedPanelOpen" class="field-chip-add" @submit.prevent="addListSearchName('filter')">
            <input v-model="searchFilterDraft" type="text" placeholder="输入字段名" />
            <button type="submit" class="ghost small">添加</button>
          </form>
          <input
            v-if="availableFilterFieldOptions.length || filterFieldOptionSearch"
            v-model="filterFieldOptionSearch"
            class="field-option-search"
            type="search"
            placeholder="搜索可选字段"
          />
          <div class="field-option-summary">
            <span>可添加字段 {{ fieldOptionAvailableCount('filter') }}，当前显示 {{ availableFilterFieldOptions.length }}</span>
            <button
              type="button"
              class="link-button"
              :disabled="!availableFilterFieldOptions.length"
              @click="addVisibleListSearchOptions('filter')"
            >
              添加当前显示字段
            </button>
          </div>
          <div v-if="availableFilterFieldOptions.length" class="field-option-pool">
            <button
              v-for="field in availableFilterFieldOptions"
              :key="`filter-option-${field.name}`"
              type="button"
              :title="fieldOptionHelpText(field)"
              @click="addListSearchName('filter', field.name)"
            >
              {{ fieldOptionLabel(field) }}
            </button>
          </div>
        </section>
        <section v-if="activeListSearchEditor === 'group'" class="field-chip-editor">
          <header>
            <strong>搜索分组字段</strong>
            <span>{{ parseNames(searchGroupByText).length }} 项</span>
          </header>
          <div class="field-chip-list">
            <span
              v-for="(name, index) in parseNames(searchGroupByText)"
              :key="`group-${name}`"
              class="field-chip"
              :class="{
                'field-chip--dragging': isListSearchChipDragging('group', name),
                'field-chip--drop-target': isListSearchChipDropTarget('group', name),
              }"
              :title="fieldHelpText(name)"
              @dragover.prevent="hoverListSearchChipDrop('group', name)"
              @drop.prevent="dropListSearchChip('group', name)"
              @dragend="clearChipDrag"
            >
              <span
                class="field-chip-handle"
                draggable="true"
                role="button"
                tabindex="0"
                :aria-label="`拖动${fieldDisplayLabel(name)}调整顺序`"
                @dragstart.stop="startListSearchChipDrag('group', name, $event)"
                @dragend.stop="clearChipDrag"
              >⋮⋮</span>
              {{ fieldDisplayLabel(name) }}
              <button type="button" title="上移" :disabled="index === 0" @click="moveListSearchName('group', name, -1)">↑</button>
              <button type="button" title="下移" :disabled="index === parseNames(searchGroupByText).length - 1" @click="moveListSearchName('group', name, 1)">↓</button>
              <button type="button" title="移除" @click="removeListSearchName('group', name)">×</button>
            </span>
          </div>
          <form v-if="advancedPanelOpen" class="field-chip-add" @submit.prevent="addListSearchName('group')">
            <input v-model="searchGroupDraft" type="text" placeholder="输入字段名" />
            <button type="submit" class="ghost small">添加</button>
          </form>
          <input
            v-if="availableGroupFieldOptions.length || groupFieldOptionSearch"
            v-model="groupFieldOptionSearch"
            class="field-option-search"
            type="search"
            placeholder="搜索可选字段"
          />
          <div class="field-option-summary">
            <span>可添加字段 {{ fieldOptionAvailableCount('group') }}，当前显示 {{ availableGroupFieldOptions.length }}</span>
            <button
              type="button"
              class="link-button"
              :disabled="!availableGroupFieldOptions.length"
              @click="addVisibleListSearchOptions('group')"
            >
              添加当前显示字段
            </button>
          </div>
          <div v-if="availableGroupFieldOptions.length" class="field-option-pool">
            <button
              v-for="field in availableGroupFieldOptions"
              :key="`group-option-${field.name}`"
              type="button"
              :title="fieldOptionHelpText(field)"
              @click="addListSearchName('group', field.name)"
            >
              {{ fieldOptionLabel(field) }}
            </button>
          </div>
        </section>
      </div>
      <div class="edit-meta">
        <span v-if="hasListSearchDraftChanges" class="edit-dirty">配置已调整，可保存并预览效果</span>
        <span v-if="advancedPanelOpen">个人设置记录：{{ listSearchAudit?.user_preference_count ?? 0 }}</span>
        <span v-if="advancedPanelOpen">生效来源：{{ boundaryLabel(listSearchAudit?.user_preference_boundary || 'ui_only') }}</span>
      </div>
      <div v-if="advancedPanelOpen && listSearchAudit?.user_preferences?.length" class="preference-list">
        <span
          v-for="item in listSearchAudit.user_preferences.slice(0, 6)"
          :key="item.id || item.scope_key"
        >
          {{ item.user_name || '用户' }} · {{ item.view_type || 'list' }} · {{ item.column_count }}列
        </span>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  auditBusinessAnalysisConfig,
  auditBusinessListSearchConfig,
  bootstrapBusinessAnalysisConfig,
  bootstrapBusinessFormConfig,
  bootstrapBusinessListSearchConfig,
  bootstrapCoverageMissingConfig,
  compareBusinessConfigSnapshot,
  exportBusinessConfigSnapshot,
  loadApprovalPolicyConfig,
  loadBusinessConfigContractVersions,
  loadBusinessConfigSurface,
  rollbackBusinessConfigContract,
  saveApprovalPolicyConfig,
  saveApprovalPolicySteps,
  saveBusinessAnalysisConfig,
  saveBusinessListSearchConfig,
  scanBusinessConfigCoverage,
  type ApprovalPolicyConfigPayload,
  type BusinessConfigAnalysisAuditPayload,
  type BusinessConfigContractVersionsPayload,
  type BusinessConfigCoverageScanItem,
  type BusinessConfigCoverageScanPayload,
  type BusinessConfigListSearchAuditPayload,
  type BusinessConfigRemediationAction,
  type BusinessConfigSnapshotComparePayload,
  type BusinessConfigSnapshotSummaryPayload,
  type BusinessConfigSurfacePayload,
} from '../api/businessConfig';
import {
  BUSINESS_CONFIG_INTENTS,
  BUSINESS_CONFIG_MODES,
  BUSINESS_CONFIG_MODELS,
  BUSINESS_CONFIG_ROUTE_FLAGS,
  isBusinessConfigRuntimeModel,
} from '../app/businessConfigBoundaries';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import { useSessionStore } from '../stores/session';

const SURFACE_LOAD_TIMEOUT_MS = 20000;
const ACTIVE_EDITOR_SCROLL_OPTIONS: ScrollIntoViewOptions = { block: 'start', behavior: 'auto' };
const CORE_DELIVERY_READINESS_SECTIONS = new Set(['form', 'list_search', 'menu', 'approval']);

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const pageContract = usePageContract('business_config');
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;

async function focusActiveEditorPanel() {
  await nextTick();
  const panel = document.querySelector<HTMLElement>('.config-editor-panel');
  panel?.scrollIntoView(ACTIVE_EDITOR_SCROLL_OPTIONS);
}
const pageSectionsReady = computed(() => (
  pageSectionEnabled('root', true)
  && pageSectionEnabled('header', true)
  && pageSectionEnabled('coverage', true)
  && pageSectionEnabled('designer', true)
  && pageSectionTagIs('root', 'section')
  && pageSectionTagIs('header', 'header')
  && pageSectionTagIs('coverage', 'section')
  && pageSectionTagIs('designer', 'section')
));
const pageSectionsFingerprint = computed(() => JSON.stringify([
  pageSectionStyle('header'),
  pageSectionStyle('coverage'),
  pageSectionStyle('designer'),
]));

async function executeGlobalPageAction(actionKey: string) {
  await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: route.query,
    onRefresh: loadSurface,
  });
}

const loading = ref(false);
const scanLoading = ref(false);
const listSearchBusy = ref(false);
const listSearchSaving = ref(false);
const approvalLoading = ref(false);
const error = ref('');
const message = ref({ text: '', detail: '' });
const surface = ref<BusinessConfigSurfacePayload | null>(null);
const coverageScan = ref<BusinessConfigCoverageScanPayload | null>(null);
const showOnlyIssues = ref(false);
const pageSearch = ref('');
const pageTypeFilter = ref<'all' | 'form' | 'list' | 'analysis'>('all');
const listSearchAudit = ref<BusinessConfigListSearchAuditPayload | null>(null);
const analysisAudit = ref<BusinessConfigAnalysisAuditPayload | null>(null);
const approvalAudit = ref<ApprovalPolicyConfigPayload | null>(null);
const listSearchPanelOpen = ref(false);
const analysisPanelOpen = ref(false);
const approvalPanelOpen = ref(false);
const selectedRuntimeRoute = ref<BusinessConfigCoverageScanItem['runtime_route'] | null>(null);
const versionsLoading = ref(false);
const versionsPanelOpen = ref(false);
const advancedPanelOpen = ref(false);
const versionTitle = ref('配置版本');
const activeVersionSection = ref<'form' | 'list_search' | 'analysis' | ''>('');
const versionContracts = ref<BusinessConfigContractVersionsPayload['contracts']>([]);
const snapshotCompareText = ref('');
const snapshotCompareLoading = ref(false);
const snapshotExportLoading = ref(false);
const snapshotCompareResult = ref<BusinessConfigSnapshotComparePayload | null>(null);
const listColumnsText = ref('');
const searchFiltersText = ref('');
const searchGroupByText = ref('');
const pivotMeasuresText = ref('');
const pivotDimensionsText = ref('');
const graphMeasuresText = ref('');
const graphDimensionsText = ref('');
const graphType = ref('bar');
const listSearchBase = ref({ list: '', filter: '', group: '' });
const analysisBase = ref({ pivotMeasures: '', pivotDimensions: '', graphMeasures: '', graphDimensions: '', graphType: 'bar' });
const approvalForm = ref({ approval_required: false, mode: 'none', manager_scope_key: '' });
const approvalBase = ref({ approval_required: false, mode: 'none', manager_scope_key: '' });
type ApprovalStepDraft = {
  key: string;
  id: number;
  name: string;
  approval_scope_key: string;
  active: boolean;
  amount_min: string;
  amount_max: string;
  condition_note: string;
  note: string;
};
const approvalSteps = ref<ApprovalStepDraft[]>([]);
const approvalStepsBaseJson = ref('[]');
const approvalStepDragIndex = ref<number | null>(null);
const approvalStepDropIndex = ref<number | null>(null);
let approvalStepTempId = 0;
let surfaceLoadSeq = 0;
const listColumnDraft = ref('');
const searchFilterDraft = ref('');
const searchGroupDraft = ref('');
const pivotMeasureDraft = ref('');
const pivotDimensionDraft = ref('');
const graphMeasureDraft = ref('');
const graphDimensionDraft = ref('');
type ListSearchEditorKind = 'list' | 'filter' | 'group';
type AnalysisEditorKind = 'pivotMeasure' | 'pivotDimension' | 'graphMeasure' | 'graphDimension';
const activeListSearchEditor = ref<ListSearchEditorKind>('list');
const activeAnalysisEditor = ref<AnalysisEditorKind>('pivotMeasure');
const chipDrag = ref<{
  area: 'list_search' | 'analysis';
  kind: ListSearchEditorKind | AnalysisEditorKind;
  name: string;
} | null>(null);
const chipDropTarget = ref<{
  area: 'list_search' | 'analysis';
  kind: ListSearchEditorKind | AnalysisEditorKind;
  name: string;
} | null>(null);
const listFieldOptionSearch = ref('');
const filterFieldOptionSearch = ref('');
const groupFieldOptionSearch = ref('');
const analysisFieldOptionSearch = ref('');
const scopeModel = ref(String(route.query.model || '').trim());
const scopeActionId = ref(numericQuery('action_id') || 0);
const scopeViewId = ref(numericQuery('view_id') || 0);
const scopeRoleKey = ref(String(route.query.role_key || '').trim());
const selectedPageLabel = ref(String(route.query.page_label || '').trim());
const rootMenuXmlid = computed(() => String(route.query.root_menu_xmlid || '').trim());
const shouldOpenPageList = computed(() => String(route.query[BUSINESS_CONFIG_ROUTE_FLAGS.openPages] || '').trim() === '1');
const shouldOpenListSearch = computed(() => String(route.query.open_list_search || '').trim() === '1');
const shouldOpenAnalysis = computed(() => String(route.query.open_analysis || '').trim() === '1');
const shouldOpenFormConfig = computed(() => String(route.query.open_form_config || '').trim() === '1');
const requestedListSearchTab = computed<ListSearchEditorKind>(() => {
  const value = String(route.query.list_search_tab || '').trim();
  return value === 'filter' || value === 'group' ? value : 'list';
});
const requestedAnalysisTab = computed<AnalysisEditorKind>(() => {
  const value = String(route.query.analysis_tab || '').trim();
  if (value === 'pivotDimension' || value === 'graphMeasure' || value === 'graphDimension') return value;
  return 'pivotMeasure';
});
const designerTitle = computed(() => {
  const model = currentModel.value || scopeModel.value.trim();
  const pageLabel = selectedPageLabel.value.trim();
  if (pageLabel) return `正在配置：${pageLabel}`;
  return model ? `正在配置：${model}` : '选择一个业务页面开始配置';
});

const sections = computed(() => surface.value?.sections || []);
const visibleSections = computed(() => sections.value.filter((section) => {
  if (advancedPanelOpen.value) return true;
  return section.key === 'form'
    || section.key === 'list_search'
    || section.key === 'analysis'
    || section.key === 'menu'
    || section.key === 'approval';
}));
const selectedCoverageRow = computed(() => (coverageScan.value?.items || []).find(coverageRowMatchesScope));
const selectedPageHasFormConfig = computed(() => {
  const row = selectedCoverageRow.value;
  return row ? rowHasFormConfig(row) : true;
});
const selectedPageHasListSearchConfig = computed(() => {
  const row = selectedCoverageRow.value;
  return row ? rowHasListSearchConfig(row) : true;
});
const selectedPageHasAnalysisConfig = computed(() => {
  const row = selectedCoverageRow.value;
  return row ? rowHasAnalysisConfig(row) : false;
});
const visibleConfigSections = computed(() => {
  const result = visibleSections.value.filter((section) => {
    if (section.key === 'form' && currentModelIsRuntimeConfig.value) return false;
    if (section.key === 'form') return selectedPageHasFormConfig.value;
    if (section.key === 'list_search') return selectedPageHasListSearchConfig.value;
    return true;
  });
  if (
    !advancedPanelOpen.value
    && selectedPageHasAnalysisConfig.value
    && !result.some((section) => section.key === 'analysis')
  ) {
    result.push({
      key: 'analysis',
      label: '分析视图配置',
      contract_count: 0,
      intent: BUSINESS_CONFIG_INTENTS.analysisAudit,
      boundary: 'business_contract',
    });
  }
  return result;
});
const currentModel = computed(() => String(scopeModel.value || surface.value?.model || '').trim());
const currentModelIsRuntimeConfig = computed(() => isBusinessConfigRuntimeModel(currentModel.value));
const approvalSection = computed(() => visibleConfigSections.value.find((section) => section.key === 'approval') || null);
const approvalModeOptions = computed(() => approvalAudit.value?.mode_options?.length
  ? approvalAudit.value.mode_options
  : [
      { value: 'none', label: '无需审核' },
      { value: 'single', label: '单级审核' },
      { value: 'linear', label: '多级顺序审核' },
    ]);
const approvalScopeOptions = computed(() => approvalAudit.value?.scope_options || []);
const approvalPolicyLabel = computed(() => {
  const policy = approvalAudit.value?.policy;
  const target = policy?.target_model_label || selectedPageLabel.value || currentModel.value || '当前业务';
  return policy?.exists ? `${target}：${policy.name || '已配置规则'}` : `${target}：尚未建立审批规则，保存后自动创建。`;
});
const approvalRuntimeText = computed(() => {
  if (!approvalAudit.value) return '未读取';
  return approvalAudit.value.runtime_approval_required ? '当前需要审批' : '当前无需审批';
});
const approvalEffectGuideText = computed(() => {
  const target = approvalAudit.value?.policy?.target_model_label || selectedPageLabel.value || '当前业务';
  return `保存后立即影响${target}的办理审批判断；未保存调整可用“还原”放弃。`;
});
const approvalImpactSummaryText = computed(() => {
  if (!approvalForm.value.approval_required) {
    return '保存后当前业务不再要求审批。';
  }
  const modeLabel = approvalModeOptions.value.find((option) => option.value === approvalForm.value.mode)?.label || '审批';
  const scopeLabel = approvalScopeOptions.value.find((option) => option.value === approvalForm.value.manager_scope_key)?.label || '未指定默认审批岗位';
  const activeSteps = approvalSteps.value.filter((step) => step.active);
  const stepPreview = activeSteps
    .slice(0, 3)
    .map((step) => String(step.name || '').trim())
    .filter(Boolean)
    .join('、');
  const suffix = activeSteps.length > 3 ? `等 ${activeSteps.length} 个步骤` : `${activeSteps.length} 个步骤`;
  return `${modeLabel}，默认岗位：${scopeLabel}，${suffix}${stepPreview ? `：${stepPreview}` : ''}。`;
});
const canOpenDesigner = computed(() => Boolean(currentModel.value && scopeAction.value && !currentModelIsRuntimeConfig.value));
const headerDesignerButtonLabel = computed(() => {
  if (canOpenDesigner.value) return '配置表单字段';
  if (currentModelIsRuntimeConfig.value) return '使用专用配置';
  return '先选择页面';
});
const startScopeSummary = computed(() => {
  if (selectedPageLabel.value) return '当前页面配置，只影响这个业务页面';
  if (currentModel.value) return '已选择业务页面，可配置表单、列表、菜单和审批';
  return '先从业务页面目录选择配置对象';
});
const snapshotSummary = computed<BusinessConfigSnapshotSummaryPayload | null>(() => surface.value?.snapshot_summary || null);
const deliveryReadiness = computed(() => surface.value?.delivery_readiness || null);
const deliveryReadinessItems = computed(() => deliveryReadiness.value?.items || []);
const visibleDeliveryReadinessItems = computed(() => {
  const items = deliveryReadinessItems.value;
  if (advancedPanelOpen.value) return items;
  return items.filter((item) => CORE_DELIVERY_READINESS_SECTIONS.has(String(item.section_key || '')));
});
const deliveryReadinessStatusText = computed(() => {
  const items = visibleDeliveryReadinessItems.value;
  if (!deliveryReadiness.value || !items.length) return '读取中';
  return items.every((item) => item.status === 'ready') ? '可交付' : '待处理';
});
const visibleDeliveryReadinessProgressText = computed(() => {
  const items = visibleDeliveryReadinessItems.value;
  if (!deliveryReadiness.value || !items.length) return snapshotSummary.value ? `配置 ${snapshotSummary.value.contract_count}` : '';
  const readyCount = items.filter((item) => item.status === 'ready').length;
  return `${readyCount}/${items.length} 项就绪`;
});
const snapshotSummaryText = computed(() => {
  const summary = snapshotSummary.value;
  if (!summary) return '';
  const published = summary.status_counts?.published || 0;
  const viewTypes = Object.entries(summary.view_type_counts || {})
    .map(([key, count]) => `${viewTypeLabel(key)} ${count}`)
    .join('、');
  return `配置快照 ${summary.contract_count}，已发布 ${published}，按动作 ${summary.action_scope_count}${viewTypes ? `，${viewTypes}` : ''}`;
});
const snapshotCompareSummary = computed(() => {
  const result = snapshotCompareResult.value;
  if (!result) return '';
  return [
    `当前 ${result.current_contract_count}`,
    `基线 ${result.baseline_contract_count}`,
    `变化 ${result.changed_count}`,
    `新增 ${result.added_count}`,
    `移除 ${result.removed_count}`,
  ].join('，');
});
const snapshotCompareChangedRows = computed(() => (snapshotCompareResult.value?.changed || []).slice(0, 8));
const snapshotCompareAddedRows = computed(() => (snapshotCompareResult.value?.added || []).slice(0, 6));
const snapshotCompareRemovedRows = computed(() => (snapshotCompareResult.value?.removed || []).slice(0, 6));
const snapshotRemediationSummary = computed(() => {
  const result = snapshotCompareResult.value;
  if (!result) return '';
  const total = result.changed_count + result.added_count + result.removed_count;
  if (!total) return '两个环境配置一致，无需生成整改动作。';
  return `可生成 ${total} 条整改项：新增 ${result.added_count}，移除 ${result.removed_count}，变化 ${result.changed_count}。`;
});
const pageTypeOptions = [
  { key: 'all' as const, label: '全部页面' },
  { key: 'form' as const, label: '表单页面' },
  { key: 'list' as const, label: '列表页面' },
  { key: 'analysis' as const, label: '分析页面' },
];
const listSearchEditorTabs: Array<{ key: ListSearchEditorKind; label: string }> = [
  { key: 'list', label: '列表列' },
  { key: 'filter', label: '搜索条件' },
  { key: 'group', label: '默认分组' },
];
const analysisEditorTabs: Array<{ key: AnalysisEditorKind; label: string }> = [
  { key: 'pivotMeasure', label: '透视指标' },
  { key: 'pivotDimension', label: '透视维度' },
  { key: 'graphMeasure', label: '图表指标' },
  { key: 'graphDimension', label: '图表维度' },
];
const listSearchPanelDescription = computed(() => (
  advancedPanelOpen.value
    ? '这些配置写入正式业务配置，不写入个人列偏好。'
    : '保存为这个页面的默认列表、搜索和分组设置，不覆盖个人列宽和排序偏好。'
));
const versionPanelDescription = computed(() => (
  advancedPanelOpen.value
    ? '按当前模型、动作、视图、角色作用域读取正式业务配置版本。'
    : '查看这个页面的配置保存记录，可在需要时回滚到历史版本。'
));
const versionPanelGuide = computed(() => {
  if (activeVersionSection.value === 'form') {
    return {
      title: '表单版本怎么用',
      body: '当前生效版决定办理页面的字段、分组和布局。恢复历史版本后会立即发布为新的当前配置。',
    };
  }
  if (activeVersionSection.value === 'list_search') {
    return {
      title: '列表与搜索版本怎么用',
      body: '这里管理页面默认列表列、搜索条件和默认分组，不覆盖用户自己的列宽、排序等个人设置。',
    };
  }
  if (activeVersionSection.value === 'analysis') {
    return {
      title: '分析版本怎么用',
      body: '这里管理透视、图表等分析视图的默认指标和维度。恢复历史版本后刷新业务页面即可生效。',
    };
  }
  return {
    title: '配置版本怎么用',
    body: '先确认当前生效版，再选择需要恢复的历史版本。恢复操作会发布为新的当前配置。',
  };
});
const versionEmptyText = computed(() => (
  advancedPanelOpen.value ? '当前作用域暂无版本记录。' : '当前页面暂无版本记录。'
));
function isCoverageIssue(row: BusinessConfigCoverageScanItem) {
  return !row.is_complete || !row.is_runtime_complete || !row.has_menu;
}

const coverageIssueRows = computed(() => (
  coverageScan.value?.items || []
).filter(isCoverageIssue));
const coverageBatchBootstrapRows = computed(() => (
  coverageScan.value?.items || []
).filter((row) => (
  rowBootstrapMissingViewTypes(row, ['form', 'tree', 'search', 'pivot', 'graph']).length > 0
)));
const coverageScopeLabel = computed(() => {
  const scan = coverageScan.value;
  if (!scan) return '未扫描';
  if (scan.include_all_root_menu_actions) {
    return scan.root_menu_xmlid ? '扫描范围：系统根菜单' : '扫描范围：全部菜单';
  }
  if (scan.include_unreachable_actions) return '扫描范围：含无菜单动作';
  return '扫描范围：当前用户可见';
});

const pageSearchText = computed(() => pageSearch.value.trim().toLowerCase());
const visibleCoverageRows = computed(() => {
  const rows = showOnlyIssues.value ? coverageIssueRows.value : coverageScan.value?.items || [];
  const keyword = pageSearchText.value;
  const filtered = rows
    .filter((row) => {
      if (pageTypeFilter.value === 'form') return row.target_view_types.includes('form');
      if (pageTypeFilter.value === 'list') return rowHasListSearchConfig(row);
      if (pageTypeFilter.value === 'analysis') return rowHasAnalysisConfig(row);
      return true;
    })
    .filter((row) => {
      if (!keyword) return true;
      const searchable = advancedPanelOpen.value
        ? [row.name, row.model, row.view_mode, pageViewModeText(row)]
        : [row.name, pageViewModeText(row)];
      return searchable.some((text) => String(text || '').toLowerCase().includes(keyword));
    });
  return filtered.slice(0, 60);
});
const remediationSummaryItems = computed(() => {
  const counts = coverageScan.value?.summary.remediation_action_counts || {};
  return Object.entries(counts)
    .map(([code, count]) => ({ code, count, label: remediationActionLabel(code) }))
    .filter((item) => item.count > 0)
    .sort((left, right) => left.label.localeCompare(right.label, 'zh-Hans-CN'));
});
const availableModelFields = computed(() => (listSearchAudit.value?.available_model_fields || [])
  .concat(analysisAudit.value?.available_model_fields || [])
  .map((field) => ({
    name: String(field.name || '').trim(),
    label: cleanBusinessFieldLabel(field.name, field.label || field.name),
    type: String(field.type || '').trim(),
  }))
  .filter((field) => field.name)
  .filter((field, index, rows) => rows.findIndex((row) => row.name === field.name) === index)
);
const configuredListColumnLabels = computed(() => {
  const labels = listSearchAudit.value?.business_config_list_column_labels || {};
  return Object.entries(labels).reduce<Record<string, string>>((acc, [name, label]) => {
    const fieldName = String(name || '').trim();
    const cleanLabel = cleanBusinessFieldLabel(fieldName, label);
    if (fieldName && cleanLabel) acc[fieldName] = cleanLabel;
    return acc;
  }, {});
});
const duplicatedFieldLabels = computed(() => {
  const counts = new Map<string, number>();
  availableModelFields.value.forEach((field) => {
    const label = field.label || field.name;
    counts.set(label, (counts.get(label) || 0) + 1);
  });
  return new Set([...counts.entries()].filter(([, count]) => count > 1).map(([label]) => label));
});
const availableListFieldOptions = computed(() => fieldOptionsNotIn('list'));
const availableFilterFieldOptions = computed(() => fieldOptionsNotIn('filter'));
const availableGroupFieldOptions = computed(() => fieldOptionsNotIn('group'));
const availableAnalysisFieldOptions = computed(() => analysisFieldOptionCandidates().slice(0, analysisFieldOptionSearch.value.trim() ? 80 : 24));
const previewRouteTarget = computed(() => {
  const runtimeRoute = selectedRuntimeRoute.value || {};
  const runtimePath = String(runtimeRoute.path || '').trim();
  if (runtimePath) return { path: runtimePath, query: runtimeRoute.query || {} };
  if (scopeAction.value) {
    const query: Record<string, string> = {};
    const menuId = String(route.query.menu_id || '').trim();
    if (menuId) query.menu_id = menuId;
    return { path: `/a/${scopeAction.value}`, query };
  }
  return { path: '', query: {} };
});
const hasListSearchDraftChanges = computed(() => (
  normalizeNamesText(listColumnsText.value) !== listSearchBase.value.list
  || normalizeNamesText(searchFiltersText.value) !== listSearchBase.value.filter
  || normalizeNamesText(searchGroupByText.value) !== listSearchBase.value.group
));
const hasAnalysisDraftChanges = computed(() => (
  normalizeNamesText(pivotMeasuresText.value) !== analysisBase.value.pivotMeasures
  || normalizeNamesText(pivotDimensionsText.value) !== analysisBase.value.pivotDimensions
  || normalizeNamesText(graphMeasuresText.value) !== analysisBase.value.graphMeasures
  || normalizeNamesText(graphDimensionsText.value) !== analysisBase.value.graphDimensions
  || String(graphType.value || 'bar') !== analysisBase.value.graphType
));
const hasApprovalDraftChanges = computed(() => (
  approvalForm.value.approval_required !== approvalBase.value.approval_required
  || String(approvalForm.value.mode || 'none') !== approvalBase.value.mode
  || String(approvalForm.value.manager_scope_key || '') !== approvalBase.value.manager_scope_key
  || approvalStepsJson.value !== approvalStepsBaseJson.value
));
const activeApprovalStepCount = computed(() => approvalSteps.value.filter((step) => step.active).length);
const approvalStepsJson = computed(() => JSON.stringify(approvalSteps.value.map((step) => ({
  id: Number(step.id || 0),
  name: String(step.name || '').trim(),
  approval_scope_key: String(step.approval_scope_key || '').trim(),
  active: Boolean(step.active),
  amount_min: normalizeAmountText(step.amount_min),
  amount_max: normalizeAmountText(step.amount_max),
  condition_note: String(step.condition_note || '').trim(),
  note: String(step.note || '').trim(),
}))));
const approvalValidationMessage = computed(() => {
  if (!approvalForm.value.approval_required) return '';
  if (!approvalSteps.value.length) return '启用审批后至少需要配置一个审批步骤。';
  const invalidNameIndex = approvalSteps.value.findIndex((step) => !String(step.name || '').trim());
  if (invalidNameIndex >= 0) return `第 ${invalidNameIndex + 1} 步需要填写步骤名称。`;
  const invalidScopeIndex = approvalSteps.value.findIndex((step) => !String(step.approval_scope_key || '').trim());
  if (invalidScopeIndex >= 0) return `第 ${invalidScopeIndex + 1} 步需要选择审批岗位。`;
  const invalidAmountIndex = approvalSteps.value.findIndex((step) => {
    const minText = normalizeAmountText(step.amount_min);
    const maxText = normalizeAmountText(step.amount_max);
    if (!minText || !maxText) return false;
    const min = Number(minText);
    const max = Number(maxText);
    return Number.isFinite(min) && Number.isFinite(max) && min > max;
  });
  if (invalidAmountIndex >= 0) return `第 ${invalidAmountIndex + 1} 步金额下限不能大于上限。`;
  return '';
});
const canSaveApprovalDraft = computed(() => hasApprovalDraftChanges.value && !approvalValidationMessage.value);

function numericQuery(name: string) {
  const parsed = Number(route.query[name] || 0);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : undefined;
}

const scopeAction = computed(() => {
  const parsed = Number(scopeActionId.value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : undefined;
});

const scopeView = computed(() => {
  const parsed = Number(scopeViewId.value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : undefined;
});

const scopeRole = computed(() => String(scopeRoleKey.value || '').trim() || undefined);

function coverageRowKey(row: Pick<BusinessConfigCoverageScanItem, 'model' | 'action_id' | 'view_id'>) {
  return [
    String(row.model || '').trim(),
    Number(row.action_id || 0),
    Number(row.view_id || 0),
  ].join(':');
}

function coverageRowMatchesScope(row: Pick<BusinessConfigCoverageScanItem, 'model' | 'action_id' | 'view_id'>) {
  const actionId = Number(scopeAction.value || 0);
  if (!actionId || Number(row.action_id || 0) !== actionId) return false;
  const rowModel = String(row.model || '').trim();
  const model = String(currentModel.value || '').trim();
  if (model && rowModel && rowModel !== model) return false;
  return Number(row.view_id || 0) === Number(scopeView.value || 0);
}

function coverageRowActionId(row: Pick<BusinessConfigCoverageScanItem, 'action_id'>) {
  return Number(row.action_id || 0) || undefined;
}

function coverageRowViewId(row: Pick<BusinessConfigCoverageScanItem, 'view_id'>) {
  return Number(row.view_id || 0) || undefined;
}

function clearMessage() {
  message.value = { text: '', detail: '' };
}

function setMessage(text: string, detail = '') {
  message.value = { text, detail };
}

function boundaryLabel(boundary: unknown) {
  const value = String(boundary || '').trim();
  if (value === 'ui_only') return '仅页面设置';
  if (value === 'business_contract') return '业务默认配置';
  if (value === 'business_contract_not_user_preference') return '业务默认配置';
  if (value === 'business_contract_with_policy_runtime') return '菜单显示规则';
  if (value === 'business_contract_version') return '版本记录';
  if (value === 'coverage_guard') return '覆盖检查';
  if (value === 'industry_policy_runtime') return '行业业务规则';
  return value || '未声明来源';
}

function sectionHelpLabel(sectionKey: string) {
  if (sectionKey === 'form') return '字段显示、隐藏、必填、布局';
  if (sectionKey === 'list_search') return '列表列、搜索条件、默认分组';
  if (sectionKey === 'analysis') return '透视、图表、日历、看板';
  if (sectionKey === 'menu') return '菜单入口、显示范围、发布状态';
  if (sectionKey === 'approval') return '启用审批、审批方式、审批岗位';
  return '业务配置';
}

function sectionDisplayLabel(sectionKey: string, fallback: string) {
  if (sectionKey === 'form') return '表单字段与布局';
  if (sectionKey === 'list_search') return '列表与搜索';
  if (sectionKey === 'analysis') return '分析视图';
  if (sectionKey === 'menu') return '菜单入口';
  if (sectionKey === 'approval') return '审批规则';
  return fallback || '业务配置';
}

function sectionPrimaryCopy(sectionKey: string) {
  if (sectionKey === 'form') return '调整字段显示、必填、顺序和页面布局。';
  if (sectionKey === 'list_search') return '调整列表列、搜索条件和默认分组。';
  if (sectionKey === 'analysis') return '查看透视、图表、日历和看板配置版本。';
  if (sectionKey === 'menu') return '调整这个页面在菜单中的显示方式。';
  if (sectionKey === 'approval') return '设置这个业务是否需要审批、审批方式和审批岗位。';
  return '调整当前业务页面配置。';
}

function sectionTaskKindLabel(sectionKey: string) {
  if (sectionKey === 'form') return '页面结构';
  if (sectionKey === 'list_search') return '查询体验';
  if (sectionKey === 'analysis') return '分析视图';
  if (sectionKey === 'menu') return '导航入口';
  if (sectionKey === 'approval') return '办理规则';
  return '业务配置';
}

function sectionImpactText(sectionKey: string) {
  const page = selectedCoverageRow.value?.name || selectedPageLabel.value || '当前页面';
  if (sectionKey === 'form') return `影响 ${page} 的表单填写体验`;
  if (sectionKey === 'list_search') return `影响 ${page} 的列表和检索默认值`;
  if (sectionKey === 'analysis') return `影响 ${page} 的统计分析视图`;
  if (sectionKey === 'menu') return `影响 ${page} 的导航可见性`;
  if (sectionKey === 'approval') return `影响 ${page} 的提交和审核判断`;
  return `影响 ${page}`;
}

function sectionPrimaryActionLabel(sectionKey: string) {
  if (sectionKey === 'form') return '配置表单字段';
  if (sectionKey === 'list_search') return '配置列表';
  if (sectionKey === 'analysis') return '配置分析';
  if (sectionKey === 'menu') return '配置菜单';
  if (sectionKey === 'approval') return '配置审批';
  return '配置';
}

function selectedPageViewTypes() {
  const row = selectedCoverageRow.value;
  const fromTarget = (row?.target_view_types || []).map((item) => String(item || '').trim()).filter(Boolean);
  const fromMode = String(row?.view_mode || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
  return new Set([...fromTarget, ...fromMode]);
}

function sectionExpectedContractCount(sectionKey: string) {
  const viewTypes = selectedPageViewTypes();
  if (sectionKey === 'list_search') {
    const expected = [
      viewTypes.has('tree') || viewTypes.has('list') ? 'tree' : '',
      viewTypes.has('search') ? 'search' : '',
    ].filter(Boolean).length;
    return expected || 2;
  }
  if (sectionKey === 'analysis') {
    const expected = ['pivot', 'graph', 'calendar', 'dashboard'].filter((viewType) => viewTypes.has(viewType)).length;
    return expected || 1;
  }
  return 1;
}

function sectionStatusLabel(sectionKey: string, contractCount: number) {
  const count = Number(contractCount || 0);
  if (sectionKey === 'menu') return count > 0 ? '已配置' : '未调整';
  const expected = sectionExpectedContractCount(sectionKey);
  if (count <= 0) return '未配置';
  if (count < expected) return '部分配置';
  return '已配置';
}

function sectionConfigProgressText(sectionKey: string, contractCount: number) {
  if (sectionKey === 'menu') return '';
  const expected = sectionExpectedContractCount(sectionKey);
  const count = Math.max(0, Math.min(Number(contractCount || 0), expected));
  return `${count}/${expected}`;
}

function sectionTaskCoverageText(sectionKey: string, contractCount: number) {
  if (sectionKey === 'menu') {
    return Number(contractCount || 0) > 0 ? '已有菜单显示规则' : '使用默认菜单显示';
  }
  const progress = sectionConfigProgressText(sectionKey, contractCount);
  return progress ? `覆盖 ${progress}` : '覆盖 0/1';
}

function viewTypeLabel(viewType: string) {
  if (viewType === 'form') return '表单';
  if (viewType === 'tree' || viewType === 'list') return '列表';
  if (viewType === 'search') return '搜索';
  if (viewType === 'pivot') return '透视';
  if (viewType === 'graph') return '图表';
  if (viewType === 'calendar') return '日历';
  if (viewType === 'dashboard') return '看板';
  return viewType || '通用';
}

function pageViewModeText(row: BusinessConfigCoverageScanItem) {
  const modes = String(row.view_mode || '')
    .split(',')
    .map((item) => viewTypeLabel(item.trim()))
    .filter(Boolean);
  return modes.length ? `页面类型 ${modes.join('、')}` : '页面类型 通用';
}

function pageDesignStatus(row: BusinessConfigCoverageScanItem) {
  if (!row.runtime_route?.path) return '暂不可预览';
  if (row.runtime_missing_view_types.includes('form')) return '可生成后设计';
  if (row.target_view_types.includes('form')) return '可设计表单';
  return '可打开页面';
}

function rowCoverageProgressText(row: BusinessConfigCoverageScanItem) {
  const targets = (row.target_view_types || []).map((item) => String(item || '').trim()).filter(Boolean);
  const expected = targets.length || 1;
  const configured = targets.filter((viewType) => Number(row.coverage?.[viewType] || 0) > 0).length;
  const runtime = targets.filter((viewType) => Number(row.runtime_coverage?.[viewType] || 0) > 0).length;
  return `配置 ${configured}/${expected}，生效 ${runtime}/${expected}`;
}

function rowActionHintText(row: BusinessConfigCoverageScanItem) {
  if (!row.has_menu) return '需配置菜单入口';
  const reasons = new Set(Object.values(row.runtime_gap_reasons || {}).map((item) => String(item || '').trim()).filter(Boolean));
  if (reasons.has('missing_contract')) {
    const missingContractTypes = rowMissingContractViewTypes(row);
    return `需补 ${missingContractTypes.map(viewTypeLabel).join('、')}`;
  }
  if (reasons.has('not_published')) return '需发布配置版本';
  if (reasons.has('not_runtime_applicable')) return '需检查作用域';
  if (row.user_preference_count > 0) return '存在个人配置';
  return '';
}

function rowMissingContractViewTypes(row: BusinessConfigCoverageScanItem) {
  return (row.runtime_missing_view_types || [])
    .filter((viewType) => String(row.runtime_gap_reasons?.[viewType] || '').trim() === 'missing_contract');
}

function rowBootstrapMissingViewTypes(row: BusinessConfigCoverageScanItem, allowedViewTypes: string[]) {
  const allowed = new Set(allowedViewTypes);
  return rowMissingContractViewTypes(row)
    .filter((viewType) => allowed.has(viewType))
}

function visibleRowRemediationActions(row: BusinessConfigCoverageScanItem) {
  return (row.remediation_actions || [])
    .filter((action) => ['configure_contract', 'publish_contract', 'fix_scope', 'configure_menu', 'review_user_preference_boundary'].includes(action.code))
    .slice(0, 2);
}

function rowHasListSearchConfig(row: BusinessConfigCoverageScanItem) {
  return row.target_view_types.some((viewType) => viewType === 'tree' || viewType === 'search')
    || String(row.view_mode || '').split(',').some((viewType) => ['tree', 'list', 'search'].includes(viewType.trim()));
}

function rowHasFormConfig(row: BusinessConfigCoverageScanItem) {
  return row.target_view_types.includes('form')
    || String(row.view_mode || '').split(',').some((viewType) => viewType.trim() === 'form');
}

function rowHasAnalysisConfig(row: BusinessConfigCoverageScanItem) {
  const analysisViewTypes = new Set(['pivot', 'graph', 'calendar', 'dashboard']);
  return row.target_view_types.some((viewType) => analysisViewTypes.has(viewType))
    || String(row.view_mode || '').split(',').some((viewType) => analysisViewTypes.has(viewType.trim()));
}

function runtimeReasonLabel(reason: string) {
  if (reason === 'missing_contract') return '待完善配置';
  if (reason === 'not_published') return '未发布';
  if (reason === 'not_runtime_applicable') return '作用域未命中';
  if (reason === 'not_published_or_not_runtime_applicable') return '未发布/作用域未命中';
  return reason || '未知';
}

function severityLabel(severity: string) {
  if (severity === 'error') return '阻断';
  if (severity === 'warning') return '警告';
  if (severity === 'notice') return '提示';
  return '正常';
}

function overallStatusLabel(status: string) {
  if (status === 'blocked') return '阻断';
  if (status === 'warning') return '警告';
  if (status === 'notice') return '提示';
  if (status === 'pass') return '通过';
  return status || '未知';
}

function versionStatusLabel(status: string) {
  if (status === 'published') return '已发布';
  if (status === 'draft') return '草稿';
  if (status === 'archived') return '已归档';
  return status || '未知';
}

function versionContractDisplayName(contract: BusinessConfigContractVersionsPayload['contracts'][number]) {
  if (advancedPanelOpen.value) return contract.name || contract.model || '业务配置';
  const page = selectedPageLabel.value || surface.value?.model || contract.model || '当前页面';
  const view = viewTypeLabel(contract.view_type);
  return view ? `${page} · ${view}` : page;
}

function versionContractImpactText(contract: BusinessConfigContractVersionsPayload['contracts'][number]) {
  const view = viewTypeLabel(contract.view_type);
  if (contract.view_type === 'form') return '影响办理页字段、分组、显示隐藏和布局。';
  if (contract.view_type === 'tree' || contract.view_type === 'list') return '影响办理页默认列表列。';
  if (contract.view_type === 'search') return '影响办理页搜索条件和默认分组。';
  if (['pivot', 'graph', 'calendar', 'dashboard'].includes(contract.view_type)) return `影响${view}视图的默认展示。`;
  return `影响${view}配置的默认运行效果。`;
}

function versionRollbackButtonLabel(contract: BusinessConfigContractVersionsPayload['contracts'][number]) {
  return contract.versions.length < 2 ? '暂无可回滚版本' : '恢复上一版';
}

function versionContractDecisionText(contract: BusinessConfigContractVersionsPayload['contracts'][number]) {
  const historyCount = Math.max(0, contract.versions.length - 1);
  const currentSummary = versionSummaryText(contract.summary);
  if (!historyCount) return `当前只有一个版本：${currentSummary}。`;
  return `当前生效：${currentSummary}。可恢复 ${historyCount} 个历史版本，恢复后会发布为新的当前配置。`;
}

function versionSummaryNames(summary: BusinessConfigContractVersionsPayload['contracts'][number]['summary']) {
  return {
    form: (summary.form_field_labels && summary.form_field_labels.length ? summary.form_field_labels : summary.form_fields) || [],
    list: summary.list_columns || [],
    filter: summary.search_filters || [],
    group: summary.search_group_by || [],
    viewTypes: summary.view_types || [],
    analysis: summary.analysis_items || [],
  };
}

function analysisItemLabel(item: string) {
  const text = String(item || '').trim();
  if (!text) return '';
  const [viewType, ...rest] = text.split('.');
  const label = viewTypeLabel(viewType);
  return rest.length ? `${label}：${rest.join(' / ')}` : label;
}

function countDiff(left: string[], right: string[]) {
  const leftSet = new Set(left);
  const rightSet = new Set(right);
  const added = right.filter((name) => !leftSet.has(name));
  const removed = left.filter((name) => !rightSet.has(name));
  return {
    added,
    removed,
  };
}

function formatDiffNames(names: string[]) {
  const visible = names.slice(0, 3).join('、');
  if (!visible) return '';
  return names.length > 3 ? `${visible} 等 ${names.length} 项` : visible;
}

function versionDeltaText(
  current: BusinessConfigContractVersionsPayload['contracts'][number]['summary'],
  target: BusinessConfigContractVersionsPayload['contracts'][number]['summary'],
  isCurrent: boolean,
) {
  if (isCurrent) return '当前版本';
  const currentNames = versionSummaryNames(current);
  const targetNames = versionSummaryNames(target);
  const parts = [
    { label: '字段', diff: countDiff(currentNames.form, targetNames.form) },
    { label: '列', diff: countDiff(currentNames.list, targetNames.list) },
    { label: '筛选', diff: countDiff(currentNames.filter, targetNames.filter) },
    { label: '分组', diff: countDiff(currentNames.group, targetNames.group) },
    { label: '分析项', diff: countDiff(currentNames.analysis, targetNames.analysis) },
    { label: '视图', diff: countDiff(currentNames.viewTypes, targetNames.viewTypes) },
  ]
    .map((item) => {
      const changes = [
        item.diff.added.length ? `多 ${item.diff.added.length}：${formatDiffNames(item.diff.added)}` : '',
        item.diff.removed.length ? `少 ${item.diff.removed.length}：${formatDiffNames(item.diff.removed)}` : '',
      ].filter(Boolean).join('、');
      return changes ? `${item.label}${changes}` : '';
    })
    .filter(Boolean);
  return parts.length ? `与当前相比：${parts.join('；')}` : '与当前一致';
}

function versionSummaryText(summary: BusinessConfigContractVersionsPayload['contracts'][number]['summary']) {
  const counts = [
    summary.form_field_count ? `字段 ${summary.form_field_count}` : '',
    summary.list_column_count ? `列 ${summary.list_column_count}` : '',
    summary.search_filter_count ? `筛选 ${summary.search_filter_count}` : '',
    summary.search_group_by_count ? `分组 ${summary.search_group_by_count}` : '',
    summary.analysis_item_count ? `分析项 ${summary.analysis_item_count}` : '',
  ].filter(Boolean);
  if (counts.length) return counts.join(' / ');
  const viewTypes = (summary.view_types || []).map(viewTypeLabel).filter(Boolean);
  return viewTypes.length ? `视图 ${viewTypes.join('、')}` : '暂无配置项';
}

function runtimeReasonText(row: BusinessConfigCoverageScanItem) {
  return row.runtime_missing_view_types
    .map((viewType) => `${viewTypeLabel(viewType)}:${runtimeReasonLabel(row.runtime_gap_reasons[viewType] || '')}`)
    .join('，');
}

function runtimeEvidenceText(row: BusinessConfigCoverageScanItem) {
  return row.target_view_types
    .map((viewType) => {
      const evidence = row.runtime_evidence[viewType];
      if (!evidence) return '';
      return `${viewTypeLabel(viewType)} ${evidence.configured_count}/${evidence.published_count}/${evidence.runtime_count}`;
    })
    .filter(Boolean)
    .join('，');
}

function runtimeRouteText(row: BusinessConfigCoverageScanItem) {
  const runtimeRoute = row.runtime_route || {};
  const path = String(runtimeRoute.path || '').trim();
  if (!path) return '';
  const params = new URLSearchParams();
  Object.entries(runtimeRoute.query || {}).forEach(([key, value]) => {
    const text = String(value || '').trim();
    if (key && text) params.set(key, text);
  });
  const query = params.toString();
  return query ? `${path}?${query}` : path;
}

function remediationActionLabel(code: string) {
  if (code === 'configure_contract') return '补齐配置';
  if (code === 'publish_contract') return '查看版本';
  if (code === 'fix_scope') return '检查范围';
  if (code === 'configure_menu') return '配置菜单';
  if (code === 'review_user_preference_boundary') return '检查个人设置';
  return code;
}

function deliveryReadinessItemStatusText(item: NonNullable<BusinessConfigSurfacePayload['delivery_readiness']>['items'][number]) {
  if (item.status === 'ready') return '就绪';
  return '待处理';
}

function deliveryReadinessItemMetaText(item: NonNullable<BusinessConfigSurfacePayload['delivery_readiness']>['items'][number]) {
  const countText = item.contract_count ? `${item.contract_count} 项` : '未建立';
  return advancedPanelOpen.value && item.boundary ? `${countText} · ${boundaryLabel(item.boundary)}` : countText;
}

function runDeliveryReadinessAction(item: NonNullable<BusinessConfigSurfacePayload['delivery_readiness']>['items'][number]) {
  if (item.action === 'coverage_scan') {
    scanSystemRootCoverage();
    return;
  }
  if (item.action === 'snapshot_compare') {
    advancedPanelOpen.value = true;
    return;
  }
  if (item.section_key === 'menu') {
    openMenuConfig();
    return;
  }
  if (item.section_key === 'approval') {
    loadApprovalConfig();
    return;
  }
  if (item.section_key === 'list_search') {
    loadListSearchConfig();
    return;
  }
  if (item.section_key === 'form') {
    openFormConfig();
  }
}

function withSurfaceLoadTimeout<T>(request: Promise<T>) {
  let timer: number | undefined;
  const timeout = new Promise<T>((_, reject) => {
    timer = window.setTimeout(() => {
      reject(new Error('配置能力读取超时，请检查网络或稍后点击“读取配置对象”重试。'));
    }, SURFACE_LOAD_TIMEOUT_MS);
  });
  return Promise.race([request, timeout]).finally(() => {
    if (timer) {
      window.clearTimeout(timer);
    }
  });
}

async function loadSurface() {
  const seq = ++surfaceLoadSeq;
  loading.value = true;
  error.value = '';
  clearMessage();
  try {
    const nextSurface = await withSurfaceLoadTimeout(
      loadBusinessConfigSurface({
        model: currentModel.value || undefined,
        action_id: scopeAction.value,
        view_id: scopeView.value,
        role_key: scopeRole.value,
      }),
    );
    if (seq !== surfaceLoadSeq) return;
    surface.value = nextSurface;
  } catch (err) {
    if (seq !== surfaceLoadSeq) return;
    error.value = err instanceof Error ? err.message : '业务配置工作台加载失败';
  } finally {
    if (seq === surfaceLoadSeq) {
      loading.value = false;
    }
  }
}

async function scanCoverage() {
  scanLoading.value = true;
  error.value = '';
  clearMessage();
  try {
    coverageScan.value = await scanBusinessConfigCoverage({
      model: currentModel.value || undefined,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      root_menu_xmlid: rootMenuXmlid.value || undefined,
      include_all_root_menu_actions: false,
      limit: 1000,
    });
    hydrateSelectedCoverageRowFromScan();
  } catch (err) {
    error.value = err instanceof Error ? err.message : '业务配置覆盖扫描失败';
  } finally {
    scanLoading.value = false;
  }
}

async function scanSystemRootCoverage() {
  scanLoading.value = true;
  error.value = '';
  clearMessage();
  try {
    coverageScan.value = await scanBusinessConfigCoverage({
      model: currentModel.value || undefined,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      root_menu_xmlid: rootMenuXmlid.value || undefined,
      include_all_root_menu_actions: true,
      limit: 1000,
    });
    hydrateSelectedCoverageRowFromScan();
  } catch (err) {
    error.value = err instanceof Error ? err.message : '系统根菜单覆盖扫描失败';
  } finally {
    scanLoading.value = false;
  }
}

async function scanCurrentModel() {
  if (!currentModel.value) return;
  scanLoading.value = true;
  error.value = '';
  clearMessage();
  try {
    coverageScan.value = await scanBusinessConfigCoverage({
      model: currentModel.value,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      root_menu_xmlid: rootMenuXmlid.value || undefined,
      include_all_root_menu_actions: Boolean(coverageScan.value?.include_all_root_menu_actions),
      limit: 1000,
    });
    hydrateSelectedCoverageRowFromScan();
  } catch (err) {
    error.value = err instanceof Error ? err.message : '当前模型覆盖扫描失败';
  } finally {
    scanLoading.value = false;
  }
}

async function rescanCoverageAfterBootstrap() {
  if (coverageScan.value?.include_all_root_menu_actions) {
    await scanSystemRootCoverage();
    return;
  }
  if (coverageScan.value?.model) {
    await scanCurrentModel();
    return;
  }
  await scanCoverage();
}

function buildCoverageSummaryText() {
  const scan = coverageScan.value;
  if (!scan) return '';
  const summary = scan.summary;
  const actions = remediationSummaryItems.value
    .map((item) => `${item.label}${item.count}`)
    .join('，') || '无';
  const routeRows = (coverageIssueRows.value.length ? coverageIssueRows.value : scan.items || [])
    .map((row) => ({
      row,
      route: runtimeRouteText(row),
    }))
    .filter((item) => item.route)
    .slice(0, 10);
  const routeEvidence = routeRows.length
    ? routeRows.map((item) => `${item.row.name || item.row.model}：${item.route}`).join('\n')
    : '无';
  return [
    `低代码配置覆盖验收：${overallStatusLabel(summary.overall_status)}`,
    `${coverageScopeLabel.value}；范围：${scan.model || '全部模型'}，动作 ${summary.action_count}`,
    `严重级别：阻断 ${summary.severity_counts.error || 0}，警告 ${summary.severity_counts.warning || 0}，提示 ${summary.severity_counts.notice || 0}`,
    `待完善：配置 ${summary.missing_count}，办理页 ${summary.runtime_missing_count}，分析页 ${summary.runtime_missing_analysis_count || 0}，无菜单 ${summary.no_menu_count}，个人设置 ${summary.user_preference_count}`,
    `原因：未发布 ${summary.not_published_gap_count}，作用域未命中 ${summary.not_runtime_applicable_gap_count}`,
    `整改：${actions}`,
    `运行页面证据：\n${routeEvidence}`,
  ].join('\n');
}

async function copyCoverageSummary() {
  const text = buildCoverageSummaryText();
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    setMessage('已复制验收摘要');
  } catch {
    setMessage('复制摘要失败', '浏览器未允许写入剪贴板，请稍后重试');
  }
}

async function downloadSnapshot() {
  snapshotExportLoading.value = true;
  error.value = '';
  clearMessage();
  try {
    const snapshot = await exportBusinessConfigSnapshot();
    const database = String(snapshot.database || 'business-config').replace(/[^a-zA-Z0-9_-]+/g, '-');
    const blob = new Blob([`${JSON.stringify(snapshot, null, 2)}\n`], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `business-config-contract-snapshot-${database}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    setMessage('已生成当前快照');
  } catch (err) {
    error.value = err instanceof Error ? err.message : '当前快照导出失败';
  } finally {
    snapshotExportLoading.value = false;
  }
}

function normalizeSnapshotFileToken(value: string) {
  return String(value || 'business-config').replace(/[^a-zA-Z0-9_-]+/g, '-');
}

function snapshotContractIdentity(row: Partial<BusinessConfigSnapshotComparePayload['added'][number]>) {
  return {
    name: row.name || '',
    model: row.model || '',
    view_type: row.view_type || '',
    action_id: Number(row.action_id || 0),
    view_id: Number(row.view_id || 0),
    role_key: row.role_key || '',
  };
}

function buildSnapshotRemediationPlan(result: BusinessConfigSnapshotComparePayload) {
  const generatedAt = new Date().toISOString();
  const actions = [
    ...result.added.map((row) => ({
      action: 'review_added_contract',
      severity: 'review_required',
      reason: '当前环境存在基线快照中没有的业务配置合同，确认是否应沉淀到目标环境或回退。',
      contract: snapshotContractIdentity(row),
      current: {
        status: row.status,
        version_no: row.version_no,
        payload_hash: row.payload_hash || '',
      },
    })),
    ...result.removed.map((row) => ({
      action: 'restore_or_accept_removed_contract',
      severity: 'review_required',
      reason: '基线快照存在但当前环境缺失该业务配置合同，确认是否需要从基线恢复或接受删除。',
      contract: snapshotContractIdentity(row),
      baseline: {
        status: row.status,
        version_no: row.version_no,
        payload_hash: row.payload_hash || '',
      },
    })),
    ...result.changed.map((row) => ({
      action: 'review_changed_contract',
      severity: 'review_required',
      reason: '当前环境与基线快照的业务配置合同状态或内容不同，确认保留当前版本还是按基线调整。',
      contract: {
        key: row.key,
        name: row.name || '',
        model: row.model || '',
        view_type: row.view_type || '',
      },
      baseline: {
        status: row.previous_status || '',
        version_no: row.previous_version_no || 0,
      },
      current: {
        status: row.current_status || '',
        version_no: row.current_version_no || 0,
      },
    })),
  ];
  return {
    schema_version: 'business_config_snapshot_remediation_plan.v1',
    generated_at: generatedAt,
    source: 'business_config_snapshot_compare',
    current_database: result.current_database,
    baseline_database: result.baseline_database,
    summary: {
      current_contract_count: result.current_contract_count,
      baseline_contract_count: result.baseline_contract_count,
      added_count: result.added_count,
      removed_count: result.removed_count,
      changed_count: result.changed_count,
      action_count: actions.length,
    },
    acceptance: {
      product_boundary: 'Only ui.business.config.contract changes are represented here.',
      execution_policy: 'This plan is review evidence. Apply changes through low-code configuration screens, migrations, or customer module baselines.',
      required_after_action: [
        'make verify.business_config.snapshot',
        'make verify.lowcode_config.runtime_boundary.guard',
        'make verify.product.surface.clean',
      ],
    },
    actions,
  };
}

function downloadJsonFile(payload: unknown, filename: string) {
  const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function downloadSnapshotRemediationPlan() {
  const result = snapshotCompareResult.value;
  if (!result) return;
  const plan = buildSnapshotRemediationPlan(result);
  const current = normalizeSnapshotFileToken(result.current_database);
  const baseline = normalizeSnapshotFileToken(result.baseline_database);
  downloadJsonFile(plan, `business-config-remediation-${baseline}-to-${current}.json`);
  setMessage('已生成整改清单', snapshotRemediationSummary.value);
}

async function compareSnapshot() {
  const text = snapshotCompareText.value.trim();
  if (!text) return;
  snapshotCompareLoading.value = true;
  error.value = '';
  clearMessage();
  try {
    const snapshot = JSON.parse(text) as Record<string, unknown>;
    snapshotCompareResult.value = await compareBusinessConfigSnapshot({ snapshot });
    const result = snapshotCompareResult.value;
    setMessage(
      '已完成快照对比',
      `变化 ${result.changed_count}，新增 ${result.added_count}，移除 ${result.removed_count}`,
    );
  } catch (err) {
    snapshotCompareResult.value = null;
    error.value = err instanceof Error ? err.message : '快照 JSON 解析或对比失败';
  } finally {
    snapshotCompareLoading.value = false;
  }
}

async function applyScopeAndLoad() {
  listSearchPanelOpen.value = false;
  listSearchAudit.value = null;
  analysisPanelOpen.value = false;
  analysisAudit.value = null;
  versionsPanelOpen.value = false;
  versionContracts.value = [];
  coverageScan.value = null;
  selectedPageLabel.value = '';
  await router.replace({
    path: route.path,
    query: {
      ...route.query,
      model: currentModel.value || undefined,
      action_id: scopeAction.value ? String(scopeAction.value) : undefined,
      view_id: scopeView.value ? String(scopeView.value) : undefined,
      role_key: scopeRole.value || undefined,
      page_label: undefined,
    },
  });
  await loadSurface();
}

async function focusScanRow(row: BusinessConfigCoverageScanItem) {
  scopeModel.value = row.model;
  scopeActionId.value = row.action_id;
  scopeViewId.value = Number(row.view_id || 0);
  selectedPageLabel.value = row.name || row.model;
  selectedRuntimeRoute.value = row.runtime_route || null;
  listSearchPanelOpen.value = false;
  listSearchAudit.value = null;
  analysisPanelOpen.value = false;
  analysisAudit.value = null;
  versionsPanelOpen.value = false;
  versionContracts.value = [];
  replaceWorkbenchQuerySilently({
    model: row.model || undefined,
    action_id: row.action_id ? String(row.action_id) : undefined,
    view_id: row.view_id ? String(row.view_id) : undefined,
    role_key: scopeRole.value || undefined,
    page_label: row.name || undefined,
    open_list_search: undefined,
  });
  await loadSurface();
}

function hydrateSelectedCoverageRowFromScan() {
  const matched = (coverageScan.value?.items || []).find(coverageRowMatchesScope);
  if (!matched) return;
  scopeModel.value = matched.model || scopeModel.value;
  scopeActionId.value = matched.action_id || scopeActionId.value;
  scopeViewId.value = Number(matched.view_id || scopeViewId.value || 0);
  selectedPageLabel.value = matched.name || selectedPageLabel.value || matched.model;
  selectedRuntimeRoute.value = matched.runtime_route || selectedRuntimeRoute.value;
}

async function openRuntimeRoute(row: BusinessConfigCoverageScanItem) {
  const runtimeRoute = row.runtime_route || {};
  const path = String(runtimeRoute.path || '').trim();
  if (!path) return;
  await router.push({
    path,
    query: buildPreviewRuntimeQuery(runtimeRoute.query || {}, {
      model: row.model,
      actionId: row.action_id,
      viewId: row.view_id,
      pageLabel: row.name || row.model,
    }),
  });
}

function buildPreviewRuntimeQuery(
  baseQuery: Record<string, string> = {},
  options: { model?: string; actionId?: number; viewId?: number; pageLabel?: string; preserveEditorContext?: boolean } = {},
) {
  const preserveEditorContext = Boolean(options.preserveEditorContext);
  return {
    ...baseQuery,
    root_menu_xmlid: route.query.root_menu_xmlid || undefined,
    page_label: options.pageLabel || selectedPageLabel.value || undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig]: '1',
    [BUSINESS_CONFIG_ROUTE_FLAGS.openPages]: '1',
    model: options.model || currentModel.value || undefined,
    action_id: options.actionId ? String(options.actionId) : (scopeAction.value ? String(scopeAction.value) : undefined),
    view_id: options.viewId ? String(options.viewId) : (scopeView.value ? String(scopeView.value) : undefined),
    list_search_tab: preserveEditorContext && listSearchPanelOpen.value && activeListSearchEditor.value !== 'list' ? activeListSearchEditor.value : undefined,
    open_list_search: preserveEditorContext && listSearchPanelOpen.value ? '1' : undefined,
    analysis_tab: preserveEditorContext && analysisPanelOpen.value && activeAnalysisEditor.value !== 'pivotMeasure' ? activeAnalysisEditor.value : undefined,
    open_analysis: preserveEditorContext && analysisPanelOpen.value ? '1' : undefined,
  };
}

async function previewSelectedRuntimeRoute() {
  const target = previewRouteTarget.value;
  const path = String(target.path || '').trim();
  if (!path) return;
  await router.push({
    path,
    query: buildPreviewRuntimeQuery(target.query || {}, { preserveEditorContext: true }),
  });
}

async function runRemediationAction(row: BusinessConfigCoverageScanItem, action: BusinessConfigRemediationAction) {
  await focusScanRow(row);
  if (action.code === 'configure_contract') {
    if (
      row.runtime_missing_view_types.some((viewType) => ['calendar', 'dashboard'].includes(viewType))
      && !row.runtime_missing_view_types.some((viewType) => ['form', 'tree', 'search', 'pivot', 'graph'].includes(viewType))
    ) {
      await loadAnalysisConfig();
      return;
    }
    await bootstrapMissingContracts(row);
    return;
  }
  if (action.code === 'fix_scope') {
    await openVersionsForRuntimeGaps(row);
    setMessage('请检查配置作用域', '当前配置已存在但未命中这个业务页面，请确认页面、视图或角色范围。');
    return;
  }
  if (action.code === 'publish_contract') {
    await openVersionsForRuntimeGaps(row);
    return;
  }
  if (action.code === 'configure_menu') {
    openMenuConfig();
    return;
  }
  if (action.code === 'review_user_preference_boundary') {
    await loadListSearchConfig();
  }
}

async function openVersionsForRuntimeGaps(row: BusinessConfigCoverageScanItem) {
  if (row.runtime_missing_view_types.some((viewType) => viewType === 'tree' || viewType === 'search')) {
    await loadVersions('list_search');
  } else if (row.runtime_missing_view_types.some((viewType) => ['pivot', 'graph', 'calendar', 'dashboard'].includes(viewType))) {
    await loadVersions('analysis');
  } else {
    await loadVersions('form');
  }
}

async function bootstrapMissingContracts(row: BusinessConfigCoverageScanItem) {
  if (!row.model) return;
  const missingContractTypes = rowBootstrapMissingViewTypes(row, ['form', 'tree', 'search', 'pivot', 'graph']);
  if (!missingContractTypes.length) {
    await openVersionsForRuntimeGaps(row);
    setMessage('没有可自动补齐的配置项', '当前待完善项需要检查发布状态或配置作用域。');
    return;
  }
  listSearchSaving.value = true;
  error.value = '';
  clearMessage();
  let savedCount = 0;
  let formFieldCount = 0;
  try {
    if (missingContractTypes.includes('form')) {
      const formResult = await bootstrapBusinessFormConfig({
        model: row.model,
        action_id: coverageRowActionId(row),
        view_id: coverageRowViewId(row),
        role_key: scopeRole.value,
        publish: true,
      });
      savedCount += 1;
      formFieldCount = formResult.field_count || 0;
    }
    const listSearchTypes = missingContractTypes
      .filter((viewType) => viewType === 'tree' || viewType === 'search');
    if (listSearchTypes.length) {
      const listResult = await bootstrapBusinessListSearchConfig({
        model: row.model,
        action_id: coverageRowActionId(row),
        view_id: coverageRowViewId(row),
        role_key: scopeRole.value,
        view_types: listSearchTypes,
        publish: true,
      });
      savedCount += listResult.saved_count || 0;
    }
    const analysisTypes = missingContractTypes
      .filter((viewType) => viewType === 'pivot' || viewType === 'graph');
    if (analysisTypes.length) {
      const analysisResult = await bootstrapBusinessAnalysisConfig({
        model: row.model,
        action_id: coverageRowActionId(row),
        view_id: coverageRowViewId(row),
        role_key: scopeRole.value,
        view_types: analysisTypes,
        publish: true,
      });
      savedCount += analysisResult.saved_count || 0;
    }
    await loadSurface();
    await scanCurrentModel();
    setMessage(
      '已补齐配置',
      formFieldCount ? `已发布 ${savedCount} 个业务配置，表单字段 ${formFieldCount}` : `已发布 ${savedCount} 个业务配置`,
    );
  } catch (err) {
    error.value = err instanceof Error ? err.message : '业务配置补齐失败，已打开手工配置';
    if (missingContractTypes.includes('form')) {
      openFormConfig();
    } else {
      await loadListSearchConfig();
    }
  } finally {
    listSearchSaving.value = false;
  }
}

async function bootstrapCoverageMissing() {
  if (!coverageBatchBootstrapRows.value.length) return;
  listSearchSaving.value = true;
  error.value = '';
  clearMessage();
  try {
    const result = await bootstrapCoverageMissingConfig({
      model: currentModel.value || undefined,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      root_menu_xmlid: rootMenuXmlid.value || undefined,
      include_all_root_menu_actions: Boolean(coverageScan.value?.include_all_root_menu_actions),
      limit: 1000,
      batch_limit: 300,
    });
    await rescanCoverageAfterBootstrap();
    const failedNames = (result.results || [])
      .filter((item) => !item.ok)
      .map((item) => item.name || item.model || String(item.action_id || ''))
      .filter(Boolean)
      .slice(0, 5)
      .join('、');
    setMessage(
      result.failed_count ? '已批量补齐配置，部分页面需手工处理' : '已批量补齐配置',
      result.failed_count
        ? `已发布 ${result.saved_count} 个业务配置，${result.failed_count} 个页面需手工处理${failedNames ? `：${failedNames}` : ''}`
        : `已发布 ${result.saved_count} 个业务配置`,
    );
  } catch (err) {
    error.value = err instanceof Error ? err.message : '批量补齐业务配置失败';
  } finally {
    listSearchSaving.value = false;
  }
}

function namesToText(names: string[]) {
  return names.join(', ');
}

function normalizeNamesText(raw: string) {
  return namesToText(parseNames(raw));
}

function parseNames(raw: string) {
  const seen = new Set<string>();
  return String(raw || '')
    .split(/[\n,，]+/)
    .map((item) => item.trim())
    .filter((item) => {
      if (!item || seen.has(item)) return false;
      seen.add(item);
      return true;
    });
}

function listSearchEditorState(kind: ListSearchEditorKind) {
  if (kind === 'list') return { text: listColumnsText, draft: listColumnDraft };
  if (kind === 'filter') return { text: searchFiltersText, draft: searchFilterDraft };
  return { text: searchGroupByText, draft: searchGroupDraft };
}

function listSearchEditorCount(kind: ListSearchEditorKind) {
  return parseNames(listSearchEditorState(kind).text.value).length;
}

function fieldOptionSearchState(kind: ListSearchEditorKind) {
  if (kind === 'list') return listFieldOptionSearch;
  if (kind === 'filter') return filterFieldOptionSearch;
  return groupFieldOptionSearch;
}

async function setActiveListSearchEditor(kind: ListSearchEditorKind) {
  activeListSearchEditor.value = kind;
  if (!listSearchPanelOpen.value) return;
  await router.replace({
    path: route.path,
    query: {
      ...route.query,
      list_search_tab: kind === 'list' ? undefined : kind,
    },
  });
}

async function setActiveAnalysisEditor(kind: AnalysisEditorKind) {
  activeAnalysisEditor.value = kind;
  if (!analysisPanelOpen.value) return;
  await router.replace({
    path: route.path,
    query: {
      ...route.query,
      analysis_tab: kind === 'pivotMeasure' ? undefined : kind,
    },
  });
}

function setListSearchNames(kind: ListSearchEditorKind, names: string[]) {
  const state = listSearchEditorState(kind);
  state.text.value = namesToText(names);
  clearMessage();
}

function resetListSearchDraft() {
  listColumnsText.value = listSearchBase.value.list;
  searchFiltersText.value = listSearchBase.value.filter;
  searchGroupByText.value = listSearchBase.value.group;
  listColumnDraft.value = '';
  searchFilterDraft.value = '';
  searchGroupDraft.value = '';
  setMessage('已放弃列表与搜索调整');
}

function fieldOptionsNotIn(kind: ListSearchEditorKind) {
  return fieldOptionCandidates(kind).slice(0, fieldOptionSearchState(kind).value.trim() ? 80 : 24);
}

function fieldOptionAvailableCount(kind: ListSearchEditorKind) {
  return fieldOptionCandidates(kind).length;
}

function fieldOptionCandidates(kind: ListSearchEditorKind) {
  const selected = new Set(parseNames(listSearchEditorState(kind).text.value));
  const keyword = fieldOptionSearchState(kind).value.trim().toLowerCase();
  return availableModelFields.value
    .filter((field) => !selected.has(field.name))
    .filter((field) => {
      if (!keyword) return true;
      return [field.name, field.label, field.type]
        .some((text) => String(text || '').toLowerCase().includes(keyword));
    });
}

function analysisEditorState(kind: AnalysisEditorKind) {
  if (kind === 'pivotMeasure') return { text: pivotMeasuresText, draft: pivotMeasureDraft };
  if (kind === 'pivotDimension') return { text: pivotDimensionsText, draft: pivotDimensionDraft };
  if (kind === 'graphMeasure') return { text: graphMeasuresText, draft: graphMeasureDraft };
  return { text: graphDimensionsText, draft: graphDimensionDraft };
}

function analysisEditorLabel(kind: AnalysisEditorKind) {
  const tab = analysisEditorTabs.find((item) => item.key === kind);
  return tab?.label || '分析字段';
}

function setAnalysisDraft(kind: AnalysisEditorKind, value: string) {
  analysisEditorState(kind).draft.value = value;
}

function setAnalysisDraftFromEvent(kind: AnalysisEditorKind, event: Event) {
  const target = event.target as HTMLInputElement | null;
  setAnalysisDraft(kind, target?.value || '');
}

function analysisEditorCount(kind: AnalysisEditorKind) {
  return parseNames(analysisEditorState(kind).text.value).length;
}

function analysisFieldOptionCandidates() {
  const selected = new Set(parseNames(analysisEditorState(activeAnalysisEditor.value).text.value));
  const keyword = analysisFieldOptionSearch.value.trim().toLowerCase();
  return availableModelFields.value
    .filter((field) => !selected.has(field.name))
    .filter((field) => {
      if (!keyword) return true;
      return [field.name, field.label, field.type]
        .some((text) => String(text || '').toLowerCase().includes(keyword));
    });
}

function fieldDisplayLabel(name: string) {
  const fieldName = String(name || '').trim();
  const configuredLabel = configuredListColumnLabels.value[fieldName];
  if (configuredLabel) return configuredLabel;
  const field = availableModelFields.value.find((item) => item.name === fieldName);
  if (!field) return cleanBusinessFieldLabel(fieldName, fieldName);
  return fieldOptionLabel(field);
}

function fieldOptionLabel(field: { name: string; label: string; type: string }) {
  const label = field.label || field.name;
  if (!duplicatedFieldLabels.value.has(label)) return label;
  const type = fieldTypeLabel(field.type);
  const hint = shortFieldNameHint(field.name);
  return `${label}（${[type, hint].filter(Boolean).join(' · ')}）`;
}

function fieldOptionHelpText(field: { name: string; label: string; type: string }) {
  return [field.label || field.name, field.name, field.type].filter(Boolean).join(' · ');
}

function cleanBusinessFieldLabel(name: unknown, label: unknown) {
  const fieldName = String(name || '').trim();
  let text = String(label || fieldName || '').trim();
  if (fieldName.startsWith('p1_visible_') && text.startsWith('P1可见')) {
    text = text.slice('P1可见'.length).trim();
  }
  return text || fieldName;
}

function fieldTypeLabel(type: string) {
  const value = String(type || '').trim();
  if (value === 'many2one') return '关联';
  if (value === 'many2many' || value === 'one2many') return '明细';
  if (value === 'monetary' || value === 'float' || value === 'integer') return '数值';
  if (value === 'date' || value === 'datetime') return '日期';
  if (value === 'boolean') return '是/否';
  if (value === 'selection') return '选项';
  if (value === 'text' || value === 'html') return '长文本';
  if (value === 'char') return '文本';
  return value;
}

function shortFieldNameHint(name: string) {
  const cleaned = String(name || '').trim();
  if (!cleaned) return '';
  return cleaned.length > 28 ? `${cleaned.slice(0, 12)}...${cleaned.slice(-10)}` : cleaned;
}

function fieldHelpText(name: string) {
  const fieldName = String(name || '').trim();
  const configuredLabel = configuredListColumnLabels.value[fieldName];
  if (configuredLabel) return [configuredLabel, fieldName].filter(Boolean).join(' · ');
  const field = availableModelFields.value.find((item) => item.name === fieldName);
  return field ? fieldOptionHelpText(field) : cleanBusinessFieldLabel(fieldName, fieldName);
}

function addListSearchName(kind: ListSearchEditorKind, explicitName = '') {
  const state = listSearchEditorState(kind);
  const name = String(explicitName || state.draft.value || '').trim();
  if (!name) return;
  const names = parseNames(state.text.value);
  if (!names.includes(name)) names.push(name);
  setListSearchNames(kind, names);
  if (!explicitName) state.draft.value = '';
}

function addVisibleListSearchOptions(kind: ListSearchEditorKind) {
  const names = parseNames(listSearchEditorState(kind).text.value);
  const existing = new Set(names);
  let addedCount = 0;
  fieldOptionsNotIn(kind).forEach((field) => {
    if (!existing.has(field.name)) {
      names.push(field.name);
      existing.add(field.name);
      addedCount += 1;
    }
  });
  setListSearchNames(kind, names);
  setMessage(addedCount ? `已添加 ${addedCount} 个字段` : '当前显示字段已全部添加');
}

function removeListSearchName(kind: ListSearchEditorKind, name: string) {
  setListSearchNames(kind, parseNames(listSearchEditorState(kind).text.value).filter((item) => item !== name));
}

function moveListSearchName(kind: ListSearchEditorKind, name: string, delta: number) {
  const names = parseNames(listSearchEditorState(kind).text.value);
  const index = names.indexOf(name);
  const nextIndex = index + delta;
  if (index < 0 || nextIndex < 0 || nextIndex >= names.length) return;
  const [moved] = names.splice(index, 1);
  names.splice(nextIndex, 0, moved);
  setListSearchNames(kind, names);
}

function reorderNamesByDrop(names: string[], sourceName: string, targetName: string) {
  const sourceIndex = names.indexOf(sourceName);
  const targetIndex = names.indexOf(targetName);
  if (sourceIndex < 0 || targetIndex < 0 || sourceIndex === targetIndex) return names;
  const next = [...names];
  const [moved] = next.splice(sourceIndex, 1);
  next.splice(targetIndex, 0, moved);
  return next;
}

function startChipDrag(
  area: 'list_search' | 'analysis',
  kind: ListSearchEditorKind | AnalysisEditorKind,
  name: string,
  event: DragEvent,
) {
  chipDrag.value = { area, kind, name };
  chipDropTarget.value = null;
  event.dataTransfer?.setData('text/plain', name);
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move';
}

function hoverChipDrop(
  area: 'list_search' | 'analysis',
  kind: ListSearchEditorKind | AnalysisEditorKind,
  name: string,
) {
  const current = chipDrag.value;
  if (!current || current.area !== area || current.kind !== kind || current.name === name) {
    chipDropTarget.value = null;
    return;
  }
  chipDropTarget.value = { area, kind, name };
}

function clearChipDrag() {
  chipDrag.value = null;
  chipDropTarget.value = null;
}

function startListSearchChipDrag(kind: ListSearchEditorKind, name: string, event: DragEvent) {
  startChipDrag('list_search', kind, name, event);
}

function hoverListSearchChipDrop(kind: ListSearchEditorKind, name: string) {
  hoverChipDrop('list_search', kind, name);
}

function dropListSearchChip(kind: ListSearchEditorKind, targetName: string) {
  const current = chipDrag.value;
  if (!current || current.area !== 'list_search' || current.kind !== kind) return;
  const names = parseNames(listSearchEditorState(kind).text.value);
  setListSearchNames(kind, reorderNamesByDrop(names, current.name, targetName));
  clearChipDrag();
}

function isListSearchChipDragging(kind: ListSearchEditorKind, name: string) {
  const current = chipDrag.value;
  return current?.area === 'list_search' && current.kind === kind && current.name === name;
}

function isListSearchChipDropTarget(kind: ListSearchEditorKind, name: string) {
  const current = chipDropTarget.value;
  return current?.area === 'list_search' && current.kind === kind && current.name === name;
}

function setAnalysisNames(kind: AnalysisEditorKind, names: string[]) {
  analysisEditorState(kind).text.value = namesToText(names);
  clearMessage();
}

function addAnalysisName(kind: AnalysisEditorKind, explicitName = '') {
  const state = analysisEditorState(kind);
  const name = String(explicitName || state.draft.value || '').trim();
  if (!name) return;
  const names = parseNames(state.text.value);
  if (!names.includes(name)) names.push(name);
  setAnalysisNames(kind, names);
  if (!explicitName) state.draft.value = '';
}

function addVisibleAnalysisOptions(kind: AnalysisEditorKind) {
  const names = parseNames(analysisEditorState(kind).text.value);
  const existing = new Set(names);
  let addedCount = 0;
  availableAnalysisFieldOptions.value.forEach((field) => {
    if (!existing.has(field.name)) {
      names.push(field.name);
      existing.add(field.name);
      addedCount += 1;
    }
  });
  setAnalysisNames(kind, names);
  setMessage(addedCount ? `已添加 ${addedCount} 个分析字段` : '当前显示字段已全部添加');
}

function removeAnalysisName(kind: AnalysisEditorKind, name: string) {
  setAnalysisNames(kind, parseNames(analysisEditorState(kind).text.value).filter((item) => item !== name));
}

function moveAnalysisName(kind: AnalysisEditorKind, name: string, delta: number) {
  const names = parseNames(analysisEditorState(kind).text.value);
  const index = names.indexOf(name);
  const nextIndex = index + delta;
  if (index < 0 || nextIndex < 0 || nextIndex >= names.length) return;
  const [moved] = names.splice(index, 1);
  names.splice(nextIndex, 0, moved);
  setAnalysisNames(kind, names);
}

function startAnalysisChipDrag(kind: AnalysisEditorKind, name: string, event: DragEvent) {
  startChipDrag('analysis', kind, name, event);
}

function hoverAnalysisChipDrop(kind: AnalysisEditorKind, name: string) {
  hoverChipDrop('analysis', kind, name);
}

function dropAnalysisChip(kind: AnalysisEditorKind, targetName: string) {
  const current = chipDrag.value;
  if (!current || current.area !== 'analysis' || current.kind !== kind) return;
  const names = parseNames(analysisEditorState(kind).text.value);
  setAnalysisNames(kind, reorderNamesByDrop(names, current.name, targetName));
  clearChipDrag();
}

function isAnalysisChipDragging(kind: AnalysisEditorKind, name: string) {
  const current = chipDrag.value;
  return current?.area === 'analysis' && current.kind === kind && current.name === name;
}

function isAnalysisChipDropTarget(kind: AnalysisEditorKind, name: string) {
  const current = chipDropTarget.value;
  return current?.area === 'analysis' && current.kind === kind && current.name === name;
}

async function loadListSearchConfig() {
  if (!currentModel.value) return;
  listSearchBusy.value = true;
  error.value = '';
  clearMessage();
  try {
    const result = await auditBusinessListSearchConfig({
      model: currentModel.value,
      action_id: scopeAction.value,
      view_id: scopeView.value,
      role_key: scopeRole.value,
    });
    listSearchAudit.value = result;
    const configuredListColumns = result.business_config_list_columns || [];
    const configuredSearchFilters = result.business_config_search_filters || [];
    const configuredSearchGroupBy = result.business_config_search_group_by || [];
    const suggestedListColumns = configuredListColumns.length ? [] : result.suggested_list_columns || [];
    const suggestedSearchFilters = (configuredSearchFilters.length || configuredSearchGroupBy.length) ? [] : result.suggested_search_filters || [];
    const suggestedSearchGroupBy = (configuredSearchFilters.length || configuredSearchGroupBy.length) ? [] : result.suggested_search_group_by || [];
    listColumnsText.value = namesToText(configuredListColumns.length ? configuredListColumns : suggestedListColumns);
    searchFiltersText.value = namesToText(configuredSearchFilters.length ? configuredSearchFilters : suggestedSearchFilters);
    searchGroupByText.value = namesToText(configuredSearchGroupBy.length ? configuredSearchGroupBy : suggestedSearchGroupBy);
    listSearchBase.value = {
      list: normalizeNamesText(namesToText(configuredListColumns)),
      filter: normalizeNamesText(namesToText(configuredSearchFilters)),
      group: normalizeNamesText(namesToText(configuredSearchGroupBy)),
    };
    activeListSearchEditor.value = requestedListSearchTab.value;
    analysisPanelOpen.value = false;
    approvalPanelOpen.value = false;
    listSearchPanelOpen.value = true;
    await focusActiveEditorPanel();
    if (!configuredListColumns.length && suggestedListColumns.length) {
      setMessage('已按当前页面生成列表草稿', '调整后点击保存设置，才会发布为正式业务配置');
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '列表与搜索设置读取失败';
  } finally {
    listSearchBusy.value = false;
  }
}

function resetAnalysisDraft() {
  pivotMeasuresText.value = analysisBase.value.pivotMeasures;
  pivotDimensionsText.value = analysisBase.value.pivotDimensions;
  graphMeasuresText.value = analysisBase.value.graphMeasures;
  graphDimensionsText.value = analysisBase.value.graphDimensions;
  graphType.value = analysisBase.value.graphType || 'bar';
  pivotMeasureDraft.value = '';
  pivotDimensionDraft.value = '';
  graphMeasureDraft.value = '';
  graphDimensionDraft.value = '';
  setMessage('已放弃分析视图调整');
}

async function loadAnalysisConfig() {
  if (!currentModel.value) return;
  listSearchBusy.value = true;
  error.value = '';
  clearMessage();
  try {
    const result = await auditBusinessAnalysisConfig({
      model: currentModel.value,
      action_id: scopeAction.value,
      view_id: scopeView.value,
      role_key: scopeRole.value,
    });
    analysisAudit.value = result;
    const configuredPivotMeasures = result.pivot_measures || [];
    const configuredPivotDimensions = result.pivot_dimensions || [];
    const configuredGraphMeasures = result.graph_measures || [];
    const configuredGraphDimensions = result.graph_dimensions || [];
    const suggestedPivotMeasures = (configuredPivotMeasures.length || configuredPivotDimensions.length) ? [] : result.suggested_pivot_measures || [];
    const suggestedPivotDimensions = (configuredPivotMeasures.length || configuredPivotDimensions.length) ? [] : result.suggested_pivot_dimensions || [];
    const suggestedGraphMeasures = (configuredGraphMeasures.length || configuredGraphDimensions.length) ? [] : result.suggested_graph_measures || [];
    const suggestedGraphDimensions = (configuredGraphMeasures.length || configuredGraphDimensions.length) ? [] : result.suggested_graph_dimensions || [];
    const configuredGraphType = (configuredGraphMeasures.length || configuredGraphDimensions.length) ? result.graph_type || 'bar' : '';
    pivotMeasuresText.value = namesToText(configuredPivotMeasures.length ? configuredPivotMeasures : suggestedPivotMeasures);
    pivotDimensionsText.value = namesToText(configuredPivotDimensions.length ? configuredPivotDimensions : suggestedPivotDimensions);
    graphMeasuresText.value = namesToText(configuredGraphMeasures.length ? configuredGraphMeasures : suggestedGraphMeasures);
    graphDimensionsText.value = namesToText(configuredGraphDimensions.length ? configuredGraphDimensions : suggestedGraphDimensions);
    graphType.value = configuredGraphType || result.suggested_graph_type || result.graph_type || 'bar';
    analysisBase.value = {
      pivotMeasures: normalizeNamesText(namesToText(configuredPivotMeasures)),
      pivotDimensions: normalizeNamesText(namesToText(configuredPivotDimensions)),
      graphMeasures: normalizeNamesText(namesToText(configuredGraphMeasures)),
      graphDimensions: normalizeNamesText(namesToText(configuredGraphDimensions)),
      graphType: configuredGraphType || 'bar',
    };
    listSearchPanelOpen.value = false;
    approvalPanelOpen.value = false;
    analysisPanelOpen.value = true;
    activeAnalysisEditor.value = requestedAnalysisTab.value;
    await focusActiveEditorPanel();
    if (
      (!configuredPivotMeasures.length && !configuredPivotDimensions.length && (suggestedPivotMeasures.length || suggestedPivotDimensions.length))
      || (!configuredGraphMeasures.length && !configuredGraphDimensions.length && (suggestedGraphMeasures.length || suggestedGraphDimensions.length))
    ) {
      setMessage('已按当前页面生成分析草稿', '调整后点击保存设置，才会发布为正式业务配置');
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '分析视图设置读取失败';
  } finally {
    listSearchBusy.value = false;
  }
}

function applyApprovalAudit(result: ApprovalPolicyConfigPayload) {
  approvalAudit.value = result;
  const policy = result.policy;
  const form = {
    approval_required: Boolean(policy.approval_required),
    mode: String(policy.mode || 'none'),
    manager_scope_key: String(policy.manager_scope_key || ''),
  };
  approvalForm.value = { ...form };
  approvalBase.value = { ...form };
  approvalSteps.value = (policy.steps || [])
    .filter((step) => step.active !== false)
    .map((step) => approvalStepFromPayload(step));
  approvalStepsBaseJson.value = approvalStepsJson.value;
}

function resetApprovalDraft() {
  approvalForm.value = { ...approvalBase.value };
  const steps = approvalAudit.value?.policy.steps || [];
  approvalSteps.value = steps.filter((step) => step.active !== false).map((step) => approvalStepFromPayload(step));
  approvalStepsBaseJson.value = approvalStepsJson.value;
  setMessage('已放弃审批设置调整');
}

function onApprovalRequiredChange() {
  if (!approvalForm.value.approval_required) {
    approvalForm.value.mode = 'none';
    return;
  }
  if (!approvalForm.value.mode || approvalForm.value.mode === 'none') {
    approvalForm.value.mode = 'single';
  }
  if (!approvalSteps.value.length) {
    addApprovalStep();
  }
}

function enableApprovalWithDefaultStep() {
  approvalForm.value.approval_required = true;
  onApprovalRequiredChange();
}

async function loadApprovalConfig() {
  if (!currentModel.value) return;
  approvalLoading.value = true;
  error.value = '';
  clearMessage();
  try {
    const result = await loadApprovalPolicyConfig({ model: currentModel.value });
    applyApprovalAudit(result);
    listSearchPanelOpen.value = false;
    analysisPanelOpen.value = false;
    approvalPanelOpen.value = true;
    await focusActiveEditorPanel();
  } catch (err) {
    error.value = err instanceof Error ? err.message : '审批设置读取失败';
  } finally {
    approvalLoading.value = false;
  }
}

async function saveApprovalConfig() {
  if (!currentModel.value || !hasApprovalDraftChanges.value) return false;
  if (approvalValidationMessage.value) {
    error.value = approvalValidationMessage.value;
    return false;
  }
  approvalLoading.value = true;
  error.value = '';
  clearMessage();
  try {
    const stepDraftChanged = approvalStepsJson.value !== approvalStepsBaseJson.value;
    const stepPayload: Parameters<typeof saveApprovalPolicySteps>[0]['steps'] = approvalSteps.value.map((step) => ({
      id: step.id > 0 ? step.id : undefined,
      name: String(step.name || '').trim(),
      approval_scope_key: String(step.approval_scope_key || '').trim(),
      active: true,
      amount_min: normalizeAmountText(step.amount_min) || false,
      amount_max: normalizeAmountText(step.amount_max) || false,
      condition_note: String(step.condition_note || '').trim(),
      note: String(step.note || '').trim(),
    }));
    const nextMode = approvalForm.value.approval_required
      ? String(approvalForm.value.mode || 'single')
      : 'none';
    let result = await saveApprovalPolicyConfig({
      model: currentModel.value,
      approval_required: approvalForm.value.approval_required,
      mode: nextMode,
      manager_scope_key: approvalForm.value.manager_scope_key || '',
    });
    if (stepDraftChanged) {
      result = await saveApprovalPolicySteps({
        model: currentModel.value,
        steps: approvalForm.value.approval_required ? stepPayload : [],
      });
    }
    applyApprovalAudit(result);
    await loadSurface();
    setMessage('审批设置已保存', result.runtime_approval_required ? '当前业务提交后会进入审批。' : '当前业务提交后无需审批。');
    return true;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '审批设置保存失败';
    return false;
  } finally {
    approvalLoading.value = false;
  }
}

function normalizeAmountText(value: unknown): string {
  const text = String(value ?? '').trim();
  if (!text) return '';
  const parsed = Number(text);
  if (!Number.isFinite(parsed) || parsed < 0) return text;
  return String(parsed);
}

function approvalStepFromPayload(step: ApprovalPolicyConfigPayload['policy']['steps'][number]): ApprovalStepDraft {
  return {
    key: `step-${step.id || `tmp-${approvalStepTempId += 1}`}`,
    id: Number(step.id || 0),
    name: String(step.name || ''),
    approval_scope_key: String(step.approval_scope_key || ''),
    active: step.active !== false,
    amount_min: step.amount_min ? String(step.amount_min) : '',
    amount_max: step.amount_max ? String(step.amount_max) : '',
    condition_note: String(step.condition_note || ''),
    note: String(step.note || ''),
  };
}

function defaultApprovalScopeKey() {
  return approvalForm.value.manager_scope_key || approvalScopeOptions.value[0]?.value || '';
}

function addApprovalStep() {
  approvalSteps.value.push({
    key: `new-step-${approvalStepTempId += 1}`,
    id: 0,
    name: `审批步骤${approvalSteps.value.length + 1}`,
    approval_scope_key: defaultApprovalScopeKey(),
    active: true,
    amount_min: '',
    amount_max: '',
    condition_note: '',
    note: '',
  });
}

function removeApprovalStep(index: number) {
  approvalSteps.value.splice(index, 1);
}

function startApprovalStepDrag(index: number, event: DragEvent) {
  approvalStepDragIndex.value = index;
  approvalStepDropIndex.value = index;
  event.dataTransfer?.setData('text/plain', String(index));
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
  }
}

function dropApprovalStep(index: number) {
  const from = approvalStepDragIndex.value;
  if (from === null || from === index) {
    clearApprovalStepDrag();
    return;
  }
  const next = [...approvalSteps.value];
  const [item] = next.splice(from, 1);
  next.splice(index, 0, item);
  approvalSteps.value = next;
  clearApprovalStepDrag();
}

function clearApprovalStepDrag() {
  approvalStepDragIndex.value = null;
  approvalStepDropIndex.value = null;
}

async function saveListSearchConfig() {
  if (!currentModel.value || !hasListSearchDraftChanges.value) return false;
  listSearchSaving.value = true;
  error.value = '';
  clearMessage();
  try {
    const result = await saveBusinessListSearchConfig({
      model: currentModel.value,
      action_id: scopeAction.value,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      list_columns: parseNames(listColumnsText.value),
      search_filters: parseNames(searchFiltersText.value),
      search_group_by: parseNames(searchGroupByText.value),
      publish: true,
    });
    await loadSurface();
    await loadListSearchConfig();
    if (coverageScan.value) {
      await rescanCoverageAfterBootstrap();
    }
    if (versionsPanelOpen.value && activeVersionSection.value === 'list_search') {
      await loadVersions('list_search');
    }
    setMessage('列表与搜索配置已保存并发布', `已保存 ${result.saved_count} 个业务配置，刷新页面后按新配置生效`);
    return true;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '列表与搜索设置保存失败';
    return false;
  } finally {
    listSearchSaving.value = false;
  }
}

async function saveAnalysisConfig() {
  if (!currentModel.value || !hasAnalysisDraftChanges.value) return false;
  listSearchSaving.value = true;
  error.value = '';
  clearMessage();
  try {
    const result = await saveBusinessAnalysisConfig({
      model: currentModel.value,
      action_id: scopeAction.value,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      pivot_measures: parseNames(pivotMeasuresText.value),
      pivot_dimensions: parseNames(pivotDimensionsText.value),
      graph_measures: parseNames(graphMeasuresText.value),
      graph_dimensions: parseNames(graphDimensionsText.value),
      graph_type: graphType.value || 'bar',
      publish: true,
    });
    await loadSurface();
    await loadAnalysisConfig();
    if (coverageScan.value) {
      await rescanCoverageAfterBootstrap();
    }
    if (versionsPanelOpen.value && activeVersionSection.value === 'analysis') {
      await loadVersions('analysis');
    }
    setMessage('分析视图配置已保存并发布', `已保存 ${result.saved_count} 个业务配置，刷新页面后按新配置生效`);
    return true;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '分析视图设置保存失败';
    return false;
  } finally {
    listSearchSaving.value = false;
  }
}

async function previewListSearchConfig() {
  if (hasListSearchDraftChanges.value) {
    const saved = await saveListSearchConfig();
    if (!saved) return;
  }
  await previewSelectedRuntimeRoute();
}

async function previewAnalysisConfig() {
  if (hasAnalysisDraftChanges.value) {
    const saved = await saveAnalysisConfig();
    if (!saved) return;
  }
  await previewSelectedRuntimeRoute();
}

function versionParams(viewType?: string) {
  return {
    model: currentModel.value,
    view_type: viewType,
    action_id: scopeAction.value,
    view_id: scopeView.value,
    role_key: scopeRole.value,
  };
}

async function loadVersions(sectionKey: string) {
  if (!currentModel.value) return;
  activeVersionSection.value = sectionKey === 'form' || sectionKey === 'list_search' || sectionKey === 'analysis'
    ? sectionKey
    : '';
  versionsLoading.value = true;
  error.value = '';
  clearMessage();
  try {
    if (sectionKey === 'form') {
      const result = await loadBusinessConfigContractVersions(versionParams('form'));
      versionTitle.value = '表单配置版本';
      versionContracts.value = result.contracts || [];
    } else if (sectionKey === 'list_search') {
      const [treeResult, searchResult] = await Promise.all([
        loadBusinessConfigContractVersions(versionParams('tree')),
        loadBusinessConfigContractVersions(versionParams('search')),
      ]);
      versionTitle.value = '列表/搜索配置版本';
      versionContracts.value = [...(treeResult.contracts || []), ...(searchResult.contracts || [])];
    } else {
      const results = await Promise.all(
        ['pivot', 'graph', 'calendar', 'dashboard'].map((viewType) => (
          loadBusinessConfigContractVersions(versionParams(viewType))
        )),
      );
      versionTitle.value = '分析视图配置版本';
      versionContracts.value = results.flatMap((result) => result.contracts || []);
    }
    versionsPanelOpen.value = true;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '配置版本读取失败';
  } finally {
    versionsLoading.value = false;
  }
}

async function rollbackContractFromWorkbench(
  contract: BusinessConfigContractVersionsPayload['contracts'][number],
  versionNo?: number,
) {
  if (!contract?.name || (versionNo ? versionNo === contract.version_no : contract.versions.length < 2)) return;
  const targetText = versionNo ? `v${versionNo}` : '上一版';
  const confirmed = window.confirm([
    `确认恢复${versionContractDisplayName(contract)}的${targetText}？`,
    versionContractImpactText(contract),
    '恢复后会立即发布为新的当前配置，刷新业务页面后生效。',
  ].join('\n'));
  if (!confirmed) return;
  listSearchSaving.value = true;
  error.value = '';
  clearMessage();
  try {
    const result = await rollbackBusinessConfigContract({
      name: contract.name,
      model: contract.model,
      view_type: contract.view_type,
      action_id: contract.action_id || undefined,
      view_id: contract.view_id || undefined,
      role_key: contract.role_key || undefined,
      version_no: versionNo,
    });
    await loadSurface();
    await loadVersions(sectionKeyForViewType(contract.view_type));
    if (coverageScan.value) {
      await rescanCoverageAfterBootstrap();
    }
    setMessage('配置已回滚并发布', `已回滚到 v${result.rolled_back_to_version}，刷新页面后按该版本生效`);
  } catch (err) {
    error.value = err instanceof Error ? err.message : '业务配置回滚失败';
  } finally {
    listSearchSaving.value = false;
  }
}

function sectionKeyForViewType(viewType: string) {
  if (viewType === 'form') return 'form';
  if (viewType === 'tree' || viewType === 'list' || viewType === 'search') return 'list_search';
  if (['pivot', 'graph', 'calendar', 'dashboard'].includes(viewType)) return 'analysis';
  return 'list_search';
}

function navNodeMenuId(node: Record<string, unknown>) {
  const meta = node.meta && typeof node.meta === 'object' ? node.meta as Record<string, unknown> : {};
  for (const candidate of [node.menu_id, meta.menu_id, node.id]) {
    const parsed = Number(candidate || 0);
    if (Number.isInteger(parsed) && parsed > 0) return parsed;
  }
  return 0;
}

function navNodeActionId(node: Record<string, unknown>) {
  const meta = node.meta && typeof node.meta === 'object' ? node.meta as Record<string, unknown> : {};
  for (const candidate of [node.action_id, meta.action_id]) {
    const parsed = Number(candidate || 0);
    if (Number.isInteger(parsed) && parsed > 0) return parsed;
  }
  return 0;
}

function navNodeModel(node: Record<string, unknown>) {
  const meta = node.meta && typeof node.meta === 'object' ? node.meta as Record<string, unknown> : {};
  return String(node.model || meta.model || '').trim();
}

function navNodeLabel(node: Record<string, unknown>) {
  const meta = node.meta && typeof node.meta === 'object' ? node.meta as Record<string, unknown> : {};
  return String(node.name || node.label || node.title || meta.name || meta.label || '').trim();
}

function findMenuConfigNavigationEntry(items: unknown[]): { menuId: number; actionId: number } | null {
  for (const item of Array.isArray(items) ? items : []) {
    if (!item || typeof item !== 'object') continue;
    const node = item as Record<string, unknown>;
    const model = navNodeModel(node);
    const label = navNodeLabel(node);
    const menuId = navNodeMenuId(node);
    const actionId = navNodeActionId(node);
    if (label === '菜单配置' && model === BUSINESS_CONFIG_MODELS.menuConfigPolicy && menuId && actionId) {
      return { menuId, actionId };
    }
    const childMatch = findMenuConfigNavigationEntry(Array.isArray(node.children) ? node.children : []);
    if (childMatch) return childMatch;
  }
  return null;
}

function menuConfigWorkbenchReturnQuery() {
  const menuEntry = findMenuConfigNavigationEntry(session.menuTree || []);
  return {
    menu_id: menuEntry?.menuId ? String(menuEntry.menuId) : undefined,
    action_id: menuEntry?.actionId ? String(menuEntry.actionId) : undefined,
    root_menu_xmlid: route.query.root_menu_xmlid || undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig]: '1',
    [BUSINESS_CONFIG_ROUTE_FLAGS.openPages]: route.query[BUSINESS_CONFIG_ROUTE_FLAGS.openPages] || '1',
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnModel]: currentModel.value || undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnActionId]: scopeAction.value ? String(scopeAction.value) : undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnMenuId]: route.query.menu_id || undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnPageLabel]: selectedPageLabel.value || undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnViewId]: scopeView.value ? String(scopeView.value) : undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnRoleKey]: scopeRole.value || undefined,
  };
}

function openMenuConfig() {
  router.push({
    path: '/admin/menu-config',
    query: menuConfigWorkbenchReturnQuery(),
  });
}

function openCreateMenuConfig() {
  router.push({
    path: '/admin/menu-config',
    query: {
      ...menuConfigWorkbenchReturnQuery(),
      create_menu: '1',
    },
  });
}

function openApprovalConfig(section: BusinessConfigSurfacePayload['sections'][number]) {
  const path = String(section.route?.path || '').trim();
  if (!path) return;
  router.push({
    path,
    query: {
      ...(section.route?.query || {}),
      [BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig]: '1',
      root_menu_xmlid: route.query.root_menu_xmlid || undefined,
      page_label: selectedPageLabel.value || undefined,
    },
  });
}

function openFormConfig() {
  if (!canOpenDesigner.value) return;
  router.push({
    path: `/f/${encodeURIComponent(currentModel.value)}/new`,
    query: {
      action_id: scopeAction.value ? String(scopeAction.value) : undefined,
      menu_id: route.query.menu_id || undefined,
      root_menu_xmlid: route.query.root_menu_xmlid || undefined,
      view_id: scopeView.value ? String(scopeView.value) : undefined,
      role_key: scopeRole.value || undefined,
      page_label: selectedPageLabel.value || undefined,
      config_mode: BUSINESS_CONFIG_MODES.lowCode,
      [BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig]: '1',
    },
  });
}

async function clearConsumedOpenIntent(keys: string[]) {
  const params = new URLSearchParams(window.location.search);
  let changed = false;
  keys.forEach((key) => {
    if (params.has(key)) {
      params.delete(key);
      changed = true;
    }
  });
  if (!changed) return;
  const query = params.toString();
  window.history.replaceState(window.history.state, '', `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`);
}

function replaceWorkbenchQuerySilently(nextValues: Record<string, string | number | undefined>) {
  const params = new URLSearchParams(window.location.search);
  Object.entries(nextValues).forEach(([key, value]) => {
    const text = String(value ?? '').trim();
    if (text) {
      params.set(key, text);
    } else {
      params.delete(key);
    }
  });
  const query = params.toString();
  window.history.replaceState(window.history.state, '', `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`);
}

onMounted(() => {
  void (async () => {
    const openPageListOnMount = shouldOpenPageList.value;
    const openFormConfigOnMount = shouldOpenFormConfig.value;
    const openListSearchOnMount = shouldOpenListSearch.value;
    const openAnalysisOnMount = shouldOpenAnalysis.value;
    await loadSurface();
    if (openPageListOnMount) {
      await scanSystemRootCoverage();
    }
    if (openFormConfigOnMount && currentModel.value && scopeAction.value) {
      await clearConsumedOpenIntent(['open_form_config']);
      const matched = (coverageScan.value?.items || []).find(coverageRowMatchesScope);
      if (matched) {
        await focusScanRow(matched);
      } else {
        await loadSurface();
      }
    }
    if (openListSearchOnMount && currentModel.value) {
      await clearConsumedOpenIntent(['open_list_search']);
      await loadListSearchConfig();
    }
    if (openAnalysisOnMount && currentModel.value) {
      await clearConsumedOpenIntent(['open_analysis']);
      await loadAnalysisConfig();
    }
  })();
});
</script>

<style scoped>
.business-config-page {
  display: grid;
  gap: 12px;
  padding-bottom: 18px;
}

.business-config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
}

.eyebrow {
  margin: 0 0 4px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

h1 {
  margin: 0;
  font-size: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.ghost {
  min-height: 34px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 12px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  cursor: pointer;
}

.ghost.primary {
  border-color: var(--sc-app-accent);
  background: var(--sc-app-accent);
  color: var(--sc-app-accent-contrast);
}

.ghost:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.ghost.small {
  min-height: 30px;
  font-size: 13px;
}

.status,
.workbench-start,
.scope-panel,
.loading-state,
.scan-panel {
  margin: 0 18px;
}

.status {
  display: grid;
  gap: 3px;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.status small {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.status.error {
  border: 1px solid var(--sc-app-danger-border);
  background: var(--sc-app-danger-bg);
  color: var(--sc-app-danger-text);
}

.status.ok {
  border: 1px solid var(--sc-app-success-border);
  background: var(--sc-app-success-bg);
  color: var(--sc-app-success-text);
}

.workbench-start,
.workbench-start-status,
.workbench-status-rail {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
}

.workbench-start {
  grid-template-columns: minmax(0, 1fr) minmax(280px, 420px);
  align-items: stretch;
}

.workbench-start-main {
  min-width: 0;
  display: grid;
  gap: 16px;
}

.workbench-start-lead {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.workbench-start-config {
  min-width: 0;
  display: grid;
  gap: 12px;
}

.workbench-start-copy {
  min-width: 0;
  display: grid;
  gap: 5px;
}

.workbench-start-copy span,
.workbench-start-copy em {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  font-style: normal;
}

.workbench-start-copy strong {
  min-width: 0;
  color: var(--sc-app-text-primary);
  font-size: 18px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workbench-start-actions {
  flex: none;
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.workbench-start-status,
.workbench-status-rail {
  background: var(--sc-app-bg);
}

.workbench-status-rail {
  position: sticky;
  top: 12px;
  align-content: start;
}

.delivery-readiness-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.delivery-readiness-head div {
  display: grid;
  gap: 2px;
}

.delivery-readiness-head span,
.delivery-readiness-head em {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  font-style: normal;
}

.delivery-readiness-head strong {
  color: var(--sc-app-text-primary);
  font-size: 16px;
}

.delivery-readiness-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
}

.delivery-readiness-grid--compact,
.delivery-readiness-grid--rail {
  grid-template-columns: minmax(0, 1fr);
}

.delivery-readiness-item {
  min-width: 0;
  min-height: 74px;
  display: grid;
  align-content: center;
  gap: 5px;
  border: 1px solid var(--sc-app-success-border);
  border-radius: 8px;
  padding: 10px 12px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-primary);
  cursor: pointer;
  text-align: left;
  font: inherit;
}

.delivery-readiness-item--pending {
  border-color: var(--sc-app-warning-border);
  background: var(--sc-app-warning-bg);
}

.delivery-readiness-item span,
.delivery-readiness-item em {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delivery-readiness-item span {
  color: var(--sc-app-text-primary);
  font-size: 13px;
  font-weight: 600;
}

.delivery-readiness-item strong {
  color: var(--sc-app-success-text);
  font-size: 12px;
}

.delivery-readiness-item--pending strong {
  color: var(--sc-app-warning-text);
}

.delivery-readiness-item em {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  font-style: normal;
}

.config-card h2,
.edit-panel h2,
.version-panel h2 {
  margin: 0;
  font-size: 15px;
}

.scope-panel {
  display: grid;
  grid-template-columns: minmax(180px, 1.2fr) repeat(2, minmax(96px, 0.5fr)) minmax(140px, 0.8fr) auto;
  align-items: end;
  gap: 8px;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.scope-panel label {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.scope-panel input {
  min-width: 0;
  min-height: 32px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 8px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-primary);
}

.loading-state {
  padding: 18px;
  color: var(--sc-app-text-secondary);
}

.scan-panel {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
}

.scan-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.page-search {
  flex: 1 1 320px;
  min-width: 220px;
  display: grid;
  gap: 4px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.page-search input {
  width: 100%;
  min-height: 34px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 10px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-primary);
  font-size: 13px;
}

.page-type-tabs {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-bg);
}

.page-type-tabs button {
  min-height: 28px;
  border: 0;
  border-radius: 6px;
  padding: 0 10px;
  background: transparent;
  color: var(--sc-app-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
}

.page-type-tabs button.active {
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  box-shadow: 0 0 0 1px var(--sc-app-border);
}

.scan-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.scan-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  font-size: 13px;
}

.scan-summary {
  color: var(--sc-app-text-primary);
}

.config-workspace {
  display: grid;
  grid-template-columns: minmax(260px, 300px) minmax(0, 1fr) minmax(230px, 280px);
  gap: 12px;
  align-items: start;
}

.workbench-status-snapshot {
  display: grid;
  gap: 4px;
  border-top: 1px solid var(--sc-app-border);
  padding-top: 10px;
}

.workbench-status-empty {
  border: 1px dashed var(--sc-app-border);
  border-radius: 6px;
  padding: 10px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.workbench-status-snapshot span,
.workbench-status-snapshot em {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  font-style: normal;
}

.workbench-status-snapshot strong {
  color: var(--sc-app-text-primary);
  font-size: 18px;
  font-variant-numeric: tabular-nums;
}

.page-picker-panel,
.page-config-panel {
  min-width: 0;
  display: grid;
  gap: 10px;
}

.page-picker-panel {
  align-content: start;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-bg);
  overflow: hidden;
}

.page-picker-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  min-height: 54px;
  padding: 12px;
  border-bottom: 1px solid var(--sc-app-border);
  color: var(--sc-app-text-primary);
}

.page-picker-head > div {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.page-picker-head span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.page-picker-head strong {
  color: var(--sc-app-text-primary);
  font-size: 14px;
}

.page-picker-head em {
  max-width: 128px;
  overflow: hidden;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  padding: 3px 8px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-secondary);
  font-size: 11px;
  font-style: normal;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-page-overview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-bg);
}

.selected-page-overview-side {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  min-width: 0;
}

.selected-page-overview > div:first-child {
  min-width: 0;
  display: grid;
  gap: 3px;
}

.selected-page-overview span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.selected-page-overview strong {
  color: var(--sc-app-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-page-overview-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
}

.selected-page-overview-meta span {
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  padding: 0 8px;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  background: var(--sc-app-panel-muted);
}

.scan-list {
  display: grid;
  gap: 0;
}

.page-picker-panel .scan-list {
  max-height: clamp(260px, calc(100vh - 360px), 520px);
  overflow-y: auto;
  overscroll-behavior: contain;
}

.scan-row {
  display: grid;
  grid-template-columns: minmax(220px, 1.2fr) minmax(220px, 1fr) auto;
  align-items: center;
  gap: 10px 14px;
  padding: 10px 12px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.scan-row--selected {
  border-color: var(--sc-app-accent);
  background: var(--sc-app-panel-muted);
  box-shadow: inset 3px 0 0 var(--sc-app-accent);
}

.scan-row--clickable {
  cursor: pointer;
}

.scan-row--clickable:hover {
  border-color: var(--sc-app-accent);
  background: var(--sc-app-panel-muted);
}

.scan-row-main {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.scan-row strong,
.scan-row-main strong {
  color: var(--sc-app-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scan-row-main span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scan-row-meta,
.scan-row-admin-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}

.scan-row-current {
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--sc-app-accent);
  border-radius: 999px;
  padding: 0 10px;
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.scan-row-meta span,
.scan-row-admin-actions span {
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  padding: 0 8px;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  background: var(--sc-app-panel-muted);
  font-size: 12px;
}

.scan-row-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  white-space: nowrap;
}

.page-picker-panel .scan-row {
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px 10px;
  align-items: start;
  border: 0;
  border-bottom: 1px solid var(--sc-app-border);
  border-radius: 0;
  padding: 12px;
  background: transparent;
}

.page-picker-panel .scan-row-main strong {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  text-overflow: ellipsis;
  white-space: normal;
  word-break: break-word;
}

.page-picker-panel .scan-row-actions {
  align-self: start;
  justify-content: flex-end;
  flex-wrap: nowrap;
  white-space: normal;
}

.page-picker-panel .scan-row-meta {
  grid-column: 1 / -1;
  gap: 4px;
}

.page-picker-panel .scan-row-meta span {
  min-height: auto;
  border: 0;
  padding: 0;
  background: transparent;
}

.page-picker-panel .scan-row-admin-actions {
  grid-column: 1 / -1;
}

.page-picker-panel .scan-row--selected {
  background: var(--sc-app-panel-muted);
}

.page-picker-panel .scan-row:last-child {
  border-bottom: 0;
}

.scan-panel--admin .scan-row {
  display: flex;
  flex-wrap: wrap;
}

.snapshot-input {
  width: 100%;
  min-height: 120px;
  resize: vertical;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 10px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-primary);
  font: inherit;
  font-size: 12px;
  line-height: 1.5;
}

.snapshot-diff-list {
  display: grid;
  gap: 6px;
}

.snapshot-remediation-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.snapshot-diff-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
  padding: 8px 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.snapshot-diff-row strong {
  color: var(--sc-app-text-primary);
}

.link-button {
  border: 0;
  padding: 0;
  background: transparent;
  color: var(--sc-app-accent);
  cursor: pointer;
  font: inherit;
}

.link-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.section-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.section-grid--start {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.config-card {
  min-width: 0;
  display: grid;
  grid-template-rows: auto 1fr auto auto;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
}

.config-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.config-card-head > div {
  min-width: 0;
  display: grid;
  gap: 3px;
}

.config-card-head span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.config-status-badge {
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--sc-app-success-border);
  border-radius: 999px;
  padding: 0 9px;
  background: var(--sc-app-success-bg);
  color: var(--sc-app-success-text);
  font-size: 12px;
  white-space: nowrap;
}

.config-status-badge.config-status--empty {
  border-color: var(--sc-app-border);
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-secondary);
}

.config-task-impact {
  display: grid;
  gap: 5px;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.config-task-impact span,
.config-task-impact em {
  min-width: 0;
}

.config-task-impact em {
  color: var(--sc-app-text-muted);
  font-size: 12px;
  font-style: normal;
}

.config-card-meta {
  min-width: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.config-card-meta span {
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  padding: 0 8px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.config-card-actions {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.edit-panel {
  display: grid;
  gap: 12px;
  margin: 0 18px;
  padding: 14px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
}

.config-editor-panel {
  grid-template-columns: 220px minmax(0, 1fr);
  align-items: start;
}

.config-editor-panel .edit-panel-head,
.config-editor-panel .edit-meta,
.config-editor-panel .preference-list {
  grid-column: 1 / -1;
}

.config-editor-panel .edit-panel-head {
  min-height: 48px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--sc-app-border);
}

.version-panel {
  display: grid;
  gap: 12px;
  margin: 0 18px;
  padding: 14px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
}

.edit-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.edit-panel-actions {
  flex: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.edit-panel p {
  margin: 4px 0 0;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.approval-config-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 10px;
  align-items: stretch;
}

.approval-rule-panel {
  position: sticky;
  top: 12px;
  display: grid;
  align-content: start;
  gap: 12px;
  min-width: 0;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  padding: 12px;
  background: var(--sc-app-bg);
}

.approval-guide,
.approval-impact-summary {
  display: grid;
  gap: 4px;
  padding: 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.approval-guide strong,
.approval-impact-summary strong {
  color: var(--sc-app-text-primary);
  font-size: 13px;
}

.approval-rule-head {
  display: grid;
  gap: 3px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--sc-app-border);
}

.approval-rule-head strong {
  color: var(--sc-app-text-primary);
  font-size: 14px;
}

.approval-rule-head span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.approval-panel .approval-rule-summary {
  grid-column: auto;
  display: grid;
  gap: 6px;
  padding-top: 10px;
  border-top: 1px solid var(--sc-app-border);
}

.approval-panel .edit-panel-actions {
  grid-column: 1 / -1;
  justify-self: end;
}

.approval-config-grid label {
  min-width: 0;
  display: grid;
  gap: 5px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.approval-config-grid select,
.approval-step-row input,
.approval-step-row select {
  min-width: 0;
  min-height: 34px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 8px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-primary);
}

.approval-steps {
  display: grid;
  gap: 10px;
  min-width: 0;
  min-height: 360px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  padding: 14px;
  background: var(--sc-app-surface);
  box-shadow: inset 0 0 0 1px rgb(148 163 184 / 6%);
}

.approval-steps--disabled {
  background: var(--sc-app-panel-muted);
}

.approval-steps header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.approval-steps header div {
  display: grid;
  gap: 2px;
}

.approval-steps header strong {
  font-size: 14px;
}

.approval-steps header span,
.approval-step-empty {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.approval-step-table {
  overflow-x: auto;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-surface);
}

.approval-step-table-head,
.approval-step-row {
  display: grid;
  grid-template-columns: 44px minmax(180px, 1.2fr) minmax(190px, 1.1fr) minmax(118px, 0.7fr) minmax(118px, 0.7fr) 42px;
  gap: 8px;
  align-items: center;
  min-width: 780px;
}

.approval-step-table-head {
  min-height: 34px;
  padding: 0 8px;
  border-bottom: 1px solid var(--sc-app-border);
  background: var(--sc-app-bg);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.approval-step-row {
  min-height: 46px;
  padding: 6px 8px;
  border-bottom: 1px solid var(--sc-app-border);
  background: var(--sc-app-bg);
}

.approval-step-row[draggable="true"] {
  cursor: grab;
}

.approval-step-row[draggable="true"]:active {
  cursor: grabbing;
}

.approval-step-row:last-child {
  border-bottom: 0;
}

.approval-step-row--dragging {
  opacity: 0.65;
  box-shadow: inset 3px 0 0 var(--sc-app-accent);
}

.approval-step-row--drop-target {
  background: var(--sc-app-panel);
  box-shadow: inset 0 2px 0 var(--sc-app-accent);
}

.approval-step-cell {
  min-width: 0;
}

.approval-step-seq {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.approval-step-actions button {
  min-width: 30px;
  min-height: 30px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-secondary);
}

.approval-step-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.approval-step-empty {
  display: grid;
  justify-items: start;
  gap: 10px;
  border: 1px dashed var(--sc-app-border);
  border-radius: 8px;
  padding: 18px;
  background: var(--sc-app-bg);
}

.approval-validation {
  border: 1px solid var(--sc-app-warning-border);
  border-radius: 6px;
  padding: 8px 10px;
  background: var(--sc-app-warning-bg);
  color: var(--sc-app-warning-text);
  font-size: 12px;
}

.approval-step-add-line {
  justify-self: start;
  min-height: 30px;
  border: 0;
  padding: 0 2px;
  background: transparent;
  color: var(--sc-app-accent);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
}

.approval-step-add-line:disabled {
  color: var(--sc-app-text-muted);
  cursor: not-allowed;
}

.approval-toggle {
  min-height: 34px;
  grid-template-columns: auto 1fr;
  align-items: center;
  align-self: end;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 10px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-primary);
}

.list-search-tabs {
  display: inline-flex;
  align-items: center;
  justify-self: start;
  gap: 2px;
  padding: 2px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-bg);
}

.config-editor-panel .list-search-tabs {
  position: sticky;
  top: 12px;
  display: grid;
  align-content: start;
  justify-self: stretch;
  gap: 6px;
  padding: 8px;
}

.config-editor-panel .list-search-tabs button {
  width: 100%;
  justify-content: space-between;
  min-height: 36px;
}

.list-search-tabs button {
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  border-radius: 6px;
  padding: 0 10px;
  background: transparent;
  color: var(--sc-app-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
}

.list-search-tabs button.active {
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  box-shadow: 0 0 0 1px var(--sc-app-border);
}

.list-search-tabs em {
  min-width: 20px;
  min-height: 20px;
  display: inline-grid;
  place-items: center;
  border-radius: 999px;
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-secondary);
  font-size: 11px;
  font-style: normal;
}

.empty-state {
  padding: 10px 0;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.version-list {
  display: grid;
  gap: 10px;
}

.version-guide {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.version-guide strong {
  color: var(--sc-app-text-primary);
  font-size: 14px;
}

.version-card {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-bg);
}

.version-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.version-card-title {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.version-card-head strong {
  font-size: 14px;
}

.version-card-head span {
  min-width: 0;
  color: var(--sc-app-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.version-card-head em {
  color: var(--sc-app-text-secondary);
  font-style: normal;
  white-space: normal;
}

.version-card-actions {
  flex: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.version-current-badge {
  min-height: 26px;
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  padding: 0 10px;
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-primary);
  font-size: 12px;
  white-space: nowrap;
}

.version-summary,
.version-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.version-decision-note {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.analysis-summary-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.analysis-summary-list span {
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  padding: 0 8px;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.version-rows {
  display: grid;
  gap: 4px;
}

.version-row {
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid var(--sc-app-border);
}

.version-row--current {
  color: var(--sc-app-text-primary);
}

.version-row-no {
  min-width: 42px;
  color: var(--sc-app-text-primary);
  font-weight: 600;
}

.version-row-delta {
  flex: 1 1 280px;
  min-width: min(100%, 220px);
}

.edit-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.edit-grid--single {
  grid-template-columns: minmax(0, 1fr);
}

.config-editor-panel .edit-grid {
  min-width: 0;
}

.field-chip-editor {
  min-width: 0;
  display: grid;
  align-content: start;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.config-editor-panel .field-chip-editor {
  min-height: 360px;
  padding: 14px;
  box-shadow: inset 0 0 0 1px rgb(148 163 184 / 6%);
}

.field-chip-editor header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.field-chip-editor strong {
  color: var(--sc-app-text-primary);
  font-size: 14px;
}

.inline-select {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--sc-app-text-secondary);
}

.inline-select select {
  min-height: 30px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 8px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  font: inherit;
}

.field-chip-list {
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  gap: 6px;
  min-height: 82px;
}

.field-chip {
  max-width: 100%;
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0 6px 0 9px;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-primary);
  font-size: 12px;
  line-height: 1;
  cursor: default;
  user-select: none;
}

.field-chip--dragging {
  opacity: 0.45;
}

.field-chip--drop-target {
  border-color: var(--sc-app-accent);
  box-shadow: inset 0 -2px 0 var(--sc-app-accent);
}

.field-chip-handle {
  display: inline-flex;
  align-items: center;
  color: var(--sc-app-text-secondary);
  cursor: grab;
  font-size: 12px;
  line-height: 1;
}

.field-chip-handle:active {
  cursor: grabbing;
}

.field-chip button {
  width: 22px;
  height: 22px;
  display: inline-grid;
  place-items: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--sc-app-text-secondary);
  cursor: pointer;
  line-height: 1;
}

.field-chip button:hover:not(:disabled) {
  background: var(--sc-app-hover-bg);
  color: var(--sc-app-text-primary);
}

.field-chip button:disabled {
  cursor: default;
  opacity: 0.35;
}

.field-chip-add {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
}

.field-chip-add input {
  width: 100%;
  min-height: 32px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 9px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  font: inherit;
}

.field-option-search {
  width: 100%;
  min-height: 30px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 9px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  font: inherit;
  font-size: 12px;
}

.field-option-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.field-option-summary .link-button {
  padding: 0;
  font-size: 12px;
  line-height: 1.2;
}

.field-option-pool {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-height: 96px;
  overflow: auto;
  padding-top: 2px;
}

.field-option-pool button {
  min-height: 26px;
  max-width: 100%;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  padding: 0 9px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-secondary);
  cursor: pointer;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field-option-pool button:hover {
  border-color: var(--sc-app-accent);
  color: var(--sc-app-text-primary);
}

.edit-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.edit-dirty {
  color: var(--sc-app-warning-text);
}

.preference-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.preference-list span {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .business-config-header,
  .edit-panel-head,
  .version-card-head {
    align-items: stretch;
    flex-direction: column;
  }

  .header-actions,
  .edit-panel-actions,
  .config-card-actions,
  .version-card-actions {
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .workbench-start,
  .scope-panel,
  .config-workspace,
  .config-editor-panel,
  .approval-config-grid,
  .edit-grid {
    grid-template-columns: 1fr;
  }

  .config-editor-panel .list-search-tabs {
    position: static;
  }

  .approval-rule-panel {
    position: static;
  }

  .workbench-start-lead,
  .workbench-start-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .workbench-start-actions .ghost,
  .delivery-readiness-item {
    width: 100%;
  }

  .workbench-status-rail {
    position: static;
  }

  .page-config-panel {
    order: -1;
  }

  .page-picker-panel .scan-list {
    max-height: min(520px, 62vh);
  }

  .selected-page-overview {
    align-items: stretch;
    flex-direction: column;
  }

  .selected-page-overview-side {
    align-items: flex-start;
    flex-direction: column;
  }

  .selected-page-overview-meta {
    justify-content: flex-start;
  }

  .approval-step-table {
    border: 0;
    background: transparent;
  }

  .approval-step-table-head {
    display: none;
  }

  .approval-step-row {
    grid-template-columns: 44px minmax(0, 1fr);
    min-width: 0;
    border: 1px solid var(--sc-app-border);
    border-radius: 6px;
    margin-bottom: 8px;
  }

  .approval-step-cell,
  .approval-step-actions {
    grid-column: 2 / -1;
  }

  .flow-card {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .flow-card .ghost {
    grid-column: 1 / -1;
  }

  .scan-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .scan-row-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
    white-space: normal;
  }
}
</style>
