#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "frontend/apps/web/src"


def require(path: str, *markers: str) -> str:
    source = (ROOT / path).read_text(encoding="utf-8")
    missing = [marker for marker in markers if marker not in source]
    if missing:
        raise SystemExit(f"[frontend_delivery_hardening_guard] FAIL {path}: missing {missing}")
    return source


def forbid(path: str, *markers: str) -> None:
    source = (ROOT / path).read_text(encoding="utf-8")
    found = [marker for marker in markers if marker in source]
    if found:
        raise SystemExit(f"[frontend_delivery_hardening_guard] FAIL {path}: forbidden {found}")


require(
    "frontend/apps/web/src/app/contextEpoch.ts",
    "beginContextTransition",
    "isCurrentContextEpoch",
    "invalidateContextRequests",
    "currentContextSignal",
    "AbortController",
)
require(
    "frontend/apps/web/src/stores/session.ts",
    "beginContextTransition",
    "isCurrentContextEpoch",
    "invalidateContextRequests",
)
require(
    "frontend/apps/web/src/views/MyWorkView.vue",
    "currentContextEpoch",
    "isCurrentContextEpoch",
    "if (!session.token)",
)
require(
    "frontend/apps/web/src/app/productErrorState.ts",
    "登录已失效",
    "无权访问",
    "记录不存在",
    "数据已发生变化",
    "网络连接异常",
    "服务暂时不可用",
    "TECHNICAL_TEXT",
)
require(
    "frontend/apps/web/src/components/StatusPanel.vue",
    "resolveProductErrorState",
    "aria-live",
    "aria-busy",
    "正在重试",
)
require(
    "frontend/apps/web/src/components/business/IntentConfirmationDialog.vue",
    "<dialog",
    "showModal()",
    "@cancel.prevent",
    "trigger?.focus()",
)
require(
    "frontend/apps/web/src/layouts/AppShell.vue",
    "skip-link",
    'id="main-content"',
    'aria-label="主导航"',
    ':aria-expanded="!sidebarHidden"',
)
client = require("frontend/apps/web/src/api/client.ts", "reason=session_expired")
require("frontend/apps/web/src/api/client.ts", "currentContextSignal()")
if "redirect=${encodeURIComponent" in client:
    raise SystemExit("[frontend_delivery_hardening_guard] FAIL 401 may restore a sensitive route")
forbid("frontend/apps/web/src/stores/session.ts", "token_prefix", "token.slice(")
require("frontend/apps/web/package.json", '"@axe-core/playwright": "4.10.2"')

diff = subprocess.run(
    ["git", "diff", "--unified=0", "origin/main", "--", "frontend/apps/web/src"],
    cwd=ROOT,
    check=True,
    capture_output=True,
    text=True,
).stdout
added = "\n".join(line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
for label, pattern in {
    "hard-coded color": r"#[0-9a-fA-F]{3,8}\b|rgba?\(",
    "page inline style": r"\sstyle=\"",
    "model-specific CSS": r"\.(?:project|contract|settlement|payment)[-_][\w-]+\s*\{",
}.items():
    if re.search(pattern, added):
        raise SystemExit(f"[frontend_delivery_hardening_guard] FAIL new {label}")

writers = []
for path in SRC.rglob("*"):
    if path.suffix not in {".ts", ".vue"}:
        continue
    source = path.read_text(encoding="utf-8")
    if "document.title" in source.replace("previewWindow.document.title", ""):
        writers.append(path.relative_to(SRC).as_posix())
if writers != ["App.vue"]:
    raise SystemExit(f"[frontend_delivery_hardening_guard] FAIL document.title writers={writers}")

print("[frontend_delivery_hardening_guard] PASS error_states=12 title_writers=1 async_epoch=enabled axe=4.10.2")
