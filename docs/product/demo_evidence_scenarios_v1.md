# Demo Evidence Scenarios v1

本文件冻结 Product Hardening v1 的官方 demo 证据场景。

## 标准场景

| 场景键 | 中文名 | 复用数据集 | 样板项目 | 目标语义 |
| --- | --- | --- | --- | --- |
| `project_normal` | 正常项目 | `s60_project_cockpit` | `展厅-智慧园区运营中心` | 执行中、存在进度证据、推荐补成本 |
| `project_over_budget` | 超预算项目 | `s60_project_cockpit` | `展厅-产线升级改造工程` | 完整闭环、付款/结算证据齐全、风险命中 `payment_exceeds_cost` |
| `project_payment_delay` | 付款风险项目 | `s60_project_cockpit` | `展厅-装配式住宅试点` | 成本已形成、付款未形成、风险命中 `execution_payment_missing` |

## 设计原则

- 标准场景名用于销售演示、验收脚本与 CI，不再直接暴露底层 `sXX_*` 目录语义。
- 标准场景当前复用已有 `release/showroom` 数据，不重复造 seed。
- 每个标准场景必须满足：
  - 有明确样板项目
  - 驾驶舱存在 `evidence_refs`
  - Evidence Chain 可追溯
  - 风险与推荐动作可解释

## 当前边界

- `project_normal / project_over_budget / project_payment_delay` 当前是 **场景别名 + 样板映射**
- 后续若要独立拆出 XML 数据集，可保持场景名不变，只替换 loader 绑定关系
