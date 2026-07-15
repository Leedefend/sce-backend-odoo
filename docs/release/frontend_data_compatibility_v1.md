# Frontend data compatibility v1

The read-only entry point is `make verify.release.data_compatibility DB_NAME=sc_release_rehearsal`. It checks module state, demo exclusion, company/user integrity, core object counts, required relationships/currencies, known demo accounts, and attachment-to-filestore presence without calling `sudo`, `create`, `write`, or `unlink`.

On 2026-07-15 the source was a no-demo production-shaped sample, not an authorized historical or production backup. The check passed structurally: one company, 68 users, 103 partners, two currencies, two attachments, zero projects/contracts/settlements/payment requests/executions/ledgers, no blocker findings, and `smart_construction_demo` uninstalled. The machine evidence is `artifacts/release/frontend-pilot-readiness/data-compatibility.json`.

This is not historical compatibility proof. Before pilot activation, Delivery owner and DBA must obtain an authorized sanitized history copy, identify it as `sanitized_history_copy`, run the same command, and resolve every blocker. Reports may contain only model/reference keys and aggregate counts; names, phone numbers, identity documents, bank data, contract text, secrets and request payloads must not be committed.
