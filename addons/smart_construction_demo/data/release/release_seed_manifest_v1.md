# 发布态 Demo 数据种子清单（v1）

本清单定义 `smart_construction_demo` 的“发布态可演示”数据边界，用于统一：

- 产品演示
- 联调验证
- 发布前验收基线

## 1. 数据分层

- `base/`：基础主数据与最小业务对象
- `demo/`：演示用户、角色矩阵、演示动作
- `scenario/sXX_*`：场景化业务链路

## 2. 发布态种子范围（包含）

发布态通过 `release seed set` 加载以下场景：

1. `s00_min_path`（最小业务通路）
2. `s10_contract_payment`（合同与收付款）
3. `s20_settlement_clearing`（结算与核销）
4. `s30_settlement_workflow`（工作流路径）
5. `s60_project_cockpit`（项目驾驶舱业务事实补齐）
6. `s90_users_roles`（角色用户覆盖）

并叠加稳定种子步骤：`demo_showroom,project_stage_sync`，补齐展示链路与阶段一致性。

## 3. 过程/演练数据（发布态不默认加载）

以下场景归类为“过程演练/失败修复”，不纳入发布态默认种子：

- `s40_failure_paths`
- `s50_repairable_paths`

如需回归失败链路，可手动单独加载。

## 4. 标准加载命令

```bash
make demo.load.release DB_NAME=sc_demo
```

## 4.1 发布态种子验收命令

```bash
make verify.demo.release.seed DB_NAME=sc_demo
```

## 5. 设计原则

1. **可重复**：同一命令可多次执行，不产生无界重复。
2. **可解释**：业务链路完整，页面指标可追溯到数据来源。
3. **可扩展**：后续增量场景进入 `s6x/s7x` 并先经过发布态评估。
