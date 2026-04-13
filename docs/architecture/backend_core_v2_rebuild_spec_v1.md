# 后端核心重建实施规范（v2）

## 目标

在 `addons/smart_core/v2` 内建立一套与旧实现解耦的后端主干架构，满足：

- 独立重构主线
- kernel pipeline 统一调度
- taxonomy modules 可扩展

- 职责边界清晰
- 输出口径统一
- 可并行迁移与可回滚
- 最终可替换旧链路

## 迁移原则

- 先重建骨架，再迁移意图
- 旧入口不中断，v2 并行验证
- 每批必须可验证、可审计、可回滚
- 事实层不被解释层污染

## 职责边界

- `intents/registry.py`：意图总账本与注册元数据
- `dispatcher.py`：流程调度、校验、权限门禁、异常封装
- `validators/*`：请求参数与上下文校验
- `policies/*`：权限与可见性策略判定
- `handlers/*`：单用例编排入口
- `services/*`：领域事实处理
- `parsers/*`：结构解析，不做业务决策
- `orchestrators/*`：跨服务编排
- `builders/*`：契约组装
- `contracts/*`：响应壳与结果对象
- `kernel/*`：独立运行时内核（context/spec/pipeline）
- `modules/*`：按领域分类的 taxonomy modules（app/meta/system/...）
- `modules/*/policies/*`：模块内语义策略（如 route policy、active_match 规则）
- `modules/*/reason_codes.py`：模块级 reason_code 枚举冻结源

## 切换策略

1. v2 新增意图先并行上线（不替换旧入口）
2. 同一意图做旧/v2 输出对照
3. snapshot 与 verify 全通过后，执行 dispatcher 单点切流
4. 灰度稳定后再下线旧实现

## 禁止项

- controller/dispatcher 直接写业务事实
- service 返回前端专用拼装字段
- parser 执行业务权限裁剪
- builder 访问 ORM
- 未经快照审计直接变更公开契约

## 验证门禁

- `scripts/verify/v2_boundary_audit.py`
- `py_compile`（v2 关键链路）
- registry/dispatcher/builder 符号审计
- 迭代报告 + task_results + delivery_context log

## app contract guard

- app taxonomy 输出字段必须保持一致：
  - `target_type`
  - `delivery_mode`
  - `is_clickable`
  - `availability_status`
  - `reason_code`
  - `route`
  - `active_match`
- 使用 `scripts/verify/v2_app_contract_guard_audit.py` 进行合同字段与枚举口径审计。

## app contract snapshot baseline

- `artifacts/v2/app_contract_snapshot_v1.json` 是 app taxonomy contract 回归基线。
- 任何 `app.catalog/app.nav/app.open` 字段变更必须同步快照并通过 `v2_app_contract_snapshot_audit`。

## app intent-contract linkage guard

- app taxonomy 入口（intent registry）与 contract 快照（snapshot）必须联动审计。
- 使用 `v2_app_intent_contract_linkage_audit` 确保 `intent_name -> response_contract -> snapshot schema` 一致。

## app one-shot governance gate

- 使用 `v2_app_governance_gate_audit` 可一键执行 app contract 治理门禁。
- 该脚本用于连续迭代中的高效回归，不替代单项审计脚本的职责边界。

## verify naming alignment for v2 app

- v2 app 治理验证入口统一为 `verify.v2.app.*` 前缀。
- 推荐使用 `make verify.v2.app.governance` 作为连续迭代默认门禁入口。

## v2 app governance alias

- 推荐脚本别名：`python3 scripts/verify/v2_app_verify_all.py --json`。
- 推荐 make 别名：`make verify.v2.app.all`。

## v2 app governance diagnostics output

- `v2_app_governance_gate_audit` 必须输出 `summary` 与 `failure_reasons`。
- `v2_app_verify_all` 需透传聚合摘要用于 CI/本地快速诊断。

## v2 app governance output schema snapshot

- governance gate 输出结构以 `v2_app_governance_output_schema_v1` 为冻结基线。
- 变更输出字段时必须更新快照并通过 `v2_app_governance_output_schema_audit`。

## v2 app governance ci light entry

- 轻量 CI 入口统一为 `make verify.v2.app.ci.light`。
- 入口一致性由 `v2_app_ci_light_entry_audit` 审计保障。

## v2 app ci-light schema guard linkage

- `verify.v2.app.ci.light` 必须包含 `v2_app_governance_output_schema_audit`，确保轻量入口覆盖输出结构门禁。

## v2 app governance detail linkage

- governance gate 详情链路必须包含 `v2_app_ci_light_entry_audit`。

## v2 app governance gate version

- governance 输出必须携带 `gate_version`，并由 output schema snapshot 守卫。

## v2 app governance gate profile

- governance 输出必须包含 `gate_profile`，取值为 `full` 或 `ci_light`。

## v2 ci-light audit output semantics

- `v2_app_ci_light_entry_audit` 输出必须包含 `gate_version` 与 `gate_profile`。

## v2 app audit common output contract

- `v2_app_*_audit` 最小公共字段：`gate_version`、`gate_profile`、`status`、`errors`。

## v2 cross-audit common output contract

- `v2_boundary_audit`、`v2_rebuild_audit`、`v2_intent_comparison_audit` 最小公共字段统一为：
  - `gate_version`
  - `gate_profile`
  - `status`
  - `errors`

## v2 cross-audit governance integration

- `v2_app_governance_gate_audit` 必须纳入：
  - `v2_boundary_audit`
  - `v2_rebuild_audit`
  - `v2_intent_comparison_audit`
- 目标：治理门禁一键覆盖 app + core v2 cross-audit。

## governance expected_checks snapshot

- `v2_app_governance_output_schema_v1` 维护 `expected_checks` 清单。
- output schema audit 必须校验 details.check 与 `expected_checks` 一致（缺失/新增均失败）。

## verify_all root errors alignment

- `v2_app_verify_all` 根输出必须包含 `errors` 字段。
- `status=FAIL` 时 `errors` 不能为空（优先使用 delegate failure_reasons）。

## verify_all failure-path guard

- 新增 `v2_app_verify_all_failure_path_audit` 作为失败路径守卫。
- 通过 `V2_APP_VERIFY_ALL_DELEGATE_CMD` 注入失败 delegate，校验 `status=FAIL` 与 root `errors` 非空。

## governance integration for verify_all failure-path guard

- 主门禁 `v2_app_governance_gate_audit` 必须包含 `v2_app_verify_all_failure_path_audit`。
- governance output schema `expected_checks` 必须包含该检查名，形成快照守卫。
