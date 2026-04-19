# Same-Person Cross-Account Handoff Screen v1

## Batch

- Task: `ITER-2026-04-18-SAME-PERSON-CROSS-ACCOUNT-HANDOFF-SCREEN`
- Layer Target: Business Fact Screening
- Module: same-person cross-account handoff
- Module Ownership: customer-delivery business continuity
- Kernel or Scenario: scenario
- Backend Sub-Layer: business-fact layer
- Reason: account-level cross-role screening showed no overlap, but runtime
  examples suggested the same people may exist in separate legacy/current
  accounts across upstream and downstream owner chains.

## Scope

- Screen only.
- Allowed outputs: this report, task contract, delivery context log.
- No source code changes.
- No frontend model special-cases.
- No payment, settlement, account, ACL, record-rule, or manifest changes.

## Input

- `cross_role_handoff_verify_screen_v1.md`:
  no account-level overlap exists between purchase-manager and payment-manager
  chains.
- Read-only Odoo shell probe on `sc_demo`:
  grouped active purchase-manager and payment-manager accounts by human-readable
  display name.

## Probe Result

| Fact | Count |
| --- | ---: |
| same-person overlap groups | 8 |

Detected same-person cross-account groups:

- `吴涛`: `legacy_10000009` (purchase-manager) + `wutao` (payment-manager)
- `文楠`: `legacy_10000015` (purchase-manager) + `wennan` (payment-manager)
- `李娜`: `legacy_a74a3dd36c004a4b8491675919c6be4c` (purchase-manager) + `lina` (payment-manager)
- `段奕俊`: `legacy_10000001` (purchase-manager) + `duanyijun` (payment-manager)
- `江一娇`: `legacy_10000013` (purchase-manager) + `jiangyijiao` (payment-manager)
- `税务经办人`: `legacy_2afb101f2d3d41058b33517895db14f9` (purchase-manager) + `shuiwujingbanren` (payment-manager)
- `罗萌`: `legacy_4e8191d3bad04354aebfe26315ac2614` (purchase-manager) + `luomeng` (payment-manager)
- `陈帅`: `legacy_10000007` (purchase-manager) + `chenshuai` (payment-manager)

## Classification

- The path is not a same-account unified ownership chain.
- It is also not a pure cross-person handoff problem.
- Current runtime facts show a stable same-person cross-account pattern:
  - upstream product/purchase ownership sits on legacy-style purchase-manager accounts
  - downstream settlement/payment ownership sits on current payment-manager accounts
  - the same natural people appear on both sides under different logins
- Therefore the dominant remaining issue is account-lane onboarding and account
  convergence guidance, not missing business semantics.

## Decision

- Do not change payment or settlement business code.
- Do not open a permission-governance batch from this result.
- Do not add frontend special-cases.
- The next low-cost task should classify whether operational guidance should
  instruct same-person users to switch accounts across upstream/downstream
  steps, or whether a future account-convergence/governance batch is justified.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-SAME-PERSON-CROSS-ACCOUNT-HANDOFF-SCREEN.yaml`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec` read-only same-person cross-account handoff screen: PASS
- `git diff --check`: PASS

## Risk And Stop Decision

- Result: PASS.
- Stop condition: none in this screen.
- Risk: the business path is operationally understandable now, but user guidance
  may still be needed because the same people act through different accounts
  across upstream and downstream steps.
- Boundary: follow-up remains an onboarding/account-lane classification problem,
  not a payment/settlement semantic issue.

## Next Step

Open a low-cost account-lane onboarding screen:

- classify whether current business continuity should be documented as a
  same-person cross-account operating procedure;
- distinguish documentation/onboarding need from any future account-convergence
  governance need;
- stop before any implementation batch unless a real runtime blocker is proven.
