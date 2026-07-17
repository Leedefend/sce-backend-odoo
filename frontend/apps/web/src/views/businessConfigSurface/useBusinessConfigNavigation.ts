import type { ComputedRef, Ref } from 'vue';
import type { RouteLocationNormalizedLoaded, Router } from 'vue-router';
import type { BusinessConfigSurfacePayload } from '../../api/businessConfig';
import { BUSINESS_CONFIG_MODES, BUSINESS_CONFIG_MODELS, BUSINESS_CONFIG_ROUTE_FLAGS } from '../../app/businessConfigBoundaries';
import type { useSessionStore } from '../../stores/session';
import { findMenuConfigNavigationEntry } from './navigation';

type SessionStore = ReturnType<typeof useSessionStore>;
type RuntimeTarget = { path: string; query: Record<string, string> };

export function useBusinessConfigNavigation(options: {
  route: RouteLocationNormalizedLoaded;
  router: Router;
  session: SessionStore;
  runtimeRouteTarget: ComputedRef<RuntimeTarget>;
  currentModel: ComputedRef<string>;
  selectedPageLabel: Ref<string>;
  scopeAction: ComputedRef<number | undefined>;
  scopeView: ComputedRef<number | undefined>;
  scopeRole: ComputedRef<string | undefined>;
  pageSearch: Ref<string>;
  pageTypeFilter: Ref<string>;
  configStatusFilter: Ref<string>;
  activeConfigSectionKey: Ref<string>;
  listSearchPanelOpen: Ref<boolean>;
  analysisPanelOpen: Ref<boolean>;
  activeListSearchEditor: Ref<string>;
  activeAnalysisEditor: Ref<string>;
  canOpenDesigner: ComputedRef<boolean>;
  ensureChangeSetToken: () => Promise<string>;
}) {
  function workbenchReturnStateQuery() {
    return {
      workbench_search: options.pageSearch.value.trim() || undefined,
      workbench_page_type: options.pageTypeFilter.value !== 'all' ? options.pageTypeFilter.value : undefined,
      workbench_config_status: options.configStatusFilter.value !== 'all' ? options.configStatusFilter.value : undefined,
      workbench_section: options.activeConfigSectionKey.value !== 'form' ? options.activeConfigSectionKey.value : undefined,
      workbench_scroll: String(Math.max(0, Math.round(window.scrollY || 0))),
    };
  }

  function buildRuntimeReturnQuery(
    baseQuery: Record<string, string> = {},
    runtimeOptions: { model?: string; actionId?: number; viewId?: number; pageLabel?: string; preserveEditorContext?: boolean } = {},
  ) {
    const preserveEditorContext = Boolean(runtimeOptions.preserveEditorContext);
    return {
      ...baseQuery,
      root_menu_xmlid: options.route.query.root_menu_xmlid || undefined,
      page_label: runtimeOptions.pageLabel || options.selectedPageLabel.value || undefined,
      [BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig]: '1',
      [BUSINESS_CONFIG_ROUTE_FLAGS.openPages]: '1',
      model: runtimeOptions.model || options.currentModel.value || undefined,
      action_id: runtimeOptions.actionId ? String(runtimeOptions.actionId) : (options.scopeAction.value ? String(options.scopeAction.value) : undefined),
      view_id: runtimeOptions.viewId ? String(runtimeOptions.viewId) : (options.scopeView.value ? String(options.scopeView.value) : undefined),
      list_search_tab: preserveEditorContext && options.listSearchPanelOpen.value && options.activeListSearchEditor.value !== 'list' ? options.activeListSearchEditor.value : undefined,
      open_list_search: preserveEditorContext && options.listSearchPanelOpen.value ? '1' : undefined,
      analysis_tab: preserveEditorContext && options.analysisPanelOpen.value && options.activeAnalysisEditor.value !== 'pivotMeasure' ? options.activeAnalysisEditor.value : undefined,
      open_analysis: preserveEditorContext && options.analysisPanelOpen.value ? '1' : undefined,
      ...workbenchReturnStateQuery(),
    };
  }

  async function openCurrentEffectivePage() {
    const target = options.runtimeRouteTarget.value;
    if (!target.path.trim()) return;
    await options.router.push({
      path: target.path,
      query: buildRuntimeReturnQuery(target.query || {}, { preserveEditorContext: true }),
    });
  }

  function menuConfigWorkbenchReturnQuery() {
    const menuEntry = findMenuConfigNavigationEntry(options.session.menuTree || [], BUSINESS_CONFIG_MODELS.menuConfigPolicy);
    return {
      menu_id: menuEntry?.menuId ? String(menuEntry.menuId) : undefined,
      action_id: menuEntry?.actionId ? String(menuEntry.actionId) : undefined,
      root_menu_xmlid: options.route.query.root_menu_xmlid || undefined,
      [BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig]: '1',
      [BUSINESS_CONFIG_ROUTE_FLAGS.openPages]: options.route.query[BUSINESS_CONFIG_ROUTE_FLAGS.openPages] || '1',
      [BUSINESS_CONFIG_ROUTE_FLAGS.returnModel]: options.currentModel.value || undefined,
      [BUSINESS_CONFIG_ROUTE_FLAGS.returnActionId]: options.scopeAction.value ? String(options.scopeAction.value) : undefined,
      [BUSINESS_CONFIG_ROUTE_FLAGS.returnMenuId]: options.route.query.menu_id || undefined,
      [BUSINESS_CONFIG_ROUTE_FLAGS.returnPageLabel]: options.selectedPageLabel.value || undefined,
      [BUSINESS_CONFIG_ROUTE_FLAGS.returnViewId]: options.scopeView.value ? String(options.scopeView.value) : undefined,
      [BUSINESS_CONFIG_ROUTE_FLAGS.returnRoleKey]: options.scopeRole.value || undefined,
      ...workbenchReturnStateQuery(),
    };
  }

  async function openMenuConfig(create = false) {
    const changeSetToken = create ? '' : await options.ensureChangeSetToken();
    void options.router.push({
      path: '/admin/menu-config',
      query: {
        ...menuConfigWorkbenchReturnQuery(),
        ...(changeSetToken ? { change_set_token: changeSetToken } : {}),
        ...(create ? { create_menu: '1' } : {}),
      },
    });
  }

  function openApprovalConfig(section: BusinessConfigSurfacePayload['sections'][number]) {
    const path = String(section.route?.path || '').trim();
    if (!path) return;
    void options.router.push({
      path,
      query: {
        ...(section.route?.query || {}),
        [BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig]: '1',
        ...workbenchReturnStateQuery(),
        root_menu_xmlid: options.route.query.root_menu_xmlid || undefined,
        page_label: options.selectedPageLabel.value || undefined,
      },
    });
  }

  async function openFormConfig() {
    if (!options.canOpenDesigner.value) return;
    const changeSetToken = await options.ensureChangeSetToken();
    void options.router.push({
      path: `/f/${encodeURIComponent(options.currentModel.value)}/new`,
      query: {
        action_id: options.scopeAction.value ? String(options.scopeAction.value) : undefined,
        menu_id: options.route.query.menu_id || undefined,
        root_menu_xmlid: options.route.query.root_menu_xmlid || undefined,
        view_id: options.scopeView.value ? String(options.scopeView.value) : undefined,
        role_key: options.scopeRole.value || undefined,
        page_label: options.selectedPageLabel.value || undefined,
        config_mode: BUSINESS_CONFIG_MODES.lowCode,
        change_set_token: changeSetToken || undefined,
        [BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig]: '1',
        ...workbenchReturnStateQuery(),
      },
    });
  }

  return {
    buildRuntimeReturnQuery,
    openCurrentEffectivePage,
    openMenuConfig: () => void openMenuConfig(false),
    openCreateMenuConfig: () => void openMenuConfig(true),
    openApprovalConfig,
    openFormConfig: () => void openFormConfig(),
  };
}
