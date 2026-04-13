# 后端核心重构实施蓝图 v1

状态：Draft (scan阶段冻结)

## 1. 目标与边界

本轮目标是将后端不确定性收敛为四条可审计主链：

- Intent Dispatcher
- Intent Registry
- Parser/Resolver
- Contract Builder + Response Envelope

本蓝图只定义重构路径与守卫，不在本批直接改动高风险业务实现。

硬边界：

- 不修改 `security/**`、`record_rules/**`、`__manifest__.py`
- 不直接改 `payment/settlement/account` 业务语义
- 不在 controller/handler 中新增临时业务分支

## 2. 扫描结论（当前代码现实）

已识别的关键现状：

- 意图入口主要集中在 `addons/smart_core/controllers/intent_dispatcher.py`
- handler 注册依赖 `addons/smart_core/core/handler_registry.py` 自动扫描注册
- 核心分发在 `addons/smart_core/core/intent_router.py`
- 基类入口在 `addons/smart_core/core/base_handler.py`
- 解析层存在多实现并存：`addons/smart_core/view/universal_parser.py` 及 `form/tree/kanban/search` parser
- 契约组装存在多口径：`addons/smart_core/view/native_view_contract_builder.py`、`workspace_home_contract_builder`、controller 局部封装
- 响应封装存在多层：`controllers/api_base.py`、`utils/response_builder.py`、`intent_dispatcher` 内归一逻辑

当前不确定性根因：

1. 缺少显式 `Intent Registry` 元数据总账本（现为运行时扫描注册）。
2. Dispatcher/Router 与 Handler 边界有历史兼容逻辑混杂。
3. Parser 与业务裁剪/权限可见性尚未完全解耦。
4. Contract Builder 与 Response Envelope 未形成单一冻结出口。

## 3. 目标链路（冻结版）

目标执行链：

```text
HTTP/API Entry
  -> Intent Dispatcher
    -> Intent Registry
      -> Request Validator
        -> Handler
          -> Domain Service / Orchestrator
            -> Parser / Resolver / Collector
              -> Contract Builder
                -> Response Envelope
```

职责冻结：

- Controller：只做协议适配、上下文注入、统一响应。
- Intent Dispatcher：只做分发、校验编排、异常包装。
- Intent Registry：只做 intent 元数据声明与查找。
- Request Validator：只做 payload/context/schema 校验。
- Handler：只做用例编排。
- Domain Service：只做业务事实处理。
- Orchestrator：只做跨 service 编排。
- Parser：只做结构解析，不做业务裁剪。
- Contract Builder：只做稳定契约输出。
- Response Envelope：只做统一响应壳。

## 4. 目录收口目标（v1）

```text
addons/smart_core/
  controllers/
  intents/
    registry.py
    registry_entries/
    schemas/
    handlers/
  orchestration/
  services/
  parsers/
  builders/
  policies/
  contracts/
    schemas/
    snapshots/
  scripts/verify/
  tests/
```

说明：本轮不做大规模迁移，只先建立并行骨架 + 守卫，再逐批迁移。

## 5. 分批实施路线（A~H）

### A. 意图总账本

1. 建 `intents/registry.py` 与 `registry_entries/*`
2. intent 元数据最小集：
   - `intent_name`
   - `handler_class`
   - `request_schema`
   - `response_contract`
   - `capability_code`
   - `permission_mode`
   - `idempotent`
   - `version`
   - `tags`
3. 增加 `intent_registry_audit`

### B. Dispatcher/Handler 链路收口

1. controller 极薄化模板落地
2. dispatcher 去业务化，仅流程控制
3. handler 用例化：一个 handler 对应一个用例

### C. 处理层归位

1. 拆分 handler / orchestrator / service / builder
2. 领域结果对象化（dataclass/result object）
3. service 禁止直接返回前端 contract

### D. 解析层重构

1. 建 `BaseParser` 基座
2. 统一 form/tree/kanban/search 解析骨架
3. parser 输出统一 diagnostics/coverage

### E. 契约输出冻结

1. 建统一 Contract Builder 层
2. 冻结 Response Envelope
3. 引入 `contract_version` + `schema_version`

### F. 权限与策略抽离

1. `permission_service.py`
2. `capability_policy.py`
3. `contract_visibility_policy.py`

### G. 守卫与回归

新增 verify（命名冻结）：

- `verify.arch.intent_registry_unique`
- `verify.arch.controller_thin_guard`
- `verify.arch.handler_contract_boundary_guard`
- `verify.arch.service_no_frontend_contract_guard`
- `verify.arch.parser_no_business_query_guard`
- `verify.arch.builder_no_orm_access_guard`
- `verify.contract.public_snapshot_guard`
- `verify.contract.envelope_consistency_guard`
- `verify.parser.coverage_guard`

### H. 文档与规范冻结

输出四份规范：

- 《后端意图开发规范》
- 《后端契约输出规范》
- 《解析器设计规范》
- 《后端目录与职责边界规范》

## 6. Response Envelope 冻结草案

```json
{
  "ok": true,
  "data": {},
  "error": null,
  "meta": {
    "trace_id": "",
    "intent": "",
    "contract_version": "",
    "schema_version": "",
    "latency_ms": 0
  },
  "effect": null
}
```

禁止出现并行口径：`success/status/code/result` 多壳并存。

## 7. 反模式禁令（立即生效）

- controller 直接 ORM 查询并返回 JSON
- handler 同时做业务 + 解析 + 契约组装
- service 直接返回前端 contract 字段
- parser 直接做业务裁剪/权限决策
- builder 直接访问 ORM
- 无版本号契约直接对外发布

## 8. 下一批执行建议（1523 起）

按低成本 staged 模式继续：

1. `scan`：intent 清单与重复语义扫描（不改代码）
2. `screen`：分类到 A/B/C/D/E/F/G/H 具体批次
3. `verify`：先落 A1/A2 的 registry 骨架与审计脚本

建议先做的最小可执行批次：

- 1523：`intents/registry.py` 骨架 + audit（只读映射，不替换现路由）

## A1 Closure Status (2026-04-09)

- A1（intent registry coverage）已完成闭环：
  - `registered=46`
  - `discovered=46`
  - `missing=0`
- 关键收口批次：
  - `1546`：修复 registry audit 多模块来源解析
  - `1547~1549`：Tier-2 三批迁移
  - `1550`：Tier-3 最后一批迁移
- 冻结文档：`docs/architecture/intent_registry_closure_v1.md`

## B-line Thinness Status (2026-04-09)

- `controller_thin_guard` 已收敛：
  - `over_threshold_count=0`
  - `orm_hint_count=0`
- 关键收口批次：
  - `1553`：`platform_meta_api.describe_model`
  - `1554`：`platform_portal_execute_api.portal_execute_button`
  - `1555`：Tier-3 两个候选清零
  - `1556`：strict fail-gate enabled
- 冻结文档：`docs/architecture/controller_thin_guard_v1.md`
- 1524：controller thin guard（只加 verify，不改业务）
- 1525：envelope consistency guard（只比对公开 API 输出壳）

## B2 Dispatcher Purity Screen (2026-04-09)

- screen 批次 `1558` 已冻结 dispatcher purity 候选优先级（仅治理筛查，无代码变更）。
- 冻结文档：`docs/architecture/dispatcher_purity_screen_v1.md`
- implement 顺序（冻结）：
  - `B2-1`：DB resolution policy + request normalizer 外移
  - `B2-2`：commit/effect policy 外移
  - `B2-3`：permission detail / alias/schema governance helper 外移
  - `B2-4`：legacy compatibility adapter 收口

## B2-1 implement (2026-04-09)

- 完成 `intent_request_normalizer` 抽离：
  - `normalize_dispatch_payload`
  - `resolve_effective_db`
- `intent_dispatcher` 由内联 DB 解析分支改为调用 helper，主流程职责收敛。

## B2-2 implement (2026-04-09)

- 完成 `intent_effect_policy` 抽离：
  - `is_write_intent`
  - `should_commit_write_effect`
- `intent_dispatcher` 不再内置写意图正则与提交触发判断，改为 policy helper 调用。

## B2-3 implement (2026-04-09)

- 完成 `intent_governance` 抽离：
  - `canon_intent`
  - `resolve_request_schema_key`
- 完成 `intent_permission_details` 抽离：
  - `build_permission_error_details`
- `intent_dispatcher` 不再内置 alias/schema map 与 api.data 权限细节拼接。

## B2-4 implement (2026-04-09)

- 完成 `intent_legacy_compat` 抽离：
  - `apply_legacy_load_view_compat`
- `intent_dispatcher._finalize_dispatch_response` 不再内置 load_view legacy data 修补细节。

## C-line Boundary Screen (2026-04-09)

- screen 批次 `1563` 已冻结 C-line 候选与实施顺序（仅治理筛查，无代码变更）。
- 冻结文档：`docs/architecture/c_line_boundary_screen_v1.md`
- implement 切片（冻结）：
  - `C1-1`：intent_router env/cursor policy 抽离
  - `C1-2`：system_init data fetch helper 化
  - `C1-3`：load_contract handler 边界收敛
  - `C1-4`：handler output object 化接入与兼容收尾

## C1-1 implement (2026-04-09)

- 完成 `intent_env_policy` 抽离：
  - `build_dispatch_envs`
  - `finalize_dispatch_cursor`
- `intent_router` 不再内置 env/cursor 生命周期逻辑，改为 policy helper 调用。

## C1-2 implement (2026-04-10)

- 完成 `system_init_dictionary_data_helper` 抽离：
  - `apply_dictionary_startup_data`
- `system_init` handler 不再内置 role_entries/home_blocks 的字典抓取与聚合细节。

## C1-3 implement (2026-04-10)

- 完成 `load_contract_boundary_helper` 抽离：
  - `read_module_install_state`
  - `build_unknown_model_message`
  - `build_contract_response_payload`
- `load_contract` handler 不再内置模块状态诊断字符串拼接与响应 payload 组装细节。

## C1-4 Output Objectization Screen (2026-04-10)

- screen 批次 `1567` 已冻结 handler output objectization 实施顺序（仅治理筛查）。
- 冻结文档：`docs/architecture/c1_4_output_objectization_screen_v1.md`
- implement 切片（冻结）：
  - `C1-4-1`：IntentExecutionResult + BaseIntentHandler adapter
  - `C1-4-2`：dispatcher normalize 对象兼容
  - `C1-4-3`：低风险 handler 试点
  - `C1-4-4`：输出口径审计与文档冻结

## C1-4-1 implement (2026-04-10)

- 完成 `IntentExecutionResult` 对象引入：
  - `addons/smart_core/core/intent_execution_result.py`
- `BaseIntentHandler.run()` 增加对象返回兼容适配：
  - `adapt_handler_result(...)`
- 保持 legacy dict 返回链路兼容，未改变公开接口形态。

## C1-4-2 implement (2026-04-10)

- `intent_dispatcher._normalize_result_shape` 已支持对象输入兼容：
  - 若返回对象实现 `to_legacy_dict()`，先转换为 legacy dict 再走统一归一。
- 与 `C1-4-1` 底座配套，保持外部响应口径不变。

## C1-4-3 implement (2026-04-10)

- 低风险 handler 对象返回试点完成：
  - `login`
  - `session.bootstrap`
- 两个 handler 成功路径改为 `IntentExecutionResult` 返回，依赖 C1-4-1/C1-4-2 兼容链路保持对外口径不变。

## C1-4-4 implement (2026-04-10)

- 新增输出口径审计脚本：
  - `scripts/verify/handler_output_style_audit.py`
- 冻结对象化 guard 文档：
  - `docs/architecture/handler_output_objectization_guard_v1.md`
- C1-4 从底座接入到低风险试点与审计门禁形成闭环。

## C1-4-3 extend (2026-04-10)

- 对象返回试点扩展到：
  - `meta_describe`
  - `permission_check`
- 结合 `login`、`session.bootstrap`，低风险对象化样本扩展为 4 个 handler。

## C1-4-3 extend-2 (2026-04-10)

- 对象返回试点继续扩展到文件意图：
  - `file.download`
  - `file.upload`
- `_err` 与成功返回统一切换为 `IntentExecutionResult`，保持对外契约兼容。

## C1-4 ui_contract screen (2026-04-10)

- screen 批次 `1574` 冻结 `ui_contract` 对象化范围：
  - Tier-1：仅主成功分支
  - Tier-2：etag/not_modified 扩展
  - Tier-3：错误分支与 legacy 路径
- 禁止在对象化批次同时改动 scene/delivery/权限裁剪链。

## C1-4 ui_contract Tier-1 implement (2026-04-10)

- 按 safe slice 执行：`ui_contract` 主成功返回分支改为 `IntentExecutionResult`。
- `_err` 分支与 scene/delivery/permission 相关逻辑保持不变。

## C1-4 ui_contract Tier-2 implement (2026-04-10)

- 按 safe Tier-2 执行：`ui_contract` 的 not_modified/etag 分支改为 `IntentExecutionResult(code=304)`。
- 错误分支与高耦合链路保持不变。

## C1-4 load_contract Tier-1 implement (2026-04-10)

- `load_contract` 主成功返回（code=200）改为 `IntentExecutionResult`。
- `_err` 分支与 `not_modified`(304) 返回保持原口径不变。

## C1-4 system_init Tier-1 implement (2026-04-10)

- `system_init` 主成功返回切换为 `IntentExecutionResult`。
- 诊断、错误、权限与场景链路逻辑保持不变。

## C1-4 api_onchange Tier-1 implement (2026-04-10)

- `api_onchange` 两个成功返回分支已切换为 `IntentExecutionResult`。
- `_err` 分支保持不变，onchange 语义与补丁计算逻辑不变。

## C1-4 efficiency audit enhance (2026-04-10)

- `handler_output_style_audit` 新增 `next_candidates` 候选排序输出。
- 迭代选择从人工筛查升级为脚本推荐，提高连续批次执行效率。

## C1-4 high-efficiency api_data family batch (2026-04-10)

- 按同类改动打包策略一次迁移 `api_data_batch`、`api_data_unlink` 的成功返回到 `IntentExecutionResult`。
- 同步迁移 `api_data` 的 ETag 304 成功返回分支到对象化链路。
- `_err` 与业务/权限语义保持不变，仅统一成功返回封装。

## C1-4 high-efficiency api_data_write batch (2026-04-10)

- `api_data_write` 的 create/write 两条主链成功返回与两条 replay 成功返回统一迁移为 `IntentExecutionResult`。
- `_err` 与冲突/权限/系统错误分支保持不变，仅收敛成功输出口径。

## v2 shadow scaffold (2026-04-10)

- 在 `addons/smart_core/v2` 建立影子重构骨架：
  - `intents/registry.py`（统一注册）
  - `dispatcher.py`（统一分发）
  - `handlers/base.py`（handler 模板）
  - `services/system_service.py`（业务服务）
  - `builders/system_builder.py`（契约组装）
  - `contracts/envelope.py`（统一返回壳）
- 提供最小可运行链路 `system.ping`，用于后续增量迁移验证。
- 本批未切换旧运行时入口，保持旧链路不受影响。

## v2 validator-policy-readonly intent batch (2026-04-10)

- 在 `v2` 新增职责层模板：
  - `validators/base.py`（请求校验）
  - `policies/permission_policy.py`（权限策略）
- `dispatcher` 接入 validator 与 permission policy，形成统一门禁入口。
- 新增只读意图 `system.registry.list`（authenticated）用于并行链路验证。

## v2 large-batch rebuild skeleton (2026-04-10)

- 一次性补齐 `v2` 完整分层骨架：
  - `parsers/base.py`、`orchestrators/base.py`
  - `contracts/result.py`（`IntentExecutionResultV2`）
  - `reasons.py`（统一错误码）
- `dispatcher` 接入结果对象归一与 reason code 统一包装。
- 新增 `scripts/verify/v2_boundary_audit.py` 作为 v2 架构边界守卫。
- 新增 `docs/architecture/backend_core_v2_rebuild_spec_v1.md` 冻结迁移原则、职责边界、切换策略。

## v2 meta readonly migration batch (2026-04-10)

- 新增首个 v2 meta 只读意图：`meta.registry.catalog`。
- 新增 `services/meta_service.py` 与 `builders/meta_builder.py`，实现 registry 元信息只读输出。
- 新增 `scripts/verify/v2_intent_comparison_audit.py`，提供 old-v2 意图迁移对照基线。

## v2 meta.describe_model migration batch (2026-04-10)

- 迁移 `meta.describe_model` 到 v2（并行只读实现）。
- 增加 `handlers/meta/describe_model.py`、`MetaService.describe_model_stub`、`build_describe_model_contract`。
- `v2_intent_comparison_audit` 可见 migrated 数增长，作为后续迁移节奏基线。

## v2 permission.check migration batch (2026-04-10)

- 迁移 `permission.check` 到 v2（并行只读实现）。
- 增加 `handlers/meta/permission_check.py`、`MetaService.permission_check_stub`、`build_permission_check_contract`。
- 迁移覆盖率继续提升，并保持旧运行时不切换。

## v2 meta.intent_catalog migration batch (2026-04-10)

- 迁移 `meta.intent_catalog` 到 v2（并行只读实现）。
- 增加 `handlers/meta/intent_catalog.py`、`MetaService.build_intent_catalog`、`build_intent_catalog_contract`。
- 复用 registry 元数据输出 intent catalog，保持 schema_version 与 source 字段稳定。

## independent full-rebuild backbone (2026-04-10)

- v2 启用独立重构主线：`kernel/context.py`、`kernel/spec.py`、`kernel/pipeline.py`。
- `dispatcher` 切换到 `RebuildPipelineV2`，由 pipeline 统一承载 validator/policy/handler 流程。
- 引入 taxonomy modules：新增 `modules/app/*` 并落地 `app.catalog`。
- 新增 `scripts/verify/v2_rebuild_audit.py` 作为独立重构骨架审计门禁。

## independent app taxonomy expansion (2026-04-10)

- 在 `modules/app` 扩展 `app.nav` 与 `app.open`。
- 补齐 `AppCatalogServiceV2` 的 nav/open 服务输出与对应 builder contract。
- `v2_rebuild_audit` 增加 nav/open 文件门禁，确保独立重构骨架完整。

## app route policy and active match batch (2026-04-10)

- 新增 `modules/app/policies/navigation_policy.py`，统一 route 与 active_match 生成。
- `app.catalog`、`app.nav`、`app.open` 全部接入 route policy 语义。
- builder 输出统一包含 `route`/`active_match`，保持导航表达一致。

## app contract target type and delivery mode (2026-04-10)

- `app.catalog`/`app.nav`/`app.open` 输出统一补齐 `target_type` 与 `delivery_mode`。
- 语义口径：`app/custom_app`、`nav/custom_nav`、`open/custom_open`。

## app availability and clickability batch (2026-04-10)

- `app.catalog`/`app.nav`/`app.open` 输出统一补齐 `is_clickable`、`availability_status`、`reason_code`。
- 默认语义：可点击节点 `available` + 空 reason_code。

## app availability classification batch (2026-04-10)

- 新增 `modules/app/policies/availability_policy.py`，按 app_key/target 分类输出 `available/degraded/unavailable`。
- app 服务层统一经可用性策略生成 `is_clickable` 与 `reason_code`。

## reason_code enum audit batch (2026-04-10)

- 新增 `modules/app/reason_codes.py`，冻结 reason_code 枚举集合。
- builder 层统一使用 `normalize_reason_code`，避免 reason_code 漂移。
- 新增 `scripts/verify/v2_app_reason_code_audit.py` 作为枚举门禁审计。

## app contract field guard batch (2026-04-10)

- 新增 `scripts/verify/v2_app_contract_guard_audit.py`，对 `app.catalog/app.nav/app.open` 合同字段做统一门禁。
- 审计字段覆盖：`target_type`、`delivery_mode`、`is_clickable`、`availability_status`、`reason_code`、`route`、`active_match`。
- 审计同时验证 `availability_status` 与 `reason_code` 枚举合法性，防止语义漂移。

## app contract snapshot baseline batch (2026-04-10)

- 新增快照：`artifacts/v2/app_contract_snapshot_v1.json`。
- 新增审计：`scripts/verify/v2_app_contract_snapshot_audit.py`。
- 审计将 `app_contract_snapshot_v1` 与 builder 关键字段进行对照，形成 contract 变更门禁。

## app intent contract linkage batch (2026-04-10)

- 新增 `scripts/verify/v2_app_intent_contract_linkage_audit.py`。
- 该审计同时校验：
  - `v2/intents/registry.py` 的 `app.catalog/app.nav/app.open` 与 response_contract 声明
  - `artifacts/v2/app_contract_snapshot_v1.json` 的 schema 集合一致性

## app governance gate batch (2026-04-10)

- 新增 `scripts/verify/v2_app_governance_gate_audit.py` 作为 app 治理一键门禁。
- 聚合审计包含：`reason_code`、`contract_guard`、`snapshot`、`intent-contract linkage`。

## app verify naming batch (2026-04-10)

- 在 `Makefile/makefile` 新增统一入口：
  - `verify.v2.app.reason_code`
  - `verify.v2.app.contract`
  - `verify.v2.app.snapshot`
  - `verify.v2.app.linkage`
  - `verify.v2.app.governance`
- 支持通过 make 一键触发 v2 app 治理门禁，提升连续迭代执行效率。

## app governance alias batch (2026-04-10)

- 新增 `scripts/verify/v2_app_verify_all.py` 作为 app 门禁脚本别名。
- 新增 `make verify.v2.app.all` 统一入口（委托 `verify.v2.app.governance`）。
- 新增使用文档：`docs/ops/v2_app_governance_gate_usage_v1.md`。

## app governance diagnostics batch (2026-04-10)

- 增强 `v2_app_governance_gate_audit.py` 输出：
  - `summary.total_checks/pass_checks/fail_checks`
  - `failure_reasons`
- 增强 `v2_app_verify_all.py`，透传 summary 与 failure_reasons 便于一键诊断。

## app governance output schema snapshot batch (2026-04-10)

- 新增输出 schema 快照：`artifacts/v2/v2_app_governance_output_schema_v1.json`。
- 新增输出 schema 审计：`scripts/verify/v2_app_governance_output_schema_audit.py`。
- 固化 governance gate 根字段、summary 字段、details 字段结构门禁。

## app governance ci light batch (2026-04-10)

- 新增 make 目标：`verify.v2.app.ci.light`（委托 `verify.v2.app.all`）。
- 新增审计：`scripts/verify/v2_app_ci_light_entry_audit.py`，校验 make/doc 入口一致性。
- 新增文档：`docs/ops/v2_app_governance_ci_entry_v1.md`。

## app ci-light schema guard batch (2026-04-10)

- `verify.v2.app.ci.light` 增加 `v2_app_governance_output_schema_audit` 串联执行。
- `v2_app_ci_light_entry_audit` 增加 schema guard 入口一致性校验。

## app governance detail-link batch (2026-04-10)

- `v2_app_governance_gate_audit` 新增聚合检查：`v2_app_ci_light_entry_audit.py`。
- governance gate 详情链路现在同时覆盖 ci-light 入口一致性。

## app governance gate version batch (2026-04-10)

- `v2_app_governance_gate_audit` 输出新增 `gate_version`。
- `v2_app_verify_all` 透传 `gate_version`。
- `v2_app_governance_output_schema_v1` 将 `gate_version` 纳入 root 字段门禁。

## app governance gate profile batch (2026-04-10)

- governance 输出新增 `gate_profile`（`full` / `ci_light`）。
- output schema snapshot 增加 `gate_profile` root 字段与枚举守卫。

## app ci-light audit output batch (2026-04-10)

- `v2_app_ci_light_entry_audit` 输出新增 `gate_version` 与 `gate_profile`。
- ci-light 审计输出语义与 governance 主门禁版本/剖面口径保持一致。

## app audit common output contract batch (2026-04-10)

- 统一 `v2_app_*_audit` 最小输出协议：`gate_version/gate_profile/status/errors`。
- 保障聚合门禁与单项审计输出具备一致解析口径。

## cross-audit common output contract batch (2026-04-10)

- 统一 `v2_boundary_audit` / `v2_rebuild_audit` / `v2_intent_comparison_audit` 输出最小协议：
  - `gate_version`
  - `gate_profile`
  - `status`
  - `errors`
- 保障 v2 核心审计脚本可被同一治理门禁稳定聚合。

## cross-audit integrated into governance gate batch (2026-04-10)

- `v2_app_governance_gate_audit` 详情链路新增：
  - `v2_boundary_audit.py`
  - `v2_rebuild_audit.py`
  - `v2_intent_comparison_audit.py`
- governance 一键门禁现在同时覆盖 app 与 core v2 cross-audit。

## governance expected_checks snapshot batch (2026-04-10)

- `v2_app_governance_output_schema_v1` 新增 `expected_checks`，冻结门禁详情检查集合。
- `v2_app_governance_output_schema_audit` 增加 expected/missing/extra 检查比对，防止检查集合静默漂移。

## verify_all root errors alignment batch (2026-04-10)

- `v2_app_verify_all` 根输出新增 `errors`，与公共最小输出契约完全对齐。
- 当 delegate 失败时优先透传 `failure_reasons`，否则提供兜底错误码。

## verify_all failure-path guard batch (2026-04-10)

- 新增 `v2_app_verify_all_failure_path_audit`：注入 delegate 失败并断言 root `errors` 非空。
- `v2_app_verify_all` 增加 `V2_APP_VERIFY_ALL_DELEGATE_CMD` 覆写能力，用于失败路径守卫测试。

## failure-path guard integrated into governance gate batch (2026-04-10)

- `v2_app_governance_gate_audit` 新增 `v2_app_verify_all_failure_path_audit` 详情检查。
- `v2_app_governance_output_schema_v1` 的 `expected_checks` 同步纳入该检查，避免守卫被静默移除。
