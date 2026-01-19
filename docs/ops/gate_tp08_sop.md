# TP08 Gate SOP (Infra)

Goal: make `make ci.gate.tp08 DB=sc_demo` run reliably to the audit phase.

## Pre-check (Docker permission)
1) Check Docker access
```
docker info >/dev/null && echo "OK docker" || echo "FAIL docker"
```
- If FAIL: run with sudo or add user to docker group, then re-login.

2) Check compose project
```
make ps
```
- Expected: services listed for dev project (odoo/db/redis).

## Fix #1: Docker permission denied
Option A (one-off):
```
sudo -n true
sudo make ci.gate.tp08 DB=sc_demo
```
Option B (persistent):
```
sudo usermod -aG docker $USER
# re-login required
```

## Fix #2: service "odoo" is not running
1) Bring up services
```
make up
```
2) Force odoo recreate if needed
```
make odoo.recreate
```
3) Validate status
```
make ps
```
- Expected: odoo/db/redis running and healthy.

## Run gate
```
make ci.gate.tp08 DB=sc_demo
```

## PASS criteria
- `make audit.project.actions DB=sc_demo` completes
- `python3 scripts/ci/assert_audit_tp08.py` completes
- Exit code 0

## FAIL triage
- If permission denied: rerun with sudo or fix docker group
- If odoo not running: rerun `make up` + `make odoo.recreate`
- If audit assertion fails: inspect `docs/audit/*` and `artifacts/logs/*_tp08_gate.log`
