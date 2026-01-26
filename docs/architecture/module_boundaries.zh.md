---
capability_stage: P0.1
status: active
since: v0.3.0-stable
---
# 模块职责边界（定版+红线）

本文定义模块职责、红线与轻量搬家规则。

## 依赖方向（单向）

```
odoo_test_helper (tools)
  -> sc_norm_engine (standards)
     -> smart_construction_bootstrap (setup)
        -> smart_construction_core (product)
           -> smart_construction_custom (client extension)
           -> smart_construction_seed (baseline init)
           -> smart_construction_demo (demo data)
```

core 不能依赖 demo/seed/custom。seed 不能依赖 demo。

## 模块职责

### smart_construction_bootstrap
- 系统最小可运行配置：语言/时区/币种、必要参数、基础检查。
- 不放业务模型、不放 demo 数据。

### smart_construction_core
- 产品核心：模型、业务规则、状态机、ACL/record rules。
- 官方 action/view/menu 和 UI 契约能力。
- Contract v1 接口/契约归属 core。

### smart_construction_custom
- 客户化字段、流程、报表与界面覆盖。
- 只能扩展 core 契约，不能替换。

### smart_construction_seed
- 新库可重复初始化（幂等、确定性）。
- 字典、基础数据、环境一致性（如币种）。
- 旧库/非空库必须明确失败并提示重建。

### smart_construction_demo
- 展厅数据、演示内容、示例用户/角色。
- 不写业务逻辑，不做 guard 绕过。

### sc_norm_engine
- 行业标准与校验字典。

### odoo_test_helper
- 测试辅助工具。

## 红线
- core 不得包含 demo/seed 专用兜底或捷径。
- demo 不得改变生产行为。
- seed 必须幂等，只针对新库。
- custom 不得改变 Contract v1 语义。

## 轻量搬家规则
- 被引用的 action/view 必须先加载；必要时拆到独立 `*_views.xml`/`*_actions_views.xml` 并前置加载。
- demo 数据只放在 `smart_construction_demo`，禁止进 core。
- seed 步骤只放 `smart_construction_seed/seed/steps`，并允许为门禁补齐最小必需数据（需注释说明）。
- Contract v1 接口/契约归 core；custom 仅通过扩展点加字段。

## 相关 SOP
- Seed 生命周期: `docs/ops/seed_lifecycle.md`
- 发布清单: `docs/ops/release_checklist_v0.3.0-stable.md`
