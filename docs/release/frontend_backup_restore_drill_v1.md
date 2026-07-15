# Frontend backup and restore drill v1

The paired backup command is `make release.rehearsal.backup`. It captures PostgreSQL custom-format dump, the matching Odoo filestore, release SHA, timestamps, sizes, and SHA-256 checksums. Backup bytes stay under ignored `artifacts/release/frontend-pilot-readiness/backup/` and must never enter Git.

The 2026-07-15 rehearsal backed up an 11,470,698-byte database dump and an 824,669-byte filestore archive in 2 seconds. The strengthened restore to `sc_release_rehearsal_restored` completed in 64 seconds; rollback restore to `sc_release_rehearsal_rollback` completed in 69 seconds. Both operations verify archive checksums, core table counts and the extracted filestore digest without moving the source filestore. Evidence is `backup/manifest.json`, `restore.json`, and `rollback.json` under the release artifact directory.

The demonstrable RPO is the backup completion point; the pilot policy is at most 24 hours, enforced by `make verify.release.monitoring`. The measured local recovery time is 64–69 seconds for this approximately 11.5 MB database dump and 0.8 MB filestore archive. It is not a production RTO claim. DBA/SRE must repeat at representative volume and confirm RTO at or below four hours before activation.

Recovery validation requires database readiness, demo exclusion, module state, attachment samples, core pages, My Work, company switching, 70 navigation leaves, and the safe/read-only J02–J11 subset. A failed checksum, count mismatch, filestore mismatch, wrong database name, or missing attachment is an immediate `NO_GO`.
