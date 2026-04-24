# History Continuity Execution Plan v1

Status: COMPLETED_FOR_REPLAY_BASELINE

Task: `ITER-2026-04-24-HISTORY-CONTINUITY-PLAN-001`

## 批次信息

- 批次：`Batch-History-Continuity`
- 目标：
  - 让历史数据进入新系统后，用户能够在新系统继续开展业务，而不是只完成 replay 行数。
- 范围：
  - `scripts/migration/*`
  - `docs/migration_alignment/*`
  - `Makefile`
  - 与历史 replay 直接相关的 bounded write 脚本
- 不做：
  - 不触碰 `payment_settlement_accounting`
  - 不在本批把 carrier 全部提升为 runtime ownership
  - 不改前端页面消费链

## 实施步骤

### Step 1

- 操作：
  - 建立历史业务连续性专题边界，冻结 lane 适配矩阵与业务目标。
- 修改范围：
  - `docs/migration_alignment/sc_demo_replay_adaptation_matrix_v1.md`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- 输出：
  - `direct-reusable / carrier-first / fresh-db-only / blocked-high-risk` 适配矩阵

完成判据：
- `sc_demo` 可执行 lane 被明确列出
- 高风险与未完成 lane 被明确排除

### Step 2

- 操作：
  - 实现 `sc_demo` 一键演练与一键回放入口
  - 参数化允许 lane 的 DB guard 与 artifact path
- 修改范围：
  - `scripts/migration/fresh_db_*`
  - `scripts/migration/history_continuity_oneclick.sh`
  - `Makefile`
- 输出：
  - `history.continuity.rehearse`
  - `history.continuity.replay`

完成判据：
- 一条命令能完成 dry-run rehearsal
- 一条命令能完成受控 replay orchestration

### Step 3

- 操作：
  - 增加业务连续性 read-only probe
  - 输出历史数据进入 runtime/carrier 模型后的可用性证据
- 修改范围：
  - `scripts/migration/history_continuity_usability_probe.py`
  - `docs/migration_alignment/*`
- 输出：
  - continuity probe JSON/report

完成判据：
- 能清楚回答：
  - 用户
  - 项目
  - 项目成员承载
  - 合同头
  - 收款申请头
  是否已经进入新系统事实面

### Step 4

- 操作：
  - 在 `sc_demo` 完成 rehearsal
  - 输出环境级与业务级结论
- 修改范围：
  - 无新增代码，执行验证
- 输出：
  - dry-run result
  - payload precheck result
  - usability probe result

完成判据：
- rehearsal 命令可执行
- 结果可归因为：
  - ready
  - conditional
  - blocked

### Step 5

- 操作：
  - 执行真实允许 lane replay
  - 在失败 lane 上补 `legacy-first` 关系解析与断点续跑能力
- 修改范围：
  - `scripts/migration/fresh_db_*`
  - `scripts/migration/history_continuity_oneclick.sh`
- 输出：
  - `sc_demo` runtime/carrier continuity baseline

完成判据：
- `partner/project/project_member_carrier/contract/receipt` 全部进入 `sc_demo`
- continuity probe `zero_critical_counts = 0`

### Step 6

- 操作：
  - 把 23 包全量连续性从 6 个核心包扩到下一组 master anchor 包
  - 先接入 `contract_counterparty_partner_sc_v1` 与 `receipt_counterparty_partner_sc_v1`
- 修改范围：
  - `scripts/migration/history_continuity_oneclick.sh`
  - `scripts/migration/history_continuity_usability_probe.py`
  - `scripts/migration/fresh_db_*counterparty*_replay_write.py`
  - `docs/migration_alignment/*`
- 输出：
  - Group A packages enter `sc_demo`
  - continuity probe gains explicit counts for both counterparty lanes

完成判据：
- `contract_counterparty_partner_sc_v1` enters `sc_demo`
- `receipt_counterparty_partner_sc_v1` enters `sc_demo`
- one-click replay can resume from these two new steps

### Step 7

- 操作：
  - 恢复合同头原始遗留 slice/retry lane
  - 让 one-click 默认路径补齐：
    - special 12-row
    - retry 57
  - 同时把已知阻断的 Group B lanes 改成 opt-in
- 修改范围：
  - `scripts/migration/contract_12_row_*`
  - `scripts/migration/fresh_db_contract_57_retry_write.py`
  - `scripts/migration/history_continuity_oneclick.sh`
  - `docs/migration_alignment/*`
- 输出：
  - `contract_sc_v1` runtime coverage from `1332` raises to `1401`

完成判据：
- bounded payload rows present = `1344 / 1344`
- retry lane rows present = `57 / 57`
- one-click default path no longer stops at already known blocked Group B lanes

## 2026-04-25 Batch-UR-A.2

- 操作：
  - 对 `never_reached_asset_gap_91` 先做 ready/blocker 分流
  - 将其中 `56` 条 ready rows 接入正式 replay lane
  - 把 ready-only lane 纳入 one-click 默认路径
- 修改范围：
  - `scripts/migration/history_contract_unreached_ready_replay_adapter.py`
  - `scripts/migration/history_contract_unreached_ready_replay_write.py`
  - `scripts/migration/history_continuity_oneclick.sh`
  - `docs/migration_alignment/*`
- 输出：
  - `contract_sc_v1` runtime coverage from `1401` raises to `1457`

完成判据：
- ready unreached replay rows present = `56 / 56`
- effective contract runtime coverage = `1457 / 1492`
- remaining blocked unreached rows = `35`
- continuity probe = `PASS`

## 2026-04-25 Batch-UR-B.1 / UR-B.2

- 操作：
  - 从 `partner_master_v1.xml` 中回放缺失的 `4` 个 canonical partner anchors
  - 基于 `partner_master_replay_gap_4 + strong_evidence_promotion_gap_19` 构建 `23` 条合同头 recovery payload
  - 将这两条 recovery lane 纳入 one-click 默认路径
- 修改范围：
  - `scripts/migration/history_partner_master_targeted_replay_*`
  - `scripts/migration/history_contract_partner_recovery_*`
  - `scripts/migration/history_continuity_oneclick.sh`
  - `docs/migration_alignment/*`
- 输出：
  - `contract_sc_v1` runtime coverage from `1457` raises to `1480`

完成判据：
- targeted partner-master replay rows = `4 / 4`
- partner-recovered contract header rows = `23 / 23`
- effective contract runtime coverage = `1480 / 1492`
- remaining blocked rows = `12`
- continuity probe = `PASS`

## 2026-04-25 Batch-UR-B.3

- 操作：
  - 将 `direction_defer_blank_counterparty_12` 回溯到原始
    `repayment_single_counterparty` strong-evidence 分析结果
  - 为这 `12` 条补 dedicated partner targeted replay lane
  - 将这 `12` 条合同头补入正式 continuity replay
- 修改范围：
  - `scripts/migration/history_partner_master_direction_defer_replay_*`
  - `scripts/migration/history_contract_direction_defer_recovery_*`
  - `scripts/migration/history_continuity_oneclick.sh`
  - `docs/migration_alignment/*`
- 输出：
  - `contract_sc_v1` runtime coverage from `1480` raises to `1492`

完成判据：
- direction-defer partner targeted replay：`created_rows = 2`
- direction-defer contract recovery rows：`12 / 12`
- effective contract runtime coverage = `1492 / 1492`
- continuity probe = `PASS`

## 验证步骤

- verify：
  - `python3 scripts/migration/fresh_db_replay_runner_dry_run.py`
- `DB_NAME=sc_demo make history.continuity.rehearse`
- `DB_NAME=sc_demo make history.continuity.replay`
- snapshot：
  - `artifacts/migration/history_continuity/<db>/<run_id>/*`
  - `/tmp/history_continuity/<db>/<run_id>/*` (container-side Odoo shell outputs)
- guard：
  - prod forbid
  - replay db allowlist
  - high-risk lane exclusion
- smoke：
  - continuity usability probe

## Final Outcome

- `contract_sc_v1` runtime coverage: `1492 / 1492`
- `legacy_receipt_income_sc_v1`: `7220 / 7220`
- `legacy_expense_deposit_sc_v1`: `11167 / 11167`
- `legacy_invoice_tax_sc_v1`: `5920 / 5920`
- `legacy_workflow_audit_sc_v1`: `79702 / 79702`
- `DB_NAME=sc_demo make history.continuity.rehearse`: `PASS`
- 历史连续性 replay 基线已经进入“可服务器一键重放”状态

## 风险与回滚

- 风险：
  - 现有 bounded write 脚本仍可能把 artifact 输出写回固定路径
- 当前 `sc_demo` 若不是空目标，真实 replay 会因为 identity collision 被阻断
- carrier-first lane 若被错误提升，会污染运行态责任链
- receipt lane 若继续依赖 fresh-db runtime contract/project ids，会在 continuity replay 中失真
- 回滚：
  - 本批修改均为 replay orchestration / guard / doc 层，可按文件回滚
  - 不涉及高风险 accounting lane

## 停机条件

- 出现对 `payment_settlement_accounting` 的执行需求
- 发现某允许 lane 实际含有非 bounded side effect
- 需要跨到前端或业务 promotion 逻辑才能让当前批次通过
