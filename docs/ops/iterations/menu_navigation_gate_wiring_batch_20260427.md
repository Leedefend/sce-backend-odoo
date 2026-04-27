# Menu Navigation Gate Wiring Batch 20260427

## 1. 本轮变更
- 目标：让 strict `gate.full` 在 Phase 9.8 summary 前生成最新 menu navigation field snapshot。
- 完成：
  - 在 `gate.full` strict 分支串入 `verify.menu.navigation_snapshot.container`。
  - 保持 `verify.phase_9_8.gate_summary` 作为汇总 target，不改变其独立可运行语义。
  - README 记录 strict gate 会先刷新导航字段证据。
- 未完成：未执行重型 `gate.full` 全量门禁。

## 2. 影响范围
- 模块：`Makefile`、`docs/ops/verify`、`docs/ops/iterations`
- 启动链：否
- contract/schema：否
- default_route：否
- Odoo 运行时代码：否

## 3. 风险
- P0：无，未改运行时代码。
- P1：`gate.full` strict 模式多一个 live container HTTP 验证步骤，耗时会略增。
- P2：若测试账号未配置，新增步骤会像其他 live verify 一样失败并阻断 strict gate。

## 4. 验证
- `make -n gate.full DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo`：PASS（dry-run contains `verify.menu.navigation_snapshot.container` before `verify.phase_9_8.gate_summary`）
- `git diff --check -- Makefile docs/ops/verify/README.md docs/ops/iterations/menu_navigation_gate_wiring_batch_20260427.md docs/ops/iterations/delivery_context_switch_log_v1.md`：PASS

## 5. 产物
- docs：`docs/ops/iterations/menu_navigation_gate_wiring_batch_20260427.md`

## 6. 回滚
- 方法：回退本批次提交，或从 `gate.full` strict 分支移除 `verify.menu.navigation_snapshot.container` 调用。
- 数据/升级：无需 `-u`，无需重启。

## 7. 下一批次
- 目标：继续扫描菜单规范化专题是否还有当前验证/文档残留；若没有，输出专题剩余任务清单。
- 前置条件：避免修改历史归档中已经完成的旧“未完成”描述。
