# 应收应付报表（项目）项目级指标提示 Batch-P

## 1. 批次定位

- Layer Target：Domain Contract
- Module：`addons/smart_construction_core.models.projection.ar_ap_project_summary`
- Reason：`实际可用余额` 和 `抵扣比例` 是项目级指标，但报表按项目+往来单位行展示。用户导出或透视时如果按行求和，会误解项目余额和比例口径。

## 2. 调整内容

本批不改变 SQL 数据口径，只补字段契约说明：

- `tax_deduction_rate`
  - 字段名：抵扣比例
  - 说明：按项目抵扣税额合计 / 项目销项税额合计计算
  - 提示：同一项目下多往来单位行会重复展示，不应按行求和
- `actual_available_balance`
  - 字段名：实际可用余额
  - 说明：来自旧库项目资金余额
  - 提示：同一项目下多往来单位行会重复展示，不应按行求和

验证时发现 `load_view` 平台契约没有透出 `fields_get().help`。本批同步补齐
`smart_core.app_config_engine` 的字段 help 透传，避免自定义前端必须用字段名推导业务说明。

## 3. 契约验证

同步增强专用前端 smoke：

```bash
make verify.portal.ar_ap_project_summary_smoke.container
```

新增断言：

- `load_view` 字段元数据包含 `tax_deduction_rate.help`
- `load_view` 字段元数据包含 `actual_available_balance.help`
- 两个说明均包含“项目级指标”和“不应按行求和”

本批验证结果：

- `python3 -m py_compile addons/smart_construction_core/models/projection/ar_ap_project_summary.py addons/smart_core/app_config_engine/models/app_model_config.py addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`：PASS
- `node --check scripts/verify/fe_ar_ap_project_summary_smoke.js`：PASS
- `ENV=test ENV_FILE=.env.prod.sim ... make mod.upgrade MODULE=smart_core,smart_construction_core`：PASS
- `ENV=test ENV_FILE=.env.prod.sim ... make restart`：PASS
- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.portal.ar_ap_project_summary_smoke.container`：PASS
- `make verify.restricted`：SKIP，当前仓库无该 target

验证产物：

```text
artifacts/codex/ar-ap-project-summary/20260428T074636/
```

## 4. 回滚

回退本批提交，升级 `smart_core,smart_construction_core` 并重启模拟生产后端，即可恢复字段说明和契约透传逻辑。
