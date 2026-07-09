<template>
  <section v-if="pageSectionsReady" class="menu-config-page" :style="pageSectionStyle('root')" :data-contract-sections="pageSectionsFingerprint">
    <header class="menu-config-header">
      <div>
        <p class="eyebrow">{{ companyLabel }}</p>
        <h1>菜单配置</h1>
      </div>
      <div class="header-actions">
        <span v-if="dirtyCount" class="dirty-count">{{ dirtyCount }} 项未保存</span>
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
        <button v-if="canReturnToBusinessConfig" type="button" class="ghost" @click="returnToBusinessConfig">
          返回配置工作台
        </button>
        <button type="button" class="ghost" :disabled="loading || saving" @click="loadPanel()">刷新菜单配置</button>
        <button type="button" class="ghost" :disabled="loading || saving || creatingMenu || deletingMenu" @click="openCreateMenu('custom')">
          新增一级菜单
        </button>
        <button type="button" class="primary" :disabled="!dirtyCount || saving" @click="saveChanges">
          {{ saving ? '保存中...' : '保存菜单配置' }}
        </button>
      </div>
    </header>

    <section v-if="showGuide" class="guide-panel">
      <div>
        <h2>配置口径</h2>
        <p>这里只配置当前业务办理范围内的菜单；已隐藏但可重新开放的系统菜单也会进入配置范围。</p>
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
        配置隐藏 {{ auditSummary.hiddenCount }}，当前显示 {{ auditSummary.runtimeVisibleCount }}，承载显示 {{ auditSummary.runtimeCarrierCount }}；
        改名 {{ auditSummary.renamedCount }}，移动 {{ auditSummary.movedCount }}，排序 {{ auditSummary.reorderedCount }}。
      </span>
      <span v-if="auditSummary.notApplicableCount">
        {{ auditSummary.notApplicableCount }} 项因业务角色范围未命中当前用户。
      </span>
      <span>运行来源：{{ auditSummary.runtimeSourceLabel }}</span>
    </section>
    <section v-if="versionPanelOpen" class="version-panel">
      <div class="version-panel-header">
        <div>
          <strong>版本与回滚</strong>
          <span>每次保存菜单配置都会生成一个已发布版本；回滚会把菜单配置恢复到选中的历史版本。</span>
        </div>
        <span v-if="versionState?.contract">当前发布版本 {{ versionState.contract.version_no }}</span>
        <span v-else>保存后生成版本</span>
      </div>
      <div v-if="versionState?.contract" class="version-current-card">
        <span class="panel-kicker">当前生效</span>
        <strong>版本 {{ versionState.contract.version_no }}</strong>
        <span>
          当前配置 {{ versionState.contract.summary.policy_count }} 项，
          隐藏 {{ versionState.contract.summary.hidden_count }}，改名 {{ versionState.contract.summary.renamed_count }}，
          移动 {{ versionState.contract.summary.moved_count }}，排序 {{ versionState.contract.summary.reordered_count }}。
        </span>
      </div>
      <div v-if="versionState?.versions.length" class="version-list">
        <label
          v-for="version in versionState.versions"
          :key="version.id"
          class="version-item"
          :class="{ selected: selectedVersionNo === version.version_no, current: version.version_no === versionState?.contract?.version_no }"
        >
          <input v-model.number="selectedVersionNo" type="radio" :value="version.version_no" />
          <span class="version-title">
            版本 {{ version.version_no }}
            <b v-if="version.version_no === versionState?.contract?.version_no">当前</b>
          </span>
          <span class="version-meta">配置 {{ version.summary.policy_count }} 项</span>
          <span class="version-meta">隐藏 {{ version.summary.hidden_count }}，改名 {{ version.summary.renamed_count }}</span>
          <span class="version-meta">移动 {{ version.summary.moved_count }}，排序 {{ version.summary.reordered_count }}</span>
        </label>
      </div>
      <div v-if="selectedRollbackVersion" class="version-preview">
        <span class="panel-kicker">准备回滚</span>
        <strong>将恢复到版本 {{ selectedRollbackVersion.version_no }}</strong>
        <span>
          回滚后会恢复该版本的显示、隐藏、名称、位置、排序和角色范围；当前未保存修改不会包含在回滚版本中。
        </span>
        <span>
          目标版本包含 {{ selectedRollbackVersion.summary.policy_count }} 项配置，
          隐藏 {{ selectedRollbackVersion.summary.hidden_count }}，移动 {{ selectedRollbackVersion.summary.moved_count }}。
        </span>
        <button type="button" class="danger" :disabled="rollbackButtonDisabled" @click="rollbackSelectedMenuConfiguration">
          {{ rollingBack ? '回滚中...' : rollbackButtonText }}
        </button>
      </div>
      <div v-else class="version-empty">
        保存菜单配置后会自动生成已发布版本；没有历史版本时，当前菜单配置不能回滚。
      </div>
    </section>
    <section v-if="createPanelOpen" class="create-panel">
      <div class="create-panel-header">
        <strong>新增菜单入口</strong>
        <div class="create-shortcuts">
          <button type="button" class="link-button" :disabled="!selectedMenu" @click="openCreateMenu('sibling')">新增同级菜单</button>
          <button type="button" class="link-button" :disabled="!selectedMenu" @click="openCreateMenu('child')">新增下级菜单</button>
          <button type="button" class="link-button" :disabled="!selectedMenu" @click="openCreateMenu('copy')">复制当前菜单入口</button>
          <button type="button" class="link-button" @click="createPanelOpen = false">收起新增入口</button>
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
              {{ menuPathLabel(source) }}
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

    <div class="menu-config-workspace sc-product-workspace sc-lowcode-workspace">
      <aside class="menu-config-tree">
        <div class="tree-panel-head">
          <div>
            <span class="panel-kicker">菜单目录</span>
            <strong>{{ treeCountLabel }}</strong>
          </div>
          <span class="tree-panel-hint">
            {{ treeDragEnabled ? '直接拖拽排序' : '搜索时暂停拖拽' }}
            <b v-if="deletableMenuCount">可删除 {{ deletableMenuCount }}</b>
          </span>
        </div>
        <div class="tree-search">
          <input v-model="searchText" type="search" placeholder="搜索菜单名称或路径" />
          <div class="tree-search-summary">
            <span>{{ treeSearchSummary }}</span>
            <button
              type="button"
              class="link-button tree-clear-filter"
              :disabled="!treeViewFiltered"
              @click="clearTreeFilter"
            >
              清空筛选
            </button>
          </div>
        </div>
        <div class="tree-state-tabs" aria-label="菜单状态筛选">
          <button
            v-for="option in menuStateFilterOptions"
            :key="option.value"
            type="button"
            :class="{ active: menuStateFilter === option.value }"
            @click="menuStateFilter = option.value"
          >
            <span>{{ option.label }}</span>
            <b>{{ option.count }}</b>
          </button>
        </div>
        <div class="tree-shortcuts">
          <button
            type="button"
            class="tree-node all"
            :class="{ active: selectedMenuId === 0 }"
            @click="selectMenu(0)"
          >
            全部菜单
          </button>
        </div>
        <div class="tree-scroll">
          <MenuConfigTree
            :nodes="visibleTree"
            :selected-menu-id="selectedMenuId"
            :drag-source-menu-id="dragSourceMenuId"
            :drag-target-menu-id="dragTargetMenuId"
            :drag-drop-position="dragDropPosition"
            :drag-enabled="treeDragEnabled"
            :search-active="treeViewFiltered"
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
              <h2>{{ menuDisplayLabel(selectedMenu) }}</h2>
              <p>{{ menuPathLabel(selectedMenu) }}</p>
            </div>
            <div class="menu-selected-badges">
              <span
                class="menu-origin-badge"
                :class="menuHandlingStateClass(selectedMenu)"
              >
                {{ menuHandlingStateLabel(selectedMenu) }}
              </span>
              <span v-if="isUserCreatedMenu(selectedMenu)" class="menu-origin-badge deletable">用户新增，可删除</span>
              <span v-else class="menu-origin-badge locked">系统菜单，可隐藏</span>
              <span v-if="isDirty(selectedMenu.id)" class="dirty-count">待保存</span>
            </div>
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
                    {{ parentOptionLabel(target) }}
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
            <strong>{{ selectedMenu ? menuDisplayLabel(selectedMenu) : '全部菜单' }}</strong>
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
          <div class="menu-side-section menu-side-action-group">
            <span class="menu-side-section-title">新增入口</span>
            <button type="button" class="ghost" :disabled="!selectedMenu || loading || saving || creatingMenu || deletingMenu" @click="openCreateMenu('sibling')">新增同级菜单</button>
            <button type="button" class="ghost" :disabled="!selectedMenu || loading || saving || creatingMenu || deletingMenu" @click="openCreateMenu('child')">新增下级菜单</button>
            <button type="button" class="ghost" :disabled="!selectedMenu || loading || saving || creatingMenu || deletingMenu" @click="openCreateMenu('copy')">复制当前菜单入口</button>
            <button
              type="button"
              class="ghost danger-ghost"
              :disabled="!canDeleteSelectedMenu || loading || saving || creatingMenu || deletingMenu"
              :title="selectedMenuDeleteHint"
              @click="deleteSelectedMenu"
            >
              {{ deletingMenu ? '删除中...' : '删除新增菜单' }}
            </button>
            <p class="action-hint">{{ selectedMenuDeleteHint }}</p>
          </div>
          <div class="menu-side-section menu-side-action-group">
            <span class="menu-side-section-title">批量维护</span>
            <p>用于连续维护多条菜单；日常配置优先使用当前菜单面板。</p>
            <button type="button" class="ghost" @click="bulkPanelOpen = !bulkPanelOpen">
              {{ bulkPanelOpen ? '收起批量维护表格' : '展开批量维护表格' }}
            </button>
          </div>
          <div class="menu-side-section menu-side-action-group menu-utility-section">
            <span class="menu-side-section-title">检查发布</span>
            <button type="button" class="ghost" @click="showGuide = !showGuide">
              {{ showGuide ? '收起菜单配置说明' : '查看菜单配置说明' }}
            </button>
            <button type="button" class="ghost" :disabled="loading || auditing || saving" @click="auditMenuConfiguration">
              {{ auditing ? '检查中...' : '检查菜单生效' }}
            </button>
            <button type="button" class="ghost" :disabled="loading || versionLoading || saving" @click="toggleVersionPanel">
              {{ versionPanelOpen ? '收起菜单版本与回滚' : (versionLoading ? '加载中...' : '查看菜单版本与回滚') }}
            </button>
          </div>
        </aside>

        <section class="menu-bulk-panel" aria-label="批量菜单配置">
          <div class="table-toolbar">
            <div class="bulk-toolbar-title">
              <span class="panel-kicker">批量维护</span>
              <strong>{{ filteredRows.length }} 条菜单</strong>
              <span>用于连续校对名称、显示范围和可见角色</span>
            </div>
            <div class="table-toolbar-actions">
              <span class="bulk-stat">未保存 {{ dirtyCount }}</span>
              <label class="toggle-filter">
                <input v-model="onlyConfigured" type="checkbox" />
                只看已配置
              </label>
              <button type="button" class="ghost" @click="bulkPanelOpen = !bulkPanelOpen">
                {{ bulkPanelOpen ? '收起批量维护表格' : '展开批量维护表格' }}
              </button>
            </div>
          </div>

          <div v-if="loading" class="loading-state">正在加载菜单配置...</div>
          <div v-else-if="!bulkPanelOpen" class="bulk-collapsed-state">
            <span>批量维护已收起，日常调整建议使用当前菜单主编辑区。</span>
            <button type="button" class="link-button" @click="bulkPanelOpen = true">展开批量维护表格</button>
          </div>
          <div v-else class="table-wrap">
            <table>
            <colgroup>
              <col class="index-col" />
              <col class="name-col" />
              <col class="default-col" />
              <col class="status-col" />
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
                <th>来源</th>
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
                    :placeholder="menuDisplayLabel(row.menu)"
                    @input="updateDraft(row.menu.id, { custom_label: inputValue($event) })"
                  />
                </td>
                <td><span class="muted">{{ menuDisplayLabel(row.menu) }}</span></td>
                <td class="status-col">
                  <span
                    class="menu-origin-badge"
                    :class="isUserCreatedMenu(row.menu) ? 'deletable' : 'locked'"
                  >
                    {{ isUserCreatedMenu(row.menu) ? '可删除' : '系统' }}
                  </span>
                </td>
                <td><span class="muted">{{ menuParentLabel(row.menu) }}</span></td>
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
                      {{ parentOptionLabel(target) }}
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
  deleteMenuConfigurationEntry,
  type MenuConfigAuditPayload,
  type MenuConfigGroup,
  type MenuConfigMenu,
  type MenuConfigPayload,
  type MenuConfigPolicy,
  type MenuConfigRuntimePayload,
  type MenuConfigRuntimeState,
  type MenuConfigSaveRow,
  type MenuConfigVersionsPayload,
} from '../api/menuConfig';
import { useSessionStore } from '../stores/session';
import { config } from '../config';
import { BUSINESS_CONFIG_ROUTE_FLAGS, MENU_CONFIG_RUNTIME_SOURCES } from '../app/businessConfigBoundaries';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';

type MenuConfigNavNode = NavNode & {
  action_id?: number | string;
  model?: string;
  config_menu_id?: number | string;
  configurable?: boolean;
  config_ref?: { model?: string; id?: number | string };
  meta?: NavNode['meta'] & {
    config_menu_id?: number | string;
    configurable?: boolean;
    config_ref?: { model?: string; id?: number | string };
  };
};

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
type RuntimeMenuConfigGroup = MenuConfigMenu & { runtime_group?: boolean };
type MenuConfigTreeNode = MenuConfigMenu & { menu_config_missing?: boolean };

const MENU_CONFIG_SAVE_NOTICE_KEY = 'sc_menu_config_save_notice';
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
const deletingMenu = ref(false);
const error = ref('');
const message = ref('');
const saveNotice = ref(storedSaveNotice());
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
const canReturnToBusinessConfig = computed(() => String(route.query[BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig] || '').trim() === '1');
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
        h('span', { title: menuPathLabel(node) }, menuDisplayLabel(node)),
        h('span', {
          class: [
            'menu-origin-badge',
            menuHandlingStateClass(node),
            'tree-origin-badge',
          ],
        }, menuTreeStateLabel(node)),
        isUserCreatedMenu(node)
          ? h('span', { class: ['menu-origin-badge', 'deletable', 'tree-origin-badge'] }, '可删除')
          : null,
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
    runtimeVisibleCount: Number(summary.runtime_visible_count || auditResult.value?.runtime?.summary?.runtime_visible_count || 0),
    runtimeHiddenCount: Number(summary.runtime_hidden_count || 0),
    runtimeCarrierCount: Number(summary.runtime_carrier_count || auditResult.value?.runtime?.summary?.runtime_carrier_count || 0),
    renamedCount: Number(summary.renamed_count || 0),
    reorderedCount: Number(summary.reordered_count || 0),
    movedCount: Number(summary.moved_count || 0),
    notApplicableCount: Array.isArray(summary.not_applicable_policy_ids) ? summary.not_applicable_policy_ids.length : 0,
    runtimeSourceLabel: summary.runtime_source === MENU_CONFIG_RUNTIME_SOURCES.contract ? '已发布配置' : '兼容配置',
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
  const confirmed = window.confirm(`确认删除新增菜单“${menuName}”？删除后会同步刷新导航配置。`);
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
  const menu = treeMenuById(menuId);
  if (isRuntimeMenuGroup(menu)) return;
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

function navConfigMenuId(node: MenuConfigNavNode) {
  const meta = node.meta || {};
  const configRef = node.config_ref || meta.config_ref || {};
  const configRefModel = String(configRef.model || 'ir.ui.menu').trim();
  const candidates = [
    node.config_menu_id,
    meta.config_menu_id,
    configRefModel === 'ir.ui.menu' ? configRef.id : 0,
    node.configurable === false || meta.configurable === false ? 0 : navMenuId(node),
  ];
  for (const candidate of candidates) {
    const menuId = Number(candidate || 0);
    if (Number.isFinite(menuId) && menuId > 0) return menuId;
  }
  return 0;
}

function navMenuLabel(node: NavNode) {
  return String(node.title || node.name || node.label || '').trim();
}

function buildTreeFromNavigation(
  navNodes: NavNode[],
  menuById: Map<number, MenuConfigMenu>,
  usedMenuIds = new Set<number>(),
): MenuConfigMenu[] {
  return navNodes.flatMap((node) => {
    const configMenuId = navConfigMenuId(node as MenuConfigNavNode);
    const runtimeNodeId = navMenuId(node);
    const label = navMenuLabel(node);
    let menu = menuById.get(configMenuId);
    if (menu && usedMenuIds.has(menu.id)) {
      menu = undefined;
    }
    if (!menu) {
      const children = Array.isArray(node.children)
        ? buildTreeFromNavigation(node.children as NavNode[], menuById, usedMenuIds)
        : [];
      if (!children.length || !label || !runtimeNodeId) return children;
      return [{
        id: runtimeNodeId,
        menu_id: runtimeNodeId,
        name: label,
        display_name: label,
        complete_name: label,
        parent_id: 0,
        parent_name: '',
        sequence: Number(node.sequence ?? node.meta?.sequence ?? 0),
        action: '',
        web_icon: '',
        xmlid: '__runtime_group__',
        group_ids: [],
        group_names: [],
        runtime_group: true,
        children,
      } as RuntimeMenuConfigGroup];
    }
    usedMenuIds.add(menu.id);
    return [{
      ...menu,
      name: label || menu.name,
      display_name: label || menu.display_name,
      sequence: Number(node.sequence ?? node.meta?.sequence ?? menu.sequence ?? 0),
      children: Array.isArray(node.children)
        ? buildTreeFromNavigation(node.children as NavNode[], menuById, usedMenuIds)
        : [],
    }];
  });
}

function markHandlingMembership(items: MenuConfigMenu[], usedMenuIds: Set<number>): MenuConfigMenu[] {
  return items.map((item) => {
    const menuId = Number(item.id || 0);
    const children = item.children?.length ? markHandlingMembership(item.children, usedMenuIds) : [];
    if (!menuId || usedMenuIds.has(menuId)) {
      return { ...item, children };
    }
    return { ...item, children, menu_config_missing: true } as MenuConfigTreeNode;
  });
}

function filterMenuConfigSurfaceTree(items: MenuConfigMenu[]): MenuConfigMenu[] {
  return items.flatMap((item) => {
    const children = item.children?.length ? filterMenuConfigSurfaceTree(item.children) : [];
    if (isMenuConfigSurfaceMenu(item) || children.length) {
      return [{ ...item, children }];
    }
    return [];
  });
}

function mergeNavigationAndConfigTrees(navigationTree: MenuConfigMenu[], configTree: MenuConfigMenu[], usedMenuIds: Set<number>) {
  if (!navigationTree.length) {
    return filterMenuConfigSurfaceTree(markHandlingMembership(configTree, usedMenuIds));
  }
  return navigationTree;
}

function runtimeNavigationTreeFromPayload(payload: MenuConfigPayload) {
  return Array.isArray(payload.runtime?.tree) ? (payload.runtime.tree as NavNode[]) : [];
}

function collectNavigationMenuIds() {
  const ids: number[] = [];
  const seen = new Set<number>();
  const walk = (items: Array<{ menu_id?: number; id?: number; children?: unknown[] }>) => {
    items.forEach((item) => {
      const menuId = navConfigMenuId(item as MenuConfigNavNode);
      if (Number.isFinite(menuId) && menuId > 0 && !seen.has(menuId)) {
        seen.add(menuId);
        ids.push(menuId);
      }
      if (Array.isArray(item.children)) {
        walk(item.children as Array<{ menu_id?: number; id?: number; children?: unknown[] }>);
      }
    });
  };
  walk(scopedNavigationTree());
  return ids;
}

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

.danger-ghost {
  border-color: var(--sc-app-danger-border);
  color: var(--sc-app-danger-text);
}

.danger-ghost:hover:not(:disabled) {
  background: var(--sc-app-danger-bg);
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
  margin: 0;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.guide-panel {
  display: grid;
  gap: 12px;
  margin: 0;
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
  margin: 0;
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
  margin: 0;
  display: grid;
  gap: 10px;
  padding: 12px;
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

.version-panel-header > div {
  display: grid;
  gap: 3px;
}

.version-panel-header span {
  color: var(--sc-app-text-secondary);
}

.version-current-card,
.version-preview {
  display: grid;
  gap: 5px;
  padding: 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-muted-bg);
  color: var(--sc-app-text-secondary);
}

.version-current-card strong,
.version-preview strong {
  color: var(--sc-app-text-primary);
}

.version-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 8px;
  max-height: 220px;
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
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
  gap: 4px 8px;
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

.version-item.current {
  cursor: default;
}

.version-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.version-title b {
  padding: 1px 5px;
  border-radius: 999px;
  background: var(--sc-app-success-bg);
  color: var(--sc-app-success-text);
  font-size: 11px;
  font-weight: 600;
}

.version-meta {
  grid-column: 2;
  min-width: 0;
  color: var(--sc-app-text-secondary);
}

.version-preview {
  border-color: var(--sc-app-warning-border);
  background: var(--sc-app-warning-bg);
  color: var(--sc-app-warning-text);
}

.version-preview .danger {
  justify-self: start;
  min-height: 32px;
  padding: 0 12px;
  border: 1px solid var(--sc-app-danger-border);
  border-radius: 6px;
  background: var(--sc-app-danger-bg);
  color: var(--sc-app-danger-text);
  font-weight: 600;
  cursor: pointer;
}

.version-preview .danger:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.create-panel {
  margin: 0;
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
  gap: var(--sc-product-workspace-gap);
  padding: 0 0 18px;
}

.menu-config-tree {
  min-width: 0;
  border: 1px solid var(--sc-app-border);
  border-right: 0;
  background: var(--sc-app-panel);
}

.tree-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
  padding: 12px 12px 10px;
  border-bottom: 1px solid var(--sc-app-border);
}

.tree-panel-head strong {
  display: block;
  color: var(--sc-app-text-primary);
  font-size: 14px;
}

.tree-panel-hint {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  padding: 3px 8px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-secondary);
  font-size: 11px;
  line-height: 1.4;
  white-space: nowrap;
}

.tree-panel-hint b {
  color: var(--sc-app-info-text);
  font-weight: 600;
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

.tree-search-summary {
  min-height: 26px;
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--sc-app-text-muted);
  font-size: 12px;
  line-height: 1.4;
}

.tree-clear-filter {
  flex: 0 0 auto;
  min-height: 24px;
  padding: 0;
  font-size: 12px;
}

.tree-clear-filter:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.tree-state-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  padding: 8px 10px 10px;
  border-bottom: 1px solid var(--sc-app-border);
}

.tree-state-tabs button {
  min-width: 0;
  min-height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  padding: 0 8px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  cursor: pointer;
}

.tree-state-tabs button span,
.tree-state-tabs button b {
  min-width: 0;
  white-space: nowrap;
}

.tree-state-tabs button b {
  color: var(--sc-app-text-primary);
  font-weight: 700;
}

.tree-state-tabs button.active {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
}

.tree-state-tabs button.active b {
  color: var(--sc-app-info-text);
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

:deep(.tree-node > span:nth-child(2)) {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-shortcuts {
  padding: 6px;
  border-bottom: 1px solid var(--sc-app-border);
}

.tree-node.all {
  padding: 8px 12px;
  border-radius: 4px;
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
  gap: var(--sc-product-workspace-gap);
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

.menu-selected-badges {
  display: inline-flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
  min-width: 120px;
}

.menu-origin-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 22px;
  max-width: 100%;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  padding: 0 8px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
}

.menu-origin-badge.deletable {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
}

.menu-origin-badge.locked {
  background: var(--sc-app-muted-bg);
  color: var(--sc-app-text-secondary);
}

.menu-origin-badge.visible {
  border-color: var(--sc-app-success-border);
  background: var(--sc-app-success-bg);
  color: var(--sc-app-success-text);
}

.menu-origin-badge.hidden {
  border-color: var(--sc-app-warning-border);
  background: var(--sc-app-warning-bg);
  color: var(--sc-app-warning-text);
}

.menu-origin-badge.unconfigured {
  background: var(--sc-app-muted-bg);
  color: var(--sc-app-text-secondary);
}

:deep(.tree-origin-badge) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  margin-left: auto;
  min-height: 18px;
  min-width: 34px;
  border-radius: 5px;
  padding: 0 6px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
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
  grid-template-columns: minmax(0, 1fr) minmax(88px, 0.35fr) minmax(112px, 0.4fr);
}

.menu-detail-grid label {
  display: grid;
  gap: 6px;
  min-width: 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.menu-visible-toggle {
  grid-template-columns: auto 1fr;
  align-content: end;
  align-items: center;
  box-sizing: border-box;
  width: 100%;
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
  height: 118px;
  max-height: 118px;
  align-content: start;
}

.menu-side-panel {
  display: grid;
  gap: 0;
  align-self: start;
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

.action-hint {
  margin-top: 2px;
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
  min-height: 58px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--sc-app-border);
}

.bulk-toolbar-title {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.bulk-toolbar-title strong {
  color: var(--sc-app-text-primary);
  font-size: 16px;
}

.bulk-toolbar-title span:not(.panel-kicker) {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.table-toolbar-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.bulk-stat {
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  padding: 3px 8px;
  background: var(--sc-app-bg);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  white-space: nowrap;
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
  min-width: 900px;
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

.status-col {
  width: 72px;
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
  gap: 4px;
  max-height: 96px;
  overflow: auto;
  box-sizing: border-box;
  padding: 6px;
  border: 1px solid var(--sc-app-border);
  border-radius: 4px;
  background: var(--sc-app-panel);
}

.group-check-item {
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr);
  align-items: center;
  min-height: 18px;
  min-width: 0;
  gap: 4px;
  color: var(--sc-app-text-primary);
  font-size: 11px;
  line-height: 1.4;
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
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  background: var(--sc-app-bg);
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
    row-gap: var(--sc-product-workspace-stack-gap);
  }

  .menu-config-editor {
    grid-template-columns: 1fr;
    row-gap: var(--sc-product-workspace-stack-gap);
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

  .table-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .table-toolbar-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .tree-scroll,
  .table-wrap {
    max-height: none;
  }
}
</style>
