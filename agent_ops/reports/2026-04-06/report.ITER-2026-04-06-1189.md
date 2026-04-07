# ITER-2026-04-06-1189

- status: PASS
- mode: execute
- layer_target: Governance Monitoring
- module: business-fact ACL and rule closure
- risk: high
- publishability: internal

## Summary of Change

- 按 Route B 执行最小闭环修复：
  - 在 `addons/smart_construction_core/security/ir.model.access.csv` 去除 `project.budget` 重复 manager ACL 行（`access_project_budget_user`）。
  - 在 `addons/smart_construction_core/security/sc_record_rules.xml` 新增 `project.budget` 与 `project.cost.ledger` 的最小 record rules（read/user/manager）。
- 回写审计进度：
  - `docs/audit/native/native_foundation_blockers_v1.md`
  - `docs/audit/native/native_foundation_execution_sequence_v1.md`

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-06-1189.yaml`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS
- `make verify.scene.legacy_contract.guard`: PASS

## Risk Analysis

- 高风险已受控：改动仅限两处授权路径，且为最小语义闭环修复。
- 未触达：manifest、财务语义、前端路径。

## Rollback Suggestion

- `git restore addons/smart_construction_core/security/ir.model.access.csv`
- `git restore addons/smart_construction_core/security/sc_record_rules.xml`
- `git restore docs/audit/native/native_foundation_blockers_v1.md`
- `git restore docs/audit/native/native_foundation_execution_sequence_v1.md`
- `git restore agent_ops/tasks/ITER-2026-04-06-1189.yaml`
- `git restore agent_ops/reports/2026-04-06/report.ITER-2026-04-06-1189.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-06-1189.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- next suggestion: 进入后续低风险批次，验证剩余主数据 seed 与权限复杂度治理项。
