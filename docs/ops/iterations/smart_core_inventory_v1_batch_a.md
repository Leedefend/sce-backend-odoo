# smart_core 现有内容盘点表 v1（Batch-A）

## Layer Target
- `Platform Layer` / `Domain Boundary Governance`

## Module
- `addons/smart_core`
- `addons/smart_construction_core`（仅作为扩展注入源）

## Reason
- 冻结 `smart_core` 平台边界，先完成“保留 / 迁出 / 待审”分类，再进入后续迁移批次。

## 盘点结果（第一轮）

| 路径 | 对象 | 当前职责 | 判定 | 原因 | 建议归属 |
| --- | --- | --- | --- | --- | --- |
| `addons/smart_core/core/handler_registry.py` | intent handler registry | 平台 intent 运行时注册 | 保留 | 纯 runtime 机制，无行业对象 | `smart_core` |
| `addons/smart_core/core/base_handler.py` | BaseIntentHandler | 平台 handler 协议基类 | 保留 | 平台协议核心 | `smart_core` |
| `addons/smart_core/core/capability_provider.py` | capability provider | 用户能力加载与分组 | 待审→已治理 | 之前直接导入建设行业 registry；本批改为 extension hook 注入 | `smart_core`（运行时） + `smart_construction_core`（能力定义） |
| `addons/smart_core/identity/identity_resolver.py` | role resolver | role 真源解析与 role surface | 待审→已治理 | 之前内置行业角色组映射；本批改为 extension profile 注入 | `smart_core`（解析引擎） + `smart_construction_core`（角色映射） |
| `addons/smart_core/adapters/odoo_nav_adapter.py` | nav scene adapter | 菜单/action 到 scene 的映射 | 待审→已治理 | 之前硬编码建设行业 scene 映射；本批改为 extension hook 注入 | `smart_core`（适配骨架） + `smart_construction_core`（行业映射） |
| `addons/smart_core/core/scene_provider.py` | scene source loader | 场景配置装载与回退 | 待审→已治理 | 之前直接导入建设 scene_registry；本批改为 provider hook 注入 | `smart_core`（加载骨架） + 扩展模块（scene source） |
| `addons/smart_core/core/ui_base_contract_asset_producer.py` | ui base asset producer | 基础契约资产生成 | 待审→已治理 | 场景来源改为 provider hook，不再直接导入建设 scene_registry | `smart_core`（资产生成） + 扩展模块（scene source） |
| `addons/smart_core/models/ui_base_contract_asset_event_trigger.py` | asset trigger | 资产刷新触发器 | 待审→已治理 | 场景来源改为 provider hook | `smart_core`（触发器） + 扩展模块（scene source） |
| `addons/smart_core/core/workspace_home_data_provider.py` | workspace profile provider | 工作台数据模板来源 | 待审→已治理 | 去除行业目录硬编码，改为 addons profile 自动发现 | `smart_core`（发现机制） + 行业模块（profile 文件） |
| `addons/smart_core/app_config_engine/services/resolvers/action_resolver.py` | server→window mapping | server action 映射 | 待审→已治理 | 去除建设模块映射硬编码，改为 extension hook 注入 | `smart_core`（解析骨架） + 扩展模块（映射定义） |
| `addons/smart_core/core/scene_provider.py`（critical overrides） | critical scene target 纠偏 | 关键场景 target/route 收口 | 待审→已治理 | 由平台默认最小集合 + 扩展注入，不在平台层固化行业场景集合 | `smart_core`（策略入口） + 扩展模块（策略数据） |
| `addons/smart_core/core/ui_base_contract_asset_producer.py` | minimal ui-base fallback | 资产缺失兜底契约 | 待审→已治理 | 去除 `project.project` / `projects.intake` 业务兜底，改通用 fallback | `smart_core` |
| `addons/smart_core/core/ui_base_contract_asset_repository.py` | minimal ui-base fallback | 资产仓储兜底契约 | 待审→已治理 | 同上，去除业务模型硬编码 | `smart_core` |
| `addons/smart_core/core/action_target_schema.py` | action target default | 通用 action 目标解析 | 待审→已治理 | 默认目标改为 `workspace.home/portal.dashboard`，不绑定行业场景 | `smart_core` |
| `addons/smart_core/handlers/file_upload.py` | file upload allowlist | 上传模型白名单 | 待审→已治理 | 平台默认通用模型，行业模型白名单改为扩展 hook 注入 | `smart_core` + 扩展模块 |
| `addons/smart_core/handlers/file_download.py` | file download allowlist | 下载模型白名单 | 待审→已治理 | 同上，改为扩展 hook 注入 | `smart_core` + 扩展模块 |
| `addons/smart_core/handlers/api_data_write.py` | data write allowlist | 模型字段白名单写入 | 待审→已治理 | 平台默认通用 allowlist，行业映射由扩展提供 | `smart_core` + 扩展模块 |
| `addons/smart_core/handlers/api_data_unlink.py` | data unlink allowlist | 模型删除白名单 | 待审→已治理 | 平台默认通用模型，行业删除白名单由扩展提供 | `smart_core` + 扩展模块 |
| `addons/smart_core/core/scene_delivery_policy.py` | surface policy | 交付面策略/白名单 | 待审→已治理 | 内建 construction 策略迁移为扩展注入（名称/文件/白名单） | `smart_core` + 扩展模块 |
| `addons/smart_core/core/workspace_home_contract_builder.py` | workspace scene routing | 工作台动作与场景路由 | 待审→已治理（阶段性） | 场景别名与 source→scene 路由改由 profile provider 注入，页面动作目标不再在平台层写死 | `smart_core`（编排骨架） + 行业 profile（语义映射） |
| `addons/smart_core/core/workspace_home_contract_builder.py` | workspace defaults semantics | 工作台默认文案与 fallback 场景语义 | 待审→已治理（第二阶段） | 平台默认场景别名从行业场景降为通用 workspace.*；默认文案从行业词汇降为平台词汇；业务语义继续由 provider hook 覆盖 | `smart_core`（通用 fallback） + 行业 profile（语义覆盖） |
| `addons/smart_core/core/workspace_home_contract_builder.py` | risk/ops payload semantics | 风险区与运行区语义结构 | 待审→已治理（第三阶段） | `risk`/`ops` 的 summary/trend/sources/tone/progress/data_state 改为 provider hook-first，平台仅保留协议 fallback | `smart_core`（协议骨架） + 行业 profile（语义实现） |
| `addons/smart_core/core/workspace_home_contract_builder.py` | role expectation & ranking semantics | 角色期望集合与动作排序权重 | 待审→已治理（第四阶段） | 角色期望集合、排序权重改为 provider hook-first，平台 fallback 改为通用键集合，行业键映射在 profile 提供 | `smart_core`（协议骨架） + 行业 profile（语义实现） |
| `addons/smart_core/core/workspace_home_contract_builder.py` | keyword/state token semantics | 语义关键词与状态词典 | 待审→已治理（第五阶段） | 风险识别 token、紧急/关注状态词典、紧急关键词改为 provider hook-first，平台仅保留通用 fallback | `smart_core`（协议骨架） + 行业 profile（语义实现） |
| `addons/smart_core/core/workspace_home_contract_builder.py` | orchestration zone/focus priority semantics | 编排分区与焦点优先级 | 待审→已治理（第六阶段） | role_zone_order 与 v1_focus_map 改为 provider hook-first，平台保留默认顺序 fallback | `smart_core`（编排骨架） + 行业 profile（语义实现） |
| `addons/smart_core/core/workspace_home_contract_builder.py` | orchestration copy semantics | 编排页分区/块标题与页面文案 | 待审→已治理（第七阶段） | `_build_page_orchestration_v1` 中 zone/block/page/action 文案改为 provider hook-first（`build_v1_copy_overrides`） | `smart_core`（编排骨架） + 行业 profile（语义实现） |
| `addons/smart_core/handlers/api_data.py` | create fallback semantics | 创建兜底字段策略 | 待审→已治理（第八阶段） | 去除平台层 `project.project` 特判，改为通用兜底 + extension hook `smart_core_create_field_fallbacks` | `smart_core`（通用兜底） + 行业扩展（模型特例） |
| `addons/smart_core/handlers/load_contract.py` | model code mapping semantics | model_code 别名映射 | 待审→已治理（第八阶段） | 去除平台层 project/task 别名硬编码，改为 extension hook `smart_core_model_code_mapping` 注入 | `smart_core`（通用映射骨架） + 行业扩展（映射定义） |
| `addons/smart_core/core/scene_delivery_policy.py` | surface default semantics | 交付面策略默认值 | 待审→已治理（第八阶段） | 平台默认策略名/allowlist 从 construction 特定降为 workspace 通用值；行业策略继续由扩展注入覆盖 | `smart_core`（通用默认） + 行业扩展（策略覆盖） |
| `addons/smart_core/core/scene_ready_contract_builder.py` | scene-ready seed action injection | 场景动作种子注入入口 | 待审→已治理（第八阶段，部分） | `_scene_ready_entry` 先读取 provider payload，支持 `default_actions` 与 `skip_pilot_seed`，减少平台层直接场景特判命中 | `smart_core`（注入入口） + scene provider（场景语义） |
| `addons/smart_core/core/scene_ready_contract_builder.py` | pilot strict scope semantics | pilot 严格模式场景范围 | 待审→已治理（第九阶段） | pilot strict 范围从行业场景白名单收敛为 `workspace.home` 默认，行业场景由 provider 明确声明 | `smart_core`（最小默认） + scene provider（场景声明） |
| `addons/smart_core/utils/contract_governance.py` | governance primary model semantics | 治理主模型判定 | 待审→已治理（第九阶段，部分） | `project.project` 强匹配改为 `_governance_primary_model`，支持从治理上下文注入主模型；demo marker 去除 `smart_construction_demo` 字面量 | `smart_core`（治理骨架） + 上层契约（模型声明） |
| `addons/smart_core/handlers/app_shell.py` | app surface fallback intents | `app.catalog` / `app.nav` / `app.open` 通用兜底 | 待审→已治理（第十阶段） | 在 `smart_core` 提供最小 app intent 兜底，确保未启用 construction 扩展时仍保留系统启动面与导航能力 | `smart_core`（最小兜底） + 扩展模块（覆写实现） |
| `addons/smart_construction_scene/profiles/workspace_home_scene_content.py` | workspace scene aliases | 行业工作台场景语义映射 | 保留（行业侧） | 承载行业 scene alias 与 source 语义路由 | `smart_construction_scene` |
| `addons/smart_core/handlers/system_init.py` | system.init | 平台启动契约聚合 | 保留（带治理） | extension facts 合并曾绑定特定模块名；本批改为通用 namespaced 合并 | `smart_core` |
| `addons/smart_core/handlers/scene_package.py` | scene package handler | 场景包治理入口 | 待审→已治理 | 由扩展 hook 提供 service class，平台层不再直接导入建设模块 | `smart_core`（handler 壳） + 扩展模块（service 提供） |
| `addons/smart_core/handlers/scene_packages_installed.py` | scene package installed | 场景包清单查询 | 待审→已治理 | 同上，改为扩展注入 | `smart_core`（handler 壳） + 扩展模块（service 提供） |
| `addons/smart_core/handlers/scene_governance.py` | scene governance handler | 场景治理入口 | 待审→已治理 | 同上，改为扩展注入 | `smart_core`（handler 壳） + 扩展模块（service 提供） |
| `addons/smart_core/security/*.xml` | 平台安全组 | 平台治理权限 | 保留 | 已完成 canonical 组治理 | `smart_core` |
| `addons/smart_core/tools/intent_write_guard.py` | verify guard | 写入意图守卫 | 待审 | 规则扫描路径包含建设模块，需抽象为可配置扫描目标 | `smart_core` |

## 本批收口结论

- 已完成：`identity / capability / nav adapter / system.init ext_facts` 的平台层去行业硬编码。
- 已冻结：平台层通过 extension hooks 获取行业映射与能力，不再直接导入建设行业实现。
- 待下一批：按同样模式治理 `tests` 中的行业示例依赖，并继续拆分 `contract_governance.py` 的 project-form 专项规则为可配置 profile（当前函数命名与字段清单仍偏历史语义）。
