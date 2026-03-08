# Phase-Capability-Productization-v0.2 交付说明

## 本轮目标

- 收敛产品场景（过滤技术派生 scene）
- 提升 `capability -> scene` 产品映射闭环
- 将角色矩阵与模板输出为机器可读 JSON
- 增加平台化验证 guard，防止回退

## 核心改动

1. 生成器增强
- `scripts/product/build_capability_productization_v1.py`
  - 新增产品场景过滤：`scene_catalog_product_v1.json`
  - 新增场景回填映射策略（按域/分组 fallback）
  - 新增映射质量指标：`quality_summary`
  - 新增 JSON 策略输出：
    - `docs/product/role_scene_matrix_v1.json`
    - `docs/product/templates/construction_enterprise_template_v1.json`
    - `docs/product/templates/owner_management_template_draft_v1.json`

2. 新增验证 guard
- `scripts/verify/portal_scene_product_filter_guard.py`
- `scripts/verify/portal_product_scene_mapping_guard.py`
- `scripts/verify/portal_role_home_scene_guard.py`
- Makefile 新增目标：
  - `verify.portal.scene_product_filter_guard`
  - `verify.portal.product_scene_mapping_guard`
  - `verify.portal.role_home_scene_guard`

3. 产物更新
- `docs/product/scene_catalog_v2.{md,json}`
- `docs/product/capability_scene_mapping_v1.{md,json}`
- `docs/product/capability_gap_backlog_v1.md`

## 指标变化（v0.2）

来自 `docs/product/capability_scene_mapping_v1.json#quality_summary`：

- `scene_total`: 144
- `scene_mapped`: 115
- `mapping_rate_all`: 0.7986
- `product_scene_total`: 31
- `product_scene_mapped`: 31
- `mapping_rate_product`: 1.0
- `product_void_scenes`: 0
- `orphan_capability_count`: 0

## 验证结果

- `make verify.portal.scene_product_filter_guard` PASS
- `make verify.portal.product_scene_mapping_guard` PASS
- `make verify.portal.role_home_scene_guard` PASS
- `make verify.frontend.quick.gate` PASS
- `make verify.portal.dashboard` PASS
