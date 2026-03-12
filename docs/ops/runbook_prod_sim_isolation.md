# prod-sim 隔离验证 Runbook

本 runbook 用于在本地/测试环境快速确认 `prod-sim` 与默认开发环境隔离是否正常。

## 适用场景
- 发布前做一次全量环境自检
- `prod-sim` 环境疑似漂移（模块/数据/容器状态不一致）
- 日常联调时做快速回归

## 前置条件
- 当前使用非生产环境：`ENV=test` + `.env.prod.sim`
- Docker 可用，且 `sc-backend-odoo-prod-sim` 项目可启动
- 验证账号可用：`svc_e2e_smoke/demo`

## 命令
- 全量隔离验证（会 reset `sc_prod_sim`）：
  - `make verify.prod.sim.isolation`
- 快速隔离验证（不 reset，适合日常回归）：
  - `make verify.prod.sim.isolation.quick`

## 两个目标的差异
- `verify.prod.sim.isolation`
  - 执行链路：`up -> demo.reset -> odoo.recreate -> wait.odoo.ready -> verify.delivery.simulation.ready`
  - 用途：发布前、漂移排查后的强一致验证
- `verify.prod.sim.isolation.quick`
  - 执行链路：`up -> wait.odoo.ready -> verify.delivery.simulation.ready`
  - 用途：联调过程中的快速健康回归

## 产出与判定
- PASS 标志：命令末尾输出 `PASS`
- 报告文件：
  - `docs/ops/audit/delivery_simulation_report.md`
  - `artifacts/backend/delivery_simulation_report.json`

## 常见问题
- 端口占用（如 `18069`/`80`）：停止冲突容器后重试
- 登录失败：确认验证账号仍可用（`svc_e2e_smoke/demo`）
- 连接中断（服务刚重启）：重试 `quick` 目标，或先执行一次完整目标
