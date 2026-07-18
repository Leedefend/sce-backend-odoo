#!/usr/bin/env bash
set -euo pipefail

scope="${1:?scope is required: source|candidate}"
phase="${2:?phase is required}"
root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"
artifacts="${CANDIDATE_ARTIFACTS:-artifacts/release/immutable-production-candidate-v1}"
mkdir -p "$artifacts/fingerprints"

if [[ "$scope" == "source" ]]; then
  export FINGERPRINT_PROJECT="${DAILY_DEV_PROJECT:-sc-backend-odoo-dev}"
  export FINGERPRINT_COMPOSE_FILE="docker-compose.yml"
  export FINGERPRINT_DB="${HISTORY_SOURCE_DB:-sc_user_data_rehearsal}"
  export FINGERPRINT_FILESTORE_MODE=exec
else
  export FINGERPRINT_PROJECT="${CANDIDATE_PROJECT:-sc-production-candidate}"
  export FINGERPRINT_COMPOSE_FILE="docker-compose.production-candidate.yml"
  export FINGERPRINT_DB="${CANDIDATE_DB:-sc_user_data_rehearsal_candidate}"
  export FINGERPRINT_FILESTORE_MODE=run
  export CANDIDATE_IMAGE="${CANDIDATE_IMAGE:?CANDIDATE_IMAGE is required}"
  export CANDIDATE_DB="$FINGERPRINT_DB" CANDIDATE_PROJECT="$FINGERPRINT_PROJECT"
fi
export FINGERPRINT_OUTPUT="$artifacts/fingerprints/$phase.json"
python3 scripts/release/production_candidate_sql_fingerprint.py
