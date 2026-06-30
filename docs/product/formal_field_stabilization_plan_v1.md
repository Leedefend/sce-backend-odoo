# 正式字段稳定化专题 v1

## 目标

正式产品的用户办理面、配置面和发布基线必须使用稳定的业务字段名和业务标签，不再把迁移、验收、低代码兼容阶段的过渡字段作为长期产品事实。

本专题不是删除历史追溯能力。旧系统来源、迁移证据、审计字段可以保留在内部模型和审计入口，但不得进入正式办理面、正式配置面和正式发布基线。

## 边界

正式面包括：

- `addons/smart_construction_core/models/core`
- `addons/smart_construction_core/models/projection`
- `addons/smart_construction_core/views/core`
- `addons/smart_construction_core/views/support/user_confirmed_formal_*`
- `addons/smart_construction_core/data/view_orchestration_*`
- `addons/smart_construction_core/data/p1_daily_business_form_orchestration_contract_data.xml`

内部面包括：

- 迁移事实模型
- 历史审计模型
- 来源追溯模型
- 修复、重放、审计脚本
- 只供研发/实施使用的 support audit 入口

## 不应进入正式面的过渡字段

- `p1_visible_*`
- `legacy_visible_*`
- `accepted_visible_*`
- `user_acceptance_*`
- `CODEX_*`
- `*_HIDDEN`

`legacy_*` 和 `source_*` 不是按前缀一刀切。若字段承载的是旧系统 ID、来源表、来源记录、导入批次、迁移证据，则只能留在内部审计面；若字段承载的是正式业务上下文，应改名为业务字段。

## 当前债务基线

当前静态审计命令：

```bash
make verify.formal_surface.transition_field_audit
```

初始债务：

| 分类 | 前缀 | 数量 |
| --- | --- | ---: |
| formal_config_contract | p1_visible | 455 |
| formal_config_contract | legacy_visible | 0 |
| formal_confirmed_view | legacy_visible | 375 |
| formal_confirmed_view | p1_visible | 202 |
| formal_confirmed_view | user_acceptance | 28 |
| formal_confirmed_view | accepted_visible | 15 |
| formal_core_model | legacy_visible | 254 |
| formal_core_model | user_acceptance | 17 |
| formal_core_view | legacy_visible | 213 |
| formal_projection_model | legacy_visible | 47 |

本专题首批已清理 `formal_config_contract.legacy_visible` 7 处，当前预算基线位于：

`scripts/verify/baselines/formal_surface_transition_field_budget_v1.json`

预算只能下降，不能上升。新增分类或新增前缀命中必须失败。

## 执行顺序

### 第一批：配置和办理面的防新增

已完成：

- 增加 `scripts/verify/formal_surface_transition_field_audit.py`
- 增加预算基线 `formal_surface_transition_field_budget_v1.json`
- 接入 `make verify.formal_surface.transition_field_audit`
- 接入 `verify.user_confirmed.formal_surface.locked`

### 第二批：配置契约字段稳定化

优先处理 `formal_config_contract.p1_visible=455`。

目标：

- 发布基线配置不再引用 `p1_visible_*`
- `ui.business.config.contract.view_orchestration.views.tree.columns` 使用正式字段名
- 配置面和办理面继续通过 `verify.business_config.list_config_boundary`

处理方式：

- 为每个 `p1_visible_*` 建立正式字段映射
- 已存在正式字段时直接替换
- 不存在正式字段时新增 compute/store 或迁移字段
- 更新生成契约和对应数据迁移
- 下调预算

### 第三批：用户确认正式视图稳定化

优先处理：

- `formal_confirmed_view.legacy_visible=375`
- `formal_confirmed_view.p1_visible=202`

目标：

- `user_confirmed_formal_list_views.xml`
- `user_confirmed_formal_form_views.xml`
- `user_confirmed_formal_list_alignment_views.xml`

不再直接引用过渡字段。

### 第四批：核心模型和核心视图稳定化

优先处理：

- `payment.request`
- `sc.invoice.registration`
- `sc.financing.loan`
- `sc.payment.execution`
- `sc.expense.claim`
- `sc.office.admin.document`
- `sc.hr.payroll.document`
- `sc.fund.account.operation`

目标：

- core 模型中业务字段使用正式命名
- 旧字段仅保留为 internal provenance
- core 视图不再暴露 `legacy_visible_*`

### 第五批：投影模型稳定化

投影模型中的 `legacy_visible_*` 应改为业务摘要、来源说明或内部追溯字段。

## 验收命令

每批清理至少运行：

```bash
make verify.formal_surface.transition_field_audit
make verify.business_config.list_config_boundary DB_NAME=sc_demo PROJECT=sc-backend-odoo-dev COMPOSE_PROJECT_NAME=sc-backend-odoo-dev
```

涉及模型字段、XML data 或视图时，还需升级模块并跑正式面锁定验收：

```bash
CODEX_MODE=gate CODEX_NEED_UPGRADE=1 MODULE="smart_core,smart_construction_core" DB_NAME=sc_demo PROJECT=sc-backend-odoo-dev COMPOSE_PROJECT_NAME=sc-backend-odoo-dev make mod.upgrade
make verify.user_confirmed.formal_surface.locked DB_NAME=sc_demo PROJECT=sc-backend-odoo-dev COMPOSE_PROJECT_NAME=sc-backend-odoo-dev
```
