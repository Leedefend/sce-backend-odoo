/* eslint-disable @typescript-eslint/no-explicit-any */
export function useBusinessConfigPublishLifecycle(deps: Record<string, any>) {
  const { currentModel, listSearchBusy, error, clearMessage, auditBusinessListSearchConfig, scopeAction, scopeView, scopeRole, listSearchAudit, namesToText, normalizeNamesText, listColumnsText, searchFiltersText, searchGroupByText, listSearchBase, activeListSearchEditor, requestedListSearchTab, analysisPanelOpen, approvalPanelOpen, listSearchPanelOpen, focusActiveEditorPanel, setMessage, auditBusinessAnalysisConfig, analysisAudit, pivotMeasuresText, pivotDimensionsText, graphMeasuresText, graphDimensionsText, graphType, analysisBase, activeAnalysisEditor, requestedAnalysisTab, listSearchSaving, hasListSearchDraftChanges, parseNames, stageUnifiedDraftItem, contractTargetKey, listContractPayload, searchContractPayload, hasAnalysisDraftChanges, analysisContractPayload, previewDraft, openImpactDialog, changeSet, publishDraft, loadSurface, rollbackPublished, discardDraft } = deps;
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
      const hasListConfig = result.has_business_list_config === true;
      const hasSearchConfig = result.has_business_search_config === true;
      const suggestedListColumns = hasListConfig ? [] : result.suggested_list_columns || [];
      const suggestedSearchFilters = hasSearchConfig ? [] : result.suggested_search_filters || [];
      const suggestedSearchGroupBy = hasSearchConfig ? [] : result.suggested_search_group_by || [];
      listColumnsText.value = namesToText(hasListConfig ? configuredListColumns : suggestedListColumns);
      searchFiltersText.value = namesToText(hasSearchConfig ? configuredSearchFilters : suggestedSearchFilters);
      searchGroupByText.value = namesToText(hasSearchConfig ? configuredSearchGroupBy : suggestedSearchGroupBy);
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
      if ((!hasListConfig && suggestedListColumns.length) || (!hasSearchConfig && (suggestedSearchFilters.length || suggestedSearchGroupBy.length))) {
        setMessage('建议配置，尚未保存', '采用或调整建议后点击保存，才会加入待发布变更');
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '列表与搜索设置读取失败';
    } finally {
      listSearchBusy.value = false;
    }
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
      const hasPivotConfig = result.has_business_pivot_config === true;
      const hasGraphConfig = result.has_business_graph_config === true;
      const suggestedPivotMeasures = hasPivotConfig ? [] : result.suggested_pivot_measures || [];
      const suggestedPivotDimensions = hasPivotConfig ? [] : result.suggested_pivot_dimensions || [];
      const suggestedGraphMeasures = hasGraphConfig ? [] : result.suggested_graph_measures || [];
      const suggestedGraphDimensions = hasGraphConfig ? [] : result.suggested_graph_dimensions || [];
      const configuredGraphType = hasGraphConfig ? result.graph_type || 'bar' : '';
      pivotMeasuresText.value = namesToText(hasPivotConfig ? configuredPivotMeasures : suggestedPivotMeasures);
      pivotDimensionsText.value = namesToText(hasPivotConfig ? configuredPivotDimensions : suggestedPivotDimensions);
      graphMeasuresText.value = namesToText(hasGraphConfig ? configuredGraphMeasures : suggestedGraphMeasures);
      graphDimensionsText.value = namesToText(hasGraphConfig ? configuredGraphDimensions : suggestedGraphDimensions);
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
        (!hasPivotConfig && (suggestedPivotMeasures.length || suggestedPivotDimensions.length))
        || (!hasGraphConfig && (suggestedGraphMeasures.length || suggestedGraphDimensions.length))
      ) {
        setMessage('建议配置，尚未保存', '采用或调整建议后点击保存，才会加入待发布变更');
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '分析视图设置读取失败';
    } finally {
      listSearchBusy.value = false;
    }
  }

  async function saveListSearchConfig() {
    if (!currentModel.value || !hasListSearchDraftChanges.value) return false;
    listSearchSaving.value = true;
    error.value = '';
    clearMessage();
    try {
      const listColumns = parseNames(listColumnsText.value);
      const searchFilters = parseNames(searchFiltersText.value);
      const searchGroupBy = parseNames(searchGroupByText.value);
      const listChanged = normalizeNamesText(listColumnsText.value) !== listSearchBase.value.list;
      const searchChanged = normalizeNamesText(searchFiltersText.value) !== listSearchBase.value.filter
        || normalizeNamesText(searchGroupByText.value) !== listSearchBase.value.group;
      if (listChanged) await stageUnifiedDraftItem({
        config_type: 'list', model: currentModel.value, view_type: 'tree', action_id: scopeAction.value, view_id: scopeView.value,
        role_key: scopeRole.value, target_key: contractTargetKey(currentModel.value, 'tree', scopeAction.value, scopeView.value),
        draft_payload: listContractPayload(listColumns), diff_summary: { summary: `列表列调整为 ${listColumns.length} 项` }, risk_level: 'low',
      });
      if (searchChanged) await stageUnifiedDraftItem({
        config_type: 'search', model: currentModel.value, view_type: 'search', action_id: scopeAction.value, view_id: scopeView.value,
        role_key: scopeRole.value, target_key: contractTargetKey(currentModel.value, 'search', scopeAction.value, scopeView.value),
        draft_payload: searchContractPayload(searchFilters, searchGroupBy), diff_summary: { summary: `搜索项 ${searchFilters.length}，分组项 ${searchGroupBy.length}` }, risk_level: 'low',
      });
      listSearchBase.value = {
        list: normalizeNamesText(listColumnsText.value),
        filter: normalizeNamesText(searchFiltersText.value),
        group: normalizeNamesText(searchGroupByText.value),
      };
      setMessage('列表与搜索修改已加入待发布变更', '正式运行页面尚未改变，可继续编辑其他配置后统一预览和发布');
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
      const pivotMeasures = parseNames(pivotMeasuresText.value);
      const pivotDimensions = parseNames(pivotDimensionsText.value);
      const graphMeasures = parseNames(graphMeasuresText.value);
      const graphDimensions = parseNames(graphDimensionsText.value);
      const pivotChanged = normalizeNamesText(pivotMeasuresText.value) !== analysisBase.value.pivotMeasures
        || normalizeNamesText(pivotDimensionsText.value) !== analysisBase.value.pivotDimensions;
      const graphChanged = normalizeNamesText(graphMeasuresText.value) !== analysisBase.value.graphMeasures
        || normalizeNamesText(graphDimensionsText.value) !== analysisBase.value.graphDimensions
        || graphType.value !== analysisBase.value.graphType;
      if (pivotChanged) await stageUnifiedDraftItem({
        config_type: 'analysis', model: currentModel.value, view_type: 'pivot', action_id: scopeAction.value, view_id: scopeView.value,
        role_key: scopeRole.value, target_key: contractTargetKey(currentModel.value, 'pivot', scopeAction.value, scopeView.value),
        draft_payload: analysisContractPayload('pivot', pivotMeasures, pivotDimensions, graphType.value),
        diff_summary: { summary: `透视指标 ${pivotMeasures.length}，维度 ${pivotDimensions.length}` }, risk_level: 'medium',
      });
      if (graphChanged) await stageUnifiedDraftItem({
        config_type: 'analysis', model: currentModel.value, view_type: 'graph', action_id: scopeAction.value, view_id: scopeView.value,
        role_key: scopeRole.value, target_key: contractTargetKey(currentModel.value, 'graph', scopeAction.value, scopeView.value),
        draft_payload: analysisContractPayload('graph', graphMeasures, graphDimensions, graphType.value),
        diff_summary: { summary: `图表指标 ${graphMeasures.length}，维度 ${graphDimensions.length}` }, risk_level: 'medium',
      });
      analysisBase.value = {
        pivotMeasures: normalizeNamesText(pivotMeasuresText.value),
        pivotDimensions: normalizeNamesText(pivotDimensionsText.value),
        graphMeasures: normalizeNamesText(graphMeasuresText.value),
        graphDimensions: normalizeNamesText(graphDimensionsText.value),
        graphType: graphType.value,
      };
      setMessage('分析修改已加入待发布变更', '正式分析页面尚未改变，可在统一变更集中检查和预览');
      return true;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '分析视图设置保存失败';
      return false;
    } finally {
      listSearchSaving.value = false;
    }
  }

  async function previewUnifiedDraft(device: 'desktop' | 'tablet' | 'mobile' = 'desktop') {
    try {
      const result = await previewDraft(device);
      setMessage('草稿预览已生成', `预览令牌仅对当前管理员有效，正式合同写入 ${result.preview?.formal_contract_write_count || 0}`);
    } catch (err) { error.value = err instanceof Error ? err.message : '草稿预览失败'; }
  }

  async function publishUnifiedDraft() {
    try {
      const confirmed = await openImpactDialog({ summary: `发布 ${changeSet.value?.item_count || 0} 项可逆配置`, immediate: true, rollbackText: '发布将生成一个变更批次，可按批次回滚。' });
      if (!confirmed) return;
      const result = await publishDraft();
      await loadSurface();
      setMessage('统一变更集已发布', `发布批次包含 ${result.item_count} 项配置，已完成权威重读`);
    } catch (err) { error.value = err instanceof Error ? err.message : '统一发布失败'; }
  }

  async function rollbackUnifiedDraft() {
    try {
      const result = await rollbackPublished();
      await loadSurface();
      setMessage('已按发布批次回滚', `回滚批次 ${result?.id || ''} 已完成运行态验证`);
    } catch (err) { error.value = err instanceof Error ? err.message : '批次回滚失败'; }
  }

  async function discardUnifiedDraft() {
    try { await discardDraft(); setMessage('未发布修改已放弃'); }
    catch (err) { error.value = err instanceof Error ? err.message : '放弃草稿失败'; }
  }
  return { loadListSearchConfig, loadAnalysisConfig, saveListSearchConfig, saveAnalysisConfig, previewUnifiedDraft, publishUnifiedDraft, rollbackUnifiedDraft, discardUnifiedDraft };
}
