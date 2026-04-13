# Delivery Demo & Handover Checklist v1

## Demo Preflight

1. 启动服务：`make restart && make frontend.restart`
2. 登录验证账户：`wutao / demo / sc_demo`
3. 运行 smoke：`unified_system_menu_click_usability_smoke`，确保 `fail_count=0`

## Demo Script

### Segment A：基础链路

- 演示登录 → 菜单加载 → 首页进入
- 展示菜单收敛结果（无技术/演示菜单暴露）

### Segment B：核心业务链

- 项目立项：新建 → 保存 → 返回
- 执行与成本：列表 → 详情 → 返回
- 合同与付款：列表 → 详情 → 返回

### Segment C：可观测性

- 展示错误态包含 `错误码/TraceID`
- 展示空态文案与下一步建议

## Handover Package

- package_index: `docs/ops/delivery_package_index_v1.md`
- final_check: `docs/ops/delivery_readiness_final_check_v1.md`
- trial_log: `docs/ops/delivery_user_trial_execution_log_v1.md`
- issue_board: `artifacts/delivery/user_trial_issue_board_v1.json`

## Acceptance Sign-off

- 技术签收：`PASS / FAIL`
- 业务签收：`PASS / FAIL`
- 交付结论：`GO / NO_GO`
- 备注：`<blocking issues or none>`

## Post-Handover Guard

- 若交付后发现 `P0/P1`：24h 内启动修复批。
- 若交付后发现 `P2/P3`：纳入下一迭代优化池并保持回归验证。
