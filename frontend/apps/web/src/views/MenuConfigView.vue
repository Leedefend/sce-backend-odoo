<template>
  <section class="menu-config-page">
    <header class="menu-config-header">
      <div>
        <p class="eyebrow">{{ companyLabel }}</p>
        <h1>菜单配置</h1>
      </div>
      <div class="header-actions">
        <span v-if="dirtyCount" class="dirty-count">{{ dirtyCount }} 项未保存</span>
        <button v-if="canReturnToBusinessConfig" type="button" class="ghost" @click="returnToBusinessConfig">
          返回配置工作台
        </button>
        <button type="button" class="ghost" @click="showGuide = !showGuide">
          {{ showGuide ? '收起说明' : '配置说明' }}
        </button>
        <button type="button" class="ghost" :disabled="loading || auditing || saving" @click="auditMenuConfiguration">
          {{ auditing ? '检查中...' : '生效检查' }}
        </button>
        <button type="button" class="ghost" :disabled="loading || versionLoading || saving" @click="toggleVersionPanel">
          {{ versionPanelOpen ? '收起版本' : (versionLoading ? '加载中...' : '版本') }}
        </button>
        <button type="button" class="ghost" :disabled="loading || saving || rollingBack" @click="rollbackSelectedMenuConfiguration">
          {{ rollingBack ? '回滚中...' : rollbackButtonText }}
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
          <span>优先在左侧树拖动同级菜单排序；需要精确控制时再填写数字。</span>
        </article>
        <article>
          <strong>移动到上级</strong>
          <span>选择新的上级菜单；不移动表示保留当前父级，不能移动到自己或自己的下级。</span>
        </article>
        <article>
          <strong>显示</strong>
          <span>关闭“显示”会对适用范围隐藏菜单；重新勾选后恢复显示。</span>
        </article>
        <article>
          <strong>适用用户组</strong>
          <span>留空表示当前公司所有用户；先按业务域筛选，再选择具体业务角色。</span>
        </article>
        <article>
          <strong>保存生效</strong>
          <span>保存后刷新页面或重新进入系统，导航会按新配置展示。</span>
        </article>
      </div>
    </section>

    <div v-if="error" class="status error">{{ error }}</div>
    <div v-else-if="message" class="status ok">{{ message }}</div>
    <section v-if="auditSummary" class="audit-panel" :class="{ 'audit-panel--warning': auditSummary.notApplicableCount > 0 }">
      <strong>菜单配置生效检查</strong>
      <span>
        配置 {{ auditSummary.configuredCount }} 项，当前用户命中 {{ auditSummary.applicableCount }} 项；
        隐藏 {{ auditSummary.hiddenCount }}，改名 {{ auditSummary.renamedCount }}，移动 {{ auditSummary.movedCount }}，排序 {{ auditSummary.reorderedCount }}。
      </span>
      <span v-if="auditSummary.notApplicableCount">
        {{ auditSummary.notApplicableCount }} 项因用户组范围未命中当前用户。
      </span>
      <span>运行来源：{{ auditSummary.runtimeSourceLabel }}</span>
    </section>
    <section v-if="versionPanelOpen" class="version-panel">
      <div class="version-panel-header">
        <strong>菜单配置版本</strong>
        <span v-if="versionState?.contract">当前版本 {{ versionState.contract.version_no }}</span>
        <span v-else>暂无菜单配置版本</span>
      </div>
      <div v-if="versionState?.versions.length" class="version-list">
        <label
          v-for="version in versionState.versions"
          :key="version.id"
          class="version-item"
          :class="{ selected: selectedVersionNo === version.version_no }"
        >
          <input v-model.number="selectedVersionNo" type="radio" :value="version.version_no" />
          <span class="version-title">版本 {{ version.version_no }}</span>
          <span class="version-meta">
            配置 {{ version.summary.policy_count }} 项，隐藏 {{ version.summary.hidden_count }}，改名 {{ version.summary.renamed_count }}，
            移动 {{ version.summary.moved_count }}，排序 {{ version.summary.reordered_count }}
          </span>
        </label>
      </div>
    </section>

    <div class="menu-config-workspace">
      <aside class="menu-config-tree">
        <div class="tree-search">
          <input v-model="searchText" type="search" placeholder="搜索菜单名称或路径" />
        </div>
        <button
          type="button"
          class="tree-node all"
          :class="{ active: selectedMenuId === 0 }"
          @click="selectMenu(0)"
        >
          全部菜单
        </button>
        <div class="tree-scroll">
          <MenuConfigTree
            :nodes="visibleTree"
            :selected-menu-id="selectedMenuId"
            :drag-source-menu-id="dragSourceMenuId"
            :drag-target-menu-id="dragTargetMenuId"
            :drag-drop-position="dragDropPosition"
            :drag-enabled="treeDragEnabled"
            :search-active="Boolean(normalizedSearchText)"
            :collapsed-menu-ids="collapsedMenuIds"
            @select="selectMenu"
            @drag-start="startTreeDrag"
            @drag-over="updateTreeDragTarget"
            @drop="applyTreeDrop"
            @reorder="applyTreeReorder"
            @drag-end="clearTreeDrag"
            @order-move="moveTreeNodeOrder"
            @toggle-collapse="toggleTreeNodeCollapse"
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
                <th>显示名称</th>
                <th>默认名称</th>
                <th>当前父级</th>
                <th class="level-col">级别</th>
                <th class="sequence-col">顺序</th>
                <th>移动到上级</th>
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
                <td><span class="muted">{{ row.menu.name }}</span></td>
                <td><span class="muted">{{ row.menu.parent_name || '顶层菜单' }}</span></td>
                <td class="level-col">{{ row.level }}</td>
                <td class="sequence-col">
                  <input
                    class="cell-input number-input"
                    type="number"
                    :value="draftFor(row.menu.id).sequence_override || ''"
                    :placeholder="String(row.menu.sequence || 0)"
                    title="可直接在左侧树拖动同级菜单排序，也可在这里输入精确顺序"
                    @input="updateDraft(row.menu.id, { sequence_override: numericValue($event) })"
                  />
                </td>
                <td>
                  <select
                    class="cell-input"
                    :value="draftFor(row.menu.id).target_parent_menu_id || 0"
                    @change="updateDraft(row.menu.id, { target_parent_menu_id: numericValue($event) })"
                  >
                    <option :value="0">不移动</option>
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
                  <div class="group-cell">
                    <div v-if="draftFor(row.menu.id).role_group_ids.length" class="group-chip-list">
                      <span
                        v-for="groupId in draftFor(row.menu.id).role_group_ids"
                        :key="`${row.menu.id}-${groupId}`"
                        class="group-chip"
                        :title="roleGroupName(groupId)"
                      >
                        {{ roleGroupName(groupId) }}
                        <button type="button" title="移除用户组" @click="removeRoleGroup(row.menu.id, groupId)">×</button>
                      </span>
                    </div>
                    <select
                      class="cell-input group-domain-select"
                      :value="roleGroupDomainForMenu(row.menu.id)"
                      @change="setRoleGroupDomain(row.menu.id, inputValue($event))"
                    >
                      <option v-for="domain in roleGroupDomainOptions" :key="domain" :value="domain">
                        {{ domain }}
                      </option>
                    </select>
                    <div class="group-check-list">
                      <label
                        v-for="group in scopedRoleGroupOptions(row.menu.id)"
                        :key="`${row.menu.id}-scope-${group.id}`"
                        class="group-check-item"
                        :title="group.display_name"
                      >
                        <input
                          type="checkbox"
                          :checked="isRoleGroupSelected(row.menu.id, group.id)"
                          @change="toggleRoleGroup(row.menu.id, group.id, checkedValue($event))"
                        />
                        <span>{{ group.display_name }}</span>
                      </label>
                    </div>
                    <button
                      v-if="draftFor(row.menu.id).role_group_ids.length"
                      type="button"
                      class="link-button group-clear"
                      @click="clearRoleGroups(row.menu.id)"
                    >
                      恢复所有用户可见
                    </button>
                    <small>{{ roleScopeSummary(row.menu.id) }}</small>
                  </div>
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
import { useRoute, useRouter } from 'vue-router';
import type { NavNode } from '@sc/schema';
import {
  loadMenuConfigurationAudit,
  loadMenuConfigurationPanel,
  loadMenuConfigurationVersions,
  rollbackMenuConfiguration,
  saveMenuConfigurationPanel,
  type MenuConfigAuditPayload,
  type MenuConfigGroup,
  type MenuConfigMenu,
  type MenuConfigPolicy,
  type MenuConfigSaveRow,
  type MenuConfigVersionsPayload,
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

type DropPosition = 'before' | 'after';

const loading = ref(false);
const saving = ref(false);
const auditing = ref(false);
const rollingBack = ref(false);
const versionLoading = ref(false);
const error = ref('');
const message = ref('');
const auditResult = ref<MenuConfigAuditPayload | null>(null);
const versionState = ref<MenuConfigVersionsPayload | null>(null);
const versionPanelOpen = ref(false);
const selectedVersionNo = ref(0);
const selectedMenuId = ref(0);
const searchText = ref('');
const dragSourceMenuId = ref(0);
const dragTargetMenuId = ref(0);
const dragDropPosition = ref<DropPosition>('after');
const onlyConfigured = ref(false);
const showGuide = ref(false);
const company = ref<{ id: number; name: string } | null>(null);
const menus = ref<MenuConfigMenu[]>([]);
const tree = ref<MenuConfigMenu[]>([]);
const collapsedMenuIds = ref<Set<number>>(new Set());
const groups = ref<MenuConfigGroup[]>([]);
const originalPolicies = ref<Record<number, DraftPolicy>>({});
const drafts = reactive<Record<number, DraftPolicy>>({});
const roleGroupDomainSelections = reactive<Record<number, string>>({});
const session = useSessionStore();
const route = useRoute();
const router = useRouter();
const canReturnToBusinessConfig = computed(() => String(route.query.return_to_business_config || '').trim() === '1');

const MenuConfigTree = defineComponent({
  name: 'MenuConfigTree',
  props: {
    nodes: { type: Array as PropType<MenuConfigMenu[]>, required: true },
    selectedMenuId: { type: Number, required: true },
    dragSourceMenuId: { type: Number, default: 0 },
    dragTargetMenuId: { type: Number, default: 0 },
    dragDropPosition: { type: String as PropType<DropPosition>, default: 'after' },
    dragEnabled: { type: Boolean, default: true },
    searchActive: { type: Boolean, default: false },
    collapsedMenuIds: { type: Object as PropType<Set<number>>, required: true },
    level: { type: Number, default: 0 },
  },
  emits: ['select', 'drag-start', 'drag-over', 'drop', 'drag-end', 'reorder', 'order-move', 'toggle-collapse'],
  setup(props, { emit }) {
    return () => h('ul', { class: ['config-tree-list', `depth-${props.level}`] }, props.nodes.map((node) => {
      const hasChildren = Boolean(node.children?.length);
      const collapsed = hasChildren && !props.searchActive && props.collapsedMenuIds.has(node.id);
      return h('li', { key: node.id }, [
      h('button', {
        type: 'button',
        draggable: false,
        'data-menu-id': String(node.id),
        class: [
          'tree-node',
          {
            active: node.id === props.selectedMenuId,
            draggable: props.dragEnabled,
            dragging: node.id === props.dragSourceMenuId,
            'drop-before': node.id === props.dragTargetMenuId && props.dragDropPosition === 'before',
            'drop-after': node.id === props.dragTargetMenuId && props.dragDropPosition === 'after',
          },
        ],
        style: { paddingLeft: `${8 + props.level * 14}px` },
        title: props.dragEnabled ? '拖动调整同级菜单顺序' : '搜索时不可拖动排序',
        onClick: () => emit('select', node.id),
        onMousedown: (event: MouseEvent) => {
          if (!props.dragEnabled || event.button !== 0) return;
          event.preventDefault();
          emit('drag-start', node.id);
          const resolveTarget = (rawEvent: MouseEvent) => {
            const element = document.elementFromPoint(rawEvent.clientX, rawEvent.clientY)?.closest('.tree-node') as HTMLElement | null;
            const menuId = Number(element?.dataset?.menuId || 0);
            if (!element || !menuId) return null;
            const rect = element.getBoundingClientRect();
            const position: DropPosition = rawEvent.clientY < rect.top + rect.height / 2 ? 'before' : 'after';
            return { menuId, position };
          };
          const cleanup = () => {
            window.removeEventListener('mousemove', handleMove);
            window.removeEventListener('mouseup', handleUp);
          };
          const handleMove = (moveEvent: MouseEvent) => {
            const target = resolveTarget(moveEvent);
            if (target) emit('drag-over', target);
          };
          const handleUp = (upEvent: MouseEvent) => {
            const target = resolveTarget(upEvent);
            cleanup();
            if (target && target.menuId !== node.id) {
              emit('reorder', { sourceId: node.id, targetId: target.menuId, position: target.position });
              return;
            }
            emit('drop', target?.menuId || node.id);
          };
          window.addEventListener('mousemove', handleMove);
          window.addEventListener('mouseup', handleUp, { once: true });
        },
        onDragstart: (event: DragEvent) => {
          if (!props.dragEnabled) return;
          event.dataTransfer?.setData('text/plain', String(node.id));
          event.dataTransfer?.setDragImage(event.currentTarget as Element, 12, 12);
          emit('drag-start', node.id);
        },
        onDragover: (event: DragEvent) => {
          if (!props.dragEnabled) return;
          event.preventDefault();
          const rect = (event.currentTarget as Element).getBoundingClientRect();
          const position: DropPosition = event.clientY < rect.top + rect.height / 2 ? 'before' : 'after';
          emit('drag-over', { menuId: node.id, position });
        },
          onDrop: (event: DragEvent) => {
            if (!props.dragEnabled) return;
            event.preventDefault();
            emit('drop', node.id);
        },
        onDragend: () => emit('drag-end'),
      }, [
        hasChildren
          ? h('span', {
            class: ['branch-marker', 'toggleable', { collapsed }],
            role: 'button',
            title: collapsed ? '展开分组' : '收起分组',
            onMousedown: (event: MouseEvent) => event.stopPropagation(),
            onClick: (event: MouseEvent) => {
              event.stopPropagation();
              emit('toggle-collapse', node.id);
            },
          }, collapsed ? '▸' : '▾')
          : h('span', { class: 'branch-marker' }, ''),
        h('span', node.name),
        props.dragEnabled ? h('span', { class: 'tree-node-order-tools' }, [
          h('span', {
            class: 'tree-node-order-btn',
            title: '上移',
            onMousedown: (event: MouseEvent) => event.stopPropagation(),
            onClick: (event: MouseEvent) => {
              event.stopPropagation();
              emit('order-move', { menuId: node.id, delta: -1 });
            },
          }, '↑'),
          h('span', {
            class: 'tree-node-order-btn',
            title: '下移',
            onMousedown: (event: MouseEvent) => event.stopPropagation(),
            onClick: (event: MouseEvent) => {
              event.stopPropagation();
              emit('order-move', { menuId: node.id, delta: 1 });
            },
          }, '↓'),
        ]) : null,
      ]),
      hasChildren && !collapsed
        ? h(MenuConfigTree, {
          nodes: node.children,
          selectedMenuId: props.selectedMenuId,
          dragSourceMenuId: props.dragSourceMenuId,
          dragTargetMenuId: props.dragTargetMenuId,
          dragDropPosition: props.dragDropPosition,
          dragEnabled: props.dragEnabled,
          searchActive: props.searchActive,
          collapsedMenuIds: props.collapsedMenuIds,
          level: props.level + 1,
          onSelect: (id: number) => emit('select', id),
          onDragStart: (id: number) => emit('drag-start', id),
          onDragOver: (payload: { menuId: number; position: DropPosition }) => emit('drag-over', payload),
          onDrop: (id: number) => emit('drop', id),
          onDragEnd: () => emit('drag-end'),
          onReorder: (payload: { sourceId: number; targetId: number; position: DropPosition }) => emit('reorder', payload),
          onOrderMove: (payload: { menuId: number; delta: number }) => emit('order-move', payload),
          onToggleCollapse: (id: number) => emit('toggle-collapse', id),
        })
        : null,
      ]);
    }));
  },
});

const companyLabel = computed(() => company.value?.name || '当前公司');

const auditSummary = computed(() => {
  const summary = auditResult.value?.summary;
  if (!summary) return null;
  return {
    configuredCount: Number(summary.configured_policy_count || 0),
    applicableCount: Number(summary.applicable_policy_count || 0),
    hiddenCount: Number(summary.hidden_count || 0),
    renamedCount: Number(summary.renamed_count || 0),
    reorderedCount: Number(summary.reordered_count || 0),
    movedCount: Number(summary.moved_count || 0),
    notApplicableCount: Array.isArray(summary.not_applicable_policy_ids) ? summary.not_applicable_policy_ids.length : 0,
    runtimeSourceLabel: summary.runtime_source === 'ui.business.config.contract.menu_orchestration' ? '已发布配置' : '兼容配置',
  };
});

const rollbackButtonText = computed(() => (
  selectedVersionNo.value ? `回滚到版本 ${selectedVersionNo.value}` : '回滚上一版'
));

const groupOptions = computed(() => {
  return [...groups.value].sort((a, b) => a.display_name.localeCompare(b.display_name, 'zh-Hans-CN'));
});

const ALL_ROLE_GROUP_DOMAINS = '全部业务域';

const roleGroupDomainOptions = computed(() => {
  const domains = new Set(groupOptions.value.map((group) => roleGroupDomain(group.display_name)));
  return [
    ALL_ROLE_GROUP_DOMAINS,
    ...Array.from(domains).sort((a, b) => a.localeCompare(b, 'zh-Hans-CN')),
  ];
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
const treeDragEnabled = computed(() => !normalizedSearchText.value);

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

function roleScopeSummary(menuId: number) {
  const count = draftFor(menuId)?.role_group_ids.length || 0;
  return count ? `限 ${count} 个用户组` : '所有用户组';
}

function roleGroupName(groupId: number) {
  const group = groupOptions.value.find((item) => Number(item.id) === Number(groupId));
  return group?.display_name || `用户组 ${groupId}`;
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

function clearRoleGroups(menuId: number) {
  updateDraft(menuId, { role_group_ids: [] });
}

function updateDraft(menuId: number, patch: Partial<DraftPolicy>) {
  const draft = drafts[menuId];
  if (!draft) return;
  Object.assign(draft, patch);
  message.value = '';
  auditResult.value = null;
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

function removeRoleGroup(menuId: number, groupId: number) {
  const draft = draftFor(menuId);
  if (!draft) return;
  updateDraft(menuId, { role_group_ids: draft.role_group_ids.filter((item) => Number(item) !== Number(groupId)) });
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

function initializeTreeCollapse(items: MenuConfigMenu[]) {
  const selectedPath = selectedMenuPath(items, selectedMenuId.value);
  const next = new Set<number>();
  const walk = (rows: MenuConfigMenu[]) => {
    rows.forEach((item) => {
      if (item.children?.length) {
        if (!selectedPath.has(item.id)) next.add(item.id);
        walk(item.children);
      }
    });
  };
  walk(items);
  collapsedMenuIds.value = next;
}

function toggleTreeNodeCollapse(menuId: number) {
  const next = new Set(collapsedMenuIds.value);
  if (next.has(menuId)) next.delete(menuId);
  else next.add(menuId);
  collapsedMenuIds.value = next;
}

function startTreeDrag(menuId: number) {
  if (!treeDragEnabled.value) return;
  dragSourceMenuId.value = menuId;
  dragTargetMenuId.value = 0;
  dragDropPosition.value = 'after';
}

function updateTreeDragTarget(payload: { menuId: number; position: DropPosition }) {
  if (!dragSourceMenuId.value || payload.menuId === dragSourceMenuId.value) return;
  if (!areVisualSiblings(tree.value, dragSourceMenuId.value, payload.menuId)) {
    dragTargetMenuId.value = 0;
    return;
  }
  dragTargetMenuId.value = payload.menuId;
  dragDropPosition.value = payload.position;
}

function reorderSiblingBranch(items: MenuConfigMenu[], sourceId: number, targetId: number, position: DropPosition): MenuConfigMenu[] {
  const ids = items.map((item) => item.id);
  if (ids.includes(sourceId) && ids.includes(targetId)) {
    const source = items.find((item) => item.id === sourceId);
    if (!source) return items;
    const next = items.filter((item) => item.id !== sourceId);
    const targetIndex = next.findIndex((item) => item.id === targetId);
    if (targetIndex < 0) return items;
    next.splice(position === 'before' ? targetIndex : targetIndex + 1, 0, source);
    return next.map((item, index) => {
      const draft = draftFor(item.id);
      if (draft) {
        draft.sequence_override = (index + 1) * 10;
      }
      return item;
    });
  }

  return items.map((item) => {
    if (!item.children?.length) return item;
    return { ...item, children: reorderSiblingBranch(item.children, sourceId, targetId, position) };
  });
}

function moveTreeNodeOrder(payload: { menuId: number; delta: number }) {
  const moveInBranch = (items: MenuConfigMenu[]): { rows: MenuConfigMenu[]; moved: boolean } => {
    const index = items.findIndex((item) => item.id === payload.menuId);
    if (index >= 0) {
      const targetIndex = index + payload.delta;
      if (targetIndex < 0 || targetIndex >= items.length) return { rows: items, moved: false };
      const next = [...items];
      const [moved] = next.splice(index, 1);
      next.splice(targetIndex, 0, moved);
      next.forEach((item, itemIndex) => {
        const draft = draftFor(item.id);
        if (draft) draft.sequence_override = (itemIndex + 1) * 10;
      });
      return { rows: next, moved: true };
    }
    let moved = false;
    const rows = items.map((item) => {
      if (!item.children?.length || moved) return item;
      const result = moveInBranch(item.children);
      moved = result.moved;
      return result.moved ? { ...item, children: result.rows } : item;
    });
    return { rows, moved };
  };
  const result = moveInBranch(tree.value);
  if (!result.moved) return;
  tree.value = result.rows;
  message.value = '';
}

function applyTreeReorder(payload: { sourceId: number; targetId: number; position: DropPosition }) {
  if (!payload.sourceId || !payload.targetId || payload.sourceId === payload.targetId) {
    clearTreeDrag();
    return;
  }
  if (!areVisualSiblings(tree.value, payload.sourceId, payload.targetId)) {
    clearTreeDrag();
    return;
  }
  tree.value = reorderSiblingBranch(tree.value, payload.sourceId, payload.targetId, payload.position);
  message.value = '';
  clearTreeDrag();
}

function applyTreeDrop(targetId: number) {
  const sourceId = dragSourceMenuId.value;
  if (!sourceId || !targetId || sourceId === targetId || !dragTargetMenuId.value) {
    clearTreeDrag();
    return;
  }
  tree.value = reorderSiblingBranch(tree.value, sourceId, targetId, dragDropPosition.value);
  message.value = '';
  clearTreeDrag();
}

function clearTreeDrag() {
  dragSourceMenuId.value = 0;
  dragTargetMenuId.value = 0;
  dragDropPosition.value = 'after';
}

function areVisualSiblings(items: MenuConfigMenu[], sourceId: number, targetId: number): boolean {
  const ids = items.map((item) => item.id);
  if (ids.includes(sourceId) && ids.includes(targetId)) return true;
  return items.some((item) => item.children?.length && areVisualSiblings(item.children, sourceId, targetId));
}

function navMenuId(node: NavNode) {
  return Number(node.menu_id || node.meta?.menu_id || node.id || 0);
}

function navMenuLabel(node: NavNode) {
  return String(node.title || node.name || node.label || '').trim();
}

function normalizedMenuLabel(value: string) {
  return String(value || '').trim().toLowerCase();
}

function buildTreeFromNavigation(
  navNodes: NavNode[],
  menuById: Map<number, MenuConfigMenu>,
  menuByLabel: Map<string, MenuConfigMenu[]>,
  usedMenuIds = new Set<number>(),
): MenuConfigMenu[] {
  return navNodes.flatMap((node) => {
    const menuId = navMenuId(node);
    const label = navMenuLabel(node);
    let menu = menuById.get(menuId);
    if (menu && usedMenuIds.has(menu.id)) {
      menu = undefined;
    }
    if (!menu) {
      const candidates = menuByLabel.get(normalizedMenuLabel(label)) || [];
      menu = candidates.find((candidate) => !usedMenuIds.has(candidate.id));
    }
    if (!menu) {
      return Array.isArray(node.children)
        ? buildTreeFromNavigation(node.children as NavNode[], menuById, menuByLabel, usedMenuIds)
        : [];
    }
    usedMenuIds.add(menu.id);
    return [{
      ...menu,
      name: label || menu.name,
      display_name: label || menu.display_name,
      sequence: Number(node.sequence ?? node.meta?.sequence ?? menu.sequence ?? 0),
      children: Array.isArray(node.children)
        ? buildTreeFromNavigation(node.children as NavNode[], menuById, menuByLabel, usedMenuIds)
        : [],
    }];
  });
}

function collectNavigationMenuIds() {
  const ids: number[] = [];
  const seen = new Set<number>();
  const walk = (items: Array<{ menu_id?: number; id?: number; children?: unknown[] }>) => {
    items.forEach((item) => {
      const menuId = navMenuId(item as NavNode);
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

function removeMenuIdsFromNavigation(nodes: NavNode[], hiddenMenuIds: Set<number>): NavNode[] {
  return nodes
    .filter((node) => !hiddenMenuIds.has(Number(node.menu_id || node.id || 0)))
    .map((node) => ({
      ...node,
      children: Array.isArray(node.children)
        ? removeMenuIdsFromNavigation(node.children as NavNode[], hiddenMenuIds)
        : node.children,
    }));
}

function applySavedVisibilityToNavigation(rows: MenuConfigSaveRow[]) {
  const hiddenMenuIds = new Set(rows.filter((row) => row.visible === false).map((row) => Number(row.menu_id || 0)).filter(Boolean));
  if (!hiddenMenuIds.size) return;
  session.menuTree = removeMenuIdsFromNavigation(session.menuTree as NavNode[], hiddenMenuIds);
  session.menuExpandedKeys = session.menuExpandedKeys.filter((key) => !hiddenMenuIds.has(Number(String(key).replace(/^menu:/, ''))));
  session.persist();
}

function returnToBusinessConfig() {
  router.push({
    path: '/admin/business-config',
    query: {
      root_menu_xmlid: route.query.root_menu_xmlid || undefined,
      model: route.query.model || undefined,
      action_id: route.query.action_id || undefined,
      menu_id: route.query.menu_id || undefined,
      page_label: route.query.page_label || undefined,
      open_pages: route.query.open_pages || '1',
    },
  });
}

async function loadPanel() {
  loading.value = true;
  error.value = '';
  message.value = '';
  try {
    const payload = await loadMenuConfigurationPanel({ menu_ids: collectNavigationMenuIds() });
    auditResult.value = null;
    company.value = payload.company || null;
    menus.value = payload.menus || [];
    const menuById = new Map((payload.menus || []).map((menu) => [menu.id, menu]));
    const menuByLabel = new Map<string, MenuConfigMenu[]>();
    (payload.menus || []).forEach((menu) => {
      const labels = [menu.name, menu.display_name].map(normalizedMenuLabel).filter(Boolean);
      labels.forEach((label) => {
        const list = menuByLabel.get(label) || [];
        list.push(menu);
        menuByLabel.set(label, list);
      });
    });
    const navOrderedTree = buildTreeFromNavigation(session.menuTree as NavNode[], menuById, menuByLabel);
    tree.value = navOrderedTree;
    initializeTreeCollapse(navOrderedTree);
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
    auditResult.value = await loadMenuConfigurationAudit({ company_id: company.value?.id || undefined });
  } catch (err) {
    error.value = err instanceof Error ? err.message : '菜单配置生效检查失败';
  } finally {
    auditing.value = false;
  }
}

async function rollbackSelectedMenuConfiguration() {
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
    await loadPanel();
    if (versionPanelOpen.value) {
      await loadVersions();
    }
    message.value = `已回滚到版本 ${result.rolled_back_to_version}，恢复 ${result.restored_count} 项菜单配置`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '菜单配置回滚失败';
  } finally {
    rollingBack.value = false;
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
    applySavedVisibilityToNavigation(rows);
    await session.loadAppInit({ force: true });
    await loadPanel();
    auditResult.value = null;
    if (versionPanelOpen.value) {
      await loadVersions();
    }
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

.audit-panel {
  margin: 0 18px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  padding: 10px 12px;
  border: 1px solid var(--sc-app-info-border);
  border-radius: 6px;
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
  font-size: 13px;
}

.audit-panel strong {
  color: var(--sc-app-text-primary);
}

.audit-panel--warning {
  border-color: var(--sc-app-warning-border);
  background: var(--sc-app-warning-bg);
  color: var(--sc-app-warning-text);
}

.version-panel {
  margin: 0 18px;
  display: grid;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel);
  font-size: 13px;
}

.version-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.version-panel-header span {
  color: var(--sc-app-text-secondary);
}

.version-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 8px;
  max-height: 142px;
  overflow: auto;
}

.version-item {
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(64px, auto) minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  padding: 8px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-muted-bg);
  cursor: pointer;
}

.version-item.selected {
  border-color: var(--sc-semantic-surface-interactive);
  background: var(--sc-app-info-bg);
}

.version-title {
  font-weight: 600;
}

.version-meta {
  min-width: 0;
  color: var(--sc-app-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-config-workspace {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
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

:deep(.tree-node) {
  width: 100%;
  min-height: 30px;
  display: flex;
  align-items: center;
  gap: 6px;
  border: 0;
  border-radius: 4px;
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

:deep(.tree-node.active) {
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
  font-weight: 600;
}

:deep(.tree-node.draggable) {
  cursor: grab;
  user-select: none;
}

:deep(.tree-node.draggable:hover) {
  background: var(--sc-app-muted-bg);
}

:deep(.tree-node.dragging) {
  cursor: grabbing;
  opacity: 0.45;
}

:deep(.tree-node.drop-before) {
  box-shadow: inset 0 2px 0 var(--sc-semantic-surface-interactive);
}

:deep(.tree-node.drop-after) {
  box-shadow: inset 0 -2px 0 var(--sc-semantic-surface-interactive);
}

.branch-marker {
  width: 12px;
  flex: 0 0 12px;
  color: var(--sc-app-text-secondary);
}

:deep(.branch-marker) {
  width: 12px;
  flex: 0 0 12px;
  color: var(--sc-app-text-secondary);
}

:deep(.branch-marker.toggleable) {
  cursor: pointer;
}

:deep(.branch-marker.toggleable:hover) {
  color: var(--sc-app-text-primary);
}

:deep(.tree-node-order-tools) {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
}

:deep(.tree-node:hover .tree-node-order-tools),
:deep(.tree-node.active .tree-node-order-tools) {
  opacity: 1;
}

:deep(.tree-node-order-btn) {
  width: 22px;
  height: 22px;
  display: inline-grid;
  place-items: center;
  border: 1px solid var(--sc-app-border);
  border-radius: 4px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
}

:deep(.tree-node-order-btn:hover) {
  border-color: var(--sc-app-border-strong);
  color: var(--sc-app-text-primary);
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
  min-width: 840px;
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
  width: 36px;
}

.level-col {
  width: 42px;
}

.sequence-col {
  width: 54px;
}

.check-col {
  width: 42px;
}

.name-col {
  width: 108px;
}

.default-col {
  width: 104px;
}

.parent-col {
  width: 106px;
}

.move-col {
  width: 120px;
}

.groups-col {
  width: 220px;
}

.note-col {
  width: 104px;
}

.muted {
  display: inline-block;
  max-width: 100%;
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

.group-domain-select {
  min-width: 0;
  height: 30px;
  padding: 0 6px;
}

.group-cell {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.group-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  max-height: 64px;
  overflow: auto;
}

.group-check-list {
  display: grid;
  gap: 2px;
  max-height: 96px;
  overflow: auto;
  padding: 3px;
  border: 1px solid var(--sc-app-border);
  border-radius: 4px;
  background: var(--sc-app-panel);
}

.group-check-item {
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr);
  align-items: center;
  min-width: 0;
  gap: 4px;
  color: var(--sc-app-text-primary);
  font-size: 11px;
  line-height: 1.3;
}

.group-check-item input {
  margin: 0;
}

.group-check-item span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-clear {
  justify-self: start;
  padding: 0;
  font-size: 11px;
  line-height: 1.2;
}

.group-chip {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  min-width: 0;
  gap: 4px;
  border: 1px solid var(--sc-app-border);
  border-radius: 4px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  font-size: 11px;
  line-height: 1.4;
  padding: 2px 4px 2px 6px;
}

.group-chip button {
  flex: 0 0 auto;
  border: 0;
  background: transparent;
  color: var(--sc-app-text-secondary);
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
  padding: 0 2px;
}

.group-chip button:hover {
  color: var(--sc-app-danger-text);
}

.group-cell small {
  overflow: hidden;
  color: var(--sc-app-text-secondary);
  font-size: 11px;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
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
