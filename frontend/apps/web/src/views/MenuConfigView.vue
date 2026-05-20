<template>
  <section class="menu-config-page">
    <header class="menu-config-header">
      <div>
        <p class="eyebrow">{{ companyLabel }}</p>
        <h1>菜单配置</h1>
      </div>
      <div class="header-actions">
        <span v-if="dirtyCount" class="dirty-count">{{ dirtyCount }} 项未保存</span>
        <button type="button" class="ghost" @click="showGuide = !showGuide">
          {{ showGuide ? '收起说明' : '配置说明' }}
        </button>
        <button type="button" class="ghost" :disabled="loading || saving" @click="loadPanel">刷新</button>
        <button type="button" class="primary" :disabled="!dirtyCount || saving" @click="saveChanges">
          {{ saving ? '保存中...' : '保存修改' }}
        </button>
      </div>
    </header>

    <section v-if="showGuide" class="guide-panel">
      <div>
        <h2>配置口径</h2>
        <p>这里只配置当前导航中实际出现的菜单；没有进入导航的技术菜单不进入配置范围。</p>
      </div>
      <div class="guide-grid">
        <article>
          <strong>菜单名称</strong>
          <span>填写后覆盖导航显示名；留空则使用默认名称。</span>
        </article>
        <article>
          <strong>排序号</strong>
          <span>填写后覆盖默认排序；留空或 0 时保留原顺序。</span>
        </article>
        <article>
          <strong>调整到分组</strong>
          <span>把菜单移动到导航内其他分组；不能移动到自己或自己的下级。</span>
        </article>
        <article>
          <strong>显示</strong>
          <span>关闭“显示”会对适用范围隐藏菜单；重新勾选后恢复显示。</span>
        </article>
        <article>
          <strong>适用用户组</strong>
          <span>留空表示当前公司所有用户；选择用户组后仅对这些用户组生效。</span>
        </article>
        <article>
          <strong>保存生效</strong>
          <span>保存后刷新页面或重新进入系统，导航会按新配置展示。</span>
        </article>
      </div>
    </section>

    <div v-if="error" class="status error">{{ error }}</div>
    <div v-else-if="message" class="status ok">{{ message }}</div>

    <div class="menu-config-workspace">
      <aside class="menu-config-tree">
        <div class="tree-search">
          <input v-model="searchText" type="search" placeholder="搜索菜单名称或路径" />
        </div>
        <button
          type="button"
          class="tree-node all"
          :class="{ active: selectedMenuId === 0 }"
          @click="selectedMenuId = 0"
        >
          全部菜单
        </button>
        <div class="tree-scroll">
          <MenuConfigTree
            :nodes="visibleTree"
            :selected-menu-id="selectedMenuId"
            @select="selectMenu"
          />
        </div>
      </aside>

      <main class="menu-config-table-panel">
        <div class="table-toolbar">
          <div>
            <strong>{{ filteredRows.length }}</strong>
            <span>条菜单</span>
          </div>
          <label class="toggle-filter">
            <input v-model="onlyConfigured" type="checkbox" />
            只看已配置
          </label>
        </div>

        <div v-if="loading" class="loading-state">正在加载菜单配置...</div>
        <div v-else class="table-wrap">
          <table>
            <colgroup>
              <col class="index-col" />
              <col class="name-col" />
              <col class="default-col" />
              <col class="parent-col" />
              <col class="level-col" />
              <col class="sequence-col" />
              <col class="move-col" />
              <col class="check-col" />
              <col class="groups-col" />
              <col class="note-col" />
            </colgroup>
            <thead>
              <tr>
                <th class="index-col">#</th>
                <th>菜单名称</th>
                <th>默认名称</th>
                <th>父级</th>
                <th class="level-col">级别</th>
                <th class="sequence-col">排序号</th>
                <th>调整到分组</th>
                <th class="check-col">显示</th>
                <th>适用用户组</th>
                <th>备注</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, index) in filteredRows"
                :key="row.menu.id"
                :class="{ selected: row.menu.id === selectedMenuId, dirty: isDirty(row.menu.id) }"
              >
                <td class="index-col">{{ index + 1 }}</td>
                <td>
                  <input
                    class="cell-input name-input"
                    :value="draftFor(row.menu.id).custom_label"
                    :placeholder="row.menu.name"
                    @input="updateDraft(row.menu.id, { custom_label: inputValue($event) })"
                  />
                </td>
                <td class="muted">{{ row.menu.name }}</td>
                <td class="muted">{{ row.menu.parent_name || '顶层菜单' }}</td>
                <td class="level-col">{{ row.level }}</td>
                <td class="sequence-col">
                  <input
                    class="cell-input number-input"
                    type="number"
                    :value="draftFor(row.menu.id).sequence_override || ''"
                    :placeholder="String(row.menu.sequence || 0)"
                    @input="updateDraft(row.menu.id, { sequence_override: numericValue($event) })"
                  />
                </td>
                <td>
                  <select
                    class="cell-input"
                    :value="draftFor(row.menu.id).target_parent_menu_id || 0"
                    @change="updateDraft(row.menu.id, { target_parent_menu_id: numericValue($event) })"
                  >
                    <option :value="0">保留当前分组</option>
                    <option
                      v-for="target in parentOptions(row.menu.id)"
                      :key="target.id"
                      :value="target.id"
                    >
                      {{ target.complete_name || target.name }}
                    </option>
                  </select>
                </td>
                <td class="check-col">
                  <input
                    type="checkbox"
                    :checked="draftFor(row.menu.id).visible"
                    @change="updateDraft(row.menu.id, { visible: checkedValue($event) })"
                  />
                </td>
                <td>
                  <select
                    class="cell-input group-select"
                    multiple
                    :value="draftFor(row.menu.id).role_group_ids.map(String)"
                    @change="updateDraft(row.menu.id, { role_group_ids: selectedValues($event) })"
                  >
                    <option v-for="group in groupOptions" :key="group.id" :value="group.id">
                      {{ group.display_name }}
                    </option>
                  </select>
                </td>
                <td>
                  <input
                    class="cell-input note-input"
                    :value="draftFor(row.menu.id).note"
                    placeholder="可选"
                    @input="updateDraft(row.menu.id, { note: inputValue($event) })"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref, type PropType } from 'vue';
import {
  loadMenuConfigurationPanel,
  saveMenuConfigurationPanel,
  type MenuConfigGroup,
  type MenuConfigMenu,
  type MenuConfigPolicy,
  type MenuConfigSaveRow,
} from '../api/menuConfig';
import { useSessionStore } from '../stores/session';

type DraftPolicy = {
  policy_id: number;
  menu_id: number;
  target_parent_menu_id: number;
  custom_label: string;
  sequence_override: number;
  visible: boolean;
  role_group_ids: number[];
  note: string;
};

type FlatRow = {
  menu: MenuConfigMenu;
  level: number;
};

const loading = ref(false);
const saving = ref(false);
const error = ref('');
const message = ref('');
const selectedMenuId = ref(0);
const searchText = ref('');
const onlyConfigured = ref(false);
const showGuide = ref(false);
const company = ref<{ id: number; name: string } | null>(null);
const menus = ref<MenuConfigMenu[]>([]);
const tree = ref<MenuConfigMenu[]>([]);
const groups = ref<MenuConfigGroup[]>([]);
const originalPolicies = ref<Record<number, DraftPolicy>>({});
const drafts = reactive<Record<number, DraftPolicy>>({});
const session = useSessionStore();

const MenuConfigTree = defineComponent({
  name: 'MenuConfigTree',
  props: {
    nodes: { type: Array as PropType<MenuConfigMenu[]>, required: true },
    selectedMenuId: { type: Number, required: true },
    level: { type: Number, default: 0 },
  },
  emits: ['select'],
  setup(props, { emit }) {
    return () => h('ul', { class: ['config-tree-list', `depth-${props.level}`] }, props.nodes.map((node) => h('li', { key: node.id }, [
      h('button', {
        type: 'button',
        class: ['tree-node', { active: node.id === props.selectedMenuId }],
        style: { paddingLeft: `${8 + props.level * 14}px` },
        onClick: () => emit('select', node.id),
      }, [
        node.children?.length ? h('span', { class: 'branch-marker' }, '▸') : h('span', { class: 'branch-marker' }, ''),
        h('span', node.name),
      ]),
      node.children?.length
        ? h(MenuConfigTree, {
          nodes: node.children,
          selectedMenuId: props.selectedMenuId,
          level: props.level + 1,
          onSelect: (id: number) => emit('select', id),
        })
        : null,
    ])));
  },
});

const companyLabel = computed(() => company.value?.name || '当前公司');

const groupOptions = computed(() => {
  return [...groups.value].sort((a, b) => a.display_name.localeCompare(b.display_name, 'zh-Hans-CN'));
});

const flatRows = computed<FlatRow[]>(() => {
  const out: FlatRow[] = [];
  const walk = (items: MenuConfigMenu[], level = 1) => {
    items.forEach((item) => {
      out.push({ menu: item, level });
      if (item.children?.length) walk(item.children, level + 1);
    });
  };
  walk(tree.value);
  return out;
});

const normalizedSearchText = computed(() => searchText.value.trim().toLowerCase());

function menuSearchText(menu: MenuConfigMenu) {
  const draft = drafts[menu.id];
  return [
    menu.name,
    menu.display_name,
    menu.complete_name,
    menu.parent_name,
    menu.xmlid,
    menu.action,
    ...(menu.group_names || []),
    draft?.custom_label || '',
    draft?.note || '',
  ].join(' ').toLowerCase();
}

function menuMatchesSearch(menu: MenuConfigMenu) {
  const term = normalizedSearchText.value;
  if (!term) return true;
  return menuSearchText(menu).includes(term);
}

const visibleTree = computed<MenuConfigMenu[]>(() => {
  const term = normalizedSearchText.value;
  if (!term) return tree.value;

  const filterBranch = (items: MenuConfigMenu[]): MenuConfigMenu[] => {
    return items.flatMap((item) => {
      const children = filterBranch(item.children || []);
      if (children.length || menuMatchesSearch(item)) {
        return [{ ...item, children }];
      }
      return [];
    });
  };

  return filterBranch(tree.value);
});

const selectedIds = computed(() => {
  if (!selectedMenuId.value) return new Set<number>();
  const out = new Set<number>();
  const walk = (items: MenuConfigMenu[]) => {
    items.forEach((item) => {
      if (item.id === selectedMenuId.value || out.has(item.parent_id)) {
        out.add(item.id);
      }
      if (item.children?.length) walk(item.children);
    });
  };
  walk(tree.value);
  return out;
});

const filteredRows = computed(() => {
  const term = normalizedSearchText.value;
  return flatRows.value.filter((row) => {
    if (!term && selectedMenuId.value && !selectedIds.value.has(row.menu.id)) return false;
    if (onlyConfigured.value && !hasConfiguration(row.menu.id)) return false;
    if (!term) return true;
    return menuMatchesSearch(row.menu);
  });
});

const dirtyCount = computed(() => Object.keys(drafts).filter((key) => isDirty(Number(key))).length);

function defaultDraft(menu: MenuConfigMenu, policy?: MenuConfigPolicy): DraftPolicy {
  return {
    policy_id: Number(policy?.id || 0),
    menu_id: menu.id,
    target_parent_menu_id: Number(policy?.target_parent_menu_id || 0),
    custom_label: String(policy?.custom_label || ''),
    sequence_override: Number(policy?.sequence_override || 0),
    visible: policy?.visible ?? true,
    role_group_ids: Array.isArray(policy?.role_group_ids) ? policy.role_group_ids.map(Number).filter(Boolean) : [],
    note: String(policy?.note || ''),
  };
}

function cloneDraft(draft: DraftPolicy): DraftPolicy {
  return {
    ...draft,
    role_group_ids: [...draft.role_group_ids],
  };
}

function normalizeDraft(draft: DraftPolicy) {
  return JSON.stringify({
    policy_id: draft.policy_id || 0,
    menu_id: draft.menu_id,
    target_parent_menu_id: draft.target_parent_menu_id || 0,
    custom_label: draft.custom_label.trim(),
    sequence_override: Number(draft.sequence_override || 0),
    visible: Boolean(draft.visible),
    role_group_ids: [...draft.role_group_ids].map(Number).filter(Boolean).sort((a, b) => a - b),
    note: draft.note.trim(),
  });
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

function updateDraft(menuId: number, patch: Partial<DraftPolicy>) {
  const draft = drafts[menuId];
  if (!draft) return;
  Object.assign(draft, patch);
  message.value = '';
}

function inputValue(event: Event) {
  return String((event.target as HTMLInputElement).value || '');
}

function numericValue(event: Event) {
  return Number((event.target as HTMLInputElement | HTMLSelectElement).value || 0);
}

function checkedValue(event: Event) {
  return Boolean((event.target as HTMLInputElement).checked);
}

function selectedValues(event: Event) {
  return Array.from((event.target as HTMLSelectElement).selectedOptions)
    .map((option) => Number(option.value || 0))
    .filter(Boolean);
}

function parentOptions(menuId: number) {
  const excluded = descendantsFor(menuId);
  excluded.add(menuId);
  return menus.value
    .filter((item) => !excluded.has(item.id))
    .sort((a, b) => (a.complete_name || a.name).localeCompare(b.complete_name || b.name, 'zh-Hans-CN'));
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

function collectNavigationMenuIds() {
  const ids: number[] = [];
  const seen = new Set<number>();
  const walk = (items: Array<{ menu_id?: number; id?: number; children?: unknown[] }>) => {
    items.forEach((item) => {
      const menuId = Number(item.menu_id || item.id || 0);
      if (Number.isFinite(menuId) && menuId > 0 && !seen.has(menuId)) {
        seen.add(menuId);
        ids.push(menuId);
      }
      if (Array.isArray(item.children)) {
        walk(item.children as Array<{ menu_id?: number; id?: number; children?: unknown[] }>);
      }
    });
  };
  walk(session.menuTree || []);
  return ids;
}

async function loadPanel() {
  loading.value = true;
  error.value = '';
  message.value = '';
  try {
    const payload = await loadMenuConfigurationPanel({ menu_ids: collectNavigationMenuIds() });
    company.value = payload.company || null;
    menus.value = payload.menus || [];
    tree.value = payload.tree || [];
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
  try {
    await saveMenuConfigurationPanel({ rows });
    await loadPanel();
    message.value = `已保存 ${rows.length} 项菜单配置`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '菜单配置保存失败';
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  void loadPanel();
});
</script>

<style scoped>
.menu-config-page {
  display: grid;
  gap: 12px;
  min-height: calc(100vh - 96px);
}

.menu-config-header {
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
  font-weight: 700;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dirty-count {
  color: var(--sc-app-warning-text);
  font-size: 13px;
}

.ghost,
.primary {
  min-height: 34px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 14px;
  cursor: pointer;
}

.ghost {
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
}

.primary {
  border-color: var(--sc-semantic-surface-interactive);
  background: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
}

.ghost:disabled,
.primary:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.status {
  margin: 0 18px;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.guide-panel {
  display: grid;
  gap: 12px;
  margin: 0 18px;
  padding: 14px 16px;
  border: 1px solid var(--sc-app-info-border);
  border-radius: 8px;
  background: var(--sc-app-info-bg);
  color: var(--sc-app-text-primary);
}

.guide-panel h2 {
  margin: 0 0 4px;
  font-size: 15px;
}

.guide-panel p {
  margin: 0;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.guide-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.guide-grid article {
  min-width: 0;
  display: grid;
  gap: 4px;
  padding: 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel);
}

.guide-grid strong {
  font-size: 13px;
}

.guide-grid span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  line-height: 1.45;
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

.menu-config-workspace {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  min-height: 0;
  padding: 0 18px 18px;
}

.menu-config-tree {
  min-width: 0;
  border: 1px solid var(--sc-app-border);
  border-right: 0;
  background: var(--sc-app-panel);
}

.tree-search {
  padding: 10px;
  border-bottom: 1px solid var(--sc-app-border);
}

.tree-search input {
  width: 100%;
  min-height: 32px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 10px;
}

.tree-scroll {
  overflow: auto;
  max-height: calc(100vh - 220px);
  padding: 6px;
}

:deep(.config-tree-list) {
  list-style: none;
  margin: 0;
  padding: 0;
}

.tree-node {
  width: 100%;
  min-height: 30px;
  display: flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: transparent;
  color: var(--sc-app-text-primary);
  text-align: left;
  cursor: pointer;
}

.tree-node.all {
  padding: 8px 12px;
  border-bottom: 1px solid var(--sc-app-border);
  font-weight: 600;
}

.tree-node.active {
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
  font-weight: 600;
}

.branch-marker {
  width: 12px;
  flex: 0 0 12px;
  color: var(--sc-app-text-secondary);
}

.menu-config-table-panel {
  min-width: 0;
  border: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
}

.table-toolbar {
  min-height: 42px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 12px;
  border-bottom: 1px solid var(--sc-app-border);
}

.toggle-filter {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--sc-app-text-secondary);
}

.loading-state {
  padding: 28px;
  color: var(--sc-app-text-secondary);
}

.table-wrap {
  overflow: auto;
  max-height: calc(100vh - 220px);
}

table {
  width: 100%;
  min-width: 1180px;
  table-layout: fixed;
  border-collapse: collapse;
  font-size: 13px;
}

th,
td {
  min-width: 0;
  border-bottom: 1px solid var(--sc-app-border);
  border-right: 1px solid var(--sc-app-border);
  padding: 6px;
  vertical-align: middle;
  overflow: hidden;
}

th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--sc-app-muted-bg);
  color: var(--sc-app-text-secondary);
  font-weight: 600;
  text-align: left;
}

tr.selected td {
  background: var(--sc-app-info-bg);
}

tr.dirty td:first-child {
  box-shadow: inset 3px 0 0 var(--sc-app-warning-text);
}

.index-col,
.level-col,
.sequence-col,
.check-col {
  text-align: center;
  white-space: nowrap;
}

.index-col {
  width: 52px;
}

.level-col {
  width: 64px;
}

.sequence-col {
  width: 86px;
}

.check-col {
  width: 62px;
}

.name-col {
  width: 150px;
}

.default-col {
  width: 140px;
}

.parent-col {
  width: 150px;
}

.move-col {
  width: 190px;
}

.groups-col {
  width: 210px;
}

.note-col {
  width: 150px;
}

.muted {
  display: block;
  overflow: hidden;
  color: var(--sc-app-text-secondary);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-input {
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 30px;
  border: 1px solid var(--sc-app-border);
  border-radius: 4px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  padding: 0 8px;
}

.number-input {
  text-align: center;
}

.group-select {
  min-width: 0;
  min-height: 54px;
  padding: 4px 6px;
}

.note-input {
  min-width: 0;
}

@media (max-width: 900px) {
  .guide-grid {
    grid-template-columns: 1fr;
  }

  .menu-config-workspace {
    grid-template-columns: 1fr;
  }

  .menu-config-tree {
    border-right: 1px solid var(--sc-app-border);
  }

  .tree-scroll,
  .table-wrap {
    max-height: none;
  }
}
</style>
