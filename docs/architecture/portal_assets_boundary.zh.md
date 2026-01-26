# Portal 资产边界

目的
- Portal 资产与 Odoo 后台 UI 彻底隔离。
- 避免依赖 @web/* 模块与后台小部件。

规则
- Portal 资产仅允许存在于 smart_construction_portal，并通过独立 bundle 加载。
- 禁止将 Portal 资产加入 web.assets_backend 或 web.assets_frontend。
- Portal 代码禁止引用 @web/* 模块。
- Portal 只消费 Contract + Meta API（N3 为只读）。

Bundle
- Bundle 名称：smart_construction_portal.assets_portal
- 页面入口：/portal/lifecycle

Feature flag
- sc.portal.lifecycle.enabled 控制路由可用性与菜单显隐。
