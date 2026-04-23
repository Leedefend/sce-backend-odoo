# Fresh DB 初始化分层与问题台账 v1

Status: READY_FOR_REVIEW
Date: 2026-04-23
Task: `ITER-2026-04-23-FRESH-DB-REPLAY-INIT-LAYER-ISSUE-REGISTER`

## 1. 初始化分层（平台级 / 行业级 / 用户企业级）

### A. 平台级初始化（Platform Init）
- 目标：让系统具备最小可运行能力（认证、system.init、基础导航/意图）。
- 主要模块：
  - `smart_core`（`system.init`、intent 路由、运行时契约）
  - `smart_construction_bootstrap`（环境最小配置）
- 成果判定：
  - `system.init` 可返回有效初始化载荷；
  - 具备基础管理员可登录能力。

### B. 行业级初始化（Industry Init）
- 目标：装载行业模型、流程与基础主数据，形成可承载业务数据重放的空库。
- 主要模块：
  - `smart_construction_core`
  - `smart_construction_custom`
  - `smart_construction_seed`（基线数据初始化，非 demo）
- 成果判定：
  - 业务模型字段齐备（含 replay 依赖 legacy carrier 字段）；
  - 行业必需字典/税率等先决条件可用。

### C. 用户企业级初始化（Enterprise/Tenant Init）
- 目标：装载企业组织与用户上下文（公司/部门/岗位/用户/角色），供业务数据绑定。
- 主要承载：
  - 企业主体数据与用户映射（`res.company/res.users` 及企业域对象）
  - 租户级权限与组织结构数据
- 成果判定：
  - replay payload 中的 `user_id`/企业锚点在目标库可解析；
  - 不依赖 demo 账户或脏库历史 ID。

## 2. 本次演练结论（sc_migration_fresh）

当前演练结果：**PASS**

- `fresh_db_replay_payload_precheck_result_v1.json`: PASS
- replay 写入链路：PASS（partner/project/member/contract/receipt）
- `fresh_db_replay_runner_dry_run_result_v1.json`: PASS

关键产物路径：
- `artifacts/migration/fresh_db_partner_l4_replay_write_result_v1.json`
- `artifacts/migration/fresh_db_project_anchor_replay_write_result_v1.json`
- `artifacts/migration/fresh_db_project_member_neutral_replay_write_result_v1.json`
- `artifacts/migration/fresh_db_contract_partner_12_anchor_replay_recovery_write_result_v1.json`
- `artifacts/migration/fresh_db_contract_57_retry_write_result_v1.json`
- `artifacts/migration/fresh_db_contract_missing_partner_anchor_write_result_v1.json`
- `artifacts/migration/fresh_db_contract_remaining_write_result_v1.json`
- `artifacts/migration/fresh_db_receipt_core_write_result_v1.json`
- `artifacts/migration/fresh_db_replay_manifest_execution_refresh_result_v1.json`
- `artifacts/migration/fresh_db_replay_runner_dry_run_result_v1.json`

## 3. 问题台账（本次全部记录）

### ISSUE-01: replay 依赖字段/模型缺失
- 层级：行业级初始化
- 现象：
  - `res.partner` 缺少 legacy 载体字段；
  - `project.project` 缺少 legacy 载体字段；
  - 缺少 `sc.project.member.staging` 模型；
  - `construction.contract` 缺少 `legacy_contract_id/legacy_project_id`。
- 根因：当前模块代码与迁移契约清单未完全对齐。
- 修复：补齐最小 carrier 模型/字段并升级 `smart_construction_core`。
- 预防门禁：
  - `fresh_db_replay_payload_precheck.py` 必须在写入前 PASS；
  - 将 replay 依赖字段纳入模块发布前校验脚本。

### ISSUE-02: `/mnt/artifacts` 写权限失败
- 层级：平台级运行环境
- 现象：odoo shell 写 `fresh_db_replay_payload_precheck_result_v1.json` 报 `PermissionError`。
- 根因：容器内 `odoo(uid=101)` 对挂载目录中文件无写权限。
- 修复：统一修正 `artifacts/migration` 目录与文件可写权限后重跑。
- 预防门禁：
  - 在 replay 前增加“容器写入探针”（touch+overwrite）。

### ISSUE-03: project_member payload 用户 ID 不存在
- 层级：用户企业级初始化
- 现象：`fresh_db_project_member_neutral_replay_write.py` precheck 报 `user_missing`（8/9/12/14/20）。
- 根因：fresh 库仅有 `admin(id=2)`，payload 仍引用旧库用户 ID。
- 修复：重建 adapter 产物后，对 payload 执行本轮映射（统一到目标库有效用户），并留存 remap 报告。
- 预防门禁：
  - 增加“用户锚点预检查”并阻断旧库 ID 直接入 fresh 库。

### ISSUE-04: project_member payload 项目 ID 漂移（出现 756）
- 层级：行业级/数据适配过程
- 现象：precheck 报 `project_missing project_id=756`，但项目实际上限为 755。
- 根因：中间 payload 在前序调试中出现陈旧/漂移状态。
- 修复：重跑 `fresh_db_project_member_neutral_replay_adapter.py` 重新生成 payload 后恢复。
- 预防门禁：
  - adapter 输出后立刻做 `min/max/id_exists` 校验；
  - 禁止手工长期复用旧 payload。

### ISSUE-05: 合同重放缺少默认税率
- 层级：行业级初始化（seed 基线）
- 现象：`fresh_db_contract_57_retry_write.py` 报缺少 `销项VAT 9%`。
- 根因：目标 fresh 库无对应基线税率。
- 修复：补齐税率基线后重跑，合同链路 PASS。
- 预防门禁：
  - 将税率先决条件纳入 replay 前置脚本（已可由 `fresh_db_core_tax_prereq_materialize` 类步骤固化）。

### ISSUE-06: 系统初始化模块未装载（seed 未安装）
- 层级：行业级初始化 / 用户企业级初始化
- 现象：`smart_construction_seed` 在 `sc_migration_fresh` 为 `uninstalled`，用户仅 1 个。
- 根因：本次按 no-demo 最小安装链路执行，未显式安装 seed。
- 修复：本轮通过定向补齐数据保障 replay 通过；正式部署前需明确 seed 策略（`PROFILE=base`）。
- 预防门禁：
  - 发布前清单必须显式声明：seed 是否执行、执行 profile、是否启用用户 bootstrap。

## 4. 正式部署前门禁（必须全部通过）

1. 初始化分层确认
- 平台级：`system.init`/登录/基础导航链路健康。
- 行业级：核心模块 + seed(base) 策略明确且已执行。
- 用户企业级：企业组织与用户映射完成，不依赖历史 ID。

2. 重放门禁确认
- `fresh_db_replay_payload_precheck_result_v1.json` = PASS
- 全部 replay 写入结果 JSON = PASS
- `fresh_db_replay_runner_dry_run_result_v1.json` = PASS

3. 生产执行边界
- 严格遵循 `docs/ops/codex_execution_allowlist.md`（prod 需显式授权流程）。
- seed 仅允许 `PROFILE=base`（参考 `docs/ops/seed_lifecycle.md`）。
- 执行前冻结本次产物与命令清单，避免临场漂移。

## 5. 建议的服务器正式部署顺序

1. 先跑“平台级 + 行业级 + 用户企业级”初始化预检（只读）。
2. 在目标库执行 seed(base) 与用户/企业初始化（如启用需显式参数）。
3. 执行 replay precheck。
4. 按合同顺序执行 replay 写入。
5. 刷新 manifest 并执行 runner dry-run。
6. 通过后再进入上线切流步骤。

