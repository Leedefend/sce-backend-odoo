# Repository Online-Credential Incident Record (2026-07-15)

Two migration documents contained six repeated non-placeholder assignments. The truncated SHA256 fingerprints are `ec2b5afa5f5f` for the username and `05278d964396` / `2efb1047074f` for the passwords. Values are intentionally omitted. The current tree now uses `<provided-via-secret-environment>` placeholders.

Credentials and sessions have not been revoked. The user explicitly decided to keep the legacy system available as a read-only historical-data source until decommissioning. No external access-log investigation result or organization-specific security-owner identifier was supplied to the repository.

Read-only history inspection found four related reachable commits: first seen at `e8cbc880f692d504f2849f75d099aeabd0fb7220`, with the last related change at `73cb51a37c17223e1b47120c2f284f0ae15b07ca`. Three branch refs contain the latter and no tag does. The scan emitted only commit/path/rule metadata and redacted fingerprints.

Git history is not rewritten in this change because GitHub/Gitee remotes, PR references, release SHAs, CI baselines, clones, forks, and caches cannot be safely or completely rewritten by this patch. This does not erase or invalidate historical values. The account and sessions must be disabled when the legacy system is decommissioned.

Preventive controls now scan Markdown credential assignments, online literal defaults, cross-system fallbacks, credential-bearing URLs, and existing high-confidence secret shapes. Online capture, replay, probes, browser comparison, and legacy attachment reads default to offline and require dedicated runtime secrets, explicit confirmation, and a destination allowlist before any request. Online attachment mirror writes also default to disabled.

Residual risk remains: reachable history and existing clones may retain values that can remain valid before legacy-system shutdown. The user explicitly accepts this risk; therefore this record does not claim credential revocation.

Chinese: [repository_credential_incident_20260715.md](repository_credential_incident_20260715.md)
