#!/usr/bin/env python3
"""Guard the default-off Lite rollout switch semantics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

RUNTIME_PATH = ROOT / "frontend/apps/web/src/app/runtime/unifiedPageContractLitePilot.ts"
ENV_PATH = ROOT / "frontend/apps/web/src/env.d.ts"
DOC_PATH = ROOT / "docs/architecture/unified_page_contract_lite/rollout_switch_batch_48.md"
ALL_TREE_DOC_PATH = ROOT / "docs/architecture/unified_page_contract_lite/all_tree_browser_smoke_batch_49.md"
ALL_TREE_LEGACY_DOC_PATH = ROOT / "docs/architecture/unified_page_contract_lite/all_tree_legacy_fallback_batch_50.md"
ALL_TREE_MATRIX_DOC_PATH = ROOT / "docs/architecture/unified_page_contract_lite/all_tree_matrix_browser_smoke_batch_51.md"
ALL_TREE_ACCEPTANCE_DOC_PATH = ROOT / "docs/architecture/unified_page_contract_lite/all_tree_acceptance_gate_batch_52.md"
ALL_TREE_SMOKE_PATH = ROOT / "scripts/verify/unified_page_contract_lite_all_tree_browser_smoke.js"
ALL_TREE_LEGACY_SMOKE_PATH = ROOT / "scripts/verify/unified_page_contract_lite_all_tree_legacy_browser_smoke.js"
ALL_TREE_MATRIX_SMOKE_PATH = ROOT / "scripts/verify/unified_page_contract_lite_all_tree_matrix_browser_smoke.js"
MAKEFILE_PATH = ROOT / "Makefile"
RUNTIME_PILOT_PATH = ROOT / "frontend/apps/web/src/app/runtime/unifiedPageContractLitePilot.ts"
ACTION_RESOLVER_PATH = ROOT / "frontend/apps/web/src/app/resolvers/actionResolver.ts"

RUNTIME_REQUIRED = (
    "LITE_CONTRACT_ROLLOUT_ENV = 'VITE_LITE_CONTRACT_ROLLOUT'",
    "type LiteContractRolloutMode = 'off' | 'pilot' | 'all_tree';",
    "export function liteContractRolloutMode(): LiteContractRolloutMode",
    "if (rollout === 'all_tree') return 'all_tree';",
    "if (rollout === 'pilot') return 'pilot';",
    "VITE_LITE_CONTRACT_PILOT",
    "? 'pilot' : 'off'",
    "if (rollout === 'off') return false;",
    "if (rollout === 'all_tree') return true;",
    "return model === LITE_CONTRACT_PILOT_MODEL;",
)

ENV_REQUIRED = (
    "readonly VITE_LITE_CONTRACT_PILOT?: string;",
    "readonly VITE_LITE_CONTRACT_ROLLOUT?: string;",
)

DOC_REQUIRED = (
    "Status: implemented default-off",
    "VITE_LITE_CONTRACT_ROLLOUT=pilot",
    "VITE_LITE_CONTRACT_ROLLOUT=all_tree",
    "legacy `ui.contract` remains the default path",
    "does not change `login`",
    "does not change `system.init`",
    "does not make Lite the default",
)

ALL_TREE_DOC_REQUIRED = (
    "Status: implemented validation smoke",
    "VITE_LITE_CONTRACT_ROLLOUT=all_tree",
    "verify.unified_page_contract.lite.all_tree_browser.host",
    "LITE_ALL_TREE_ACTION_IDS",
    "load_contract Lite preview",
    "no repeated action-phase `ui.contract` fallback",
    "does not make Lite the default",
)

ALL_TREE_LEGACY_DOC_REQUIRED = (
    "Status: implemented guarded fallback",
    "LITE_ALL_TREE_LEGACY_ACTION_ID=642",
    "action-phase `ui.contract` is used",
    "action-phase `load_contract` is not called",
    "does not make Lite the default",
)

ALL_TREE_MATRIX_DOC_REQUIRED = (
    "Status: implemented matrix smoke",
    "verify.unified_page_contract.lite.all_tree_matrix_browser.host",
    "classifies `tree`/`list` as Lite expected",
    "classifies non-tree views as legacy expected",
    "LITE_ALL_TREE_MATRIX_LIMIT=8",
    "does not make Lite the default",
)

ALL_TREE_ACCEPTANCE_DOC_REQUIRED = (
    "Status: implemented acceptance gate",
    "verify.unified_page_contract.lite.all_tree_acceptance_browser.host",
    "verify.unified_page_contract.lite.all_tree_browser.host",
    "verify.unified_page_contract.lite.all_tree_legacy_browser.host",
    "verify.unified_page_contract.lite.all_tree_matrix_browser.host",
    "This is a review gate, not a default runtime switch.",
    "does not make Lite the default",
)

ALL_TREE_SMOKE_REQUIRED = (
    "VITE_LITE_CONTRACT_ROLLOUT=all_tree",
    "LITE_ALL_TREE_ACTION_IDS",
    "load_contract",
    "lite_preview",
    "payloadType === 'lite_contract'",
    "ui.contract",
    "lite_all_tree_rollout",
    "repeatedly called ui.contract",
)

ALL_TREE_LEGACY_SMOKE_REQUIRED = (
    "VITE_LITE_CONTRACT_ROLLOUT=all_tree",
    "LITE_ALL_TREE_LEGACY_ACTION_ID",
    "load_contract",
    "ui.contract",
    "lite_all_tree_legacy_rollout",
    "non-tree action dispatched load_contract",
)

ALL_TREE_MATRIX_SMOKE_REQUIRED = (
    "VITE_LITE_CONTRACT_ROLLOUT=all_tree",
    "LITE_ALL_TREE_MATRIX_LIMIT",
    "discoverMatrix",
    "system.init",
    "ui.contract",
    "load_contract",
    "lite_all_tree_matrix_rollout",
    "matrix discovery found no tree/list action",
    "matrix discovery found no non-tree action",
)

FRONTEND_FALLBACK_REQUIRED = (
    "needsLiteContractAllTreeViewPreflight",
    "legacyContract = await loadActionContract(actionId)",
    "candidateMeta = mergeMeta(seedMeta, resolveMetaFromContract(legacyContract, actionId))",
)

MAKEFILE_REQUIRED = (
    "verify.unified_page_contract.lite.all_tree_browser.host",
    "verify.unified_page_contract.lite.all_tree_legacy_browser.host",
    "verify.unified_page_contract.lite.all_tree_matrix_browser.host",
    "verify.unified_page_contract.lite.all_tree_acceptance_browser.host",
    "unified_page_contract_lite_all_tree_browser_smoke.js",
    "unified_page_contract_lite_all_tree_legacy_browser_smoke.js",
    "unified_page_contract_lite_all_tree_matrix_browser_smoke.js",
    "LITE_ALL_TREE_ACTION_IDS",
    "LITE_ALL_TREE_LEGACY_ACTION_ID",
    "LITE_ALL_TREE_MATRIX_LIMIT",
)

FORBIDDEN = (
    "VITE_LITE_CONTRACT_ROLLOUT=all_tree by default",
    "VITE_LITE_CONTRACT_PILOT=1 by default",
    "Lite is now the default",
    "removes legacy fallback",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def missing_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token not in text]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    for path in (
        RUNTIME_PATH,
        ENV_PATH,
        DOC_PATH,
        ALL_TREE_DOC_PATH,
        ALL_TREE_LEGACY_DOC_PATH,
        ALL_TREE_MATRIX_DOC_PATH,
        ALL_TREE_ACCEPTANCE_DOC_PATH,
        ALL_TREE_SMOKE_PATH,
        ALL_TREE_LEGACY_SMOKE_PATH,
        ALL_TREE_MATRIX_SMOKE_PATH,
        MAKEFILE_PATH,
        RUNTIME_PILOT_PATH,
        ACTION_RESOLVER_PATH,
    ):
        if not path.exists():
            errors.append(f"missing file: {path.relative_to(ROOT)}")

    runtime = read_text(RUNTIME_PATH) if RUNTIME_PATH.exists() else ""
    env = read_text(ENV_PATH) if ENV_PATH.exists() else ""
    doc = read_text(DOC_PATH) if DOC_PATH.exists() else ""
    all_tree_doc = read_text(ALL_TREE_DOC_PATH) if ALL_TREE_DOC_PATH.exists() else ""
    all_tree_legacy_doc = read_text(ALL_TREE_LEGACY_DOC_PATH) if ALL_TREE_LEGACY_DOC_PATH.exists() else ""
    all_tree_matrix_doc = read_text(ALL_TREE_MATRIX_DOC_PATH) if ALL_TREE_MATRIX_DOC_PATH.exists() else ""
    all_tree_acceptance_doc = read_text(ALL_TREE_ACCEPTANCE_DOC_PATH) if ALL_TREE_ACCEPTANCE_DOC_PATH.exists() else ""
    all_tree_smoke = read_text(ALL_TREE_SMOKE_PATH) if ALL_TREE_SMOKE_PATH.exists() else ""
    all_tree_legacy_smoke = read_text(ALL_TREE_LEGACY_SMOKE_PATH) if ALL_TREE_LEGACY_SMOKE_PATH.exists() else ""
    all_tree_matrix_smoke = read_text(ALL_TREE_MATRIX_SMOKE_PATH) if ALL_TREE_MATRIX_SMOKE_PATH.exists() else ""
    makefile = read_text(MAKEFILE_PATH) if MAKEFILE_PATH.exists() else ""
    runtime_pilot = read_text(RUNTIME_PILOT_PATH) if RUNTIME_PILOT_PATH.exists() else ""
    action_resolver = read_text(ACTION_RESOLVER_PATH) if ACTION_RESOLVER_PATH.exists() else ""

    for label, text, tokens in (
        ("runtime", runtime, RUNTIME_REQUIRED),
        ("env", env, ENV_REQUIRED),
        ("doc", doc, DOC_REQUIRED),
        ("all_tree_doc", all_tree_doc, ALL_TREE_DOC_REQUIRED),
        ("all_tree_legacy_doc", all_tree_legacy_doc, ALL_TREE_LEGACY_DOC_REQUIRED),
        ("all_tree_matrix_doc", all_tree_matrix_doc, ALL_TREE_MATRIX_DOC_REQUIRED),
        ("all_tree_acceptance_doc", all_tree_acceptance_doc, ALL_TREE_ACCEPTANCE_DOC_REQUIRED),
        ("all_tree_smoke", all_tree_smoke, ALL_TREE_SMOKE_REQUIRED),
        ("all_tree_legacy_smoke", all_tree_legacy_smoke, ALL_TREE_LEGACY_SMOKE_REQUIRED),
        ("all_tree_matrix_smoke", all_tree_matrix_smoke, ALL_TREE_MATRIX_SMOKE_REQUIRED),
        ("makefile", makefile, MAKEFILE_REQUIRED),
        ("runtime_pilot", runtime_pilot, FRONTEND_FALLBACK_REQUIRED[:1]),
        ("action_resolver", action_resolver, FRONTEND_FALLBACK_REQUIRED[1:]),
    ):
        missing = missing_tokens(text, tokens)
        if missing:
            errors.append(f"{label} missing tokens: {missing}")

    forbidden = sorted({
        token
        for token in FORBIDDEN
        if token in runtime
        or token in env
        or token in doc
        or token in all_tree_doc
        or token in all_tree_legacy_doc
        or token in all_tree_matrix_doc
        or token in all_tree_acceptance_doc
        or token in all_tree_smoke
        or token in all_tree_legacy_smoke
        or token in all_tree_matrix_smoke
    })
    if forbidden:
        errors.append(f"forbidden rollout tokens found: {forbidden}")

    report = {
        "ok": not errors,
        "decision": "lite_rollout_switch_default_off" if not errors else "blocked",
        "default_mode": "off",
        "rollout_modes": ["off", "pilot", "all_tree"],
        "legacy_flag": "VITE_LITE_CONTRACT_PILOT=1 maps to pilot",
        "all_tree_browser_smoke": "verify.unified_page_contract.lite.all_tree_browser.host",
        "all_tree_legacy_browser_smoke": "verify.unified_page_contract.lite.all_tree_legacy_browser.host",
        "all_tree_matrix_browser_smoke": "verify.unified_page_contract.lite.all_tree_matrix_browser.host",
        "all_tree_acceptance_browser_smoke": "verify.unified_page_contract.lite.all_tree_acceptance_browser.host",
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite rollout switch guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite rollout switch guard passed")
    print("- decision: lite_rollout_switch_default_off")
    print("- modes: off, pilot, all_tree")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
