## 2026-04-24 List Selection Contract Smoke

- 目标：把“列表选择态必须显示 live `ui.contract` 下发的 `selection` 动作”沉淀成自动浏览器回归，而不是继续靠人工点检。
- 新增脚本：`frontend/apps/web/scripts/list_selection_contract_smoke.mjs`
- 覆盖对象：
  - `payment.request` (`/a/473?menu_id=273`)
  - `project.material.plan` (`/a/471?menu_id=305`)
- 断言：
  - 页面实际 `ui.contract` 响应里必须存在 `selection=single|multi`
  - 勾选记录后，`.batch-bar` 必须出现除 `清空` 外的动作按钮
  - DOM 按钮文案必须与 contract 下发动作存在交集
- 产物：
  - `artifacts/playwright/logs/list_selection_contract_smoke.json`
  - `artifacts/playwright/screenshots/list_selection_*.png`
## Form Action Alignment

- Batch: `FE/BE-form-action-align`
- Scope:
  - `addons/smart_core/handlers/ui_contract.py`
  - `frontend/apps/web/src/pages/ContractFormPage.vue`
- Findings:
  - 审核表单按钮偏多并非单点前端问题。
  - `ui.contract(action_open -> form)` 曾混入：
    - `selection=multi` 的 list server actions
    - act_window 导航动作
  - `ContractFormPage` 又会把 `buttons + toolbar.header + sidebar + footer` 一并消费，导致表单态动作与原生不对齐。
- Fix:
  - 后端在 `action_open(form)` 上收窄到 native form-compatible surface：
    - 仅保留 `selection=none`
    - 仅保留 `header/smart/sidebar/footer`
    - 清空 `toolbar.header`
  - 前端再按当前 `renderProfile`、`selection=none`、`level !== toolbar` 过滤，避免后端回退时再次溢出。
- Live Result:
  - `payment.request` 顶层 form contract 已只剩原生 5 个 header 状态按钮 + 1 个 `付款记录` stat button。
  - `付款申请审批通过回调 / 驳回回调 / 我的付款申请` 已不再进入 form action surface。

## Tier Review List Action Alignment

- Batch: `BE-tier-review-list-action-align`
- Scope:
  - `addons/smart_core/utils/contract_governance.py`
  - `addons/smart_core/tests/test_action_dispatcher_server_mapping.py`
- Findings:
  - `tier.review` 的两个待审列表入口 `494/495` 原先会把当前页和兄弟页 act_window 当成列表动作一起交付。
  - 这组动作不属于原生列表能力，只会形成循环导航和重复入口。
- Fix:
  - 在 user contract 的 `tier.review` list governance 中，剔除 `smart_construction_core.action_sc_tier_review_my_*` 前缀动作。
- Live Result:
  - `action_open=494` 与 `action_open=495` 现在都不再暴露这组导航动作。
  - live `ui.contract` 结果：`buttons=[]`, `toolbar.header=[]`。

## List-A Native Alignment Audit

- Batch: `List-A`
- Scope:
  - `frontend/apps/web/src/pages/ListPage.vue`
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/components/page/PageToolbar.vue`
  - `frontend/apps/web/src/app/action_runtime/useActionViewFilterComputedRuntime.ts`
  - `frontend/apps/web/src/app/action_runtime/useActionViewGroupedRowsRuntime.ts`
  - `frontend/apps/web/src/app/action_runtime/useActionViewActionGroupingRuntime.ts`
- Representative samples:
  - `action_open=452` / `project.project`
  - `action_open=473` / `payment.request`
  - `action_open=471` / `project.material.plan`
- Frozen facts:
  - live DOM 三个代表列表当前都能直接进入 table 主体，但统一存在 `focusStrip=1`，说明列表主链前面仍挂着一层产品化 header/focus 编排。
  - live DOM 三个代表列表当前都没有出现 `pageToolbar / summaryStrip / batchBar / groupedTable / quickFilters / routePreset / quickActions`，这些增强区块并非当前默认渲染主链必现项。
  - live contract 三个代表列表都返回：
    - `head.view_type = tree`
    - `search` 完整存在（`defaults/facets/filters/group_by/saved_filters`）
  - `project.project` 额外返回 `list_profile`，而 `payment.request` / `project.material.plan` 没有 `list_profile`，说明当前列表列语义来源并不统一。
  - `payment.request` / `project.material.plan` 的 live contract 仍混有 `header/smart/toolbar` 动作，当前只是经过前端选择态收敛后不再全部露出，不代表列表动作面已与原生 tree 完全对齐。
- Owner matrix:
  - `native-required`
    - table columns / row records
    - checkbox selection
    - native `selection` action surface
    - contract `search.filters/group_by/order`
  - `contract-declared`
    - `head`
    - `search`
    - `buttons/toolbar`
    - `list_profile`（仅部分模型）
  - `frontend-derived`
    - `PageHeader`
    - `focus_strip`
    - action grouping（`basic/workflow/drilldown`）
    - grouped rows pagination / expand-collapse runtime
  - `frontend-inferred`
    - `PageToolbar` 固定 chips：`全部 / 在办 / 已归档`
    - 列表增强区块的固定露出策略
    - 一部分排序 / 过滤 budget slicing
- Execution plan:
  - `List-B`: 先收掉 `frontend-inferred`，从默认主链剥离固定 chips、固定增强区块露出条件。
  - `List-C`: 再收 `frontend-derived`，把必须保留的 grouped rows / header chrome / action grouping 迁回 contract 或降为外挂区。
  - `List-D`: 最后补浏览器回归和 intrusion guard，把列表页的 native-aligned 语义固化。

## List-B Default Exposure Cleanup

- Batch: `List-B`
- Scope:
  - `frontend/apps/web/src/components/page/PageToolbar.vue`
  - `frontend/apps/web/src/pages/ListPage.vue`
  - `frontend/apps/web/src/views/ActionView.vue`
- Changes:
  - `PageToolbar` 去掉固定 filter chips `全部 / 在办 / 已归档`，保留搜索和 contract-driven 排序。
  - `ListPage` 不再向 `PageToolbar` 传递固定 `filterValue / onFilter` UI 语义。
  - `ActionView` 将下列增强区块的默认露出从 `true` 改为 `false`，只允许 contract/page section 显式开启时显示：
    - `route_preset`
    - `focus_strip`
    - `quick_filters`
    - `saved_filters`
    - `group_view`
    - `group_summary`
    - `quick_actions`
- Result:
  - 列表默认主链进一步收回到 `tree table + contract search/sort + selection action`。
  - 不再由前端默认外挂固定 chips 和产品增强区块。

## List-C Derived Surface Reduction

- Batch: `List-C`
- Scope:
  - `frontend/apps/web/src/components/page/PageHeader.vue`
  - `frontend/apps/web/src/pages/ListPage.vue`
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/app/action_runtime/useActionViewActionGroupingRuntime.ts`
- Changes:
  - `PageHeader` 去掉前端派生的：
    - `mode`
    - `record count`
    - `status pill`
    - `刷新` 按钮
    - 仅保留标题和副标题。
  - `ListPage` 的 `summary-strip` 改成默认关闭，只有显式 `summary_strip` section 开启才显示。
  - `ListPage` 的自定义 `grouped-table` 改成默认关闭，只有显式 `grouped_table` section 开启才显示。
  - `ActionView` 现在显式把 `summary_strip` / `grouped_table` 默认值收为 `false`。
  - 列表 `quick actions` 的动作排序不再按前端 `basic/workflow/drilldown` 语义重排，改为保持 contract 原顺序；overflow 也统一折叠为单一“更多操作”组。
- Result:
  - 列表默认视觉层更接近原生 tree/list。
  - 前端不再默认注入状态胶囊、条数胶囊、刷新按钮、自定义摘要带、自定义 grouped table。
  - 快捷动作若被显式开启，也不再按前端产品语义重排。

## Scene Route Target Drift Fix

- Batch: `Scene-Target-Drift-Fix`
- Frozen fact:
  - `/a/452?menu_id=281` 的项目列表 action-route 已经正确，浏览器表头与 `project.project list_profile` 对齐。
  - 真正错误的是 scene-route：
    - `/s/projects.list` 命中 `action_id=519/menu_id=329`
    - `/s/projects.ledger` 命中 `action_id=495/menu_id=280`
  - `addons/smart_construction_scene/profiles/scene_registry_content.py` 中这两个 scene 的 registry source 是正确的：
    - `projects.list -> action_sc_project_list / menu_sc_root`
    - `projects.ledger -> action_sc_project_kanban_lifecycle / menu_sc_project_project`
  - 漂移发生在 `addons/smart_construction_scene/scene_registry.py`：
    - DB scene payload 含 stale numeric `action_id/menu_id`
    - 与 registry fallback 合并时仅补缺字段，不会用 fallback 的 `action_xmlid/menu_xmlid` 覆盖旧 numeric
    - 导致下游 `scene registry -> capability default_payload -> scene route handoff` 一起带歪
- Fix:
  - 在 `scene_registry.load_scene_configs_with_timings()` 的 DB/fallback merge 阶段新增 target identity upgrade：
    - 若 fallback target 含 `action_xmlid/menu_xmlid`
    - 则把 xmlid 身份覆盖到当前 scene target
    - 并移除 stale `action_id/menu_id`
    - 同时补齐缺失的 `route/model/view_mode/view_type/record_id`
- Files:
  - [addons/smart_construction_scene/scene_registry.py](/home/lidefend/sce-backend-odoo/addons/smart_construction_scene/scene_registry.py)
  - [addons/smart_construction_scene/tests/test_scene_registry_yaml_asset_merge.py](/home/lidefend/sce-backend-odoo/addons/smart_construction_scene/tests/test_scene_registry_yaml_asset_merge.py)
- Verification:
  - `python3 -m unittest addons.smart_construction_scene.tests.test_scene_registry_yaml_asset_merge`：PASS
  - `pnpm -C frontend/apps/web typecheck:strict`：PASS
  - `make restart`：PASS

## Scene Runtime Asset Drift Fix

- Batch: `Scene-Runtime-Asset-Drift-Fix`
- Frozen fact:
  - live `system.init` 里 `scene_ready_contract_v1.projects.list` 仍然错误绑定到了：
    - `meta.target.action_id = 519`
    - `meta.target.menu_id = 329`
    - `meta.ui_base_contract_source.source_ref = action:519`
  - 这说明问题不在列表 consumer，而在 scene runtime surface 自己继续复用了 stale `ui_base_contract` asset。
- Root cause:
  - `scene_provider.merge_missing_scenes_from_registry()` 只会基于已有 scene `target` 继续向下走。
  - `ui_base_contract_asset_repository._asset_is_stale_for_scene()` 只把“纯 canonical scene root + action asset”判为 stale，`projects.list` 这种带 fallback target 的 scene 不会触发失效。
  - 结果是旧 asset `action:519` 会持续进入 `scene_ready_contract_v1`。
- Fix:
  - `addons/smart_core/core/scene_provider.py`
    - 新增 provider payload identity upgrade。
    - 对 critical scene，如果 provider 的 `primary_action/fallback_strategy` 已给出 canonical `action_xmlid/menu_xmlid`，运行时 target 直接按 provider xmlid 升级并重新 hydrate。
  - `addons/smart_core/core/ui_base_contract_asset_repository.py`
    - action-backed scene 如果当前 scene 的 resolved action identity 与 asset `source_ref=action:*` 不一致，也判为 stale。
    - 这样 `projects.list` 的旧 `action:519` asset 会被淘汰并刷新为 `action:452`。
  - Tests:
    - [addons/smart_core/tests/test_scene_provider_target_identity_merge.py](/home/lidefend/sce-backend-odoo/addons/smart_core/tests/test_scene_provider_target_identity_merge.py)
    - [addons/smart_core/tests/test_ui_base_contract_asset_repository.py](/home/lidefend/sce-backend-odoo/addons/smart_core/tests/test_ui_base_contract_asset_repository.py)
- Live verification:
  - `system.init` 现在返回：
    - `projects.list.meta.target.action_id = 452`
    - `projects.list.meta.target.menu_id = 265`
    - `projects.list.meta.ui_base_contract_source.source_ref = action:452`
  - 这说明 `/s/projects.list` 已经回到正确的 `project.project` base contract 源。
## Batch-Nav-DualTrack-Freeze

### 目标

冻结 `action/menu` 与 `scene` 的双轨规则，停止继续用启发式把两条链混在一起。

### 已确认事实

- `projects.list` canonical 链：
  - scene route: `/s/projects.list`
  - target action: `452`
  - live `ui.contract(452)` 已返回正确 `list_profile.columns / column_labels`
- 旧 demo showcase 链：
  - menu: `343`
  - action: `536`
  - xmlid:
    - `smart_construction_demo.menu_sc_project_list_showcase`
    - `smart_construction_demo.action_sc_project_list_showcase`
  - 标题：`项目列表（演示）`
  - 该链属于旧 `action/menu` 轨，不属于 canonical `projects.list`

### 架构结论

- `action/menu` 允许继续存在
- `scene` 允许继续存在
- 当前必须双轨并存
- `scene_key` 不是 owner signal
- `meta.scene_source=scene_contract` / `meta.action_type=scene.contract` 才是 owner signal
- 定稿口径：
  - `action = native source of truth`
  - `scene = compiled delivery surface`

### 规范文档

- [navigation_dual_track_contract_v1.md](/home/lidefend/sce-backend-odoo/docs/architecture/navigation_dual_track_contract_v1.md)

### 后续要求

- 先按双轨规范清菜单树与入口类型
- 再继续做列表/表单显示对齐
- 禁止再通过“看到 scene_key 就改标题/改路由”的启发式继续修

### Batch-Nav-DualTrack-Cleanup-1

- 已将旧 demo showcase 项目列表入口从 scene map 中摘除：
  - `smart_construction_demo.menu_sc_project_list_showcase`
  - `smart_construction_demo.action_sc_project_list_showcase`
- 目的：
  - 保留其作为旧 `action/menu` 轨入口存在
  - 但不再被声明为 canonical `projects.list` scene
- 当前规则收口为：
  - canonical 项目列表：`projects.list -> 452`
  - showcase 演示列表：`343/536 -> 旧 action/menu`
  - 两者不再共享同一个 `scene_key` 身份
