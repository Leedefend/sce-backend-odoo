# 应收应付报表（项目）自筹字段 Batch-G

## 批次边界

- Layer Target：Domain Projection
- Module：`addons/smart_construction_core`
- Reason：旧库“应收应付报表（项目）”包含自筹收入、退回、未退字段；新系统原有收款事实未完整承载该专用口径，需要先补旧库事实载体，再进入项目汇总报表。

## 本批目标

- 新增 `sc.legacy.self.funding.fact` 历史自筹事实模型。
- 从旧库自筹垫付收款和自筹退回明细导入有效事实到模拟生产库。
- 在 `sc.ar.ap.project.summary` 中新增：
  - 自筹收入金额
  - 自筹退回金额
  - 自筹未退金额

## 事实判断

旧过程 `UP_USP_SELECT_YSYFHZB_XM` 自筹字段来源：

- `ZCSRJE`：`C_JFHKLR.f_JE`
- `ZCTHJE`：`C_JFHKLR_TH_ZCDF_CB.BCTK`
- `ZCWTJE`：自筹收入 - 自筹退回

旧库完整口径：

- 自筹收入：2153 行，223309983.61
- 自筹退回：1575 行，145077200.09
- 合计输入：3728 行

新系统现状：

- `sc.legacy.receipt.income.fact` 只承载少量 `C_JFHKLR` 行，不能覆盖旧过程自筹垫付口径。
- 自筹退回来自独立退回主子表，原有收款事实没有对应载体。
- 因此本批新增专用历史事实模型，避免将专用字段混入一般收款。

## 口径说明

自筹收入过滤条件：

- `C_JFHKLR.DJZT = '2'`
- `ISNULL(C_JFHKLR.DEL, 0) = 0`
- `LX = '自筹垫付'`
- `type = '其他类型收款'`

自筹退回过滤条件：

- `C_JFHKLR_TH_ZCDF.DJZT = '2'`
- `ISNULL(C_JFHKLR_TH_ZCDF.DEL, 0) = 0`
- 子表金额取 `C_JFHKLR_TH_ZCDF_CB.BCTK`

报表计算：

- 自筹收入金额 = 同项目同往来单位有效自筹收入合计
- 自筹退回金额 = 同项目同往来单位有效自筹退回合计
- 自筹未退金额 = 自筹收入金额 - 自筹退回金额

## 交付结果

- 模型：`sc.legacy.self.funding.fact`
- 内部菜单：历史财务事实（内部）/ 历史自筹收退
- 脚本：
  - `scripts/migration/fresh_db_legacy_self_funding_replay_adapter.py`
  - `scripts/migration/fresh_db_legacy_self_funding_replay_write.py`
- 报表：`sc.ar.ap.project.summary` 新增自筹收入金额、自筹退回金额、自筹未退金额

## 验证结果

- `python3 -m py_compile ...`：PASS
- XML parse：PASS
- `CSV ir.model.access duplicate id check`：PASS，340 行，无重复 id
- `ENV=test ENV_FILE=.env.prod.sim CODEX_MODE=gate CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_prod_sim make mod.upgrade`：PASS
- `python3 scripts/migration/fresh_db_legacy_self_funding_replay_adapter.py`：PASS，payload 3728 行
- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim MIGRATION_REPLAY_DB_ALLOWLIST=sc_prod_sim MIGRATION_ARTIFACT_ROOT=/mnt/artifacts/migration make odoo.shell.exec < scripts/migration/fresh_db_legacy_self_funding_replay_write.py`：PASS，写入 3673 行，跳过缺项目 55 行
- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec`：
  - `fact_rows=3673`
  - `fact_missing_partner_rows=14`
  - `fact_self_funding_amount=219525590.83`
  - `fact_refund_amount=143229174.39`
  - `fact_unreturned_amount=76296416.44`
  - `summary_rows=11187`
  - `summary_self_funding_rows=595`
  - `summary_self_funding_income_amount=219525590.83`
  - `summary_self_funding_refund_amount=143229174.39`
  - `summary_self_funding_unreturned_amount=76296416.44`
- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make verify.restricted`：SKIP，当前 Makefile 无该 target

## 重建链路

- `history.production.fresh_init` 调用 `scripts/migration/history_continuity_oneclick.sh`。
- 本批新增事实已接入完整 replay 链路：
  - `legacy_self_funding_adapter`
  - `legacy_self_funding_replay`
- 支持局部续跑：
  - `HISTORY_CONTINUITY_START_AT=legacy_self_funding_adapter`
  - `HISTORY_CONTINUITY_STOP_AFTER=legacy_self_funding_replay`
- 支持 Makefile 单独执行：
  - `make fresh_db.legacy_self_funding.replay.adapter`
  - `make fresh_db.legacy_self_funding.replay.write`

## 风险

- 55 条旧库自筹明细存在旧项目 ID，但当前模拟生产项目主数据未匹配，未进入项目汇总报表；涉及自筹收入 3784392.78、退回 1848025.70、净未退 1936367.08。
- 14 条已落库事实未匹配新系统 `res.partner`，当前按历史往来单位名称参与报表汇总。
- 实际可用余额仍未纳入，应继续单独拆解旧过程资金余额口径，避免与自筹未退混淆。

## 回滚

- 回退本批次提交并升级 `smart_construction_core`，即可移除模型、视图、菜单和报表字段。
- 如需回滚模拟生产数据，可按 `import_batch=legacy_self_funding_v1` 删除 `sc.legacy.self.funding.fact` 行后升级模块。

## 下一批次

- 继续拆解旧库“实际可用余额”字段，判断是否应作为项目资金汇总能力承载，还是只作为应收应付项目报表专属指标。
