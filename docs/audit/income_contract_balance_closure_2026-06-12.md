# 收入合同收款开票余额闭环口径

日期：2026-06-12

## 业务边界

- 收入合同 `construction.contract(type=out)` 是收款申请、收款登记、销项开票的业务锚点。
- 收款申请 `payment.request(type=receive)` 表达发起办理金额。
- 收款登记 `sc.receipt.income` 表达财务确认后的真实收款事实，进入资金台账。
- 销项发票登记 `sc.invoice.registration(direction=output)` 表达正式开票事实。
- 合同执行汇总只统计已生效业务事实，不统计草稿、驳回、取消等未生效办理单。

## 办理规则

- 新系统收款登记必须关联收款申请、合同、项目、往来单位和收款账户。
- 新系统收款登记金额不能超过关联收款申请金额。
- 新系统销项开票登记必须满足项目、合同、往来单位一致。
- 新系统销项开票登记金额不能超过收入合同剩余开票余额。
- 红冲销项票为负数调整，不占用正向开票余额。
- 历史迁移事实保持用户旧系统口径，不 retroactive 改写；新办理从当前门禁开始收口。

## 台账口径

- 合同已收款金额只统计 `sc.receipt.income` 的 `received`、`legacy_confirmed` 状态。
- 合同已开票金额只统计 `sc.invoice.registration` 的 `registered`、`legacy_confirmed` 状态。
- 草稿态越界单不进入合同执行汇总，避免未完成办理污染合同余额。

## 验收证据

- 收入合同金额 1000，收款申请 800，收款登记 800 后合同已收款为 800。
- 同一收款申请再登记 801 会被阻断。
- 销项开票 872 登记后合同已开票为 872。
- 同一合同再开票 200 会被阻断，因为超过合同剩余开票余额。
- 收款登记完成后生成 `sc.treasury.ledger`，资金事实进入资金台账。

## 本轮验收命令

- `DB_NAME=sc_demo scripts/ops/validate_income_contract_receipt_invoice_closure.sh`
- `python3 -m py_compile addons/smart_construction_core/models/core/receipt_income.py addons/smart_construction_core/models/core/invoice_registration.py addons/smart_construction_core/models/support/contract_center.py scripts/verify/income_contract_receipt_invoice_closure_audit.py`
- `git diff --check`
