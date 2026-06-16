<template>
  <section class="business-config-page">
    <header class="business-config-header">
      <div>
        <p class="eyebrow">低代码页面设计器</p>
        <h1>{{ designerTitle }}</h1>
      </div>
      <div class="header-actions">
        <button type="button" class="ghost primary" :disabled="!canOpenDesigner" @click="openFormConfig">
          {{ canOpenDesigner ? '进入拖拽设计' : '先选择页面' }}
        </button>
        <button type="button" class="ghost" :disabled="scanLoading" @click="scanSystemRootCoverage">
          {{ scanLoading ? '读取中...' : '选择业务页面' }}
        </button>
        <button type="button" class="ghost" :disabled="loading" @click="advancedPanelOpen = !advancedPanelOpen">
          高级作用域
        </button>
      </div>
    </header>

    <div v-if="error" class="status error">{{ error }}</div>
    <div v-else-if="message" class="status ok">{{ message }}</div>

    <section v-if="!coverageScan" class="workbench-flow">
      <article class="flow-card flow-card--primary">
        <span class="flow-step">1</span>
        <div>
          <h2>选择业务页面</h2>
          <p>读取可配置页面列表，选择要调整的页面。</p>
        </div>
        <button type="button" class="ghost primary" :disabled="scanLoading" @click="scanSystemRootCoverage">
          {{ scanLoading ? '读取中...' : '选择页面' }}
        </button>
      </article>
      <article class="flow-card">
        <span class="flow-step">2</span>
        <div>
          <h2>拖拽设计表单</h2>
          <p>进入设计器后拖动字段、隐藏字段、调整分组。</p>
        </div>
        <button type="button" class="ghost" :disabled="!canOpenDesigner" @click="openFormConfig">进入设计</button>
      </article>
      <article class="flow-card">
        <span class="flow-step">3</span>
        <div>
          <h2>保存并预览</h2>
          <p>保存配置后打开业务页面确认效果。</p>
        </div>
        <button type="button" class="ghost" :disabled="!canOpenDesigner" @click="openFormConfig">预览配置</button>
      </article>
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
          <input v-model="pageSearch" type="search" placeholder="输入页面名称或业务对象" />
        </label>
        <label class="scan-toggle">
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
          {{ listSearchSaving ? '生成中...' : '生成基础配置' }}
        </button>
      </div>
      <div class="scan-summary">
        <span>业务页面 {{ coverageScan.summary.action_count }}</span>
        <span>当前显示 {{ visibleCoverageRows.length }}</span>
        <span>{{ coverageScopeLabel }}</span>
        <span v-if="coverageScan.summary.user_preference_count">已有个人配置 {{ coverageScan.summary.user_preference_count }}</span>
        <span v-if="advancedPanelOpen">治理结论 {{ overallStatusLabel(coverageScan.summary.overall_status) }}</span>
        <span v-if="advancedPanelOpen">需处理 {{ coverageIssueRows.length }}</span>
        <span v-for="item in advancedPanelOpen ? remediationSummaryItems : []" :key="item.code">
          {{ item.label }} {{ item.count }}
        </span>
      </div>
      <div v-if="visibleCoverageRows.length" class="scan-list">
        <div v-for="row in visibleCoverageRows" :key="row.action_id" class="scan-row" :class="{ 'scan-row--selected': row.action_id === scopeAction }">
          <div class="scan-row-main">
            <strong>{{ row.name || row.model }}</strong>
            <span>{{ row.model }}</span>
          </div>
          <div class="scan-row-meta">
            <span>{{ pageViewModeText(row) }}</span>
            <span>{{ pageDesignStatus(row) }}</span>
            <span v-if="row.user_preference_count">已有个人配置 {{ row.user_preference_count }}</span>
            <span v-if="advancedPanelOpen">{{ runtimeEvidenceText(row) }}</span>
            <span v-if="advancedPanelOpen && runtimeReasonText(row)">原因 {{ runtimeReasonText(row) }}</span>
          </div>
          <div v-if="advancedPanelOpen" class="scan-row-admin-actions">
            <span>{{ severityLabel(row.severity) }}</span>
            <span v-if="row.missing_view_types.length">需补 {{ row.missing_view_types.map(viewTypeLabel).join('、') }}</span>
            <span v-if="row.runtime_missing_view_types.length">运行时未命中 {{ row.runtime_missing_view_types.map(viewTypeLabel).join('、') }}</span>
          </div>
          <div class="scan-row-actions">
            <button type="button" class="ghost small primary" @click="openDesignerForRow(row)">设计表单</button>
            <button
              type="button"
              class="ghost small"
              :disabled="!row.runtime_route?.path"
              @click="openRuntimeRoute(row)"
            >
              预览页面
            </button>
            <button type="button" class="ghost small" @click="focusScanRow(row)">选择</button>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">当前没有匹配的业务页面，可调整搜索条件或取消“只看需处理”。</div>
    </section>
    <section v-if="advancedPanelOpen && coverageScan" class="scan-panel scan-panel--admin">
      <div class="scan-toolbar">
        <strong>高级治理视图</strong>
      </div>
      <div class="scan-list">
        <div v-for="row in visibleCoverageRows" :key="`admin-${row.action_id}`" class="scan-row">
          <strong>{{ row.name || row.model }}</strong>
          <span>{{ severityLabel(row.severity) }}</span>
          <span>{{ row.model }}</span>
          <span>{{ row.view_mode || '-' }}</span>
          <span>菜单 {{ row.menu_count }}</span>
          <span v-if="row.user_preference_count">个人偏好 {{ row.user_preference_count }} · {{ row.user_preference_boundary }}</span>
          <span v-if="row.missing_view_types.length">需补 {{ row.missing_view_types.map(viewTypeLabel).join('、') }}</span>
          <span v-else>配置完整</span>
          <span v-if="row.runtime_missing_view_types.length">运行时未命中 {{ row.runtime_missing_view_types.map(viewTypeLabel).join('、') }}</span>
          <span v-else>运行时完整</span>
          <span>{{ runtimeEvidenceText(row) }}</span>
          <span v-if="runtimeReasonText(row)">原因 {{ runtimeReasonText(row) }}</span>
          <button
            v-for="action in row.remediation_actions"
            :key="`admin-${row.action_id}-${action.code}`"
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
    <section v-if="!loading" class="section-grid">
      <article v-for="section in sections" :key="section.key" class="config-card">
        <div class="config-card-head">
          <h2>{{ section.label }}</h2>
          <strong>{{ section.contract_count }}</strong>
        </div>
        <p>{{ boundaryLabel(section.boundary) }}</p>
        <div class="config-card-meta">
          <span>{{ sectionHelpLabel(section.key) }}</span>
        </div>
        <div class="config-card-actions">
          <button
            v-if="section.key === 'form' || section.key === 'list_search'"
            type="button"
            class="ghost small"
            :disabled="!currentModel || versionsLoading"
            @click="loadVersions(section.key)"
          >
            {{ versionsLoading ? '读取中...' : '版本' }}
          </button>
          <button
            v-if="section.key === 'list_search'"
            type="button"
            class="ghost small"
            :disabled="!currentModel || listSearchBusy"
            @click="loadListSearchConfig"
          >
            {{ listSearchBusy ? '读取中...' : '配置列表搜索' }}
          </button>
          <button
            v-else-if="section.key === 'form'"
            type="button"
            class="ghost small"
            :disabled="!canOpenDesigner"
            @click="openFormConfig"
          >
            拖拽设计表单
          </button>
          <button
            v-else-if="section.key === 'menu'"
            type="button"
            class="ghost small"
            @click="openMenuConfig"
          >
            调整菜单入口
          </button>
          <button
            v-else
            type="button"
            class="ghost small"
            disabled
          >
            编辑入口待接入
          </button>
        </div>
      </article>
    </section>

    <section v-if="versionsPanelOpen" class="version-panel">
      <div class="edit-panel-head">
        <div>
          <h2>{{ versionTitle }}</h2>
          <p>按当前模型、动作、视图、角色作用域读取正式业务契约版本。</p>
        </div>
        <button type="button" class="ghost small" :disabled="versionsLoading" @click="versionsPanelOpen = false">
          关闭
        </button>
      </div>
      <div v-if="!versionContracts.length" class="empty-state">当前作用域暂无版本记录。</div>
      <div v-else class="version-list">
        <article v-for="contract in versionContracts" :key="contract.id" class="version-card">
          <div class="version-card-head">
            <div class="version-card-title">
              <strong>{{ viewTypeLabel(contract.view_type) }}</strong>
              <span>{{ contract.name }}</span>
            </div>
            <div class="version-card-actions">
              <em>当前 v{{ contract.version_no }}</em>
              <button
                type="button"
                class="ghost small"
                :disabled="versionsLoading || listSearchSaving || contract.versions.length < 2"
                @click="rollbackContractFromWorkbench(contract)"
              >
                回滚上一版
              </button>
            </div>
          </div>
          <div class="version-summary">
            <span>表单字段 {{ contract.summary.form_field_count }}</span>
            <span>列表列 {{ contract.summary.list_column_count }}</span>
            <span>筛选 {{ contract.summary.search_filter_count }}</span>
            <span>分组 {{ contract.summary.search_group_by_count }}</span>
          </div>
          <div class="version-rows">
            <div v-for="version in contract.versions" :key="version.id" class="version-row">
              <span>v{{ version.version_no }}</span>
              <span>{{ version.status }}</span>
              <span>{{ version.created_by || '-' }}</span>
              <span>
                字段 {{ version.summary.form_field_count }} /
                列 {{ version.summary.list_column_count }} /
                筛选 {{ version.summary.search_filter_count }} /
                分组 {{ version.summary.search_group_by_count }}
              </span>
              <button
                type="button"
                class="link-button"
                :disabled="versionsLoading || listSearchSaving || version.version_no === contract.version_no"
                @click="rollbackContractFromWorkbench(contract, version.version_no)"
              >
                回滚到此版
              </button>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section v-if="listSearchPanelOpen" class="edit-panel">
      <div class="edit-panel-head">
        <div>
          <h2>列表/搜索业务配置</h2>
          <p>这些配置写入正式业务契约，不写入个人列偏好。</p>
        </div>
        <button type="button" class="ghost small" :disabled="listSearchSaving" @click="saveListSearchConfig">
          {{ listSearchSaving ? '保存中...' : '保存业务默认' }}
        </button>
      </div>
      <div class="edit-grid">
        <label>
          <span>默认列表列</span>
          <textarea v-model="listColumnsText" placeholder="name, email, phone" />
        </label>
        <label>
          <span>搜索筛选字段</span>
          <textarea v-model="searchFiltersText" placeholder="state, partner_id" />
        </label>
        <label>
          <span>搜索分组字段</span>
          <textarea v-model="searchGroupByText" placeholder="partner_id, state" />
        </label>
      </div>
      <div class="edit-meta">
        <span>个人偏好记录：{{ listSearchAudit?.user_preference_count ?? 0 }}</span>
        <span>边界：{{ listSearchAudit?.user_preference_boundary || 'ui_only' }}</span>
      </div>
      <div v-if="listSearchAudit?.user_preferences?.length" class="preference-list">
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
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  auditBusinessListSearchConfig,
  bootstrapBusinessFormConfig,
  bootstrapBusinessListSearchConfig,
  bootstrapCoverageMissingConfig,
  loadBusinessConfigContractVersions,
  loadBusinessConfigSurface,
  rollbackBusinessConfigContract,
  saveBusinessListSearchConfig,
  scanBusinessConfigCoverage,
  type BusinessConfigContractVersionsPayload,
  type BusinessConfigCoverageScanItem,
  type BusinessConfigCoverageScanPayload,
  type BusinessConfigListSearchAuditPayload,
  type BusinessConfigRemediationAction,
  type BusinessConfigSurfacePayload,
} from '../api/businessConfig';

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const scanLoading = ref(false);
const listSearchBusy = ref(false);
const listSearchSaving = ref(false);
const error = ref('');
const message = ref('');
const surface = ref<BusinessConfigSurfacePayload | null>(null);
const coverageScan = ref<BusinessConfigCoverageScanPayload | null>(null);
const showOnlyIssues = ref(false);
const pageSearch = ref('');
const listSearchAudit = ref<BusinessConfigListSearchAuditPayload | null>(null);
const listSearchPanelOpen = ref(false);
const versionsLoading = ref(false);
const versionsPanelOpen = ref(false);
const advancedPanelOpen = ref(false);
const versionTitle = ref('配置版本');
const versionContracts = ref<BusinessConfigContractVersionsPayload['contracts']>([]);
const listColumnsText = ref('');
const searchFiltersText = ref('');
const searchGroupByText = ref('');
const scopeModel = ref(String(route.query.model || '').trim());
const scopeActionId = ref(numericQuery('action_id') || 0);
const scopeViewId = ref(numericQuery('view_id') || 0);
const scopeRoleKey = ref(String(route.query.role_key || '').trim());
const rootMenuXmlid = computed(() => String(route.query.root_menu_xmlid || '').trim());
const shouldOpenPageList = computed(() => String(route.query.open_pages || '').trim() === '1');
const designerTitle = computed(() => {
  const model = currentModel.value || scopeModel.value.trim();
  return model ? `正在配置：${model}` : '选择一个业务页面开始配置';
});

const sections = computed(() => surface.value?.sections || []);
const currentModel = computed(() => String(scopeModel.value || surface.value?.model || '').trim());
const canOpenDesigner = computed(() => Boolean(currentModel.value && scopeAction.value));
function isCoverageIssue(row: BusinessConfigCoverageScanItem) {
  return !row.is_complete || !row.is_runtime_complete || !row.has_menu;
}

const coverageIssueRows = computed(() => (
  coverageScan.value?.items || []
).filter(isCoverageIssue));
const coverageBatchBootstrapRows = computed(() => (
  coverageScan.value?.items || []
).filter((row) => (
  row.runtime_missing_view_types.some((viewType) => viewType === 'form' || viewType === 'tree' || viewType === 'search')
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
  const filtered = keyword
    ? rows.filter((row) => [
      row.name,
      row.model,
      row.view_mode,
      pageViewModeText(row),
    ].some((text) => String(text || '').toLowerCase().includes(keyword)))
    : rows;
  return filtered.slice(0, 60);
});
const remediationSummaryItems = computed(() => {
  const counts = coverageScan.value?.summary.remediation_action_counts || {};
  return Object.entries(counts)
    .map(([code, count]) => ({ code, count, label: remediationActionLabel(code) }))
    .filter((item) => item.count > 0)
    .sort((left, right) => left.label.localeCompare(right.label, 'zh-Hans-CN'));
});

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

function boundaryLabel(boundary: string) {
  if (boundary === 'business_contract') return '业务默认配置';
  if (boundary === 'business_contract_not_user_preference') return '业务默认配置';
  if (boundary === 'business_contract_with_policy_runtime') return '菜单显示规则';
  return boundary || '未声明边界';
}

function sectionHelpLabel(sectionKey: string) {
  if (sectionKey === 'form') return '字段显示、隐藏、必填、布局';
  if (sectionKey === 'list_search') return '列表列、搜索条件、默认分组';
  if (sectionKey === 'menu') return '菜单入口、显示范围、发布状态';
  return '业务配置';
}

function viewTypeLabel(viewType: string) {
  if (viewType === 'form') return '表单';
  if (viewType === 'tree' || viewType === 'list') return '列表';
  if (viewType === 'search') return '搜索';
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

function runtimeReasonLabel(reason: string) {
  if (reason === 'missing_contract') return '缺契约';
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
  if (code === 'configure_contract') return '补配置';
  if (code === 'publish_contract') return '看版本';
  if (code === 'fix_scope') return '查作用域';
  if (code === 'configure_menu') return '配菜单';
  if (code === 'review_user_preference_boundary') return '查偏好';
  return code;
}

async function loadSurface() {
  loading.value = true;
  error.value = '';
  message.value = '';
  try {
    surface.value = await loadBusinessConfigSurface({
      model: currentModel.value || undefined,
      action_id: scopeAction.value,
      view_id: scopeView.value,
      role_key: scopeRole.value,
    });
  } catch (err) {
    error.value = err instanceof Error ? err.message : '业务配置工作台加载失败';
  } finally {
    loading.value = false;
  }
}

async function scanCoverage() {
  scanLoading.value = true;
  error.value = '';
  message.value = '';
  try {
    coverageScan.value = await scanBusinessConfigCoverage({
      model: currentModel.value || undefined,
      role_key: scopeRole.value,
      root_menu_xmlid: rootMenuXmlid.value || undefined,
      include_all_root_menu_actions: false,
      limit: 1000,
    });
  } catch (err) {
    error.value = err instanceof Error ? err.message : '业务配置覆盖扫描失败';
  } finally {
    scanLoading.value = false;
  }
}

async function scanSystemRootCoverage() {
  scanLoading.value = true;
  error.value = '';
  message.value = '';
  try {
    coverageScan.value = await scanBusinessConfigCoverage({
      model: currentModel.value || undefined,
      role_key: scopeRole.value,
      root_menu_xmlid: rootMenuXmlid.value || undefined,
      include_all_root_menu_actions: true,
      limit: 1000,
    });
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
  message.value = '';
  try {
    coverageScan.value = await scanBusinessConfigCoverage({
      model: currentModel.value,
      role_key: scopeRole.value,
      root_menu_xmlid: rootMenuXmlid.value || undefined,
      include_all_root_menu_actions: Boolean(coverageScan.value?.include_all_root_menu_actions),
      limit: 1000,
    });
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
    `缺口：配置缺口 ${summary.missing_count}，运行时缺口 ${summary.runtime_missing_count}，无菜单 ${summary.no_menu_count}，个人偏好 ${summary.user_preference_count}`,
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
    message.value = '已复制验收摘要';
  } catch {
    message.value = text;
  }
}

async function applyScopeAndLoad() {
  listSearchPanelOpen.value = false;
  listSearchAudit.value = null;
  versionsPanelOpen.value = false;
  versionContracts.value = [];
  coverageScan.value = null;
  await router.replace({
    path: route.path,
    query: {
      ...route.query,
      model: currentModel.value || undefined,
      action_id: scopeAction.value ? String(scopeAction.value) : undefined,
      view_id: scopeView.value ? String(scopeView.value) : undefined,
      role_key: scopeRole.value || undefined,
    },
  });
  await loadSurface();
}

async function focusScanRow(row: BusinessConfigCoverageScanItem) {
  scopeModel.value = row.model;
  scopeActionId.value = row.action_id;
  scopeViewId.value = 0;
  listSearchPanelOpen.value = false;
  listSearchAudit.value = null;
  versionsPanelOpen.value = false;
  versionContracts.value = [];
  await router.replace({
    path: route.path,
    query: {
      ...route.query,
      model: row.model || undefined,
      action_id: row.action_id ? String(row.action_id) : undefined,
      view_id: undefined,
      role_key: scopeRole.value || undefined,
    },
  });
  await loadSurface();
}

async function openDesignerForRow(row: BusinessConfigCoverageScanItem) {
  await focusScanRow(row);
  openFormConfig();
}

async function openRuntimeRoute(row: BusinessConfigCoverageScanItem) {
  const runtimeRoute = row.runtime_route || {};
  const path = String(runtimeRoute.path || '').trim();
  if (!path) return;
  await router.push({
    path,
    query: runtimeRoute.query || {},
  });
}

async function runRemediationAction(row: BusinessConfigCoverageScanItem, action: BusinessConfigRemediationAction) {
  await focusScanRow(row);
  if (action.code === 'configure_contract' || action.code === 'fix_scope') {
    await bootstrapMissingContracts(row);
    return;
  }
  if (action.code === 'publish_contract') {
    if (row.runtime_missing_view_types.some((viewType) => viewType === 'tree' || viewType === 'search')) {
      await loadVersions('list_search');
    } else {
      await loadVersions('form');
    }
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

async function bootstrapMissingContracts(row: BusinessConfigCoverageScanItem) {
  if (!row.model) return;
  listSearchSaving.value = true;
  error.value = '';
  message.value = '';
  let savedCount = 0;
  let formFieldCount = 0;
  try {
    if (row.runtime_missing_view_types.includes('form')) {
      const formResult = await bootstrapBusinessFormConfig({
        model: row.model,
        action_id: row.action_id || undefined,
        view_id: scopeView.value,
        role_key: scopeRole.value,
        publish: true,
      });
      savedCount += 1;
      formFieldCount = formResult.field_count || 0;
    }
    const listSearchTypes = row.runtime_missing_view_types
      .filter((viewType) => viewType === 'tree' || viewType === 'search');
    if (listSearchTypes.length) {
      const listResult = await bootstrapBusinessListSearchConfig({
        model: row.model,
        action_id: row.action_id || undefined,
        view_id: scopeView.value,
        role_key: scopeRole.value,
        view_types: listSearchTypes,
        publish: true,
      });
      savedCount += listResult.saved_count || 0;
    }
    await loadSurface();
    await scanCurrentModel();
    message.value = formFieldCount
      ? `已生成并发布 ${savedCount} 个业务契约，表单字段 ${formFieldCount}`
      : `已生成并发布 ${savedCount} 个业务契约`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '业务契约自动生成失败，已打开手工配置';
    if (row.runtime_missing_view_types.includes('form')) {
      openFormConfig();
    } else {
      await loadListSearchConfig();
    }
  } finally {
    listSearchSaving.value = false;
  }
}

async function bootstrapFormConfig(row: BusinessConfigCoverageScanItem) {
  if (!row.model) return;
  listSearchSaving.value = true;
  error.value = '';
  message.value = '';
  try {
    const result = await bootstrapBusinessFormConfig({
      model: row.model,
      action_id: row.action_id || undefined,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      publish: true,
    });
    await loadSurface();
    await scanCurrentModel();
    message.value = `已生成并发布表单业务契约，字段 ${result.field_count}`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '表单契约自动生成失败，已打开手工配置';
    openFormConfig();
  } finally {
    listSearchSaving.value = false;
  }
}

async function bootstrapListSearchConfig(row: BusinessConfigCoverageScanItem) {
  if (!row.model) return;
  listSearchSaving.value = true;
  error.value = '';
  message.value = '';
  try {
    const viewTypes = row.runtime_missing_view_types
      .filter((viewType) => viewType === 'tree' || viewType === 'search');
    const result = await bootstrapBusinessListSearchConfig({
      model: row.model,
      action_id: row.action_id || undefined,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      view_types: viewTypes.length ? viewTypes : ['tree', 'search'],
      publish: true,
    });
    await loadSurface();
    await scanCurrentModel();
    message.value = `已生成并发布 ${result.saved_count} 个列表/搜索业务契约`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '列表/搜索契约自动生成失败';
    await loadListSearchConfig();
  } finally {
    listSearchSaving.value = false;
  }
}

async function bootstrapCoverageMissing() {
  if (!coverageBatchBootstrapRows.value.length) return;
  listSearchSaving.value = true;
  error.value = '';
  message.value = '';
  try {
    const result = await bootstrapCoverageMissingConfig({
      model: currentModel.value || undefined,
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
    message.value = result.failed_count
      ? `已生成并发布 ${result.saved_count} 个业务契约，${result.failed_count} 个动作需手工处理${failedNames ? `：${failedNames}` : ''}`
      : `已生成并发布 ${result.saved_count} 个业务契约`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '批量补齐业务契约失败';
  } finally {
    listSearchSaving.value = false;
  }
}

function namesToText(names: string[]) {
  return names.join(', ');
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

async function loadListSearchConfig() {
  if (!currentModel.value) return;
  listSearchBusy.value = true;
  error.value = '';
  message.value = '';
  try {
    const result = await auditBusinessListSearchConfig({
      model: currentModel.value,
      action_id: scopeAction.value,
      view_id: scopeView.value,
      role_key: scopeRole.value,
    });
    listSearchAudit.value = result;
    listColumnsText.value = namesToText(result.business_config_list_columns || []);
    searchFiltersText.value = namesToText(result.business_config_search_filters || []);
    searchGroupByText.value = namesToText(result.business_config_search_group_by || []);
    listSearchPanelOpen.value = true;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '列表/搜索配置读取失败';
  } finally {
    listSearchBusy.value = false;
  }
}

async function saveListSearchConfig() {
  if (!currentModel.value) return;
  listSearchSaving.value = true;
  error.value = '';
  message.value = '';
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
    message.value = `已保存 ${result.saved_count} 个业务配置契约`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '列表/搜索配置保存失败';
  } finally {
    listSearchSaving.value = false;
  }
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
  versionsLoading.value = true;
  error.value = '';
  message.value = '';
  try {
    if (sectionKey === 'form') {
      const result = await loadBusinessConfigContractVersions(versionParams('form'));
      versionTitle.value = '表单配置版本';
      versionContracts.value = result.contracts || [];
    } else {
      const [treeResult, searchResult] = await Promise.all([
        loadBusinessConfigContractVersions(versionParams('tree')),
        loadBusinessConfigContractVersions(versionParams('search')),
      ]);
      versionTitle.value = '列表/搜索配置版本';
      versionContracts.value = [...(treeResult.contracts || []), ...(searchResult.contracts || [])];
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
  const confirmed = window.confirm(`确认将${viewTypeLabel(contract.view_type)}配置回滚到${targetText}？`);
  if (!confirmed) return;
  listSearchSaving.value = true;
  error.value = '';
  message.value = '';
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
    await loadVersions(contract.view_type === 'form' ? 'form' : 'list_search');
    if (coverageScan.value) {
      await rescanCoverageAfterBootstrap();
    }
    message.value = `已回滚到 v${result.rolled_back_to_version}`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '业务配置回滚失败';
  } finally {
    listSearchSaving.value = false;
  }
}

function openMenuConfig() {
  router.push({
    path: '/admin/menu-config',
    query: {
      menu_id: route.query.menu_id || undefined,
      action_id: scopeAction.value ? String(scopeAction.value) : undefined,
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
      config_mode: 'business_config_lowcode',
    },
  });
}

onMounted(() => {
  void (async () => {
    await loadSurface();
    if (shouldOpenPageList.value) {
      await scanSystemRootCoverage();
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
.workbench-flow,
.scope-panel,
.loading-state,
.scan-panel {
  margin: 0 18px;
}

.status {
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
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

.workbench-flow {
  display: grid;
  grid-template-columns: 1.1fr 1fr 1fr;
  gap: 10px;
}

.flow-card {
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
}

.flow-card--primary {
  border-color: var(--sc-app-accent);
}

.flow-step {
  display: inline-grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 50%;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-primary);
  font-weight: 700;
}

.flow-card h2,
.config-card h2,
.edit-panel h2,
.version-panel h2 {
  margin: 0;
  font-size: 15px;
}

.flow-card p {
  margin: 4px 0 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
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

.scan-list {
  display: grid;
  gap: 8px;
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
  box-shadow: inset 3px 0 0 var(--sc-app-accent);
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

.scan-panel--admin .scan-row {
  display: flex;
  flex-wrap: wrap;
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
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
  padding: 0 18px;
}

.config-card {
  min-width: 0;
  display: grid;
  gap: 10px;
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

.config-card strong {
  font-size: 22px;
}

.config-card p {
  margin: 0;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.config-card-meta {
  min-width: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.config-card-actions {
  display: flex;
  justify-content: flex-end;
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

.edit-panel p {
  margin: 4px 0 0;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
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

.version-card {
  display: grid;
  gap: 8px;
  padding: 10px;
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
  gap: 3px;
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
  flex: none;
  color: var(--sc-app-text-secondary);
  font-style: normal;
}

.version-card-actions {
  flex: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.version-summary,
.version-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.version-rows {
  display: grid;
  gap: 4px;
}

.version-row {
  padding-top: 6px;
  border-top: 1px solid var(--sc-app-border);
}

.edit-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.edit-grid label {
  min-width: 0;
  display: grid;
  gap: 6px;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.edit-grid textarea {
  width: 100%;
  min-height: 112px;
  resize: vertical;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 8px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-primary);
  font: inherit;
}

.edit-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
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
  .workbench-flow,
  .scope-panel,
  .edit-grid {
    grid-template-columns: 1fr;
  }

  .flow-card {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .flow-card .ghost {
    grid-column: 1 / -1;
  }
}
</style>
