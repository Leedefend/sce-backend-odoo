# 账户与往来资金办理证据闭环

日期：2026-06-12

## 业务边界

- 账户调拨、项目借公司款、承包人借项目款、项目还公司款、承包人还项目款属于内部往来资金域。
- 内部往来资金不挂经营收付款申请，不进入 `payment.ledger`。
- 一旦形成真实资金流入或流出，必须以来源模型和来源记录进入 `sc.treasury.ledger`，且 `payment_request_id` 为空。
- 新发生的借款/还款办理默认币种固定为人民币 `CNY`，不依赖当前公司币种漂移。
- 还款类 `sc.expense.claim` 分类要求附件证据；验证脚本必须模拟真实表单上传到 `attachment_ids`，不能只创建孤立附件。

## 用户数据口径

- 旧系统没有统一“往来款”概念，旧入口名不能直接作为新产品分类验收数。
- 当前借款往来分类以可维护业务分类字典为长期锚点：
  - `finance.loan.project_borrow_company`
  - `finance.loan.contractor_project_borrow`
  - `finance.repayment.project_company`
  - `finance.repayment.contractor_project`
- 旧“承包人借项目款”入口活动数与当前事实分类数存在差异，是旧入口名称和事实分类规则不等价导致；验收时按字典分类、用途文本证据和下游往来事实解释，不按旧菜单名直接收口。

## 本轮加固

- `validate_interfund_account_loan_closure` 的项目还公司款、承包人还项目款样本已补附件上传。
- 该闭环现在覆盖：
  - 账户间调拨完成并生成双向资金台账。
  - 项目借公司款完成并生成项目流入资金台账。
  - 承包人借项目款完成并生成项目流出资金台账。
  - 项目还公司款完成并生成项目流出资金台账。
  - 承包人还项目款完成并生成项目流入资金台账。
  - 以上往来资金台账均不挂 `payment.request`。
  - 借款与还款样本均校验为 `CNY`。

## 验收证据

- `DB_NAME=sc_demo scripts/ops/validate_interfund_account_loan_closure.sh`
- `DB_NAME=sc_demo scripts/ops/validate_finance_interfund_category_handling_policy.sh`
- `DB_NAME=sc_demo scripts/ops/validate_interfund_treasury_ledger_backfill_readiness.sh`
- `DB_NAME=sc_demo make verify.interfund_user_data.full_coverage.audit`
- `DB_NAME=sc_demo make verify.interfund_borrow.classification_gap.audit`

## 后续

- 将借还款分类的文本识别规则继续沉淀到业务分类字典和行业模板配置。
- 对旧入口差异保留可解释样本，等用户验收时确认新分类口径后再作为正式验收基线。
