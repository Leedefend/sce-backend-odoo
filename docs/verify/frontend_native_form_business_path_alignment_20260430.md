# Frontend Native Form Business Path Alignment 20260430

## Scope

- Batch: `Batch-Form-Business-Path-Alignment-F1`
- Layer Target: Form View Contract + Generic Form Renderer
- Module: `addons/smart_core`, `frontend/apps/web`, `scripts/verify`
- Database: `sc_prod_sim`
- User: `wutao / 123456`
- Typical page: `project.project/771`, action `506`, menu `353`
- Native URL: `http://127.0.0.1:18069/web#id=771&model=project.project&view_type=form&action=506&menu_id=353`
- Custom URL: `http://127.0.0.1:5174/r/project.project/771?menu_id=353&action_id=506`

## Gap List

| ID | Gap | Root Cause | Status |
| --- | --- | --- | --- |
| F1 | one2many add-row label was hardcoded as `+ 新增行` in frontend. | Backend subview contract did not carry native operation labels, so frontend invented copy. | Fixed |
| F2 | Empty one2many sections did not expose native list columns. | Frontend only rendered column labels inside existing/new row controls, so an empty business subtable hid its structure. | Fixed |
| F3 | Native readonly business column `清单合计` was missing from custom form. | Parser filtered readonly x2many columns out of the contract instead of preserving them as visible readonly business columns. | Fixed |
| F4 | Form comparison script gave false pass by scanning whole page text. | Sidebars/menus polluted button text checks and tab collection missed custom native tab classes. | Fixed |

## Fixes

- Parser preserves visible x2many readonly fields in `views.form.subviews.*.tree.columns` with `surface_role=business_read` and `readonly=true`.
- Parser adds `policies.ui_labels.add_row=添加行` to x2many subviews, including fallback-inferred subviews.
- Frontend one2many fallback renderer consumes `adapter.one2manyCreateLabel()` instead of local text.
- Frontend renders stable one2many column headers from contract even when there are no rows.
- Frontend honors one2many column `readonly` by disabling controls and ignoring attempted updates.
- Added `scripts/verify/form_native_custom_gap_audit.js` as a real browser native/custom form gap gate scoped to the form surface.

## Verification

- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `python3 -m py_compile 'addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py'`: PASS
- `node --check scripts/verify/form_native_custom_gap_audit.js`: PASS
- Runtime refresh:
  - `CODEX_DB=sc_prod_sim CODEX_MODULES=smart_core CODEX_NEED_UPGRADE=1 make codex.fast`: PASS
  - `FRONTEND_PROFILE=prod-sim make frontend.restart`: PASS, frontend points to `sc_prod_sim` via `http://localhost:18069`
- Real browser native/custom gap gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 ODOO_URL=http://127.0.0.1:18069 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_native_custom_gap_audit.js`
  - artifact: `artifacts/form-native-custom-gap/20260430T093028/summary.json`
  - result: `pass=true`
  - covered surfaces: tabs, statusbar, smart buttons, header actions, chatter actions, x2many add action, x2many columns.
  - custom business path: clicking `添加行` in `投标管理` creates an inline row with `投标名称、投标轮次、招标人/业主、投标报价、清单合计、状态、投标截止时间`.
  - readonly assertion: `清单合计` is rendered in the row and disabled.

## Current Conclusion

The `project.project` form business surface is now governed by backend contract for the checked native/custom paths. The custom page no longer invents one2many labels, no longer hides empty subtable columns, and no longer drops visible readonly business columns.

This batch does not claim pixel-level parity with Odoo native form rendering. It gates contract and business-path reachability for the checked form structure and one2many add-row path.

## L4 Operation Path Addendum

追加批次继续按 target matrix 推进真实业务操作路径，覆盖 `P04/P12/P20/P23`。

新增修复：

- Existing-record save validation no longer scans untouched historical one2many rows. Only rows changed in this user operation (`isNew/dirty/removed`) participate in one2many draft validation.
- one2many draft row changes now participate in `hasChanges`, so clicking `添加行` enables the form save path.
- Native verification reloads Odoo form with a cache-buster, avoiding stale hash-route DOM during native/custom persistence comparison.

Verification:

- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `python3 -m py_compile 'addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py'`: PASS
- `node --check scripts/verify/form_native_custom_gap_audit.js`: PASS
- `node --check scripts/verify/form_business_path_acceptance.js`: PASS
- Real browser L4 operation gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 ODOO_URL=http://127.0.0.1:18069 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_business_path_acceptance.js`
  - artifact: `artifacts/form-business-path/20260430T093047/summary.json`
  - result: `pass=true`
  - `P20`: clearing required `名称` shows user-facing validation instead of raw technical error.
  - `P04/P23`: changing `名称` saves, custom reload sees the new value, native Odoo reload sees the same value, then the script reverts the name and verifies both custom/native return to `Role Smoke User`.
  - `P12/P20`: clicking one2many `添加行` enables save; saving an incomplete row shows `投标名称不能为空；状态不能为空`.
  - console errors: `0`.

Data hygiene:

- The persistence path temporarily changed `project.project/771.name` and reverted it.
- Odoo chatter tracking records containing `L4-` were removed after the run; remaining `L4-` chatter count is `0`.

Current matrix coverage after this addendum:

- `P02`: existing record read
- `P04`: edit/save lifecycle for a main form field
- `P11`: one2many empty surface
- `P12`: one2many add-row validation path
- `P13`: one2many readonly/computed columns
- `P14`: notebook/tabs
- `P15`: header/statusbar surface
- `P16`: smart/stat button surface
- `P17`: chatter action surface
- `P20`: required field and row validation friendly errors
- `P23`: persistence verified by custom reload and native Odoo reload

## P19 Body Action Safety Addendum

追加批次 `Batch-Form-Body-Action-Safety-P19` 覆盖 project form notebook/body
按钮的安全语义、危险动作确认、取消阻断、安全导航继续可达。

Contract decision:

- Form layout button action must carry backend-owned `action_safety`.
- Safe navigation actions declare `classification=safe` and do not require confirmation.
- Dangerous object/server actions declare `classification=danger`; body/row dangerous actions
  require confirmation unless a later backend contract explicitly changes that policy.
- Frontend must not infer danger from button name, method name, CSS class, or business label.
  It only consumes `action_safety`.

Verification:

- Runtime refresh:
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_DB=sc_prod_sim CODEX_MODULES=smart_core CODEX_NEED_UPGRADE=1 CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make codex.fast`: PASS
- Contract probe after refresh:
  - `工程量清单分析`: `classification=safe`, `requires_confirm=false`
  - `重建工程量清单层级`: `classification=danger`, `requires_confirm=true`
- Real browser P19 gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_body_action_safety_acceptance.js`
  - artifact: `artifacts/form-body-action-safety/20260430T235942/summary.json`
  - result: `pass=true`
  - checks: safe navigation contract, dangerous mutation guard contract, dismiss prevents
    `execute_button`, safe navigation still opens
  - console errors: `0`

Operational note:

- The first P19 attempt failed because the prod-sim Odoo runtime was still serving the old
  parser contract. After restart/upgrade, the same browser path passed. Any future parser or
  contract-field change must include runtime refresh before declaring acceptance.

## M4 P26 Field Label Localization Addendum

追加批次 `Batch-Form-M4-Localization-P26` 覆盖 M4 历史事实只读表单字段标签本地化。

Finding:

- `form_m4_legacy_readonly_acceptance` 证明 M4 表单只读和数据可见，但 artifact 中字段标签仍为
  `Document Date / Document No / Source Family / Income Category` 等英文。
- 这属于后端模型事实缺口，不属于前端翻译职责。

Fix:

- `sc.legacy.receipt.income.fact` 字段补齐中文 `string`，模型描述改为 `历史收款收入事实`。
- `form_m4_legacy_readonly_acceptance.js` 增加 `M4-P26` 字段标签中文断言。
- `form_localization_acceptance.js` 扩展 `P26-M4`，状态条用例仍只检查状态条，M4 用例检查字段标签。

Verification:

- `python3 -m py_compile addons/smart_construction_core/models/support/legacy_receipt_income_fact.py`: PASS
- `node --check scripts/verify/form_m4_legacy_readonly_acceptance.js`: PASS
- `node --check scripts/verify/form_localization_acceptance.js`: PASS
- Runtime refresh:
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_DB=sc_prod_sim CODEX_MODULES=smart_construction_core CODEX_NEED_UPGRADE=1 CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make codex.fast`: PASS
- Real browser M4 gate:
  - artifact: `artifacts/form-m4-legacy-readonly/20260501T012931/summary.json`
  - result: `pass=true`
  - checks include `legacy projection field labels are localized by backend contract`
- Real browser P26 gate:
  - artifact: `artifacts/form-localization/20260501T013238/summary.json`
  - result: `pass=true`
  - covered paths: `P26-M1/P26-M2/P26-M3/P26-M4`

Data hygiene:

- This batch is read-only. It changes metadata and performs browser/API reads only; no business records are created or mutated.

## M4 Readonly Mutation Policy Addendum

追加批次 `Batch-Form-M4-Readonly-Mutation-Policy` 覆盖 M4 历史事实只读投影的后端执行边界。

Finding:

- M4 页面已经通过 `create=0/edit=0` 和前端只读渲染阻止普通页面编辑，但这不足以证明真实用户无法通过公开数据办理接口写入历史事实。
- `api.data` 的 `create/write` 路径在本批前直接进入 ORM，未读取只读投影策略。

Fix:

- `smart_core.api.data` 在 `create/write` 进入 ORM 前调用
  `smart_core_api_data_mutation_policy`。
- `smart_construction_core` 对 `sc.legacy.receipt.income.fact` 声明 `create/write`
  禁止，返回 `READONLY_PROJECTION_MUTATION_DENIED`。
- 前端不新增任何只读模型判断；仍只按后端表单契约渲染。

Verification:

- `python3 -m py_compile addons/smart_core/handlers/api_data.py addons/smart_core/handlers/reason_codes.py addons/smart_core/utils/reason_codes.py addons/smart_construction_core/core_extension.py addons/smart_construction_core/__init__.py`: PASS
- `node --check scripts/verify/form_m4_legacy_readonly_acceptance.js`: PASS
- Runtime refresh:
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_DB=sc_prod_sim CODEX_MODULES=smart_core,smart_construction_core CODEX_NEED_UPGRADE=1 CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make codex.fast`: PASS
- Real browser M4 gate:
  - artifact: `artifacts/form-m4-legacy-readonly/20260501T014935/summary.json`
  - result: `pass=true`
  - checks include `api.data create/write is denied by backend readonly projection policy`
  - create/write reason code: `READONLY_PROJECTION_MUTATION_DENIED`
  - policy source: `smart_construction_core`
  - console errors: `0`
- `git diff --check`: PASS

Conclusion:

- 本批结论不是仅说明本次页面成功，而是补齐了只读投影模型在公开数据写入口的后端兜底策略。
- 后续历史承载模型若升级为系统业务模型，必须显式复核该模型的 mutation policy，明确从只读投影切换为业务模型后的 `create/write` 允许边界与验收脚本更新。

## L6 Readonly Projection Evidence Addendum

追加批次 `Batch-Form-L6-Readonly-Projection-Evidence` 修正 M2-M5 通用回归脚本对 M4 只读投影的 surface 判定。

Finding:

- M4 专项 gate 已证明历史事实可见、只读、刷新/深链恢复可用。
- L6 通用脚本旧口径只把 input、readonly class、statusbar、o2m 计为 renderable surface；
  当前 M4 投影是文本化业务事实渲染，artifact 已包含完整历史字段和值，但旧脚本误判 `hasRenderableSurface=false`。

Fix:

- `form_model_tier_acceptance.js` 在后端契约声明 `read=true/create!=true/write!=true`
  时，允许以模型业务标题和足量业务事实文本作为只读投影 surface 证据。
- `form_model_error_recovery_acceptance.js` 的 P25 reload/deep-link 判定同步补齐该只读投影文本 evidence。

Verification:

- Failure baseline:
  - `artifacts/form-model-tier/20260501T015238/summary.json`: M4 false fail.
  - `artifacts/form-model-error-recovery/20260501T015238/summary.json`: M4 P25 false fail.
- Passing gates:
  - `artifacts/form-native-custom-gap/20260501T015209/summary.json`: PASS.
  - `artifacts/form-model-tier/20260501T015815/summary.json`: PASS.
  - `artifacts/form-model-error-recovery/20260501T020124/summary.json`: PASS.
- `node --check scripts/verify/form_model_tier_acceptance.js && node --check scripts/verify/form_model_error_recovery_acceptance.js`: PASS.

Conclusion:

- L6 现在能区分“编辑型表单 surface”和“只读投影业务事实 surface”，不会把真实可用的 M4 页面误判为不可渲染。
- 该修正不放宽业务页面标准：只读投影必须同时满足后端只读契约、页面无错误、模型业务标题可见、业务事实文本可见。

## P16 Smart Button Overflow Addendum

追加批次 `Batch-Form-Smart-Button-Overflow-F43` 收口 `P16` overflow/more 形态。此前已有 smart button 导航证据，但原生页面在项目详情页 smart button box 中使用 `更多` 承载溢出入口，自定义页把所有入口直接平铺，结构形态仍有差异。

修复：

- `NativeFormTreeRenderer` 对后端 layout/action 契约声明的 smart button group 增加通用 overflow 渲染。
- 前 4 个 smart button 直显，其余入口进入 `更多` 菜单。
- 前端不新增业务命名或权限判断；菜单项 label/action 仍来自后端契约。

Verification:

- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `FRONTEND_PROFILE=prod-sim make frontend.restart`: PASS
- `node --check scripts/verify/form_smart_button_overflow_acceptance.js`: PASS
- Real browser P16 overflow gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 ODOO_URL=http://127.0.0.1:18069 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_smart_button_overflow_acceptance.js`
  - artifact: `artifacts/form-smart-button-overflow/20260430T231612/summary.json`
  - result: `pass=true`
  - native direct: `执行结构/工程量清单/预算/成本/合同/更多`
  - native overflow: `物资/采购/结算/财务/0投标`
  - custom direct: `执行结构/工程量清单/预算/成本/合同/更多`
  - custom overflow: `物资/采购/结算/财务/投标管理`
  - native/custom console errors: `0`

Data hygiene:

- 本批只读打开原生与自定义页面并点击 `更多`，无业务数据写入。

## L4 Chatter Note Addendum

追加批次 `Batch-Form-Chatter-Note-F39` 覆盖 `P17 log note`，仍以
`project.project/771` 为典型页。

新增验收：

- 新增 `scripts/verify/form_chatter_note_acceptance.js`，真实浏览器登录
  `wutao/123456`，打开 prod-sim 项目详情页。
- chatter actions 为 `发送消息/记录备注/活动`，且 `记录备注` enabled。
- 点击 `记录备注`，输入唯一正文 `P17 note acceptance ...` 并提交。
- 页面时间线回显该正文，无 console/page error。

Verification:

- `node --check scripts/verify/form_chatter_note_acceptance.js`: PASS
- Real browser gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_chatter_note_acceptance.js`
  - artifact: `artifacts/form-chatter-note/20260430T223635/summary.json`
  - result: `pass=true`
  - matching timeline row `type=备注`
  - console errors: `0`
- Database subtype probe:
  - Makefile Odoo shell on `sc_prod_sim`
  - matching `mail.message.subtype_id` XMLID: `mail.mt_note`

Data hygiene:

- The gate wrote `mail.message` records with body prefix `P17 note acceptance`.
- Post-cleanup probe deleted all matching acceptance rows with explicit commit and confirmed
  `remaining_note_acceptance_messages=0`.

Display-label contract closure:

- `chatter.timeline` now resolves `mail.mt_note` in the backend and returns
  `typeLabel=备注` plus `subtype=mail.mt_note`.
- Normal comments continue to return `typeLabel=评论`; frontend only renders the
  backend label and does not infer note/comment semantics from subtype or from
  the clicked button.

## P25 Navigation Recovery Addendum

追加批次 `Batch-Form-Navigation-Recovery-F40` 覆盖 M1 项目详情页 P25
刷新、浏览器历史与未登录深链恢复，仍以 `project.project/771` 为典型页。

新增验收：

- 新增 `scripts/verify/form_navigation_recovery_acceptance.js`。
- 已登录状态打开项目详情页后刷新页面，URL 保持
  `/r/project.project/771?menu_id=353&action_id=506`，状态条与输入控件恢复。
- 从 `/a/506?menu_id=353` 项目台账进入详情页后，浏览器 Back 回列表、
  Forward 回详情页，两侧均重新渲染成功。
- 未登录新上下文直接访问详情页深链时，路由进入
  `/login?redirect=...`；提交登录后回到原详情页深链。

Verification:

- `node --check scripts/verify/form_navigation_recovery_acceptance.js`: PASS
- Real browser P25 gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_navigation_recovery_acceptance.js`
  - artifact: `artifacts/form-navigation-recovery/20260430T224314/summary.json`
  - result: `pass=true`
  - scenarios: `record_form_reload`, `browser_back_forward`,
    `unauthenticated_deep_link_login_return`
  - console errors: `0`

Data hygiene:

- This gate is read-only. It does not save, create, unlink, or mutate business data.

## P15 Status Transition Addendum

追加批次 `Batch-Form-Status-Transition-F41` 覆盖 M1 项目详情页 P15 的安全状态推进路径。

新增修复：

- Statusbar 字段由后端 `views.form.statusbar.field` 契约声明，不属于普通字段 layout。
- 前端此前点击状态条会更新 `formData` 并标记 dirty，但 `hasChanges` 与
  `collectWritableValues()` 只统计普通 layout 字段，导致保存按钮不启用。
- 修复后，契约声明的 statusbar 字段在可写时参与变更判断与保存 payload；
  前端仍不按 `project.project`、`lifecycle_state` 或具体状态值做业务判断。

Verification:

- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_status_transition_acceptance.js`: PASS
- `FRONTEND_PROFILE=prod-sim make frontend.restart`: PASS
- Real browser P15 gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_status_transition_acceptance.js`
  - artifact: `artifacts/form-status-transition/20260430T225703/summary.json`
  - result: `pass=true`
  - scenario: `statusbar_safe_transition_draft_to_paused`
  - console errors: `0`

Data hygiene:

- The gate created temporary projects with prefix `P15 Status Acceptance`.
- Post-cleanup removed failed-run and passing-run projects `881/882/883/884`,
  related `mail.message` rows and `mail.alias` rows.
- Cleanup probe: `remaining_p15_status_projects=0`.

## P04 Discard Unsaved Edit Addendum

追加批次 `Batch-Form-Edit-Discard-F33` 关闭普通编辑页的放弃未保存改动路径。此前 P04 已有多批保存、刷新、读库证据，但没有用户误改后“不落库恢复”的独立证据。

Contract fix:

- Backend `PageAssembler` now injects `views.form.ui_labels` with `save/saving/discard/reload/save_success`.
- `ContractFormPage` renders the ordinary discard action only when an existing record has unsaved changes.
- The discard button label comes from `views.form.ui_labels.discard`; the frontend does not name this action itself.
- Discard executes the existing `reload()` path, clearing dirty state and reloading the backend record.

Verification:

- `python3 -m py_compile addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- Runtime refresh:
  - prod-sim Odoo restart through Makefile: PASS
  - prod-sim frontend restart through Makefile: PASS
- Real browser discard gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_edit_discard_acceptance.js`
  - artifact: `artifacts/form-edit-discard/20260430T215910/summary.json`
  - result: `pass=true`
  - console errors: `0`

Observed behavior:

- Before edit: `project.project/771.name = Role Smoke User`
- User edits `名称` to `P04 discard should not persist ...`
- Header shows enabled `保存` and enabled `放弃`
- After clicking `放弃`, input returns to `Role Smoke User`; header no longer shows `放弃`; read-back from `api.data` is still `Role Smoke User`

Data hygiene:

- No save was executed in this gate. The temporary edited value was browser state only and did not persist.

## P07 Quick Input Edge Addendum

追加批次 `Batch-Form-Relation-Quick-Input-Edge-F34` 补齐 many2one 快速输入边界。此前 P07 已证明单匹配 `Project User` 可按契约 `single_contains_or_exact` 回填 `Demo Project User`，本轮继续覆盖多匹配和清空。

Coverage:

- Multiple match:
  - Backend `api.data` confirms keyword `公司` returns multiple `res.partner` records.
  - Browser types `公司` in the `客户` many2one input and presses Enter.
  - Custom form opens `客户：搜索更多` instead of guessing one record.
  - Dialog headers are `名称/完整名称/工作职位/电话/手机/电子邮件`; select is disabled before row selection.
- Clear:
  - Browser clears `项目管理员 = Demo Project User`.
  - Header shows enabled `保存` and enabled `放弃`.
  - Browser clicks `放弃`; input restores to `Demo Project User`.
  - Backend read confirms `project.project/771.user_id` remains `[109, "Demo Project User"]`.

Verification:

- `node --check scripts/verify/form_relation_quick_input_edge_acceptance.js`: PASS
- Real browser relation quick-input edge gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_relation_quick_input_edge_acceptance.js`
  - artifact: `artifacts/form-relation-quick-input-edge/20260430T220443/summary.json`
  - result: `pass=true`
  - console errors: `0`

Data hygiene:

- No save was executed. The clear path was explicitly discarded and backend `user_id` stayed unchanged.

## P08 Dialog Create-And-Edit Addendum

追加批次 `Batch-Form-Relation-Dialog-Create-F35` 补齐 `搜索更多` 弹窗内的 `新建` 入口。此前 P08 已覆盖 cancel/select，但弹窗 footer 的 create-and-edit 路径没有独立证据。

Gap and fix:

- Gap: relation dialog `新建` was coupled to `keyword`; with empty search input it showed missing-name behavior and did not navigate to the maintenance form.
- Fix: `ContractFormPage.createRelationFromSearchDialog` now branches by backend contract `relation_entry.create_mode`.
- `create_mode=page`: open the relation maintenance form directly, with return parameters.
- `create_mode=quick`: still requires a non-empty label before quick-create.

Verification:

- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_relation_dialog_create_entry_acceptance.js`: PASS
- Runtime refresh: prod-sim frontend restart through Makefile PASS
- Real browser dialog create gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_relation_dialog_create_entry_acceptance.js`
  - artifact: `artifacts/form-relation-dialog-create-entry/20260430T220856/summary.json`
  - result: `pass=true`
  - console errors: `0`

Observed behavior:

- `客户：搜索更多` dialog renders headers `名称/完整名称/工作职位/电话/手机/电子邮件`.
- Footer renders `选择` disabled, `新建` enabled, `取消` enabled.
- Clicking `新建` opens `/f/res.partner/new?action_id=314&view_mode=form`.
- Return query is complete: `return_field=partner_id`, `return_model=project.project`, `return_action_id=506`, `return_menu_id=353`.
- The create form shows `名称` and `保存`; technical audit fields are absent.

Data hygiene:

- No partner was saved. The gate only verifies route/surface reachability.

## P09 Deferred Relation Create Addendum

追加批次 `Batch-Form-Relation-Deferred-Create-F36` 关闭 no-match many2one 由主表单保存触发创建的完整路径。此前 P09 只证明输入无匹配值不会立即创建关联记录，本轮补齐保存时创建、主记录关联和清理。

Coverage:

- Browser opens `project.project/771`.
- User types a unique no-match customer label `P09 Deferred Partner ...` in the `客户` many2one input.
- Inline hint displays `保存时创建“...”`.
- Backend `res.partner` exact-name query remains empty before save.
- User clicks main form `保存`.
- Backend creates exactly one `res.partner`, and `project.project/771.partner_id` points to that record.
- Cleanup restores project `partner_id` and deletes the temporary partner through `api.data.unlink`.

Verification:

- `node --check scripts/verify/form_relation_deferred_create_save_acceptance.js`: PASS
- Real browser deferred-create gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_relation_deferred_create_save_acceptance.js`
  - artifact: `artifacts/form-relation-deferred-create-save/20260430T222029/summary.json`
  - result: `pass=true`
  - console errors: `0`

Data hygiene:

- `project.project/771.partner_id` restored to `false`.
- Temporary `res.partner/8070` deleted through delete policy `DELETE_POLICY_ALLOWED`.
- `remaining_partners=[]`.

## P10 Many2many Multi-Select Addendum

追加批次 `Batch-Form-Many2many-Multi-Select-F37` 补齐 many2many 一次选择多个记录的真实浏览器证据。此前 P10 已覆盖单个 tag 选择、保存、刷新、移除；本轮补齐 `select multiple`。

Coverage:

- Backend creates two temporary `project.tags`.
- Browser opens `project.project/771`.
- User selects both tag options in the many2many `标签` control in one operation.
- User saves and reloads the form.
- Page shows both tags; backend read confirms `project.project/771.tag_ids` contains both ids.
- Browser clears back to the original tag set and saves.
- Page and backend read no longer include the temporary tags.

Verification:

- `node --check scripts/verify/form_many2many_multi_select_acceptance.js`: PASS
- Real browser many2many multi-select gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_many2many_multi_select_acceptance.js`
  - artifact: `artifacts/form-many2many-multi-select/20260430T222310/summary.json`
  - result: `pass=true`
  - console errors: `0`

Data hygiene:

- Project tags restored to the original empty set.
- Temporary `project.tags/6` and `project.tags/7` deleted through delete policy `RELATION_MAINTENANCE_DELETE_ALLOWED`.
- `project_tags_after_cleanup=[]`.

## P18 Attachment Delete Policy Addendum

追加批次 `Batch-Form-Attachment-Delete-Policy-F38` 补齐附件删除策略证据。此前 P18 已覆盖上传、列表回显、下载和内容一致性；本轮补齐删除 allowed/denied 的明确契约与浏览器证据。

Contract fix:

- Backend form contract now injects `views.form.attachments.delete`.
- For current policy, `model=ir.attachment`, `intent=api.data.unlink`, `enabled=false`.
- `delete_policy.reason_code=DELETE_POLICY_DENIED`, source `delete_policy_default_denied`.
- Frontend does not infer attachment deletion capability. Since contract says disabled, no delete button is rendered.

Verification:

- `python3 -m py_compile addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`: PASS
- `node --check scripts/verify/form_attachment_delete_policy_acceptance.js`: PASS
- Runtime refresh: prod-sim Odoo restart through Makefile PASS
- Real browser attachment delete-policy gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_attachment_delete_policy_acceptance.js`
  - artifact: `artifacts/form-attachment-delete-policy/20260430T222818/summary.json`
  - result: `pass=true`
  - console errors: `0`

Observed behavior:

- Attachment upload block is visible.
- `.native-attachment-delete` count is `0`.
- `api.data.unlink` dry-run for `ir.attachment` returns `403` with `DELETE_POLICY_DENIED`.

Data hygiene:

- Dry-run only. No attachment or business record was created or deleted.

## P03 Create Entry Addendum

追加批次 `Batch-Form-Create-Entry-F32` 收口 create surface 入口。本轮只验证创建页入口、默认创建 surface、return 参数和技术字段收敛，不保存新业务记录。

Coverage:

- Project list create: clicking `新建` on `/a/506?menu_id=353` opens `/f/project.project/new?menu_id=353`.
- Project create surface: save action is visible; business labels include `名称/任务名称/客户/标签/项目管理员/安排的日期/投标记录`; `名称` is required; technical labels `ID/创建人/创建时间/最后更新人/最后更新时间` are absent.
- Relation create-and-edit: clicking `客户 -> 新建并维护` on `project.project/771` opens `/f/res.partner/new?action_id=314&view_mode=form` with `return_field=partner_id`, `return_model=project.project`, `return_action_id=506`, and `return_menu_id=353`.
- Partner relation create surface: save action and `名称` field are visible; technical labels are absent. Independent Odoo shell confirms `env['res.partner']._fields['name'].required == False`, so no required marker is expected on this relation create surface.

Verification:

- `node --check scripts/verify/form_create_entry_acceptance.js`: PASS
- Odoo shell fact probe through `make odoo.shell.exec`: PASS, `res_partner_name_required=False`
- Real browser create-entry gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_create_entry_acceptance.js`
  - artifact: `artifacts/form-create-entry/20260430T215301/summary.json`
  - result: `pass=true`
  - console errors: `0`

Data hygiene:

- No create form was saved. This batch does not insert `project.project` or `res.partner` records.

Current matrix coverage after this addendum:

- `P01`: menu/action list route, direct record route, list row route, smart button route, relation search-more dialog route
- `P02`: existing record read
- `P03`: list create route and many2one create-and-edit route surfaces
- `P04`: edit/save lifecycle for a main form field
- `P07`: many2one quick input with contract-owned match semantics
- `P08`: many2one search-more cancel/select
- `P09`: no-match deferred relation create does not create before main save
- `P10`: many2many select/remove/save/reload
- `P11`: one2many empty surface
- `P12`: one2many add-row validation path
- `P13`: one2many readonly/computed columns
- `P14`: notebook/tabs
- `P15`: header/statusbar surface
- `P16`: smart/stat button surface
- `P17`: chatter action surface
- `P20`: required field and row validation friendly errors
- `P23`: persistence verified by custom reload and native Odoo reload

## P01 Entry Routing Addendum

追加批次 `Batch-Form-Entry-Routing-F31` 收口 `P01`。本轮不新增业务能力，只补齐真实入口可达性证据，确保自定义前端的动作入口、记录入口、smart button 和关系弹窗不会把用户带到错误 surface。

Coverage:

- Direct record route: `/r/project.project/771?menu_id=353&action_id=506` renders the project form shell and native statusbar.
- Action list route: `/a/506?menu_id=353` renders the project ledger list with 80 rows.
- List row route: clicking the first project row opens `/r/project.project/514?menu_id=353&action_id=506` with the form shell and statusbar.
- Smart button route: clicking `投标管理` on project `771` navigates to `/a/538?menu_id=358&action_id=538`.
- Relation dialog route: `项目管理员：搜索更多` loads relation table headers `名称/登录/语言/最新认证/状态`; row select enables `选择`, fills the many2one input, and closes the dialog.

Verification:

- `node --check scripts/verify/form_entry_routing_acceptance.js`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- Real browser route gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_entry_routing_acceptance.js`
  - artifact: `artifacts/form-entry-routing/20260430T214815/summary.json`
  - result: `pass=true`
  - console errors: `0`

Data hygiene:

- This gate is read-only for persisted data. The relation dialog select updates only the unsaved browser form state; the script reopens `project.project/771` at the end and does not call save.

Current matrix coverage after this addendum:

- `P01`: menu/action list route, direct record route, list row route, smart button route, relation search-more dialog route
- `P02`: existing record read
- `P04`: edit/save lifecycle for a main form field
- `P07`: many2one quick input with contract-owned match semantics
- `P08`: many2one search-more cancel/select
- `P09`: no-match deferred relation create does not create before main save
- `P10`: many2many select/remove/save/reload
- `P11`: one2many empty surface
- `P12`: one2many add-row validation path
- `P13`: one2many readonly/computed columns
- `P14`: notebook/tabs
- `P15`: header/statusbar surface
- `P16`: smart/stat button surface
- `P17`: chatter action surface
- `P20`: required field and row validation friendly errors
- `P23`: persistence verified by custom reload and native Odoo reload

## P06 Primitive Field Addendum B

追加批次 `Batch-Form-Primitive-Fields-F28` 继续补齐原始字段类型验收，样本切换为
`project.cost.ledger`，避免在项目主表上制造不可控业务状态。

新增验收：

- `scripts/verify/form_primitive_numeric_date_acceptance.js`
- artifact: `artifacts/form-primitive-numeric-date/20260430T190139/summary.json`
- result: `pass=true`

覆盖结论：

- `发生日期` 按契约渲染为 `input[type=date]`。
- `数量` 与 `金额` 按契约渲染为 `input[type=number]`。
- 浏览器编辑 `发生日期=2099-10-11`、`数量=2.75`、`金额=166.88` 后保存成功。
- `api.data` 读库与刷新重开页面均确认保存值一致，覆盖 `P06/P04/P23`。
- `备注/摘要` 在该模型中为 `Char`，只作为同表单普通输入回归，不声明关闭 Odoo `text`
  或 `html` 字段。

数据卫生：

- 本轮 fixture `project.cost.ledger/2`、`project.cost.period/4`、
  `project.cost.code/4` 已通过 Makefile Odoo shell 删除。
- 成本台账保存时由模型重算生成的自动期间 `project.cost.period/5` 已确认无台账引用后删除。
- 公开删除被 `DELETE_POLICY_DENIED` 拒绝为预期策略，不计入 actionable console error。
- 更早失败尝试留下的 `P06B%` 成本科目/期间残留已补做宽域清理，并显式
  `env.cr.commit()` 后独立确认 remaining 为 `[]`。

剩余边界：

- `text/html/datetime` 仍未关闭，需要后续选择真实安全样本单独验收。

## P06 Primitive Field Addendum C

追加批次 `Batch-Form-Primitive-Fields-F29` 继续补齐原始字段类型验收，样本切换为
`sc.construction.diary`。

新增修复：

- `FormSection` 不再把 `text/html` 字段渲染成单行 input。
- 前端仍只消费字段类型契约；当字段类型为 `text/html` 时，通用控件形态为
  `textarea`，不加入模型名或字段名特判。

新增验收：

- `scripts/verify/form_primitive_text_datetime_acceptance.js`
- artifact: `artifacts/form-primitive-text-datetime/20260430T212650/summary.json`
- result: `pass=true`

覆盖结论：

- `日志日期` 按契约渲染为 `input[type=datetime-local]`。
- `日志内容`、`单据说明`、`备注` 按契约渲染为 `textarea`。
- 浏览器编辑 `日志日期=2099-11-12T09:35` 和三处文本字段后保存成功。
- `api.data` 读库确认 `date_diary=2099-11-12 09:35:00`，三处文本字段持久化。
- 刷新重开页面后，datetime input 与 textarea 均显示保存后的值，覆盖 `P06/P04/P23`。

数据卫生：

- 本轮 fixture `sc.construction.diary/5665` 已通过 Makefile Odoo shell 删除并显式
  `env.cr.commit()`。
- 独立确认 `document_no=P06C-1777584411125` remaining 为 `[]`。
- 公开删除被 `DELETE_POLICY_DENIED` 拒绝为预期策略，不计入 actionable console error。

剩余边界：

- `html` 尚未在当前业务模型中找到安全可写且原生 form 可见的样本，保留后续专项。

## P06 Primitive Field Addendum D

追加批次 `Batch-Form-Primitive-Fields-F30` 关闭最后一个原始字段类型 `html`。

新增验收：

- `scripts/verify/form_primitive_html_acceptance.js`
- artifact: `artifacts/form-primitive-html/20260430T213742/summary.json`
- result: `pass=true`

覆盖结论：

- 样本字段为 `project.project/771.description`，字段类型为 Odoo `html`。
- 该字段位于项目详情页 notebook 的 `描述` 页签内；真实浏览器先切换页签，再按契约找到
  `描述` 控件。
- `描述` 按通用字段类型契约渲染为 `textarea`。
- 浏览器写入包含 `<p>`、`<ol>`、`<strong>` 的 HTML 内容后保存成功。
- `api.data` 读库确认 HTML 标签持久化；刷新重开并再次切换 `描述` 页签后，textarea 显示值与读库一致。

数据卫生：

- 验收前 `project.project/771.description` 为空。
- 脚本 finally 通过 `api.data` 恢复原值，artifact 显示 `restored=true`。
- Makefile Odoo shell 独立确认 `description=''` 且不含 `P06D edited project html`。

P06 收口：

- `char/integer/selection/boolean/date/float/monetary/datetime/text/html` 均已有真实浏览器控件形态、
  保存、刷新和读库证据。
- P06 primitive field widget matrix 本轮关闭。

## M4 Legacy Readonly Addendum

追加批次 `Batch-Form-M4-Legacy-Readonly-F25` 覆盖历史事实投影表单的只读契约闭环。

新增修复：

- Form parser 解析原生 form 根节点 `create/edit/delete`，输出
  `views.form.capabilities.can_create/can_write/can_delete`。
- `app.view.config` 与 governed contract 白名单正式保留 form `capabilities`，避免解析器产出在
  unwrap/sanitize 阶段被丢弃。
- Contract governance 根据 `views.form.capabilities` 下调
  `permissions.effective.rights.create/write/unlink` 与 head permissions，并在无 create/write
  权限时输出 `render_profile=readonly`。
- 前端继续只消费权限和 render profile 契约，不按历史模型名写特判。

Verification:

- `python3 -m py_compile 'addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py' addons/smart_core/utils/contract_governance.py addons/smart_core/app_config_engine/models/contract_mixin.py addons/smart_core/app_config_engine/models/app_view_config.py`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_m4_legacy_readonly_acceptance.js`: PASS
- Runtime refresh:
  - prod-sim Odoo `make restart`: PASS
  - prod-sim frontend `make frontend.restart`: PASS
- Real browser M4 readonly gate:
  - artifact: `artifacts/form-m4-legacy-readonly/20260430T155818/summary.json`
  - result: `pass=true`
  - `P02/P23`: persisted facts are visible for `sc.legacy.receipt.income.fact/7220`.
  - `P05`: custom renderer exposes no enabled edit/save workflow.
  - `P25`: reload and direct deep link recovery remain readonly and populated.
  - direct create route does not expose an enabled create workflow.
  - console errors: `0`.

## P24 Concurrency Conflict Addendum

追加批次 `Batch-Form-Concurrency-F26` 收口 `P24`。上一轮只验证 M2-M5 form edit
契约包含 `record_version`，本轮补齐真实浏览器 stale-save 行为。

新增验收：

- 新增 `scripts/verify/form_concurrency_conflict_acceptance.js`。
- 脚本创建一条可清理的 M5 `sc.dictionary` 临时记录，两个浏览器上下文分别打开同一记录。
- 第二页先修改 `名称` 并保存成功；第一页保留旧 `record_version` token，再修改 `名称` 并保存。
- 预期第一页保存被后端 `if_match/write_date` 策略拒绝，页面显示友好冲突提示，数据库仍保持第二页保存结果。

Verification:

- `node --check scripts/verify/form_concurrency_conflict_acceptance.js`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- Real browser P24 gate:
  - artifact: `artifacts/form-concurrency-conflict/20260430T171005/summary.json`
  - result: `pass=true`
  - stale feedback includes `数据已被其他操作更新，请重新加载后再保存。`
  - stale write did not overwrite the second tab value.
  - `actionable_console_errors=0`

Data hygiene:

- Public `api.data.unlink` for `sc.dictionary` remains denied by delete policy in this scenario.
- The fixture `sc.dictionary/14` was removed through Makefile Odoo shell; cleanup confirmed `remaining=[]`.

### P24 Recovery Follow-up

追加批次 `Batch-Form-Concurrency-Recovery-F42` 补齐冲突后的恢复路径。

新增验收：

- `scripts/verify/form_concurrency_conflict_acceptance.js` 现在要求两步通过：
  - stale save 被拒绝，页面显示友好冲突提示，且读库确认未覆盖第二页结果。
  - stale 页点击 `放弃` 后重新加载最新值，再修改并保存成功。
- 该路径验证用户不会被困在冲突错误态，可以通过契约声明的 `放弃/reload`
  恢复到后端最新版本，再继续办理。

Verification:

- `node --check scripts/verify/form_concurrency_conflict_acceptance.js`: PASS
- Real browser P24 gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 ACTION_ID=619 node scripts/verify/form_concurrency_conflict_acceptance.js`
  - artifact: `artifacts/form-concurrency-conflict/20260430T230226/summary.json`
  - result: `pass=true`
  - checks: `two browser tabs stale save is rejected with friendly conflict feedback`,
    `stale form can discard, reload latest value, and save again`
  - actionable console errors: `0`

Data hygiene:

- The passing fixture `sc.dictionary/18` was removed through Makefile Odoo shell.
- Earlier failed-run leftovers `13/14/17` were also removed.
- Cleanup probe: `remaining_p24_dictionary=0`.

## P06 Primitive Field Addendum A

追加批次 `Batch-Form-Primitive-Fields-F27A` 收口 P06 的首批安全可写基础字段。
本批不强行触碰交易单据字段，只覆盖可创建、可清理的 M5 配置维护记录，以及可恢复的 M1
项目布尔星标。

新增验收：

- 新增 `scripts/verify/form_primitive_fields_acceptance.js`。
- `sc.dictionary` 创建页验证：
  - `名称` / `编码`: char 输入。
  - `排序`: integer number 输入。
  - `字典类型`: selection select，option label 来自后端契约。
- 浏览器创建临时记录并读库确认 `name/code/type/sequence`。
- 浏览器编辑同一记录，刷新后确认表单显示值与读库一致。
- `project.project/771` 验证 `is_favorite` 布尔 favorite widget：点击后读库确认布尔值变化，再点击恢复原值。

Verification:

- `node --check scripts/verify/form_primitive_fields_acceptance.js`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- Real browser P06-A gate:
  - artifact: `artifacts/form-primitive-fields/20260430T171818/summary.json`
  - result: `pass=true`
  - `char/integer/selection/boolean` checks all pass.
  - `actionable_console_errors=0`

Data hygiene:

- Public `api.data.unlink` for `sc.dictionary` remains denied by delete policy in this scenario.
- The fixture `sc.dictionary/16` was removed through Makefile Odoo shell; cleanup confirmed `remaining=[]`.
- `project.project/771.is_favorite` was restored to its initial value by the script.

Boundary:

- This is P06 batch A only. `text/html/float/monetary/date/datetime` remain open for follow-up
  batches on safe M2/M3/M4 specimens.

## P27 Accessibility Addendum

追加批次 `Batch-Form-Accessibility-F21` 覆盖 `P27`，仍以 `project.project/771`
为典型页。

新增修复：

- 关系搜索弹窗打开后焦点进入弹窗搜索输入框。
- 弹窗打开期间增加 document-level Escape 监听，确保焦点仍停留在触发按钮或页面其他位置时，
  Escape 也能关闭当前弹窗。
- 该修复只处理通用控件可达性，不增加前端业务判断。

Verification:

- `node --check scripts/verify/form_accessibility_acceptance.js`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- Runtime refresh:
  - `FRONTEND_PROFILE=prod-sim make frontend.restart`: PASS
- Real browser P27 gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_accessibility_acceptance.js`
  - artifact: `artifacts/form-accessibility/20260430T140647/summary.json`
  - result: `pass=true`
  - covered scenarios:
    `named_control_semantics`,
    `keyboard_tab_reaches_critical_controls`,
    `relation_dialog_escape_close_select_semantics`,
    `chatter_activity_composer_disabled_semantics`.
  - console errors: `0`.

Current matrix coverage after this addendum:

- `P27`: keyboard focus reaches critical controls, relation dialog Escape/close/select semantics work,
  and chatter activity composer disabled/enabled semantics are browser-proven.

## P28 Visual Containment Addendum

追加批次 `Batch-Form-Visual-Containment-F22` 覆盖 `P28`，仍以
`project.project/771` 为典型页。

新增验收：

- 新增 `scripts/verify/form_visual_containment_acceptance.js`。
- 脚本真实登录 `wutao`，分别用 desktop/tablet/mobile 三套 viewport 打开项目表单、
  关系搜索弹窗，并保存截图。
- DOM 规则检查：
  - 页面无视口级横向溢出。
  - 关键控件无自身文本裁剪、无无效尺寸、无异常重叠。
  - 关系弹窗保持在当前 viewport 内。
  - 状态条和关系表格按允许横向滚动容器处理，不误判为裁剪。

Verification:

- `node --check scripts/verify/form_visual_containment_acceptance.js`: PASS
- Real browser P28 gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_visual_containment_acceptance.js`
  - artifact: `artifacts/form-visual-containment/20260430T141142/summary.json`
  - result: `pass=true`
  - viewports: `desktop 1440x980`, `tablet 900x1180`, `mobile 390x844`
  - screenshots: `desktop_form.png`, `desktop_relation_dialog.png`,
    `tablet_form.png`, `tablet_relation_dialog.png`,
    `mobile_form.png`, `mobile_relation_dialog.png`.

Current matrix coverage after this addendum:

- `P28`: desktop/tablet/mobile visual containment for the project form and relation search dialog
  is browser-proven.

## M3 Purchase Order Line Lifecycle Addendum

追加批次 `Batch-Form-M3-Purchase-Order-Line-F23` 覆盖 M3
`purchase.order` one2many 明细真实办理路径。

新增修复：

- Generic `api.data` 写入运行时为 one2many 新增子记录补齐后端事实：
  父记录 inverse、`company_id/currency_id/partner_id`、`date_planned`，以及
  根据 `product_id` 补齐 `product_uom`。
- `ContractFormPage` 编辑态只提交脏字段；one2many 已有行改为字段级脏提交，
  避免编辑数量/单价时把未编辑的产品或描述占位值写回。
- 非创建态必填校验只检查本次 payload 中包含的字段，创建态仍完整校验必填字段。

Verification:

- `python3 -m py_compile addons/smart_core/handlers/api_data.py`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_m3_purchase_order_line_acceptance.js`: PASS
- Runtime refresh:
  - prod-sim Odoo `make restart`: PASS
  - prod-sim frontend `make frontend.restart`: PASS
- Real browser M3 line gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=caisiqi E2E_PASSWORD=123456 PRODUCT_ID=1 node scripts/verify/form_m3_purchase_order_line_acceptance.js`
  - artifact: `artifacts/form-m3-purchase-order-line/20260430T144957/summary.json`
  - result: `pass=true`
  - covered paths:
    `P12` add/edit/remove row,
    `P13` readonly `小计` column present,
    `P20` no user-visible technical error,
    `P23` persistence verified after reload.
  - expected public delete policy: `public_unlink_denied=true`,
    `requires_shell_cleanup=true`, `actionable_console_errors=0`.

Data hygiene:

- Temporary `purchase.order/46` was removed through Makefile Odoo shell after the
  browser run; cleanup confirmed `remaining=[]`.

## M5 Dictionary Maintenance Addendum

追加批次 `Batch-Form-M5-Dictionary-Maintenance-F24` 覆盖 M5
`sc.dictionary` 配置维护路径。

新增验收：

- 新增 `scripts/verify/form_m5_dictionary_maintenance_acceptance.js`。
- 真实浏览器登录 `wutao`，打开自定义 `sc.dictionary` 创建页，填写
  `字典类型/编码/名称/排序`，保存后通过 `api.data` 读库确认记录持久化。
- 打开创建出的记录，修改名称，保存后再次读库确认编辑结果持久化。
- 使用相同 `code + type` 再次创建，验证页面显示友好重复错误，并确认数据库没有新增第二条。

Verification:

- `node --check scripts/verify/form_m5_dictionary_maintenance_acceptance.js`: PASS
- Real browser M5 gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 node scripts/verify/form_m5_dictionary_maintenance_acceptance.js`
  - artifact: `artifacts/form-m5-dictionary-maintenance/20260430T154519/summary.json`
  - result: `pass=true`
  - covered paths:
    `P03` create form,
    `P04` edit lifecycle,
    `P05` create-form technical-field containment,
    `P20` duplicate friendly error,
    `P23` persistence after create/edit.
  - duplicate feedback:
    `已有相同记录，请先搜索并选择已有记录；如确需新建，请使用不同名称。`
  - technical leak check:
    no `duplicate key/psycopg2/Traceback/DETAIL`.
  - expected public delete policy:
    `public_unlink_denied=true`, `requires_shell_cleanup=true`,
    `actionable_console_errors=0`.

Data hygiene:

- Temporary `sc.dictionary/11` was removed through Makefile Odoo shell after the
  browser run; cleanup confirmed `remaining=[]`.

## M3 Purchase Order Action Addendum

追加批次 `Batch-Form-M3-Purchase-Order-F18` 覆盖 M3 `purchase.order`
原生确认动作与非待审按钮隐藏。

新增修复：

- Form parser 将 Odoo 原生 `type="object"` 按钮交付为 `kind=object`，
  不再误交付为 `server`。这修复了真实用户点击 `确认订单` 后
  `execute_button` 返回“后端不支持按钮类型: server”的根因。
- Form layout 内 button 节点补齐 `modifiers` 契约，NativeFormTreeRenderer
  继续使用通用 `isNodeVisible` 消费后端语义，隐藏不属于当前状态或当前审批状态的按钮。
- ContractFormPage 对 action 列表也消费 `visible.attrs.invisible/states`，
  保证 header action 与 native layout button 使用同一后端可见性语义。

Verification:

- `python3 -m py_compile 'addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py'`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_m3_purchase_order_acceptance.js`: PASS
- Runtime refresh:
  - prod-sim Odoo `make restart`: PASS
  - prod-sim frontend `make frontend.restart`: PASS
- Real browser M3 gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim SUBMITTER_LOGIN=caisiqi SUBMITTER_PASSWORD=123456 PURCHASE_ORDER_ID=34 ACTION_ID=549 node scripts/verify/form_m3_purchase_order_acceptance.js`
  - artifact: `artifacts/form-m3-purchase-order/20260430T133803/summary.json`
  - result: `pass=true`
  - `P30`: RFQ form renders `确认订单` as executable object action; invalid approval buttons are hidden.
  - `P31`: after confirm, record becomes `state=purchase, validation_status=no` under current non-blocking approval policy; non-pending approval buttons remain hidden.
  - console errors: `0`.

Policy fact:

- `sc.approval.policy` for `purchase.order` exists but `approval_required=False`
  in current `sc_prod_sim`; therefore this batch validates non-blocking confirm,
  not strict tier approval. A future strict approval batch must first set or seed
  `approval_required=True` as an explicit fixture fact.

Data hygiene:

- Temporary `purchase.order/32/33/34`, `project.project/878/879/880`,
  and `res.partner/8067/8068/8069` were deleted.
- Temporary products `product.product/27/28/29` were archived because generated
  stock moves keep valid foreign-key references; no active temporary purchase
  products remain visible to users.

## P26 Localization Addendum

追加批次 `Batch-Form-Localization-F20` 收口 P26，重点验证同一真实用户语言下
后端契约与自定义表单 DOM 不再泄漏英文标准状态。

Root cause:

- `app.model.config` 是语言无关缓存，历史上保存了英文 `string/selection`。
  `page_assembler._to_fields_map` 在组装运行时契约时让该缓存覆盖了当前用户
  `fields_get()` 的中文元数据，导致 M3 `purchase.order` 状态条显示
  `RFQ/Purchase Order/Locked/Cancelled`。

Fix:

- `page_assembler._to_fields_map` 改为以当前用户上下文的 `fields_get()`
  作为字段显示名与 selection labels 真源，缓存只提供稳定字段集合。
- Form parser `_build_statusbar` 对任意 selection 状态字段构造 states，
  不再限定字段名必须是 `state`，覆盖 `project.project.lifecycle_state`。
- 新增 `scripts/verify/form_localization_acceptance.js` 作为 P26 浏览器门禁。

Verification:

- `python3 -m py_compile addons/smart_core/app_config_engine/services/assemblers/page_assembler.py 'addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py'`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_localization_acceptance.js`: PASS
- Runtime refresh:
  - prod-sim Odoo `make restart`: PASS
  - prod-sim frontend `make frontend.restart`: PASS
- Real browser P26 gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_PASSWORD=123456 node scripts/verify/form_localization_acceptance.js`
  - artifact: `artifacts/form-localization/20260430T135607/summary.json`
  - result: `pass=true`
  - M1 `project.project/771` DOM labels: `草稿/在建/停工/竣工/结算中/保修期/关闭`
  - M2 `payment.request/28489` contract and DOM labels: `草稿/提交/审批中/已批准/已驳回/已完成/已取消`
  - M3 `purchase.order/9` contract and DOM labels: `询价/发送询价/待批准/采购订单/已锁定/已取消`
  - `english_leak=false`, console errors: `0`.

## M2 Reject Reason Addendum

追加批次 `Batch-M2-Payment-Reject-Reason-F17` 覆盖付款申请驳回路径。

新增修复：

- 后端 `payment.request` business action 交付契约补齐
  `kind=mutation/level=header/selection=none/visible_profiles`，确保治理后的动作在原生表单树模式下可达。
- `ContractFormPage` 将 `views.form.business_actions` 纳入通用 action 合并源。
- 原生表单树模式下，前端继续隐藏原生重复 header action，但保留契约 mutation action；
  原生 XML 按钮仍由 native layout 渲染。
- `ContractFormPage` 保存 `required_params/requires_reason`，执行 mutation 前按契约收集
  `reason`，并通过 `sceneMutationRuntime.params` 传给 `payment.request.execute`。

Verification:

- `python3 -m py_compile addons/smart_construction_core/core_extension.py`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_m2_payment_request_reject_acceptance.js`: PASS
- Real browser M2 reject gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 APPROVER_LOGIN=chenshuai APPROVER_PASSWORD=123456 PAYMENT_REQUEST_ID=28489 ACTION_ID=585 node scripts/verify/form_m2_payment_request_reject_acceptance.js`
  - artifact: `artifacts/form-m2-payment-request-reject/20260430T132147/summary.json`
  - result: `pass=true`
  - contract: `payment_reject.allowed=true`, `requires_reason=true`, `required_params=["reason"]`
  - browser: exact `驳回` action visible, prompt message `驳回原因`
  - backend state: `payment.request/28489.state=rejected`
  - console errors: `0`

Data hygiene:

- Post-run cleanup restored `payment.request/28489` to `draft/no`.
- Generated reject acceptance chatter message was removed.
- Cleanup probe: `ledger_count=0`, `review_count=0`.

## M2 Payment Submit Advisory Policy Addendum

本批次纠正付款申请提交策略：附件、结算状态和资金承载在当前阶段不应默认成为系统强阻断。

Contract decision:

- `payment.request` 提交/审批前置风险由后端统一收集为 advisory contract。
- 默认模式下 `ui.contract` 和 `payment.request.available_actions` 对 `submit` 返回
  `allowed=true`、`reason_code=OK`，同时提供
  `warning_message`、`advisory_warnings`、`advisory_reason_codes`。
- `payment.request.execute` 提交默认放行，并在返回值中携带同一批 advisory warnings。
- 前端只消费后端 `warning_message` 作为按钮提示，不按附件、结算或资金字段自行判断。
- 强阻断能力通过系统参数保留：
  `sc.payment.force_block_all` 或
  `sc.payment.force_block.<reason_code_lowercase>`。
- 原生表单中“结算额度不足”提示文案同步改为风险提示，避免继续声明“系统将阻止提交/完成”。

Verification:

- `python3 -m py_compile addons/smart_construction_core/models/core/payment_request.py addons/smart_construction_core/handlers/payment_request_available_actions.py addons/smart_construction_core/core_extension.py addons/smart_core/app_config_engine/services/assemblers/page_assembler.py addons/smart_core/utils/reason_codes.py`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_m2_payment_request_acceptance.js`: PASS
- `git diff --check`: PASS
- Runtime refresh:
  - `smart_construction_core` upgraded on `sc_prod_sim` after XML view wording change.
  - prod-sim Odoo and frontend restarted.
- Real browser M2 payment submit gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 PAYMENT_REQUEST_ID=28489 ACTION_ID=585 node scripts/verify/form_m2_payment_request_acceptance.js`
  - artifact: `artifacts/form-m2-payment-request/20260430T123639/summary.json`
  - result: `pass=true`
  - contract: `submit.allowed=true`, `submit.reason_code=OK`
  - advisories: `PAYMENT_ATTACHMENTS_REQUIRED`, `P0_PAYMENT_SETTLEMENT_NOT_READY`, `P0_PAYMENT_FUNDING_NOT_READY`
  - execute: `status=200`, `ok=true`
  - DOM wording: “系统将提示风险，是否继续办理由审批人判断。”
- Force-block switch probe:
  - temporary param: `sc.payment.force_block.payment_attachments_required=True`
  - result: `action_submit` blocked with `PAYMENT_ATTACHMENTS_REQUIRED`
  - cleanup: parameter restored to `False`

Data hygiene:

- `payment.request/28489` restored to `draft/no`.
- Acceptance attachments for the representative record: `0`.

## M2 Payment Approval Decision Addendum

提交后的审批动作已同步收口为后端契约驱动的 advisory mode。

Contract decision:

- `approve` 不再要求前端理解 `validation_status`。
- 后端新增 `action_approval_decision`：
  - `waiting/pending`: 执行 tier 审批通过。
  - `validated`: 执行最终批准。
  - `no` 且无 tier review: 允许审批人直接批准，同时返回风险提示。
- `payment.request.available_actions` 在提交态按同一语义声明
  `approve.allowed=true/reason_code=OK`，并携带 advisory warnings。
- 前端仍只触发 `payment.request.execute` + `action=approve`，不做 tier 状态判断。

Verification:

- `python3 -m py_compile addons/smart_construction_core/models/core/payment_request.py addons/smart_construction_core/handlers/payment_request_available_actions.py addons/smart_construction_core/handlers/payment_request_approval.py addons/smart_construction_core/handlers/payment_request_execute.py addons/smart_construction_core/core_extension.py`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_m2_payment_request_acceptance.js`: PASS
- `git diff --check`: PASS
- Real browser M2 payment submit + approval gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 APPROVER_LOGIN=chenshuai APPROVER_PASSWORD=123456 PAYMENT_REQUEST_ID=28489 ACTION_ID=585 node scripts/verify/form_m2_payment_request_acceptance.js`
  - artifact: `artifacts/form-m2-payment-request/20260430T124532/summary.json`
  - result: `pass=true`
  - submit actor: `wutao`, execute submit `status=200`
  - approver actor: `chenshuai`
  - approval contract: `approve.allowed=true`, `approve.reason_code=OK`
  - approval advisories: `P0_PAYMENT_SETTLEMENT_NOT_READY`, `P0_PAYMENT_FUNDING_NOT_READY`
  - approval execute: `status=200`, `ok=true`

Data hygiene:

- `payment.request/28489` restored to `draft/no`.
- `review_count=0`.
- Acceptance attachments for the representative record: `0`.

## M2 Payment Completion Addendum

付款申请完成路径已闭环到真实业务状态。

Contract decision:

- `done` 是后端业务办理动作，不要求用户通过只读 `ledger_line_ids` 表格手工新增付款台账。
- 未足额付款默认作为 advisory：`P0_PAYMENT_NOT_FULLY_PAID`。
- 执行 `done` 时，如尚未存在足额付款记录，后端自动生成 `payment.ledger`，然后将申请置为 `done`。
- `payment.ledger` 在 `payment_soft_gate` 下继承已被审批人接受的结算状态风险；强阻断能力仍可通过
  `sc.payment.force_block.p0_payment_settlement_not_ready` 开启。
- 前端仍只消费动作契约，不根据付款金额、台账数量或结算状态自行决定是否显示完成。

Verification:

- `python3 -m py_compile addons/smart_construction_core/models/core/payment_ledger.py addons/smart_construction_core/models/core/payment_request.py addons/smart_construction_core/handlers/payment_request_available_actions.py addons/smart_construction_core/handlers/payment_request_approval.py addons/smart_core/utils/reason_codes.py addons/smart_core/handlers/reason_codes.py`: PASS
- `node --check scripts/verify/form_m2_payment_request_acceptance.js`: PASS
- `git diff --check`: PASS
- Real browser M2 payment submit + approval + completion gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 APPROVER_LOGIN=chenshuai APPROVER_PASSWORD=123456 PAYMENT_REQUEST_ID=28489 ACTION_ID=585 node scripts/verify/form_m2_payment_request_acceptance.js`
  - artifact: `artifacts/form-m2-payment-request/20260430T125842/summary.json`
  - result: `pass=true`
  - done contract: `allowed=true`, `reason_code=OK`
  - done advisories: `P0_PAYMENT_NOT_FULLY_PAID`, `P0_PAYMENT_SETTLEMENT_NOT_READY`, `P0_PAYMENT_FUNDING_NOT_READY`
  - done execute: `status=200`, `ok=true`, `payment_request.state=done`
  - console errors: `0`

Data hygiene:

- Acceptance-generated `payment.ledger/12195` removed.
- `payment.request/28489` restored to `draft/no`.
- `review_count=0`.
- Acceptance attachments for the representative record: `0`.

## M2 Payment Done Prerequisite Addendum

审批通过后的状态和完成动作前置条件已继续收口。

Contract decision:

- 无 tier review 的审批人直接通过路径将记录落到
  `state=approved` 与 `validation_status=validated`。
- `done` 动作仍不在未付款时放行，但原因必须契约化。
- 新增 shared reason code `P0_PAYMENT_NOT_FULLY_PAID`，meta 提供
  `suggested_action=complete_payment_execution`。
- 前端不得根据 `is_fully_paid`、金额字段或错误文本推断完成动作；只消费后端动作契约。

Verification:

- Runtime import probe: `PaymentRequestAvailableActionsHandler(...).run` returned `ok=True`, `actions=4`, `primary=submit`.
- Real browser M2 payment submit + approval + done-prerequisite gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 APPROVER_LOGIN=chenshuai APPROVER_PASSWORD=123456 PAYMENT_REQUEST_ID=28489 ACTION_ID=585 node scripts/verify/form_m2_payment_request_acceptance.js`
  - artifact: `artifacts/form-m2-payment-request/20260430T125319/summary.json`
  - result: `pass=true`
  - approval execute state: `approved`
  - done contract: `allowed=false`, `reason_code=P0_PAYMENT_NOT_FULLY_PAID`, `suggested_action=complete_payment_execution`
  - console errors: `0`

Data hygiene:

- `payment.request/28489` restored to `draft/no`.
- `review_count=0`.
- Acceptance attachments for the representative record: `0`.

## L4 Activity Contract Addendum

追加批次 `Batch-Form-Action-Paths-F4` 收口 `P17 activity`。上一轮仅能暴露“活动缺少可执行调度契约”，本轮将其补成后端契约和真实浏览器可用路径。

新增修复：

- Form chatter contract now exposes `chatter_schedule_activity.payload.execute_intent=chatter.activity.schedule`.
- Activity payload declares backend-owned field semantics for `summary/date_deadline/note`; frontend consumes these labels and no longer reports a missing scheduling contract.
- Added backend intent `chatter.activity.schedule`, which creates `mail.activity` with write access checks, model metadata validation, activity type resolution, and traceable result metadata.
- `chatter.timeline` now includes `mail.activity` rows, so scheduled activities are visible in the same collaboration timeline.
- Frontend renders the activity composer from contract payload and submits to the backend intent; the activity summary is displayed in the timeline after scheduling.
- The action-path browser gate now requires both message posting and activity scheduling for `P17`.

Verification:

- `python3 -m py_compile addons/smart_core/handlers/chatter_activity_schedule.py addons/smart_core/handlers/chatter_timeline.py addons/smart_core/handlers/chatter_post.py 'addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py'`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_action_path_acceptance.js`: PASS
- Runtime refresh:
  - `CODEX_DB=sc_prod_sim CODEX_MODULES=smart_core CODEX_NEED_UPGRADE=1 make codex.fast`: PASS
  - `FRONTEND_PROFILE=prod-sim make frontend.restart`: PASS
- Real browser L4 action gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_action_path_acceptance.js`
  - artifact: `artifacts/form-action-path/20260430T102555/summary.json`
  - result: `pass=true`
  - `P15`: statusbar still passes.
  - `P16`: smart/stat button navigation still passes.
  - `P17`: `发送消息/记录备注/活动` are enabled; message posting succeeds; activity scheduling succeeds and appears in timeline.
  - console errors: `0`.

Data hygiene:

- The gate temporarily wrote `mail.message` and `mail.activity` records with `L4 form chatter/activity` prefixes.
- Post-cleanup probe removed them and confirmed `remaining_chatter_test_messages=0`, `remaining_activity_test_records=0`.

Current matrix coverage after this addendum:

- `P02`: existing record read
- `P04`: edit/save lifecycle for a main form field
- `P07`: many2one quick input with contract-owned match semantics
- `P08`: many2one search-more cancel/select
- `P09`: no-match deferred relation create does not create before main save
- `P10`: many2many select/remove/save/reload
- `P11`: one2many empty surface
- `P12`: one2many add-row validation path
- `P13`: one2many readonly/computed columns
- `P14`: notebook/tabs
- `P15`: statusbar real browser reachability
- `P16`: smart/stat button navigation reachability
- `P17`: chatter message and activity scheduling real browser reachability
- `P20`: required field and row validation friendly errors
- `P23`: persistence verified by custom reload and native Odoo reload

## L4 Attachment Contract Addendum

追加批次 `Batch-Form-Action-Paths-F5` 收口 `P18 upload/download`。本轮暴露的缺口是后端附件契约判定过窄：`project.project` 已有 mail chatter 能力，但原生 form 没有单独 `oe_attachment_box` 节点时，`views.form.attachments.enabled` 未下发，导致自定义页面没有可用附件入口。

新增修复：

- Form parser now treats chatter-enabled forms as attachment-capable forms and emits `views.form.attachments` with backend-owned upload/download intent, max size, accepted types, and UI labels.
- Custom form consumes only `views.form.attachments` to render upload/download controls; it does not infer file capability from model names or chatter DOM.
- Attachment upload uses `file.upload`; attachment listing comes through `chatter.timeline`; attachment download uses `file.download`.
- The browser gate now creates a safe text fixture, uploads it through the visible page control, waits for timeline visibility, downloads it, and asserts downloaded content equals uploaded content.

Verification:

- `python3 -m py_compile 'addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py' addons/smart_core/handlers/file_upload.py addons/smart_core/handlers/file_download.py`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_action_path_acceptance.js`: PASS
- Runtime refresh:
  - `CODEX_DB=sc_prod_sim CODEX_MODULES=smart_core CODEX_NEED_UPGRADE=1 make codex.fast`: PASS
  - `FRONTEND_PROFILE=prod-sim make frontend.restart`: PASS
- Real browser L4 action gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_action_path_acceptance.js`
  - artifact: `artifacts/form-action-path/20260430T103816/summary.json`
  - result: `pass=true`
  - `P18`: file upload appears in timeline; download suggested filename matches uploaded filename; downloaded content matches uploaded content.
  - console errors: `0`.

Data hygiene:

- The gate temporarily wrote `mail.message`, `mail.activity`, and `ir.attachment` rows with `L4 form chatter/activity/attachment` prefixes.
- Post-cleanup probe removed them and confirmed `messages=0`, `activities=0`, `attachments=0`.

## M2-M5 Error And Recovery Addendum

追加批次 `Batch-Form-M2-M5-Error-Recovery-F9` 深化代表模型
`P20/P24/P25`，不改业务数据、不改前端语义。

覆盖模型：

- M2 `payment.request/28489`, action `585`
- M3 `purchase.order/9`, action `549`
- M4 `sc.legacy.receipt.income.fact/7220`, action `561`
- M5 `sc.dictionary/5`, action `619`

Verification:

- `node --check scripts/verify/form_model_error_recovery_acceptance.js`: PASS
- `python3 -m py_compile addons/smart_core/handlers/api_data.py addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- Real browser M2-M5 error/recovery gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 node scripts/verify/form_model_error_recovery_acceptance.js`
  - artifact: `artifacts/form-model-error-recovery/20260430T112735/summary.json`
  - result: `pass=true`
  - decision: `pass`
  - `P20`: create-form required validation shows user-facing friendly errors and stays on `new`; no record creation path is accepted as success.
  - `P25`: existing record reload and direct deep link recovery stay renderable for all four tiers.
  - `P24`: all four tiers now expose `record_version` conflict semantics in `ui.contract` form edit surface.
  - console errors: `0`.

Architecture conclusion:

- `write_date` appearing as an ordinary field descriptor is not a concurrency contract.
- Backend form contract now declares `record_version.strategy=write_date_if_match`, `token_field=write_date`, and `request_param=if_match` for edit forms with a real record id.
- Generic `api.data` `op=write` now accepts `if_match`/`record_version` and returns `409` with `RECORD_VERSION_CONFLICT` before write when the submitted token is stale.
- Custom form reads and submits the token only when `record_version` is present in contract; frontend still must not infer stale-write policy from `write_date` field presence.
- Environment note: frontend prod-sim proxies to `http://localhost:18069`; code changes must be loaded by restarting the `sc-backend-odoo-prod-sim` Odoo container, not only the default dev Odoo service.

Data hygiene:

- The browser gate intentionally exercises empty create validation and requires the route to remain `new`.
- No fixture records are created by this gate.

Current matrix coverage after this addendum:

- `P02`: existing record read
- `P04`: edit/save lifecycle for a main form field
- `P07`: many2one quick input with contract-owned match semantics
- `P08`: many2one search-more cancel/select
- `P09`: no-match deferred relation create does not create before main save
- `P10`: many2many select/remove/save/reload
- `P11`: one2many empty surface
- `P12`: one2many add-row validation path
- `P13`: one2many readonly/computed columns
- `P14`: notebook/tabs
- `P15`: statusbar real browser reachability
- `P16`: smart/stat button navigation reachability
- `P17`: chatter message and activity scheduling real browser reachability
- `P18`: attachment upload/list/download real browser reachability
- `P20`: required field and row validation friendly errors
- `P23`: persistence verified by custom reload and native Odoo reload

## L4 Body Action Contract Addendum

追加批次 `Batch-Form-Action-Paths-F6` 收口 `P19 body/notebook action buttons`。本轮以 `工程量清单` 页签内的安全导航按钮 `工程量清单分析` 为典型路径，验证表单 body/notebook 内按钮不是静态标签，而是可执行的后端 action 契约。

新增验证：

- Browser gate switches to the native-derived `工程量清单` tab.
- It targets non-smart body action button `工程量清单分析`.
- It clicks the button, requires URL navigation, then returns to the original project detail page for later paths.
- This path uses existing `NativeFormTreeRenderer -> native-action -> runAction` contract chain; no new frontend business rule was introduced.

Verification:

- `node --check scripts/verify/form_action_path_acceptance.js`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- Real browser L4 action gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_action_path_acceptance.js`
  - artifact: `artifacts/form-action-path/20260430T104130/summary.json`
  - result: `pass=true`
  - `P19`: `工程量清单分析` visible and navigates successfully.

## M2 Payment Request Business Action Addendum

追加批次 `Batch-Form-M2-Payment-Request-F10` 深化交易单据代表模型
`payment.request/28489`，覆盖 `P15/P20` 的后端业务动作语义与真实
浏览器表单可达性。

新增修复：

- `smart_construction_core` 暴露 `smart_core_form_business_actions` hook，
  form contract 装配层可调用行业模块输出业务动作语义。
- `payment.request` 表单 header button 现在携带后端声明的
  `business_action/allowed/reason_code/suggested_action/mutation/refresh_policy`。
- `提交审批` 在当前记录下由后端声明为不可执行，
  `reason_code=PAYMENT_ATTACHMENTS_REQUIRED`，
  `suggested_action=upload_attachment`。
- `payment.request.execute` 捕获底层 `[SC_GUARD:*]` 业务 guard，并将
  `PAYMENT_ATTACHMENTS_REQUIRED` 作为一等 `reason_code` 返回，前端不解析错误文本。
- 前端通用 action 映射只消费契约中的 `mutation/allowed/reason`，不写
  `payment.request` 特例判断。

Verification:

- `python3 -m py_compile addons/smart_core/utils/reason_codes.py addons/smart_construction_core/handlers/payment_request_approval.py addons/smart_construction_core/handlers/payment_request_execute.py addons/smart_construction_core/core_extension.py addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_m2_payment_request_acceptance.js`: PASS
- `git diff --check`: PASS
- Runtime refresh:
  - `make mod.upgrade MODULE=smart_core` on `sc_prod_sim`: PASS
  - `make mod.upgrade MODULE=smart_construction_core` on `sc_prod_sim`: PASS
  - prod-sim Odoo restart: PASS
  - `FRONTEND_PROFILE=prod-sim make frontend.restart`: PASS
- Real browser M2 payment gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 node scripts/verify/form_m2_payment_request_acceptance.js`
  - artifact: `artifacts/form-m2-payment-request/20260430T114557/summary.json`
  - result: `pass=true`
  - `M2-P15-P20`: form contract includes 7 payment business actions; submit is blocked with `PAYMENT_ATTACHMENTS_REQUIRED` and mutation semantics.
  - `M2-P20`: executing submit returns HTTP 400 with `reason_code=PAYMENT_ATTACHMENTS_REQUIRED`, `suggested_action=upload_attachment`.
  - `M2-P02-P15`: browser opens the custom payment request form, renders statusbar labels `草稿/提交/审批中/已批准/已驳回/已完成/已取消`, and header action buttons are present.
  - unexpected console errors: `0`.

Boundary:

- This closes the representative M2 payment-request submit-blocked path.
- It does not yet close every transaction document state transition, approval
  success path, reject reason dialog, attachment upload-to-submit success path,
  or multi-role approval matrix. Those remain explicit M2 follow-up rows.

## M2 Payment Request Attachment And Next Blocker Addendum

追加批次 `Batch-Form-M2-Payment-Request-F11` 继续深化
`payment.request/28489`，覆盖 `P18` 附件路径和上传后下一业务阻断解释。

新增修复：

- `payment.request` 纳入行业附件上传/下载白名单：
  `smart_core_file_upload_allowed_models` 与
  `smart_core_file_download_allowed_models`。
- `smart_core_form_business_actions` 对 `payment.request` 同步下发
  `views.form.attachments`，因为提交业务规则依赖附件，即使原生 form
  没有 chatter 节点也必须给用户附件入口。
- `ContractFormPage` 的通用协作区支持 attachment-only contract；
  `attachments.enabled=true` 时渲染上传/下载工具，不再要求 chatter action 存在。
- `payment.request.available_actions` 预检捕获底层 `[SC_GUARD:*]`，
  上传附件后 `提交审批` 从 `PAYMENT_ATTACHMENTS_REQUIRED` 推进到
  `P0_PAYMENT_SETTLEMENT_NOT_READY`。
- `P0_PAYMENT_SETTLEMENT_NOT_READY` 纳入共享 reason meta，
  `suggested_action=complete_settlement_approval`。

Verification:

- `python3 -m py_compile addons/smart_core/utils/reason_codes.py addons/smart_construction_core/handlers/payment_request_available_actions.py addons/smart_construction_core/handlers/payment_request_approval.py addons/smart_construction_core/core_extension.py addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_m2_payment_request_acceptance.js`: PASS
- `git diff --check`: PASS
- Runtime refresh:
  - prod-sim Odoo restart: PASS
  - `FRONTEND_PROFILE=prod-sim make frontend.restart`: PASS
- Real browser M2 payment gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 node scripts/verify/form_m2_payment_request_acceptance.js`
  - artifact: `artifacts/form-m2-payment-request/20260430T115623/summary.json`
  - result: `pass=true`
  - `M2-P18`: browser uploads a txt attachment from the payment request form, timeline shows it, download content matches uploaded content.
  - `M2-P15-P20-P18`: after upload, contract no longer reports `PAYMENT_ATTACHMENTS_REQUIRED`; it reports `P0_PAYMENT_SETTLEMENT_NOT_READY`.
  - `M2-P20-P18`: executing submit after upload returns HTTP 400 with `reason_code=P0_PAYMENT_SETTLEMENT_NOT_READY`, `suggested_action=complete_settlement_approval`.
  - unexpected console errors: `0`.

Data hygiene:

- The gate temporarily uploaded
  `M2 payment request attachment acceptance 1777550191187.txt`.
- Post-cleanup probe deleted the `ir.attachment` row and confirmed `remaining=0`.

Boundary:

- This closes the payment-request attachment prerequisite path and precise next
  blocker explanation.
- It does not yet close successful submit. The current representative record is
  correctly blocked because settlement `STO2600005` is still in `submit`; the
  next M2 path needs either a settlement-approved specimen or a controlled
  fixture to prove successful submit and approval transitions.

## M2 Payment Request Funding Guard Addendum

追加批次 `Batch-Form-M2-Payment-Request-F12` 在受控 fixture 下继续推进
提交路径。将 `payment.request/28489` 的关联结算单 `STO2600005` 临时从
`submit` 调整为 `approve`，保留付款申请本身 `draft/no`，用于越过结算状态
阻断并验证下一层业务门禁。

新增修复：

- 资金承载门禁从普通 `UserError` 收敛为标准 guard reason：
  - `P0_PAYMENT_FUNDING_NOT_READY`
  - `P0_PAYMENT_FUNDING_BASELINE_INVALID`
  - `P0_PAYMENT_FUNDING_CAP_EXCEEDED`
- 共享 reason meta 增加对应 suggested action：
  - `setup_project_funding`
  - `fix_project_funding_baseline`
  - `adjust_payment_amount_or_funding`
- `payment.request.available_actions` 与 `payment.request.execute` 现在在资金
  门禁失败时返回一致的 reason code，不再泛化为 `BUSINESS_RULE_FAILED`。

Verification:

- `python3 -m py_compile addons/smart_core/utils/reason_codes.py addons/smart_construction_core/models/core/payment_request.py addons/smart_construction_core/handlers/payment_request_available_actions.py addons/smart_construction_core/handlers/payment_request_approval.py`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `git diff --check`: PASS
- Real browser controlled funding-guard gate:
  - setup: settlement `STO2600005` temporarily set to `approve`.
  - command: browser login `wutao/123456`, open `payment.request/28489`, upload txt attachment, fetch contract, execute submit.
  - artifact: `artifacts/form-m2-payment-request-funding-guard/20260430T120232/summary.json`
  - result: `pass=true`
  - contract: `allowed=false`, `reason_code=P0_PAYMENT_FUNDING_NOT_READY`, `suggested_action=setup_project_funding`.
  - execute: HTTP 400, `reason_code=P0_PAYMENT_FUNDING_NOT_READY`, `suggested_action=setup_project_funding`.
  - unexpected console errors: `0`.

Data hygiene:

- Fixture cleanup restored `payment.request/28489` to `state=draft`, `validation_status=no`.
- Fixture cleanup restored settlement `STO2600005` to `state=submit`.
- Uploaded fixture attachment
  `M2 payment funding guard fixture 1777550558797.txt` was deleted; cleanup confirmed `attachments_remaining=0`.

Boundary:

- This closes precise funding-guard explanation for the submit path.
- Successful submit is still open because the representative project lacks
  funding readiness. The next submit-success gate needs a controlled funding
  baseline fixture or a different real payment request whose project funding is
  ready and whose settlement is approved.
  - `P15/P16/P17/P18`: regression still passes in the same run.
  - console errors: `0`.

Data hygiene:

- The gate temporarily wrote `mail.message`, `mail.activity`, and `ir.attachment` rows with `L4 form chatter/activity/attachment` prefixes.
- Post-cleanup probe removed them and confirmed `messages=0`, `activities=0`, `attachments=0`.

Current matrix coverage after this addendum:

- `P02`: existing record read
- `P04`: edit/save lifecycle for a main form field
- `P07`: many2one quick input with contract-owned match semantics
- `P08`: many2one search-more cancel/select
- `P09`: no-match deferred relation create does not create before main save
- `P10`: many2many select/remove/save/reload
- `P11`: one2many empty surface
- `P12`: one2many add-row validation path
- `P13`: one2many readonly/computed columns
- `P14`: notebook/tabs
- `P15`: statusbar real browser reachability
- `P16`: smart/stat button navigation reachability
- `P17`: chatter message and activity scheduling real browser reachability
- `P18`: attachment upload/list/download real browser reachability
- `P19`: body/notebook action button navigation reachability
- `P20`: required field and row validation friendly errors
- `P23`: persistence verified by custom reload and native Odoo reload

## L5 Role/State Matrix Addendum

追加批次 `Batch-Form-Role-State-F7` 收口 `P21/P22`。本轮不改变业务实现，新增独立真实浏览器验收脚本，验证角色面与状态面不是单账号、单状态偶然通过。

新增验证：

- Added `scripts/verify/form_role_state_acceptance.js`.
- `P21` logs in real users `wutao/chenshuai/caisiqi/zhaowei/yangdesheng`, calls `system.init` to capture backend `role_surface.role_code`, calls `load_contract` to capture the same delivery contract chain used by the page, then opens the custom project form and checks statusbar, smart buttons, chatter, and attachment entry reachability.
- `P22` covers every current `project.project.lifecycle_state` selection value: `draft/in_progress/paused/done/closing/warranty/closed`.
- Existing records covered `draft=771` and `in_progress=755`; missing states were covered with temporary `L5 State Matrix *` fixture projects, opened through the real browser, then cleaned.
- Status expected labels come from contract data (`views.form.statusbar.states`, falling back to `fields.lifecycle_state.selection` when the delivery contract keeps state labels on field selection). The script does not infer labels from DOM text.

Verification:

- `node --check scripts/verify/form_role_state_acceptance.js`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- Real browser L5 role/state gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_PASSWORD=123456 ACTION_ID=506 MENU_ID=353 ROLE_LOGINS=wutao,chenshuai,caisiqi,zhaowei,yangdesheng STATE_RECORDS=draft:771,in_progress:755,paused:873,done:874,closing:875,warranty:876,closed:877 node scripts/verify/form_role_state_acceptance.js`
  - artifact: `artifacts/form-role-state/20260430T105354/summary.json`
  - result: `pass=true`
  - `P21`: all 5 real users pass with backend `role_surface.role_code` present and form surfaces reachable.
  - `P22`: all 7 lifecycle states pass; active statusbar label matches contract label.
  - console errors: `0`.

Data hygiene:

- Temporary fixture projects `L5 State Matrix paused/done/closing/warranty/closed *` were removed with sudo cleanup after the browser run.
- Cleanup probe confirmed `remaining_l5_state_matrix_projects=0`.

Current matrix coverage after this addendum:

- `P02`: existing record read
- `P04`: edit/save lifecycle for a main form field
- `P07`: many2one quick input with contract-owned match semantics
- `P08`: many2one search-more cancel/select
- `P09`: no-match deferred relation create does not create before main save
- `P10`: many2many select/remove/save/reload
- `P11`: one2many empty surface
- `P12`: one2many add-row validation path
- `P13`: one2many readonly/computed columns
- `P14`: notebook/tabs
- `P15`: statusbar real browser reachability
- `P16`: smart/stat button navigation reachability
- `P17`: chatter message and activity scheduling real browser reachability
- `P18`: attachment upload/list/download real browser reachability
- `P19`: body/notebook action button navigation reachability
- `P20`: required field and row validation friendly errors
- `P21`: role matrix form contract/render reachability across 5 real users
- `P22`: full current lifecycle state statusbar alignment across 7 states
- `P23`: persistence verified by custom reload and native Odoo reload

## L6 Representative Model Tier Addendum

追加批次 `Batch-Form-Model-Tier-F8` 将表单矩阵从 M1 项目详情页推广到 M2-M5 的首批代表模型。该批次只声明“契约与表单表面可达性”通过，不声明这些模型的完整业务办理路径已全部闭环。

新增验证：

- Added `scripts/verify/form_model_tier_acceptance.js`.
- M2 transaction document specimen: `payment.request/28489`, action `585` (`付款/收款申请`).
- M3 line-heavy operational specimen: `purchase.order/9`, action `549` (`采购单`).
- M4 projection/read-heavy specimen: `sc.legacy.receipt.income.fact/7220`, action `561` (`历史收款收入事实`).
- M5 configuration/maintenance specimen: `sc.dictionary/5`, action `619` (`业务字典`).
- For each specimen the script calls `load_contract`, opens the custom form, waits for loading completion, and requires a non-empty renderable surface with no visible page error and no console errors.

Verification:

- `node --check scripts/verify/form_model_tier_acceptance.js`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- Real browser L6 representative tier gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 node scripts/verify/form_model_tier_acceptance.js`
  - artifact: `artifacts/form-model-tier/20260430T110612/summary.json`
  - result: `pass=true`
  - M2/M3/M4/M5 all have `contractOk=true`, `hasRenderableSurface=true`, `noVisibleError=true`.
  - console errors: `0`.

Important boundary:

- This gate proves representative model forms are no longer M1-only and can render from backend contract.
- It does not yet prove per-model create/edit/submit/approve/line-edit/read-only/drill-in workflows. Those remain the next L4/L5 expansion tasks for each model tier.

Current matrix coverage after this addendum:

- M1 `project.project`: P02/P04/P07/P08/P09/P10/P11/P12/P13/P14/P15/P16/P17/P18/P19/P20/P21/P22/P23 covered by prior batches.
- M2 `payment.request`: representative contract/render reachability covered.
- M3 `purchase.order`: representative contract/render reachability covered.
- M4 `sc.legacy.receipt.income.fact`: representative contract/render reachability covered.
- M5 `sc.dictionary`: representative contract/render reachability covered.

## L4 Action Path Addendum

追加批次 `Batch-Form-Action-Paths-F3` 覆盖 `P15/P16/P17` 的真实可达路径，仍以 `project.project/771` 为典型页。

新增修复：

- Custom form no longer renders backend-declared chatter actions as disabled placeholders. Chatter buttons are enabled from contract facts and open a generic contract-driven composer.
- Frontend passes only contract action mode (`message` / `note`) to `chatter.post`; message subtype, fallback behavior, and sender envelope are resolved in backend intent.
- `chatter.post` now supplies a backend-owned `email_from` fallback when the real user has no email configured, so real browser collaboration records remain usable instead of exposing Odoo's raw sender-email failure.
- Unsupported `activity` currently remains visible and clickable, but reports the explicit gap `活动 缺少可执行调度契约`; it is not silently disabled and not faked in frontend.
- Added `scripts/verify/form_action_path_acceptance.js` as the action-path browser gate.

Verification:

- `python3 -m py_compile addons/smart_core/handlers/chatter_post.py`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_action_path_acceptance.js`: PASS
- Runtime refresh:
  - `CODEX_DB=sc_prod_sim CODEX_MODULES=smart_core CODEX_NEED_UPGRADE=1 make codex.fast`: PASS
  - `FRONTEND_PROFILE=prod-sim make frontend.restart`: PASS
- Real browser L4 action gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_action_path_acceptance.js`
  - artifact: `artifacts/form-action-path/20260430T100925/summary.json`
  - result: `pass=true`
  - `P15`: statusbar renders native states `草稿/在建/停工/竣工/结算中/保修期/关闭`, with current state active and controls reachable.
  - `P16`: smart/stat buttons are enabled and `投标管理` navigates from the form to its target action.
  - `P17`: `发送消息/记录备注/活动` are no longer disabled; posting a message succeeds through `chatter.post` and refreshes timeline.
  - console errors: `0`.

P17 activity closure:

- The form contract now declares a schedulable activity payload for the
  chatter action: `execute_intent=chatter.activity.schedule`,
  `activity_type_xmlid=mail.mail_activity_data_todo`, and fields
  `summary/date_deadline/note`.
- Frontend renders the activity composer from that payload and calls the backend
  intent; it does not infer activity type, fields, or scheduling semantics.
- `chatter.activity.schedule` creates `mail.activity` under backend ACL and
  record-rule checks, and `chatter.timeline` returns the activity for page
  feedback.

Verification update:

- `python3 -m py_compile addons/smart_core/handlers/chatter_activity_schedule.py addons/smart_core/handlers/chatter_timeline.py 'addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py'`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `node --check scripts/verify/form_action_path_acceptance.js`: PASS
- Runtime refresh:
  - prod-sim Odoo `make restart`: PASS
  - prod-sim frontend `make frontend.restart`: PASS
- Real browser L4 action gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_action_path_acceptance.js`
  - artifact: `artifacts/form-action-path/20260430T134241/summary.json`
  - result: `pass=true`
  - `P17`: message post and activity schedule both reachable; activity summary is visible after scheduling.
  - `P15/P16/P19/P18`: statusbar, smart action, body action, and attachment paths remained `pass`.
  - console errors: `0`.

Data hygiene:

- The action gate temporarily wrote one `mail.message` with body prefix `L4 form chatter acceptance`.
- Post-cleanup probe removed the test message and confirmed `remaining_chatter_test_messages=0`.

Current matrix coverage after this addendum:

- `P02`: existing record read
- `P04`: edit/save lifecycle for a main form field
- `P07`: many2one quick input with contract-owned match semantics
- `P08`: many2one search-more cancel/select
- `P09`: no-match deferred relation create does not create before main save
- `P10`: many2many select/remove/save/reload
- `P11`: one2many empty surface
- `P12`: one2many add-row validation path
- `P13`: one2many readonly/computed columns
- `P14`: notebook/tabs
- `P15`: statusbar real browser reachability
- `P16`: smart/stat button navigation reachability
- `P17`: chatter message real browser reachability; activity scheduling remains an explicit contract gap
- `P20`: required field and row validation friendly errors
- `P23`: persistence verified by custom reload and native Odoo reload

## L4 Relation Path Addendum

追加批次 `Batch-Form-Relation-Paths-F2` 覆盖 `P07/P08/P09/P10`，仍以 `project.project/771` 为典型页。

新增修复：

- Backend relation contract now declares quick-input match semantics as `single_contains_or_exact`; frontend consumes this contract value and no longer owns matching policy.
- Disabled inline-create fields still carry match semantics, so quick-fill behavior is not coupled to create permission.
- Native-form-tree save collection now uses native layout visible fields when native tree rendering is active. This fixes the gap where a field is visible and operable in the native-derived form, but was filtered out by the custom advanced-field visibility rule before write.
- The relation path gate creates a unique `project.tags` fixture for many2many selection, unlinks it from `project.project/771` through the user-facing write path, and requires external backend cleanup for physical fixture deletion because frontend API correctly denies `project.tags` unlink.

Verification:

- `pnpm --dir frontend/apps/web run typecheck`: PASS
- `python3 -m py_compile addons/smart_core/app_config_engine/services/assemblers/page_assembler.py 'addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py'`: PASS
- `node --check scripts/verify/form_relation_path_acceptance.js`: PASS
- Real browser L4 relation gate:
  - command: `FRONTEND_URL=http://127.0.0.1:5174 DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 RECORD_ID=771 ACTION_ID=506 MENU_ID=353 node scripts/verify/form_relation_path_acceptance.js`
  - artifact: `artifacts/form-relation-path/20260430T093136/summary.json`
  - result: `pass=true`
  - `P07`: typing `Project User` quick-fills `Demo Project User` under contract `single_contains_or_exact`.
  - `P08`: search-more dialog supports cancel without mutation and row select with value return.
  - `P09`: no-match customer input shows pending inline-create label and does not create the related record before main save.
  - `P10`: many2many tag select persists after save/reload, then remove persists after save/reload.
  - console errors: `0`.

Data hygiene:

- The P10 fixture tag was removed after the run through backend shell cleanup.
- Post-cleanup probe: `remaining_l4_tags=0`, `project_771_tags=[]`.

## Delete Policy Contract Addendum

P10 exposed a contract gap: treating `api.data.unlink` as a near-global deny list is not a valid business policy. Deletion must be a backend-owned model policy with explicit allow/deny semantics, not a frontend workaround and not an operational shell-only cleanup path.

Contract decision:

- `api.data.unlink` now resolves a model-level `delete_policy` contract before executing.
- Relation field contracts now expose `relation_entry.delete_policy`; the same policy is mirrored in `semantic_page.relation_entries`.
- `project.tags` is allowed for relation maintenance deletion with `delete_mode=unlink`, reason `RELATION_MAINTENANCE_DELETE_ALLOWED`, and remains subject to Odoo ACL and record rules.
- `project.project` remains denied in this batch with `DELETE_POLICY_DENIED`; primary business object deletion requires a separate business-state policy batch.

Verification:

- `python3 -m py_compile addons/smart_core/utils/delete_policy.py addons/smart_core/utils/reason_codes.py addons/smart_core/handlers/api_data_unlink.py addons/smart_core/app_config_engine/services/assemblers/page_assembler.py addons/smart_construction_core/core_extension.py`: PASS
- Runtime refresh:
  - `CODEX_DB=sc_prod_sim CODEX_MODULES=smart_core,smart_construction_core CODEX_NEED_UPGRADE=1 make codex.fast`: PASS
  - `FRONTEND_PROFILE=prod-sim make frontend.restart`: PASS
- Real browser relation gate after delete-policy contract:
  - artifact: `artifacts/form-relation-path/20260430T093959/summary.json`
  - result: `pass=true`
  - fixture cleanup evidence: `deleted_tag=true`
  - returned policy: `model=project.tags`, `delete_mode=unlink`, `reason_code=RELATION_MAINTENANCE_DELETE_ALLOWED`
- Contract probe for `tag_ids.relation_entry.delete_policy`: PASS, `delete_mode=unlink`.
- Negative probe for `api.data.unlink` on `project.project/771` with `dry_run=true`: PASS, rejected with `DELETE_POLICY_DENIED`.

Current matrix coverage after this addendum:

- `P02`: existing record read
- `P04`: edit/save lifecycle for a main form field
- `P07`: many2one quick input with contract-owned match semantics
- `P08`: many2one search-more cancel/select
- `P09`: no-match deferred relation create does not create before main save
- `P10`: many2many select/remove/save/reload
- `P11`: one2many empty surface
- `P12`: one2many add-row validation path
- `P13`: one2many readonly/computed columns
- `P14`: notebook/tabs
- `P15`: header/statusbar surface
- `P16`: smart/stat button surface
- `P17`: chatter action surface
- `P20`: required field and row validation friendly errors
- `P23`: persistence verified by custom reload and native Odoo reload
