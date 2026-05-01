# Frontend Native Form Business Path Target Matrix 20260430

## Purpose

This matrix is the acceptance target for native/custom form alignment. A form
batch is not closed by proving one page can open. It is closed only when every
path class below has either passing evidence or an explicit blocker with owner,
root cause, and next batch.

## Batch Boundary

- Layer Target: Verification Governance / Form Contract Acceptance
- Module: `addons/smart_core`, `frontend/apps/web`, `scripts/verify`, `docs/verify`
- Source of truth: Odoo native form view rendered for the same real user, same database, same action/menu.
- Custom renderer rule: frontend renders contract semantics only; if frontend must decide business meaning, the contract is incomplete.
- Primary specimen: `project.project/771`, action `506`, menu `353`, user `wutao`, database `sc_prod_sim`.
- Expansion rule: every form surface added to the product must be assigned to one of the model tiers in this document before release.

## Model Tiers

| Tier | Model Class | Required Examples | Why It Exists |
| --- | --- | --- | --- |
| M1 | Master/business object form | `project.project`, supplier/partner maintenance | Covers lifecycle, header, statusbar, smart buttons, notebook, chatter, x2many. |
| M2 | Transaction document form | payment request, settlement, receipt, invoice, expense | Covers create/edit/submit/approve/reject/cancel and required financial fields. |
| M3 | Line-heavy operational form | purchase order, BOQ, contract lines, material plan | Covers editable one2many/many2many, readonly computed columns, totals, row validation. |
| M4 | Projection/read-heavy form | legacy finance facts, dashboards opened as records | Covers readonly business data, no-create/no-edit paths, drill-in buttons. |
| M5 | Configuration/maintenance form | dictionary, partner category, account master | Covers quick create, create-and-edit, duplicate validation, friendly errors. |

## Acceptance Levels

| Level | Name | Must Prove | Evidence |
| --- | --- | --- | --- |
| L0 | Runtime/Data Baseline | Service health, real user login, language, action/menu, record existence, baseline data not polluted. | Shell/API probe plus browser login. |
| L1 | Native Fact Capture | Native form structure for the same user: header, statusbar, stat buttons, notebook tabs, field labels, subviews, modifiers, chatter, dialogs. | Native browser screenshot and structured DOM JSON. |
| L2 | Contract Completeness | Contract contains every native structure and semantic needed by frontend: fields, modifiers, subviews, actions, labels, relation entries, permission results. | `ui.contract/load_view` snapshot and schema guard. |
| L3 | Custom Render Parity | Custom page renders the same business surface: no missing native-present tabs, buttons, labels, subview columns, readonly markers, required markers. | Native/custom browser diff. |
| L4 | Business Operation Paths | Real browser executes create/edit/save/discard/reload/relation/search/more/quick-create/action paths without frontend business guessing. | Playwright path scripts with API/write result evidence. |
| L5 | Role/State/Error Matrix | Same paths under role, state, permission, validation, duplicate, missing required, network/API error, concurrency conflict. | Multi-user browser/API matrix. |
| L6 | Regression Closure | Same gate runs on representative M1-M5 models and fails on any uncovered path class. | CI/release gate artifact bundle. |

## Path Matrix

| ID | Path Class | Required Coverage | Native Fact | Contract Gate | Browser Gate | Close Rule |
| --- | --- | --- | --- | --- | --- | --- |
| P01 | Entry routing | Open from menu/list/kanban/smart button/direct URL/relation dialog. | Native target action/menu/view mode. | route/action payload has model, id, view mode, menu/action ids. | Custom reaches same record/form. | No route creates a different surface silently. |
| P02 | Existing record read | Open persisted record with real user. | Native title, status, header, tabs. | `record_id/render_profile=edit`. | Custom displays same business structure. | Missing native-present structure is fail. |
| P03 | Create form | Open new record from list and relation create. | Native create form fields/defaults. | `render_profile=create`, defaults, required, invisible, readonly. | Custom creates draft page with same required surface. | Required/default mismatch is fail. |
| P04 | Edit lifecycle | Edit, dirty state, save success, save failure, discard, reload after save. | Native save/discard behavior. | write intent, onchange, validation, error labels. | Real browser completes edit and observes persisted value. | Save path must prove backend persistence or dry-run where write is dangerous. |
| P05 | Required/readonly/invisible | Static and dynamic modifiers. | Native modifiers in DOM and behavior. | field modifiers and runtime states. | Required markers, disabled controls, hidden fields match. | Frontend local modifier inference is fail. |
| P06 | Primitive field widgets | char/text/html/int/float/monetary/date/datetime/boolean/selection. | Native widget rendering and accepted values. | widget, type, options, selection labels. | Input, invalid input, clear, save, display. | Every type used by target model covered. |
| P07 | Many2one quick input | Keyword search, partial match, exact match, multiple matches, no match, clear. | Native autocomplete/search-more. | relation entry, search mode, labels, inline create policy. | Custom follows contract and no frontend matching policy. | Match semantics must be contract-defined. |
| P08 | Many2one search more | Open dialog, search, paginate, select, cancel, create-and-edit. | Native modal structure. | dialog fields/actions/labels/domain/context. | Browser completes select/cancel/create path. | Dialog shape invented by frontend is fail. |
| P09 | Deferred relation create | User types no-match value, main form save creates related record only at save time. | Native or approved product behavior. | inline create policy and pending-create payload. | Related record created with main save, not before. | Early creation is fail. |
| P10 | Many2many | Search, select multiple, remove, save, reload. | Native tags/list. | relation options/domain/labels. | Browser proves selection persistence. | Hidden selected values or stale options fail. |
| P11 | One2many empty surface | Empty subtable still shows native columns and add action. | Native list headers/add row. | `subviews.*.tree.columns`, `policies.ui_labels`. | Browser sees headers before rows. | Empty table without structure is fail. |
| P12 | One2many add/edit/remove | Add row, edit cells, required validation, remove, restore, save/reload. | Native inline tree behavior. | row command semantics, relation field, columns, readonly/required. | Browser executes row lifecycle. | Any row command generated by frontend rule is fail. |
| P13 | One2many readonly/computed columns | Readonly visible columns, totals, computed values. | Native visible readonly columns. | readonly column preserved with `surface_role=business_read`. | Disabled in custom and present in headers/rows. | Dropping readonly business columns is fail. |
| P14 | Notebook/tabs | All visible tabs, nested groups, active tab switching. | Native tab list and content. | layout tree preserves notebook/page. | Custom tabs/content match native-present set. | Any native-present tab missing is fail. |
| P15 | Header/statusbar | Header buttons, status transitions, disabled states, confirm/error. | Native header/statusbar. | action semantics, state policy, labels, permission. | Browser sees and safely executes allowed state path. | Button naming in frontend is fail. |
| P16 | Smart/stat buttons | Visible count/actions, overflow/more behavior, navigation. | Native stat button box and overflow. | button box actions and display policy. | Custom navigates to same target or records unsupported gap. | Missing business stat button is fail. |
| P17 | Chatter/collaboration | Send message, log note, schedule activity, attachments if enabled. | Native chatter actions. | chatter contract and action labels. | Browser opens/executes safe chatter action. | Chatter declared present but unusable is fail. |
| P18 | Attachments/files | Upload, list, download, delete denied/allowed. | Native attachment behavior. | attachment policy, limits, accepted types. | Browser exercises file path in safe fixture. | File path requires dedicated security evidence. |
| P19 | Server actions/buttons inside tabs | Object/action buttons in body/notebook. | Native body buttons. | action payload and safe/danger classification. | Browser clicks safe navigation and validates dangerous buttons guarded. | Static button label without action is fail. |
| P20 | Validation and friendly errors | Missing required, duplicate, domain violation, access denied, business state denial. | Native/server error behavior. | error code/message/user-facing label. | Browser sees actionable friendly error. | Raw database/Odoo trace to user is fail. |
| P21 | Permissions by role | Admin, manager, business user, readonly user, denied user. | Native role-specific visibility. | effective rights/rules/reasons. | Custom same visibility/executable result. | Frontend deriving permissions is fail. |
| P22 | State by lifecycle | Draft/in progress/stopped/done/closed/legacy confirmed/cancelled. | Native state-specific modifiers/buttons. | state policy and runtime modifiers. | Browser matrix per state. | State-only success is insufficient. |
| P23 | Persistence integrity | Save, reload, re-open from list, native sees same value. | Native after-save record. | write/read contracts align. | Custom save then native/custom reload compare. | UI-only success without persistence proof is fail. |
| P24 | Concurrency/conflict | Two tabs/users edit same record, stale save, retry/discard. | Native conflict behavior or server policy. | version/etag/conflict contract. | Browser proves conflict message. | Silent overwrite is fail. |
| P25 | Refresh/navigation recovery | Back/forward, reload, session expiry, direct deep link. | Native route recovery. | route/session contract. | Browser survives reload/deep link or shows login and returns. | Lost draft/state without policy is fail. |
| P26 | Localization | Same user language for native and custom. | Native labels in user lang. | contract generated with `user.lang`. | Custom labels match expected language. | Mixed untranslated standard labels are fail unless documented blocker. |
| P27 | Accessibility and control reachability | Keyboard focus, dialog escape/close, disabled semantics. | Native reachable controls. | control semantics/labels. | Browser checks focusable key paths. | Mouse-only critical path is fail. |
| P28 | Visual containment | No overlap, clipped text, broken layout across desktop/mobile. | Native reference plus design constraints. | layout dimensions/hints where needed. | Screenshots desktop/mobile. | Business control hidden by layout is fail. |

## Execution Order

1. L0-L1: capture native facts before changing implementation.
2. L2: fail fast on contract gaps; backend contract is fixed before frontend renderer changes.
3. L3: custom render parity only after contract evidence is complete.
4. L4: execute real browser business paths for the page specimen.
5. L5: repeat the same paths across roles, states, and error cases.
6. L6: promote the matrix to representative M1-M5 models before release closure.

## Required Artifact Shape

Every matrix run must produce:

- `native_form.png`
- `custom_form.png`
- `native_surface.json`
- `custom_surface.json`
- `contract_snapshot.json`
- `path_results.json`
- `gap_report.json`

`gap_report.json` must include:

- `path_id`
- `level`
- `status`: `pass`, `fail`, `blocked`, or `not_applicable`
- `native_fact`
- `contract_fact`
- `custom_fact`
- `root_cause`
- `owner_layer`
- `next_action`

## Stop Conditions

- A native-present business field/action/tab/subview is missing in contract.
- Frontend needs to infer business meaning, permission, state, matching, labels, or relation behavior.
- Browser success cannot prove persistence or safe dry-run.
- The same model has duplicate active form/list/action facts that make the native target ambiguous.
- A user-visible error exposes raw database/Odoo technical detail.

## Current Baseline From F1

The first checked specimen `project.project/771` has passing evidence for:

- P02 existing record read
- P04 edit/save lifecycle for a main form field
- P07 many2one quick input with contract-owned match semantics
- P08 many2one search-more cancel/select
- P09 no-match deferred relation create before main form save
- P10 many2many select/remove/save/reload
- P11 one2many empty surface
- P12 one2many add-row validation path
- P13 one2many readonly/computed columns
- P14 notebook/tabs
- P15 header/statusbar real browser reachability
- P16 smart/stat button real browser navigation
- P17 chatter message and activity scheduling real browser reachability
- P18 attachment upload/list/download real browser reachability
- P19 body/notebook action button navigation reachability
- P20 required field and row validation friendly errors
- P21 role matrix form contract/render reachability across 5 real users
- P22 full current lifecycle state statusbar alignment across 7 states
- P23 persistence verified by custom reload and native Odoo reload

F4 closure:

- P17 activity scheduling is now covered by backend contract
  `chatter.activity.schedule` and real browser evidence
  `artifacts/form-action-path/20260430T102555/summary.json`.

F5 closure:

- P18 attachment upload/list/download is now covered by backend `views.form.attachments`
  contract and real browser evidence
  `artifacts/form-action-path/20260430T103816/summary.json`.

F6 closure:

- P19 body/notebook action button navigation is now covered by the native layout
  action contract and real browser evidence
  `artifacts/form-action-path/20260430T104130/summary.json`.

F7 closure:

- P21 role matrix is now covered by `system.init.role_surface` plus custom form
  browser reachability for `wutao/chenshuai/caisiqi/zhaowei/yangdesheng`.
- P22 state matrix is now covered for every current
  `project.project.lifecycle_state` value: `draft/in_progress/paused/done/closing/warranty/closed`.
- Evidence: `artifacts/form-role-state/20260430T105354/summary.json`.

F8 closure:

- The matrix is now promoted to first representative M2-M5 surface reachability:
  - M2 `payment.request/28489`, action `585`
  - M3 `purchase.order/9`, action `549`
  - M4 `sc.legacy.receipt.income.fact/7220`, action `561`
  - M5 `sc.dictionary/5`, action `619`
- Evidence: `artifacts/form-model-tier/20260430T110612/summary.json`.
- Boundary: this proves contract/render reachability for each model tier, not
  full per-tier business operation closure.

F9 closure:

- The matrix now has representative M2-M5 evidence for:
  - `P20`: create-form required validation friendly errors.
  - `P24`: record-version conflict semantics present in form edit contract.
  - `P25`: reload and direct deep link recovery.
- Evidence: `artifacts/form-model-error-recovery/20260430T112735/summary.json`.
- Decision: `pass`.

F9 implementation note:

- `P24` was first observed as `CONTRACT_MISSING`; the fix is contract-first.
- The form edit contract now exposes `record_version` with
  `strategy=write_date_if_match`, `token_field=write_date`, and
  `request_param=if_match`.
- Generic `api.data` write rejects stale tokens with `409` and
  `RECORD_VERSION_CONFLICT` before executing the write.
- Frontend submits the token only when this contract is present. It does not
  infer conflict policy from ordinary `write_date` field descriptors.

F10 closure:

- M2 `payment.request/28489` now has form-level backend business action
  contract evidence for submit/approve/reject/done semantics.
- `提交审批` is contract-declared blocked for the current record with
  `PAYMENT_ATTACHMENTS_REQUIRED` and `upload_attachment`.
- `payment.request.execute` returns the same reason code and suggested action;
  the frontend does not parse business error text.
- Browser evidence confirms the payment request form statusbar and header
  action surface are renderable.
- Evidence: `artifacts/form-m2-payment-request/20260430T114557/summary.json`.
- Boundary: this closes the representative M2 submit-blocked path only. M2
  approval success, reject reason, attachment upload then submit, and role/state
  approval matrix remain open.

F11 closure:

- M2 `payment.request/28489` now has a browser-proven attachment path:
  upload from the custom payment request form, timeline visibility, download,
  and content match.
- `payment.request` is now included in backend file upload/download allowlists,
  and the form contract emits `views.form.attachments` for this model because
  submit rules require attachments.
- After upload, submit no longer reports `PAYMENT_ATTACHMENTS_REQUIRED`; both
  contract and execute path report `P0_PAYMENT_SETTLEMENT_NOT_READY` with
  `suggested_action=complete_settlement_approval`.
- Evidence: `artifacts/form-m2-payment-request/20260430T115623/summary.json`.
- Data hygiene: uploaded acceptance attachment was removed; cleanup confirmed
  `remaining=0`.
- Boundary: successful submit remains open because this representative record
  is correctly blocked by settlement `STO2600005` state `submit`.

F12 closure:

- Under a controlled fixture, settlement `STO2600005` was temporarily moved to
  `approve` to expose the next submit prerequisite.
- The next blocker is now contractized as `P0_PAYMENT_FUNDING_NOT_READY` with
  `suggested_action=setup_project_funding`, in both available-actions contract
  and execute result.
- Evidence:
  `artifacts/form-m2-payment-request-funding-guard/20260430T120232/summary.json`.
- Data hygiene: payment request restored to `draft/no`, settlement restored to
  `submit`, uploaded fixture attachment removed with `attachments_remaining=0`.
- Boundary: successful submit remains open until a funding-ready project fixture
  or real specimen is available.

The next batch must continue M2-M5 L4/L5 operation paths beyond P20/P24/P25
and extend F12 from precise funding-guard explanation to controlled successful
transaction transitions.
No future batch may claim full form acceptance unless every path row is `pass`
or explicitly closed as `not_applicable` with native evidence.

F13 policy correction:

- F10-F12 的旧结论“附件/结算/资金承载阻断提交”已被本批次替换。
- 当前阶段付款申请提交策略为默认 advisory mode：附件缺失、结算未审批、资金承载未就绪均由后端契约返回
  `warning_message/advisory_warnings/advisory_reason_codes`，但 `提交审批`
  仍应 `allowed=true` 且 execute 返回 `200/OK`。
- 是否阻断业务办理由审批人结合提示判断；系统仅在显式启用强阻断参数时阻断。
- 强阻断开关保留：
  `sc.payment.force_block_all` 或
  `sc.payment.force_block.<reason_code_lowercase>`，例如
  `sc.payment.force_block.payment_attachments_required`。
- 真实浏览器证据：
  `artifacts/form-m2-payment-request/20260430T123639/summary.json`，
  `payment.request/28489` 在无附件、结算 `STO2600005=submit`、项目资金承载未就绪时，
  契约返回 `allowed=true/reason_code=OK`，advisory codes 包含
  `PAYMENT_ATTACHMENTS_REQUIRED/P0_PAYMENT_SETTLEMENT_NOT_READY/P0_PAYMENT_FUNDING_NOT_READY`，
  execute 提交返回 `200`。
- 强阻断能力证据：临时启用
  `sc.payment.force_block.payment_attachments_required=True` 后，`action_submit`
  被 `PAYMENT_ATTACHMENTS_REQUIRED` 阻断；参数已恢复为 `False`。
- 数据卫生：验收后 `payment.request/28489` 已恢复 `draft/no`，测试附件为 `0`。

F14 approval decision correction:

- 提交后的审批动作同样进入 advisory mode。
- `approve` 契约在 `validation_status in waiting/pending` 时代表 tier 审批决定；
  在 `validation_status=validated` 时代表最终批准；在没有 tier review 且
  `validation_status=no` 的提交态单据上，审批人可以直接作出批准决定。
- 该语义由后端 `action_approval_decision` 承载，前端仍只按
  `payment.request.execute?action=approve` 契约触发，不判断 tier 状态。
- 真实浏览器证据：
  `artifacts/form-m2-payment-request/20260430T124532/summary.json`。
  `wutao` 提交 `payment.request/28489` 后，`chenshuai` 作为审批人重新登录，
  `approve.allowed=true/reason_code=OK`，advisory codes 包含
  `P0_PAYMENT_SETTLEMENT_NOT_READY/P0_PAYMENT_FUNDING_NOT_READY`，execute 审批返回
  `200/OK`。
- 数据卫生：验收后 `payment.request/28489` 已恢复 `draft/no`，review 数为 `0`，
  测试附件为 `0`。

F17 reject reason closure:

- `reject` 动作继续由后端契约声明 `requires_reason=true` 与
  `required_params=["reason"]`，前端不判断驳回业务规则，只按契约收集必填参数。
- `views.form.business_actions` 已纳入通用 action 合并源；原生表单树模式下仍由原生
  layout 承载 XML 按钮，但契约 mutation action 会继续在 header action 区可达。
- `payment.request` 业务 action 契约显式声明 `kind=mutation/level=header`，避免治理后的
  `驳回` 被 body action 隐藏，用户不再只能点到原生 `审批驳回`。
- 真实浏览器证据：
  `artifacts/form-m2-payment-request-reject/20260430T132147/summary.json`。
  `wutao` 提交后，`chenshuai` 打开自定义付款申请表单，页面出现治理后的
  `驳回` 按钮；点击后弹出 `prompt`，文案为 `驳回原因`；填写原因后
  `payment.request/28489` 读回 `state=rejected`，console errors 为 `0`。
- 数据卫生：验收后 `payment.request/28489` 已恢复 `draft/no`，`payment.ledger=0`，
  review 数为 `0`，验收驳回消息已清理。

F18 purchase order confirm closure:

- M3 `purchase.order` 的原生 `<button type="object">` 按钮不再被解析为 `kind=server`；
  后端表单按钮契约恢复为 `kind=object/intent=execute`，与 `execute_button`
  支持的 `object/action` 类型一致。
- Native form layout 内的 button 节点现在同步下发 `modifiers/attributes.modifiers`；
  前端通用原生树渲染器只按这些后端修饰符契约隐藏按钮，不再暴露非当前状态/非待审状态动作。
- 当前模拟生产库的 `purchase.order` 审批策略事实为 `approval_required=False`，
  因此 RFQ `确认订单` 走非强制审批策略，真实办理结果应为
  `state=purchase, validation_status=no`；这与当前阶段“提交/确认放行、审批人结合提示判断”的策略一致。
- 真实浏览器证据：
  `artifacts/form-m3-purchase-order/20260430T133803/summary.json`。
  `caisiqi` 打开 `purchase.order/34`，RFQ 状态下只显示当前可用原生动作
  `通过EMail发送/打印询价/确认订单/取消`，不再显示 `审批通过/审批驳回`；
  点击 `确认订单` 后读回 `state=purchase, validation_status=no`，确认后页面仍不显示
  非待审审批按钮，console errors 为 `0`。
- 数据卫生：验收临时 `purchase.order/32/33/34`、`project.project/878/879/880`、
  `res.partner/8067/8068/8069` 已删除；临时产品 `product.product/27/28/29`
  因库存移动外键引用无法硬删，已归档为 `active=False`。

F19 chatter activity closure:

- P17 的活动调度缺口已关闭：后端表单契约在 `views.form.chatter.actions`
  中交付 `execute_intent=chatter.activity.schedule`、默认活动类型
  `mail.mail_activity_data_todo` 与 `summary/date_deadline/note` 字段契约；
  前端只按该 payload 渲染活动表单并提交，不自行创造活动语义。
- 新增 `chatter.activity.schedule` intent 负责真实创建 `mail.activity`，
  `chatter.timeline` 回读活动用于页面回显；权限仍走 `write` ACL 与 record rule。
- 真实浏览器证据：
  `artifacts/form-action-path/20260430T134241/summary.json`。
  `wutao` 打开 `project.project/771`，`发送消息/记录备注/活动` 均可用；
  点击 `活动` 填写摘要、截止日期、备注后，页面回显
  `L4 form activity acceptance ...`，`activity_scheduled=true`，console errors 为 `0`。
- 同轮回归：P15 statusbar、P16 smart button、P19 body action、P18 attachment
  均为 `pass`。
- 数据卫生：验收写入的 `mail.message=1`、`mail.activity=1`、`ir.attachment=1`
  已删除，cleanup 后 `remaining messages/activities/attachments=0`。

F20 localization closure:

- P26 本地化缺口已关闭：契约组装不再让语言无关的 `app.model.config`
  缓存字段定义覆盖当前用户语言的 `fields_get()` 结果。运行时字段显示名、
  selection labels 优先来自当前真实用户上下文。
- Form parser 的 statusbar states 构造不再只识别字段名 `state`；
  对 `lifecycle_state` 等任意 selection 状态字段也按字段元数据构造状态列表。
- 新增真实浏览器验收：
  `scripts/verify/form_localization_acceptance.js`。
- 真实浏览器证据：
  `artifacts/form-localization/20260430T135607/summary.json`。
  覆盖：
  - M1 `project.project/771`，`wutao`，状态条 DOM 为
    `草稿/在建/停工/竣工/结算中/保修期/关闭`。
  - M2 `payment.request/28489`，`wutao`，契约与 DOM 为
    `草稿/提交/审批中/已批准/已驳回/已完成/已取消`。
  - M3 `purchase.order/9`，`caisiqi`，契约与 DOM 为
    `询价/发送询价/待批准/采购订单/已锁定/已取消`，不再泄漏
    `RFQ/Purchase Order/Locked/Cancelled`。
- 验收结果：`pass=true`，`english_leak=false`，console errors 为 `0`。

F20 follow-up M4 field label localization closure:

- M4 `sc.legacy.receipt.income.fact` 只读投影在当前验收中暴露 P26 缺口：表单业务值可见，
  但字段标签仍为英文模型默认值，如 `Document Date`、`Document No`、
  `Source Family`、`Income Category`。
- 根因：该历史事实模型字段未声明中文 `string`，视图也未覆盖字段 `string`，后端契约只能下发英文字段元数据。
- 修复：`sc.legacy.receipt.income.fact` 模型字段补齐中文业务标签，`_description`
  收口为 `历史收款收入事实`；前端无改动。
- 验收增强：
  - `scripts/verify/form_m4_legacy_readonly_acceptance.js` 新增 `M4-P26` 字段标签中文断言。
  - `scripts/verify/form_localization_acceptance.js` 从 M1-M3 状态条本地化扩展到 M4 字段标签本地化。
- 真实浏览器证据：
  - M4 专项：`artifacts/form-m4-legacy-readonly/20260501T012931/summary.json`，
    `pass=true`，`M4-P26=pass`，console errors 为 `0`。
  - P26 总体验收：`artifacts/form-localization/20260501T013238/summary.json`，
    `P26-M1/P26-M2/P26-M3/P26-M4` 全部 `pass`。
- 运行时要求：字段元数据变更必须升级 `smart_construction_core` 并重启 Odoo 后验收。

F21 accessibility/control reachability closure:

- P27 已纳入真实浏览器验收：新增
  `scripts/verify/form_accessibility_acceptance.js`，覆盖自定义 form 关键控件的
  可访问名称、Tab 焦点路径、关系搜索弹窗 Escape/关闭/选择按钮语义，以及 chatter
  活动 composer 的提交禁用/启用状态。
- 修复关系搜索弹窗键盘闭环：弹窗打开后焦点进入搜索输入框；同时在弹窗打开期间注册
  document-level Escape 监听，避免焦点仍停留在触发按钮时 Escape 无法关闭弹窗。
  该改动只属于通用弹窗可达性，不引入任何业务判断。
- 真实浏览器证据：
  `artifacts/form-accessibility/20260430T140647/summary.json`。
  `wutao` 打开 `project.project/771` 后，P27 四个场景全部 `pass`：
  `named_control_semantics`、`keyboard_tab_reaches_critical_controls`、
  `relation_dialog_escape_close_select_semantics`、
  `chatter_activity_composer_disabled_semantics`。
- 验收结果：`pass=true`，console errors 为 `0`。

F22 visual containment closure:

- P28 已纳入真实浏览器验收：新增
  `scripts/verify/form_visual_containment_acceptance.js`，覆盖桌面、平板、手机
  viewport 下的项目表单与关系搜索弹窗截图。
- 验收规则检查视口级横向溢出、关键控件自身裁剪、无效尺寸、异常重叠、弹窗是否在当前
  viewport 内；状态条和关系表格这类契约允许横向滚动的控件按滚动容器处理。
- 真实浏览器证据：
  `artifacts/form-visual-containment/20260430T141142/summary.json`。
  覆盖：
  - desktop `1440x980`
  - tablet `900x1180`
  - mobile `390x844`
- 每个 viewport 均产出 `*_form.png` 与 `*_relation_dialog.png` 截图；
  三套 viewport 均 `pass`。
- 验收结果：`pass=true`。

F16 payment completion closure:

- `done` 不再要求用户先通过只读付款记录表格手工登记台账；后端完成动作负责在需要时自动生成
  `payment.ledger`。
- 未足额付款从阻断改为 advisory：`P0_PAYMENT_NOT_FULLY_PAID`，
  `suggested_action=complete_payment_execution`。
- `payment.ledger` 在 `payment_soft_gate` 下继承审批人已接受的结算状态风险；
  若开启 `sc.payment.force_block.p0_payment_settlement_not_ready`，仍可恢复强阻断。
- 真实浏览器证据：
  `artifacts/form-m2-payment-request/20260430T125842/summary.json`。
  `wutao` 提交、`chenshuai` 审批后，`done` 契约返回
  `allowed=true/reason_code=OK`，advisory codes 包含
  `P0_PAYMENT_NOT_FULLY_PAID/P0_PAYMENT_SETTLEMENT_NOT_READY/P0_PAYMENT_FUNDING_NOT_READY`；
  execute `done` 返回 `200/OK` 且 `payment_request.state=done`。
- 数据卫生：验收自动生成的 `payment.ledger/12195` 已删除，`payment.request/28489`
  恢复 `draft/no`，review 数为 `0`，测试附件为 `0`。

F15 approved state and done prerequisite correction:

- 审批人直接通过后，业务事实应落为 `state=approved` 与
  `validation_status=validated`，不能停留在中间态 `approve`。
- `done` 动作的不可用原因从泛化 `BUSINESS_RULE_FAILED` 收敛为
  `P0_PAYMENT_NOT_FULLY_PAID`，并给出
  `suggested_action=complete_payment_execution`。
- `P0_PAYMENT_NOT_FULLY_PAID` 已纳入 shared reason meta，避免前端从字段或错误文本判断完成动作原因。
- 真实浏览器证据：
  `artifacts/form-m2-payment-request/20260430T125319/summary.json`。
  `wutao` 提交、`chenshuai` 审批后，execute 返回
  `payment_request.state=approved`；随后 `done` 契约返回
  `allowed=false/reason_code=P0_PAYMENT_NOT_FULLY_PAID/suggested_action=complete_payment_execution`。
- 数据卫生：验收后 `payment.request/28489` 已恢复 `draft/no`，review 数为 `0`，
  测试附件为 `0`。

F23 M3 purchase order line lifecycle closure:

- M3 `purchase.order` 明细行已从表面可达推进到真实办理闭环，覆盖
  `P12/P13/P20/P23`。
- 后端 `api.data` 写入运行时在处理 one2many 新增子记录时补齐后端事实：
  inverse 父记录、`company_id/currency_id/partner_id`、`date_planned`，以及
  用户选择 `product_id` 后的采购单位 `product_uom`。这些字段不要求前端从隐藏列或
  Odoo 约束中推导。
- 前端表单编辑态只提交脏字段；one2many 已有行从整行脏改为字段级脏。新增行仍提交整行，
  已有行只提交用户实际改过的单元格，避免把 `#id` 这类显示占位写回业务字段。
- 非创建态必填校验只验证本次提交 payload 中包含的字段，避免编辑少数字段时被未触碰的
  历史必填字段阻断。
- 真实浏览器证据：
  `artifacts/form-m3-purchase-order-line/20260430T144957/summary.json`。
  `caisiqi` 在自定义 `purchase.order` 表单中新增采购明细，输入产品、描述、数量、单价；
  保存后重开读库确认 `product_id=1`、`product_uom=7`、数量和单价持久化；随后编辑数量/单价、
  保存、重开读库确认变化；最后移除明细并确认订单行为空。
- 验收结果：所有业务检查 `pass`；公开 `api.data.unlink` 对 `purchase.order` 按删除策略返回
  `403/DELETE_POLICY_DENIED`，该预期 403 被记录为非行动项，`actionable_console_errors=0`。
- 数据卫生：验收临时 `purchase.order/46` 已通过 Makefile Odoo shell 删除，remaining 为 `[]`。

F24 M5 dictionary maintenance closure:

- M5 `sc.dictionary` 配置维护表单已覆盖 `P03/P04/P05/P20/P23`。
- 新增真实浏览器验收：
  `scripts/verify/form_m5_dictionary_maintenance_acceptance.js`。
- 创建态表单按后端契约显示业务维护字段 `字典类型/编码/名称/排序`，不显示
  `ID/创建人/创建时间/最后更新人/最后更新时间` 等审计技术字段；`active` 由后端默认
  `True` 承载。
- `wutao` 在浏览器中创建临时字典记录后，脚本通过 `api.data` 读库确认
  `name/code/type/active` 持久化；随后打开同一记录编辑名称并再次读库确认。
- 重复 `code + type` 创建触发后端唯一约束，前端显示友好错误
  `已有相同记录，请先搜索并选择已有记录；如确需新建，请使用不同名称。`，
  未暴露 `duplicate key/psycopg2/Traceback/DETAIL` 技术细节，也未产生第二条记录。
- 真实浏览器证据：
  `artifacts/form-m5-dictionary-maintenance/20260430T154519/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 公开 `api.data.unlink` 对 `sc.dictionary` 按删除策略返回
  `403/DELETE_POLICY_DENIED`，验收临时 `sc.dictionary/11` 已通过 Makefile Odoo shell 删除，
  remaining 为 `[]`。

F25 M4 legacy readonly projection closure:

- M4 `sc.legacy.receipt.income.fact` 历史事实投影已覆盖 `P02/P05/P23/P25` 的只读办理路径。
- 原生 form 根节点 `create="0" edit="0" delete="0"` 已作为后端契约事实进入
  `views.form.capabilities`，并由治理层收敛到 `permissions.effective.rights` 与
  `render_profile=readonly`；前端不再需要从模型名或字段状态推断历史事实页面是否只读。
- 真实浏览器验收：
  `scripts/verify/form_m4_legacy_readonly_acceptance.js`。
  `wutao` 打开 `sc.legacy.receipt.income.fact/7220` 后，页面显示
  `DKQR-20221010-005`、`刘伟零星工程项目`、`刘伟`、`legacy_receipt_income_asset_v1`
  等持久化业务事实。
- 自定义表单无启用的输入控件和保存动作；刷新与直接深链恢复后仍显示同一历史事实。
  直接访问 `/f/sc.legacy.receipt.income.fact/new?action_id=561` 不暴露可用创建流程。
- 真实浏览器证据：
  `artifacts/form-m4-legacy-readonly/20260430T155818/summary.json`。
  验收结果 `pass=true`，console errors 为 `0`。
- 后续 P26 补充：字段标签中文化已通过
  `artifacts/form-m4-legacy-readonly/20260501T012931/summary.json` 复验，
  M4 只读投影覆盖范围更新为 `P02/P05/P23/P25/P26`。

F26 P24 real browser concurrency conflict closure:

- P24 不再仅以 `record_version` 契约存在作为通过条件；本轮新增真实浏览器 stale-save
  验收：
  `scripts/verify/form_concurrency_conflict_acceptance.js`。
- 验收使用 M5 `sc.dictionary` 临时记录，两个真实浏览器上下文同账号同时打开同一记录：
  第二页先保存名称变更，第一页在未刷新状态下继续保存旧版本 token。
- 后端 `api.data` 根据 `if_match/write_date` 拒绝第一页 stale write，返回
  `RECORD_VERSION_CONFLICT` 与用户友好提示
  `数据已被其他操作更新，请重新加载后再保存。`；页面不暴露
  `Traceback/psycopg2/Internal Server Error`。
- 读库确认 stale 页面的保存未覆盖第二页结果，避免 silent overwrite。
- 真实浏览器证据：
  `artifacts/form-concurrency-conflict/20260430T171005/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 数据卫生：验收临时 `sc.dictionary/14` 已通过 Makefile Odoo shell 删除，
  cleanup 后 `remaining=[]`。

F27 P06 primitive field widget closure, batch A:

- P06 已新增首批真实浏览器验收：
  `scripts/verify/form_primitive_fields_acceptance.js`。
- 本批只关闭安全可写的基础字段子集：
  - M5 `sc.dictionary`: `char`、`integer`、`selection`
  - M1 `project.project/771`: `boolean` favorite widget
- `sc.dictionary` 创建页按后端契约渲染 `名称/编码/字典类型/排序`：
  `名称/编码` 为文本输入，`排序` 为 number 输入，`字典类型` 为 select 且 option
  文案来自后端 selection labels。
- 浏览器创建临时字典记录后，读库确认 `name/code/type/sequence` 持久化；随后编辑
  `name/type/sequence`，刷新打开后显示值与读库一致。
- `active/启用` 未纳入 M5 创建页验收，因为该字段在当前契约中不显示，默认值由后端承载；
  boolean 子路径改用项目详情页 `is_favorite` 星标控件验证，点击后读库确认布尔值改变，再点击恢复原值。
- 真实浏览器证据：
  `artifacts/form-primitive-fields/20260430T171818/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 数据卫生：验收临时 `sc.dictionary/16` 已通过 Makefile Odoo shell 删除，
  cleanup 后 `remaining=[]`；`project.project/771.is_favorite` 已恢复脚本执行前状态。
- Remaining P06 subtypes: `text/html/float/monetary/date/datetime` 仍需在对应 M2/M3/M4
  安全样本中继续补齐，不在本批宣称完成。

F28 P06 primitive field widget closure, batch B:

- P06 第二批真实浏览器验收已补齐：
  `scripts/verify/form_primitive_numeric_date_acceptance.js`。
- 本批以 `project.cost.ledger` 为安全可清理样本，关闭原始字段子集：
  - `date`: `发生日期`
  - `float`: `数量`
  - `monetary`: `金额`
  - 同场景顺带验证 `备注/摘要` 普通文本输入保存回读，但当前模型字段为 `Char`，
    不声明覆盖 Odoo `text/html` 字段类型。
- 验收先通过后端契约/API 创建受控 `project.cost.code`、`project.cost.period`、
  `project.cost.ledger` fixture，再由真实浏览器打开
  `/r/project.cost.ledger/<id>?action_id=511` 执行用户编辑。
- 页面控件形态确认：
  `发生日期` 为 `input[type=date]`，`数量/金额` 为 `input[type=number]`。
- 用户编辑 `发生日期=2099-10-11`、`数量=2.75`、`金额=166.88` 后保存成功；
  读库和刷新重开表单均确认值一致，覆盖 `P06/P04/P23`。
- 真实浏览器证据：
  `artifacts/form-primitive-numeric-date/20260430T190139/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 数据卫生：公开 `api.data.unlink` 对成本台账相关模型按删除策略返回预期
  `403/DELETE_POLICY_DENIED`；验收临时 `project.cost.ledger/2`、
  `project.cost.period/4`、`project.cost.code/4` 已通过 Makefile Odoo shell 删除。
  成本台账保存时由模型重算生成的自动期间 `project.cost.period/5` 也已确认无台账引用后删除。
  更早失败尝试留下的 `P06B%` 残留已按台账、期间、成本科目依赖顺序清理，并显式
  `env.cr.commit()` 后独立确认 remaining 为 `[]`。
- Remaining P06 subtypes: `text/html/datetime` 仍需在后续安全样本中补齐，不在本批宣称完成。

F29 P06 primitive field widget closure, batch C:

- P06 第三批真实浏览器验收已补齐：
  `scripts/verify/form_primitive_text_datetime_acceptance.js`。
- 本批以 `sc.construction.diary` 为安全可清理样本，关闭原始字段子集：
  - `datetime`: `日志日期`
  - `text`: `日志内容`、`单据说明`、`备注`
- 本轮暴露并修复前端通用字段渲染缺口：`text/html` 字段不应落成单行 input；
  `FormSection` 现在按字段类型将 `text/html` 渲染为多行 `textarea`，前端仍只消费后端字段类型契约。
- 验收先通过后端契约/API 创建受控 `sc.construction.diary` fixture，再由真实浏览器打开
  `/r/sc.construction.diary/<id>?action_id=610` 执行用户编辑。
- 页面控件形态确认：
  `日志日期` 为 `input[type=datetime-local]`，`日志内容/单据说明/备注` 为 `textarea`。
- 用户编辑 `日志日期=2099-11-12T09:35` 与三处文本字段后保存成功；
  读库确认 `date_diary=2099-11-12 09:35:00` 且三处文本持久化，刷新重开表单显示一致，覆盖 `P06/P04/P23`。
- 真实浏览器证据：
  `artifacts/form-primitive-text-datetime/20260430T212650/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 数据卫生：公开 `api.data.unlink` 对 `sc.construction.diary` 按删除策略返回预期
  `403/DELETE_POLICY_DENIED`；验收临时 `sc.construction.diary/5665` 已通过 Makefile
  Odoo shell 删除并显式 `env.cr.commit()`，独立确认 remaining 为 `[]`。
F30 P06 primitive field widget closure, batch D:

- P06 最后一批真实浏览器验收已补齐：
  `scripts/verify/form_primitive_html_acceptance.js`。
- 本批以 `project.project/771.description` 为 `html` 字段样本。该字段位于项目详情页
  notebook 的 `描述` 页签内；验收必须先切换页签再操作，避免误判字段未交付。
- 页面控件形态确认：
  `描述` 按字段类型契约渲染为 `textarea`。
- 用户编辑 HTML 内容
  `<p>P06D edited project html ...</p><ol><li>line A</li><li><strong>line B</strong></li></ol>`
  后保存成功；读库确认 HTML 标签持久化，刷新重开并再次切换 `描述` 页签后显示一致，覆盖
  `P06/P04/P23`。
- 真实浏览器证据：
  `artifacts/form-primitive-html/20260430T213742/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 数据卫生：验收前 `project.project/771.description` 为空；脚本在 finally 中通过
  `api.data` 恢复原值，artifact 显示 `restored=true`。随后 Makefile Odoo shell 独立确认
  `description=''` 且不含 `P06D edited project html`。
- P06 primitive field matrix status: `char/integer/selection/boolean/date/float/monetary/datetime/text/html`
  均已有真实浏览器控件形态、保存、刷新和读库证据；P06 本轮关闭。

F31 P01 entry routing closure:

- P01 已新增真实浏览器入口路由验收：
  `scripts/verify/form_entry_routing_acceptance.js`。
- 本批以 `project.project` 项目台账为典型业务办理页，覆盖真实用户常用入口：
  - 直接记录 URL：`/r/project.project/771?menu_id=353&action_id=506`
  - 动作列表入口：`/a/506?menu_id=353`
  - 列表行点击打开记录：`/a/506` 第一行进入 `/r/project.project/514`
  - 详情页 smart button：`投标管理` 跳转到 `/a/538?menu_id=358&action_id=538`
  - 关系字段 `项目管理员` 的 `搜索更多` 弹窗：加载关系列表、选择行、回填输入框并关闭弹窗
- 验收只读执行；关系弹窗回填后不保存主表单，最终重新打开原记录，避免写入业务数据。
- 真实浏览器证据：
  `artifacts/form-entry-routing/20260430T214815/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- P01 closure rule: custom route/action/dialog entries must arrive at the declared business surface
  and must not silently create a different form/list surface.

F32 P03 create entry surface closure:

- P03 已新增真实浏览器创建入口验收：
  `scripts/verify/form_create_entry_acceptance.js`。
- 本批覆盖两个 create surface 入口，不执行保存，避免写入业务数据：
  - 项目台账列表点击 `新建`，进入 `/f/project.project/new?menu_id=353`
  - 项目详情页 `客户` many2one 点击 `新建并维护`，进入
    `/f/res.partner/new?action_id=314&view_mode=form&return_field=partner_id&return_model=project.project&return_action_id=506&return_menu_id=353`
- 项目创建页显示保存动作、业务字段 `名称/任务名称/客户/标签/项目管理员/安排的日期/投标记录`，
  且 `名称` 按契约显示 required；`ID/创建人/创建时间/最后更新人/最后更新时间`
  未泄漏到创建表单。
- 关系 create-and-edit 页显示 `名称` 与保存动作，return 参数完整，技术字段未泄漏。
  本轮独立 Odoo shell 确认 `res.partner.name` 当前模型事实为 `required=False`，
  因此关系创建页不显示 required 星号不是缺口。
- 真实浏览器证据：
  `artifacts/form-create-entry/20260430T215301/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。

F33 P04 discard unsaved edit closure:

- P04 在已有保存/刷新/读库证据基础上，补齐 `放弃未保存改动` 真实浏览器验收：
  `scripts/verify/form_edit_discard_acceptance.js`。
- 本批先修复契约缺口：后端 form contract 新增 `views.form.ui_labels`
  (`save/saving/discard/reload/save_success`)，前端只消费该契约渲染普通表单的放弃动作。
- 验收流程：
  - 读库确认 `project.project/771.name = Role Smoke User`
  - 浏览器打开项目详情页，将 `名称` 输入框改为 `P04 discard should not persist ...`
  - 页面出现契约标签 `放弃`，点击后重新加载原记录
  - 输入框恢复 `Role Smoke User`，读库仍为 `Role Smoke User`
- 真实浏览器证据：
  `artifacts/form-edit-discard/20260430T215910/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 数据卫生：脚本未调用保存；读库确认临时编辑值未持久化。

F34 P07 many2one quick-input edge closure:

- P07 在已有单匹配快速回填证据基础上，补齐多匹配与清空边界验收：
  `scripts/verify/form_relation_quick_input_edge_acceptance.js`。
- 多匹配路径：
  - 后端 `api.data` 先确认 `res.partner` 关键词 `公司` 有多个候选。
  - 真实浏览器在项目详情页 `客户` 字段输入 `公司` 并回车。
  - 自定义页不误填任一客户，打开 `客户：搜索更多` 弹窗，表头为
    `名称/完整名称/工作职位/电话/手机/电子邮件`，`选择` 初始 disabled。
- 清空路径：
  - 项目详情页 `项目管理员` 初始值为 `Demo Project User`。
  - 用户清空输入框后出现 `保存/放弃`，但不保存。
  - 点击 `放弃` 后输入框恢复 `Demo Project User`，读库确认
    `project.project/771.user_id` 仍为 `[109, "Demo Project User"]`。
- 真实浏览器证据：
  `artifacts/form-relation-quick-input-edge/20260430T220443/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 数据卫生：脚本未保存主表单；清空动作通过 `放弃` 恢复，读库确认未持久化。

F35 P08 relation dialog create-and-edit closure:

- P08 在已有搜索更多 cancel/select 证据基础上，补齐弹窗 `新建` 入口：
  `scripts/verify/form_relation_dialog_create_entry_acceptance.js`。
- 本批暴露并修复通用前端缺口：
  `create_mode=page` 的关系弹窗 `新建` 不应要求用户先输入关键词；只有
  quick-create 模式才需要名称。前端现在按契约 create mode 分流。
- 验收流程：
  - 打开项目详情页 `客户：搜索更多`
  - 弹窗表头为 `名称/完整名称/工作职位/电话/手机/电子邮件`
  - footer 按钮为 `选择(disabled)/新建/取消`
  - 点击 `新建` 进入 `/f/res.partner/new?action_id=314&view_mode=form`
  - 创建页携带 `return_field=partner_id`、`return_model=project.project`、
    `return_action_id=506`、`return_menu_id=353`
  - 创建页显示 `名称` 与 `保存`，技术字段未泄漏
- 真实浏览器证据：
  `artifacts/form-relation-dialog-create-entry/20260430T220856/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 数据卫生：脚本只进入创建页，不保存 `res.partner`。

F36 P09 deferred relation create on main save closure:

- P09 在已有“无匹配输入不提前创建”证据基础上，补齐主表单保存触发创建的真实闭环：
  `scripts/verify/form_relation_deferred_create_save_acceptance.js`。
- 验收流程：
  - 生成唯一客户名 `P09 Deferred Partner ...`
  - 输入到项目详情页 `客户` many2one 字段并 blur
  - 浏览器显示 `保存时创建“...”`，且后端 `res.partner` 精确查询仍为空
  - 点击主表单 `保存`
  - 后端创建 1 条 `res.partner`，项目 `partner_id` 关联到该新记录
  - finally 恢复项目原 `partner_id`，再按 delete policy 删除临时 partner
- 真实浏览器证据：
  `artifacts/form-relation-deferred-create-save/20260430T222029/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 数据卫生：`project.project/771.partner_id` 已恢复为 `false`，临时 `res.partner/8070`
  已通过 `api.data.unlink` 删除，`remaining_partners=[]`。

F37 P10 many2many multi-select closure:

- P10 在已有单个 many2many tag 选择/移除/刷新证据基础上，补齐 `select multiple`
  真实浏览器验收：
  `scripts/verify/form_many2many_multi_select_acceptance.js`。
- 验收流程：
  - 创建两个临时 `project.tags`
  - 项目详情页 `标签` many2many 控件一次选中两个 option
  - 点击保存并刷新重开项目
  - 页面 tag 列表显示两个临时标签，读库 `project.project/771.tag_ids` 包含两个 id
  - 再通过浏览器恢复原始 tag 集合并保存，刷新后页面和读库均不再包含临时标签
  - finally 再次恢复原始 tag 集合，并通过 `api.data.unlink` 删除两个临时标签
- 真实浏览器证据：
  `artifacts/form-many2many-multi-select/20260430T222310/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 数据卫生：`project_tags_after_cleanup=[]`，临时 `project.tags/6`、`project.tags/7`
  已按 `RELATION_MAINTENANCE_DELETE_ALLOWED` 删除。

F38 P18 attachment delete policy closure:

- P18 在已有上传/下载证据基础上，补齐附件删除策略证据：
  `scripts/verify/form_attachment_delete_policy_acceptance.js`。
- 本批修复契约缺口：后端 `views.form.attachments` 显式下发 `delete` contract，
  包含 `intent=api.data.unlink`、`model=ir.attachment`、`enabled=false` 和
  `delete_policy.reason_code=DELETE_POLICY_DENIED`。
- 真实浏览器打开 `project.project/771`：
  - 附件上传入口可见
  - 页面不展示 `.native-attachment-delete`
  - `api.data.unlink` 对 `ir.attachment` 的 dry-run 删除返回 403
    `DELETE_POLICY_DENIED`
- 真实浏览器证据：
  `artifacts/form-attachment-delete-policy/20260430T222818/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 数据卫生：dry-run 删除，无附件或业务记录写入。

F39 P17 log note closure:

- P17 在已有发送消息与活动调度证据基础上，补齐 `记录备注` 专项路径：
  `scripts/verify/form_chatter_note_acceptance.js`。
- 真实浏览器打开 `project.project/771`：
  - chatter actions 显示 `发送消息/记录备注/活动` 且均 enabled
  - 点击 `记录备注` 后填写唯一备注内容并提交
  - 时间线回显该备注内容，无 console/page error
- 数据库独立校验：
  - `mail.message` 写入 subtype 为 `mail.mt_note`
  - 验收备注随后通过 Makefile Odoo shell 删除
  - `remaining_note_acceptance_messages=0`
- 真实浏览器证据：
  `artifacts/form-chatter-note/20260430T223635/summary.json`。
  验收结果 `pass=true`，`console_errors=0`。
- 显示语义闭环：`chatter.timeline` 现在由后端解析 `mail.mt_note`，返回
  `typeLabel=备注` 与 `subtype=mail.mt_note`；普通评论仍返回 `typeLabel=评论`。
  前端只渲染后端 label，不按 subtype 或点击按钮来源自行判断。

F40 P25 navigation recovery closure:

- P25 在已有 M2-M5 reload/deep-link 证据基础上，补齐 M1 项目详情页专项恢复路径：
  `scripts/verify/form_navigation_recovery_acceptance.js`。
- 真实浏览器验收范围：
  - 已登录用户打开 `project.project/771` 后刷新页面，仍回到同一详情页且状态条、输入控件可见
  - 从项目台账列表进入详情页后执行浏览器 Back/Forward，列表和详情页均可恢复
  - 未登录状态直接访问详情页深链，路由跳转到 `/login?redirect=...`，登录后回到原
    `project.project/771?menu_id=353&action_id=506`
- 真实浏览器证据：
  `artifacts/form-navigation-recovery/20260430T224314/summary.json`。
  验收结果 `pass=true`，`console_errors=0`。
- 数据卫生：本批只读浏览器导航恢复，不执行保存、不创建、不删除业务记录。

F41 P15 status transition closure:

- P15 在已有状态条可见证据基础上，补齐安全状态推进真实办理路径：
  `scripts/verify/form_status_transition_acceptance.js`。
- 本批暴露并修复前端契约消费缺口：
  - `setStatusbarValue()` 已将后端 statusbar 字段写入 dirty 集合，但 `hasChanges`
    和保存 payload 只统计普通 layout 字段。
  - 修复后，后端 `views.form.statusbar.field` 声明的状态字段在可写时参与
    `hasChanges` 和 `collectWritableValues()`，前端不按模型名或状态名推断。
- 真实浏览器验收：
  - 真实用户 `wutao` 通过 `api.data` 创建临时 `project.project`
  - 打开临时项目详情页，点击状态条 `停工`
  - 保存按钮启用，点击保存后页面提示保存成功
  - 重开表单与读库均确认 `lifecycle_state=paused`
- 真实浏览器证据：
  `artifacts/form-status-transition/20260430T225703/summary.json`。
  验收结果 `pass=true`，`console_errors=0`。
- 数据卫生：本轮失败与成功产生的临时项目 `881/882/883/884`、伴生
  `mail.message` 与 `mail.alias` 已通过 Makefile Odoo shell 删除，
  `remaining_p15_status_projects=0`。

F42 P24 conflict recovery closure:

- P24 在已有 stale save 拒绝证据基础上，补齐冲突后的用户恢复与继续保存路径：
  `scripts/verify/form_concurrency_conflict_acceptance.js`。
- 验收流程：
  - 创建临时 `sc.dictionary`
  - 两个真实浏览器上下文打开同一记录
  - 第二页先保存名称变更
  - 第一页基于旧 `record_version` 保存，被后端 `RECORD_VERSION_CONFLICT` 拒绝
  - 第一页点击 `放弃`，重新加载到第二页已保存的最新名称
  - 第一页再次修改名称并保存成功，读库确认新名称持久化
- 真实浏览器证据：
  `artifacts/form-concurrency-conflict/20260430T230226/summary.json`。
  验收结果 `pass=true`，`actionable_console_errors=0`。
- 数据卫生：验收临时 `sc.dictionary/18` 已通过 Makefile Odoo shell 删除；
  前一轮失败残留 `13/14/17` 也已清理；`remaining_p24_dictionary=0`。

F43 P16 smart button overflow closure:

- P16 在已有 smart/stat 按钮导航证据基础上，补齐原生 `更多` overflow 形态与
  自定义渲染对齐证据：`scripts/verify/form_smart_button_overflow_acceptance.js`。
- 本批暴露并修复前端通用渲染缺口：
  - 自定义页此前把超过原生直显数量的 smart button 直接展开为平铺按钮。
  - `NativeFormTreeRenderer` 现在对后端 layout/action 契约声明的 smart button
    group 使用通用 overflow 形态：前 4 个直显，剩余入口进入 `更多` 菜单。
  - 前端不新增业务语义判断；按钮 label/action 仍全部来自后端契约。
- 真实浏览器对比：
  - 原生直显：`执行结构/工程量清单/预算/成本/合同/更多`
  - 原生 `更多`：`物资/采购/结算/财务/0投标`
  - 自定义直显：`执行结构/工程量清单/预算/成本/合同/更多`
  - 自定义 `更多`：`物资/采购/结算/财务/投标管理`
- 真实浏览器证据：
  `artifacts/form-smart-button-overflow/20260430T231612/summary.json`。
  验收结果 `pass=true`，native/custom console errors 均为 `0`。
- 数据卫生：本批只读浏览器对比，不创建、不保存、不删除业务记录。

F44 P19 body action safety closure:

- P19 在已有 body/notebook 按钮可见证据基础上，补齐按钮安全语义与执行保护闭环：
  `scripts/verify/form_body_action_safety_acceptance.js`。
- 本批暴露的缺口：
  - 运行时未加载后端解析改动时，主 `ui.contract action_open` 中 body button
    没有 `action_safety`，前端没有契约输入，危险对象按钮会继续执行。
  - 这不是前端选择器问题，根因是后端视图解析契约未进入当前 prod-sim 运行时。
- 收口结果：
  - `工程量清单分析` 下发 `classification=safe`、`requires_confirm=false`。
  - `重建工程量清单层级` 下发 `classification=danger`、`requires_confirm=true`、
    `reason_code=NATIVE_BUTTON_DANGEROUS_ACTION`。
  - 前端只消费 `action_safety`：危险动作弹出确认，取消后不发送 `execute_button`；
    安全导航动作不弹确认且继续跳转。
- 真实浏览器证据：
  `artifacts/form-body-action-safety/20260430T235942/summary.json`。
  验收结果 `pass=true`，`console_errors=0`。
- 运行时要求：涉及后端 parser/contract 字段的改动必须通过 prod-sim Odoo restart/upgrade
  刷新运行时后再验收；否则新库或模拟生产验收会复现旧契约。

F45 M4 readonly projection mutation policy closure:

- M4 历史事实只读页不能只依赖前端禁用控件；公开数据办理接口也必须在 ORM
  create/write 之前读取后端 mutation policy 并拒绝只读投影模型写入。
- `smart_core.api.data` 增加 `smart_core_api_data_mutation_policy` 扩展点；
  `smart_construction_core` 对 `sc.legacy.receipt.income.fact` 声明
  `create/write` 禁止，reason code 为
  `READONLY_PROJECTION_MUTATION_DENIED`。
- 验收脚本 `scripts/verify/form_m4_legacy_readonly_acceptance.js` 已补齐
  `M4-P04/P05/P20` 探针：真实用户会话直接调用 `api.data create/write`，
  均被后端策略拒绝，且 policy source 为 `smart_construction_core`。
- 真实浏览器证据：
  `artifacts/form-m4-legacy-readonly/20260501T014935/summary.json`。
  验收结果 `pass=true`，`console_errors=0`。
- 结论：本批不是仅说明本次页面成功，而是补齐了只读投影模型在新库重建后也必须加载的
  后端执行策略；后续若历史承载模型升级为系统业务模型，必须同步复核该 mutation
  policy，明确从只读投影切换为业务模型后的 create/write 允许边界。

F46 L6 readonly projection evidence correction:

- L6 代表模型回归暴露验收脚本口径缺口：M4 `sc.legacy.receipt.income.fact`
  页面实际已渲染历史事实文本，但通用脚本只把 input/readonly class/statusbar/o2m
  计为 surface，遗漏只读投影的文本化业务事实 surface。
- `form_model_tier_acceptance.js` 与 `form_model_error_recovery_acceptance.js`
  已补齐只读投影判定：当后端契约声明 `read=true/create!=true/write!=true`，
  且页面文本包含模型业务标题与足量业务事实时，计为可渲染只读 surface。
- 真实浏览器证据：
  - `artifacts/form-native-custom-gap/20260501T015209/summary.json`：原生/自定义结构差异审计 PASS。
  - `artifacts/form-model-tier/20260501T015815/summary.json`：M2-M5 surface reachability PASS。
  - `artifacts/form-model-error-recovery/20260501T020124/summary.json`：P20/P24/P25 across M2-M5 PASS。
- 失败基线保留：
  `artifacts/form-model-tier/20260501T015238/summary.json` 与
  `artifacts/form-model-error-recovery/20260501T015238/summary.json`
  证明旧脚本口径会误判 M4 只读投影。
