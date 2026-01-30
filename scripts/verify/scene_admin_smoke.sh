#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"

python3 "$ROOT_DIR/scripts/verify/scene_admin_smoke.py"
