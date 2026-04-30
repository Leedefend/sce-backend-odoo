# Frontend Native Business Alignment Batch 2026-04-29

Status: `PASS_WITH_KNOWN_RENDERER_GAPS`

## Scope

- Layer Target: `Frontend Page Orchestration / Backend Contract Governance`
- Module: `addons/smart_core`, `addons/smart_construction_core`, `scripts/verify`, `frontend/apps/web`
- Database: `sc_prod_sim`
- Frontend: `http://127.0.0.1:5174`
- Real user: `chenshuai / 123456`

## Corrected Conclusion

The earlier approve/reject browser closure was not sufficient. It proved that
records could be opened from `我的工作` and approval actions could execute, but
it did not prove that form internals were delivered or usable.

The deep form acceptance found and fixed these blockers:

- `views.form.layout` was pruned by contract sanitization, leaving the custom
  page without native group/notebook/x2many structure.
- Existing record routes sent `render_profile=edit`, but backend governance
  returned `render_profile=create`; edit-only fields such as
  `purchase.order.order_line` were hidden.
- Native relation fields in layout could still be classified as technical,
  causing business x2many fields to be filtered out of the user surface.
- one2many descriptors did not expose `relation_field`, so the save path could
  not build a deterministic dry-run write.
- SC business users did not imply `smart_core.group_smart_core_data_operator`,
  so write intents were blocked before Odoo model ACL/record rules could decide.

## Fixes

- Preserved full form contract structures during governance sanitization:
  `layout`, `header_buttons`, `stat_buttons`, `field_modifiers`, `subviews`,
  `chatter`, `attachments`.
- Preserved request runtime metadata in page contracts:
  `record_id`, `res_id`, and `render_profile`.
- Marked native layout relation fields as business `relation` semantics unless
  they are known technical mail/activity/rating/website fields.
- Added one2many `relation_field` from Odoo `inverse_name`.
- Added `purchase.order.line` to the controlled data write allowlist for dry-run
  line-create validation.
- Added `smart_core.group_smart_core_data_operator` to `group_sc_internal_user`;
  platform write intent access now opens the channel, while Odoo ACL and record
  rules still control actual business write permission.
- Updated one2many smoke scripts to consume the current recursive
  `views.form.layout` contract shape.

## Evidence

Native/custom structure coverage:

- `payment.request`: `field=31 group=9 header=1 sheet=1`
- `construction.contract`: `field=27 group=4 notebook=1 page=2 header=1 sheet=1`
- `purchase.order`: `field=38 group=9 notebook=1 page=2 header=1 sheet=1`
- `sc.settlement.adjustment`: `field=17 group=7 header=1 sheet=1`

Real browser DOM acceptance:

- Artifact: `artifacts/browser-real-user-form-structure/matrix_20260429T162048Z/matrix_recheck.json`
- Artifact: `artifacts/browser-real-user-form-structure/purchase_real_20260429T162902Z/purchase_order_9_real_recheck.json`
- `purchase.order/9`: `render_profile=edit`, `record_id=9`,
  `order_line.relation_field=order_id`, label `订单行` visible,
  relation editor visible, `+ 新增行` visible.

Makefile verification:

- `verify.portal.view_contract_coverage_smoke.container`:
  `PASS` for `payment.request`, `construction.contract`, `purchase.order`,
  `sc.settlement.adjustment`.
- `verify.portal.one2many_read_smoke.container`:
  `PASS one2many_field=order_line`.
- `verify.portal.one2many_edit_smoke.container`:
  `PASS one2many_edit field=order_line`.

## Residual Design Gap

2026-04-29 项目详情页追加验收结论：

- 根因：`project.project.get_view(form)` 的父 arch 包含 `task_ids` 内联
  tree，但 `get_view()['fields']` 漏掉了只出现在 inline x2many 子视图中的
  字段元数据，后端 parser 因此没有产出 `views.form.subviews.task_ids`。
- 修复：`app.view.parser` 先从原生 arch 扫描字段，再用模型
  `fields_get` 补齐缺失字段；x2many 子视图列补充 relation fields、列标签、
  类型、required/readonly/selection。
- 修复：`ContractFormPage` 改为优先递归消费 `views.form.layout`，不再用旧
  `contractVisibleFields` 白名单挡住原生 layout 显式字段；原生静态
  `invisible=1` 节点在前端隐藏。
- 修复：one2many 新增行过滤 id/sequence/count/audit/readonly/non-scalar 列，
  避免真实用户先看到技术列。
- 边界修正：上述 one2many 列过滤已从前端撤回到后端契约。前端不再判断
  技术列、只读列、optional/column_invisible/invisible 列，也不再固定截断
  one2many columns；前端只渲染 `views.form.subviews.*.tree.columns`。
- 后端契约新增/保留语义：`tree.column_policy.surface=business_edit`、
  `tree.column_policy.front_end_filtering=false`、列级 `surface_role=business_edit`；
  若无可办理列，后端设置 `policies.can_create=false` 与
  `reason_code=NO_BUSINESS_EDIT_COLUMNS`。

追加验证：

- `project.project` parser shell：`subviews_keys=['activity_ids','collaborator_ids','tag_ids','task_ids']`；
  `task_ids.columns_count=23 fields_count=108`；
  `collaborator_ids.columns_count=2 fields_count=9`。
- 真实浏览器 `chenshuai / sc_prod_sim / project.project/771`：
  `native-tabs=['描述','设置','协作 / 系统']`，`relationEditors=3`，
  `+ 新增行=2`。
- 真实浏览器新增任务行 dry UI：
  新增行可达，显示 `Priority / State / Title / 工程状态`。这些列由后端
  `task_ids.tree.columns` 直接给出，前端没有再做技术列过滤。
- 真实浏览器协作页签：
  `addRowsBefore=1`，`collaborator_ids` 因后端
  `policies.can_create=false` 不再显示新增入口。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。
- `python3 -m py_compile` parser 文件：`PASS`。
- `verify.portal.view_contract_coverage_smoke.container`：
  `PASS` with `ALLOWED_MISSING=ribbon,chatter`，artifact:
  `/mnt/artifacts/codex/portal-shell-v0_8-semantic/20260429T171933`。

仍未收口：

- `ribbon` 与 `chatter` 仍是覆盖 smoke 的已知缺口，不得宣称项目表单已经与
  Odoo 原生视觉/协作区完全一致。
- 字段翻译仍受当前 contract 语言上下文影响，部分 Odoo 标准字段在自定义页
  仍显示英文（如 `Customer`、`Project Manager`、`Tasks`）。

因此本批验收目标调整为：

- native structure is preserved in contract;
- custom page receives the correct edit profile and record id;
- business fields and relation editors are reachable;
- x2many read and save dry-run paths are available to real users.

Full visual parity with Odoo native form rendering, including `ribbon`,
`chatter`, and exact translation parity, remains a follow-up renderer/contract
upgrade. It is not a blocker for this batch's business form reachability, but it
is a blocker for any claim of pixel/structure parity with Odoo native.

## 2026-04-30 精确对比修复追加

根因修正：

- `project.project` 业务页签缺失不是前端过滤问题，根因是后端 native view
  解析链使用 `sudo/admin` 合成视图。Odoo 在 `get_view` 合成继承视图时会按
  当前用户 groups 裁剪 XML；`wutao/chenshuai` 原生可见 11 个页签，而
  admin/sudo 路径只剩 `描述/设置/协作 / 系统`。
- 修复后，`app.view.config` 与 `app.view.parser` 使用当前真实用户合成
  native view；仅平台配置记录读取/写入提权，运行态 group/ACL 过滤仍绑定真实用户。
- `views.form.header_buttons/button_box` 纳入前端既有 action 渲染链；
  `views.form.chatter.actions` 由后端契约给出，前端只按契约渲染
  `发送消息/记录备注/活动`。

验证：

- Odoo shell：`wutao/chenshuai` 的 `project.project.form` contract 均包含
  `投标管理、施工信息、WBS结构、工程量清单、工程结构、合同、工程资料、驾驶舱、描述、设置、协作 / 系统`。
- Odoo shell：`chatter.enabled=true`，`header_buttons` 包含
  `共享只读、分享可编辑的内容、提交立项、预算、合同、邀请合作者`。
- 真实浏览器对比：artifact
  `artifacts/browser-real-user-form-structure/project_precision_compare_final_20260429173843/summary.json`。
- 真实浏览器结果：自定义页 11 个 expected tabs 全部 visible；
  `customMissingExpectedTabs=[]`，`customHiddenExpectedTabs=[]`。
- 真实浏览器结果：自定义页与原生页均出现
  `共享只读、分享可编辑的内容、提交立项、发送消息、记录备注、活动`；
  `presentDiff={}`。
- `python3 -m py_compile` parser/assembler 文件：`PASS`。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。

当前结论：

- 项目详情页“原生结构字段/页签/header/chatter 关键交付可达性”已按真实用户浏览器验收通过。
- 仍未声明像素级完全一致；ribbon、Odoo 原生 chatter 消息流真实交互、复杂 widget
  视觉细节仍属于后续 renderer 能力升级范围。

## 2026-04-30 复杂交互机制追加

本轮继续以 `project.project/771` 为典型页，验收详情页内部复杂交互：

- 后端 parser 对 `views.form.layout` 内的 body/button 节点补齐标准化
  `action` 契约，包含 `kind/level/selection/intent/payload/visible`，页签内
  按钮不再只是静态 label。
- 前端 `NativeFormTreeRenderer` 按 layout 节点渲染页签内按钮，并通过
  `native-action` 事件把后端 action row 交给既有 `runAction` 执行链。
  前端没有推断按钮业务语义。
- `ui.contract` 与 `load_view/load_contract` 在未显式传 `lang` 时默认使用
  当前真实用户 `user.lang`。本轮发现 `task_ids` 子视图 API 已可返回中文，
  但 `ui.contract` 主链仍沿用默认上下文导致浏览器显示
  `Priority/State/Title`；已修复为两条契约入口一致。
- 项目原生 layout 已有字段时，不再从 `visible_fields` 回填
  `补充业务信息`，避免污染 native page 结构。

验证结果：

- API `ui.contract`：
  `task_ids.tree.columns=[优先级,状态,称谓,工程状态]`，selection 也按
  `zh_CN` 返回。
- 真实浏览器：
  artifact
  `artifacts/browser-real-user-form-structure/project_complex_interactions_final_20260429T180404/summary.json`。
- 真实浏览器结果：
  `hasBackfill=false`；
  11 个项目页签全部可见；
  `工程量清单` 页签内
  `导入清单、生成工程结构、生成施工任务、工程量清单分析、重建工程量清单层级、校验工程量清单`
  全部可见；
  点击安全跳转按钮 `工程量清单分析` 后进入
  `/a/523?action_id=523`；
  `协作 / 系统` 页签 `+ 新增行` 可见，新增行显示
  `优先级、状态、称谓、工程状态`。
- `python3 -m py_compile`：
  `load_contract.py`、`ui_contract.py`、parser、contract governance 均 `PASS`。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。

风险边界：

- `生成工程结构`、`重建工程量清单层级`、`校验工程量清单` 等按钮已验证可见且
  有后端 action 契约，但未在模拟生产业务数据上直接点击，以避免触发真实变更。
  本轮实际点击的是安全导航型按钮 `工程量清单分析`。
- 仍未声明像素级完全一致；chatter 消息流、ribbon 与复杂 widget 视觉细节仍属于
  后续 renderer 能力升级范围。

## 2026-04-30 整体结构与重复渲染追加

本轮用户复核指出：项目详情页整体结构仍未对齐，且存在字段/动作重复渲染。
复核后确认问题不是后端缺少字段，而是前端同时使用了多条结构源：

- 页面外层仍渲染 `headerActions`、`workflowTransitions`、`bodyActions`、
  `searchFilters`；
- `NativeFormTreeRenderer` 同时递归渲染 `views.form.layout` 中的
  header/button_box/page buttons；
- 单字段节点即使被 native modifiers/policy 判定不可见，也会生成空
  `字段` section；
- 无标题 group 会被前端补成 `信息组`，header 会被补成 `头部`；
- 原生 `oe_title/h1` 容器未被 renderer 当作结构容器消费，导致项目标题区字段缺失。

修复：

- native form tree 模式下，关闭外层 `headerActions`、`workflowTransitions`、
  `bodyActions` 与 `searchFilters` 渲染，表单主体只消费
  `views.form.layout`。
- `NativeFormTreeRenderer` 仅在 `fieldSchemasForNodes(...)` 非空时渲染
  FormSection，避免不可见字段生成空块。
- 无标题 `group/sheet/field/header` 不再由前端补造 `信息组/字段/头部` 标题。
- 通用 renderer 支持 `container/div/span/h1/h2/h3` 结构节点，恢复
  `oe_title/h1` 中的标题字段。
- `FormSection` 在无标题且无 action slot 时不渲染空 section header。

验证：

- 真实浏览器结构验收 artifact:
  `artifacts/browser-real-user-form-structure/project_structure_final_1777486542108/summary.json`。
- 结果：
  `快捷筛选=0`、`字段=0`、`信息组=0`、`头部=0`；
  `共享只读/分享可编辑的内容/提交立项` 均只出现 1 次；
  `名称` 标题字段已出现；
  11 个原生页签仍全部可见。
- 复杂交互回归 artifact:
  `artifacts/browser-real-user-form-structure/project_structure_interaction_regression_1777486585531/summary.json`。
- 回归结果：
  `工程量清单` 页签内 6 个按钮仍全部可见；
  `协作 / 系统` 页签 `+ 新增行` 仍可达；
  新增行仍显示 `优先级、状态、称谓、工程状态`。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。

当前边界：

- 本轮收口的是结构源重复与明显前端补造标题，不声明像素级完全一致。
- Odoo `statusbar` widget、`web_ribbon`、真实 chatter 消息流和复杂 widget
  视觉仍需后续 renderer 专项升级。

## 2026-04-30 模拟生产库原生中文基线追加

本轮用户复核指出：Odoo 原生菜单/原生视图默认语言仍出现英文。这不是前端渲染
问题，也不是自定义页面应当兜底的问题；根因在模拟生产/全新历史库初始化流程：

- 旧流程只激活 `zh_CN` 语言记录、设置用户 `user.lang`，但模块安装阶段没有
  确定性执行 `--load-language=zh_CN`；
- 扩展模块安装后也没有刷新已安装模块翻译，因此原生菜单、原生 view arch 与
  字段 label 可能仍沿用英文；
- 平台 preflight 没有把语言基线作为门禁，导致重建成功但原生可用性不完整。

修复：

- `prod_sim_oneclick.sh` 与 `fresh_production_history_init.sh` 的 Odoo 模块安装
  增加 `--load-language=${SC_RUNTIME_LANG:-zh_CN}`。
- 新增 `scripts/ops/ensure_runtime_language_baseline.py`：通过 Odoo
  `base.language.install` 对已安装模块刷新 `zh_CN` 翻译，统一用户语言/时区，
  并写入平台默认语言/时区参数。
- 新增 `scripts/verify/runtime_language_baseline_probe.py`：校验 `zh_CN` 存在且
  active、关键真实用户 `admin/wutao/chenshuai` 为中文/中国时区、项目原生表单
  字段 label 和关键按钮为中文、原生菜单为中文。
- Makefile 新增 `runtime.language.ensure` 与
  `verify.runtime.language.baseline`，作为当前库修复入口和后续重建门禁。

验证：

- `python3 -m py_compile scripts/ops/ensure_runtime_language_baseline.py scripts/verify/runtime_language_baseline_probe.py`：
  `PASS`。
- `bash -n scripts/deploy/prod_sim_oneclick.sh scripts/deploy/fresh_production_history_init.sh`：
  `PASS`。
- `sc_prod_sim make runtime.language.ensure`：
  `PASS; lang=zh_CN; users=113; users_updated=1; translations_overwrite=True`。
- `sc_prod_sim make verify.runtime.language.baseline`：
  `PASS; project.project fields=名称/客户/项目管理员/可见性; form strings=提交立项/预算/合同/执行结构/工程量清单; menus=智能施工 2.0/项目台账（试点）`。

结论：

- 本缺口已经从“本次手工修复”提升为“重建流程确定性初始化 + 门禁探针”。
- 后续新库只要走 `prod_sim_oneclick.sh` 或 `fresh_production_history_init.sh`
  主流程，不应再因同一原因出现原生菜单/原生视图默认英文。
- 若绕过主流程直接安装模块或只恢复数据库，必须显式运行
  `make runtime.language.ensure` 和 `make verify.runtime.language.baseline`。

## 2026-04-30 项目详情复杂办理闭环追加

用户继续复核指出三个真实办理缺口：

- 项目详情页自定义页面缺少 Odoo 原生 `statusbar` 项目状态条；
- many2one 下拉只有有限选项和新建入口，没有原生“搜索更多”的完整搜索弹窗；
- 同名新建触发数据库唯一约束时，底层数据库错误直接暴露给用户。

修复：

- 前端按 `views.form.statusbar` 渲染通用状态条，不再把
  `widget=statusbar` 字段当普通 selection 显示；状态值、选项、只读性均来自后端
  contract/field policy。
- many2one 通用表单 schema 增加 `many2oneSearchToken`，`FormSection` 下拉增加
  `搜索更多...` 入口；`ContractFormPage` 打开通用关系搜索弹窗，通过
  `api.data list` 按后端 relation/domain/context 查询完整候选并选择回填。
- 搜索弹窗支持在后端契约允许的 `quick/page` 新建模式下发起新建；quick 新建前先搜索
  同名记录，命中则直接选择已有记录，避免重复创建。
- `api.data create` 对唯一约束/数据库异常做用户友好消息归一；前端
  `sanitizeUiErrorMessage` 同步屏蔽 `psycopg2/SQL/Traceback` 等底层异常文本。

验证：

- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。
- `python3 -m py_compile addons/smart_core/handlers/api_data.py`：`PASS`。
- 真实浏览器 `wutao / sc_prod_sim / project.project/771`：
  - `native-statusbar=1`；
  - 状态条显示 `草稿、在建、停工、竣工、结算中、保修期、关闭`；
  - many2one 下拉 `搜索更多...` 入口出现；
  - 点击后打开 `.relation-dialog`；
  - 搜索弹窗返回 `120` 条可选记录。

边界：

- 本轮补齐的是通用 statusbar 与 many2one 搜索/新建闭环；未声明 Odoo 所有复杂 widget
  已完全复刻。
- full page 新建仍按后端 `relation_entry.action_id/menu_id` 跳转维护页；quick 新建仅在
  后端契约允许时启用。

### 状态条视觉修正

用户复核认为状态条虽然出现，但视觉仍像普通按钮条，不符合原生状态推进形态。

修复：

- 保持 `views.form.statusbar` 契约来源不变，只调整前端通用渲染样式；
- 状态段改为 chevron 箭头推进形态；
- 完成态、当前态、未到达态分别使用不同层级与颜色；
- 移动/窄屏下保持横向滚动，避免状态文本挤压换行。

验证：

- 真实浏览器 `wutao / sc_prod_sim / project.project/771`：
  `native-statusbar=1`，labels=
  `草稿/在建/停工/竣工/结算中/保修期/关闭`，`activeCount=1`，
  前三个状态段 `clip-path=polygon(...)`，状态条高度 `40px`。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。

### 搜索更多弹窗原生列表契约对齐

用户复核指出：`搜索更多` 弹窗形态仍像前端自造，不像 Odoo 原生
Select/Create 列表弹窗。

修复：

- 弹窗打开时先加载关系模型 `ui.contract(view_type=tree)`；
- 弹窗主体从单列候选按钮改为表格；
- 表头、读取字段、展示列来自关系模型原生 tree 契约
  `views.tree.columns_schema/columns + fields.*.string`；
- 前端只负责渲染表格、选中行、确认选择；搜索 domain 和 relation 仍使用后端
  `relation_entry/domain` 语义。

验证：

- 真实浏览器 `wutao / sc_prod_sim / project.project/771`，客户字段点击
  `搜索更多...`：
  - `dialogOpen=true`；
  - headers=`显示名称/完整名称/工作职位/电话/手机/电子邮件`；
  - `rowCount=120`；
  - `selectedCount=1`；
  - `hasSelectButton=true`。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。

### 搜索更多弹窗结构与交互继续对齐

用户复核指出：虽然弹窗已经使用关系模型 tree 契约，但结构与交互仍和原生存在差异。

修复：

- 弹窗改为原生 Select/Create 风格三段式结构：header / body / footer；
- header 使用标题 + 右上角关闭按钮；
- footer 使用 `选择 / 新建 / 取消`，并显示记录数量；
- 打开弹窗后不默认选中记录，`选择` 按钮保持 disabled；
- 点击行后选中并启用 `选择`；
- 双击行直接选择、回填 many2one 并关闭弹窗；
- `Esc` 可关闭弹窗。

验证：

- 真实浏览器 `wutao / sc_prod_sim / project.project/771`，客户字段点击
  `搜索更多...`：
  - before: `dialogOpen=true`，`rowCount=120`，`selectedCount=0`；
  - before buttons: `选择 disabled=true`，`新建 disabled=false`，
    `取消 disabled=false`；
  - `hasCloseX=true`，`countText=120 条记录`；
  - after row click: `selectedCount=1`，`选择 disabled=false`；
  - after row dblclick: `dialogOpen=false`，客户字段已回填。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。

### Relation 弹窗按钮命名边界纠偏

用户复核指出：弹窗中的 `选择/新建/取消/关闭/搜索` 等按钮文案由前端直接命名，
这是越过契约边界。

修复：

- 后端 `relation_entry` 新增 `ui_labels`，统一下发 relation 搜索入口、弹窗标题、
  搜索输入、搜索按钮、选择、新建、取消、关闭、空状态、记录数、quick create
  prompt、错误兜底等文案；
- `FormSection` 的 many2one `搜索更多...`、`快速新建...`、`新建并维护...`
  入口文案改为消费字段 schema；
- `ContractFormPage` relation 弹窗所有按钮/标题/placeholder/空状态/记录数文案
  改为消费 `relation_entry.ui_labels`；
- 前端不再为 relation 搜索弹窗自行命名交互按钮。

验证：

- Odoo shell `project.project.partner_id.relation_entry.ui_labels`：
  已返回 `search_more/dialog_title/search_placeholder/search/select/create/cancel/close/empty/record_count/...`。
- 真实浏览器 `wutao / sc_prod_sim / project.project/771`：
  `optionText=搜索更多...`，`title=客户：搜索更多`，
  `closeAria=关闭`，`placeholder=输入名称搜索`，`searchButton=搜索`，
  `countText=120 条记录`，`footerButtons=选择/新建/取消`。
- `python3 -m py_compile page_assembler.py`：`PASS`。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。

### 项目名称收藏星标对齐

用户复核指出：原生表单中的 `在仪表板上显示项目` 不应作为普通布尔字段显示，
应借鉴原生和列表页处理，在项目名称前以星标表达收藏状态。

修复：

- 表单渲染器识别原生 layout 字段节点 `widget=boolean_favorite`；
- `boolean_favorite` 不再作为普通字段独立展示；
- 同组名称字段增加星标前缀，星标 aria/title 使用后端字段 label；
- 点击星标沿用列表页即时写入 `is_favorite`、失败回滚的模式；
- 前端仅消费原生 widget 语义，不根据字段名或文案自行判断业务含义。

验证：

- Odoo shell 确认原生字段：`is_favorite widget=boolean_favorite`，
  label=`在仪表板上显示项目`，记录 `771` 初始 `is_favorite=false`。
- 真实浏览器 `wutao / sc_prod_sim / project.project/771`：
  `favoriteCount=1`，`favoriteAria=在仪表板上显示项目`，
  普通文本字段 `在仪表板上显示项目` 不再显示；
  名称字段值 `Role Smoke User` 前出现星标；
  点击后 `aria-pressed false -> true -> false`，最终数据库恢复
  `is_favorite=false`。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。

### 项目详情页结构与交互差异清单

本轮按 Odoo 原生 `project.project` form arch、后端 `ui.contract`、真实浏览器自定义页
三方对比，差异按“契约缺口优先”归因：

| 编号 | 差异 | 归因 | 状态 |
| --- | --- | --- | --- |
| D1 | 原生草稿提示 `alert alert-info` 在自定义页缺失 | parser 丢失容器静态文本，前端没有静态文本节点渲染 | 已补齐 |
| D2 | `web_ribbon`、`sc_insight_banner` widget 节点无 name/title/bg_color/显隐语义 | parser 只保留了 `type=widget`，属性未契约化 | 已补齐属性与显隐语义；当前记录按契约隐藏 |
| D3 | smart button 无 string 时显示技术 id `538` | 后端按钮 label 兜底用了 `name`，未解析 action 名称 | 已补齐，显示为 `投标管理` |
| D4 | 容器/widget 的 `invisible` 仍是原生表达式，前端无法无脑判断 | 缺少结构化 modifier 语义 | 已补齐简单 `field_compare` / `field_truthy` 契约，前端通用消费 |
| D5 | chatter 区仍以 `关注者/活动/消息` 原始字段形态进入表单渲染 | 原生 `oe_chatter` 尚未提升为专用 chatter node/renderer | 已补齐 |
| D6 | `radio`、`many2many_tags`、`many2one_avatar_user`、`daterange` 等 widget 目前降级为基础输入 | widget 表达已在字段契约中，但通用渲染器缺少对应 renderer | 已补齐 |
| D7 | button_box/stat button 视觉仍是普通按钮组，不是原生 smart button/statinfo 形态 | stat button 契约已有，但 layout 渲染未消费 stat 视觉语义 | 已补齐首批 smart button 形态 |
| D8 | `not xxx`、复合表达式等 modifiers 仍未完全结构化 | modifier parser 只覆盖当前高频简单表达式 | 已补齐首批 AST/domain 结构化 |

### 结构节点语义第一轮补齐

修复：

- parser 为容器节点保留 `text`，避免原生静态提示丢失；
- parser 为 `widget` 节点输出 `name/widget/label/attributes`；
- parser 将简单显隐表达式契约化为 `field_compare` / `field_truthy`；
- parser 对 `type=action` 且无 `string/title` 的按钮，用 `ir.actions.actions.name`
  作为 label，不再把技术 id 交给前端兜底；
- `NativeFormTreeRenderer` 增加静态文本、`web_ribbon` 与通用节点显隐消费。

验证：

- 后端 contract probe：草稿提示节点带 `text`；`web_ribbon` 带
  `field_truthy(active)`；`sc_insight_banner` 带
  `field_compare(lifecycle_state == draft)`；无空 label / 纯数字 label button。
- 真实浏览器 `wutao / sc_prod_sim / project.project/771`：
  - action labels 包含 `投标管理`；
  - `numericButtonVisible=false`；
  - `draftAlertVisible=true`；
  - `ribbonVisible=false`；
  - `insightBannerVisible=false`；
  - console errors: `0`。
- `python3 -m py_compile parsers Tree Form.py`：`PASS`。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。

### Widget Renderer 契约消费

修复：

- `FormSectionFieldSchema` 增加 `widget`，从 `views.form.layout` 字段节点或字段
  descriptor 透传到通用表单渲染器；
- `selection + widget=radio` 渲染为原生 radio 组；字段 readonly 时仍按
  widget 呈现为 disabled radio，不再被普通 readonly 文本降级；
- `many2one_avatar_user` / `many2one_avatar_employee` 由通用 many2one 控件呈现
  avatar 入口形态；
- `many2many_tags` 在 relation fallback 中按 tag 形态展示已选项，搜索占位文案
  继续走字段/schema adapter，不再写死；
- 页面层只补 `selectedRelationOptions` 数据通道，未写项目字段特例。

验证：

- 真实浏览器 `wutao / 123456 / sc_prod_sim / project.project/771`：
  - 设置页签 `privacy_visibility`：`.field--widget-radio input[type=radio] = 3`；
  - radio labels：
    `Invited internal users (private)` /
    `All internal users` /
    `Invited portal users and all internal users (public)`；
  - `radioDisabledCount=3`，readonly 状态下仍按 widget 呈现；
  - `many2many_tags` widget editor count `1`；
  - `many2one_avatar_user` avatar count `1`；
  - `native-statusbar-step=7`，`.native-chatter-block=1`，前序能力未回退；
  - console errors `0`，page errors `0`；
  - screenshot:
    `artifacts/playwright/screenshots/project_771_widget_alignment_d6.png`。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。

追加修复：

- 后端为 `widget=daterange` 输出 `fieldInfo.widget_semantics`：
  `kind=date_range/start_field/end_field`；
- 前端仅在存在 `widget_semantics.kind=date_range` 且 `end_field` 明确时渲染
  双日期输入，不自行猜测结束日期字段。

追加验证：

- Odoo shell `project.project/771` contract probe：
  `date_start widget=daterange`，
  `widget_semantics={kind: date_range, start_field: date_start, end_field: date}`，
  `widget_options={end_date_field: date, always_range: 1}`。
- 真实浏览器 `wutao / 123456 / sc_prod_sim / project.project/771`：
  `.field--widget-daterange .native-date-range = 1`；
  `input[type=date] = 2`；
  console errors `0`，page errors `0`。

### Smart Button 形态对齐

修复：

- `NativeFormTreeRenderer` 消费后端 action 契约中的 `level=smart`；
- 同时消费原生 layout 容器 `class=oe_button_box`，将其内按钮切换为
  `.native-actions--smart` / `.native-action-btn--smart`；
- smart button 仍通过原 `native-action` 事件执行，前端没有按按钮业务含义命名
  或推断目标。

验证：

- 真实浏览器 `wutao / 123456 / sc_prod_sim / project.project/771`：
  - `.native-actions--smart = 2`；
  - `.native-action-btn--smart = 9`；
  - labels 包含：
    `预算 / 合同 / 执行结构 / 工程量清单 / 预算/成本 / 物资/采购 / 结算/财务 / 投标管理`；
  - smart button `min-height=54px`；
  - `native-statusbar-step=7`，`.native-chatter-block=1`，前序能力未回退；
  - console errors `0`，page errors `0`；
  - screenshot:
    `artifacts/playwright/screenshots/project_771_smart_buttons_d7.png`。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。

### Complex Modifier 契约结构化

修复：

- 后端 modifier parser 支持 Python AST 表达式：
  `not field`、`a and b`、`a or b`、比较表达式、`in/not in`；
- 后端 attrs domain 支持 prefix domain：
  `|` / `&` / `!` 与 tuple 条件；
- 结构化输出统一为：
  `field_truthy`、`field_compare`、`not`、`all`、`any`、`static`；
- 前端 `evaluateNativeModifierValue` 只消费这些结构化 kind，不解析 XML 或原始表达式。

验证：

- Odoo shell contract probe：
  - `user_id.readonly = {kind: not, expr: field_truthy(active), raw: not active}`；
  - `date_start.required = {kind: any, exprs: [field_truthy(date_start), field_truthy(date)], raw: date_start or date}`；
  - header share button invisible 仍为 `field_compare(privacy_visibility != portal)`。
- 真实浏览器 `wutao / 123456 / sc_prod_sim / project.project/771`：
  - 设置页 `not alias_name` 生效，`电子邮件别名` 当前隐藏；
  - `radioCount=3`、`statusbarCount=7`、`chatterCount=1`，前序能力未回退；
  - screenshot:
    `artifacts/playwright/screenshots/project_771_modifier_daterange_d8.png`。
- `python3 -m py_compile parsers Tree Form.py`：`PASS`。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。

### Chatter 节点契约化

修复：

- parser 识别 `class=oe_chatter` 容器，输出 `type=chatter` 节点；
- chatter 节点保留 `label=沟通记录`、`fields=[message_follower_ids, activity_ids, message_ids]`，
  但不再把这些字段作为普通 `children` 下发表单渲染；
- `views.form.chatter` 增加同源 `label/fields/actions/features`；
- `NativeFormTreeRenderer` 增加 `chatter` slot，页面只消费
  `views.form.chatter.label/actions` 渲染沟通动作，不再自行识别 chatter 字段。

验证：

- 后端 contract probe：
  - `layout` 中 `chatter_nodes=1`；
  - chatter node `children_len=0`；
  - `raw_chatter_field_nodes=0`；
  - `views.form.chatter.label=沟通记录`；
  - `views.form.chatter.fields=message_follower_ids/activity_ids/message_ids`。
- 真实浏览器 `wutao / sc_prod_sim / project.project/771`：
  - `.native-chatter-block` 数量 `1`；
  - 标题 `沟通记录`；
  - 按钮 `发送消息 / 记录备注 / 活动`；
  - 普通表单字段 label 中不再出现 `关注者/活动/消息`；
  - console errors: `0`。
- `python3 -m py_compile parsers Tree Form.py`：`PASS`。
- `pnpm --dir frontend/apps/web run typecheck`：`PASS`。
