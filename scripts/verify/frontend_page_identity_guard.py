#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend/apps/web/src"


def fail(message: str) -> None:
    raise SystemExit(f"[frontend_page_identity_guard] FAIL: {message}")


required = {
    "layouts/AppShell.vue": "usePageIdentityRuntime",
    "views/ActionView.vue": "usePublishedPageIdentity",
    "pages/ContractFormPage.vue": "usePublishedPageIdentity",
    "App.vue": "document.title",
    "views/AccessDeniedView.vue": "usePageIdentityRuntime",
    "views/NotFoundView.vue": "usePageIdentityRuntime",
}
for relative, marker in required.items():
    source = (FRONTEND / relative).read_text(encoding="utf-8")
    if marker not in source:
        fail(f"missing authoritative identity integration: {relative}:{marker}")

writers = []
for path in FRONTEND.rglob("*"):
    if path.suffix not in {".ts", ".vue"}:
        continue
    source = path.read_text(encoding="utf-8")
    page_title_writes = source.replace("previewWindow.document.title", "")
    if "document.title" in page_title_writes:
        writers.append(path.relative_to(FRONTEND).as_posix())
if writers != ["App.vue"]:
    fail(f"document.title must have one page writer, got {writers}")

identity_sources = "\n".join(
    path.read_text(encoding="utf-8")
    for path in sorted((FRONTEND / "app").glob("pageIdentity*.ts"))
)
for forbidden in ("project.project", "construction.contract", "payment.request", "settlement"):
    if forbidden in identity_sources:
        fail(f"model-specific identity rule forbidden: {forbidden}")
for forbidden in ("model ===", "model !==", "includes(model)", "switch (model)", "switch(model)"):
    if forbidden in identity_sources:
        fail(f"model-specific identity branch forbidden: {forbidden}")

router = (FRONTEND / "router/index.ts").read_text(encoding="utf-8")
if "`${model || '记录'} #${id || ''}`" in router:
    fail("router still exposes model #id title")
if "action: '业务动作'" in router:
    fail("route-name generic business action title remains")

form_labels = (FRONTEND / "pages/contractForm/uiLabels.ts").read_text(encoding="utf-8")
if "`记录 #${params.recordId}`" in form_labels:
    fail("form subtitle still exposes record id")

print("[frontend_page_identity_guard] PASS writers=1 integrations=6")
