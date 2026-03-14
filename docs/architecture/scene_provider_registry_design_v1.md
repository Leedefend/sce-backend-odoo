# Scene Provider Registry 设计说明 v1

## 1. 目标
- 将场景内容提供机制从“路径猜测”升级为“平台注册驱动”。
- 平台层只负责机制与标准；行业层显式注册内容 provider。
- 运行时按 `scene_key` 从 registry 获取 provider，前端继续只消费编排结果契约。

## 2. 分层边界
- 平台层（`smart_scene`）
  - `SceneContentProvider` 标准对象
  - `SceneProviderRegistry` 注册/查询/优先级机制
  - 统一加载流程与诊断输出
- 行业层（`smart_construction_scene`）
  - 通过注册模块声明 `workspace.home` / `project.dashboard` / `scene.registry` provider
  - 提供 scene content 实现文件（profiles）
- 兼容层（`smart_core`）
  - 仅保留 legacy fallback provider（`workspace_home_data_provider.py`）

## 3. 核心对象
- 文件：`addons/smart_scene/core/scene_provider_registry.py`
- `SceneContentProvider`
  - `scene_key`
  - `provider_key`
  - `module_name`
  - `provider_path`
  - `priority`
  - `contract_version`
  - `source`
- `SceneProviderRegistry`
  - `register(provider)`
  - `register_spec(**kwargs)`
  - `get_provider(scene_key)`
  - `list_providers(scene_key=None)`

## 4. 注册流程
1. 平台先装载 fallback providers（兼容保障）。
2. 平台扫描行业注册模块：
   - `addons/smart_construction_scene/bootstrap/register_scene_providers.py`
3. 行业注册模块调用 `registry.register_spec(...)` 显式声明 provider。
4. registry 按优先级降序选择可用 provider。

## 5. 运行时解析
- 入口保持兼容：`addons/smart_scene/core/provider_locator.py`
- 逻辑已改为：
  - registry 优先：`resolve_scene_provider_path(scene_key, base_dir)`
  - 路径 fallback 兜底（仅迁移期）

## 6. 现阶段已覆盖 scene
- `workspace.home`
- `project.dashboard`
- `scene.registry`

## 7. 验证与治理
- 新增守卫：`scripts/verify/scene_provider_registry_guard.py`
- Make target：`make verify.scene.provider.registry.guard`
- 纳入平台核验链：`verify.platform.kernel.ready`

## 8. 后续演进
- P1：provider 诊断字段进入 `scene_contract_v1.diagnostics.provider_trace`
- P1：扩展 scene provider 覆盖矩阵与重复注册冲突报告
- P2：`provider_locator` 已降级为 deprecated shim（仅 registry 转发）；后续可评估完全移除 shim API
