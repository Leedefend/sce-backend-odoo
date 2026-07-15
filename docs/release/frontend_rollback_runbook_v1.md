# Frontend pilot rollback runbook v1

Trigger rollback for widespread login/system.init failure, permission or company isolation loss, amount inconsistency, migration drift, unreadable attachments, blocked core journeys, sustained error threshold breach, or severe performance regression.

1. Stop admission to the new release and record candidate SHA/database.
2. Stop only the pilot release runtime; do not stop development or acceptance services.
3. Select the previously approved application image by immutable digest.
4. If the release performed no data-changing migration, start the previous image against the unchanged database. Otherwise restore the paired database and filestore with `make release.rehearsal.rollback` first in rehearsal and the approved production procedure at deployment time.
5. Confirm `dbfilter`, `list_db=false`, environment marker, and database name before startup.
6. Run login, system.init, attachment read, project/contract/settlement/payment read, My Work, company isolation and navigation smoke.
7. Record elapsed time and incident owner; reopen traffic only after permission and amount sampling pass.

The 2026-07-15 isolated rollback restored `sc_release_rehearsal_rollback` in 69 seconds with matching checksums, core counts, and filestore digest. This command never targets production and the guard rejects empty, `postgres`, `sc_demo`, `sc_frontend_acceptance`, `sc_prod`, and `sc_prod_sim` names.
