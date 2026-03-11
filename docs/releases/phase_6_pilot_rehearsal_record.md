# SCEMS v1.0 Phase 6：试运行演练记录（W6-02）

## 1. 演练批次

| 批次 | 时间 | 参与角色 | 结论 | 记录人 |
|---|---|---|---|---|
| Batch-1 | 2026-03-11 | 项目经理/项目成员/财务协同/管理层 | PASS | Codex |

## 2. 核心链路检查

| 链路 | 结果 | 备注 |
|---|---|---|
| 登录 -> 我的工作 | PASS | `make verify.portal.my_work_smoke.container DB_NAME=sc_demo` |
| 我的工作 -> 项目台账 | PASS | `make verify.portal.scene_package_ui_smoke.container DB_NAME=sc_demo` |
| 项目台账 -> 项目管理控制台 | PASS | `make verify.portal.scene_package_ui_smoke.container DB_NAME=sc_demo` |
| 控制台 -> 合同执行 | PASS | `make verify.runtime.surface.dashboard.strict.guard` |
| 控制台 -> 成本控制 | PASS | `make verify.runtime.surface.dashboard.strict.guard` |
| 控制台 -> 资金管理 | PASS | `make verify.runtime.surface.dashboard.strict.guard` |
| 控制台 -> 风险提醒 | PASS | `make verify.runtime.surface.dashboard.strict.guard` |

## 3. 角色体验验证

| 角色 | 关键检查项 | 结果 | 备注 |
|---|---|---|---|
| 项目经理 | 项目总览、进度、风险处置入口 | PASS | scene package + dashboard strict guard |
| 项目成员 | 任务协同、项目信息可见性 | PASS | my_work smoke + scene package ui smoke |
| 财务协同 | 付款申请、资金视图、数据一致性 | PASS | dashboard strict guard |
| 管理层查看 | 只读访问、指标可视化、风险汇总 | PASS | `make verify.role.management_viewer.readonly.guard` |

## 4. 问题分级闭环统计

| 级别 | 新增 | 已关闭 | 未关闭 | 阻断发布 |
|---|---:|---:|---:|---|
| P0 | 0 | 0 | 0 | 否 |
| P1 | 0 | 0 | 0 | 否 |
| P2 | 0 | 0 | 0 | 否 |

## 5. W6-02 判定

- 判定：`DONE`
- 进入 `DONE` 条件：
  - 核心链路检查项全部完成；
  - 关键角色体验验证全部完成；
  - `P0` 未关闭数量为 `0`。
