# Project Budget Legacy Material Projection 2026-06-10

## Scope

专项补齐历史材料预算/清单事实进入正式 `project.budget` 和 `project.budget.boq.line`。

来源：

- 表：`sc_legacy_material_stock_fact`
- 条件：`active AND fact_type = 'material_budget_item' AND project_id IS NOT NULL`
- 源行：`8747`
- 源项目：`4`

## Backfill

```text
PROJECT_BUDGET_LEGACY_MATERIAL_BACKFILL: {"created_budgets": 4, "created_lines": 8747, "operation": "project_budget_legacy_material_backfill", "skipped_lines": 0, "source_projects": 4, "source_rows": 8747, "status": "PASS"}
```

处理策略：

- 每个项目生成一个历史预算版本：`LEGACY-MATERIAL-BUDGET`
- 每条历史材料预算事实生成一条正式预算清单
- 历史数量、单价、金额按源值保留；当前源数据金额/数量均为 `0`，不伪造目标成本
- 历史来源 ID、源表、历史单位等写入清单备注，用于审计追踪和幂等回填

## Audit

```text
PROJECT_BUDGET_LEGACY_MATERIAL_AUDIT: {"failures": [], "projected_budgets": 4, "projected_lines": 8747, "source_ids_projected": 8747, "source_projects": 4, "source_rows": 8747, "status": "PASS"}
```

项目分布：

- 项目 `499`：`34/34`
- 项目 `715`：`2/2`
- 项目 `753`：`8402/8402`
- 项目 `820`：`309/309`

## Release Gate

```text
FORMAL_BUSINESS_RELEASE_GATE_RESULT: PASS db=sc_demo started_at=2026-06-10T00:18:18+08:00 finished_at=2026-06-10T00:20:32+08:00
```

关键数据对齐结果：

- 用户确认正式菜单：`62`
- 检查记录：`256844`
- 检查字段：`861`
- 不一致字段：`0`
- 只读来源字段未承接：`0`

## Visible Matrix

预算投影前：

- `issue_count`: `25`
- `legacy_facts_not_projected_to_business_surface`: `3`
- `project.budget`: `3`

预算投影后：

- `issue_count`: `22`
- `legacy_facts_not_projected_to_business_surface`: `0`
- 剩余业务字段专项模型：`8`
- 剩余纯元数据门：`14`

## Policy

- 不改用户已确认菜单体系。
- 不覆盖用户已验收列表值。
- 不制造源数据不存在的预算金额。
- 回填只在非生产门控脚本下执行，审计纳入正式发布门。
