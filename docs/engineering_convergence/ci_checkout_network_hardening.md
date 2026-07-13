# CI Checkout Network Hardening

## Incident

PR `#1037` had two failed `v1.1 quality gate` attempts before a successful rerun.
Both failed before repository checkout completed on the self-hosted runner
`ci-1-95-2-123`.

Observed errors:

- `Failure when receiving data from the peer`
- `Failed to connect to github.com port 443`

The `Run unified PR quality gate` step did not execute on the failed attempts.
The third rerun fetched the same commit and passed, so the failure was runner to
GitHub network instability rather than a repository content failure.

## Mitigation

The quality gate now runs `scripts/ci/checkout_from_ci_mirror.sh` for checkout.
The script keeps the local mirror strategy and adds:

- cache repository initialization and origin repair;
- Git HTTP/1.1 transport to avoid HTTP/2 peer reset sensitivity;
- Git low-speed timeout settings;
- repeated branch and commit fetch attempts with backoff;
- network diagnostics for DNS, GitHub HTTP reachability, and `ls-remote` when
  fetch attempts fail.

If checkout still fails after all attempts, the job fails with enough context to
distinguish runner network failures from code quality failures.
