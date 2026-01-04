# TP-06｜权限 × 视图 × 行为一致性审计（B2）

目标：确保“可见入口 = 可用入口”，避免 AccessError 与“点炸”体验。
本阶段只做审计输出，不改变业务语义。

## 审计范围

- 项目中心相关入口（菜单 / action / 按钮）
- 角色：demo_pm / demo_cost / demo_readonly / admin
- 场景：项目列表、项目看板、项目详情页

## 审计清单（v1）

| 审计项 | 入口类型 | 目标角色 | 预期结果 | 通过标准 |
| --- | --- | --- | --- | --- |
| A-01 | 项目看板三点菜单 | demo_pm | 可见且可用 | 无 AccessError |
| A-02 | 项目详情页页签 | demo_pm | 仅展示允许页签 | 不触发未授权模型读取 |
| A-03 | BOQ 入口 | demo_pm | 不可见或降维 | 不出现 AccessError |
| A-04 | 成本台账入口 | demo_pm | 仅摘要 | 不进入明细 |
| A-05 | 合同入口 | demo_pm | 只读汇总 | 不含配置动作 |
| A-06 | 资料区入口 | demo_pm | 只读可见 | 不影响主流程 |
| A-07 | BOQ / 成本 / 进度 | demo_cost | 明细可用 | 功能不回退 |
| A-08 | 只读角色 | demo_readonly | 可见摘要 | 入口可点击且无 AccessError |
| A-09 | 管理员入口 | admin | 全量可用 | 原功能不受损 |

## 输出物

- `docs/audit/action_groups_missing_db.csv`（action groups 缺失清单）
- 角色视角审计记录（表格或 checklist）

## 审计执行建议

1. 先跑 `make demo.full DB=sc_demo` 刷新数据
2. 逐角色验证（demo_pm / demo_cost / demo_readonly / admin）
3. 发现问题只记录，不立刻改权限
4. 形成“问题清单 → 归因（菜单 / action / view / ACL）”

## 完成定义（TP-06 Done）

- 所有“可见入口”均可进入，无 AccessError
- 审计清单 A-01 ~ A-09 有明确结论
- 输出物可复用为后续回归基线
- 若入口在某角色下不可用，默认优先选择“隐藏或降维表达”，而非补权限。
