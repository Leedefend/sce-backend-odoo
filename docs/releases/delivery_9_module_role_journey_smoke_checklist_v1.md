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
| 资金财务 | 财务/管理层 | `make verify.portal.payment_request_approval_all_smoke.container` | PASS | finance -> executive handoff 已通过 |
| 数据与字典 | 配置管理员 | `make verify.scene.delivery.readiness.role_matrix` | PASS | 入口与治理链路已覆盖 |
| 配置中心 | 配置管理员 | `make verify.scene.delivery.readiness.role_matrix` | PASS | 入口与治理链路已覆盖 |

---

## 4. Handoff 收口（最终）

命令：

```bash
make verify.portal.payment_request_approval_all_smoke.container
```

结果：PASS（2026-07-05）

核心失败信息：

- `payment_request_approval_smoke`：PASS
- `payment_request_approval_handoff_smoke`：PASS
- `verify.portal.payment_request_approval_field_consumer_audit`：PASS（`unexpected_deprecated_refs=0`）
- finance submit 后 executive 可见 `approve/reject`，并完成 approve handoff。

结论：财务跨角色审批 handoff 已关闭。

---

## 5. 下一步动作

1. 保持 `make verify.portal.payment_request_approval_all_smoke.container` 作为 finance 旅程回归。
2. 保持 `make verify.release.delivery_9_module.final_closeout.guard` 作为 9 模块文档/证据收口门禁。
3. 后续新增角色旅程进入常规迭代，不重开本轮 P0。
