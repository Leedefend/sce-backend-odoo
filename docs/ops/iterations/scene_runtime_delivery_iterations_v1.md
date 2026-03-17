# Scene Runtime Delivery Iterations v1

## 交付节奏定义

- 模式：独立提交 + 连续迭代
- 目标：每轮可验收、可回滚、可继续叠加

## 当前分解（可直接作为提交单元）

### Commit Unit 1：P0 边界与标准

- 文件族：
  - `docs/architecture/ui_base_vs_scene_ready_contract_v1.md`
  - `docs/architecture/app_shell_vs_page_scene_contract_v1.md`
  - `docs/contracts/ui_base_contract_schema_v1.md`
  - `docs/ops/audits/current_response_contract_gap_audit_v1.md`

### Commit Unit 2：后端链路打通

- 文件族：
  - `addons/smart_core/core/ui_base_contract_adapter.py`
  - `addons/smart_core/core/scene_ready_contract_builder.py`
  - `addons/smart_scene/services/ui_base_contract_adapter.py`
  - `addons/smart_scene/services/__init__.py`

### Commit Unit 3：前端消费收口

- 文件族：
  - `frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts`
  - `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/pages/ContractFormPage.vue`
  - `docs/ops/audits/frontend_direct_base_contract_usage_audit_v1.md`

### Commit Unit 4：行业三件套与样板

- 文件族：
  - `addons/smart_construction_scene/scenes/projects/*.yaml`
  - `addons/smart_construction_scene/policies/construction_scene_policy.py`
  - `addons/smart_construction_scene/providers/*.py`
  - `addons/smart_construction_scene/bootstrap/register_scene_providers.py`
  - `docs/architecture/industry_scene_profile_policy_provider_spec_v1.md`

### Commit Unit 5：验证闭环与矩阵

- 文件族：
  - `addons/smart_core/tests/test_scene_runtime_contract_chain.py`
  - `addons/smart_core/tests/__init__.py`
  - `docs/ops/verify/*.md`
  - `docs/architecture/scene_coverage_matrix_v1.md`
  - `docs/contracts/projects_scene_ready_samples_v1.md`

## 每轮最小验收门槛

- 后端：`py_compile` 通过（改动文件）
- 前端：改动文件 `eslint` 通过
- 文档：新增文档路径完整且可追溯到改动模块

