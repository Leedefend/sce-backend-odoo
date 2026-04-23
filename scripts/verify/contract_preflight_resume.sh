#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STATE_FILE="${ROOT}/artifacts/backend/contract_preflight_resume.state"

mkdir -p "$(dirname "${STATE_FILE}")"

resume_from="${CONTRACT_PREFLIGHT_RESUME_FROM:-}"
if [[ -z "${resume_from}" && -s "${STATE_FILE}" ]]; then
  resume_from="$(cat "${STATE_FILE}")"
fi

run_target() {
  local target="$1"
  case "${target}" in
    verify.contract.view_type_semantic.strict.smoke)
      if [[ "${CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES:-0}" != "1" ]]; then
        echo "[verify.contract.preflight.resume] CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0: skip strict view-type semantic smoke"
        return 0
      fi
      ;;
    audit.intent.surface)
      make --no-print-directory audit.intent.surface \
        INTENT_SURFACE_MD="${CONTRACT_PREFLIGHT_INTENT_SURFACE_MD:-artifacts/intent_surface_report.md}" \
        INTENT_SURFACE_JSON="${CONTRACT_PREFLIGHT_INTENT_SURFACE_JSON:-artifacts/intent_surface_report.json}"
      return $?
      ;;
  esac
  make --no-print-directory "${target}"
}

if [[ "${BASELINE_FREEZE_ENFORCE:-1}" == "1" ]]; then
  make --no-print-directory verify.baseline.freeze_guard
else
  echo "[verify.contract.preflight.resume] BASELINE_FREEZE_ENFORCE=0: skip baseline freeze guard"
fi

targets=(
  verify.test_seed_dependency.guard
  verify.contract_drift.guard
  verify.scene.contract_path.gate
  verify.contract.governance.coverage
  verify.docs.all
  verify.grouped.governance.bundle
  audit.intent.surface
  verify.scene_capability.contract.guard
  verify.contract.governance.brief
  verify.contract.scene_coverage.guard
  verify.contract.mode.smoke
  verify.project.form.contract.surface.guard
  verify.relation.access_policy.consistency.audit
  verify.system_group.business_acl.guard
  verify.native_surface_integrity_guard
  verify.governed_surface_policy_guard
  verify.contract.surface_mapping_guard
  verify.contract.parse_boundary.guard
  verify.contract.production_chain.guard
  verify.contract.ordering.smoke
  verify.scene.hud.trace.smoke
  verify.scene.meta.trace.smoke
  verify.contract.api.mode.smoke
  verify.contract.view_type_semantic.smoke
  verify.frontend.search_groupby_savedfilters.guard
  verify.frontend.x2many_command_semantic.guard
  verify.frontend.view_type_render_coverage.guard
  verify.native_view.semantic_page
  verify.contract.view_type_semantic.strict.smoke
  verify.scene.contract.shape
  contract.evidence.export
)

started=0
found=0
for target in "${targets[@]}"; do
  if [[ -z "${resume_from}" ]]; then
    started=1
  elif [[ "${started}" -eq 0 ]]; then
    if [[ "${target}" == "${resume_from}" ]]; then
      started=1
      found=1
      echo "[verify.contract.preflight.resume] resume from: ${target}"
    else
      continue
    fi
  fi

  if run_target "${target}"; then
    :
  else
    echo "${target}" > "${STATE_FILE}"
    echo "[verify.contract.preflight.resume] failed target recorded: ${target}"
    exit 2
  fi
done

if [[ -n "${resume_from}" && "${found}" -eq 0 ]]; then
  echo "[verify.contract.preflight.resume] invalid resume target: ${resume_from}"
  exit 2
fi

rm -f "${STATE_FILE}"
echo "[verify.contract.preflight.resume] PASS"
