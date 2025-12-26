#!/usr/bin/env bash
set -euo pipefail
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
