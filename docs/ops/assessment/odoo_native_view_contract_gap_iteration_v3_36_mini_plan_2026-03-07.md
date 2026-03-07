# Odoo 原生承载差距迭代计划（v3.36-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_5`

## 目标定位

对照评估报告执行 P1 差距复核，判断是否已补齐；若存在未补齐项，直接在本轮补齐。

## 复核范围（P1）

1. 双表单引擎分叉（`RecordView` vs `ContractFormPage`）
2. x2many 编辑语义
3. 搜索能力消费 `group_by/saved_filters`

## 本轮补齐目标

1. 补齐 P1 复核中发现的治理缺口：更新路由守卫与当前单引擎路由事实一致
2. 输出 P1 状态结论并形成可审计记录
