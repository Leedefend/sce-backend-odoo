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
        <button type="button" class="ghost" :disabled="loading || saving" @click="loadPanel()">刷新</button>
        <button type="button" class="ghost" :disabled="loading || saving || creatingMenu" @click="openCreateMenu('custom')">
          新增菜单
        </button>
        <button type="button" class="primary" :disabled="!dirtyCount || saving" @click="saveChanges">
          {{ saving ? '保存中...' : '保存修改' }}
        </button>
      </div>
    </header>

    <section v-if="showGuide" class="guide-panel">
      <div>
        <h2>配置口径</h2>
        <p>这里只配置当前导航中实际出现的菜单；未面向业务用户开放的入口不进入配置范围。</p>
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
          <span>可在当前菜单面板选择新的上级菜单，也可在左侧树拖到目标分组；不能移动到自己或自己的下级。</span>
        </article>
        <article>
          <strong>显示</strong>
          <span>关闭“显示”会对适用范围隐藏菜单；重新勾选后恢复显示。</span>
        </article>
        <article>
          <strong>可见业务角色</strong>
          <span>留空表示所有业务角色可见；按业务域筛选后，可勾选需要保留菜单的角色。</span>
        </article>
        <article>
          <strong>保存生效</strong>
          <span>保存后刷新页面或重新进入系统，导航会按新配置展示。</span>
        </article>
      </div>
    </section>

    <div v-if="error" class="status error">{{ error }}</div>
    <div v-else-if="statusMessage" class="status ok">{{ statusMessage }}</div>
    <section v-if="auditSummary" class="audit-panel" :class="{ 'audit-panel--warning': auditSummary.notApplicableCount > 0 }">
      <strong>菜单配置生效检查</strong>
      <span>
        配置 {{ auditSummary.configuredCount }} 项，当前用户命中 {{ auditSummary.applicableCount }} 项；
        隐藏 {{ auditSummary.hiddenCount }}，改名 {{ auditSummary.renamedCount }}，移动 {{ auditSummary.movedCount }}，排序 {{ auditSummary.reorderedCount }}。
      </span>
      <span v-if="auditSummary.notApplicableCount">
        {{ auditSummary.notApplicableCount }} 项因业务角色范围未命中当前用户。
      </span>
      <span>运行来源：{{ auditSummary.runtimeSourceLabel }}</span>
    </section>
    <section v-if="versionPanelOpen" class="version-panel">
      <div class="version-panel-header">
        <strong>菜单配置版本</strong>
        <span v-if="versionState?.contract">当前版本 {{ versionState.contract.version_no }}</span>
        <span v-else>保存后生成版本</span>
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
      <div v-else class="version-empty">
        保存菜单配置后会自动生成已发布版本；没有历史版本时，当前菜单配置不能回滚。
      </div>
    </section>
    <section v-if="createPanelOpen" class="create-panel">
      <div class="create-panel-header">
        <strong>新增菜单入口</strong>
        <div class="create-shortcuts">
          <button type="button" class="link-button" :disabled="!selectedMenu" @click="openCreateMenu('sibling')">新增同级</button>
          <button type="button" class="link-button" :disabled="!selectedMenu" @click="openCreateMenu('child')">新增下级</button>
          <button type="button" class="link-button" :disabled="!selectedMenu" @click="openCreateMenu('copy')">复制当前入口</button>
          <button type="button" class="link-button" @click="createPanelOpen = false">关闭</button>
        </div>
      </div>
      <div class="create-form">
        <label>
          <span>菜单名称</span>
          <input v-model="createForm.name" class="cell-input" type="text" placeholder="输入业务菜单名称" />
        </label>
        <label>
          <span>上级菜单</span>
          <select v-model.number="createForm.parent_menu_id" class="cell-input">
            <option v-if="!createParentOptions.length" :value="0" disabled>暂无可选业务父级</option>
            <option v-for="target in createParentOptions" :key="target.id" :value="target.id">
              {{ parentOptionLabel(target) }}
            </option>
          </select>
        </label>
        <label>
          <span>复制已有入口</span>
          <select v-model.number="createForm.source_menu_id" class="cell-input">
            <option :value="0">只创建分组菜单</option>
            <option v-for="source in copySourceOptions" :key="source.id" :value="source.id">
              {{ source.complete_name || source.name }}
            </option>
          </select>
        </label>
        <label>
          <span>排序号</span>
          <input v-model.number="createForm.sequence" class="cell-input" type="number" placeholder="自动" />
        </label>
        <label class="create-check">
          <input v-model="createForm.visible" type="checkbox" />
          <span>创建后显示</span>
        </label>
        <label>
          <span>备注</span>
          <input v-model="createForm.note" class="cell-input" type="text" placeholder="可选" />
        </label>
      </div>
      <div class="create-panel-footer">
        <span>复制入口会沿用已有菜单打开的页面；长期固定入口需沉淀到用户模块。</span>
        <button type="button" class="primary" :disabled="creatingMenu || !createForm.name.trim()" @click="createMenuEntry">
          {{ creatingMenu ? '创建中...' : '创建菜单' }}
        </button>
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

      <main class="menu-config-editor">
        <section v-if="selectedMenu" class="menu-selected-panel menu-primary-panel" aria-label="当前菜单配置">
          <div class="menu-selected-head">
            <div>
              <span class="panel-kicker">当前菜单</span>
              <h2>{{ selectedMenu.name }}</h2>
              <p>{{ selectedMenu.complete_name || selectedMenu.parent_name || '顶层菜单' }}</p>
            </div>
            <span v-if="isDirty(selectedMenu.id)" class="dirty-count">待保存</span>
          </div>
          <div class="menu-detail-section">
            <div class="menu-detail-section-head">
              <strong>基础信息</strong>
            </div>
            <div class="menu-detail-grid menu-detail-grid--basic">
              <label>
                <span>显示名称</span>
                <input
                  class="cell-input"
                  :value="selectedDraft.custom_label"
                  :placeholder="selectedMenu.name"
                  @input="updateDraft(selectedMenu.id, { custom_label: inputValue($event) })"
                />
              </label>
              <label>
                <span>备注</span>
                <input
                  class="cell-input"
                  :value="displayNoteValue(selectedDraft.note)"
                  placeholder="可选"
                  @input="updateDraft(selectedMenu.id, { note: inputValue($event) })"
                />
              </label>
            </div>
          </div>
          <div class="menu-detail-section">
            <div class="menu-detail-section-head">
              <strong>位置与显示</strong>
            </div>
            <div class="menu-detail-grid menu-detail-grid--placement">
              <label>
                <span>移动到上级</span>
                <select
                  class="cell-input"
                  :value="selectedDraft.target_parent_menu_id || 0"
                  @change="updateDraft(selectedMenu.id, { target_parent_menu_id: numericValue($event) })"
                >
                  <option :value="0">不移动</option>
                  <option
                    v-for="target in parentOptions(selectedMenu.id)"
                    :key="target.id"
                    :value="target.id"
                  >
                    {{ target.complete_name || target.name }}
                  </option>
                </select>
              </label>
              <label>
                <span>排序号</span>
                <input
                  class="cell-input"
                  type="number"
                  :value="selectedDraft.sequence_override || ''"
                  :placeholder="String(selectedMenu.sequence || 0)"
                  @input="updateDraft(selectedMenu.id, { sequence_override: numericValue($event) })"
                />
              </label>
              <label class="menu-visible-toggle">
                <input
                  type="checkbox"
                  :checked="selectedDraft.visible"
                  @change="updateDraft(selectedMenu.id, { visible: checkedValue($event) })"
                />
                <span>显示菜单</span>
              </label>
            </div>
          </div>
          <div class="menu-role-panel menu-detail-section">
            <div class="menu-role-head">
              <strong>可见业务角色</strong>
              <span>{{ roleScopeSummary(selectedMenu.id) }}</span>
            </div>
            <div v-if="selectedDraft.role_group_ids.length" class="group-chip-list">
              <span
                v-for="groupId in selectedDraft.role_group_ids"
                :key="`selected-${selectedMenu.id}-${groupId}`"
                class="group-chip"
                :title="roleGroupName(groupId)"
              >
                {{ roleGroupName(groupId) }}
                <button type="button" title="移除业务角色" @click="removeRoleGroup(selectedMenu.id, groupId)">×</button>
              </span>
            </div>
            <select
              class="cell-input group-domain-select"
              :value="roleGroupDomainForMenu(selectedMenu.id)"
              @change="setRoleGroupDomain(selectedMenu.id, inputValue($event))"
            >
              <option v-for="domain in roleGroupDomainOptions" :key="domain" :value="domain">
                {{ domain }}
              </option>
            </select>
            <div class="group-check-list menu-role-check-list">
              <label
                v-for="group in scopedRoleGroupOptions(selectedMenu.id)"
                :key="`selected-${selectedMenu.id}-scope-${group.id}`"
                class="group-check-item"
                :title="group.display_name"
              >
                <input
                  type="checkbox"
                  :checked="isRoleGroupSelected(selectedMenu.id, group.id)"
                  @change="toggleRoleGroup(selectedMenu.id, group.id, checkedValue($event))"
                />
                <span>{{ group.display_name }}</span>
              </label>
            </div>
            <div class="group-scope-actions">
              <span class="group-scope-count">{{ scopedRoleGroupSelectionText(selectedMenu.id) }}</span>
              <button
                type="button"
                class="link-button"
                :disabled="!scopedUnselectedRoleGroupCount(selectedMenu.id)"
                @click="selectScopedRoleGroups(selectedMenu.id)"
              >
                勾选当前分组
              </button>
              <button
                type="button"
                class="link-button"
                :disabled="!scopedSelectedRoleGroupCount(selectedMenu.id)"
                @click="clearScopedRoleGroups(selectedMenu.id)"
              >
                清空当前分组
              </button>
              <button
                v-if="selectedDraft.role_group_ids.length"
                type="button"
                class="link-button"
                @click="clearRoleGroups(selectedMenu.id)"
              >
                恢复所有角色可见
              </button>
            </div>
          </div>
        </section>
        <section v-else class="menu-selected-panel menu-primary-panel menu-selected-panel--empty" aria-label="菜单配置概览">
          <div>
            <span class="panel-kicker">菜单配置</span>
            <h2>全部菜单</h2>
            <p>从左侧选择一个菜单后，在这里调整名称、父级、显示范围和业务角色。</p>
          </div>
        </section>

        <aside class="menu-side-panel" aria-label="菜单配置摘要">
          <div class="menu-side-panel-head">
            <span class="panel-kicker">配置摘要</span>
            <strong>{{ selectedMenu ? selectedMenu.name : '全部菜单' }}</strong>
          </div>
          <div class="menu-side-section menu-side-summary">
            <div class="menu-state-list">
              <span>
                <b>{{ selectedMenu && isDirty(selectedMenu.id) ? '待保存' : '已同步' }}</b>
                当前菜单
              </span>
              <span>
                <b>{{ dirtyCount }}</b>
                未保存菜单
              </span>
              <span>
                <b>{{ selectedMenu ? selectedDraft.role_group_ids.length : 0 }}</b>
                限定角色
              </span>
            </div>
          </div>
          <div v-if="selectedMenu" class="menu-side-section menu-side-action-group">
            <span class="menu-side-section-title">新增入口</span>
            <button type="button" class="ghost" @click="openCreateMenu('sibling')">新增同级</button>
            <button type="button" class="ghost" @click="openCreateMenu('child')">新增下级</button>
            <button type="button" class="ghost" @click="openCreateMenu('copy')">复制当前入口</button>
          </div>
          <div class="menu-side-section menu-side-action-group">
            <span class="menu-side-section-title">批量维护</span>
            <p>用于连续维护多条菜单；日常配置优先使用当前菜单面板。</p>
            <button type="button" class="ghost" @click="bulkPanelOpen = !bulkPanelOpen">
              {{ bulkPanelOpen ? '收起批量调整' : '展开批量调整' }}
            </button>
          </div>
          <div class="menu-side-section menu-side-action-group menu-utility-section">
            <span class="menu-side-section-title">检查发布</span>
            <button type="button" class="ghost" @click="showGuide = !showGuide">
              {{ showGuide ? '收起配置说明' : '查看配置说明' }}
            </button>
            <button type="button" class="ghost" :disabled="loading || auditing || saving" @click="auditMenuConfiguration">
              {{ auditing ? '检查中...' : '生效检查' }}
            </button>
            <button type="button" class="ghost" :disabled="loading || versionLoading || saving" @click="toggleVersionPanel">
              {{ versionPanelOpen ? '收起版本记录' : (versionLoading ? '加载中...' : '版本记录') }}
            </button>
            <button type="button" class="ghost" :disabled="rollbackButtonDisabled" @click="rollbackSelectedMenuConfiguration">
              {{ rollingBack ? '回滚中...' : rollbackButtonText }}
            </button>
          </div>
        </aside>

        <section class="menu-bulk-panel" aria-label="批量菜单配置">
        <div class="table-toolbar">
          <div>
            <strong>{{ filteredRows.length }}</strong>
            <span>条菜单</span>
          </div>
          <div class="table-toolbar-actions">
            <label class="toggle-filter">
              <input v-model="onlyConfigured" type="checkbox" />
              只看已配置
            </label>
            <button type="button" class="ghost" @click="bulkPanelOpen = !bulkPanelOpen">
              {{ bulkPanelOpen ? '收起' : '展开' }}
            </button>
          </div>
        </div>

        <div v-if="loading" class="loading-state">正在加载菜单配置...</div>
        <div v-else-if="!bulkPanelOpen" class="bulk-collapsed-state">
          <span>批量调整已收起</span>
          <button type="button" class="link-button" @click="bulkPanelOpen = true">展开批量编辑表格</button>
        </div>
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
                <th>可见业务角色</th>
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
                        <button type="button" title="移除业务角色" @click="removeRoleGroup(row.menu.id, groupId)">×</button>
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
                    <div class="group-scope-actions">
                      <span class="group-scope-count">{{ scopedRoleGroupSelectionText(row.menu.id) }}</span>
                      <button
                        type="button"
                        class="link-button"
                        :disabled="!scopedUnselectedRoleGroupCount(row.menu.id)"
                        @click="selectScopedRoleGroups(row.menu.id)"
                      >
                        勾选当前分组
                      </button>
                      <button
                        type="button"
                        class="link-button"
                        :disabled="!scopedSelectedRoleGroupCount(row.menu.id)"
                        @click="clearScopedRoleGroups(row.menu.id)"
                      >
                        清空当前分组
                      </button>
                    </div>
                    <button
                      v-if="draftFor(row.menu.id).role_group_ids.length"
                      type="button"
                      class="link-button group-clear"
                      @click="clearRoleGroups(row.menu.id)"
                    >
                      恢复所有角色可见
                    </button>
                    <small>{{ roleScopeSummary(row.menu.id) }}</small>
                  </div>
                </td>
                <td>
                  <input
                    class="cell-input note-input"
                    :value="displayNoteValue(draftFor(row.menu.id).note)"
                    placeholder="可选"
                    @input="updateDraft(row.menu.id, { note: inputValue($event) })"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        </section>
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
  createMenuConfigurationEntry,
  type MenuConfigAuditPayload,
  type MenuConfigGroup,
  type MenuConfigMenu,
  type MenuConfigPolicy,
  type MenuConfigSaveRow,
  type MenuConfigVersionsPayload,
} from '../api/menuConfig';
import { useSessionStore } from '../stores/session';
import { config } from '../config';

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

type DropPosition = 'before' | 'after' | 'inside';

const MENU_CONFIG_SAVE_NOTICE_KEY = 'sc_menu_config_save_notice';

function storedSaveNotice() {
  if (typeof window === 'undefined') return '';
  return String(window.sessionStorage.getItem(MENU_CONFIG_SAVE_NOTICE_KEY) || '').trim();
}

function setSaveNotice(value: string) {
  saveNotice.value = value;
  if (typeof window === 'undefined') return;
  if (value) {
    window.sessionStorage.setItem(MENU_CONFIG_SAVE_NOTICE_KEY, value);
  } else {
    window.sessionStorage.removeItem(MENU_CONFIG_SAVE_NOTICE_KEY);
  }
}

const loading = ref(false);
const saving = ref(false);
const auditing = ref(false);
const rollingBack = ref(false);
const versionLoading = ref(false);
const creatingMenu = ref(false);
const error = ref('');
const message = ref('');
const saveNotice = ref(storedSaveNotice());
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
const createPanelOpen = ref(false);
const bulkPanelOpen = ref(false);
const company = ref<{ id: number; name: string } | null>(null);
const statusMessage = computed(() => message.value || saveNotice.value);
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
const createForm = reactive({
  name: '',
  parent_menu_id: 0,
  source_menu_id: 0,
  sequence: 0,
  visible: true,
  note: '',
});

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
            'drop-inside': node.id === props.dragTargetMenuId && props.dragDropPosition === 'inside',
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

const canRollbackMenuConfiguration = computed(() => {
  const currentVersion = Number(versionState.value?.contract?.version_no || 0);
  return Boolean(
    currentVersion
    && (versionState.value?.versions || []).some((version) => Number(version.version_no || 0) !== currentVersion),
  );
});

const rollbackButtonText = computed(() => {
  if (!versionState.value?.contract) return '先查看版本';
  if (!canRollbackMenuConfiguration.value) return '暂无可回滚版本';
  return selectedVersionNo.value ? `回滚到版本 ${selectedVersionNo.value}` : '回滚上一版';
});

const rollbackButtonDisabled = computed(() => (
  loading.value
  || saving.value
  || rollingBack.value
  || versionLoading.value
  || Boolean(versionState.value?.contract && !canRollbackMenuConfiguration.value)
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
const selectedMenu = computed(() => menus.value.find((menu) => Number(menu.id) === Number(selectedMenuId.value)) || null);
const selectedDraft = computed(() => (
  selectedMenu.value ? draftFor(selectedMenu.value.id) || defaultDraftForEmpty() : defaultDraftForEmpty()
));
const rootMenuXmlid = computed(() => String(route.query.root_menu_xmlid || config.startupRootXmlid || '').trim());
const rootMenu = computed(() => (
  rootMenuXmlid.value
    ? menus.value.find((menu) => menu.xmlid === rootMenuXmlid.value) || null
    : null
));
const navigationMenus = computed(() => flattenMenuTree(tree.value));
const navigationParentMenus = computed(() => navigationMenus.value.filter((menu) => (
  Boolean(menu.children?.length) || !String(menu.action || '').trim()
)));
const createParentOptions = computed(() => {
  const byId = new Map<number, MenuConfigMenu>();
  if (rootMenu.value) byId.set(Number(rootMenu.value.id), rootMenu.value);
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

function defaultDraftForEmpty(): DraftPolicy {
  return {
    policy_id: 0,
    menu_id: 0,
    target_parent_menu_id: 0,
    custom_label: '',
    sequence_override: 0,
    visible: true,
    role_group_ids: [],
    note: '',
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
  return count ? `限 ${count} 个业务角色可见` : '所有业务角色可见';
}

function displayNoteValue(value: string) {
  const note = String(value || '').trim();
  if (/^(user_confirmed_|system_|technical_)/i.test(note)) return '';
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
  createForm.parent_menu_id = selectedMenu.value?.id || defaultCreateParentId.value;
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
    message.value = `已创建菜单“${createdName}”，可继续新增下级菜单；刷新页面后导航按配置生效`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '菜单创建失败';
  } finally {
    creatingMenu.value = false;
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
      out.push(item);
      if (item.children?.length) walk(item.children);
    });
  };
  walk(items);
  return out;
}

function parentOptionSortKey(menu: MenuConfigMenu) {
  const isRoot = rootMenu.value && Number(menu.id) === Number(rootMenu.value.id);
  return `${isRoot ? '0' : '1'}:${menu.complete_name || menu.name}`;
}

function parentOptionLabel(menu: MenuConfigMenu) {
  const label = menu.complete_name || menu.name;
  if (rootMenu.value && Number(menu.id) === Number(rootMenu.value.id)) {
    return `业务根菜单：${menu.name || label}（新增一级分组）`;
  }
  return label;
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
    const allowedParentIds = parentOptionIds(dragSourceMenuId.value);
    const targetMenu = menuById(payload.menuId);
    if (allowedParentIds.has(Number(payload.menuId))) {
      dragTargetMenuId.value = payload.menuId;
      dragDropPosition.value = 'inside';
      return;
    }
    if (!targetMenu || !allowedParentIds.has(Number(targetMenu.parent_id || 0))) {
      dragTargetMenuId.value = 0;
      return;
    }
    dragTargetMenuId.value = payload.menuId;
    dragDropPosition.value = payload.position;
    return;
  }
  dragTargetMenuId.value = payload.menuId;
  dragDropPosition.value = payload.position;
}

function resequenceBranch(items: MenuConfigMenu[]) {
  return items.map((item, index) => {
    const draft = draftFor(item.id);
    if (draft) {
      draft.sequence_override = (index + 1) * 10;
    }
    return item;
  });
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
    return resequenceBranch(next);
  }

  return items.map((item) => {
    if (!item.children?.length) return item;
    return { ...item, children: reorderSiblingBranch(item.children, sourceId, targetId, position) };
  });
}

function removeTreeNode(items: MenuConfigMenu[], sourceId: number): { rows: MenuConfigMenu[]; removed: MenuConfigMenu | null } {
  let removed: MenuConfigMenu | null = null;
  const rows = items.flatMap((item) => {
    if (Number(item.id) === Number(sourceId)) {
      removed = item;
      return [];
    }
    if (!item.children?.length) return [item];
    const result = removeTreeNode(item.children, sourceId);
    if (result.removed) {
      removed = result.removed;
      return [{ ...item, children: resequenceBranch(result.rows) }];
    }
    return [item];
  });
  return { rows, removed };
}

function insertTreeNodeInside(items: MenuConfigMenu[], parentId: number, source: MenuConfigMenu): { rows: MenuConfigMenu[]; inserted: boolean } {
  let inserted = false;
  const rows = items.map((item) => {
    if (Number(item.id) === Number(parentId)) {
      inserted = true;
      const nextChild = { ...source, parent_id: parentId, parent_name: item.complete_name || item.name };
      const children = resequenceBranch([...(item.children || []), nextChild]);
      return { ...item, children };
    }
    if (!item.children?.length) return item;
    const result = insertTreeNodeInside(item.children, parentId, source);
    inserted = inserted || result.inserted;
    return result.inserted ? { ...item, children: result.rows } : item;
  });
  return { rows, inserted };
}

function moveTreeNodeToParent(sourceId: number, parentId: number): boolean {
  if (!sourceId || !parentId || sourceId === parentId || !parentOptionIds(sourceId).has(parentId)) return false;
  const result = removeTreeNode(tree.value, sourceId);
  if (!result.removed) return false;
  const inserted = insertTreeNodeInside(result.rows, parentId, result.removed);
  if (!inserted.inserted) return false;
  const draft = draftFor(sourceId);
  if (draft) {
    draft.target_parent_menu_id = parentId;
  }
  tree.value = inserted.rows;
  setSaveNotice('');
  return true;
}

function insertTreeNodeRelative(
  items: MenuConfigMenu[],
  source: MenuConfigMenu,
  targetId: number,
  parentId: number,
  position: Exclude<DropPosition, 'inside'>,
): { rows: MenuConfigMenu[]; inserted: boolean } {
  const ids = items.map((item) => Number(item.id));
  if (ids.includes(Number(targetId))) {
    const target = items.find((item) => Number(item.id) === Number(targetId));
    const nextSource = { ...source, parent_id: parentId, parent_name: target?.parent_name || source.parent_name };
    const withoutSource = items.filter((item) => Number(item.id) !== Number(source.id));
    const targetIndex = withoutSource.findIndex((item) => Number(item.id) === Number(targetId));
    if (targetIndex < 0) return { rows: items, inserted: false };
    withoutSource.splice(position === 'before' ? targetIndex : targetIndex + 1, 0, nextSource);
    return { rows: resequenceBranch(withoutSource), inserted: true };
  }
  let inserted = false;
  const rows = items.map((item) => {
    if (!item.children?.length) return item;
    const result = insertTreeNodeRelative(item.children, source, targetId, parentId, position);
    inserted = inserted || result.inserted;
    return result.inserted ? { ...item, children: result.rows } : item;
  });
  return { rows, inserted };
}

function moveTreeNodeRelative(sourceId: number, targetId: number, position: Exclude<DropPosition, 'inside'>): boolean {
  if (!sourceId || !targetId || sourceId === targetId) return false;
  const target = menuById(targetId);
  const parentId = Number(target?.parent_id || 0);
  if (!target || !parentId || !parentOptionIds(sourceId).has(parentId)) return false;
  const result = removeTreeNode(tree.value, sourceId);
  if (!result.removed) return false;
  const inserted = insertTreeNodeRelative(result.rows, result.removed, targetId, parentId, position);
  if (!inserted.inserted) return false;
  const draft = draftFor(sourceId);
  if (draft) {
    draft.target_parent_menu_id = parentId;
  }
  tree.value = inserted.rows;
  setSaveNotice('');
  return true;
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
  setSaveNotice('');
}

function applyTreeReorder(payload: { sourceId: number; targetId: number; position: DropPosition }) {
  if (!payload.sourceId || !payload.targetId || payload.sourceId === payload.targetId) {
    clearTreeDrag();
    return;
  }
  if (!areVisualSiblings(tree.value, payload.sourceId, payload.targetId)) {
    const moved = payload.position === 'inside'
      ? moveTreeNodeToParent(payload.sourceId, payload.targetId)
      : moveTreeNodeRelative(payload.sourceId, payload.targetId, payload.position);
    if (moved) {
      message.value = '';
      setSaveNotice('');
    }
    clearTreeDrag();
    return;
  }
  tree.value = reorderSiblingBranch(tree.value, payload.sourceId, payload.targetId, payload.position);
  message.value = '';
  setSaveNotice('');
  clearTreeDrag();
}

function applyTreeDrop(targetId: number) {
  const sourceId = dragSourceMenuId.value;
  if (!sourceId || !targetId || sourceId === targetId || !dragTargetMenuId.value) {
    clearTreeDrag();
    return;
  }
  let moved = false;
  if (dragDropPosition.value === 'inside') {
    moved = moveTreeNodeToParent(sourceId, targetId);
  } else if (areVisualSiblings(tree.value, sourceId, targetId)) {
    tree.value = reorderSiblingBranch(tree.value, sourceId, targetId, dragDropPosition.value);
    moved = true;
  } else {
    moved = moveTreeNodeRelative(sourceId, targetId, dragDropPosition.value);
  }
  if (moved) {
    message.value = '';
    setSaveNotice('');
  }
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

function attachMissingConfiguredMenus(
  baseTree: MenuConfigMenu[],
  allMenus: MenuConfigMenu[],
  usedMenuIds: Set<number>,
  rootMenuId = 0,
): MenuConfigMenu[] {
  const rootIds = new Set(baseTree.map((item) => Number(item.id)));
  const byParent = new Map<number, MenuConfigMenu[]>();
  allMenus.forEach((menu) => {
    if (usedMenuIds.has(Number(menu.id))) return;
    const parentId = Number(menu.parent_id || 0);
    if (!parentId && !rootIds.size) return;
    const list = byParent.get(parentId) || [];
    list.push({ ...menu, children: [] });
    byParent.set(parentId, list);
  });

  const sortBranch = (items: MenuConfigMenu[]) => [...items].sort((a, b) => (
    Number(a.sequence || 0) - Number(b.sequence || 0)
    || Number(a.id || 0) - Number(b.id || 0)
  ));

  const buildMissingBranch = (parentId: number): MenuConfigMenu[] => sortBranch(byParent.get(parentId) || []).map((menu) => ({
    ...menu,
    children: buildMissingBranch(Number(menu.id)),
  }));

  const attach = (items: MenuConfigMenu[]): MenuConfigMenu[] => sortBranch(items.map((item) => ({
    ...item,
    children: sortBranch([
      ...(item.children?.length ? attach(item.children) : []),
      ...buildMissingBranch(Number(item.id)),
    ]),
  })));

  const attached = attach(baseTree);
  const rootMissing = rootMenuId
    ? buildMissingBranch(rootMenuId).filter((menu) => !rootIds.has(Number(menu.id)))
    : [];
  if (attached.length) return sortBranch([...attached, ...rootMissing]);
  return buildMissingBranch(0);
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

function returnToBusinessConfig() {
  router.push({
    path: '/admin/business-config',
    query: {
      root_menu_xmlid: route.query.root_menu_xmlid || undefined,
      model: route.query.model || undefined,
      action_id: route.query.action_id || undefined,
      menu_id: route.query.menu_id || undefined,
      page_label: route.query.page_label || undefined,
      view_id: route.query.view_id || undefined,
      role_key: route.query.role_key || undefined,
      open_pages: route.query.open_pages || '1',
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
    const payload = await loadMenuConfigurationPanel({
      menu_ids: collectNavigationMenuIds(),
      root_menu_xmlid: rootMenuXmlid.value || undefined,
    });
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
    const usedMenuIds = new Set<number>();
    const navOrderedTree = buildTreeFromNavigation(session.menuTree as NavNode[], menuById, menuByLabel, usedMenuIds);
    const completeTree = attachMissingConfiguredMenus(
      navOrderedTree,
      payload.menus || [],
      usedMenuIds,
      rootMenu.value?.id || 0,
    );
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
    auditResult.value = await loadMenuConfigurationAudit({ company_id: company.value?.id || undefined });
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
    await saveMenuConfigurationPanel({ rows });
    auditResult.value = null;
    setSaveNotice(`已保存 ${rows.length} 项菜单配置，正在刷新导航`);
    saving.value = false;
    try {
      await session.loadAppInit({ force: true });
      await loadPanel({ preserveStatus: true });
      if (versionPanelOpen.value) {
        await loadVersions();
      }
      setSaveNotice(`已保存 ${rows.length} 项菜单配置，导航已刷新`);
    } catch (refreshErr) {
      error.value = refreshErr instanceof Error
        ? `菜单配置已保存，刷新导航失败：${refreshErr.message}`
        : '菜单配置已保存，刷新导航失败';
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '菜单配置保存失败';
  } finally {
    saving.value = false;
  }
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

.version-empty {
  padding: 8px;
  border: 1px dashed var(--sc-app-border);
  border-radius: 6px;
  color: var(--sc-app-text-secondary);
  background: var(--sc-app-muted-bg);
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

.create-panel {
  margin: 0 18px;
  display: grid;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-panel);
  font-size: 13px;
}

.create-panel-header,
.create-panel-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.create-shortcuts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.create-form {
  display: grid;
  grid-template-columns: repeat(3, minmax(180px, 1fr));
  gap: 10px;
}

.create-form label {
  display: grid;
  gap: 6px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.create-check {
  grid-template-columns: auto 1fr;
  align-items: end;
  align-content: end;
  min-height: 58px;
}

.create-panel-footer {
  color: var(--sc-app-text-secondary);
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

:deep(.tree-node.drop-inside) {
  background: var(--sc-app-info-bg);
  box-shadow: inset 0 0 0 1px var(--sc-semantic-surface-interactive);
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

.menu-config-editor {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  align-content: start;
  align-items: start;
  gap: 12px;
  border: 1px solid var(--sc-app-border);
  padding: 12px;
  background: var(--sc-app-panel);
}

.menu-selected-panel,
.menu-bulk-panel {
  min-width: 0;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-surface);
}

.menu-selected-panel {
  display: grid;
  gap: 12px;
  padding: 14px;
}

.menu-primary-panel {
  min-height: 360px;
}

.menu-selected-panel--empty {
  color: var(--sc-app-text-secondary);
}

.menu-selected-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--sc-app-border);
}

.panel-kicker {
  display: inline-block;
  margin-bottom: 4px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.menu-selected-head h2,
.menu-selected-panel--empty h2 {
  margin: 0;
  font-size: 16px;
}

.menu-selected-head p,
.menu-selected-panel--empty p {
  margin: 4px 0 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.menu-detail-section {
  display: grid;
  gap: 10px;
  min-width: 0;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  padding: 12px;
  background: var(--sc-app-bg);
}

.menu-detail-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: var(--sc-app-text-primary);
  font-size: 13px;
}

.menu-detail-grid {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.menu-detail-grid--basic {
  grid-template-columns: minmax(180px, 0.8fr) minmax(0, 1.2fr);
}

.menu-detail-grid--placement {
  grid-template-columns: minmax(220px, 1fr) minmax(96px, 0.4fr) minmax(150px, 0.5fr);
}

.menu-detail-grid label {
  display: grid;
  gap: 6px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.menu-visible-toggle {
  grid-template-columns: auto 1fr;
  align-content: end;
  align-items: center;
  min-height: 58px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 10px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-primary);
}

.menu-role-panel {
  gap: 8px;
}

.menu-role-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 13px;
}

.menu-role-head span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.menu-role-check-list {
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  max-height: 132px;
}

.menu-side-panel {
  position: sticky;
  top: 12px;
  display: grid;
  gap: 0;
  min-width: 0;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  padding: 12px;
  background: var(--sc-app-surface);
}

.menu-side-panel-head {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding-bottom: 10px;
}

.menu-side-panel-head strong {
  min-width: 0;
  overflow: hidden;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-side-section {
  display: grid;
  gap: 8px;
  min-width: 0;
  padding: 12px 0;
  border-top: 1px solid var(--sc-app-border);
}

.menu-side-section-title {
  color: var(--sc-app-text-primary);
  font-size: 13px;
  font-weight: 600;
}

.menu-side-section p {
  margin: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  line-height: 1.45;
}

.menu-side-action-group .ghost {
  width: 100%;
  justify-content: center;
}

.menu-utility-section {
  gap: 8px;
}

.menu-state-list {
  display: grid;
  gap: 6px;
}

.menu-state-list span {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.menu-state-list b {
  color: var(--sc-app-text-primary);
  font-size: 13px;
}

.menu-bulk-panel {
  grid-column: 1 / -1;
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

.table-toolbar-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
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

.bulk-collapsed-state {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 12px;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
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

.group-scope-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.group-scope-count {
  color: var(--sc-app-text-secondary);
  font-size: 11px;
  line-height: 1.2;
}

.group-scope-actions .link-button {
  padding: 0;
  font-size: 11px;
  line-height: 1.2;
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

  .menu-config-editor {
    grid-template-columns: 1fr;
  }

  .menu-side-panel,
  .menu-bulk-panel {
    grid-column: auto;
  }

  .menu-side-panel {
    position: static;
  }

  .menu-config-tree {
    border-right: 1px solid var(--sc-app-border);
  }

  .menu-detail-grid--basic,
  .menu-detail-grid--placement,
  .menu-role-check-list {
    grid-template-columns: 1fr;
  }

  .menu-selected-head,
  .menu-role-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .tree-scroll,
  .table-wrap {
    max-height: none;
  }
}
</style>
