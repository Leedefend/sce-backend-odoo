# 成本域 API / 报表接口（骨架）

本文件先只定义“我们将来需要什么数据”，真正接口在后端实现时再补充 path 与参数。

## 1. 单项目经营驾驶舱

- 目标：给项目详情页 / Vue 大屏提供经营视角数据。
- 输入：`project_id`
- 输出示例字段：

```jsonc
{
  "project_id": 1,
  "budget": {
    "amount_cost_target": 0.0,
    "amount_revenue_target": 0.0
  },
  "contract": {
    "amount_income": 0.0,
    "amount_subcontract": 0.0,
    "amount_purchase": 0.0
  },
  "progress": {
    "amount_output": 0.0,
    "progress_percent": 0.0
  },
  "kpi": {
    "gross_margin_rate": 0.0,
    "health_index": 0.0
  }
}
```

## 2. PMO 汇总接口（预留）

* 输入：区域 / 事业部 / 项目经理 等维度
* 输出：项目列表 + 核心 KPI（CFI-G / CVR-G 等）

> 暂不实现，只做字段设计；等后端模型与 compute 稳定后再落地。

```
