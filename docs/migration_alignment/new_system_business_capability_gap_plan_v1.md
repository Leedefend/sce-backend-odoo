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
- settlement adjustment runtime records: `12913` legacy rows projected,
  `12528` legacy-confirmed rows
- historical fund confirmation lines: `13398`
- historical expense/deposit facts: preserved as searchable finance facts
- historical expense reimbursement lines: preserved as searchable line facts
- expense/deposit runtime claims: `13314` legacy rows projected,
  `13279` legacy-confirmed rows
- treasury reconciliation runtime records: fund daily and fund confirmation
  rows with project/amount/balance anchors are projected to
  `sc.treasury.reconciliation`; old completed rows are kept as
  `legacy_confirmed`
- receipt/income runtime records: receipt income facts and residual receipt
  rows with project/amount anchors are projected to `sc.receipt.income`; old
  completed rows are kept as `legacy_confirmed`
- construction diary runtime records: legacy construction diary/quality-note
  lines with project anchors are projected to `sc.construction.diary`; old
  completed rows are kept as `legacy_confirmed`
- historical financing loan facts: `318`
- historical fund daily snapshots: `496`
- historical fund daily lines: `7754`
- historical material categories/details: preserved as archive-first master data
- historical purchase/general contracts: preserved as searchable contract facts
- historical users: `101`
- historical user roles: `330`, projected to runtime capability groups: `253`
- migrated users with runtime capability groups: `96`
- current historical project scopes: `20000`, linked to runtime projects: `17453`
- legacy projects with migrated user follower access: `480`
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

P1-C keeps old expense/deposit and expense reimbursement rows as historical
finance facts instead of forcing them into new editable reimbursement workflow.
This preserves project, applicant, payee, amount, approval amount, and source
document context while avoiding false new-system approvals. The
`history_expense_deposit_runtime_probe` validates the searchable surfaces.

P2-A exposes historical material categories and details to material roles and
adds a controlled material-manager action to promote selected legacy material
rows into `product.template` / `product.product`. Promotion is opt-in and
records the legacy material source on the product; the full historical catalog
stays archive-first.

P2-B exposes `T_CGHT_INFO` purchase/general contract residue as searchable
contract facts. These rows are not auto-promoted to native contracts because
the current carrier has partner text and credit-code evidence, not a verified
`partner_id`. The runtime probe reports strong-anchor candidates for a future
explicit promotion pass.

P2-C projects legacy user roles and current project scopes into runtime access.
Role names are conservatively mapped to SC capability groups by business
domain; generic/admin-like legacy labels are retained as unmapped evidence.
Current project scopes are resolved through project `legacy_parent_id` and
applied as project follower access so existing project record rules allow
continuity without using removed scope rows as new authority.

P1-D adds `sc.settlement.adjustment` as the runtime carrier for settlement
deductions and adjustments. Historical `T_KK_SJDJB_CB` rows with project anchors
are projected into this model as legacy rows; old completed rows become
`legacy_confirmed`, while new-system users can continue registering and
confirming manual settlement adjustments from the settlement center.

P1-E adds `sc.expense.claim` as the runtime carrier for expense reimbursement
and deposit/guarantee money operations. Historical expense reimbursement and
expense/deposit facts with project anchors are projected as legacy rows; old
completed rows become `legacy_confirmed`, while new-system finance users can
continue registering, submitting, approving, and completing manual expense or
deposit claims.

P1-F adds `sc.treasury.reconciliation` as the runtime carrier for treasury
daily reconciliation and fund confirmation. Historical fund daily lines and
fund confirmation lines with project anchors are projected as legacy rows; old
completed rows become `legacy_confirmed`, while new-system finance users can
continue registering, confirming, and completing treasury reconciliation work.

P1-G adds `sc.receipt.income` as the runtime carrier for receipt and income
registration outside strict `payment.request` approval rules. Historical
receipt income facts and residual receipt rows with project/amount anchors are
projected as legacy rows; old completed rows become `legacy_confirmed`, while
new-system finance users can continue registering, confirming, and marking
manual receipt income as received.

P1-H adds `sc.construction.diary` as the runtime carrier for project-site
construction diary and quality-note records. Historical construction diary
lines with project anchors are projected as legacy rows; old completed rows
become `legacy_confirmed`, while new-system project users can continue
registering, confirming, and completing manual site diary records.

## Capability Matrix

| Legacy business area | Current new-system state | Gap | Plan |
| --- | --- | --- | --- |
| Projects, partners, members | Runtime records and anchors exist; current legacy user-project scopes are projected to project follower access where anchors resolve | 2547 current scope rows still lack project anchors; removed scopes remain audit-only | Keep current replay; recover missing anchors only from stronger project evidence and never authorize from removed scope rows. |
| Construction contracts | Runtime `construction.contract` exists | Some old terms/attachments are still history-only | Add contract historical evidence smart tabs and attachment drill-through. |
| Supplier contracts | Runtime supplier contracts and summary lines exist | Some blocked/weak partner contract residue remains neutral | Keep weak rows neutral; add partner recovery only for confirmed active counterparties. |
| Purchase/general contracts | Historical purchase/general contract workbench is visible | Native promotion requires verified `partner_id` anchors | Keep searchable contract facts now; promote only rows with confirmed project, partner, amount, tax, and attachment policy. |
| Payment requests | Runtime `payment.request` exists with states; historical actual outflow is projected to `sc.treasury.ledger` | 153 nonpositive cash-like rows remain fact-only | Keep request/approval/cash ledger separated; improve residual handling only with stronger business anchors. |
| Receipts and income | Receipt requests plus neutral receipt facts exist; historical receipts are projected to `sc.treasury.ledger`; receipt income and residual receipt rows are projected to `sc.receipt.income` | Rows without project/amount anchors remain fact-only; accounting posting remains explicit | Use receipt income runtime for continuing income registration; link payment request, treasury ledger, contract, and partner anchors only when evidence is strong. |
| Invoice and tax | Invoice/tax facts and invoice registration workbench are visible | Accounting posting remains explicit, not automatic migration side effect | Keep searchable historical surfaces; promote to accounting moves only through future controlled posting workflow. |
| Settlement/deductions | New settlement order exists; historical deduction facts are projected to `sc.settlement.adjustment`; new manual adjustment registration and confirmation exists | Historical rows without project anchors remain fact-only; legacy rows are not auto-linked to settlement orders without stronger anchors | Use settlement adjustment runtime for continuing operations; link historical rows to settlement/contract/partner only when explicit anchors are recovered. |
| Fund daily, fund confirmation, financing | Cash ledger, fund confirmation, financing, fund daily snapshot, and fund daily line workbenches are visible; project-anchored fund daily/confirmation facts are projected to `sc.treasury.reconciliation` | Financing/borrowing facts remain archive-first and historical rows without project anchors remain fact-only | Use treasury reconciliation runtime for continuing daily/confirmation operations; keep financing promotion separate until a repayment/borrowing workflow is explicitly designed. |
| Expense reimbursement/deposit | Expense/deposit facts and reimbursement lines are projected to `sc.expense.claim`; new manual registration, approval, and completion exists | Legacy rows are not automatically linked to payment requests unless stronger payment anchors are recovered | Use runtime claims for continuing operations; supplement payment request links only through explicit anchor recovery. |
| Material catalog | Search archive and controlled material-to-product promotion exist | Bulk promotion remains intentionally disabled | Keep archive-first catalog; material managers promote selected rows only when needed for new material plans/purchase flows. |
| Attachments | URL/index facts exist; 19,537 URL attachments and 178,931 file index rows are visible | Binary custody is not complete | Keep URL/index custody available now; copy selected binaries only after repository and hash policy are approved. |
| Construction diary / quality notes | Historical construction diary facts are projected to `sc.construction.diary`; project users can register new diary records | Binary attachments remain URL/path custody only | Use construction diary runtime for continuing site records; binary copy remains under attachment custody policy. |
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
   - `sc.settlement.adjustment` is available as a native adjustment model.
   - Legacy project-anchored deduction/adjustment rows are projected as
     historical runtime records.
   - Contract/payment/receipt links remain explicit follow-up work where
     anchors are strong enough.

3. Treasury daily/reconciliation runtime
   - `sc.treasury.reconciliation` is available as the native daily and fund
     confirmation document.
   - Historical project-anchored fund daily lines and fund confirmation rows
     are projected as historical runtime records.
   - New operations can be confirmed and reconciled in the finance center.

4. Expense reimbursement and deposit workflow
   - `sc.expense.claim` is available as the native expense/deposit document.
   - Historical project-anchored expense/deposit rows are projected as
     historical runtime records.
   - New operations can be submitted, approved, and completed in the finance
     center.

## P2 Controlled Promotion and Search

1. Material archive to product promotion
   - Keep 2.27M material rows out of products by default.
   - Search/archive UI and "promote selected material" action are available.
   - Promotion creates or links a product and preserves the legacy material
     source on the product record.

2. Purchase/general contract promotion
   - Recover partner anchors for `T_CGHT_INFO` rows only where counterparty is
     confirmed.
   - Promote to native contract only after project, partner, amount, tax, and
     attachment policies pass.
   - Current iteration exposes the archive and reports strong-anchor candidate
     counts; it does not invent partner links from text alone.

3. Historical user scope review
   - Legacy roles are projected to runtime capability groups when the role name
     has a clear business-domain meaning.
   - Current project scopes are linked to runtime projects by
     `project_project.legacy_parent_id` and applied as follower access for
     existing project record rules.
   - Removed and ambiguous scope rows remain evidence only.

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
6. P1 expense/deposit searchable archive and formal archive-first decision.
7. P2 material/product promotion and weak contract promotion.
8. P2 historical user access projection and missing project-scope anchor
   review.
9. P3 HR/platform audit only after explicit business decision.

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
- Migrated users with clear old role/scope facts can enter the corresponding
  new-system business centers and open linked projects.
- Privacy-restricted salary/personnel facts remain unavailable to ordinary
  finance/project users.
