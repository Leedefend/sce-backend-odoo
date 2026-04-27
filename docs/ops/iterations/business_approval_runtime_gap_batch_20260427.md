# Business Approval Runtime Gap Batch - 2026-04-27

## Scope

- Layer Target: Domain Layer / business approval runtime
- Module: `smart_construction_core`
- Reason: 上一批已提供业务审批规则矩阵，本批补齐运行时缺口，使提交/确认动作按业务配置判断是否需要审核，并由配置的审核能力组执行审核。

## Changes

- `sc.approval.policy`
  - 新增 `is_approval_required`、`next_state_after_submit`、`assert_user_can_approve`。
  - 运行时按业务单据和公司取启用规则。
- `sc.settlement.order`
  - 提交时按规则进入 `submit` 或直接 `approve`。
  - 批准时校验审批规则中的审核能力组。
- `sc.expense.claim`
  - 提交时按规则进入 `submit` 或直接 `approved`。
  - 批准时校验审批规则中的审核能力组。
- `sc.general.contract` / `construction.contract` / `purchase.order`
  - 确认动作接入审批规则能力组校验。
  - 前端确认/完成类按钮收口到对应审批能力组。
- `sc.legacy.purchase.contract.fact`
  - 新增办理状态 `state`。
  - 新增提交、批准、已签署、取消动作。
  - 历史记录初始化为 `legacy_confirmed`，新建记录默认为 `draft`。
  - 审批规则执行状态从 `policy_only` 调整为 `document_state`。

## Verification

- `python3 -m py_compile` for changed Python files.
- `python3 -m xml.etree.ElementTree` for changed XML files.
- `git diff --check`
- `ENV=test ENV_FILE=.env.prod.sim ... make mod.upgrade MODULE=smart_construction_core`
- Runtime smoke through Odoo shell:
  - `EXPENSE_AFTER_SUBMIT=submit`
  - `EXPENSE_NON_FINANCE_APPROVE=BLOCKED:ValidationError`
  - `EXPENSE_AFTER_FINANCE_APPROVE=approved`
  - `LEGACY_PURCHASE_AFTER_SUBMIT=submit`
  - `LEGACY_PURCHASE_AFTER_APPROVE=approved`
  - `GENERAL_CONTRACT_NON_MANAGER_CONFIRM=BLOCKED:ValidationError`
  - `GENERAL_CONTRACT_AFTER_MANAGER_CONFIRM=confirmed`
  - `APPROVAL_RUNTIME_SMOKE=PASS`
- DB sync:
  - `APPROVAL_RUNTIME_DB_SYNC=PASS legacy_policy_runtime=document_state null_state_count=0`
- Restart and navigation:
  - `ENV=test ENV_FILE=.env.prod.sim ... make restart`
  - `ENV=test ENV_FILE=.env.prod.sim ... E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.menu.navigation_snapshot.container`
  - `PASS checked=143 scenes=16 trace=e1de37c6f779`

## Residual Risk

- `tier_validation` 单据仍由原分级审批机制执行；本批没有替换 tier 审批内核。
- 本批先覆盖已配置矩阵中的核心 `document_state/policy_only` 缺口；后续新增业务单据时需同步新增审批规则和动作接入。
