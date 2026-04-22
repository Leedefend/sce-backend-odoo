# Project Intake Scene-Layer Screen V1

## Problem

We already recovered one boundary mistake:

- project intake create-flow semantics must not live inside
  `addons/smart_core/utils/contract_governance.py`

But the semantics still need a legal owner.

The remaining question is:

- where should project intake form contract semantics be supplied after the
  input chain is available?

## Current Fact

### Platform core

`smart_core` currently owns:

- generic contract governance
- generic input-chain transport
- generic menu/action/model contract dispatch

This is the wrong place for project intake scene semantics.

### Industry layer

`smart_construction_core/services/contract_governance_overrides.py` currently
registers:

- `smart_construction_core.project_form`
  - mapped to `apply_project_form_domain_override`

But this still points back to the shared project form override logic in
`smart_core`, not to a scene-specific intake semantic supply point.

## Candidate Ownership Points

### Option A: industry-specific contract override in `smart_construction_core`

Meaning:

- add a dedicated project intake override in `smart_construction_core`
- the override runs only when the current form surface belongs to intake entry

Pros:

- keeps industry scene semantics in industry module
- fits the existing domain-override mechanism

Cons:

- still needs a clean way to detect intake entry from input-chain context

### Option B: scene entry handler supplies form semantics

Meaning:

- project intake semantics are emitted near `project.initiation` scene entry /
  entry target resolution
- form page then consumes a scene-ready envelope rather than generic model
  governance

Pros:

- strongest scene ownership
- cleanest semantic story

Cons:

- may require more movement in how the form contract is loaded/opened

### Option C: post-assembly scene semantic patch in industry layer

Meaning:

- keep generic contract assembly as is
- after assembly, industry scene layer patches intake-specific form_governance

Pros:

- bounded change
- preserves mainline contract pipeline

Cons:

- can become a hidden second governance layer if not named clearly

## Ownership Decision

Recommended owner:

- `smart_construction_core` industry/scene layer

Recommended mechanism:

- `Option A` first

Reason:

- project intake is an industry scenario, not a platform primitive
- the repository already has an industry-side governance override registration
  pattern
- extending that pattern with a dedicated intake override is the smallest change
  that still respects the layer boundary

## Recommended Next Batch

1. add a dedicated project intake contract override in
   `smart_construction_core`
2. make it activate only when input-chain identity proves the current create
   form belongs to intake entry
3. emit intake-specific form semantics there
4. let frontend consume those semantics and delete the remaining
   route-based standard intake inference

## Stop Boundary

Do not reintroduce project intake scene semantics into `smart_core`
contract governance.
