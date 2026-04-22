# -*- coding: utf-8 -*-

from datetime import date, timedelta

from odoo import api, models


class ProjectDemoCockpitSeed(models.Model):
    _inherit = "project.project"

    _DEMO_COCKPIT_MARKER = "DEMO_COCKPIT_R2"
    _OFFICIAL_SAMPLE_PROFILES = {
        "展厅-智慧园区运营中心": {
            "profile": "execution",
            "showcase_ready": True,
            "seed_costs": False,
            "seed_payments": False,
            "health_state": "warn",
            "execution_state": "in_progress",
            "target_lifecycle_state": "in_progress",
        },
        "展厅-装配式住宅试点": {
            "profile": "payment",
            "showcase_ready": True,
            "seed_costs": True,
            "seed_payments": False,
            "health_state": "warn",
            "execution_state": "done",
            "target_lifecycle_state": "in_progress",
        },
        "展厅-产线升级改造工程": {
            "profile": "settlement_complete",
            "showcase_ready": True,
            "seed_costs": True,
            "seed_payments": True,
            "health_state": "good",
            "execution_state": "done",
            "target_lifecycle_state": "done",
        },
    }

    @api.model
    def sc_demo_seed_cockpit_round2(self):
        partner_model = self.env["res.partner"]
        cost_code_model = self.env["project.cost.code"]
        contract_model = self.env["construction.contract"]
        contract_line_model = self.env["construction.contract.line"]
        cost_ledger_model = self.env["project.cost.ledger"]
        payment_request_model = self.env["payment.request"]
        activity_model = self.env["mail.activity"]
        model_model = self.env["ir.model"]

        projects = self._sc_demo_release_projects()

        partner_fallback = partner_model.search([("is_company", "=", True)], limit=1)
        cost_code = cost_code_model.search([], order="id asc", limit=1)
        model_id = model_model._get_id("project.project")
        todo_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)

        for project in projects:
            profile = self._sc_demo_profile(project)
            partner = project.partner_id or partner_fallback
            if not partner:
                continue

            self._sc_demo_seed_contracts(
                project=project,
                partner=partner,
                contract_model=contract_model,
                contract_line_model=contract_line_model,
            )
            if profile.get("seed_costs", True):
                self._sc_demo_seed_cost_ledger(
                    project=project,
                    partner=partner,
                    cost_code=cost_code,
                    cost_ledger_model=cost_ledger_model,
                )
            else:
                self._sc_demo_cleanup_cost_ledger(project)
            if profile.get("seed_payments", True):
                self._sc_demo_seed_payments(
                    project=project,
                    partner=partner,
                    payment_request_model=payment_request_model,
                )
            else:
                self._sc_demo_cleanup_payments(project)
            self._sc_demo_seed_risk_signals(
                project=project,
                activity_model=activity_model,
                todo_type=todo_type,
                model_id=model_id,
                profile=profile,
            )
            self._sc_demo_apply_showcase_profile(project, profile)

        return True

    @api.model
    def _sc_demo_release_projects(self):
        """Pick showroom-first projects for cockpit demo seeding."""

        project_model = self.with_context(active_test=False)
        projects = project_model.browse()

        sample_names = list(self._OFFICIAL_SAMPLE_PROFILES.keys())
        if sample_names:
            projects |= project_model.search(
                [("active", "=", True), ("name", "in", sample_names)],
                order="id asc",
            )

        projects |= project_model.search(
            [("active", "=", True), ("name", "ilike", "展厅-%")],
            order="id asc",
            limit=24,
        )

        if len(projects) < 12:
            projects |= project_model.search(
                [("active", "=", True), ("project_code", "ilike", "DEMO-%")],
                order="id asc",
                limit=24,
            )

        return projects

    @api.model
    def _sc_demo_profile(self, project):
        profile = dict(
            self._OFFICIAL_SAMPLE_PROFILES.get(
                str(project.name or "").strip(),
                {
                    "profile": "showroom",
                    "showcase_ready": False,
                    "seed_costs": True,
                    "seed_payments": True,
                    "health_state": "warn",
                    "execution_state": "done",
                    "target_lifecycle_state": str(getattr(project, "lifecycle_state", "") or "").strip().lower() or "in_progress",
                },
            )
        )
        profile.setdefault("profile", "showroom")
        profile.setdefault("showcase_ready", False)
        profile.setdefault("seed_costs", True)
        profile.setdefault("seed_payments", True)
        profile.setdefault("health_state", "warn")
        profile.setdefault("execution_state", "done")
        profile.setdefault(
            "target_lifecycle_state",
            str(getattr(project, "lifecycle_state", "") or "").strip().lower() or "in_progress",
        )
        return profile

    @api.model
    def _sc_demo_seed_contracts(self, project, partner, contract_model, contract_line_model):
        marker = self._DEMO_COCKPIT_MARKER
        existing = contract_model.search_count(
            [("project_id", "=", project.id), ("subject", "ilike", marker)]
        )
        if existing:
            return

        base_out = 8_000_000.0 + (project.id % 7) * 1_100_000.0
        base_in = base_out * 0.62
        samples = [
            ("out", f"[{marker}] {project.name}-收入合同", base_out),
            ("in", f"[{marker}] {project.name}-支出合同", base_in),
        ]
        for contract_type, subject, amount in samples:
            contract = contract_model.create(
                {
                    "subject": subject,
                    "type": contract_type,
                    "project_id": project.id,
                    "partner_id": partner.id,
                }
            )
            contract_line_model.create(
                {
                    "contract_id": contract.id,
                    "qty_contract": 1.0,
                    "price_contract": amount,
                    "note": marker,
                }
            )
            if contract.state in ("draft", "confirmed"):
                try:
                    contract.action_set_running()
                except Exception:
                    continue

    @api.model
    def _sc_demo_seed_cost_ledger(self, project, partner, cost_code, cost_ledger_model):
        if not cost_code:
            return

        marker = self._DEMO_COCKPIT_MARKER
        base = date.today()
        samples = [
            ("材料采购", 1_180_000.0, 5),
            ("人工费用", 820_000.0, 15),
            ("机械费用", 430_000.0, 25),
            ("分包结算", 1_650_000.0, 35),
        ]
        for note_text, amount, days in samples:
            entry_note = f"{marker}-{note_text}"
            existing = cost_ledger_model.search_count(
                [
                    ("project_id", "=", project.id),
                    ("note", "=", entry_note),
                ]
            )
            if existing:
                continue
            happen_day = base - timedelta(days=days)
            try:
                cost_ledger_model.create(
                    {
                        "project_id": project.id,
                        "cost_code_id": cost_code.id,
                        "date": happen_day,
                        "period": happen_day.strftime("%Y-%m"),
                        "amount": amount,
                        "partner_id": partner.id,
                        "note": entry_note,
                    }
                )
            except Exception:
                continue

    @api.model
    def _sc_demo_cleanup_cost_ledger(self, project):
        ledger_model = self.env["project.cost.ledger"]
        marker = self._DEMO_COCKPIT_MARKER
        try:
            ledger_model.search(
                [("project_id", "=", project.id), ("note", "ilike", f"{marker}-%")]
            ).unlink()
        except Exception:
            return

    @api.model
    def _sc_demo_seed_payments(self, project, partner, payment_request_model):
        marker = self._DEMO_COCKPIT_MARKER
        samples = [
            ("receive", "approved", 2_800_000.0, "节点回款A"),
            ("receive", "done", 1_650_000.0, "节点回款B"),
            ("pay", "draft", 1_200_000.0, "分包付款A"),
            ("pay", "draft", 860_000.0, "材料付款B"),
        ]
        for req_type, state, amount, note_text in samples:
            req_name = f"{marker}-{project.id}-{note_text}"
            exists = payment_request_model.search_count(
                [
                    ("project_id", "=", project.id),
                    ("name", "=", req_name),
                ]
            )
            if exists:
                continue
            try:
                payment_request_model.create(
                    {
                        "name": req_name,
                        "project_id": project.id,
                        "partner_id": partner.id,
                        "type": req_type,
                        "state": state,
                        "amount": amount,
                        "note": marker,
                    }
                )
            except Exception:
                continue

    @api.model
    def _sc_demo_cleanup_payments(self, project):
        payment_request_model = self.env["payment.request"]
        marker = self._DEMO_COCKPIT_MARKER
        try:
            payment_request_model.search(
                [
                    ("project_id", "=", project.id),
                    "|",
                    ("note", "=", marker),
                    ("name", "ilike", f"{marker}-%"),
                ]
            ).unlink()
        except Exception:
            return

    @api.model
    def _sc_demo_seed_risk_signals(self, project, activity_model, todo_type, model_id, profile=None):
        marker = self._DEMO_COCKPIT_MARKER
        profile = dict(profile or {})
        target_health = str(profile.get("health_state") or "warn").strip().lower() or "warn"
        if "health_state" in project._fields and (project.health_state or "") != target_health:
            project.write({"health_state": target_health})

        if not todo_type or not model_id:
            return

        marker_summary = f"{marker}-成本偏差复核"
        existing = activity_model.search_count(
            [
                ("res_model", "=", "project.project"),
                ("res_id", "=", project.id),
                ("summary", "=", marker_summary),
            ]
        )
        if existing:
            return
        activity_model.create(
            {
                "activity_type_id": todo_type.id,
                "res_model_id": model_id,
                "res_id": project.id,
                "summary": marker_summary,
                "note": f"{marker}：请复核本周成本偏差。",
                "user_id": project.user_id.id or self.env.user.id,
                "date_deadline": date.today() - timedelta(days=2),
            }
        )

    @api.model
    def _sc_demo_apply_showcase_profile(self, project, profile):
        vals = {"sc_demo_showcase": True, "sc_demo_showcase_ready": bool(profile.get("showcase_ready"))}
        if "health_state" in project._fields:
            vals["health_state"] = str(profile.get("health_state") or "warn")
        if "sc_execution_state" in project._fields:
            vals["sc_execution_state"] = str(profile.get("execution_state") or "done")
        project.write(vals)

        target_lifecycle = str(profile.get("target_lifecycle_state") or "").strip().lower()
        if target_lifecycle and getattr(project, "lifecycle_state", "") != target_lifecycle:
            try:
                project.action_set_lifecycle_state(target_lifecycle)
            except Exception:
                pass
