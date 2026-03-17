# Scene Runtime Commit Playbook v1

## 使用说明

- 目标：按独立提交单元连续交付，不打断节奏。
- 约束：每个单元先本地验收，再提交下一单元。

## Unit A：边界与标准（文档）

### 文件

- `docs/architecture/ui_base_vs_scene_ready_contract_v1.md`
- `docs/architecture/app_shell_vs_page_scene_contract_v1.md`
- `docs/contracts/ui_base_contract_schema_v1.md`
- `docs/ops/audits/current_response_contract_gap_audit_v1.md`

### 验收

```bash
test -f docs/architecture/ui_base_vs_scene_ready_contract_v1.md
test -f docs/architecture/app_shell_vs_page_scene_contract_v1.md
test -f docs/contracts/ui_base_contract_schema_v1.md
test -f docs/ops/audits/current_response_contract_gap_audit_v1.md
```

### 提交

```bash
git add docs/architecture/ui_base_vs_scene_ready_contract_v1.md \
  docs/architecture/app_shell_vs_page_scene_contract_v1.md \
  docs/contracts/ui_base_contract_schema_v1.md \
  docs/ops/audits/current_response_contract_gap_audit_v1.md
git commit -m "docs(scene): freeze base/scene/app-shell boundaries"
```

## Unit B：后端主链（Base -> Scene-ready）

### 文件

- `addons/smart_core/core/ui_base_contract_adapter.py`
- `addons/smart_core/core/scene_ready_contract_builder.py`
- `addons/smart_scene/services/ui_base_contract_adapter.py`
- `addons/smart_scene/services/__init__.py`

### 验收

```bash
python3 -m py_compile \
  addons/smart_core/core/ui_base_contract_adapter.py \
  addons/smart_core/core/scene_ready_contract_builder.py \
  addons/smart_scene/services/ui_base_contract_adapter.py \
  addons/smart_scene/services/__init__.py
```

### 提交

```bash
git add addons/smart_core/core/ui_base_contract_adapter.py \
  addons/smart_core/core/scene_ready_contract_builder.py \
  addons/smart_scene/services/ui_base_contract_adapter.py \
  addons/smart_scene/services/__init__.py
git commit -m "feat(scene): adapt ui base contract into orchestrator input"
```

## Unit C：前端消费收口（list/form）

### 文件

- `frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts`
- `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
- `frontend/apps/web/src/views/ActionView.vue`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `docs/ops/audits/frontend_direct_base_contract_usage_audit_v1.md`

### 验收

```bash
pnpm -C frontend/apps/web exec eslint \
  src/app/resolvers/sceneReadyResolver.ts \
  src/app/resolvers/sceneRegistry.ts \
  src/views/ActionView.vue \
  src/pages/ContractFormPage.vue
```

### 提交

```bash
git add frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts \
  frontend/apps/web/src/app/resolvers/sceneRegistry.ts \
  frontend/apps/web/src/views/ActionView.vue \
  frontend/apps/web/src/pages/ContractFormPage.vue \
  docs/ops/audits/frontend_direct_base_contract_usage_audit_v1.md
git commit -m "feat(frontend): consume scene-ready surfaces for list and intake"
```

## Unit D：行业三件套与样板

### 文件

- `addons/smart_construction_scene/scenes/projects/projects.list.scene.yaml`
- `addons/smart_construction_scene/scenes/projects/projects.intake.scene.yaml`
- `addons/smart_construction_scene/scenes/projects/project.management.scene.yaml`
- `addons/smart_construction_scene/scenes/projects/contracts.workspace.scene.yaml`
- `addons/smart_construction_scene/scenes/projects/finance.workspace.scene.yaml`
- `addons/smart_construction_scene/policies/construction_scene_policy.py`
- `addons/smart_construction_scene/providers/projects_list_provider.py`
- `addons/smart_construction_scene/providers/project_intake_provider.py`
- `addons/smart_construction_scene/bootstrap/register_scene_providers.py`
- `docs/architecture/industry_scene_profile_policy_provider_spec_v1.md`

### 验收

```bash
python3 -m py_compile \
  addons/smart_construction_scene/policies/construction_scene_policy.py \
  addons/smart_construction_scene/providers/projects_list_provider.py \
  addons/smart_construction_scene/providers/project_intake_provider.py \
  addons/smart_construction_scene/bootstrap/register_scene_providers.py
```

### 提交

```bash
git add addons/smart_construction_scene/scenes/projects/projects.list.scene.yaml \
  addons/smart_construction_scene/scenes/projects/projects.intake.scene.yaml \
  addons/smart_construction_scene/scenes/projects/project.management.scene.yaml \
  addons/smart_construction_scene/scenes/projects/contracts.workspace.scene.yaml \
  addons/smart_construction_scene/scenes/projects/finance.workspace.scene.yaml \
  addons/smart_construction_scene/policies/construction_scene_policy.py \
  addons/smart_construction_scene/providers/projects_list_provider.py \
  addons/smart_construction_scene/providers/project_intake_provider.py \
  addons/smart_construction_scene/bootstrap/register_scene_providers.py \
  docs/architecture/industry_scene_profile_policy_provider_spec_v1.md
git commit -m "feat(industry): add profile policy provider baseline for core scenes"
```

## Unit E：验证闭环与矩阵

### 文件

- `addons/smart_core/tests/test_scene_runtime_contract_chain.py`
- `addons/smart_core/tests/__init__.py`
- `docs/ops/verify/scene_runtime_verify_plan_v1.md`
- `docs/ops/verify/verify.scene.runtime.form_projects_intake_template_v1.md`
- `docs/ops/verify/verify.scene.runtime.list_projects_list_template_v1.md`
- `docs/ops/verify/scene_runtime_verify_index_v1.md`
- `docs/architecture/scene_coverage_matrix_v1.md`
- `docs/contracts/projects_scene_ready_samples_v1.md`
- `docs/ops/iterations/scene_runtime_delivery_iterations_v1.md`

### 验收

```bash
python3 -m py_compile addons/smart_core/tests/test_scene_runtime_contract_chain.py
test -f docs/ops/verify/verify.scene.runtime.form_projects_intake_template_v1.md
test -f docs/ops/verify/verify.scene.runtime.list_projects_list_template_v1.md
```

### 提交

```bash
git add addons/smart_core/tests/test_scene_runtime_contract_chain.py \
  addons/smart_core/tests/__init__.py \
  docs/ops/verify/scene_runtime_verify_plan_v1.md \
  docs/ops/verify/verify.scene.runtime.form_projects_intake_template_v1.md \
  docs/ops/verify/verify.scene.runtime.list_projects_list_template_v1.md \
  docs/ops/verify/scene_runtime_verify_index_v1.md \
  docs/architecture/scene_coverage_matrix_v1.md \
  docs/contracts/projects_scene_ready_samples_v1.md \
  docs/ops/iterations/scene_runtime_delivery_iterations_v1.md
git commit -m "test(scene): add runtime chain verification templates and matrix"
```

