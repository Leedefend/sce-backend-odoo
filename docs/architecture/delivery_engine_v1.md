# Delivery Engine v1

## Goal

Promote released navigation from a standalone sidebar contract into a unified runtime delivery surface:

- product policy
- menu delivery
- scene delivery
- capability delivery

## Layer Target

- Platform Layer: `addons/smart_core/delivery`
- Scene Layer: consume published scene facts only, do not re-implement scene orchestration
- Verify Layer: release guards for menu / scene / policy integrity

## Runtime Contract

`system.init` now emits:

- `delivery_engine_v1.nav`
- `delivery_engine_v1.scenes`
- `delivery_engine_v1.capabilities`
- `delivery_engine_v1.product_policy`

`release_navigation_v1` remains as a compatibility projection of the same runtime.

## Ownership

- runtime engine:
  - `addons/smart_core/delivery/delivery_engine.py`
- policy loader:
  - `addons/smart_core/delivery/product_policy_service.py`
  - `addons/smart_core/models/product_policy.py`
- runtime integration:
  - `addons/smart_core/handlers/system_init.py`
  - `addons/smart_core/core/system_init_payload_builder.py`

## Scope

Current default product policy: `construction.standard`

Released entries:

- FR-1 项目立项
- FR-2 项目推进
- FR-3 成本记录
- FR-4 付款记录
- FR-5 结算结果
- 我的工作

## Non-Goals

- no replacement of raw Odoo menu storage
- no admin UI for product policy management in this batch
- no rewrite of existing FR-1 to FR-5 scene/business semantics

## Verification

- `make verify.product.delivery_menu_integrity_guard`
- `make verify.product.delivery_scene_integrity_guard`
- `make verify.product.delivery_policy_guard`
- `make verify.release.delivery_engine.v1`

