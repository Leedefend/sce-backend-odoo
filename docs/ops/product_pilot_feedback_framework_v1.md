# Product Pilot Feedback Framework v1

## Purpose
- Standardize how pilot feedback is collected, classified, and turned into decisions.

## Feedback Sources
- runtime verify artifacts
- operator walkthrough notes
- blocked-action screenshots or recordings
- product docs mismatch observations
- environment instability notes

## Required Feedback Dimensions
- scenario
  - what flow the user was executing
- actor
  - which product role was acting
- expected result
  - what the user thought should happen
- actual result
  - what the system returned
- impact
  - whether the issue blocked use, caused confusion, or reduced efficiency
- proposed decision
  - fix now, defer, or reject

## Classification Model
- `blocking`
  - user cannot complete the target flow
- `understanding`
  - user can continue, but does not understand what the product is asking or saying
- `experience`
  - user can continue and understands the flow, but the experience is noisy or inefficient
- `environment`
  - issue comes from startup, data, or runtime trust rather than product behavior

## Decision Policy
- Fix now:
  - blocking issues
  - high-priority understanding issues
- Defer:
  - low-priority understanding issues
  - experience improvements that do not affect trial success
- Reject:
  - requests that expand scope beyond the current semantic phase without sufficient evidence

## Review Mechanism
- One feedback document per pilot batch
- One freeze decision per semantic phase
- One explicit next-batch recommendation
- No issue should move into implementation without:
  - category
  - evidence
  - scope decision

## Minimal Template
- title
- phase
- flow
- actor
- category
- severity
- evidence
- decision
- owner
- target_phase

## Governance Rule
- Feedback does not automatically mean implementation.
- Expansion requires:
  - repeated evidence or clear strategic value
  - fit with the active product boundary
  - explicit phase approval
