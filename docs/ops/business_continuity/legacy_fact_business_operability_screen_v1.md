# Legacy Fact Business Operability Screen v1

## Scope
- Database: `sc_demo`
- Mode: rollback-only runtime screen
- Target: whether imported legacy business facts can carry daily operations in the new system.
- No persistent business records were created.

## Architecture Decision
- Layer Target: Business operability screening
- Backend sub-layer: business-fact layer first, then permission lane if blocked
- Reason: daily operability must be checked against backend facts and runtime authority before frontend or scene changes.

## Rollback Guarantee
Rollback persistence check after test:

| Model | Rollback marker count |
| --- | ---: |
| `construction.contract` | 0 |
| `construction.contract.line` | 0 |
| `payment.request` | 0 |

## Existing Fact Availability

| Check | Result | Evidence |
| --- | --- | --- |
| Running imported project exists | PASS | project `65` |
| Usable imported contract exists | PASS | contract `1426`, state `running` |
| Completed linked payment exists | PASS | payment `17639` |
| Project contract action exists | PASS | action `513`, model `construction.contract`, mode `tree,form` |

## Contract Handling

| Flow | Result | Evidence |
| --- | --- | --- |
| Create new contract on imported project | PASS | rollback contract created |
| Confirm contract without lines | FAIL | blocked by business rule: `请先录入合同行后再确认。` |
| Add minimum contract line | PASS | rollback line amount `1000.0` |
| Confirm contract with line | PASS | state becomes `confirmed`, amount total `1090.0` |
| Set contract running | PASS | state becomes `running` |

Interpretation:
- Contract handling is usable.
- The "confirm without lines" failure is correct business behavior, not a defect.
- Imported project/contract facts can carry new contract work.

## Payment Handling

| Flow | Result | Evidence |
| --- | --- | --- |
| Create payment on imported contract as system runtime user | PASS | rollback payment created |
| Submit payment as system runtime user | FAIL | current shell user `__system__` lacks finance submit group |
| Finance user role exists | PASS | `sc_fx_finance`, user `257` |
| Finance user has submit group | PASS | `group_sc_cap_finance_user` |
| Finance user creates payment | FAIL | record rule blocks reading linked project |

Failure detail:

```text
Fixture Finance (id=257) does not have read access to project.project
```

Finance project access matrix for project `65`:

| User | Project Read |
| --- | --- |
| `admin` | PASS |
| `sc_fx_executive` | PASS |
| `sc_fx_finance` | FAIL |
| `wutao` | PASS |
| `wennan` | PASS |
| `lina` | FAIL |
| `duanyijun` | PASS |
| `jiangyijiao` | FAIL |
| `shuiwujingbanren` | PASS |
| `luomeng` | FAIL |
| `chenshuai` | PASS |

Interpretation:
- Payment facts are now structurally ready: project, partner, company, and contract links exist for deterministic slice.
- Payment create/submit is blocked for some finance users by project record-rule visibility.
- This is a permission-governance blocker, not a frontend or scene-orchestration blocker.

## Classification

| Area | Status | Classification |
| --- | --- | --- |
| Imported project as carrier | PASS | usable business fact |
| Contract create/confirm/run | PASS | usable business flow |
| Payment create as system/admin | PASS | usable model facts |
| Payment submit for finance role | BLOCKED | permission governance |
| Frontend consumer | not implicated | no evidence of frontend defect |

## Result
PASS_WITH_RISK.

The contract business can be handled on top of imported facts. Payment handling has a concrete authority-path blocker: finance users need project visibility for the linked project before they can create/submit payment requests using imported project/contract facts.

## Next Required Lane
Dedicated permission-governance batch:

- Objective: finance/payment users can read the project facts required by payment request handling.
- Scope must explicitly include the exact `security/**` or record-rule path if changes are needed.
- Do not change payment financial semantics.
- Do not grant broad platform-admin access.
- Verify with `sc_fx_finance` or another finance user, not `__system__`.
