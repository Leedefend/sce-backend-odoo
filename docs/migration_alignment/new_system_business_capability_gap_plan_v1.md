# New System Business Capability Gap Plan v1

Date: 2026-04-26

This plan is based on the restored legacy business facts in `sc_prod_sim`.
The target is not only to preserve old facts, but to make every old-system
business activity that users still need operable in the new system.

## Current Evidence

Latest `history_business_usable_probe` on `sc_prod_sim` after P0-A:

- status: `PASS`
- decision: `history_business_usable_ready`
- promotion gaps: `0`
- runtime projects: `765`
- runtime contracts: `6793`
- supplier contracts: `5301`
- payment requests: `28484`
- payment request lines: `31883`
- receipt invoice lines: `4454`
- workflow audit facts: `79702`
- `sc.history.todo`: `79702`
- open history todos: `79702`
- target-linked history todos: `77745`
- historical cash requests projected to treasury ledger: `16047`
- nonpositive historical cash requests retained outside ledger: `153`
- `sc.treasury.ledger`: `16047`
- legacy file index rows: `178931`
- legacy URL attachments: `19537`
- historical invoice registration lines: `25393`
- historical invoice tax facts: `5920`
- historical deduction adjustment lines: `13521`
- historical fund confirmation lines: `13398`
- historical financing loan facts: `318`
- historical fund daily snapshots: `496`
- historical fund daily lines: `7754`
- `mail.activity`: `0`
- `tier.review`: `0`

P0-A projects `sc.legacy.workflow.audit` into `sc.history.todo` as a dedicated
historical workbench. This closes the immediate actionable surface gap without
fabricating `tier.review` approvals or assigning old permissions as new runtime
authority.

P0-B projects positive historical actual outflow and receipt requests into
`sc.treasury.ledger`: `12992` historical outflows and `3055` historical
receipts. The ledger intentionally allows historical rows without a new-system
settlement order because the legacy cash fact is still valid even when the old
record cannot satisfy every new workflow rule.

P0-C exposes legacy attachment custody as URL-type `ir.attachment` records and
adds operational entry points for receipt invoice lines, payment request lines,
and the legacy file index. Binary bytes remain outside Odoo until a separate
file repository copy-and-hash policy is approved.

P1-A exposes historical invoice registration, invoice tax, deduction adjustment,
and fund-confirmation facts as searchable finance workbench surfaces. It does
not create `account.move` records automatically; posting remains a controlled
new-system operation.

P1-B exposes treasury reconciliation evidence as searchable finance surfaces:
`sc.treasury.ledger` keeps actual cash movements, `sc.legacy.fund.daily.*`
keeps old daily account/bank balance facts, and
`sc.legacy.financing.loan.fact` keeps financing/borrowing facts. The
`history_treasury_reconciliation_probe` validates these surfaces together.

## Capability Matrix

| Legacy business area | Current new-system state | Gap | Plan |
| --- | --- | --- | --- |
| Projects, partners, members | Runtime records and anchors exist | Member scope is mostly evidence, not permission workflow | Keep current replay; add project member read/search surfaces and explicit promotion rules only when users need old scope as active permission. |
| Construction contracts | Runtime `construction.contract` exists | Some old terms/attachments are still history-only | Add contract historical evidence smart tabs and attachment drill-through. |
| Supplier contracts | Runtime supplier contracts and summary lines exist | Some blocked/weak partner contract residue remains neutral | Keep weak rows neutral; add partner recovery only for confirmed active counterparties. |
| Purchase/general contracts | Neutral `sc.legacy.purchase.contract.fact` | Not native contract workflow | Add a purchase/general contract module or promotion wizard for active rows with recoverable partner anchors. |
| Payment requests | Runtime `payment.request` exists with states; historical actual outflow is projected to `sc.treasury.ledger` | 153 nonpositive cash-like rows remain fact-only | Keep request/approval/cash ledger separated; improve residual handling only with stronger business anchors. |
| Receipts and income | Receipt requests plus neutral receipt facts exist; historical receipts are projected to `sc.treasury.ledger` | Residual receipts and fund confirmations are not fully native receive/treasury actions | Add receipt workbench and controlled promotion for rows with project/partner/amount anchors. |
| Invoice and tax | Invoice/tax facts and invoice registration workbench are visible | Accounting posting remains explicit, not automatic migration side effect | Keep searchable historical surfaces; promote to accounting moves only through future controlled posting workflow. |
| Settlement/deductions | New settlement order exists; old deduction facts are neutral | Old deduction/settlement adjustments cannot be processed natively | Add settlement adjustment runtime model linked to contracts, receipts, and payments. |
| Fund daily, fund confirmation, financing | Cash ledger, fund confirmation, financing, fund daily snapshot, and fund daily line workbenches are visible | Formal new-entry reconciliation workflow is still future work | Keep historical facts searchable now; add write-side treasury daily/reconciliation workflow only for new business operations. |
| Expense reimbursement/deposit | Facts are preserved | No native reimbursement workflow for old-style expenses | Add expense reimbursement/deposit workflow or explicit archive-only policy per business owner. |
| Material catalog | Search archive exists | Not a usable product/master-data workflow | Add archive search UI plus controlled material-to-product promotion. |
| Attachments | URL/index facts exist; 19,537 URL attachments and 178,931 file index rows are visible | Binary custody is not complete | Keep URL/index custody available now; copy selected binaries only after repository and hash policy are approved. |
| Attendance/personnel/salary | Privacy-restricted facts exist | Not a native HR workflow | Add HR-lite modules only if users still process these in the construction system; otherwise keep restricted archive. |
| Workflow/todo | Audit facts and `sc.history.todo` workbench exist | Remaining weak rows open the source audit instead of a target runtime record | Keep P0 projection idempotent; improve target linking only when stronger anchors are recovered. |

## P0 Must Do Before Claiming Full Replacement

1. Unified historical workbench
   - Show old pending/approved/done workflow facts by user, project, partner,
     document, and source table.
   - Provide entry points from project, contract, payment, receipt, invoice,
     and finance screens.
   - Do not grant write authority from old permissions automatically.

2. Actionable todo projection
   - Convert selected old workflow facts into `mail.activity` or a dedicated
     `sc.history.todo` model.
   - Support "acknowledge/read", "open source fact", "open target record", and
     "mark resolved by migration decision".
   - Keep tier approval semantics separate; do not fabricate approvals.

3. Payment and receipt execution surfaces
   - Separate request, approval, actual outflow/receipt, treasury ledger, and
     settlement linkage.
   - Add promotion rules for facts with strong anchors.
   - Keep residual/weak rows as read-only historical facts.

4. Attachment custody
   - Decide file classes to copy: payment, contract, invoice, receipt, project,
     document center.
   - Copy binaries outside Odoo first, then attach selected files by URL or
     binary with verification.

## P1 Native Runtime Completion

1. Invoice and tax runtime
   - Build invoice registration model from existing special invoice and tax
     facts.
   - Support invoice number, tax amount, deduction, partner, project, contract,
     source attachment, and status.
   - Accounting moves remain opt-in, not automatic migration side effects.

2. Settlement adjustment runtime
   - Promote deduction/settlement adjustment facts into a native adjustment
     model.
   - Link to contract/payment/receipt where anchors exist.
   - Preserve old reason text and source state.

3. Treasury daily/reconciliation runtime
   - Turn fund daily snapshots and lines into operational views.
   - Add account balance, bank balance, system difference, daily income,
     daily expense, and confirmation/reconciliation workflow.

4. Expense reimbursement and deposit workflow
   - Add reimbursement/deposit document models if users still process these.
   - Otherwise expose existing facts through searchable archive menus.

## P2 Controlled Promotion and Search

1. Material archive to product promotion
   - Keep 2.27M material rows out of products by default.
   - Add search, compare, and "promote selected material" action.

2. Purchase/general contract promotion
   - Recover partner anchors for `T_CGHT_INFO` rows only where counterparty is
     confirmed.
   - Promote to native contract only after project, partner, amount, tax, and
     attachment policies pass.

3. Historical user scope review
   - Provide read-only scope evidence.
   - Promote to active access only through explicit role approval.

## P3 Optional / Policy Driven

1. HR-lite support
   - Attendance, personnel movement, and salary are already preserved with
     restricted access.
   - Build native HR workflows only if these processes remain in this product.

2. Platform audit traceability
   - Low-code history, login logs, API logs, click logs, and config history are
     not ordinary business continuity requirements.
   - Migrate only for legal/audit traceability.

## Execution Order

1. P0 workflow workbench and todo projection.
2. P0 payment/receipt execution separation.
3. P0 attachment custody for contract/payment/receipt/invoice/project files.
4. P1 invoice/tax runtime.
5. P1 settlement adjustment and treasury reconciliation runtime visibility.
6. P1 expense/deposit workflow or formal archive-only decision.
7. P2 material/product promotion and weak contract promotion.
8. P3 HR/platform audit only after explicit business decision.

## Acceptance Criteria

- `mail.activity_total` or dedicated history todo count is non-zero for
  actionable old workflow facts.
- Users can open old workflow items from a workbench and navigate to target
  records or neutral facts.
- Payment and receipt records distinguish request, approval, actual cash
  movement, and ledger state.
- Invoice/tax/deduction/fund confirmation facts have either native runtime
  models or explicitly approved archive-only policies.
- Attachment links needed for day-to-day business open successfully.
- Privacy-restricted salary/personnel facts remain unavailable to ordinary
  finance/project users.
