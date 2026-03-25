#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$ROOT_DIR/scripts/_lib/common.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME required}"

compose ${COMPOSE_FILES} exec -T odoo sh -lc "odoo shell -d '${DB_NAME}' -c '${ODOO_CONF}'" <<'PY'
import json
from pathlib import Path

from odoo.addons.smart_core.delivery.release_operator_contract_registry import (
    build_release_operator_contract_registry,
)
from odoo.addons.smart_core.delivery.release_operator_contract_versions import (
    RELEASE_OPERATOR_CONTRACT_REGISTRY_VERSION,
    RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION,
    RELEASE_OPERATOR_SURFACE_CONTRACT_VERSION,
    RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
)
from odoo.addons.smart_core.delivery.release_operator_read_model_service import (
    ReleaseOperatorReadModelService,
)
from odoo.addons.smart_core.delivery.release_operator_surface_service import (
    ReleaseOperatorSurfaceService,
)
from odoo.addons.smart_core.delivery.release_operator_write_model_service import (
    ReleaseOperatorWriteModelService,
)

OUT_JSON = Path("/mnt/artifacts/backend/release_operator_contract_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_operator_contract_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "registry": {}, "surface": {}, "read_model": {}, "write_model": {}}
try:
    registry = build_release_operator_contract_registry()
    if str(registry.get("contract_version") or "").strip() != RELEASE_OPERATOR_CONTRACT_REGISTRY_VERSION:
        raise RuntimeError("registry contract drift")
    contracts = registry.get("contracts") if isinstance(registry.get("contracts"), dict) else {}
    if str((contracts.get("surface") or {}).get("contract_version") or "").strip() != RELEASE_OPERATOR_SURFACE_CONTRACT_VERSION:
        raise RuntimeError("surface registry version drift")
    if str((contracts.get("read_model") or {}).get("contract_version") or "").strip() != RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION:
        raise RuntimeError("read model registry version drift")
    if str((contracts.get("write_model") or {}).get("contract_version") or "").strip() != RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION:
        raise RuntimeError("write model registry version drift")

    surface = ReleaseOperatorSurfaceService(env).build_surface(product_key="construction.standard")
    read_model = ReleaseOperatorReadModelService(env).build_read_model(product_key="construction.standard")
    write_model = ReleaseOperatorWriteModelService(env).build_from_intent(
        intent="release.operator.rollback",
        params={"product_key": "construction.standard", "target_snapshot_id": 0, "note": "contract guard"},
    )

    for label, payload, version in (
        ("surface", surface, RELEASE_OPERATOR_SURFACE_CONTRACT_VERSION),
        ("read_model", read_model, RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION),
        ("write_model", write_model, RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION),
    ):
        if str(payload.get("contract_version") or "").strip() != version:
            raise RuntimeError(f"{label}: contract version drift")
        payload_registry = payload.get("contract_registry") if isinstance(payload.get("contract_registry"), dict) else {}
        if str(payload_registry.get("contract_version") or "").strip() != RELEASE_OPERATOR_CONTRACT_REGISTRY_VERSION:
            raise RuntimeError(f"{label}: registry missing")

    report["registry"] = {
        "contract_version": registry.get("contract_version"),
        "keys": sorted(list(contracts.keys())),
    }
    report["surface"] = {"contract_version": surface.get("contract_version")}
    report["read_model"] = {"contract_version": read_model.get("contract_version")}
    report["write_model"] = {
        "contract_version": write_model.get("contract_version"),
        "operation": write_model.get("operation"),
    }
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Operator Contract Guard\n\n"
        "- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_operator_contract_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Operator Contract Guard\n\n"
    "- status: `PASS`\n"
    f"- registry version: `{report['registry'].get('contract_version')}`\n"
    f"- write model version: `{report['write_model'].get('contract_version')}`\n",
)
print("[release_operator_contract_guard] PASS")
PY
