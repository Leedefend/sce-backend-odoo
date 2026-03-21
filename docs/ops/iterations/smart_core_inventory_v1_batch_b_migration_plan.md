# smart_core 现有内容盘点表 v1（Batch-B：明显越界点迁移计划）

## Layer Target
- `Platform Layer` / `Boundary Governance`

## Module
- `addons/smart_core/core`
- `addons/smart_core/security`
- `addons/smart_core/handlers`

## Reason
- 在 Batch-A 分类冻结基础上，先处理“最明显且低风险可迁移”的越界项，避免平台层继续承载行业语义。

## 本批策略（只迁明显越界点）
- 先迁“硬编码行业 role/scene/业务关键词”的默认值与字典。
- 保留 runtime 框架与 fallback 骨架在 `smart_core`。
- 不在本批做：onchange/x2many、复杂契约结构重构、前端联动大改。

## 迁移候选清单（Batch-B）

| 优先级 | 路径 | 对象 | 当前越界点 | 动作 | 建议归属 |
| --- | --- | --- | --- | --- | --- |
| P0 | `addons/smart_core/core/page_contracts_builder.py` | 页面契约默认文案/关键词 | 含 `project_manager`、`payment/付款`、`projects.` 等行业语义 | 提取为 extension profile（平台保留空默认） | `smart_construction_core` / `smart_construction_scene` |
| P0 | `addons/smart_core/core/page_orchestration_data_provider.py` | 页面编排默认受众 | 硬编码行业角色组合 | 提取为 extension hook（平台仅保留 generic audience） | `smart_construction_core` |
| P0 | `addons/smart_core/core/workspace_home_data_provider.py` | 工作台模板默认 audience | `project_manager/construction_manager/finance_manager` | 提取 profile，平台仅保留 neutral role buckets | `smart_construction_scene` |
| P0 | `addons/smart_core/core/workspace_home_contract_builder.py` | 工作台契约默认内容 | 大量 `portal.dashboard` 与 payment/risk 业务词 | 平台仅保留 minimum workspace shell；行业块下沉到扩展提供器 | `smart_construction_scene` |
| P1 | `addons/smart_core/core/scene_delivery_policy.py` | 场景交付默认白名单 | 含 `portal.dashboard` 行业偏置默认 | 平台默认收敛为 `workspace.home`，其余交由扩展注入 | `smart_construction_scene` |
| P1 | `addons/smart_core/core/action_target_schema.py` | action fallback target | 默认落 `portal.dashboard` | 平台默认 target 改 `workspace.home` | `smart_core`（修正后保留） |
| P1 | `addons/smart_core/core/system_init_payload_builder.py` | landing scene default | 默认 `portal.dashboard` | 平台默认落 `workspace.home`，行业落地通过 role profile 覆盖 | `smart_core`（修正后保留） |
| P1 | `addons/smart_core/core/scene_provider.py` | CRITICAL_SCENE_TARGET_OVERRIDES | 包含 `portal.dashboard` | 平台 critical 最小集合仅保留 `workspace.home` | `smart_core`（修正后保留） |
| P2 | `addons/smart_core/security/groups.xml` | legacy compat groups | `group_sc_*` 行业前缀仍在平台 | 保留兼容但标记 sunset；逐步迁移引用到 canonical `group_smart_core_*` | `smart_core`（兼容层） |

## 不在本批迁移（边界说明）
- `addons/smart_core/handlers/system_init.py`
  - 已完成平台最小面收口（`workspace.home` + nav isolation）；本批不再拆大逻辑，仅维持稳定。
- `addons/smart_core/handlers/app_shell.py`
  - 属于平台最小 fallback 能力面，必须保留。

## 执行顺序（建议）
1. **Step-1（P0）**：先抽离 `page_contracts_builder` + `page_orchestration_data_provider` 的行业关键词与角色受众。
2. **Step-2（P0）**：收敛 `workspace_home_*` 的默认内容为平台 neutral 版本。
3. **Step-3（P1）**：统一 scene/target 默认（`scene_delivery_policy`、`action_target_schema`、`system_init_payload_builder`、`scene_provider`）。
4. **Step-4（P2）**：`group_sc_*` 兼容组进入 sunset 清单并清理 `REQUIRED_GROUPS` 残留引用。

## 验证门禁（每步都跑）
- `make verify.smart_core.minimum_surface DB_NAME=sc_platform_core E2E_LOGIN=admin E2E_PASSWORD=admin`
- `make verify.smart_core.minimum_surface.nav_isolation_guard DB_NAME=sc_platform_core E2E_LOGIN=admin E2E_PASSWORD=admin`

## 本批验收标准
- `smart_core` 默认输出不再携带行业角色/行业业务词作为平台默认值。
- 平台-only 数据库继续满足 minimum-surface 全链路通过。
- 行业语义由 extension/profile 提供，不再由平台硬编码。
