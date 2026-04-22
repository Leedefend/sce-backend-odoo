# Manifest 加载链审计 v1（原生业务事实层）

## 1) 核心模块装载拓扑

| 模块 | depends | data 条目数 | 安全条目 | 视图条目 | 动作条目 |
|---|---|---:|---:|---:|---:|
| `smart_core` | `base`, `web` | 5 | 3 | 0 | 0 |
| `smart_enterprise_base` | `base`, `hr`, `smart_core` | 6 | 1 | 4 | 0 |
| `smart_construction_core` | `project/purchase/stock/account/... + smart_core + smart_enterprise_base + tier_validation` | 84 | 9 | 53 | 8 |
| `smart_construction_scene` | `smart_construction_core` | 7 | 1 | 1 | 0 |

## 2) 链路核对结论

### 基础数据链

- `smart_construction_core` 的基础数据 seed（序列、阶段、规则）位于 manifest 前段，满足业务事实预加载要求。
- `smart_enterprise_base` 将 `runtime_params.xml` + `ir.model.access.csv` + 主数据视图统一装载，链路稳定。

### 安全链

- `smart_core`、`smart_enterprise_base`、`smart_construction_core`、`smart_construction_scene` 均在 manifest 中显式装载 ACL。
- `smart_construction_core` 同时装载 `sc_record_rules.xml`、`sc_scene_rules.xml`，安全面完整但复杂度高。

### 菜单/视图/审批动作链

- `smart_construction_core` 显式加载 `actions/project_list_actions.xml` 后再加载 `views/menu_root.xml`，符合入口先后关系。
- Tier 审批动作 `material_plan_tier_actions.xml`、`payment_request_tier_actions.xml` 在 manifest 中存在，审批动作链有效。

## 3) 风险点

1. **加载体量偏大**：`smart_construction_core` 单模块 `84` data 条目，升级回归窗口大。
2. **安全混装**：同一模块同时承载 capability/group/ACL/rules，定位冲突成本高。
3. **补丁文件后置**：`action_groups_patch.xml`、`menu_tech_hide_patch.xml` 后置加载，需在 Batch B 做最小冲突回归。

## 4) 审计结论

- Manifest 维度链路“成立”。
- 当前不建议调整装载顺序；优先进入 Batch B 做冲突修复与闭环验证。

