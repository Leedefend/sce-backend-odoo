# Migration Rebuild Artifacts

This directory contains repository-backed migration rebuild assets used to
reproduce legacy business-data reconstruction from a fresh checkout.

Most files are stored as ordinary Git objects with byte-preserving attributes.
The three files larger than GitHub's normal per-file limit are stored as
tracked parts while keeping their original local repository paths ignored:

- `fresh_db_legacy_material_detail_replay_payload_v1.csv`
- `fresh_db_legacy_workflow_detail_replay_payload_v1.csv`
- `scbsly_direct_select3_status_online_dump_20260603.json`

Run `bash artifacts/migration/materialize_large_payload_parts.sh` after checkout
when these large payloads are needed for replay or verification. The script
rebuilds the original files from `.parts/part_*` and validates their SHA-256.
