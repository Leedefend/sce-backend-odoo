# Batch-History-Capability-Promotion-C Tax Deduction

## 1. 本轮变更

- 目标：把历史抵扣税额事实纳入正式抵扣登记能力的业务可用初始化链。
- 完成：
  - `history.business.usable.init` 新增 `tax_deduction_registration_projection` 步骤。
  - 新增 Make target `fresh_db.tax_deduction_registration.projection.write`，可单独执行抵扣登记正式投影。
  - 修复 `fresh_db_tax_deduction_registration_projection_write.py` 在 Odoo shell 中无 `__file__` 时误写 `/artifacts` 的产物路径解析问题。
  - `formal_projection_refresh_probe` 增加 `legacy_tax_deduction -> sc.tax_deduction_registration` 缺口检查。
  - `history_business_usable_probe` 增加抵扣登记 counts、sample 与 promotion gap。
- 未完成：未扩展财税分析聚合；留给下一批 treasury/tax analysis capability。

## 2. 影响范围

- 模块：`scripts/migration`、`scripts/verify`、`Makefile`、`docs/ops/iterations`
- 启动链：否
- contract：否
- 路由：否
- Odoo 模块升级：不需要新增模型/字段；如目标库尚未升级到包含 `sc.tax.deduction.registration` 的版本，需先升级 `smart_construction_core`。

## 3. 风险

- P0：无。
- P1：目标库若存在历史抵扣事实但尚未运行正式投影，新增 probe 会正确阻断 `history.business.usable.probe`。
- P2：抵扣登记投影仍依赖历史事实中的项目锚点；无项目锚点的历史事实继续保留在内部事实层。

## 4. 验证

- 命令：
  - `bash -n scripts/migration/history_business_usable_init.sh`
  - `python3 -m py_compile scripts/migration/history_business_usable_probe.py scripts/verify/formal_projection_refresh_probe.py scripts/migration/fresh_db_tax_deduction_registration_projection_write.py`
  - `make -n fresh_db.tax_deduction_registration.projection.write DB_NAME=sc_demo`
  - `git diff --check`
  - `DB_NAME=sc_demo make fresh_db.tax_deduction_registration.projection.write`
  - `DB_NAME=sc_demo make verify.prod.sim.formal.projections`
  - `DB_NAME=sc_demo make history.business.usable.probe`
  - `make verify.restricted`
- 结果：PASS。
  - 实际投影：`candidate_count=4915`，`created=4915`，`visible_rows=4915`，`status=PASS`。
  - formal projection：`decision=formal_projection_refresh_ready`，`gap_count=0`。
  - business usable：`decision=history_business_usable_ready`，`gap_count=0`。

## 5. 产物

- snapshot：N/A，本批不改 contract/schema。
- logs：
  - `artifacts/backend/delivery_mainline_run_summary.json`
  - `artifacts/backend/delivery_mainline_run_summary.md`
  - `artifacts/backend/backend_contract_closure_mainline_summary.json`
  - `/mnt/artifacts/migration/fresh_db_tax_deduction_registration_projection_write_result_v1.json`
  - `/mnt/artifacts/migration/formal_projection_refresh_probe_result_v1.json`
  - `/mnt/artifacts/migration/history_business_usable_probe_result_v1.json`
- docs：`docs/ops/iterations/history_capability_promotion_c_tax_deduction_batch_20260513.md`

## 6. 回滚

- 方法：回退本批修改后，`history.business.usable.init` 不再自动运行抵扣登记投影，两个 probe 不再检查该正式能力缺口。
- 数据回滚：如已在目标库运行投影，可按 `legacy_source_model='sc.legacy.tax.deduction.fact'` 与 `source_origin='legacy'` 审计删除或停用 `sc.tax.deduction.registration` 投影行。

## 7. 下一批次

- 目标：继续增强正式财税/资金分析能力，优先把抵扣、发票、资金台账聚合到可解释的 treasury/tax analysis projection。
- 前置条件：业务确认分析页的分组维度和金额口径，不以 raw `sc.legacy.*` 页面作为用户主入口。
