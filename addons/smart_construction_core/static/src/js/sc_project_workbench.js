/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ScProjectWorkbench extends Component {
  static template = "smart_construction_core.ScProjectWorkbench";

  setup() {
    this.orm = useService("orm");
    this.action = useService("action");
    this.user = useService("user");
    this.state = useState({
      companyName: this._resolveCompanyName(),
      userName: this._resolveUserName(),
      projectTotal: "…",
      projectActive: "…",
      projectInactive: "—",
      costAlerts: "--",
      pendingApprovals: "--",
    });

    onWillStart(async () => {
      const total = await this.orm.searchCount("project.project", []);
      const active = await this.orm.searchCount("project.project", [["active", "=", true]]);
      this.state.projectTotal = total;
      this.state.projectActive = active;
      this.state.projectInactive = total - active;
    });
  }

  _resolveCompanyName() {
    const companyId = this.user && this.user.companyId ? this.user.companyId : null;
    const companies = this.user && this.user.user_companies ? this.user.user_companies.allowed_companies : null;
    if (companyId && companies && companies[companyId]) return companies[companyId].name;
    const session = window.odoo && window.odoo.__session_info__ ? window.odoo.__session_info__ : null;
    const sessionCompanies = session && session.user_companies ? session.user_companies.allowed_companies : null;
    if (companyId && sessionCompanies && sessionCompanies[companyId]) return sessionCompanies[companyId].name;
    return "—";
  }

  _resolveUserName() {
    if (this.user && this.user.name) return this.user.name;
    const session = window.odoo && window.odoo.__session_info__ ? window.odoo.__session_info__ : null;
    return session && session.name ? session.name : "—";
  }

  openProjectList() {
    this.action.doAction("smart_construction_core.action_sc_project_list");
  }

  openCostCompare() {
    this.action.doAction("smart_construction_core.action_project_cost_compare");
  }

  openContractLedger() {
    this.action.doAction("smart_construction_core.action_project_contract_overview");
  }

  openPaymentRequest() {
    this.action.doAction("smart_construction_core.action_payment_request");
  }
}
