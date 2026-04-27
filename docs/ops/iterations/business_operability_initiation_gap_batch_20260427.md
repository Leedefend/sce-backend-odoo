# Business Operability Initiation Gap Batch - 2026-04-27

## Scope

- Layer Target: `Domain/business operability`
- Module: `smart_construction_core`
- Reason: real users found that purchase/general contract pages had no create handling capability. The business rule is: internal users may initiate business documents; approval remains role restricted.

## Findings

The first audit confirmed that menu visibility alone was not enough. A page can be visible but still not operable when one of these layers is missing:

- model `create/write` ACL
- action/menu groups include only domain specialist groups
- view arch disables `create/edit`
- required technical identity fields have no business-safe default

Specific gaps:

- `采购/一般合同` was still configured as a read-only fact page:
  - tree/form `create=0 edit=0`
  - action context disabled create
  - user/manager ACL was read-only
  - required `legacy_record_id` had no default for new-system records
- `采购单` had no Smart Construction business menu entry under `物资管理`.
- Related business documents still had the same initiation gap for non-specialist internal users: settlement, expense/guarantee, treasury reconciliation, receipt income, payment execution, invoice registration, and financing loan.

## Changes

- Kept `采购/一般合同` as a business handling page and upgraded it to create/edit:
  - removed view/action create suppression
  - opened ACL for business initiators, contract users, and contract managers
  - added `sc.legacy.purchase.contract.fact` sequence and model default for `legacy_record_id`
- Added `采购单` action/menu under `物资管理`, visible to business initiators and purchase roles.
- Opened initiation ACL to `group_sc_cap_business_initiator` for:
  - `purchase.order`, `purchase.order.line`
  - `construction.contract`, `construction.contract.line`
  - `sc.general.contract`
  - `sc.legacy.purchase.contract.fact`
  - `sc.settlement.order`, `sc.settlement.order.line`, `sc.settlement.adjustment`
  - `sc.expense.claim`
  - `sc.treasury.reconciliation`
  - `sc.receipt.income`
  - `sc.payment.execution`
  - `sc.invoice.registration`
  - `sc.financing.loan`
- Added business initiator visibility to the corresponding actions/menus where users must be able to start a document.

## Verification

- `python3 -m py_compile addons/smart_construction_core/models/support/legacy_purchase_contract_fact.py`
- XML parse checks for changed views/security/data files
- `git diff --check`
- `make mod.upgrade MODULE=smart_construction_core`
- Operability matrix on `sc_prod_sim` for sampled real users:
  - users: `wutao`, `denghongying`, `yangdesheng`, `yinjiamei`, `weihuguanliyuan`
  - models checked: 13 business initiation models
  - `OPERABILITY_MISSING_CREATE_COUNT=0`
- Transaction rollback create smoke for `denghongying`:
  - `sc.legacy.purchase.contract.fact`: ok, generated `PC...`
  - `sc.general.contract`: ok, generated `GC...`
  - `purchase.order`: ok, generated `P...`
  - `sc.settlement.order`: ok, generated `STO...`
- `make restart`
- `E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.menu.navigation_snapshot.container`
  - `PASS checked=141 scenes=16 trace=a480bf86854d`

## Result

PASS. Purchase/general contract and related business document initiation have been normalized so internal users can start work continuously, while delete and approval remain restricted by existing manager/domain controls.
