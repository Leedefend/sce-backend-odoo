# Partner Import Source Alignment Audit v1

Status: Business-fit iteration batch
Branch: `feature/user-history-data-alignment`
Source root: `/home/odoo/workspace/partner_import_source`
Current payload: `artifacts/migration/fresh_db_partner_l4_replay_payload_v1.csv`
Current rebuild payload:
`artifacts/migration/fact_based_partner_rebuild_2_fact_only_20260506T2055/fact_based_partner_rebuild_payload_v1.csv`

## Conclusion

The current partner replay and rebuild payloads are structurally valid, but they
are not fully aligned with the user's current business source snapshot. The
source is not a pure customer list or a pure supplier list: it is a mixed
counterparty register assembled from supplier registry files, expense-unit
registry files, and counterparty cash-flow files.

The old replay payload also loses basic entity information. It only carries
identity and role fields such as `legacy_partner_source`, `legacy_partner_id`,
`name`, `tax_no`, `source_type`, and replay metadata. It does not carry bank
account, bank name, project source, cooperation type, region, address, or tax
rate evidence from the Excel source.

The newer fact-based rebuild payload already carries several of these columns,
but it was generated in `fact-only` role mode and only used the `2/` source
directory. That leaves root-level supplier registry files and registry-only
supplier role evidence under-aligned with business reality.

## Evidence

Generated with:

```bash
python3 scripts/migration/partner_import_source_audit.py
```

Artifacts:

- `artifacts/migration/partner_import_source_audit_v1/summary_v1.json`
- `artifacts/migration/partner_import_source_audit_v1/source_rows_v1.csv`
- `artifacts/migration/partner_import_source_audit_v1/source_entities_v1.csv`
- `artifacts/migration/partner_import_source_audit_v1/source_payload_gap_samples_v1.csv`

Normalized no-DB asset generated with:

```bash
python3 scripts/migration/partner_import_source_asset_build.py
```

Asset artifacts:

- `artifacts/migration/partner_import_source_asset_v1/partner_master_source_v1.csv`
- `artifacts/migration/partner_import_source_asset_v1/partner_master_review_queue_v1.csv`
- `artifacts/migration/partner_import_source_asset_v1/partner_master_source_summary_v1.json`

Business-alignment overlay generated with:

```bash
python3 scripts/migration/partner_business_alignment_overlay.py
```

Overlay artifacts:

- `artifacts/migration/partner_business_alignment_overlay_v1/partner_business_alignment_summary_v1.json`
- `artifacts/migration/partner_business_alignment_overlay_v1/partner_business_alignment_overlay_v1.csv`
- `artifacts/migration/partner_business_alignment_overlay_v1/partner_business_alignment_action_queue_v1.csv`

Unified rebuild payload generated with:

```bash
python3 scripts/migration/partner_business_aligned_rebuild_adapter.py
```

Unified payload artifacts:

- `artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_result_v1.json`
- `artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_payload_business_aligned_v1.csv`
- `artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_current_only_review_v1.csv`

Write gate generated with:

```bash
python3 scripts/migration/partner_business_aligned_rebuild_gate.py
```

Write gate artifacts:

- `artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_gate_result_v1.json`
- `artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_gate_v1.csv`
- `artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_write_candidates_v1.csv`
- `artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_update_only_v1.csv`
- `artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_blocked_review_v1.csv`

Business-fit audit generated with:

```bash
python3 scripts/migration/partner_asset_business_fit_audit.py
```

Business-fit audit artifact:

- `artifacts/migration/partner_asset_business_fit_audit_v1.json`

Replay rehearsal package generated with:

```bash
python3 scripts/migration/partner_business_aligned_replay_package_build.py
```

Replay rehearsal artifacts:

- `artifacts/migration/partner_business_aligned_replay_package_v1/manifest.json`
- `artifacts/migration/partner_business_aligned_replay_package_v1/package_build_result_v1.json`
- `artifacts/migration/partner_business_aligned_replay_package_v1.tar.gz`

## Source Shape

| Metric | Value |
| --- | ---: |
| source rows | 12,272 |
| source entities | 7,792 |
| counterparty-flow rows | 5,812 |
| supplier-registry rows | 6,254 |
| expense-unit registry rows | 206 |
| entities with tax number | 2,253 |
| entities without tax number | 5,539 |
| personal/name fragments | 705 |

Role evidence split:

| Target role from source evidence | Entities |
| --- | ---: |
| supplier | 7,083 |
| customer and supplier | 51 |
| customer | 13 |
| unknown | 645 |

The role split is evidence-based, not final business approval. It proves the
source must be normalized as mixed counterparty data before any write.

## Current Payload Gap

| Metric | Value |
| --- | ---: |
| current payload rows | 6,541 |
| current payload `cooperat_company` rows | 3,899 |
| current payload `company_supplier` rows | 2,642 |
| source names missing in payload | 1,399 |
| source tax numbers missing in payload | 410 |
| payload names missing in source | 1,382 |
| payload tax numbers missing in source | 1,785 |
| source/payload name overlap | 4,584 |
| source/payload tax overlap | 1,843 |

Basic-info schema gap:

| Field family | Present in source | Present in current payload |
| --- | --- | --- |
| bank name / bank account | yes | no |
| project source | yes | no |
| cooperation type / main supply type | yes | no |
| region / address | partial | no |
| tax rate | yes | no |

Source completeness counts:

| Source evidence | Entity count |
| --- | ---: |
| entities with bank account | 6,602 |
| entities with bank name | 6,606 |
| entities with region | 791 |
| entities with address | 8 |
| entities with business scope | 0 |

## Normalized Asset Output

The first normalized asset is no-DB and does not write Odoo. It preserves the
source evidence that the old payload did not carry.

| Asset status | Rows |
| --- | ---: |
| loadable | 2,253 |
| missing-tax review | 4,245 |
| unknown-role review | 645 |
| personal-fragment review | 598 |
| mixed-role review | 51 |

The asset contains 7,792 rows, including 6,602 rows with bank account evidence
and 6,606 rows with bank name evidence. Review rows are intentionally separated
into `partner_master_review_queue_v1.csv` so the loader can later apply a narrow
write policy instead of silently importing ambiguous identities.

This asset is not a replacement data-rebuild package. It is a comparison and
normalization layer for the existing rebuild flow.

## Business Alignment Overlay

Compared with the latest fact-based rebuild payload, the source snapshot
produces these alignment actions:

| Action | Rows |
| --- | ---: |
| fill basic info | 5,794 |
| adjust business role | 1,151 |
| add missing partner candidate | 668 |
| already aligned | 179 |

The large `fill basic info` queue is mostly caused by bank, bank account,
project, and tax-rate evidence being present in the source snapshot but absent
or empty in the current rebuild payload row. The `adjust business role` queue is
the evidence that `fact-only` role mode is too narrow for this user source:
supplier registry and payment-flow evidence need to participate in
`supplier_rank` and mixed-role decisions.

In Odoo, bank accounts belong to `res.partner.bank`, not to `res.partner`.
Therefore, "handle bank information separately" means the aligned rebuild must
write partner identity and role fields to `res.partner`, then write account
holder, bank name, and account number to `res.partner.bank` linked to the same
partner. It does not mean a separate business objective or a new rebuild process.

## Unified Payload

`partner_business_aligned_rebuild_adapter.py` keeps the existing fact-based
payload column contract and refreshes it from the full business source root. This
turns the overlay into the next loader input instead of a parallel asset lane.

| Metric | Value |
| --- | ---: |
| existing fact-based payload rows | 5,233 |
| business-aligned payload rows | 7,792 |
| current-only rows for review | 26 |
| rows with bank account | 6,602 |
| rows with bank name | 6,606 |
| rows with credit code | 2,253 |

Role split in the unified payload:

| Role | Rows |
| --- | ---: |
| supplier | 7,083 |
| customer and supplier | 51 |
| customer | 13 |
| unknown review | 645 |

Review flags are carried in the existing `review_flags` column. High-volume flags
include `missing_credit_code` for 5,539 rows, `personal_fragment_review` for 705
rows, and `unknown_business_role` for 645 rows. These flags should gate write
mode rather than block the unified payload generation itself.

## Write Gate

The gate classifies the unified payload before any Odoo write:

| Gate action | Rows | Meaning |
| --- | ---: | --- |
| write candidate | 2,123 | may create or update when target matching is unambiguous |
| update-only candidate | 4,225 | may update an existing unique target but must not create a new partner |
| blocked review | 1,444 | manual review only |

Blocking review flags include invalid bank accounts, placeholder credit codes,
multiple current matches, personal fragments, and unknown business roles.
`missing_credit_code` rows are update-only by default because many historical
suppliers are valid business counterparties but unsafe to create automatically
without stronger identity.

The guarded Odoo shell writer is:

```bash
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim \
  MIGRATION_WRITE_MODE=dry-run \
  bash scripts/ops/odoo_shell_exec.sh \
  < scripts/migration/partner_business_aligned_rebuild_write.py
```

Use `MIGRATION_WRITE_MODE=write` only after the dry-run result has been reviewed.
The writer resolves targets by legacy identity, VAT, then exact name. It writes
only the fields already present on the current `res.partner` extension:
role ranks, supplier type, account name, bank name, bank account, VAT, and
legacy traceability.

## Design Implication

The next iteration should not patch `customer_rank` and `supplier_rank` directly
from the old replay payload. It should feed the existing rebuild flow with a
business-alignment overlay from `/home/odoo/workspace/partner_import_source`
that contains explicit evidence:

- stable identity: tax number when valid, otherwise normalized name plus source
  provenance;
- role evidence: supplier registry, payment amount, receipt amount, expense-unit
  tags, and project source;
- basic info: bank name, bank account, account holder, tax rate, region,
  address, cooperation type, and source file/row;
- conflict status: loadable, mixed-role, missing-tax, personal-fragment,
  duplicate-name, and unknown-role.

The next step is to point the current loader at
`fact_based_partner_rebuild_payload_business_aligned_v1.csv`, apply write gates
from `review_flags`, and keep the 26 current-only rows in manual review. This
keeps the existing rebuild package structure intact while correcting the
business alignment gap and avoids silently losing user-provided basic
information.

Current environment note: local static generation and Python compilation passed.
The Odoo dry-run command requires the compose `odoo` service to be running.

## Asset Business-Fit Audit

The important output of this iteration is not the tarball. The primary finding
is that the old `partner_sc_v1` asset lane no longer fits the current model and
business source.

| Check | Old asset | Current business-fit result |
| --- | ---: | ---: |
| partner rows | 6,541 | 7,792 |
| row delta |  | 1,251 |
| write candidates |  | 2,123 |
| update-only candidates |  | 4,225 |
| blocked review rows |  | 1,444 |

Old XML field surface:

- keeps: `name`, `company_type`, `vat`, legacy identity/evidence fields;
- misses current business fields:
  `customer_rank`, `supplier_rank`, `sc_supplier_type`, `sc_account_name`,
  `sc_bank_name`, `sc_bank_account`;
- carries an outdated validation gate: `no_partner_rank_fields`.

The logical pages that need iteration are therefore:

| Logical page | Required change |
| --- | --- |
| identity and dedup | Move from old 6,541-row asset logic to the 7,792-row business source normalization. |
| role semantics | Replace `no_partner_rank_fields`; roles now need explicit customer/supplier/mixed evidence. |
| basic info surface | Include supplier type and account fields now available on `res.partner`. |
| write gate | Keep write/update-only/blocked queues as part of the replay contract. |
| review queue | Preserve missing-credit, personal-fragment, unknown-role, invalid-account cases for review. |

This is the actual iteration target for the original asset package.

## Replay Rehearsal Package

The generated tarball is a rehearsal artifact for checking package completeness.
It is not the final package to submit. It helps verify which files a future
complete replay package must include after the old partner asset lane has been
iterated.

Rehearsal result:

| Item | Value |
| --- | --- |
| rehearsal root | `artifacts/migration/partner_business_aligned_replay_package_v1` |
| tarball | `artifacts/migration/partner_business_aligned_replay_package_v1.tar.gz` |
| tarball sha256 | `f530d77b87fe45759ba304735d04804074b140b0c33956865c5a8b6c8361171e` |
| tarball bytes | `1,610,738` |
| packaged file count | 17 |
| package build DB writes | 0 |

The rehearsal includes:

- the business-aligned payload and gate queues;
- the current-only and blocked review queues;
- source audit summaries needed to explain why the payload differs from the
  older fact-only lane;
- replay scripts required to regenerate and apply the payload;
- `manifest.json` with row counts, byte sizes, sha256 checksums, build commands,
  dry-run command, and write command.

This rehearsal must not be treated as final delivery. The next code iteration
should refresh the original partner asset generator/manifest logic so the asset
lane itself produces the business-fit payload and gates.
