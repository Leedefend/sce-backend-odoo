# Odoo 原生承载差距迭代计划（v0.3）

日期：2026-03-04  
分支：`feat/interaction-core-p1-v0_2`

## 本轮目标（下一组 10 提交）

在不引入新业务契约前提下，把 `group_by` 从“参数透传”提升到“用户可读结果”，并继续补齐契约治理覆盖。

1. `api.data` 在 `group_by` 请求下返回轻量分组摘要（`group_summary`）
2. `ActionView` 渲染分组摘要条，支持点击后快速收敛到对应记录
3. 增加专项 guard，防止 `group_by/group_summary` 回退
4. 扩充 contract cases 到 project/contract/cost/risk 等关键域

## 验收口径

1. 在列表页启用 `group_by` 后，首屏可看到分组摘要与计数
2. 点击分组摘要项，可触发可见的数据收敛行为（搜索或筛选）
3. `make verify.frontend.quick.gate` 与 `make verify.smart_core` 通过
4. `docs/contract/cases.yml` 新增关键业务域样本
