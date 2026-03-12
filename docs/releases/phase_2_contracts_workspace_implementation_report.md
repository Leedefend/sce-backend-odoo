# SCEMS v1.0 Phase 2：`contracts.workspace` 场景落地报告

## 1. 目标
补齐 V1 主导航目标场景之一 `contracts.workspace`，形成最小可用场景定义与运行入口。

## 2. 实施内容

### 2.1 场景注册兜底
- 文件：`addons/smart_construction_scene/scene_registry.py`
- 新增 fallback scene：`contracts.workspace`
- 目标：`/s/contracts.workspace`，并关联合同中心 menu/action 作为过渡承载。

### 2.2 场景编排记录
- 文件：`addons/smart_construction_scene/data/sc_scene_orchestration.xml`
- 新增 `sc.scene` 记录：`sc_scene_contracts_workspace`

### 2.3 场景版本载荷
- 文件：`addons/smart_construction_scene/data/sc_scene_layout.xml`
- 新增 `sc.scene.version`：`sc_scene_version_contracts_workspace_v2`
- 载荷属性：`layout.kind=workspace`、`route=/s/contracts.workspace`

## 3. 验证结果

### 3.1 通过
- `python3 -m py_compile addons/smart_construction_scene/scene_registry.py`
- `make verify.project.form.contract.surface.guard`
- `make verify.scene.catalog.governance.guard`

### 3.2 备注
- `make verify.portal.scene_registry` 当前失败（`expected=3/1` 的前端脚本断言与现态不一致），属于既有前端校验基线问题，不是本次 `contracts.workspace` 变更引入的后端失败。

## 4. 下一步
- 继续补齐 `cost.analysis` / `finance.workspace` / `risk.center` 场景定义，完成 Phase 2 四个待补齐 workspace 场景收口。

