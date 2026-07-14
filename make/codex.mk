# ======================================================
# ==================== Codex Targets ===================
# ======================================================
.PHONY: codex.fast codex.gate codex.print codex.pr codex.cleanup codex.sync-main codex.cli

codex.print:
	@echo "== Codex SOP =="
	@echo "CODEX_MODE=$(CODEX_MODE) CODEX_DB=$(CODEX_DB) CODEX_MODULES=$(CODEX_MODULES) CODEX_NEED_UPGRADE=$(CODEX_NEED_UPGRADE)"
	@echo "SC_GATE_STRICT=$(SC_GATE_STRICT) SC_SCENE_OBS_STRICT=$(SC_SCENE_OBS_STRICT) SCENE_OBSERVABILITY_PREFLIGHT_STRICT=$(SCENE_OBSERVABILITY_PREFLIGHT_STRICT)"
	@echo "BASELINE_FREEZE_ENFORCE=$(BASELINE_FREEZE_ENFORCE)"
	@echo "BUSINESS_INCREMENT_PROFILE=$(BUSINESS_INCREMENT_PROFILE)"
	@echo "fast: restart (optional upgrade only if CODEX_NEED_UPGRADE=1) ; forbid demo.reset/gate.full"
	@echo "gate: optional upgrade + demo.reset + contract.export_all + gate.full"

CODEX_CLI_ARGS ?=
codex.cli: guard.prod.forbid
	@bash scripts/ops/codex_cli.sh $(CODEX_CLI_ARGS)

codex.fast: guard.prod.forbid check-compose-project check-compose-env
	@echo "[codex.fast] mode=fast db=$(CODEX_DB) modules=$(CODEX_MODULES) need_upgrade=$(CODEX_NEED_UPGRADE)"
	@$(MAKE) restart CODEX_MODE=fast DB=$(CODEX_DB)
	@if [ "$(CODEX_NEED_UPGRADE)" = "1" ]; then \
	  echo "[codex.fast] upgrading modules (explicitly allowed) ..."; \
	  $(MAKE) mod.upgrade CODEX_MODE=fast CODEX_NEED_UPGRADE=1 MODULE="$(CODEX_MODULES)" DB="$(CODEX_DB)"; \
	else \
	  echo "[codex.fast] skip module upgrade (default)"; \
	fi
	@echo "[codex.fast] done. (No demo.reset / No gate.full)"

codex.gate: guard.prod.forbid check-compose-project check-compose-env
	@echo "[codex.gate] mode=gate db=$(CODEX_DB) modules=$(CODEX_MODULES) need_upgrade=$(CODEX_NEED_UPGRADE)"
	@if [ "$(CODEX_NEED_UPGRADE)" = "1" ]; then \
	  echo "[codex.gate] upgrading modules ..."; \
	  $(MAKE) mod.upgrade CODEX_MODE=gate CODEX_NEED_UPGRADE=1 MODULE="$(CODEX_MODULES)" DB="$(CODEX_DB)"; \
	else \
	  echo "[codex.gate] skip module upgrade (not needed)"; \
	fi
	@$(MAKE) demo.reset CODEX_MODE=gate DB="$(CODEX_DB)"
	@$(MAKE) contract.export_all DB="$(CODEX_DB)"
	@$(MAKE) gate.full CODEX_MODE=gate BD="$(CODEX_DB)"
	@echo "[codex.gate] ✅ gate flow done."

codex.snapshot: guard.prod.forbid check-compose-project check-compose-env
	@echo "[codex.snapshot] db=$(CODEX_DB)"
	@$(MAKE) contract.export_all DB="$(CODEX_DB)"

.PHONY: codex.snapshot.export verify.backend.guard verify.portal.smoke
codex.snapshot.export: guard.prod.forbid
	@$(MAKE) --no-print-directory codex.snapshot

verify.backend.guard: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.boundary.guard

verify.portal.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) --no-print-directory verify.portal.fe_smoke.container

.PHONY: codex.pr codex.cleanup codex.sync-main

codex.pr: guard.prod.forbid
	@$(MAKE) codex.pr.body
	@$(MAKE) pr.push
	@$(MAKE) pr.create

codex.cleanup: guard.prod.forbid
	@$(MAKE) branch.cleanup

codex.sync-main: guard.prod.forbid
	@$(MAKE) main.sync

.PHONY: codex.run
codex.run: guard.prod.forbid
	@if [ -z "$(FLOW)" ]; then \
	  echo "❌ FLOW is required (fast|snapshot|gate|pr|merge|cleanup|rollback|release|main)"; exit 2; \
	fi
	@case "$(FLOW)" in \
	  fast) FLOW=fast bash scripts/ops/codex_run.sh ;; \
	  snapshot) FLOW=snapshot bash scripts/ops/codex_run.sh ;; \
	  gate) FLOW=gate bash scripts/ops/codex_run.sh ;; \
	  pr) $(MAKE) codex.pr ;; \
	  merge) $(MAKE) codex.merge ;; \
	  rollback) $(MAKE) codex.rollback ;; \
	  release) $(MAKE) codex.release.note ;; \
	  cleanup) $(MAKE) codex.cleanup ;; \
	  main) $(MAKE) codex.sync-main ;; \
	  *) echo "❌ unknown FLOW=$(FLOW)"; exit 2 ;; \
	esac

# ------------------ PR (Codex-safe) ------------------
.PHONY: pr.create pr.status pr.push pr.update pr.merge

PR_BASE ?= main
PR_TITLE ?=
PR_BODY_FILE ?= artifacts/pr_body.md
PR_MERGE_METHOD ?= squash
PR_MERGE_SUBJECT ?=
PR_MERGE_BODY ?= Merged by Codex through make pr.merge.

pr.create: guard.prod.forbid
	@branch="$$(git rev-parse --abbrev-ref HEAD)"; \
	if ! echo "$$branch" | grep -qE '^(codex|feat|feature|fix|experiment)/'; then \
	  echo "❌ pr.create only allowed on codex/*, feat/*, feature/*, fix/*, experiment/* (current=$$branch)"; exit 2; \
	fi; \
	if [ -z "$(PR_TITLE)" ]; then \
	  echo "❌ PR_TITLE is required"; exit 2; \
	fi; \
	if [ ! -f "$(PR_BODY_FILE)" ]; then \
	  echo "❌ PR_BODY_FILE not found: $(PR_BODY_FILE)"; exit 2; \
	fi; \
	echo "[pr.create] base=$(PR_BASE) head=$$branch title=$(PR_TITLE) body=$(PR_BODY_FILE)"; \
	gh pr create --base "$(PR_BASE)" --head "$$branch" --title "$(PR_TITLE)" --body-file "$(PR_BODY_FILE)"

pr.update: guard.prod.forbid
	@bash -lc '\
	set -euo pipefail; \
	BR="$$(git rev-parse --abbrev-ref HEAD)"; \
	if ! echo "$$BR" | grep -Eq "^(feat|feature|fix|codex|experiment)/.+"; then \
	  echo "[DENY] pr.update: branch not allowed: $$BR"; exit 2; \
	fi; \
	ENV_NAME="$${ENV:-dev}"; \
	if [ "$$ENV_NAME" = "prod" ]; then \
	  echo "[DENY] pr.update: ENV=prod is forbidden"; exit 3; \
	fi; \
	if [ -n "$${PROD_DANGER:-}" ]; then \
	  echo "[DENY] pr.update: PROD_DANGER is set (forbidden)"; exit 4; \
	fi; \
	if ! command -v gh >/dev/null 2>&1; then \
	  echo "[DENY] pr.update: gh CLI not found"; exit 5; \
	fi; \
	PR="$${PR:-}"; \
	if [ -z "$$PR" ]; then \
	  echo "[DENY] pr.update: missing PR=<number>"; exit 6; \
	fi; \
	ARGS=""; \
	if [ -n "$${TITLE:-}" ]; then ARGS="$$ARGS --title \"$${TITLE}\""; fi; \
	if [ -n "$${BODY:-}" ]; then ARGS="$$ARGS --body \"$${BODY}\""; fi; \
	if [ -n "$${BODY_FILE:-}" ]; then ARGS="$$ARGS --body-file \"$${BODY_FILE}\""; fi; \
	if [ -n "$${LABELS:-}" ]; then ARGS="$$ARGS --add-label \"$${LABELS}\""; fi; \
	if [ -n "$${REMOVE_LABELS:-}" ]; then ARGS="$$ARGS --remove-label \"$${REMOVE_LABELS}\""; fi; \
	if [ -z "$$ARGS" ]; then \
	  echo "[DENY] pr.update: nothing to update (set TITLE/BODY/BODY_FILE/LABELS/REMOVE_LABELS)"; exit 7; \
	fi; \
	echo "[pr.update] branch=$$BR ENV=$$ENV_NAME PR=$$PR"; \
	eval "gh pr edit $$PR $$ARGS"; \
	'

pr.push: guard.prod.forbid
	@bash scripts/ops/git_safe_push.sh

pr.merge: guard.prod.forbid
	@bash -lc '\
	set -euo pipefail; \
	BR="$$(git rev-parse --abbrev-ref HEAD)"; \
	if ! echo "$$BR" | grep -Eq "^(feat|feature|fix|codex|experiment)/.+"; then \
	  echo "[DENY] pr.merge: branch not allowed: $$BR"; exit 2; \
	fi; \
	ENV_NAME="$${ENV:-dev}"; \
	if [ "$$ENV_NAME" = "prod" ]; then \
	  echo "[DENY] pr.merge: ENV=prod is forbidden"; exit 3; \
	fi; \
	if [ -n "$${PROD_DANGER:-}" ]; then \
	  echo "[DENY] pr.merge: PROD_DANGER is set (forbidden)"; exit 4; \
	fi; \
	if ! command -v gh >/dev/null 2>&1; then \
	  echo "[DENY] pr.merge: gh CLI not found"; exit 5; \
	fi; \
	PR="$${PR:-}"; \
	if [ -z "$$PR" ]; then \
	  echo "[DENY] pr.merge: missing PR=<number>"; exit 6; \
	fi; \
	METHOD="$(PR_MERGE_METHOD)"; \
	case "$$METHOD" in merge|squash|rebase) ;; *) echo "[DENY] pr.merge: invalid PR_MERGE_METHOD=$$METHOD"; exit 7 ;; esac; \
	SUBJECT="$(PR_MERGE_SUBJECT)"; \
	if [ -z "$$SUBJECT" ]; then SUBJECT="Merge PR #$$PR"; fi; \
	echo "[pr.merge] branch=$$BR ENV=$$ENV_NAME PR=$$PR method=$$METHOD"; \
	gh pr merge "$$PR" "--$$METHOD" --subject "$$SUBJECT" --body "$(PR_MERGE_BODY)"; \
	'

pr.status:
	@gh pr status || true

# ------------------ Branch cleanup (Codex-safe) ------------------
.PHONY: branch.cleanup branch.cleanup.feature

CLEAN_BRANCH ?=

branch.cleanup: guard.prod.forbid
	@if [ -z "$(CLEAN_BRANCH)" ]; then echo "❌ CLEAN_BRANCH is required"; exit 2; fi
	@if ! echo "$(CLEAN_BRANCH)" | grep -qE '^codex/'; then echo "❌ only codex/* can be deleted"; exit 2; fi
	@echo "[branch.cleanup] checking merged into main: $(CLEAN_BRANCH)"
	@git fetch origin main >/dev/null 2>&1 || true
	@branch_sha="$$(git rev-parse "$(CLEAN_BRANCH)")"; \
	main_sha="$$(git rev-parse origin/main 2>/dev/null || git rev-parse main)"; \
	if git merge-base --is-ancestor "$$branch_sha" "$$main_sha"; then \
	  echo "[branch.cleanup] merge-base check: ok"; \
	else \
	  echo "[branch.cleanup] merge-base check failed; checking merged PR via gh ..."; \
	  if ! command -v gh >/dev/null 2>&1; then \
	    echo "❌ gh not found; cannot verify merged PR for $(CLEAN_BRANCH)"; \
	    exit 2; \
	  fi; \
	  pr_count="$$(gh pr list --state merged --search 'head:$(CLEAN_BRANCH)' --json number --jq 'length')" || \
	    (echo "❌ gh pr list failed; network/auth required to verify merge for $(CLEAN_BRANCH)" && exit 2); \
	  if [ "$$pr_count" -lt 1 ]; then \
	    echo "❌ branch not merged into main yet: $(CLEAN_BRANCH)"; \
	    exit 2; \
	  fi; \
	  echo "[branch.cleanup] merged PR detected for $(CLEAN_BRANCH)"; \
	fi
	@echo "[branch.cleanup] deleting local: $(CLEAN_BRANCH)"
	@git branch -d "$(CLEAN_BRANCH)"
	@echo "[branch.cleanup] deleting remote: $(CLEAN_BRANCH)"
	@git push origin --delete "$(CLEAN_BRANCH)"
	@echo "✅ [branch.cleanup] done"

branch.cleanup.feature: guard.prod.forbid
	@bash scripts/ops/branch_cleanup_safe.sh "$(CLEAN_BRANCH)"

# ------------------ Main sync (safe) ------------------
.PHONY: main.sync

main.sync: guard.prod.forbid
	@echo "[main.sync] checkout main + fast-forward pull"
	@git checkout main
	@git pull --ff-only origin main
