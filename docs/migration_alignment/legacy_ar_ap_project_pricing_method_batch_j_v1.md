# 应收应付报表（项目）计价方式 Batch-J

## 1. 批次定位

- Layer Target：业务事实分析层 / Domain Projection
- Module：`addons/smart_construction_core`、`scripts/migration`
- Reason：旧库“应收应付报表（项目）”仍有 `JJFS_YF` 计价方式字段未承载；该字段来自供应商合同事实，不是数值指标，需要按旧过程保留项目、往来单位维度的合同计价方式。

## 2. 旧库口径

旧过程 `UP_USP_SELECT_YSYFHZB_XM` 中 `JJFS_YF` 为供应商合同计价方式汇总，来源为 `T_GYSHT_INFO.JJFSTEXT`。

本批按有效供应商合同口径抽取：

- `ISNULL(DJZT, '0') = '2'`
- `ISNULL(DEL, 0) = 0`

旧库抽取结果：

- 有效供应商合同：`5345` 条
- 有计价方式合同：`4677` 条
- 空计价方式合同：`668` 条
- 非空计价方式种类：`17` 个

## 3. 新系统承载

新增 `sc.legacy.supplier.contract.pricing.fact`，专门承载历史供应商合同计价方式事实：

- `legacy_contract_id`：旧合同 ID，唯一约束
- `project_legacy_id/project_id/project_name`：旧项目锚点与新项目映射
- `partner_legacy_id/partner_id/partner_name`：旧供应商锚点与新往来单位映射
- `pricing_method_legacy_id/pricing_method_text`：旧计价方式 ID 与显示名
- `amount_total`：合同金额，仅作为上下文留存，本批不进入金额指标

映射策略：

- 项目按 `project.project.legacy_project_id` 匹配
- 往来单位优先按 `res.partner.legacy_partner_id` 匹配，失败时按名称匹配
- 无法匹配的项目或往来单位保留历史名称，避免事实丢失

## 4. 报表投影

`sc.ar.ap.project.summary` 新增字段：

- `payable_pricing_method_text`，显示名 `计价方式`

投影规则：

- 仅使用 `active=True`
- 仅使用 `document_state='2'`
- 仅使用 `deleted_flag in ('0', '')`
- 空计价方式不进入聚合
- 同一项目、同一往来单位下多个计价方式按去重后的显示名拼接

项目关联使用 `IS NOT DISTINCT FROM`，确保旧项目未匹配时仍能作为异常事实行保留。

## 5. 重建链路

新增入口：

```bash
make fresh_db.legacy_supplier_contract_pricing.replay.adapter
make fresh_db.legacy_supplier_contract_pricing.replay.write
```

一键重建链路新增 step：

- `legacy_supplier_contract_pricing_adapter`
- `legacy_supplier_contract_pricing_replay`

支持断点执行：

```bash
DB_NAME=<target_db> HISTORY_CONTINUITY_START_AT=legacy_supplier_contract_pricing_adapter \
  HISTORY_CONTINUITY_STOP_AFTER=legacy_supplier_contract_pricing_replay \
  make history.continuity.replay
```

## 6. 模拟生产验证

- adapter：PASS
  - 抽取合同 `5345` 条
  - 非空计价方式合同 `4677` 条
  - 非空计价方式 `17` 个
- write：PASS
  - 首次写入 `5345` 条
  - 缺项目 `11` 条
  - 缺往来单位 `32` 条
- 断点重放：PASS
  - 更新 `5345` 条
  - 新增 `0` 条
  - 缺项目 `11` 条
  - 缺往来单位 `32` 条
- 报表投影：
  - 汇总行数 `11640`
  - 有计价方式汇总行 `3412`

## 7. 风险与回滚

- P1：11 条旧供应商合同存在项目未匹配，当前以历史项目名称保留事实，后续应补项目锚点或确认旧项目不迁移原因。
- P2：32 条旧供应商合同未匹配新 `res.partner`，当前按历史供应商名称进入报表。
- P2：计价方式是文本事实，不参与透视数值汇总；后续如需按计价方式分组统计，应单独定义报表维度。
- 回滚：删除 `sc.legacy.supplier.contract.pricing.fact` 中 `import_batch=legacy_supplier_contract_pricing_v1` 行，回退本批提交并升级 `smart_construction_core`。

## 8. 下一批次

旧报表 27 字段已进入最后收口阶段。下一轮应对“字段全口径可用矩阵”做一次完整审计，确认每个旧字段在新系统中是数值指标、文本维度、异常事实还是明确不迁移。
