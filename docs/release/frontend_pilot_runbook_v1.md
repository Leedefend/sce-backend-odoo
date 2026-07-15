# Frontend pilot runbook v1

Pilot scope is one company, one or two projects, and at most 20 named users across finance, PM, project member and executive. Enabled scope is project, contract, settlement, payment request/execution, My Work, payment request form, submit and authorized approval. My Work remains payment-request-only; no unsupported approval carrier, bulk action, notification, or implicit ledger is promised.

Before opening: confirm immutable SHA/image, real domain/TLS, monitoring ownership, authorized history compatibility, representative restore timing, daily paired backup, health/readiness, account/company membership and role samples. Run compatibility, upgrade, fingerprint comparison, smoke, 70 navigation leaves, and J02–J11 against resettable rehearsal data. Production writes require a separate approved deployment change and are outside FE-RC01.

Daily checks: login/system.init, error and latency dashboards, My Work counts, one form submit/approval sample, permission/company audit sample, database/filestore capacity, backup age/checksum, and user support queue. Any P0 data/permission incident freezes the pilot and invokes rollback assessment.

Exit to broader use only after five consecutive working days with zero P0 data/permission incidents, zero P1 blocking incidents, at least 99% core-journey success, no sustained unhandled 5xx growth, successful daily paired backup, users independently completing J04–J08, amount sampling consistent, and zero cross-company/project disclosure.

Pilot support hours and named contacts must be filled by Delivery owner before activation; absence is a launch blocker. The safe shutdown path is to disable pilot access, preserve evidence, take a paired backup, and follow `frontend_rollback_runbook_v1.md`.
