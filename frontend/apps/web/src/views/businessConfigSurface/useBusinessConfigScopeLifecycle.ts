/* eslint-disable @typescript-eslint/no-explicit-any */
import type { BusinessConfigCoverageScanItem } from '../../api/businessConfig';
import { ApiError } from '../../api/client';

export function useBusinessConfigScopeLifecycle(deps: Record<string, any>) {
  const { scopeAction, currentModel, scopeView, message, surfaceLoadSeq, loading, error, withSurfaceLoadTimeout, loadBusinessConfigSurface, SURFACE_LOAD_TIMEOUT_MS, scopeRole, session, router, route, surface, scanLoading, coverageScan, scanBusinessConfigCoverage, rootMenuXmlid, selectedPageLabel, scopeModel, scopeActionId, scopeViewId, selectedRuntimeRoute, replaceWorkbenchQuerySilently, focusSelectedConfigPanelOnMobile, resetEditorPanels, runtimeReturnQuery } = deps;
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

  async function loadSurface() {
    const seq = ++surfaceLoadSeq.value;
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
        SURFACE_LOAD_TIMEOUT_MS,
      );
      if (seq !== surfaceLoadSeq.value) return;
      surface.value = nextSurface;
    } catch (err) {
      if (seq !== surfaceLoadSeq.value) return;
      if (err instanceof ApiError && err.status === 401) { await session.logout(); await router.replace({ path: '/login', query: { next: route.fullPath } }); return; }
      if (err instanceof ApiError && err.status === 403) { await router.replace({ path: '/access-denied', query: { from: route.fullPath, reason: err.reasonCode || 'PERMISSION_DENIED' } }); return; }
      error.value = err instanceof Error ? err.message : '业务配置工作台加载失败';
    } finally {
      if (seq === surfaceLoadSeq.value) {
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
      error.value = err instanceof Error ? err.message : '业务配置覆盖检查失败';
    } finally {
      scanLoading.value = false;
    }
  }

  async function scanSystemRootCoverage() {
    if (!surface.value && currentModel.value) { await loadSurface(); if (!surface.value) return; }
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
      error.value = err instanceof Error ? err.message : '系统根菜单覆盖检查失败';
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
      error.value = err instanceof Error ? err.message : '当前业务对象覆盖检查失败';
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

  async function applyScopeAndLoad() {
    resetEditorPanels();
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
    resetEditorPanels();
    replaceWorkbenchQuerySilently({
      model: row.model || undefined,
      action_id: row.action_id ? String(row.action_id) : undefined,
      view_id: row.view_id ? String(row.view_id) : undefined,
      role_key: scopeRole.value || undefined,
      page_label: row.name || undefined,
      open_list_search: undefined,
    });
    await loadSurface();
    await focusSelectedConfigPanelOnMobile();
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
      query: runtimeReturnQuery(runtimeRoute.query || {}, {
        model: row.model,
        actionId: row.action_id,
        viewId: row.view_id,
        pageLabel: row.name || row.model,
      }),
    });
  }

  return { coverageRowKey, coverageRowMatchesScope, coverageRowActionId, coverageRowViewId, clearMessage, setMessage, loadSurface, scanCoverage, scanSystemRootCoverage, scanCurrentModel, rescanCoverageAfterBootstrap, applyScopeAndLoad, focusScanRow, hydrateSelectedCoverageRowFromScan, openRuntimeRoute };
}
