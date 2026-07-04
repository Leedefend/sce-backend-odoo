#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
STRICT_JSON_NAME = "scbs_release_acceptance_strict_result_v1.json"
STRICT_MD_NAME = "scbs_release_acceptance_strict_v1.md"
REPLAY_JSON_NAME = "scbs_no_legacy_replay_acceptance_result_v1.json"
REQUIRED_STRICT_CHECKS = {
    "payment_closed",
    "contract_closed",
    "stock_policy_closed",
    "fund_daily_closed",
    "payment_source_unique",
    "contract_source_unique",
    "stock_source_unique",
    "fund_daily_source_unique",
}
REQUIRED_REPLAY_CHECKS = {
    "staging_total",
    "staging_family_payment",
    "staging_family_stock_in",
    "staging_family_supplier_contract",
    "staging_family_fund_daily",
    "formal_payment_execution",
    "formal_supplier_contract",
    "formal_stock_in",
    "formal_fund_daily",
}


def _artifact_dir() -> Path | None:
    raw = os.getenv("PROD_SIM_ACCEPTANCE_ARTIFACT_DIR", "").strip()
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _check_bool_checks(prefix: str, checks: object, required: set[str], errors: list[str]) -> dict:
    if not isinstance(checks, dict):
        errors.append(f"{prefix}.checks must be object")
        return {}
    missing = sorted(required - set(checks))
    if missing:
        errors.append(f"{prefix}.checks missing required keys: {', '.join(missing)}")
    for key, value in checks.items():
        if not isinstance(key, str) or not key:
            errors.append(f"{prefix}.checks keys must be non-empty strings")
        if not isinstance(value, bool):
            errors.append(f"{prefix}.checks.{key} must be bool")
    return checks


def _check_count_amount(prefix: str, value: object, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix} must be object")
        return
    if "rows" in value and (not isinstance(value.get("rows"), int) or value.get("rows") < 0):
        errors.append(f"{prefix}.rows must be non-negative int")
    if "amount" in value and not isinstance(value.get("amount"), (int, float)):
        errors.append(f"{prefix}.amount must be number")


def _check_strict(path: Path, md_path: Path, errors: list[str]) -> None:
    payload = _load_json(path)
    if not payload:
        errors.append(f"missing or invalid json: {path.relative_to(ROOT).as_posix()}")
        return
    if payload.get("status") not in {"PASS", "REVIEW_REQUIRED"}:
        errors.append("strict.status must be PASS or REVIEW_REQUIRED")
    if payload.get("database") != "sc_prod_sim":
        errors.append("strict.database must be sc_prod_sim")
    if payload.get("mode") != "strict":
        errors.append("strict.mode must be strict")
    failed = payload.get("failed_checks")
    if not isinstance(failed, list) or not all(isinstance(item, str) for item in failed):
        errors.append("strict.failed_checks must be string list")
        failed = []
    checks = _check_bool_checks("strict", payload.get("checks"), REQUIRED_STRICT_CHECKS, errors)
    expected_failed = sorted(key for key, value in checks.items() if value is not True)
    if sorted(failed) != expected_failed:
        errors.append("strict.failed_checks must match failed check keys")
    if payload.get("status") == "PASS" and failed:
        errors.append("strict.status=PASS must not contain failed checks")
    observations = payload.get("observations")
    if not isinstance(observations, dict):
        errors.append("strict.observations must be object")
    else:
        if observations.get("mode") != "strict":
            errors.append("strict.observations.mode must be strict")
        formal = observations.get("formal")
        if not isinstance(formal, dict):
            errors.append("strict.observations.formal must be object")
        else:
            for key in ("payment_execution", "contract", "stock_in", "fund_daily"):
                _check_count_amount(f"strict.observations.formal.{key}", formal.get(key), errors)
    if not md_path.is_file():
        errors.append(f"missing markdown report: {md_path.relative_to(ROOT).as_posix()}")
    else:
        text = md_path.read_text(encoding="utf-8")
        for token in ("# SCBS Release Acceptance", "Status:", "- database: `sc_prod_sim`", "- mode: `strict`", "## Checks"):
            if token not in text:
                errors.append(f"strict markdown missing token: {token}")


def _check_replay(path: Path, errors: list[str]) -> None:
    payload = _load_json(path)
    if not payload:
        errors.append(f"missing or invalid json: {path.relative_to(ROOT).as_posix()}")
        return
    if payload.get("status") != "PASS":
        errors.append("replay.status must be PASS")
    if payload.get("database") != "sc_prod_sim":
        errors.append("replay.database must be sc_prod_sim")
    _check_bool_checks("replay", payload.get("checks"), REQUIRED_REPLAY_CHECKS, errors)
    for section in ("expected", "actual"):
        value = payload.get(section)
        if not isinstance(value, dict):
            errors.append(f"replay.{section} must be object")
            continue
        for subsection in ("staging", "formal"):
            if not isinstance(value.get(subsection), dict):
                errors.append(f"replay.{section}.{subsection} must be object")
    baseline = payload.get("baseline")
    if not isinstance(baseline, str) or not baseline:
        errors.append("replay.baseline must be non-empty string")


def main() -> int:
    errors: list[str] = []
    artifact_dir = _artifact_dir()
    if artifact_dir is None:
        errors.append("PROD_SIM_ACCEPTANCE_ARTIFACT_DIR is required")
    elif not artifact_dir.is_dir():
        errors.append(f"artifact directory does not exist: {artifact_dir}")
    else:
        try:
            artifact_dir.relative_to(ROOT)
        except ValueError:
            errors.append("PROD_SIM_ACCEPTANCE_ARTIFACT_DIR must be inside the repository workspace")
        _check_strict(artifact_dir / STRICT_JSON_NAME, artifact_dir / STRICT_MD_NAME, errors)
        _check_replay(artifact_dir / REPLAY_JSON_NAME, errors)

    if errors:
        print("[prod_sim_acceptance_evidence_schema_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[prod_sim_acceptance_evidence_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
