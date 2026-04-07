# ITER-2026-04-07-1290 Report

## Summary of execution
- 启动 fresh-runtime 防再生验证：创建新库 `sc_prod_fresh_1290`，随后执行 `smart_construction_custom` fresh 安装。
- 安装阶段失败，导致本批次进入 `FAIL` 并按规则停止。

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1290.yaml`
- PASS: `ENV=prod.sim ENV_FILE=.env.prod.sim make db.create DB=sc_prod_fresh_1290`
- FAIL: `ENV=prod.sim ENV_FILE=.env.prod.sim make mod.install MODULE=smart_construction_custom DB_NAME=sc_prod_fresh_1290`

## Failure detail
- 失败位置：`addons/smart_construction_core/data/sc_capability_group_seed.xml:55`
- 失败原因：`required_group_ids` 引用 `smart_construction_core.group_sc_cap_project_read`，但在 fresh 安装该时点该外部ID尚不可用。
- 关键报错：
  - `External ID not found in the system: smart_construction_core.group_sc_cap_project_read`
  - `ParseError while parsing ... sc_capability_group_seed.xml`

## Risk analysis
- 风险等级：`high`
- 影响：fresh-runtime 安装链被阻断，`1290` 后续验收（scene 安装、stage_gate）无法继续执行。
- 规则判定：命中 stop condition `acceptance_failed`，当前迭代必须停止。

## Rollback suggestion
- 回滚最近 seed 改动后再开修复批次：
  - `git restore addons/smart_construction_core/data/sc_capability_group_seed.xml`
  - 或在新修复任务中改为“仅恢复 install-order 必要且无前置 group 依赖”的最小 XMLID 集。

## Next iteration suggestion
- 新开 dedicated recovery batch（例如 `ITER-1291`）：
  1) 修复 `sc_capability_group_seed.xml` 的 fresh 安装前置依赖问题；
  2) 重新执行 `1290` 全链验收。
