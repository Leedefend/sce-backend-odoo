/* eslint-disable @typescript-eslint/no-explicit-any */
import type { BusinessConfigCoverageScanItem, BusinessConfigRemediationAction } from '../../api/businessConfig';

export function useBusinessConfigRemediationLifecycle(deps: Record<string, any>) {
  const { focusScanRow, loadAnalysisConfig, loadVersions, setMessage, openMenuConfig, loadListSearchConfig, rowBootstrapMissingViewTypes, listSearchSaving, error, clearMessage, bootstrapBusinessFormConfig, coverageRowActionId, coverageRowViewId, scopeRole, bootstrapBusinessListSearchConfig, bootstrapBusinessAnalysisConfig, loadSurface, scanCurrentModel, openFormConfig, coverageBatchBootstrapRows, openImpactDialog, bootstrapCoverageMissingConfig, currentModel, scopeView, rootMenuXmlid, coverageScan, rescanCoverageAfterBootstrap, approvalImpactSummaryText, saveApprovalConfig } = deps;
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
      setMessage('没有可自动生成的配置项', '当前项目需要检查发布状态或配置作用域。');
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
    const confirmed = await openImpactDialog({
      summary: `批量补齐 ${coverageBatchBootstrapRows.value.length} 个页面的缺失配置`,
      rollbackText: '每个已发布配置均保留版本，可按页面恢复。',
    });
    if (!confirmed) return;
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

  async function confirmAndSaveApprovalConfig() {
    const confirmed = await openImpactDialog({
      summary: approvalImpactSummaryText.value || '调整当前页面的审批规则',
      rollbackText: '审批规则会立即被运行态消费；请使用可复位配置恢复原状态。',
    });
    if (!confirmed) return;
    await saveApprovalConfig();
  }
  return { runRemediationAction, openVersionsForRuntimeGaps, bootstrapMissingContracts, bootstrapCoverageMissing, confirmAndSaveApprovalConfig };
}
