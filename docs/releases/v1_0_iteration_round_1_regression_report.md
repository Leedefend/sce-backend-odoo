# v1.0 Iteration Round 1 最小回归报告

## 1. 执行范围

按本轮要求执行以下最小回归命令：

1. `make verify.frontend.build`
2. `make verify.frontend.typecheck.strict`
3. `make verify.project.dashboard.contract`
4. `make verify.phase_next.evidence.bundle`

发布态 Demo 数据闭环命令（新增固定项）：

5. `make demo.load.release DB_NAME=sc_demo`
6. `make verify.demo.release.seed DB_NAME=sc_demo`

## 2. 结果

- `make verify.frontend.build`：PASS
- `make verify.frontend.typecheck.strict`：PASS
- `make verify.project.dashboard.contract`：PASS
- `make verify.phase_next.evidence.bundle`：PASS（最终复验通过）
- `make demo.load.release DB_NAME=sc_demo`：PASS（发布态种子加载成功）
- `make verify.demo.release.seed DB_NAME=sc_demo`：PASS（发布态种子验收通过）

历史失败信息（已复验关闭）：

- `[role_capability_floor_prod_like] FAIL`
- `admin session setup failed: <urlopen error timed out>`

历史复现结果：同命令重试 1 次，失败一致。

最终复验结果（2026-07-05）：

- `make verify.phase_next.evidence.bundle`：PASS
- `make verify.release.round1.final_closeout.guard`：PASS
- `make verify.release.master_stage.final_closeout.guard`：PASS

## 3. 影响评估

- 本轮“产品表达层”改动未破坏前端构建、严格类型检查、项目驾驶舱 contract 校验。
- `phase_next.evidence.bundle` 历史失败已通过最终复验关闭，不再作为发布阻塞。

## 4. 建议

1. 保持 `verify.phase_next.evidence.bundle` 纳入发布前最小回归；
2. 保持 `verify.release.round1.final_closeout.guard` 和 `verify.release.master_stage.final_closeout.guard` 纳入文档/证据闭环；
3. 后续环境超时按运行环境事件处理，不回滚本轮产品表达收口结论。

## 5. 发布态 Demo 种子验收要点（固定章节）

- 目标：确保演示数据是“可重复加载 + 可自动验收”的发布态基线。
- 加载命令：`make demo.load.release DB_NAME=sc_demo`
- 验收命令：`make verify.demo.release.seed DB_NAME=sc_demo`
- 最低通过标准：
  - 展厅项目覆盖正常；
  - `project_id=20` 合同/成本/资金不为空；
  - 发布态角色用户（含 `svc_e2e_smoke`）齐全。
