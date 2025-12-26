#!/usr/bin/env bash
set -euo pipefail
source scripts/common/compose.sh
compose_dev down
compose_dev up -d
