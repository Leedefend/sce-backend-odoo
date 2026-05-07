# Partner Import Source Alignment Audit v1

Status: Business-fit iteration batch
Branch: `feature/user-history-data-alignment`
Source root: `/home/odoo/workspace/partner_import_source`
Legacy fresh-db payload:
`artifacts/migration/fresh_db_partner_l4_replay_payload_v1.csv`
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

Business-fit partner asset lane generated with:

```bash
python3 scripts/migration/partner_asset_generator.py \
  --business-gate artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_gate_v1.csv \
  --out .runtime_artifacts/migration_assets/partner_business_fit_sc_v1 \
  --source partner_import_source \
  --asset-version business_fit_v1 \
  --check
```

Verified with:

```bash
python3 scripts/migration/partner_asset_verify.py \
  --asset-root .runtime_artifacts/migration_assets/partner_business_fit_sc_v1 \
  --lane partner \
  --check
```

Regression guard:

```bash
python3 scripts/migration/partner_asset_business_fit_guard.py --check
```

Closure guard:

```bash
python3 scripts/migration/partner_business_fit_closure_guard.py --check
```

The closure guard regenerates and verifies the partner asset, partner-bank
asset, review queue, and rehearsal package. Current closure result: payload
7,792 rows, gate split 2,123 write / 4,225 update-only / 1,444 review, package
29 files, DB writes 0.

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

Direction correction: if the existing model cannot carry the business facts,
the model must be completed before data import. This iteration therefore extends
`res.partner.bank` first, then aligns the bank-account asset and replay write to
that model surface.

The model-level bank account surface now includes:

- `sc_legacy_external_id`
- `sc_legacy_partner_source`
- `sc_legacy_partner_id`
- `sc_legacy_partner_name`
- `sc_account_holder_name`
- `sc_bank_name`
- `sc_source_evidence`
- `sc_import_batch`

Customer and supplier forms now expose `bank_ids` as a child table so imported
accounts are visible on the business partner instead of being hidden in a
sidecar file or flattened text-only fields.

The first no-DB bank-account split is now represented by
`partner_bank_business_asset_generator.py`. It consumes the same business-fit
partner gate and emits a replay-ready CSV contract for `res.partner.bank`:

```bash
python3 scripts/migration/partner_bank_business_asset_generator.py --check
```

Runtime result:

| Item | Value |
| --- | ---: |
| source gate rows | 7,792 |
| loadable bank-account rows | 5,574 |
| discarded rows | 2,218 |
| blocked partner review rows | 1,444 |
| missing bank-account rows | 774 |
| DB writes | 0 |

The bank asset keeps `partner_external_id` equal to the business-fit partner
external ID, so the child account replay can resolve its parent after the
partner lane has loaded.

The corresponding write script is:

```bash
FRESH_DB_PARTNER_BANK_INPUT_CSV=.runtime_artifacts/migration_assets/partner_bank_business_fit_v1/10_master/partner_bank/partner_bank_master_v1.csv \
FRESH_DB_PARTNER_BANK_EXPECTED_ROWS=5574 \
python3 scripts/migration/fresh_db_partner_bank_replay_write.py
```

The write script requires the completed `res.partner.bank` extension fields and
resolves each account parent through `res.partner.legacy_partner_source` plus
`res.partner.legacy_partner_id`.

## Partner Basic Information Surface

The source snapshot also carries partner-level basic facts that were not present
in the earlier business-fit payload. The model and payload surface now carry:

- `sc_region`
- `street`
- `sc_registered_capital`
- `sc_business_scope`
- `sc_default_tax_rate`
- `sc_default_tax_rate_text`

Regenerated payload evidence:

| Item | Value |
| --- | ---: |
| business-aligned payload rows | 7,792 |
| rows with region | 791 |
| rows with address | 8 |
| rows with registered capital | 10 |
| rows with business scope | 0 |
| rows with tax rate | 3,741 |

`sc_business_scope` is still kept on the model because it is a valid partner
business fact, but it is not a required non-empty guard for this source snapshot
because the current Excel files did not provide populated values.

Tax rates are stored as both normalized percentage values and original source
text. For example, `13%` and `0.1300` both normalize to `13`, while the original
text remains available for audit.

## Import Review Queue

Blocked rows are no longer treated as disposable CSV leftovers. They now have a
system model, `sc.partner.import.review`, so the unresolved business facts can
be reviewed inside the application before being promoted to real partners.

Generated with:

```bash
python3 scripts/migration/partner_import_review_asset_generator.py --check
```

Review queue result:

| Item | Value |
| --- | ---: |
| review rows | 1,444 |
| candidate rows | 1,444 |
| unknown business role | 645 |
| personal fragment review | 617 |
| invalid bank account review | 84 |
| invalid or placeholder credit | 70 |
| multiple current payload matches | 28 |
| review rows carrying tax rate | 446 |
| review rows carrying region | 134 |

The fresh-db replay script for this queue is:

```bash
FRESH_DB_PARTNER_IMPORT_REVIEW_INPUT_CSV=artifacts/migration/partner_business_aligned_rebuild_v1/partner_import_review_queue_v1.csv \
FRESH_DB_PARTNER_IMPORT_REVIEW_EXPECTED_ROWS=1444 \
python3 scripts/migration/fresh_db_partner_import_review_replay_write.py
```

Resolved reviews can be exported back into the partner write contract with:

```bash
PARTNER_IMPORT_REVIEW_BATCH=partner_business_fit_v1 \
python3 scripts/migration/fresh_db_partner_import_review_resolution_export.py
```

The export writes resolved rows as `gate_action=write_candidate` into
`partner_import_review_resolved_promotions_v1.csv`, while ignored rows are kept
in `partner_import_review_ignored_v1.csv`.

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

The update-only queue carries substantial business facts and needs a read-only
target match probe before write mode:

| Item | Value |
| --- | ---: |
| update-only rows | 4,225 |
| rows with bank account | 3,815 |
| rows with tax rate | 1,867 |

Probe command:

```bash
PARTNER_UPDATE_ONLY_GATE_CSV=artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_gate_v1.csv \
python3 scripts/migration/fresh_db_partner_update_only_match_probe.py
```

The probe outputs unique-match, not-found, and ambiguous counts without writing
to the database. Rows that do not resolve to exactly one `res.partner` must stay
outside write mode or be sent to the review path.

After the probe has produced `partner_update_only_match_probe_v1.csv`, split the
queue with:

```bash
python3 scripts/migration/partner_update_only_probe_split.py --check
```

The split produces:

- `partner_update_only_matched_updates_v1.csv`: update-only rows with exactly
  one target partner, safe to pass to the guarded writer.
- `partner_update_only_probe_review_queue_v1.csv`: not-found or ambiguous rows,
  shaped for `sc.partner.import.review` rather than silent skipping.

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

## Partner Asset Lane Iteration

`partner_asset_generator.py` now supports a business-fit input mode through
`--business-gate`. This keeps the original `partner_sc_v1` lane and manifest
shape, but swaps the old raw-company/supplier-only logic for the current
business-aligned gate queue.

Runtime verification result:

| Item | Value |
| --- | ---: |
| asset package | `partner_sc_v1` |
| runtime asset root | `.runtime_artifacts/migration_assets/partner_business_fit_sc_v1` |
| loadable XML records | 6,348 |
| review/discard rows | 1,444 |
| DB writes | 0 |

The regression guard verifies both sides:

- existing `migration_assets` partner lane still passes with 6,541 records;
- business-fit runtime lane generates and verifies with 6,348 loadable records;
- 1,444 rows remain in review/discard;
- required business fields and gates are present.

The generated XML now allows the current customer/supplier information surface:

- `customer_rank`
- `supplier_rank`
- `sc_supplier_type`
- `sc_account_name`
- `sc_bank_name`
- `sc_bank_account`

The validation gate has also moved from the old `no_partner_rank_fields` logic
to:

- `partner_role_fields_allowed`
- `partner_basic_info_fields_present`
- `write_gate_queues_present`

This is the first concrete step of iterating the original asset package rather
than submitting a final complete package.

## Fresh-DB Replay Bridge

The fresh-db replay bridge now accepts the iterated business-fit partner asset
surface instead of only the old L4 identity/tax payload. This keeps the
historical replay flow usable while allowing the current `res.partner` model
fields to pass through the same contract.

No-DB adapter rehearsal:

```bash
python3 scripts/migration/partner_asset_generator.py \
  --business-gate artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_gate_v1.csv \
  --out .runtime_artifacts/migration_assets/partner_business_fit_sc_v1 \
  --source partner_import_source \
  --asset-version business_fit_v1 \
  --check

PARTNER_ASSET_XML=.runtime_artifacts/migration_assets/partner_business_fit_sc_v1/10_master/partner/partner_master_v1.xml \
FRESH_DB_PARTNER_L4_OUTPUT_JSON=.runtime_artifacts/migration/fresh_db_partner_l4_business_fit_adapter_result_v1.json \
FRESH_DB_PARTNER_L4_OUTPUT_CSV=.runtime_artifacts/migration/fresh_db_partner_l4_business_fit_payload_v1.csv \
FRESH_DB_PARTNER_L4_OUTPUT_REPORT=.runtime_artifacts/migration/fresh_db_partner_l4_business_fit_adapter_report_v1.md \
python3 scripts/migration/fresh_db_partner_l4_replay_adapter.py
```

Rehearsal result:

| Item | Value |
| --- | ---: |
| adapter payload rows | 6,348 |
| duplicate replay identities | 0 |
| raw source misses | 0 |
| DB writes | 0 |

The adapter payload now carries:

- `vat`
- `company_type`
- `customer_rank`
- `supplier_rank`
- `sc_supplier_type`
- `sc_account_name`
- `sc_bank_name`
- `sc_bank_account`

## Customer/Supplier Display Surface

The business-fit lane is not considered usable just because replay payloads can
be generated. The user-facing customer and supplier pages must also expose the
facts needed for lookup, review, and operational use.

Current display surfaces:

| Surface | Business facts visible |
| --- | --- |
| Customer list | role markers, credit code, region, registered capital, default tax rate, account name, bank, account number, legacy identity |
| Customer form | basic profile, contact details, compatibility account fields, `bank_ids`, business scope, legacy evidence |
| Customer search | name, credit code, region, default tax rate, bank, account number, legacy identity, mixed customer/supplier filter |
| Supplier list | role markers, supplier type, credit code, region, registered capital, default tax rate, account name, bank, account number, legacy identity |
| Supplier form | supplier type, basic profile, contact details, compatibility account fields, `bank_ids`, notes, attachments, business scope, legacy evidence |
| Supplier search | supplier type, credit code, region, default tax rate, bank, account number, legacy identity, mixed supplier/customer filter |
| Import review queue | blocked/update-only rows with role suggestion, target partner, bank/tax/identity evidence, and resolve actions |

Static display guard:

```bash
python3 scripts/migration/partner_display_surface_guard.py --check
```

Latest no-DB result:

| Item | Value |
| --- | ---: |
| checked views | 9 |
| checked search views | 3 |
| checked action domains | 2 |
| DB writes | 0 |

This answers the current readiness question more directly: `res.partner` and
`res.partner.bank` now carry the customer/supplier business facts, the customer
and supplier menus are constrained by `customer_rank` / `supplier_rank`, and the
primary list/form/search surfaces expose those facts instead of hiding them
inside the replay package.

`fresh_db_partner_l4_replay_write.py` consumes those explicit payload fields
when present and only falls back to the legacy source-type role inference for
old payloads. For the business-fit 6,348-row payload, run the write script with:

```bash
FRESH_DB_PARTNER_L4_INPUT_CSV=.runtime_artifacts/migration/fresh_db_partner_l4_business_fit_payload_v1.csv \
FRESH_DB_PARTNER_L4_EXPECTED_ROWS=6348 \
python3 scripts/migration/fresh_db_partner_l4_replay_write.py
```

The write step still requires an allowed fresh replay database and was not
executed in this local pass because the compose `odoo` service was unavailable.

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
| tarball sha256 | regenerated per package build |
| tarball bytes | regenerated per package build |
| packaged file count | includes required artifacts plus available optional probe/export artifacts |
| package build DB writes | 0 |

The rehearsal includes:

- the business-aligned payload and gate queues;
- the current-only, blocked review, and application review queues;
- scripts for partner bank replay, review replay, review resolution export,
  update-only match probing, and update-only probe splitting;
- source audit summaries needed to explain why the payload differs from the
  older fact-only lane;
- replay scripts required to regenerate and apply the payload;
- `manifest.json` with row counts, byte sizes, sha256 checksums, build commands,
  post-probe commands, dry-run command, and write command.

This rehearsal must not be treated as final delivery. The next code iteration
should refresh the original partner asset generator/manifest logic so the asset
lane itself produces the business-fit payload and gates.
