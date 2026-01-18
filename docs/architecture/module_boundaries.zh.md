---
capability_stage: P0.1
status: active
since: v0.3.0-stable
---
# 模块边界

本文定义模块职责与依赖方向的硬性规则。

## 依赖方向（必须单向）

```
odoo_test_helper (工具)
  -> sc_norm_engine (规范)
     -> smart_construction_bootstrap (安装/初始化)
        -> smart_construction_core (产品核心)
           -> smart_construction_custom (客户扩展)
           -> smart_construction_seed (基线初始化)
           -> smart_construction_demo (演示数据)
```

core **不得**依赖 demo/seed/custom；demo/custom 不得把业务逻辑回灌 core。

## 模块职责

### smart_construction_core
- 业务模型/字段/视图/菜单/动作
- ACL/record rules
- UI 体验（侧边栏/工作台/登录首跳）
- 可独立安装（不依赖 demo/seed）

### smart_construction_seed
- 幂等初始化（ICP 默认值/字典/最小阶段）
- Profiles（`base` / `demo_full`）
- 可重复执行且安全

### smart_construction_demo
- 仅演示数据（用户/项目/字典）
- 不含行为 hooks
- 可随时卸载不影响生产

### smart_construction_custom
- 客户差异（流程/报表/命名/皮肤）
- 不应成为 demo 的硬依赖（除非明确规划）

### smart_construction_bootstrap
- 安装与首次初始化辅助（若以模块实现）

### sc_norm_engine
- 行业规范/标准/校验

### odoo_test_helper
- 仅测试工具

## 禁止事项
- core 依赖 demo/seed/custom
- demo 通过 hooks 改变生产行为
- seed 在生产写入 demo 数据

## 相关 SOP
- Seed 生命周期：`docs/ops/seed_lifecycle.md`
- 发布清单：`docs/ops/release_checklist_v0.3.0-stable.md`
