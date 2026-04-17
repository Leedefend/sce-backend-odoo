# Fresh Work Operational Usability Scan v1

## Scope
- Database: `sc_demo`
- Mode: read-only scan
- Focus: project, contract, and payment daily-business continuity after imported facts were aligned.
- No business records were created, updated, deleted, or action-triggered.

## Architecture Decision
- Layer Target: Runtime business usability scan
- Backend sub-layer: business-fact layer
- Reason: usability gaps must be diagnosed against backend-owned business facts before frontend consumption or scene orchestration changes.

## Entry Surface Check

### Project
- Model exists: yes
- Access: read/create/write/unlink all available for current runtime user
- Actions: 14
- Views: form/tree/search/kanban/calendar/activity are available
- State distribution:
  - `draft / initiation / ready`: 55
  - `in_progress / execution / in_progress`: 701

Continuity result:
- Imported projects: 755
- Imported running projects: 701
- Running projects missing owner or location: 701

Interpretation:
- Imported projects with downstream facts are now usable as execution projects.
- Normal fresh-work transition remains guarded by owner/location/BOQ prerequisites.
- Missing owner/location on imported running projects is an imported data-quality/business-fact gap, not a frontend issue.

### Contract
- Model exists: yes
- Access: read/create/write/unlink all available for current runtime user
- Actions: 7
- Views: form/tree are available
- Required fields: `company_id`, `currency_id`, `partner_id`, `project_id`, `subject`, `tax_id`, `type`
- Imported contracts: 6793
- Imported usable contracts: 6685
- Missing project: 0
- Missing partner: 0
- Missing company: 0

State distribution:
- `in / confirmed`: 1083
- `in / draft`: 93
- `in / running`: 4137
- `out / confirmed`: 819
- `out / draft`: 15
- `out / running`: 646

Interpretation:
- Contract continuity is usable for daily follow-up.
- The 108 draft contracts are intentionally retained because no downstream business fact was found.

### Payment Request
- Model exists: yes
- Access: read/create/write/unlink all available for current runtime user
- Actions: 7
- Views: form/tree are available
- Required fields: `amount`, `currency_id`, `name`, `partner_id`, `project_id`, `type`

State distribution:
- `done / validated`: 12194
- `draft / no`: 17908

Continuity checks:
- Total payment requests: 30102
- Done and validated: 12194
- Missing project: 0
- Missing partner: 0
- Missing company: 30102
- Missing contract: 28299
- Payment ledger rows: 12194
- Ledger-linked requests: 12194
- Ledger amount total: 2087094963.14

Interpretation:
- The downstream-fact payment batch is operationally usable as completed payment evidence.
- Fresh payment creation has model-level create access and core required fields.
- Imported payment records still have backend business-fact gaps for `company_id` and `contract_id`.
- These gaps are not scene layout or frontend-consumer issues.

## Classification

| Finding | Classification | Next Lane |
| --- | --- | --- |
| Imported projects running but missing owner/location | data-quality/business-fact | project imported ownership/location fact screen |
| Imported contracts have project/partner/company and usable states | pass | no immediate lane |
| 12194 payment requests are done/validated with ledger facts | pass | no immediate lane |
| All payment requests missing `company_id` | business-fact | dedicated payment linkage fact alignment |
| Most payment requests missing `contract_id` | business-fact | dedicated payment linkage fact alignment |

## Result
PASS with next high-risk lane identified.

The system can now carry imported project, contract, and completed-payment facts forward for daily browsing and follow-up. The next material blocker for full business continuity is payment linkage completeness, especially company and contract linkage on imported payment requests.

## Next Recommended Task
Open a dedicated high-risk payment linkage fact alignment task:

- derive `company_id` from linked project or contract where deterministic
- derive `contract_id` only from unambiguous downstream or source manifest evidence
- do not infer contract linkage from amount/name similarity
- do not touch settlement or accounting records
- produce rollback snapshot before any write
