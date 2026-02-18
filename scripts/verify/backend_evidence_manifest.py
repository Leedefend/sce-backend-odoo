#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "backend_evidence_manifest_guard.json"


def _resolve_artifacts_dir() -> Path:
    candidates = [
        str(os.getenv("ARTIFACTS_DIR") or "").strip(),
        "/mnt/artifacts",
        str(ROOT / "artifacts"),
    ]
    for raw in candidates:
        if not raw:
            continue
        path = Path(raw)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".probe_write"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return path
        except Exception:
            continue
    raise RuntimeError("no writable artifacts dir available")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    required = [
        str(item).strip()
        for item in (baseline.get("required_artifacts") if isinstance(baseline.get("required_artifacts"), list) else [])
        if str(item).strip()
    ]
    required = sorted(set(required))
    if not required:
        print("[backend_evidence_manifest] FAIL")
        print(f"invalid baseline required_artifacts: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    artifacts_root = _resolve_artifacts_dir()
    backend_dir = artifacts_root / "backend"
    backend_dir.mkdir(parents=True, exist_ok=True)
    out_json = backend_dir / "backend_evidence_manifest.json"
    out_md = backend_dir / "backend_evidence_manifest.md"

    entries = []
    missing = []
    total_size_bytes = 0
    for rel in required:
        path = ROOT / rel
        exists = path.is_file()
        size_bytes = int(path.stat().st_size) if exists else 0
        total_size_bytes += size_bytes
        row = {
            "path": rel,
            "exists": exists,
            "size_bytes": size_bytes,
            "sha256": _sha256(path) if exists else "",
        }
        entries.append(row)
        if not exists:
            missing.append(rel)

    entries = sorted(entries, key=lambda row: str(row.get("path") or ""))
    missing = sorted(set(missing))
    alignment = _load_json(ROOT / "artifacts" / "scene_catalog_runtime_alignment_guard.json")
    alignment_summary = alignment.get("summary") if isinstance(alignment.get("summary"), dict) else {}
    alignment_probe_login = str(alignment_summary.get("probe_login") or "").strip()
    alignment_probe_source = str(alignment_summary.get("probe_source") or "").strip()
    payload = {
        "ok": len(missing) == 0,
        "summary": {
            "artifact_count": len(entries),
            "present_count": sum(1 for item in entries if item.get("exists")),
            "missing_count": len(missing),
            "total_size_bytes": total_size_bytes,
            "alignment_probe_login": alignment_probe_login,
            "alignment_probe_source": alignment_probe_source,
            "artifacts_dir": str(backend_dir),
        },
        "baseline": baseline,
        "artifacts": entries,
        "missing": missing,
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Backend Evidence Manifest",
        "",
        f"- status: {'PASS' if payload['ok'] else 'FAIL'}",
        f"- artifact_count: {payload['summary']['artifact_count']}",
        f"- present_count: {payload['summary']['present_count']}",
        f"- missing_count: {payload['summary']['missing_count']}",
        f"- total_size_bytes: {payload['summary']['total_size_bytes']}",
        f"- alignment_probe_login: {payload['summary']['alignment_probe_login'] or '-'}",
        f"- alignment_probe_source: {payload['summary']['alignment_probe_source'] or '-'}",
        "",
        "## Artifacts",
        "",
    ]
    for item in entries:
        lines.append(
            f"- {item['path']}: {'OK' if item['exists'] else 'MISSING'} size={item['size_bytes']} sha256={item['sha256']}"
        )
    if missing:
        lines.extend(["", "## Missing", ""])
        for rel in missing:
            lines.append(f"- {rel}")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(out_json))
    print(str(out_md))
    if not payload["ok"]:
        print("[backend_evidence_manifest] FAIL")
        return 1
    print("[backend_evidence_manifest] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
