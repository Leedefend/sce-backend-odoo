# v1.0 工作台后端收口重构报告（本轮）

## 1. 目标与范围

本轮在 `release/construction-system-v1.0` 上完成工作台后端收口重构，目标是将 `portal.dashboard` 从“系统能力摘要页”推进为“业务行动中枢”。

边界遵循：

- 不修改登录链路、ACL 权限基线、scene governance、delivery policy 主机制。
- `page_orchestration_v1` 作为主协议。
- `page_orchestration` 保留 legacy 兼容。

## 2. 关键改动文件

- `addons/smart_core/core/workspace_home_contract_builder.py`
- `addons/smart_core/core/workspace_home_data_provider.py`
- `addons/smart_construction_core/core_extension.py`
- `addons/smart_construction_demo/__manifest__.py`
- `addons/smart_construction_demo/data/scenario/s10_contract_payment/25_workbench_actions.xml`
- `scripts/verify/workbench_extraction_hit_rate_report.py`
- `docs/product/workbench_purpose_and_model_v1.md`
- `docs/product/workbench_purpose_and_model_v1.en.md`
- `docs/product/workbench_product_acceptance_checklist_v1.md`
- `docs/product/workbench_product_acceptance_checklist_v1.en.md`
- `docs/demo/demo_data_round_2_plan.md`
- `docs/demo/demo_data_round_2_plan.en.md`
- `docs/releases/workbench_visibility_diagnosis_v1.md`
- `docs/releases/workbench_visibility_diagnosis_v1.en.md`

## 3. Contract 结构性变化（重构前后）

### 3.1 协议主次明确

- 新增 `contract_protocol.primary=page_orchestration_v1`。
- `page_orchestration` 明确标记为 `legacy.compatibility`，不再作为主叙事载体。

### 3.2 首页语义从“能力优先”改为“行动优先”

- `today_actions` 由“能力入口映射”升级为：
  - 业务动作优先抽取（任务/审批/风险等）；
  - 数据不足时 capability fallback。
- `risk.actions` 同步采用业务优先，锁定能力作为次级兜底。
- 新增 `project_actions` 作为 PM 可见真实业务源，补齐项目经理真实动作链路。

### 3.3 指标分层

- `metrics`：业务运营指标（行动量、风险量、执行压力等）。
- `platform_metrics`：平台能力计数（ready/locked/preview/scene）。
- 平台诊断信息进入 `diagnostics`，与用户主视图分层。
- 命中率升级为双口径：
  - `business_rate`（业务语义命中）
  - `factual_rate`（真实记录命中）

### 3.4 四区主骨架保持稳定

`hero / today_focus / analysis / quick_entries` 四区结构保留，避免推翻现有页面。

## 4. 产品表达结果

- 工作台副标题改为行动导向：`先处理行动项，再关注风险与总体状态`。
- `hero` 语义降级为补充区（在 provider 侧降权），首屏聚焦 `today_focus`。
- 形成“先行动、再风险、后状态、再入口”的工作流。

## 5. 兼容性说明

- 对旧前端/旧脚本：`page_orchestration` 仍可读取。
- 对新前端：继续以 `page_orchestration_v1` 渲染。
- 未触碰认证、权限、治理、交付主链路。

## 6. 回归验证结果

- `make verify.frontend.build`：PASS
- `make verify.frontend.typecheck.strict`：PASS
- `make verify.project.dashboard.contract`：PASS
- `make verify.phase_next.evidence.bundle`：PASS（在 `ENV=test + .env.prod.sim` 下）
- `make verify.workbench.extraction_hit_rate.report`：PASS

## 7. 可见性事实与修复证据（权限 vs 归属）

基于 `docs/releases/workbench_visibility_diagnosis_v1.md` 的结论：

- 问题主因是“权限 + demo 归属导致 PM 可见真实源不足”，不是前端渲染问题。
- 修复策略遵循边界：不修改 ACL 基线，只补 PM 可见真实源与 demo 数据。

修复后（`artifacts/backend/workbench_extraction_hit_rate_report.md`）：

- `pm`: `today_factual_rate=83.33%`, `risk_factual_rate=100%`
- `finance`: `today_factual_rate=100%`, `risk_factual_rate=100%`
- `owner`: `today_factual_rate=100%`, `risk_factual_rate=100%`

## 8. 已知风险与后续动作

### 风险

- 业务数据源键名在不同租户/环境可能不一致，业务动作抽取命中率需持续观测。

### 下一轮建议

1. 补一份“业务动作抽取命中率”观测报告（按角色与场景）。
2. 将 `diagnostics` 的 HUD 展示标准化，避免调试字段回流到用户主视图。
3. 对 `today_actions` 增加时效因子（逾期/临期）排序权重。
