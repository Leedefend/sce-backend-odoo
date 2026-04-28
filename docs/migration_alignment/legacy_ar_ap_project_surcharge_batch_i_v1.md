# 应收应付报表（项目）附加税 Batch-I

## 1. 批次定位

- Layer Target：业务事实分析层 / Domain Projection
- Module：`addons/smart_construction_core`、`scripts/migration`
- Reason：旧库“应收应付报表（项目）”剩余字段包含销项附加税、进项附加税、抵扣附加税，必须按旧过程事实来源补齐，避免报表字段缺口。

## 2. 旧库口径

旧过程 `UP_USP_SELECT_YSYFHZB_XM` 字段：

- `KPDJFJS`：`C_JXXP_XXKPDJ` + `C_JXXP_XXKPDJ_CB.D_SCBSJS_FJS`
- `JXSBFJS`：`C_JXXP_ZYFPJJD` + `C_JXXP_ZYFPJJD_CB.D_SCBSJS_FJS`
- `DKDJFJS`：`C_JXXP_DKDJ_New` + `C_JXXP_DKDJ_CB.D_SCBSJS_DKFJS`

有效过滤：

- `ISNULL(DJZT, '0') = '2'`
- `ISNULL(DEL, 0) = 0`

旧库有效金额：

- 销项附加税：`20,595,859.4964`
- 进项附加税：`13,328,329.2112`
- 抵扣附加税：`1,759,613.9436`

## 3. 新系统承载

新增 `sc.legacy.invoice.surcharge.fact`，专门承载销项/进项发票附加税事实：

- `direction=output` 来源 `C_JXXP_XXKPDJ_CB`
- `direction=input` 来源 `C_JXXP_ZYFPJJD_CB`
- 项目按旧项目 ID 匹配 `project.project.legacy_project_id`
- 往来单位优先按历史往来单位 ID 匹配，失败时按名称匹配

抵扣附加税复用 Batch-F 已有 `sc.legacy.tax.deduction.fact.deduction_surcharge_amount`。

## 4. 报表投影

`sc.ar.ap.project.summary` 新增：

- 销项附加税
- 进项附加税
- 抵扣附加税

本批同时将抵扣税额投影过滤补齐为旧过程一致的 `DJZT=2 && DEL=0`。因此应收应付项目报表中的抵扣税额从 Batch-F 的 DEL=0 口径修正为旧过程有效口径：

- 抵扣税额：`56,009,185.14`
- 抵扣附加税：`1,759,613.9436`

为避免历史项目未匹配时金额被 SQL `NULL = NULL` 吞掉，报表投影的项目关联改为 `IS NOT DISTINCT FROM`，未匹配项目会作为“未匹配项目”异常行显示。

## 5. 重建链路

新增入口：

```bash
make fresh_db.legacy_invoice_surcharge.replay.adapter
make fresh_db.legacy_invoice_surcharge.replay.write
```

一键重建链路新增 step：

- `legacy_invoice_surcharge_adapter`
- `legacy_invoice_surcharge_replay`

支持断点执行：

```bash
DB_NAME=<target_db> HISTORY_CONTINUITY_START_AT=legacy_invoice_surcharge_adapter \
  HISTORY_CONTINUITY_STOP_AFTER=legacy_invoice_surcharge_replay \
  make history.continuity.replay
```

## 6. 模拟生产验证

- adapter：PASS，抽取 27053 行
  - 销项 4540 行，`20,595,859.4964`
  - 进项 22513 行，`13,328,329.2112`
- write：PASS，写入 27053 行
  - 缺项目 124 行
  - 缺往来单位 521 行
- 报表投影：
  - 销项附加税：`20,595,859.4964`
  - 进项附加税：`13,328,329.2112`
  - 抵扣附加税：`1,759,613.9436`
  - 抵扣税额：`56,009,185.14`

## 7. 风险与回滚

- P1：124 行历史附加税无法匹配新项目，当前以“未匹配项目”异常行保留，后续应补项目锚点或确认旧项目不迁移原因。
- P2：521 行未匹配新 `res.partner`，当前仍按历史往来单位名称进入报表。
- 回滚：删除 `sc.legacy.invoice.surcharge.fact` 中 `import_batch=legacy_invoice_surcharge_v1` 行，回退本批提交并升级 `smart_construction_core`。

## 8. 下一批次

继续检查旧报表 27 字段是否已经全部具备投影或明确承载边界；如字段已闭环，下一轮应转向报表交叉核对和用户可读口径说明。
