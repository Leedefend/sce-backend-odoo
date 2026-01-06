#!/usr/bin/env bash
set -euo pipefail

make audit.project.actions DB=sc_demo
python3 scripts/ci/assert_audit_tp08.py
