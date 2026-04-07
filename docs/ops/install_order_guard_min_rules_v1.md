# Install-Order Guard (Minimum Rules) v1

适用范围：`addons/smart_construction_core/data/sc_capability_group_seed.xml`

## 规则
- capability/group 的早期 seed 允许物化 core-owned external-id。
- 早期 seed 不允许通过 `required_group_ids` 引用后加载的 security XMLID（如 `smart_construction_core.group_sc_cap_*`）。
- security 组绑定应由后续 security 数据加载阶段或场景编排阶段完成，不在 install-order 早期 seed 强绑定。

## 守卫脚本
- `python3 scripts/verify/native_business_fact_install_order_guard_verify.py`

通过标准：
- 返回 `PASS`，且无 early `required_group_ids -> smart_construction_core.group_sc_cap_*` 依赖。
