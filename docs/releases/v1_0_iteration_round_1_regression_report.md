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
- `make verify.phase_next.evidence.bundle`：FAIL（环境超时）
- `make demo.load.release DB_NAME=sc_demo`：PASS（发布态种子加载成功）
- `make verify.demo.release.seed DB_NAME=sc_demo`：PASS（发布态种子验收通过）

失败信息：

- `[role_capability_floor_prod_like] FAIL`
- `admin session setup failed: <urlopen error timed out>`

复现结果：同命令重试 1 次，失败一致。

## 3. 影响评估

- 本轮“产品表达层”改动未破坏前端构建、严格类型检查、项目驾驶舱 contract 校验。
- `phase_next.evidence.bundle` 失败属于环境连通/会话初始化超时，不属于本轮页面表达改动直接引入。

## 4. 建议

1. 在可稳定访问的环境重跑：`make verify.phase_next.evidence.bundle`。
2. 若仍失败，优先排查：
   - Admin session 初始化链路
   - URL 连通性与超时阈值
3. 当前分支先保留“产品表达验证”状态，不立即发版。

## 5. 发布态 Demo 种子验收要点（固定章节）

- 目标：确保演示数据是“可重复加载 + 可自动验收”的发布态基线。
- 加载命令：`make demo.load.release DB_NAME=sc_demo`
- 验收命令：`make verify.demo.release.seed DB_NAME=sc_demo`
- 最低通过标准：
  - 展厅项目覆盖正常；
  - `project_id=20` 合同/成本/资金不为空；
  - 发布态角色用户（含 `svc_e2e_smoke`）齐全。
