# Governance Incident Release Note v1

## 1. 本轮变更
- 目标：修复 `project_code` 在项目创建页泄漏问题，确保“系统生成字段不进入创建态”由治理层保障。
- 完成：
  - 修复 `render_profile` 判定：`new/0/null/none/false` 统一归入 create。
  - 补强项目表单识别：`project.project` 只要包含 `form` 视图（含 `tree,form`）即触发表单治理。
  - 固化字段可见性：`project_code/code` 在 create 不可见，仅 `edit/readonly` 可见。
  - 同步技能与文档：将规则写入治理 summary 与 `project-governance-codex` / `contract-audit` skill。
- 未完成：全模型范围“系统生成字段创建态可见性”专项扫描。

## 2. 问题分级与归因
- 现象：创建项目页出现“项目编号”字段，且前端隐藏后会反复出现。
- 根因层级：治理层 / 契约层。
- 根因说明：
  - `render_profile` 对 `id='new'` 误判为编辑态；
  - 项目表单治理对 `view_type` 识别过窄，复合视图场景可能漏管。
- 是否存在前端兜底：是（临时），已按要求移除并回归后端契约治理。

## 3. 影响范围
- 模块：`addons/smart_core`、`addons/smart_construction_core`、`.codex/skills/*`。
- 启动链（login → system.init → ui.contract）：否。
- contract/schema：是。
- default_route/scene：否。
- public intent：否。

## 4. 风险
- P0：浏览器缓存可能短时持有旧前端资源或旧契约结果。
- P1：其他模型可能存在同类 create/edit 语义判定缺陷。
- P2：若团队继续用前端兜底，将再次绕过治理层。
- 缓解策略：
  - 强制以 create 契约快照验收；
  - 将规则固化到 skill；
  - 后续批次执行“系统生成字段”横向扫描。

## 5. 验证
- 执行命令：
  - `make mod.upgrade CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_core,smart_construction_core MODULE=smart_core DB_NAME=sc_prod_sim ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim`
  - `make deploy.prod.sim.oneclick ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
  - `make contract.export CONTRACT_CASE=project_ui_contract_model_create_admin_postfix CONTRACT_USER=admin CONTRACT_OP=intent.invoke CONTRACT_INTENT='ui.contract' CONTRACT_INTENT_PARAMS='{"op":"model","model":"project.project","view_type":"form"}' CONTRACT_OUTDIR=artifacts/contract/rootfix DB_NAME=sc_prod_sim ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim`
  - `make contract.export CONTRACT_CASE=project_ui_contract_model_tree_form_admin_postfix CONTRACT_USER=admin CONTRACT_OP=intent.invoke CONTRACT_INTENT='ui.contract' CONTRACT_INTENT_PARAMS='{"op":"model","model":"project.project","view_type":"tree,form"}' CONTRACT_OUTDIR=artifacts/contract/rootfix DB_NAME=sc_prod_sim ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim`
- 结果：PASS。
- 关键结论：
  - `render_profile`：`create`。
  - `visible_fields`：不包含 `project_code/code`。
  - `field_policies`：`project_code/code.visible_profiles=['edit','readonly']`。

## 6. 证据路径
- contract snapshot：
  - `artifacts/contract/rootfix/project_ui_contract_model_create_admin_postfix.json`
  - `artifacts/contract/rootfix/project_ui_contract_model_tree_form_admin_postfix.json`
- logs：`/tmp/contract_export.log`、`/tmp/contract_export2.log`
- guard/report：`docs/ops/iterations/codex_skills_governance_upgrade_summary_v1.md`
- trace_id（如有）：由线上接口返回，未在该离线导出快照中固定。

## 7. 回滚方案
- 回滚 commit/tag：回退 `smart_core` 契约治理补丁提交。
- 回滚步骤：
  - 回退代码到上一个稳定提交；
  - `make mod.upgrade ... smart_core`；
  - `make restart ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`。
- 回滚后验证：重新导出 create 契约并检查 `render_profile` 与 `visible_fields`。

## 8. 下一批次
- 目标（唯一）：完成“系统生成字段创建态不可见”全模型治理扫描。
- 前置语义拍板：明确字段分类基线（system-generated / user-input / technical）。
- 阻塞项：跨模块字段语义清单尚未统一。

## 9. 复盘结论（一句话）
- 本次问题属于：治理规则边界不完整（已补齐并固化到技能与验收模板）。

