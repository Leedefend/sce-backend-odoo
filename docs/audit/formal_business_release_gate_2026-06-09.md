# Formal Business Release Gate 2026-06-09

## Scope

把用户已确认正式菜单体系锁定验收和正式业务办理能力验收合并成一个发布门禁。

总门禁顺序执行：

- `user_confirmed_menu_surface_guard.py`
- `user_confirmed_form_capability_audit.py`
- `user_confirmed_form_data_alignment_audit.py`
- `user_confirmed_settlement_usability_audit.py`
- `validate_business_capability_gate.sh`

## Command

```bash
DB_NAME=sc_demo scripts/ops/validate_formal_business_release_gate.sh
```

## Result

- 数据库：`sc_demo`
- 开始时间：`2026-06-10T00:00:44+08:00`
- 结束时间：`2026-06-10T00:03:04+08:00`
- 总结果：`PASS`

子门禁结果：

- 用户确认菜单面锁定：`PASS`
- 用户确认表单能力：`PASS`
- 用户确认表单数据对齐：`PASS`
- 用户确认结算办理可用性：`PASS`
- 正式业务办理能力：`PASS`

## Coverage

- 用户确认菜单分组、可见菜单、禁止泄漏分组
- 用户确认正式表单字段能力
- 用户确认列表与正式表单数据值对齐
- 用户确认结算单业务分类和核心可见字段可承接
- 正式业务办理能力：核心单据办理、核心闭环、财务动作、施工生产动作

## Data Alignment

- 用户确认正式菜单：`62`
- 覆盖模型：`36`
- 检查记录：`256844`
- 检查正式字段：`861`
- 不一致字段：`0`
- 只读来源字段未承接：`0`
- 严重度分布：`{"ok": 62}`

本轮发布准备执行：

- `scripts/ops/user_confirmed_formal_data_backfill.py`
- `scripts/ops/user_confirmed_attachment_bind.py`
- `scripts/ops/user_confirmed_settlement_usability_backfill.py`

关键修复：

- 把用户确认正式字段从验收面回填到正式表单字段。
- 把历史附件引用绑定到正式 `attachment_ids`。
- 将入库单正式主编号 `name` 对齐用户确认的入库单号 `legacy_visible_02`。
- 将直管验收结算单的业务分类和验收可见字段回填到正式结算单。

## Policy

- 仅允许在非生产环境运行，脚本调用 `guard_prod_forbid`。
- 任意子验收失败时总门禁失败。
- 总门禁脚本只验收，不修改用户菜单体系和业务数据；发布准备数据修复由显式回填脚本执行。
