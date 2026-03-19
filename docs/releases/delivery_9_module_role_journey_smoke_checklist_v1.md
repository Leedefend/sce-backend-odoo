# 9模块角色旅程 Smoke 清单 v1

## 1. 目标

把“9模块可交付”落到可执行的 system-bound 验收清单，统一命令入口、通过标准和证据路径。

---

## 2. 基线命令（所有模块通用）

```bash
make verify.scene.delivery.readiness.role_matrix
make verify.portal.role_surface_smoke.container
make verify.portal.scene_health_contract_smoke.container
make verify.portal.scene_health_pagination_smoke.container
make verify.frontend.quick.gate
```

通过标准：

- 全部命令退出码为 0
- 输出中包含 `PASS`
- 产物可在 `artifacts/backend/*` 与 `artifacts/codex/*` 追溯

---

## 3. 模块级角色旅程（可执行项）

| 模块 | 关键角色 | 验证命令 | 当前结果 | 备注 |
|---|---|---|---|---|
| 项目管理 | PM/管理层 | `make verify.portal.role_surface_smoke.container` | PASS | 已验证 landing scene 可达 |
| 项目执行 | PM | `make verify.scene.delivery.readiness.role_matrix` | PASS | runtime boundary + role matrix 已通过 |
| 任务管理 | PM | `make verify.scene.delivery.readiness.role_matrix` | PASS | 依赖 scene readiness 主链 |
| 风险管理 | PM/管理层 | `make verify.scene.delivery.readiness.role_matrix` | PASS | 依赖 scene readiness 主链 |
| 成本管理 | PM/财务 | `make verify.scene.delivery.readiness.role_matrix` | PASS | 依赖 scene readiness 主链 |
| 合同管理 | PM/管理层 | `make verify.scene.delivery.readiness.role_matrix` | PASS | 依赖 scene readiness 主链 |
| 资金财务 | 财务/管理层 | `make verify.portal.payment_request_approval_all_smoke.container` | FAIL | handoff 链路存在阻塞（见第4节） |
| 数据与字典 | 配置管理员 | `make verify.scene.delivery.readiness.role_matrix` | PASS | 入口与治理链路已覆盖 |
| 配置中心 | 配置管理员 | `make verify.scene.delivery.readiness.role_matrix` | PASS | 入口与治理链路已覆盖 |

---

## 4. 已发现阻塞（本轮）

命令：

```bash
make verify.portal.payment_request_approval_all_smoke.container
```

结果：FAIL

核心失败信息：

- `payment_request_approval_handoff_smoke` 失败
- 失败原因：`executive has no allowed follow-up action after submit`
- 实际 allowed actions：`['submit']`
- 期望动作：`approve/reject` 之一

结论：该问题属于财务模块跨角色审批交接阻塞项，应纳入 P0 blocker 跟踪。

---

## 5. 下一步动作

1. 修复 payment request handoff 策略/权限映射（finance → executive）
2. 修复后回归：

```bash
make verify.portal.payment_request_approval_all_smoke.container
```

3. 回归通过后，将财务模块状态从 `FAIL/BLOCKED` 调整为 `IN_PROGRESS` 或 `READY_FOR_PILOT`

