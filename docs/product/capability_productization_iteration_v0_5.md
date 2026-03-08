# Phase-Capability-Productization-v0.5 交付说明

## 本轮目标

- 建立统一导航入口注册表（scene + capability）
- 增加导航注册表一致性守卫

## 新增产物

- `docs/product/navigation_entry_registry_v1.json`
  - `entry_source=scene|capability`
  - `registry_key` 全局唯一
  - 引用 `scene_key/capability_key` 均可追溯

## 新增验证

- `verify.portal.navigation_entry_registry_guard`
  - 校验 registry key 唯一
  - 校验 scene/capability 引用有效
  - 校验 source 双维入口均存在

## 当前入口规模

- scene entries: 31
- capability entries: 42
- navigation entries: 73

## 结果

- 入口治理从“分散注册”升级为“统一导航注册”
- 前端后续可直接消费单一导航注册表做渲染与灰度控制
