#!/usr/bin/env bash
set -euo pipefail
source scripts/common/env.sh

# install gate: at_install + your custom tags
TEST_TAGS="at_install,sc_install,sc_gate"
# reuse Makefile computation style not needed here; just compute robustly:
TEST_TAGS_FINAL="$(echo "$TEST_TAGS" | tr ',' '\n' | sed "s#^#/${MODULE}:#" | paste -sd, -)"

export TEST_TAGS TEST_TAGS_FINAL
bash scripts/ci/run_ci.sh
