# Lifecycle States (Project)

This document defines the official semantics for `project.lifecycle_state`.
It is the baseline for the lifecycle × capability matrix in Phase N1.

- draft (Draft)
  - Description: project initiation and preparation.
  - Stage type: management
  - New business objects: allowed (basic project data, BOQ, contracts)
- in_progress (In Progress)
  - Description: active execution and delivery.
  - Stage type: execution
  - New business objects: allowed
- paused (Paused)
  - Description: temporarily halted; no new execution work.
  - Stage type: management
  - New business objects: not allowed
- done (Completed)
  - Description: execution completed, ready to settle.
  - Stage type: management
  - New business objects: limited (settlement/payment only)
- closing (Closing)
  - Description: settlement in progress.
  - Stage type: management
  - New business objects: limited (settlement/payment only)
- warranty (Warranty)
  - Description: warranty/defects liability period.
  - Stage type: management
  - New business objects: not allowed
- closed (Closed)
  - Description: final close; no changes allowed.
  - Stage type: management
  - New business objects: not allowed
