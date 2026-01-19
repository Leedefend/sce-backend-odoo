/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

function normalizeCompanies(raw) {
  if (!raw) return [];
  const list = Array.isArray(raw) ? raw : Object.values(raw);
  const out = [];
  for (const entry of list) {
    if (!entry) continue;
    if (Array.isArray(entry)) {
      const id = Number(entry[0]);
      if (!Number.isFinite(id)) continue;
      out.push({ id, name: entry[1] || `公司 ${id}`, sequence: 0 });
      continue;
    }
    if (typeof entry === "object") {
      if (typeof entry.id === "number") {
        out.push({
          id: entry.id,
          name: entry.name || entry.display_name || `公司 ${entry.id}`,
          sequence: typeof entry.sequence === "number" ? entry.sequence : 0,
        });
      }
    }
  }
  out.sort((a, b) => (a.sequence - b.sequence) || a.name.localeCompare(b.name));
  return out;
}

export class ScCompanySwitcherSidebar extends Component {
  static template = "smart_construction_core.ScCompanySwitcherSidebar";
  static props = {};

  setup() {
    this.companyService = useService("company");
    this.user = useService("user");
    this.state = useState({ open: false });
    this._onDocumentClick = (ev) => {
      const target = ev.target;
      if (!(target instanceof Element)) return;
      if (target.closest(".sc-company-switcher")) return;
      this.state.open = false;
    };

    onMounted(() => {
      document.addEventListener("click", this._onDocumentClick);
    });

    onWillUnmount(() => {
      document.removeEventListener("click", this._onDocumentClick);
    });
  }

  get userCompanies() {
    if (this.user && this.user.user_companies) return this.user.user_companies;
    if (this.user && this.user.userCompanies) return this.user.userCompanies;
    const session = window.odoo && window.odoo.__session_info__ ? window.odoo.__session_info__ : null;
    return session && session.user_companies ? session.user_companies : null;
  }

  get allowedCompanies() {
    if (this.companyService && this.companyService.allowedCompanies) {
      return normalizeCompanies(this.companyService.allowedCompanies);
    }
    if (this.companyService && this.companyService.allowedCompaniesWithAncestors) {
      return normalizeCompanies(this.companyService.allowedCompaniesWithAncestors);
    }
    const userCompanies = this.userCompanies || {};
    const raw = userCompanies.allowed_companies || userCompanies.allowedCompanies || {};
    return normalizeCompanies(raw);
  }

  get currentCompanyId() {
    if (this.companyService && this.companyService.currentCompany) {
      return this.companyService.currentCompany.id || null;
    }
    const userCompanies = this.userCompanies || {};
    return userCompanies.current_company || userCompanies.currentCompany || null;
  }

  get currentCompanyName() {
    const currentId = this.currentCompanyId;
    const current = this.allowedCompanies.find((company) => company.id === currentId);
    if (current) return current.name;
    if (this.allowedCompanies.length) return this.allowedCompanies[0].name;
    return "公司";
  }

  get canSwitch() {
    return this.allowedCompanies.length > 1;
  }

  toggleOpen() {
    if (!this.canSwitch) return;
    this.state.open = !this.state.open;
  }

  async switchCompany(companyId) {
    if (!this.canSwitch) return;
    if (companyId === this.currentCompanyId) {
      this.state.open = false;
      return;
    }
    if (this.companyService && typeof this.companyService.setCompanies === "function") {
      await this.companyService.setCompanies([companyId], true);
    } else {
      const hash = window.location.hash || "";
      const q = hash.startsWith("#") ? hash.slice(1) : hash;
      const params = new URLSearchParams(q);
      params.set("cids", String(companyId));
      window.location.hash = params.toString();
      window.location.reload();
    }
    this.state.open = false;
  }
}
