# v1.1 Engineering Risk Ledger

Date: 2026-07-12
Owner: release owner

| ID | Risk | Level | Owner | Due | Mitigation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| R-001 | Uncontrolled changes continue to enter `main` without PR evidence. | High | Repository admin | Week 1 | Enable branch protection, PR template, CODEOWNERS, required checks. | Branch protection screenshot or repository rules export. |
| R-002 | Existing validation scripts are numerous and overlapping, causing false confidence or wasted execution time. | High | Test owner | Week 2 | Complete `test_inventory.csv`, classify layers, retire duplicate guards. | Inventory PR and retired-script list. |
| R-003 | Core money and accumulated values lack focused unit coverage. | High | Backend owner | Week 2 | Add unit tests for budget, contract, payment, settlement, tax, accumulated values. | CI unit report. |
| R-004 | Role and project isolation may regress through menu, model, or Intent API changes. | High | Security owner | Week 3 | Add permission integration tests and Intent authorization tests. | Permission matrix report. |
| R-005 | Production backup/filestore restore is assumed but not repeatedly proven. | High | DevOps owner | Week 5 | Run DB and filestore restore drill in an empty environment. | Restore drill report with RPO/RTO. |
| R-006 | Makefile and core module size make CI and ownership hard to maintain. | Medium | Architecture owner | Week 4 | Add dependency map, split plan, service-layer ADR, complexity budget. | ADRs and split PR. |
| R-007 | E2E evidence does not represent real business-chain completion. | High | QA owner | Week 3 | Implement 12 named E2E scenarios with fixed data and artifacts. | E2E report with screenshots/logs. |
| R-008 | Secrets or real credentials are committed to repository or image layers. | High | DevOps owner | Week 1 | Run secret scan in CI and rotate any discovered credential. | SEC-06 report. |
| R-009 | Large BOQ/import/data-scale paths are not performance-baselined before pilot. | Medium | Performance owner | Week 5 | Build S/M/L/XL performance datasets and measure P95. | Performance baseline report. |
| R-010 | Pilot enters real usage without daily issue/evidence loop. | Medium | Project manager | Week 6 | Define pilot issue labels, daily metrics, exit criteria, and sign-off template. | Pilot runbook and daily report template. |
| R-011 | Core E2E journey coverage has only preflight coverage for BOQ import, BOQ-to-WBS/task generation, and settlement approval. | High | QA owner | Week 3 | Upgrade E2E-02, E2E-03, and E2E-08 from preflight to fixed-data browser/API journeys with artifacts. | `e2e_journey_matrix.md`, `make test.e2e.preflight`, and future E2E run artifacts. |
| R-012 | Three P0 split-plan files continue to absorb unrelated behavior: `ContractFormPage.vue`, `Makefile`, `BusinessConfigSurfaceView.vue`. | High | Architecture owner | Week 4 | Assign owners and split plans before accepting non-defect additions. | `split_plan_queue.md` and follow-up PRs. |

## Review Cadence

- Review every Wednesday during convergence.
- Any High risk without mitigation progress for 3 working days must be escalated to the release owner.
- Risk closure requires evidence, not only implementation status.
