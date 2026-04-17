# Imported Fact Usability Screen v1

Task: `ITER-2026-04-17-BUSINESS-CONTINUITY-FACT-USABILITY-SCREEN`

Source scan: `docs/ops/business_continuity/imported_fact_usability_scan_v1.md`

Mode: screen only

Timestamp: `2026-04-17T20:46:01+08:00`

## Screen Boundary

This screen classifies the 12 scan candidates. It does not rescan the
repository, query new surfaces, or implement fixes.

## Classification

| Candidate | Lane | First owner layer | Implementation risk | Screen result |
| --- | --- | --- | --- | --- |
| 1. Project lifecycle imported as one opening state | business-fact alignment | business-fact layer | medium | Needs lifecycle fact alignment rules before users can continue work from imported projects. |
| 2. Project ownership/customer facts incomplete | business-fact alignment | business-fact layer | medium | Needs owner/company/customer fact materialization or explicit exception handling. |
| 3. Contracts relation-complete but workflow-state-flat | business-fact alignment | business-fact layer | medium | Needs imported contract operational state alignment based on downstream facts and audit facts. |
| 4. Contract zero-amount records | data-quality exception | business-fact layer | low-to-medium | Needs exception list and UI/operation tolerance; should not block all contract continuity. |
| 5. Payment missing company | business-fact alignment | business-fact layer | high | Needs dedicated payment continuity batch; financial domain risk applies. |
| 6. Payment sparse contract linkage | data-quality exception + business-fact alignment | business-fact layer | high | Needs dedicated payment relation screen before state or workflow changes. |
| 7. Payment state partially aligned | business-fact alignment | business-fact layer | high | Needs dedicated payment state alignment; must use downstream facts, not new approval triggers. |
| 8. Ledger exists, settlement execution empty | scene-orchestration + business-fact gap | scene-orchestration layer first | high | Needs separate settlement continuity design; do not fabricate settlement orders from ledger facts in a scan/screen chain. |
| 9. Legacy financial fact query surfaces populated | query-only legacy fact surface | scene-orchestration layer | low | Keep as query/report facts until a business process explicitly consumes them. |
| 10. Workflow audit classification mostly unknown | business-fact support evidence | business-fact layer | medium-to-high | Useful as approval evidence, but needs semantic classification screen before state writes. |
| 11. Tender/material/procurement execution empty | fresh-work lane | scene-orchestration layer | medium | Treat as new-system fresh processing unless a legacy import source is later supplied. |
| 12. Native action states may not be reachable | scene-orchestration guidance | scene-orchestration layer | medium | Needs action guidance around what is available for imported records after fact alignment. |

## Execution Lanes

### Lane A: Project Continuity Foundation

Purpose: make imported projects usable as daily-work anchors.

Inputs:
- Candidate 1
- Candidate 2
- Candidate 12 for project actions

Expected output:
- project lifecycle/phase alignment rule
- company/customer exception strategy
- action guidance for imported project records

Why first:
- Projects are the common parent for contracts, payments, ledgers, and legacy financial facts.
- This lane avoids touching payment/settlement high-risk code first.

### Lane B: Contract Continuity Alignment

Purpose: make imported contracts operationally usable without pretending they are newly drafted.

Inputs:
- Candidate 3
- Candidate 4
- Candidate 10 for contract audit support
- Candidate 12 for contract actions

Expected output:
- imported contract state alignment rule
- zero-amount exception handling
- action guidance for confirmed/imported contracts

Why second:
- Contracts already have project/partner/company links.
- Contract continuity is lower risk than payment state writes and unlocks downstream context.

### Lane C: Payment Continuity High-Risk Track

Purpose: align payment records with business facts without triggering new approvals.

Inputs:
- Candidate 5
- Candidate 6
- Candidate 7
- Candidate 10 for payment audit support

Expected output:
- payment company fact strategy
- payment contract-link exception strategy
- payment state alignment rules from ledger/downstream facts

Why separate:
- Payment is a high-risk domain under repository stop rules.
- Requires dedicated task authorization before implementation.

### Lane D: Settlement And Legacy Financial Fact Consumption

Purpose: decide how query-only legacy financial facts and empty settlement execution surfaces should become usable.

Inputs:
- Candidate 8
- Candidate 9

Expected output:
- query-only vs actionable financial fact boundary
- settlement continuity design, if business requires operational settlement records

Why later:
- Current evidence supports query availability but not safe operational materialization.

### Lane E: Fresh-Work Operational Surfaces

Purpose: keep tender/material/procurement usable for new-system work while not claiming legacy continuity.

Inputs:
- Candidate 11

Expected output:
- explicit product wording and scene guidance that these surfaces are fresh-work lanes unless legacy sources are added.

## First Recommended Execution Batch

Start with Lane A: Project Continuity Foundation.

Batch type:
- `screen` first if project lifecycle mapping rules are not already defined.
- `implement` only after lifecycle and ownership facts are mapped to concrete rules.

Stop signals for implementation:
- Any rule would infer company/customer facts without evidence.
- Project lifecycle alignment requires payment/settlement facts before project facts are stable.
- Frontend special-casing is proposed before backend fact/orchestration split is complete.

## Non-Goals

- Do not write payment states in the project or contract lanes.
- Do not fabricate settlement orders from ledgers.
- Do not convert query-only legacy financial facts into operational records without a dedicated business rule.
- Do not trigger new approvals for records whose historical business facts already prove completion.
