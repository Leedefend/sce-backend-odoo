# Delivery Sprint Blockers v1

## Conclusion (First)
- The repository has a solid delivery skeleton and governance baseline, but is not yet in a customer-pilot-safe state.
- This sprint switches from “feature expansion” to “delivery seal-off”, with strict P0 blocker burn-down.

## P0 Blockers (Must Close First)
| ID | Blocker | Current State | Exit Criteria | Owner |
|---|---|---|---|---|
| B1 | Frontend delivery path not sealed | `frontend gate` not consistently green (ActionView/AppShell chain has lint/type risks) | `pnpm -C frontend gate` passes consistently, no new red lines on core files | FE |
| B2 | Scene Contract / Provider shape not fully sealed | Contract/provider boundaries still have “minimum-runnable” paths | Delivery-package key scenes pass contract/provider guards | BE |
| B3 | Capability gap backlog is distorted | “All green” signals while gap backlog lacks real entries | Build real gap tiers (Blocker/Pilot Risk/Post-GA) and enforce in release gates | PM+Tech Lead |
| B4 | Delivery evidence is not one-page auditable | No unified evidence board for “9 modules × 4 role journeys” | Publish one-page readiness scoreboard (commit/db/seed/results) | Delivery |

## P1 (Immediately After)
- Script critical role journeys (PM/Finance/Procurement/Executive).
- Make search/filter/pagination/batch-action delivery status explicit.

## Sprint Boundary
- Freeze new capability additions; focus only on blockers and delivery closure.
- Priority: stability > new features.

