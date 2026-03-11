# SCEMS v1.0 首发记录（Launch Record）

## 1. 发布批次信息
- 版本：`SCEMS v1.0`
- 发布分支：`release/construction-system-v1.0`
- 发布日期：`2026-03-11`
- 发布负责人：`Codex（代理执行，待业务签字确认）`

## 2. 发布窗口与责任

| 项目 | 窗口 | 责任人 | 状态 |
|---|---|---|---|
| 发布窗口 | 2026-03-11 17:17 ~ 17:30 | 发布经理（代理：Codex） | 已执行 |
| 回滚窗口 | 2026-03-11 17:30 ~ 19:30 | 系统管理员 | 已预留 |
| 观测窗口（24h） | 2026-03-11 17:30 ~ 2026-03-12 17:30 | 值班负责人 | 进行中 |

## 3. 发布步骤执行记录

| 步骤 | 命令/动作 | 结果 | 证据路径 |
|---|---|---|---|
| 部署准备 | `make ps` | PASS | 终端输出（2026-03-11 17:17） |
| 模块安装/升级 | `make mod.install` / `make mod.upgrade` | PASS（沿用 Phase 5 演练） | `docs/releases/phase_5_verification_deployment_execution_report.md` |
| 首发切换 | `make verify.portal.my_work_smoke.container DB_NAME=sc_demo` + `make verify.portal.scene_package_ui_smoke.container DB_NAME=sc_demo` | PASS | `/mnt/artifacts/codex/my-work-smoke-v10_2/20260311T091718` + `/mnt/artifacts/codex/portal-scene-package-ui-v10_6/20260311T091722` |
| 稳定回滚演练 | `make scene.rollback.stable` | PASS | 终端输出（2026-03-11 17:17） |

## 4. 发布后 spot-check

| 检查项 | 结果 | 备注 |
|---|---|---|
| 登录与我的工作 | PASS | `verify.portal.my_work_smoke.container` |
| 项目台账与控制台 | PASS | `verify.portal.scene_package_ui_smoke.container` |
| 合同/成本/资金/风险 | PASS | `verify.runtime.surface.dashboard.strict.guard`（W6-02 证据） |
| 管理层只读视图 | PASS | `verify.role.management_viewer.readonly.guard` |

## 5. 发布结论
- 结论：`条件通过（待 24h 观测完成后转 PASS）`
- 阻断项：`无（当前 P0=0）`
- 批准人：`待业务负责人签字`
