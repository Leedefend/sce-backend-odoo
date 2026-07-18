<template src="./menuConfig/template.html"></template>
<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-unused-vars */
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import type { NavNode } from '@sc/schema';
import ScButton from '../components/design-system/ScButton.vue';
import BusinessConfigImpactDialog from './businessConfigSurface/BusinessConfigImpactDialog.vue';
import {
  loadMenuConfigurationAudit,
  loadMenuConfigurationPanel,
  loadMenuConfigurationVersions,
  rollbackMenuConfiguration,
  createMenuConfigurationEntry,
  deleteMenuConfigurationEntry,
  type MenuConfigAuditPayload,
  type MenuConfigGroup,
  type MenuConfigMenu,
  type MenuConfigPolicy,
  type MenuConfigPayload,
  type MenuConfigRuntimePayload,
  type MenuConfigRuntimeState,
  type MenuConfigSaveRow,
  type MenuConfigVersionsPayload,
} from '../api/menuConfig';
import {
  openBusinessConfigChangeSet,
  stageBusinessConfigChangeSetItem,
} from '../api/businessConfig';
import { useSessionStore } from '../stores/session';
import { config } from '../config';
import { BUSINESS_CONFIG_ROUTE_FLAGS } from '../app/businessConfigBoundaries';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import { createMenuConfigTree, type MenuConfigDropPosition } from './menuConfig/createMenuConfigTree';
import { useMenuTreeEditor } from './menuConfig/useMenuTreeEditor';
import { createMenuTreeAdapter, type RuntimeMenuConfigGroup } from './menuConfig/menuTreeAdapter';
import { checkedValue, cloneDraft, defaultDraft, defaultDraftForEmpty, inputValue, normalizeDraft, numericValue, type DraftPolicy } from './menuConfig/menuDraftAdapter';
import { persistMenuSaveNotice, storedMenuSaveNotice } from './menuConfig/menuSaveNotice';
type FlatRow = {
  menu: MenuConfigMenu;
  level: number;
};
type DropPosition = MenuConfigDropPosition;
const pageContract = usePageContract('menu_config');
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const pageSectionsReady = computed(() => (
  pageSectionEnabled('root', true)
  && pageSectionEnabled('header', true)
  && pageSectionEnabled('tree', true)
  && pageSectionEnabled('editor', true)
  && pageSectionTagIs('root', 'section')
  && pageSectionTagIs('header', 'header')
  && pageSectionTagIs('tree', 'section')
  && pageSectionTagIs('editor', 'section')
));
const pageSectionsFingerprint = computed(() => JSON.stringify([
  pageSectionStyle('header'),
  pageSectionStyle('tree'),
  pageSectionStyle('editor'),
]));
async function executeGlobalPageAction(actionKey: string) {
  await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: route.query,
    onRefresh: () => loadPanel(),
  });
}
function setSaveNotice(value: string) {
  saveNotice.value = value;
  persistMenuSaveNotice(value);
}
const loading = ref(false);
const saving = ref(false);
const auditing = ref(false);
const rollingBack = ref(false);
const versionLoading = ref(false);
const creatingMenu = ref(false);
const deletingMenu = ref(false);
const error = ref('');
const message = ref('');
const saveNotice = ref(storedMenuSaveNotice());
const auditResult = ref<MenuConfigAuditPayload | null>(null);
const versionState = ref<MenuConfigVersionsPayload | null>(null);
const versionPanelOpen = ref(false);
const selectedVersionNo = ref(0);
const selectedMenuId = ref(0);
const searchText = ref('');
const menuStateFilter = ref<'all' | 'visible' | 'hidden' | 'unconfigured'>('all');
const dragSourceMenuId = ref(0);
const dragTargetMenuId = ref(0);
const dragDropPosition = ref<DropPosition>('after');
const onlyConfigured = ref(false);
const showGuide = ref(false);
const createPanelOpen = ref(false);
const bulkPanelOpen = ref(false);
const company = ref<{ id: number; name: string } | null>(null);
const statusMessage = computed(() => message.value || saveNotice.value);
const menus = ref<MenuConfigMenu[]>([]);
const tree = ref<MenuConfigMenu[]>([]);
const collapsedMenuIds = ref<Set<number>>(new Set());
const groups = ref<MenuConfigGroup[]>([]);
const runtimeState = ref<MenuConfigRuntimePayload | null>(null);
const originalPolicies = ref<Record<number, DraftPolicy>>({});
const drafts = reactive<Record<number, DraftPolicy>>({});
const roleGroupDomainSelections = reactive<Record<number, string>>({});
const session = useSessionStore();
const route = useRoute();
const router = useRouter();
const impactDialog = reactive({ open: false, summary: '', rollbackText: '' });
let impactDialogResolver: ((confirmed: boolean) => void) | null = null;
function confirmImpact(summary: string, rollbackText: string) {
  impactDialog.open = true; impactDialog.summary = summary; impactDialog.rollbackText = rollbackText;
  return new Promise<boolean>((resolve) => { impactDialogResolver = resolve; });
}
function resolveImpactDialog(confirmed: boolean) {
  impactDialog.open = false; impactDialogResolver?.(confirmed); impactDialogResolver = null;
}
const canReturnToBusinessConfig = computed(() => String(route.query[BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig] || '').trim() === '1');
const createForm = reactive({
  name: '',
  parent_menu_id: 0,
  source_menu_id: 0,
  sequence: 0,
  visible: true,
  note: '',
});
const MenuConfigTree = createMenuConfigTree({
  menuPathLabel: (menu) => menuPathLabel(menu),
  menuDisplayLabel: (menu) => menuDisplayLabel(menu),
  menuHandlingStateClass: (menu) => menuHandlingStateClass(menu),
  menuTreeStateLabel: (menu) => menuTreeStateLabel(menu),
  isUserCreatedMenu: (menu) => isUserCreatedMenu(menu),
});

const companyLabel = computed(() => company.value?.name || '当前公司');

const auditSummary = computed(() => {
  const summary = auditResult.value?.summary;
  if (!summary) return null;
  return {
    configuredCount: Number(summary.configured_policy_count || 0),
    applicableCount: Number(summary.applicable_policy_count || 0),
    hiddenCount: Number(summary.hidden_count || 0),
    runtimeVisibleCount: Number(summary.runtime_visible_count || auditResult.value?.runtime?.summary?.runtime_visible_count || 0),
    runtimeHiddenCount: Number(summary.runtime_hidden_count || 0),
    runtimeCarrierCount: Number(summary.runtime_carrier_count || auditResult.value?.runtime?.summary?.runtime_carrier_count || 0),
    renamedCount: Number(summary.renamed_count || 0),
    reorderedCount: Number(summary.reordered_count || 0),
    movedCount: Number(summary.moved_count || 0),
    notApplicableCount: Array.isArray(summary.not_applicable_policy_ids) ? summary.not_applicable_policy_ids.length : 0,
    runtimeSourceLabel: String(summary.source_label || '配置来源待确认'),
  };
});

const canRollbackMenuConfiguration = computed(() => {
  const currentVersion = Number(versionState.value?.contract?.version_no || 0);
  return Boolean(
    currentVersion
    && (versionState.value?.versions || []).some((version) => Number(version.version_no || 0) !== currentVersion),
  );
});

const selectedRollbackVersion = computed(() => {
  const currentVersion = Number(versionState.value?.contract?.version_no || 0);
  const selected = Number(selectedVersionNo.value || 0);
  if (!selected || selected === currentVersion) return null;
  return (versionState.value?.versions || []).find((version) => Number(version.version_no || 0) === selected) || null;
});

const rollbackButtonText = computed(() => {
  if (!versionState.value?.contract) return '先查看版本';
  if (!canRollbackMenuConfiguration.value) return '暂无可回滚版本';
  return selectedVersionNo.value ? `回滚到版本 ${selectedVersionNo.value} 菜单配置` : '回滚到上一版本菜单配置';
});

const rollbackButtonDisabled = computed(() => (
  loading.value
  || saving.value
  || rollingBack.value
  || versionLoading.value
  || Boolean(versionState.value?.contract && !canRollbackMenuConfiguration.value)
  || !selectedRollbackVersion.value
));

const groupOptions = computed(() => {
  return [...groups.value].sort((a, b) => a.display_name.localeCompare(b.display_name, 'zh-Hans-CN'));
});

const ALL_ROLE_GROUP_DOMAINS = '全部业务角色';

const roleGroupDomainOptions = computed(() => {
  const domains = new Set(groupOptions.value.map((group) => roleGroupDomain(group.display_name)));
  return [
    ALL_ROLE_GROUP_DOMAINS,
    ...Array.from(domains).sort((a, b) => a.localeCompare(b, 'zh-Hans-CN')),
  ];
});

function isProductNavigationRoot(menu: MenuConfigMenu | null | undefined) {
  if (!menu) return false;
  const label = String(menu.display_name || menu.name || '').trim();
  const completeName = String(menu.complete_name || '').trim();
  return label === '智慧施工管理平台' || completeName === '智慧施工管理平台';
}

function isSystemNavigationRoot(menu: MenuConfigMenu | null | undefined) {
  if (!menu) return false;
  const label = String(menu.display_name || menu.name || '').trim();
  return label === '系统菜单';
}

const displayTreeSource = computed<MenuConfigMenu[]>(() => {
  if (tree.value.length !== 1) return tree.value;
  const [root] = tree.value;
  if ((!isProductNavigationRoot(root) && !isSystemNavigationRoot(root)) || !root.children?.length) return tree.value;
  return root.children;
});

const flatRows = computed<FlatRow[]>(() => {
  const out: FlatRow[] = [];
  const walk = (items: MenuConfigMenu[], level = 1) => {
    items.forEach((item) => {
      if (!isRuntimeMenuGroup(item)) {
        out.push({ menu: item, level });
      }
      if (item.children?.length) walk(item.children, level + 1);
    });
  };
  walk(displayTreeSource.value);
  return out;
});

const visibleFlatRows = computed<FlatRow[]>(() => {
  const out: FlatRow[] = [];
  const walk = (items: MenuConfigMenu[], level = 1) => {
    items.forEach((item) => {
      if (!isRuntimeMenuGroup(item)) {
        out.push({ menu: item, level });
      }
      if (item.children?.length) walk(item.children, level + 1);
    });
  };
  walk(visibleTree.value);
  return out;
});

const treeCountLabel = computed(() => {
  const total = flatRows.value.length;
  const current = visibleFlatRows.value.length;
  if (current === total) return `${total} 个可配置菜单`;
  return `${current} / ${total} 个可配置菜单`;
});

const normalizedSearchText = computed(() => searchText.value.trim().toLowerCase());
const treeViewFiltered = computed(() => Boolean(normalizedSearchText.value) || menuStateFilter.value !== 'all');
const treeDragEnabled = computed(() => !treeViewFiltered.value);

const menuStateFilterOptions = computed(() => {
  const counts = flatRows.value.reduce((acc, row) => {
    const state = menuHandlingStateClass(row.menu);
    acc.all += 1;
    if (state === 'visible') acc.visible += 1;
    if (state === 'hidden') acc.hidden += 1;
    if (state === 'unconfigured') acc.unconfigured += 1;
    return acc;
  }, {
    all: 0,
    visible: 0,
    hidden: 0,
    unconfigured: 0,
  });
  return [
    { value: 'all' as const, label: '全部', count: counts.all },
    { value: 'visible' as const, label: '已启用', count: counts.visible },
    { value: 'hidden' as const, label: '已隐藏', count: counts.hidden },
    { value: 'unconfigured' as const, label: '候选', count: counts.unconfigured },
  ];
});

function menuSearchText(menu: MenuConfigMenu) {
  const draft = drafts[menu.id];
  return [
    menuDisplayLabel(menu),
    menuPathLabel(menu),
    menuParentLabel(menu),
    menu.name,
    menu.display_name,
    menu.complete_name,
    menu.parent_name,
    menu.xmlid,
    menu.action,
    ...(menu.group_names || []),
    draft?.custom_label || '',
    draft?.note || '',
    menuHandlingStateLabel(menu),
    menuTreeStateLabel(menu),
  ].join(' ').toLowerCase();
}

function menuMatchesSearch(menu: MenuConfigMenu) {
  const term = normalizedSearchText.value;
  if (!term) return true;
  return menuSearchText(menu).includes(term);
}

function runtimeStateForMenu(menu: MenuConfigMenu | null | undefined): MenuConfigRuntimeState | null {
  if (!menu) return null;
  const states = runtimeState.value?.states || {};
  return states[String(menu.id)] || states[String(menu.menu_id)] || null;
}

function isMenuShownInHandling(menu: MenuConfigMenu | null | undefined) {
  if (!menu) return false;
  const state = runtimeStateForMenu(menu);
  if (state) return Boolean(state.runtime_visible);
  const draft = drafts[menu.id];
  return Boolean(draft?.policy_id && draft.visible);
}

function isMenuConfigSurfaceMenu(menu: MenuConfigMenu | null | undefined) {
  if (!menu) return false;
  if (isRuntimeMenuGroup(menu)) return true;
  const state = runtimeStateForMenu(menu);
  if (!state) return true;
  return state.runtime_state !== 'configured_visible_runtime_absent'
    && state.runtime_visibility_reason !== 'configured_visible_runtime_absent';
}

function menuHandlingStateLabel(menu: MenuConfigMenu | null | undefined) {
  const state = runtimeStateForMenu(menu);
  if (state?.runtime_visible) {
    if (state.runtime_visibility_reason === 'visible_descendant_carrier' || state.runtime_state === 'visible_carrier') {
      return '办理面显示 · 承载子菜单';
    }
    if (state.runtime_visibility_reason === 'visible_release_navigation_group' || state.runtime_state === 'visible_release_navigation_group') {
      return '办理面显示 · 产品导航分组';
    }
    if (state.runtime_visibility_reason === 'visible_protected' || state.runtime_state === 'visible_protected') {
      return '办理面显示 · 系统保护';
    }
    return '办理面显示';
  }
  const draft = menu ? drafts[menu.id] : null;
  if (state && state.runtime_visibility_reason === 'hidden_permission') return '当前用户不可见';
  if (state && state.runtime_visibility_reason === 'configured_visible_runtime_absent') return '当前未进入导航';
  return draft?.policy_id ? '当前隐藏' : '候选';
}

function menuHandlingStateClass(menu: MenuConfigMenu | null | undefined) {
  if (isMenuShownInHandling(menu)) return 'visible';
  const draft = menu ? drafts[menu.id] : null;
  return draft?.policy_id ? 'hidden' : 'unconfigured';
}

function menuTreeStateLabel(menu: MenuConfigMenu | null | undefined) {
  const state = menuHandlingStateClass(menu);
  if (state === 'visible') return '启用';
  if (state === 'hidden') return '当前隐藏';
  return '候选';
}

function menuMatchesStateFilter(menu: MenuConfigMenu) {
  if (menuStateFilter.value === 'all') return true;
  return menuHandlingStateClass(menu) === menuStateFilter.value;
}

function clearTreeFilter() {
  searchText.value = '';
  menuStateFilter.value = 'all';
}

const visibleTree = computed<MenuConfigMenu[]>(() => {
  const term = normalizedSearchText.value;
  if (!term && menuStateFilter.value === 'all') {
    return displayTreeSource.value;
  }

  const filterBranch = (items: MenuConfigMenu[]): MenuConfigMenu[] => {
    return items.flatMap((item) => {
      const children = filterBranch(item.children || []);
      const searchMatched = !term || menuMatchesSearch(item);
      const stateMatched = menuMatchesStateFilter(item);
      if (children.length || (searchMatched && stateMatched)) {
        return [{ ...item, children }];
      }
      return [];
    });
  };

  return filterBranch(displayTreeSource.value);
});

const selectedIds = computed(() => {
  if (!selectedMenuId.value) return new Set<number>();
  const out = new Set<number>();
  const walk = (items: MenuConfigMenu[], selectedAncestor = false) => {
    items.forEach((item) => {
      const active = selectedAncestor || item.id === selectedMenuId.value;
      if (active && !isRuntimeMenuGroup(item)) {
        out.add(item.id);
      }
      if (item.children?.length) walk(item.children, active);
    });
  };
  walk(visibleTree.value);
  return out;
});

const filteredRows = computed(() => {
  const term = normalizedSearchText.value;
  const sourceRows = term ? flatRows.value : visibleFlatRows.value;
  return sourceRows.filter((row) => {
    if (!term && selectedMenuId.value && !selectedIds.value.has(row.menu.id)) return false;
    if (onlyConfigured.value && !hasConfiguration(row.menu.id)) return false;
    if (!term) return true;
    return menuMatchesSearch(row.menu);
  });
});

const dirtyCount = computed(() => Object.keys(drafts).filter((key) => isDirty(Number(key))).length);
const treeSearchSummary = computed(() => {
  const total = flatRows.value.length;
  const current = visibleFlatRows.value.length;
  const dirty = dirtyCount.value;
  return `显示 ${current} / ${total}，未保存 ${dirty}`;
});
const selectedMenu = computed(() => menus.value.find((menu) => Number(menu.id) === Number(selectedMenuId.value)) || null);
const selectedDraft = computed(() => (
  selectedMenu.value ? draftFor(selectedMenu.value.id) || defaultDraftForEmpty() : defaultDraftForEmpty()
));
const deletableMenuCount = computed(() => menus.value.filter((menu) => isUserCreatedMenu(menu)).length);
const canDeleteSelectedMenu = computed(() => {
  const menu = selectedMenu.value;
  if (!menu?.id) return false;
  return isUserCreatedMenu(menu);
});
const selectedMenuDeleteHint = computed(() => {
  if (!selectedMenu.value) return '请选择一个菜单后再删除。';
  if (canDeleteSelectedMenu.value) return '该菜单由配置新增，可以删除。';
  return '系统内置菜单不能物理删除，需要关闭“显示菜单”来隐藏。';
});
const rootMenuXmlid = computed(() => String(route.query.root_menu_xmlid || config.startupRootXmlid || '').trim());
const shouldLoadFullRootMenuConfig = computed(() => (
  String(route.query[BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig] || '').trim() === '1'
  && Boolean(rootMenuXmlid.value)
));
const rootMenu = computed(() => (
  rootMenuXmlid.value
    ? menus.value.find((menu) => menu.xmlid === rootMenuXmlid.value) || null
    : null
));
const BUSINESS_MENU_ROOT_LABEL = '智慧施工管理平台';

function isBusinessRootNode(node: NavNode) {
  const label = navMenuLabel(node);
  return label === BUSINESS_MENU_ROOT_LABEL || Number(navMenuId(node)) === Number(rootMenu.value?.id || 0);
}

function unwrapProductNavigationRoot(nodes: NavNode[]) {
  if (nodes.length !== 1) return nodes;
  const [node] = nodes;
  if (navMenuLabel(node) !== '系统菜单' || !Array.isArray(node.children)) return nodes;
  return node.children as NavNode[];
}

function scopedNavigationTree() {
  const sourceNodes = Array.isArray(session.menuTree) && session.menuTree.length
    ? (session.menuTree as NavNode[])
    : [];
  const nodes = unwrapProductNavigationRoot(sourceNodes);
  const explicitRootId = Number(rootMenu.value?.id || 0);
  const matched = nodes.find((node) => (
    (explicitRootId && Number(navMenuId(node)) === explicitRootId)
    || isBusinessRootNode(node)
  ));
  return matched ? [matched] : nodes.filter((node) => navMenuLabel(node) !== '系统菜单');
}

async function ensureProductNavigationReady() {
  if (Array.isArray(session.menuTree) && session.menuTree.length) return;
  if (!session.token) return;
  await session.loadAppInit();
}

const navigationMenus = computed(() => flattenMenuTree(tree.value));
const navigationParentMenus = computed(() => navigationMenus.value.filter((menu) => (
  Boolean(menu.children?.length) || !String(menu.action || '').trim()
)));
const configuredParentMenus = computed(() => menus.value.filter((menu) => (
  !isRuntimeMenuGroup(menu)
  && isMenuConfigSurfaceMenu(menu)
  && (Boolean(menu.children?.length) || !String(menu.action || '').trim())
)));
const createParentOptions = computed(() => {
  const byId = new Map<number, MenuConfigMenu>();
  if (rootMenu.value) byId.set(Number(rootMenu.value.id), rootMenu.value);
  configuredParentMenus.value.forEach((menu) => byId.set(Number(menu.id), menu));
  navigationParentMenus.value.forEach((menu) => byId.set(Number(menu.id), menu));
  return Array.from(byId.values()).sort((a, b) => parentOptionSortKey(a).localeCompare(parentOptionSortKey(b), 'zh-Hans-CN'));
});
const defaultCreateParentId = computed(() => (
  rootMenu.value?.id
  || createParentOptions.value[0]?.id
  || 0
));
const copySourceOptions = computed(() => navigationMenus.value
  .filter((menu) => Boolean(String(menu.action || '').trim()))
  .sort((a, b) => (a.complete_name || a.name).localeCompare(b.complete_name || b.name, 'zh-Hans-CN')));

function isUserCreatedMenu(menu: MenuConfigMenu | null | undefined): boolean {
  if (!menu?.id) return false;
  if (isRuntimeMenuGroup(menu)) return false;
  return !String(menu.xmlid || '').trim();
}

function isRuntimeMenuGroup(menu: MenuConfigMenu | null | undefined): boolean {
  return Boolean((menu as RuntimeMenuConfigGroup | null | undefined)?.runtime_group);
}

function draftFor(menuId: number) {
  return drafts[menuId];
}

function isDirty(menuId: number) {
  const draft = drafts[menuId];
  const original = originalPolicies.value[menuId];
  if (!draft || !original) return false;
  return normalizeDraft(draft) !== normalizeDraft(original);
}

function hasConfiguration(menuId: number) {
  const draft = drafts[menuId];
  if (!draft) return false;
  return Boolean(
    draft.policy_id
    || draft.target_parent_menu_id
    || draft.custom_label.trim()
    || draft.sequence_override
    || !draft.visible
    || draft.role_group_ids.length
    || draft.note.trim(),
  );
}

function roleScopeSummary(menuId: number) {
  const count = draftFor(menuId)?.role_group_ids.length || 0;
  return count ? `限 ${count} 个业务角色可见` : '所有业务角色可见';
}

function displayNoteValue(value: string) {
  const note = String(value || '').trim();
  if (/^(user_confirmed_|system_|technical_|synced_from_|generated_from_|migrated_from_)/i.test(note)) return '';
  return note;
}

function roleGroupName(groupId: number) {
  const group = groupOptions.value.find((item) => Number(item.id) === Number(groupId));
  return group?.display_name || `业务角色 ${groupId}`;
}

function roleGroupDomain(label: string) {
  if (/项目|业主/.test(label)) return '项目中心';
  if (/合同/.test(label)) return '合同中心';
  if (/结算/.test(label)) return '结算中心';
  if (/付款|财务|资金|费用|保证金/.test(label)) return '财务/付款';
  if (/物资|采购|供应/.test(label)) return '物资/采购';
  if (/经营|管理层|业务配置|通用/.test(label)) return '管理/通用';
  return '其他';
}

function roleGroupDomainForMenu(menuId: number) {
  return roleGroupDomainSelections[menuId] || ALL_ROLE_GROUP_DOMAINS;
}

function setRoleGroupDomain(menuId: number, value: string) {
  roleGroupDomainSelections[menuId] = value || ALL_ROLE_GROUP_DOMAINS;
}

function scopedRoleGroupOptions(menuId: number) {
  const domain = roleGroupDomainForMenu(menuId);
  return groupOptions.value.filter((group) => {
    return domain === ALL_ROLE_GROUP_DOMAINS || roleGroupDomain(group.display_name) === domain;
  });
}

function isRoleGroupSelected(menuId: number, groupId: number) {
  return (draftFor(menuId)?.role_group_ids || []).map(Number).includes(Number(groupId));
}

function toggleRoleGroup(menuId: number, groupId: number, selected: boolean) {
  const draft = draftFor(menuId);
  if (!draft) return;
  const existing = new Set(draft.role_group_ids.map(Number));
  if (selected) {
    existing.add(Number(groupId));
  } else {
    existing.delete(Number(groupId));
  }
  updateDraft(menuId, { role_group_ids: Array.from(existing).sort((a, b) => a - b) });
}

function scopedSelectedRoleGroupCount(menuId: number) {
  const scopedIds = new Set(scopedRoleGroupOptions(menuId).map((group) => Number(group.id)));
  return (draftFor(menuId)?.role_group_ids || []).filter((groupId) => scopedIds.has(Number(groupId))).length;
}

function scopedUnselectedRoleGroupCount(menuId: number) {
  return Math.max(0, scopedRoleGroupOptions(menuId).length - scopedSelectedRoleGroupCount(menuId));
}

function scopedRoleGroupSelectionText(menuId: number) {
  const total = scopedRoleGroupOptions(menuId).length;
  if (!total) return '当前分组 0/0';
  return `当前分组 ${scopedSelectedRoleGroupCount(menuId)}/${total}`;
}

function selectScopedRoleGroups(menuId: number) {
  const draft = draftFor(menuId);
  if (!draft) return;
  const existing = new Set(draft.role_group_ids.map(Number));
  scopedRoleGroupOptions(menuId).forEach((group) => existing.add(Number(group.id)));
  updateDraft(menuId, { role_group_ids: Array.from(existing).sort((a, b) => a - b) });
}

function clearScopedRoleGroups(menuId: number) {
  const draft = draftFor(menuId);
  if (!draft) return;
  const scopedIds = new Set(scopedRoleGroupOptions(menuId).map((group) => Number(group.id)));
  updateDraft(menuId, {
    role_group_ids: draft.role_group_ids
      .map(Number)
      .filter((groupId) => !scopedIds.has(groupId))
      .sort((a, b) => a - b),
  });
}

function clearRoleGroups(menuId: number) {
  updateDraft(menuId, { role_group_ids: [] });
}

function updateDraft(menuId: number, patch: Partial<DraftPolicy>) {
  const draft = drafts[menuId];
  if (!draft) return;
  Object.assign(draft, patch);
  message.value = '';
  setSaveNotice('');
  auditResult.value = null;
}

function removeRoleGroup(menuId: number, groupId: number) {
  const draft = draftFor(menuId);
  if (!draft) return;
  updateDraft(menuId, { role_group_ids: draft.role_group_ids.filter((item) => Number(item) !== Number(groupId)) });
}

function parentOptions(menuId: number) {
  const excluded = descendantsFor(menuId);
  excluded.add(menuId);
  return createParentOptions.value
    .filter((item) => !excluded.has(item.id))
    .sort((a, b) => parentOptionSortKey(a).localeCompare(parentOptionSortKey(b), 'zh-Hans-CN'));
}

function parentOptionIds(menuId: number) {
  return new Set(parentOptions(menuId).map((item) => Number(item.id)));
}

function menuById(menuId: number) {
  return menus.value.find((menu) => Number(menu.id) === Number(menuId)) || null;
}

function treeMenuById(menuId: number) {
  let found: MenuConfigMenu | null = null;
  const walk = (items: MenuConfigMenu[]): boolean => items.some((item) => {
    if (Number(item.id) === Number(menuId)) {
      found = item;
      return true;
    }
    return Boolean(item.children?.length && walk(item.children));
  });
  walk(tree.value);
  return found;
}

function descendantsFor(menuId: number) {
  const out = new Set<number>();
  const byParent = new Map<number, MenuConfigMenu[]>();
  menus.value.forEach((menu) => {
    const list = byParent.get(menu.parent_id) || [];
    list.push(menu);
    byParent.set(menu.parent_id, list);
  });
  const walk = (id: number) => {
    (byParent.get(id) || []).forEach((child) => {
      out.add(child.id);
      walk(child.id);
    });
  };
  walk(menuId);
  return out;
}

function selectMenu(menuId: number) {
  selectedMenuId.value = menuId;
}

function upsertCreatedMenu(menu: MenuConfigMenu, policy?: MenuConfigPolicy) {
  if (!menu?.id) return;
  const nextMenu = { ...menu, children: menu.children || [] };
  const menuIndex = menus.value.findIndex((item) => Number(item.id) === Number(nextMenu.id));
  if (menuIndex >= 0) {
    menus.value.splice(menuIndex, 1, nextMenu);
  } else {
    menus.value.push(nextMenu);
  }

  const draft = defaultDraft(nextMenu, policy);
  drafts[nextMenu.id] = cloneDraft(draft);
  originalPolicies.value = {
    ...originalPolicies.value,
    [nextMenu.id]: cloneDraft(draft),
  };

  const insertIntoBranch = (items: MenuConfigMenu[]): { rows: MenuConfigMenu[]; inserted: boolean } => {
    let inserted = false;
    const rows = items.map((item) => {
      if (Number(item.id) === Number(nextMenu.parent_id || 0)) {
        const existing = item.children || [];
        if (existing.some((child) => Number(child.id) === Number(nextMenu.id))) {
          inserted = true;
          return {
            ...item,
            children: existing.map((child) => (Number(child.id) === Number(nextMenu.id) ? nextMenu : child)),
          };
        }
        inserted = true;
        return {
          ...item,
          children: [...existing, nextMenu].sort((a, b) => (
            Number(a.sequence || 0) - Number(b.sequence || 0)
            || Number(a.id || 0) - Number(b.id || 0)
          )),
        };
      }
      if (!item.children?.length) return item;
      const result = insertIntoBranch(item.children);
      if (result.inserted) {
        inserted = true;
        return { ...item, children: result.rows };
      }
      return item;
    });
    return { rows, inserted };
  };

  const result = insertIntoBranch(tree.value);
  tree.value = result.inserted ? result.rows : [...tree.value, nextMenu];
}

function resetCreateForm() {
  createForm.name = '';
  createForm.parent_menu_id = defaultCreateParentId.value;
  createForm.source_menu_id = 0;
  createForm.sequence = 0;
  createForm.visible = true;
  createForm.note = '';
}

function openCreateMenu(mode: 'custom' | 'sibling' | 'child' | 'copy') {
  const current = selectedMenu.value;
  resetCreateForm();
  if (mode === 'sibling' && current) {
    createForm.parent_menu_id = Number(current.parent_id || defaultCreateParentId.value);
    createForm.name = `${current.name}（同级）`;
  } else if (mode === 'child' && current) {
    createForm.parent_menu_id = current.id;
  } else if (mode === 'copy' && current) {
    createForm.parent_menu_id = Number(current.parent_id || defaultCreateParentId.value);
    createForm.source_menu_id = current.id;
    createForm.name = `${current.name}副本`;
  }
  if (!createParentOptions.value.some((menu) => Number(menu.id) === Number(createForm.parent_menu_id))) {
    createForm.parent_menu_id = defaultCreateParentId.value;
  }
  createPanelOpen.value = true;
  message.value = '';
  error.value = '';
}

async function createMenuEntry() {
  if (!createForm.name.trim()) return;
  creatingMenu.value = true;
  error.value = '';
  message.value = '';
  try {
    const result = await createMenuConfigurationEntry({
      company_id: company.value?.id || undefined,
      name: createForm.name.trim(),
      parent_menu_id: createForm.parent_menu_id || 0,
      source_menu_id: createForm.source_menu_id || 0,
      sequence: Number(createForm.sequence || 0),
      visible: createForm.visible,
      note: createForm.note.trim(),
    });
    const createdMenu = result.menu;
    const createdName = createdMenu?.name || createForm.name.trim();
    upsertCreatedMenu(result.menu, result.policy);
    selectedMenuId.value = Number(createdMenu?.id || 0);
    createPanelOpen.value = false;
    auditResult.value = null;
    await session.loadAppInit({ force: true });
    await loadPanel({ preserveStatus: true });
    if (versionPanelOpen.value) {
      await loadVersions();
    }
    selectedMenuId.value = Number(createdMenu?.id || 0);
    message.value = `已创建菜单“${createdName}”，导航已刷新，可继续新增下级菜单`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '菜单创建失败';
  } finally {
    creatingMenu.value = false;
  }
}

async function deleteSelectedMenu() {
  const menu = selectedMenu.value;
  if (!menu?.id || !canDeleteSelectedMenu.value) return;
  if (dirtyCount.value) {
    error.value = '请先保存或放弃未保存修改后再删除菜单。';
    return;
  }
  const menuName = menu.name || menu.display_name || '当前菜单';
  const confirmed = await confirmImpact(`删除新增菜单“${menuName}”并同步刷新导航`, '删除后不能通过未保存草稿恢复；如已有已发布版本，可从版本记录回滚。');
  if (!confirmed) return;

  const fallbackMenuId = Number(menu.parent_id || 0);
  deletingMenu.value = true;
  error.value = '';
  message.value = '';
  setSaveNotice('');
  auditResult.value = null;
  try {
    const result = await deleteMenuConfigurationEntry({
      company_id: company.value?.id || undefined,
      menu_id: menu.id,
    });
    await session.loadAppInit({ force: true });
    selectedMenuId.value = fallbackMenuId;
    await loadPanel({ preserveStatus: true });
    if (versionPanelOpen.value) {
      await loadVersions();
    }
    const countText = result.deleted_count > 1 ? `等 ${result.deleted_count} 个菜单` : '';
    message.value = `已删除菜单“${menuName}”${countText}，导航已刷新`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '菜单删除失败';
  } finally {
    deletingMenu.value = false;
  }
}

function selectedMenuPath(items: MenuConfigMenu[], menuId: number): Set<number> {
  if (!menuId) return new Set();
  const path: number[] = [];
  const walk = (rows: MenuConfigMenu[]): boolean => rows.some((item) => {
    path.push(item.id);
    if (item.id === menuId || walk(item.children || [])) return true;
    path.pop();
    return false;
  });
  walk(items);
  return new Set(path);
}

function flattenMenuTree(items: MenuConfigMenu[]): MenuConfigMenu[] {
  const out: MenuConfigMenu[] = [];
  const walk = (rows: MenuConfigMenu[]) => {
    rows.forEach((item) => {
      if (!isRuntimeMenuGroup(item)) {
        out.push(item);
      }
      if (item.children?.length) walk(item.children);
    });
  };
  walk(items);
  return out;
}

function parentOptionSortKey(menu: MenuConfigMenu) {
  const isRoot = rootMenu.value && Number(menu.id) === Number(rootMenu.value.id);
  return `${isRoot ? '0' : '1'}:${menuPathLabel(menu)}`;
}

function parentOptionLabel(menu: MenuConfigMenu) {
  const label = menuPathLabel(menu);
  if (rootMenu.value && Number(menu.id) === Number(rootMenu.value.id)) {
    return `业务根菜单：${menuDisplayLabel(menu) || label}（新增一级分组）`;
  }
  return label;
}

function menuDisplayLabel(menu: MenuConfigMenu | null | undefined) {
  if (!menu) return '';
  const draft = drafts[menu.id];
  return String(
    draft?.custom_label
    || shortMenuLabel(menu.name)
    || shortMenuLabel(menu.display_name)
    || shortMenuLabel(menu.complete_name)
    || menu.name
    || menu.display_name
    || menu.complete_name
    || `菜单 ${menu.id}`,
  ).trim();
}

function shortMenuLabel(value: string | null | undefined) {
  const text = String(value || '').trim();
  if (!text) return '';
  const parts = text.split('/').map((part) => part.trim()).filter(Boolean);
  return parts.length ? parts[parts.length - 1] : text;
}

function menuPathLabel(menu: MenuConfigMenu | null | undefined) {
  if (!menu) return '';
  const path = String(menu.complete_name || '').trim();
  if (path) return path;
  const parent = String(menu.parent_name || '').trim();
  const label = menuDisplayLabel(menu);
  return parent ? `${parent} / ${label}` : (label || '顶层菜单');
}

function menuParentLabel(menu: MenuConfigMenu | null | undefined) {
  if (!menu) return '顶层菜单';
  const parent = String(menu.parent_name || '').trim();
  return parent || '顶层菜单';
}

const {
  initializeTreeCollapse,
  toggleTreeNodeCollapse,
  startTreeDrag,
  updateTreeDragTarget,
  moveTreeNodeOrder,
  applyTreeReorder,
  applyTreeDrop,
  clearTreeDrag,
} = useMenuTreeEditor({
  selectedMenuId,
  collapsedMenuIds,
  dragSourceMenuId,
  dragTargetMenuId,
  dragDropPosition,
  treeDragEnabled,
  tree,
  message,
  selectedMenuPath,
  menuById,
  treeMenuById,
  isRuntimeMenuGroup,
  parentOptionIds,
  draftFor,
  setSaveNotice,
});

const {
  navMenuId,
  navMenuLabel,
  buildTreeFromNavigation,
  mergeNavigationAndConfigTrees,
  runtimeNavigationTreeFromPayload,
  collectNavigationMenuIds,
} = createMenuTreeAdapter({
  isMenuConfigSurfaceMenu: (menu) => isMenuConfigSurfaceMenu(menu),
  scopedNavigationTree: () => scopedNavigationTree(),
});

function returnToBusinessConfig() {
  router.push({
    path: '/admin/business-config',
    query: {
      root_menu_xmlid: route.query.root_menu_xmlid || undefined,
      model: route.query[BUSINESS_CONFIG_ROUTE_FLAGS.returnModel] || route.query.model || undefined,
      action_id: route.query[BUSINESS_CONFIG_ROUTE_FLAGS.returnActionId] || route.query.action_id || undefined,
      menu_id: route.query[BUSINESS_CONFIG_ROUTE_FLAGS.returnMenuId] || undefined,
      page_label: route.query[BUSINESS_CONFIG_ROUTE_FLAGS.returnPageLabel] || route.query.page_label || undefined,
      view_id: route.query[BUSINESS_CONFIG_ROUTE_FLAGS.returnViewId] || route.query.view_id || undefined,
      role_key: route.query[BUSINESS_CONFIG_ROUTE_FLAGS.returnRoleKey] || route.query.role_key || undefined,
      [BUSINESS_CONFIG_ROUTE_FLAGS.openPages]: route.query[BUSINESS_CONFIG_ROUTE_FLAGS.openPages] || '1',
    },
  });
}

async function loadPanel(options: { preserveStatus?: boolean } = {}) {
  loading.value = true;
  const shouldKeepSaveFeedback = String(message.value || saveNotice.value || '').startsWith('已保存');
  if (!options.preserveStatus && !shouldKeepSaveFeedback) {
    error.value = '';
    message.value = '';
    setSaveNotice('');
  }
  try {
    await ensureProductNavigationReady();
    const scopedMenuIds = shouldLoadFullRootMenuConfig.value ? [] : collectNavigationMenuIds();
    const payload = await loadMenuConfigurationPanel({
      menu_ids: scopedMenuIds.length ? scopedMenuIds : undefined,
      root_menu_id: Number(rootMenu.value?.id || 0) || undefined,
      root_menu_xmlid: rootMenuXmlid.value || undefined,
    });
    auditResult.value = null;
    company.value = payload.company || null;
    menus.value = payload.menus || [];
    const menuById = new Map((payload.menus || []).map((menu) => [menu.id, menu]));
    const usedMenuIds = new Set<number>();
    const scopedNavTree = runtimeNavigationTreeFromPayload(payload);
    if (!scopedNavTree.length) {
      throw new Error('菜单配置缺少最终运行时导航树，已阻止回退到原生菜单结构。');
    }
    const navigationTree = buildTreeFromNavigation(scopedNavTree, menuById, usedMenuIds);
    const completeTree = mergeNavigationAndConfigTrees(navigationTree, payload.tree || [], usedMenuIds);
    runtimeState.value = payload.runtime || null;
    tree.value = completeTree;
    const routeMenuId = Number(route.query.menu_id || 0);
    const firstMenuId = completeTree[0]?.id || payload.menus?.[0]?.id || 0;
    if (!selectedMenuId.value || !payload.menus.some((menu) => Number(menu.id) === Number(selectedMenuId.value))) {
      selectedMenuId.value = payload.menus.some((menu) => Number(menu.id) === routeMenuId) ? routeMenuId : firstMenuId;
    }
    initializeTreeCollapse(completeTree);
    groups.value = payload.groups || [];
    Object.keys(drafts).forEach((key) => delete drafts[Number(key)]);
    const nextOriginal: Record<number, DraftPolicy> = {};
    menus.value.forEach((menu) => {
      const policy = payload.policies?.[String(menu.id)];
      const draft = defaultDraft(menu, policy);
      drafts[menu.id] = cloneDraft(draft);
      nextOriginal[menu.id] = cloneDraft(draft);
    });
    originalPolicies.value = nextOriginal;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '菜单配置加载失败';
  } finally {
    loading.value = false;
  }
}

async function loadVersions() {
  versionLoading.value = true;
  error.value = '';
  try {
    const payload = await loadMenuConfigurationVersions({ company_id: company.value?.id || undefined });
    versionState.value = payload;
    const currentVersion = Number(payload.contract?.version_no || 0);
    const fallback = payload.versions.find((version) => version.version_no < currentVersion)
      || payload.versions.find((version) => version.version_no !== currentVersion)
      || payload.versions[0];
    selectedVersionNo.value = Number(fallback?.version_no || 0);
  } catch (err) {
    error.value = err instanceof Error ? err.message : '菜单配置版本加载失败';
  } finally {
    versionLoading.value = false;
  }
}

async function toggleVersionPanel() {
  versionPanelOpen.value = !versionPanelOpen.value;
  if (versionPanelOpen.value) {
    await loadVersions();
  }
}

async function auditMenuConfiguration() {
  auditing.value = true;
  error.value = '';
  message.value = '';
  try {
    const payload = await loadMenuConfigurationAudit({ company_id: company.value?.id || undefined });
    auditResult.value = payload;
    runtimeState.value = payload.runtime || runtimeState.value;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '菜单配置生效检查失败';
  } finally {
    auditing.value = false;
  }
}

async function rollbackSelectedMenuConfiguration() {
  if (!versionState.value?.contract) {
    versionPanelOpen.value = true;
    await loadVersions();
    return;
  }
  if (!canRollbackMenuConfiguration.value) return;
  rollingBack.value = true;
  error.value = '';
  message.value = '';
  auditResult.value = null;
  try {
    const result = await rollbackMenuConfiguration({
      company_id: company.value?.id || undefined,
      version_no: selectedVersionNo.value || undefined,
    });
    await session.loadAppInit({ force: true });
    await loadPanel({ preserveStatus: true });
    if (versionPanelOpen.value) {
      await loadVersions();
    }
    message.value = `已回滚到版本 ${result.rolled_back_to_version}，恢复 ${result.restored_count} 项菜单配置，导航已刷新`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '菜单配置回滚失败';
  } finally {
    rollingBack.value = false;
  }
}

async function requestRollbackMenuConfiguration() {
  if (!selectedRollbackVersion.value) return;
  const confirmed = await confirmImpact(`将菜单配置恢复到版本 ${selectedRollbackVersion.value.version_no}`, '回滚会立即刷新导航；操作后仍可选择其他已发布版本恢复。');
  if (confirmed) await rollbackSelectedMenuConfiguration();
}
async function saveChanges() {
  const rows: MenuConfigSaveRow[] = Object.keys(drafts)
    .map(Number)
    .filter((menuId) => isDirty(menuId))
    .map((menuId) => {
      const draft = drafts[menuId];
      return {
        policy_id: draft.policy_id || undefined,
        menu_id: draft.menu_id,
        target_parent_menu_id: draft.target_parent_menu_id || 0,
        custom_label: draft.custom_label,
        sequence_override: draft.sequence_override || 0,
        visible: draft.visible,
        role_group_ids: draft.role_group_ids,
        note: draft.note,
      };
    });
  if (!rows.length) return;
  saving.value = true;
  error.value = '';
  message.value = '';
  setSaveNotice('');
  try {
    const roleKey = String(route.query[BUSINESS_CONFIG_ROUTE_FLAGS.returnRoleKey] || '').trim();
    const routeToken = String(route.query.change_set_token || '').trim();
    const changeSet = routeToken
      ? { token: routeToken }
      : await openBusinessConfigChangeSet({ role_key: roleKey || undefined });
    await stageBusinessConfigChangeSetItem({
      change_set_token: changeSet.token,
      config_type: 'menu',
      target_key: `menu.config.company.${company.value?.id || session.companyId || 0}`,
      contract_name: `menu.config.company.${company.value?.id || session.companyId || 0}`,
      model: 'ir.ui.menu',
      role_key: roleKey || undefined,
      draft_payload: { rows },
      diff_summary: { summary: `${rows.length} 项菜单显示、名称、位置或角色范围修改` },
      risk_level: 'medium',
    });
    rows.forEach((row) => {
      const draft = drafts[row.menu_id];
      if (draft) originalPolicies.value[row.menu_id] = cloneDraft(draft);
    });
    auditResult.value = null;
    setSaveNotice(`已将 ${rows.length} 项菜单配置加入待发布变更；当前导航尚未改变`);
  } catch (err) {
    error.value = err instanceof Error ? err.message : '菜单配置保存失败';
  } finally {
    saving.value = false;
  }
}
async function requestSaveChanges() {
  const confirmed = await confirmImpact(`将 ${dirtyCount.value} 项菜单修改加入待发布变更`, '当前操作不会改变线上导航；请返回页面设计工作台统一检查并发布。');
  if (confirmed) await saveChanges();
}
function clearCreateMenuRouteFlag() {
  if (String(route.query.create_menu || '').trim() !== '1') return;
  const url = new URL(window.location.href);
  url.searchParams.delete('create_menu');
  window.history.replaceState(window.history.state, '', `${url.pathname}${url.search}${url.hash}`);
}
onMounted(async () => {
  await loadPanel();
  if (String(route.query.create_menu || '').trim() === '1') {
    openCreateMenu('custom');
    clearCreateMenuRouteFlag();
  }
});
</script>

<style scoped src="./menuConfig/style.css"></style>
<style scoped src="./menuConfig/table.css"></style>
<style scoped src="./menuConfig/responsive.css"></style>
