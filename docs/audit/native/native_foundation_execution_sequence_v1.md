# 原生业务事实层七审计结果执行顺序 v1

## 目标

- 将已约定的 7 份审计结论转为可连续执行的批次顺序。
- 坚持低风险优先；涉及 `security/**`、`ir.model.access.csv`、`record_rules/**` 的项先进入高风险闸门，不直接实施。

## 顺序清单（screen 结论）

| 顺序 | 审计结果 | 当前结论 | 下一动作 | 风险级别 |
|---|---|---|---|---|
| 1 | `native_foundation_acceptance_matrix_v1.md` | 基础链路总体 PASS，需围绕阻塞项推进 | 作为总入口基线，后续每批次以此矩阵回勾验收项 | low |
| 2 | `native_manifest_load_chain_audit_v1.md` | manifest 装载链成立，暂不建议调整加载顺序 | 保持只读；仅在后续冲突证据出现时开新 screen 批次 | low |
| 3 | `native_menu_action_health_check_v1.md` | 菜单/动作静态健康，无悬挂引用 | 保持只读；将动作补丁链作为回归检查项，不先改结构 | low |
| 4 | `module_init_bootstrap_audit_v1.md` | 初始化链可解释，优先级低于运行时门禁可达性 | 保持只读；不做 bootstrap 重构 | low |
| 5 | `master_data_field_binding_audit_v1.md` | 字段绑定静态成立，暴露 `project.budget` ACL 重复风险 | 进入高风险候选池，等待专用授权任务 | high-gated |
| 6 | `role_capability_acl_rule_matrix_v1.md` | 财务规则较完整；项目/任务/预算/成本规则显式面偏弱 | 进入高风险候选池，等待专用授权任务 | high-gated |
| 7 | `native_foundation_blockers_v1.md` | 阻塞主线项需逐个清理 | 按“低风险可执行 -> 高风险闸门”拆分后续任务链 | mixed |

## 高风险闸门声明（必须先过）

1. 任何 `ir.model.access.csv` 变更：
   - 当前仓库策略默认停止；必须创建专用高风险任务契约并命中允许的窄例外。
2. 任何 `record_rules/**` 变更：
   - 当前策略默认停止；本链路不直接实施。
3. 任何 `security/**` 变更：
   - 当前策略默认停止；仅在专用 permission-governance 批次且显式授权时可进入。

## 连续执行规则（依次进行）

- 先做 low-risk：验证脚本、文档基线、阻塞归类、短链门禁。
- 再做 high-risk：仅在新建专用任务契约并满足窄例外时进入。
- 每批次必须给出：变更摘要、验证结果、风险结论、回滚建议、下一批次建议。

## 下一批建议（第 1 可执行批次）

- 开启 `ITER-2026-04-06-1181`（low-risk, execute）：
  - 目标：对 `native_foundation_blockers_v1.md` 中“非 ACL/非 record-rule”阻塞项做最小修复或验证闭环。
  - 路径：仅限 `scripts/verify/**`、`docs/ops/iterations/**`、`agent_ops/**`。
  - 验证：仅短链 `make verify.*`，不跑 CI 长链。

## 执行进度检查点

- `ITER-2026-04-06-1181`：已完成（PASS）
  - 内容：P0 legacy auth 阻塞台账语义收敛。
- `ITER-2026-04-06-1182`：已完成（PASS）
  - 内容：manifest 加载链低风险复核（只读证据）：
    - `addons/smart_core/__manifest__.py` 仍显式装载 `security/ir.model.access.csv`。
    - `addons/smart_enterprise_base/__manifest__.py` 仍显式装载 `security/ir.model.access.csv`。
    - `addons/smart_construction_core/__manifest__.py` 仍显式装载 `security/ir.model.access.csv`、`security/sc_record_rules.xml`、`security/action_groups_patch.xml`。
  - 结论：第 2 项维持“链路成立 + 不做顺序重排”的 low-risk 策略。
- `ITER-2026-04-06-1183`：已完成（PASS）
  - 内容：menu/action 健康项低风险复核（只读证据）：
    - `smart_construction_core` 菜单 action 总数 `61`，缺失引用 `0`。
    - `smart_enterprise_base` 菜单 action 总数 `4`，缺失引用 `0`。
    - 关键动作面（`ir.actions.act_window` / `ir.actions.server`）维持已审计可达状态。
  - 结论：第 3 项维持“入口健康 + 不做结构改写”的 low-risk 策略。
- `ITER-2026-04-06-1184`：已完成（PASS）
  - 内容：module init/bootstrap 健康项低风险复核（只读证据）：
    - `smart_construction_core` 仍保留 `pre_init_hook` 与 `post_init_hook` 启动链。
    - `smart_core` 继续通过 extension loader 汇聚注册贡献。
    - `smart_enterprise_base` / bundles 仍通过 `ext_facts` 注入企业启用与 bundle 信息。
  - 结论：第 4 项维持“初始化链可解释 + 暂不重构 bootstrap”的 low-risk 策略。

## 第5/6步高风险闸门筛分（screen）

- `ITER-2026-04-06-1185`：已完成（PASS, screen）
  - Step-5（`master_data_field_binding_audit_v1.md`）分类结果：
    - `project.budget` ACL 重复项修复涉及 `ir.model.access.csv`，属于高风险闸门；需专用授权任务，不在当前链直接实施。
  - Step-6（`role_capability_acl_rule_matrix_v1.md`）分类结果：
    - 项目/任务/预算/成本显式 record-rule 补齐涉及 `record_rules/**`，属于高风险闸门；需专用授权任务，不在当前链直接实施。
  - 执行决策：第 5/6 步从“实施队列”切换为“授权队列”，待用户显式授权后进入专用高风险批次。

## 高风险授权前置结论

- `ITER-2026-04-06-1186`：已完成（PASS, authorization-screen）
  - 用户已显式授权继续高风险前置批次。
  - 边界判定：当前目标（`project.budget` ACL 去重 + 项目/任务/预算/成本 record-rule 补齐）
    暂未命中仓库规则已定义的 `ir.model.access.csv` 与 `record_rules/**` 窄例外条款。
  - 执行结论：在未新增匹配例外条款或未重定向到已存在例外目标前，实施批次保持停止；
    仅允许继续治理与授权边界定义工作。

## Route A 对齐结果（existing exception mapping）

- `ITER-2026-04-06-1187`：已完成（PASS_WITH_RISK, screen）
  - 用户选择 Route A（映射到既有窄例外条款）。
  - 映射结论：当前目标未命中既有窄例外：
    - Step-5 目标为 `project.budget` ACL 重复修复，目标路径在 `addons/smart_construction_core/security/ir.model.access.csv`，
      但现有 `ir.model.access.csv` 例外条款仅覆盖特定 objective/path（主要在 `smart_enterprise_base` 或 fresh-runtime install-order 恢复场景）。
    - Step-6 目标为 `record_rules/**` 补齐，当前规则集中无对应可执行窄例外。
  - 结论：Route A 不能直接进入实施；需转 Route B（新增例外条款）或重定向目标到已存在例外范围内的任务。

## Route B 进展（exception drafting）

- `ITER-2026-04-06-1188`：已完成（PASS, draft）
  - 已产出窄例外条款草案：
    - `docs/ops/governance/native_business_fact_acl_recordrule_exception_draft_v1.md`
  - 草案内容包括：
    - 精确路径 allowlist（仅 `ir.model.access.csv` + `sc_record_rules.xml` 两个实施文件）
    - 同批验证命令
    - 超范围即停机条件
  - 下一步：待批准草案后，开启高风险 `execute` 批次实施 step-5/6 最小闭环修复。

## Route B 实施结果

- `ITER-2026-04-06-1189`：已完成（PASS, execute）
  - ACL：移除 `project.budget` 重复 manager ACL 行（`access_project_budget_user`）。
  - Record rules：补齐 `project.budget` 与 `project.cost.ledger` 最小规则闭环（read/user/manager 按项目成员域 + manager 全量）。
  - 验证：
    - `make verify.scene.legacy_auth.smoke.semantic` PASS
    - `make verify.scene.legacy_contract.guard` PASS

## 后续低风险跟进

- `ITER-2026-04-06-1190`：已完成（PASS, execute）
  - 运行 `make verify.test_seed_dependency.guard`，结果 PASS。
  - 结论：当前测试依赖面无外部 seed/demo 越界；后续可进入 seed 物化 screen 批次定义最小 install-time 范围。

## Seed 物化范围 screen

- `ITER-2026-04-06-1191`：已完成（PASS, screen）
  - 已产出 `docs/ops/governance/native_seed_materialization_scope_v1.md`。
  - 明确最小物化范围：企业主数据骨架 + 非交易字典；排除支付/结算/会计交易数据。
  - 下一步：若用户继续授权，开启专用高风险 seed execute 批次，仅触达 customer seed 模块路径。

## Seed 物化执行结果

- `ITER-2026-04-06-1192`：已完成（PASS, execute）
  - 新增 install-time 字典种子文件：
    - `addons/smart_construction_custom/data/customer_project_dictionary_seed.xml`
  - manifest 数据链已挂载：
    - `addons/smart_construction_custom/__manifest__.py` 增加 `data/customer_project_dictionary_seed.xml`
  - 验证：
    - `make verify.test_seed_dependency.guard` PASS

## Seed 可见性验收证据

- `ITER-2026-04-06-1193`：已完成（PASS, execute）
  - 新增验收证据文档：
    - `docs/audit/native/native_seed_install_visibility_evidence_v1.md`
  - 结论：manifest 挂载与 seed payload 可见性成立，依赖守卫 PASS。
