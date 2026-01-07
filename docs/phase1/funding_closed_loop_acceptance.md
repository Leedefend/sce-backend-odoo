# Funding Closed-Loop Acceptance (Phase 1)

## UI Path (Happy Path)

1) Project
   - Create or open a project.
   - Ensure `funding_enabled = True` and project has a code.

2) Funding Baseline
   - Create a funding baseline in `draft`.
   - Activate it (state = `active`).

3) Payment Request
   - Create a payment request for the project (amount > 0).
   - Submit the request (state = `submit`).

4) Approve
   - Use tier validation to approve the request.
   - State becomes `approved`.

5) Ledger
   - Add payment ledger lines for the approved request.

6) Done
   - When paid total reaches request amount, set request to `done`.

## Expected Pass/Fail Points

- Overpay blocked:
  - Adding a ledger line that makes paid total exceed request amount must fail.

- Not approved blocked:
  - Creating/updating/deleting ledger lines is blocked unless request state is `approved`.

- Not fully paid blocked:
  - Setting request to `done` fails unless paid total equals or exceeds request amount
    (currency rounding respected).
