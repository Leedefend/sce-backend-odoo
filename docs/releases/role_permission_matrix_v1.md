# SCEMS v1.0 角色权限矩阵（Role Permission Matrix）

## 1. 目标
建立 V1 固定角色的权限基线，作为 ACL / record rules / capability / block visibility 的统一口径。

## 2. 角色映射（业务角色 -> 当前验证角色）

| 业务角色（V1） | 当前验证角色（prod-like） | 说明 |
|---|---|---|
| 项目经理 | `pm` (`sc_fx_pm`) | 已覆盖 |
| 项目成员 | `project_member` (`sc_fx_project_member`) | 已统一，兼容保留 `material_user/cost_user` |
| 合同管理人员 | `contract_admin` (`sc_fx_contract_admin`) | 已覆盖 |
| 财务协同人员 | `finance` (`sc_fx_finance`) | 已覆盖 |
| 管理层查看 | `executive` (`sc_fx_executive`) | 已覆盖（应维持只读策略） |
| 系统管理员 | `admin`（非 prod-like 固定夹具） | 通过系统内置管理员角色保障 |

## 3. 权限维度基线

### 3.1 模型访问（ACL）
- `project.project`: 项目相关角色至少读权限，项目经理具备必要写权限。
- `construction.contract`: 合同管理/项目经理/管理层可读，合同管理具备操作权限。
- `project.cost`: 成本相关角色可读写受控。
- `payment.request`: 财务协同与管理层可读，财务协同具备流程权限。

### 3.2 记录规则（Record Rules）
- 项目成员：仅可见被授权项目数据。
- 财务协同：可见财务域记录，不越权写入非财务域对象。
- 管理层查看：只读视角优先。

### 3.3 Capability / Block 可见性
- `system.init` 输出 capability 必须与角色基线一致。
- `project.management` 7-block 支持按角色可见/只读。
- 未授权 capability 应返回拒绝或降级语义，不出现空白失败。

## 4. 当前验证快照（来自 role_capability_floor_prod_like）

| 角色 | capability_count | journey(system.init/ui.contract) | 状态 |
|---|---:|---|---|
| `pm` | 25 | PASS / PASS | PASS |
| `executive` | 42 | PASS / PASS | PASS |
| `finance` | 37 | PASS / PASS | PASS |
| `contract_admin` | 42 | PASS / PASS | PASS |
| `project_member` | 25 | PASS / PASS | PASS |
| `material_user` | 25 | PASS / PASS | PASS |
| `cost_user` | 25 | PASS / PASS | PASS |

## 5. 待补齐项
- 管理层查看角色增加只读约束核验脚本。
- 管理层只读验证从契约层扩展到写意图运行时探测。
