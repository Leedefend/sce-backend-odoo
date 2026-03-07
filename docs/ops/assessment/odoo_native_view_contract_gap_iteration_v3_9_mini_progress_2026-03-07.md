# Odoo 原生承载差距迭代进展（v3.9-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 前端契约消费落地：
   - ActionView `group_offset` 从固定值切换为路由态驱动
   - 解析并消费 `group_paging.next_group_offset/prev_group_offset`
   - 新增分组窗口状态 `offset/count/total` 与导航动作
2. 交互增强：
   - GroupSummaryBar 新增“上一组/下一组”窗口按钮与窗口范围信息
3. 路由一致性：
   - `group_offset` 纳入 `syncRouteListState` 与 grouped 路由归一化
   - 分组变更、样本大小变更、搜索/排序/过滤后统一回到窗口起点
4. 契约文档同步：
   - 增补“前端优先使用 `next_group_offset/prev_group_offset`”兼容规则

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

grouped 分组分页能力已从“字段可用”升级到“消费闭环可用”，窗口导航逻辑由后端语义主导，前端路由态可稳定复现当前分组窗口。
