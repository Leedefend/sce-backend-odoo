/** @odoo-module **/

import { Component, onMounted, onWillStart, onWillUnmount, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ScCompanySwitcherSidebar } from "./sc_company_switcher_sidebar";
import { DOMAIN_NAV_MAP, DEFAULT_DOMAIN_KEY, PINNED_ENTRIES } from "@smart_construction_core/config/domain_nav_map";

const mainComponents = registry.category("main_components");
const ROOT_XMLID = "smart_construction_core.menu_sc_root";
const ROOT_NAME = "智能施工 2.0";
const OPEN_SECTIONS_KEY = "sc_sidebar_open_sections";
const RECENT_MENUS_KEY = "sc_sidebar_recent_menus";
const FAVORITE_MENUS_KEY = "sc_sidebar_favorite_menus";
const RECENT_LIMIT = 8;
const FAVORITE_LIMIT = 12;
const SHOW_OVERVIEW = getConfigFlag("sc_sidebar_overview", true);
const OVERVIEW_MENU_XMLIDS = new Set(["smart_construction_core.menu_sc_project_center"]);
const OVERVIEW_MENU_IDS = new Set();
const OVERVIEW_MENU_NAMES = new Set(["项目中心"]);
const OVERVIEW_ACTION_XMLID = "smart_construction_core.action_sc_project_workbench";
const DEBUG_ENABLED = Boolean(
  (window.odoo && window.odoo.__DEBUG__) || /\bdebug\b/.test(window.location.search || "")
);
const ENABLE_ROLE_ENTRIES = getConfigFlag("sc_role_entries", true);

export class ScSidebarHeader extends Component {
  static template = "smart_construction_core.ScSidebarHeader";
  static props = {};
  static components = { ScCompanySwitcherSidebar };

  setup() {
    this.user = useService("user");
  }

  get userLabel() {
    if (!this.user) return "";
    return this.user.name || this.user.userName || this.user.displayName || "";
  }
}

export class ScSidebar extends Component {
  static template = "smart_construction_core.ScSidebar";
  static props = {};
  static components = { ScCompanySwitcherSidebar, ScSidebarHeader };

  setup() {
    this.orm = useService("orm");
    this.action = useService("action");
    this.user = useService("user");
    try {
      this.companyService = useService("company");
    } catch (err) {
      this.companyService = null;
    }
    this.state = useState({
      visible: false,
      sections: [],
      activeMenuId: 0,
      searchTerm: "",
      recentMenus: [],
      favoriteMenus: [],
      roleEntries: [],
      enableRoleEntries: ENABLE_ROLE_ENTRIES,
      pinnedEntries: [],
      debugMessage: "",
      showOverview: SHOW_OVERVIEW,
      allowedCompanies: [],
      selectedCompanyIds: [],
      companyMenuOpen: false,
    });
    this.storageKey = getStorageKey(this.user, OPEN_SECTIONS_KEY);
    this.recentKey = getStorageKey(this.user, RECENT_MENUS_KEY);
    this.favoriteKey = getStorageKey(this.user, FAVORITE_MENUS_KEY);
    this.menuMap = null;
    this.menuIndex = {};
    this._loading = false;
    this._lastCompanyKey = getCompanyKeyFromHash() || getCompanyKey(this.user);
    this._onHashChange = () => this.syncActiveMenu();
    this.debugLog = (...args) => {
      if (DEBUG_ENABLED) console.log("[SC][sidebar]", ...args);
    };
    this.toggleSection = (sectionId) => {
      const section = findSectionById(this.state.sections, sectionId);
      if (section) section.isOpen = !section.isOpen;
      this.persistOpenSections();
    };
    this.toggleDomain = (domainId) => {
      const domain = this.state.sections.find((item) => item.id === domainId);
      if (domain) domain.isOpen = !domain.isOpen;
      this.persistOpenSections();
    };
    this.onSectionTitleClick = (section) => {
      if (!section) return;
      if (section.children && section.children.length) {
        this.toggleSection(section.id);
        return;
      }
      if (section.actionId) {
        this.openMenu(section.id, section.actionId, section.name);
        return;
      }
      this.toggleSection(section.id);
    };
    this.onDomainTitleClick = (domain) => {
      if (!domain) return;
      this.toggleDomain(domain.id);
    };
    this.openPinnedEntry = async (entry) => {
      if (!entry || entry.disabled) return;
      if (entry.menuId && entry.actionId) {
        await this.openMenu(entry.menuId, entry.actionId, entry.name);
        return;
      }
      if (entry.actionId) {
        await this.action.doAction(entry.actionId, { clearBreadcrumbs: false });
      }
    };
    this.openMenu = async (menuId, actionId, label) => {
      this.state.activeMenuId = menuId;
      this.addRecentMenu(menuId, actionId, label);
      setHashParams({ menu_id: menuId, action: actionId });
      if (actionId) {
        await this.action.doAction(actionId, { clearBreadcrumbs: false });
      }
      window.setTimeout(() => this.syncActiveMenu(), 0);
    };
    this.persistOpenSections = () => {
      if (!this.storageKey) return;
      const openIds = [];
      for (const domain of this.state.sections) {
        if (domain.isOpen) openIds.push(domain.id);
        for (const section of domain.sections || []) {
          if (section.isOpen) openIds.push(section.id);
        }
      }
      saveOpenSectionIds(this.storageKey, openIds);
    };
    this.addRecentMenu = (menuId, actionId, label) => {
      if (!this.recentKey || !menuId) return;
      const name = label || resolveMenuLabel(menuId, this.menuIndex) || "";
      const next = addRecentEntry(this.state.recentMenus, { menuId, actionId, name }, RECENT_LIMIT);
      this.state.recentMenus = next;
      saveMenuEntries(this.recentKey, next);
    };
    this.toggleFavorite = (menuId, actionId, label) => {
      if (!this.favoriteKey || !menuId) return;
      const name = label || resolveMenuLabel(menuId, this.menuIndex) || "";
      const next = toggleFavoriteEntry(this.state.favoriteMenus, { menuId, actionId, name }, FAVORITE_LIMIT);
      this.state.favoriteMenus = next;
      saveMenuEntries(this.favoriteKey, next);
    };
    this.isFavorite = (menuId) => {
      return this.state.favoriteMenus.some((entry) => entry.menuId === menuId);
    };
    this.clearRecentMenus = () => {
      this.state.recentMenus = [];
      saveMenuEntries(this.recentKey, []);
    };
    this.clearFavoriteMenus = () => {
      this.state.favoriteMenus = [];
      saveMenuEntries(this.favoriteKey, []);
    };
    this.onSearchInput = (ev) => {
      this.state.searchTerm = ev.target.value || "";
    };
    this.toggleCompanyMenu = () => {
      this.state.companyMenuOpen = !this.state.companyMenuOpen;
    };
    this.toggleCompanySelection = (companyId) => {
      const next = new Set(this.state.selectedCompanyIds);
      if (next.has(companyId)) {
        next.delete(companyId);
      } else {
        next.add(companyId);
      }
      if (!next.size && this.state.allowedCompanies.length) {
        next.add(this.state.allowedCompanies[0].id);
      }
      this.state.selectedCompanyIds = Array.from(next);
    };
    this.applyCompanySelection = async () => {
      const nextIds = normalizeCompanyIds(this.state.selectedCompanyIds);
      const currentIds = normalizeCompanyIds(
        getSelectedCompanyIds(this.user, this.companyService, this.state.allowedCompanies)
      );
      if (!nextIds.length) return;
      if (arraysEqual(nextIds, currentIds)) {
        this.state.companyMenuOpen = false;
        return;
      }
      if (this.companyService && typeof this.companyService.setCompanies === "function") {
        await this.companyService.setCompanies(nextIds);
      } else {
        setHashParams({ cids: nextIds.join(",") });
        window.location.reload();
      }
      this.state.companyMenuOpen = false;
    };
    this._onDocumentClick = (ev) => {
      const target = ev.target;
      if (!(target instanceof Element)) return;
      if (target.closest(".sc-sidebar__company")) return;
      this.state.companyMenuOpen = false;
    };

    onMounted(() => {
      this.syncActiveMenu();
      this.syncCompanyState();
      window.addEventListener("hashchange", this._onHashChange);
      window.addEventListener("popstate", this._onHashChange);
      document.addEventListener("click", this._onDocumentClick);
      this.loadSections();
    });

    onWillStart(() => {
      // Avoid dev-mode watchdog warnings; actual loading happens onMounted.
    });

    onWillUnmount(() => {
      window.removeEventListener("hashchange", this._onHashChange);
      window.removeEventListener("popstate", this._onHashChange);
      document.removeEventListener("click", this._onDocumentClick);
    });
  }

  async loadSections() {
    if (this._loading) return;
    this._loading = true;
    const rootId = await this.getRootMenuId();
    this.debugLog("rootId", rootId);
    const menus = await this.orm.call("ir.ui.menu", "load_menus", [false], {
      context: this.user ? this.user.context : undefined,
    });
    this.debugLog("menus keys", menus && Object.keys(menus));
    const rootMenu = this.resolveRootMenu(menus, rootId);
    this.debugLog("rootMenu", rootMenu);
    if (!rootMenu) {
      this.state.visible = false;
      this.state.debugMessage = DEBUG_ENABLED
        ? "Root menu not found; check XMLID or permissions."
        : "";
      this._loading = false;
      return;
    }

    const sections = buildMenuSections(rootMenu, this.menuMap);
    const domainSections = buildDomainSections(sections, this.menuMap);
    for (const domain of domainSections) {
      const isSingleSection = domain.sections.length === 1;
      for (const section of domain.sections) {
        section._hideTitle = shouldFlattenSection(domain, section, isSingleSection);
        if (section._hideTitle) {
          section.isOpen = true;
        }
      }
    }
    this.debugLog("sections", domainSections);
    if (!domainSections.length) {
      this.state.visible = false;
      this.state.debugMessage = DEBUG_ENABLED ? "No visible sections for root menu." : "";
      this._loading = false;
      return;
    }

    const activeId = getActiveMenuId();
    this.state.activeMenuId = activeId;
    const storedOpen = this.storageKey ? loadOpenSectionIds(this.storageKey) : null;
    for (const domain of domainSections) {
      domain.isOpen = storedOpen ? storedOpen.includes(domain.id) : false;
      for (const section of domain.sections) {
        section.isOpen = storedOpen ? storedOpen.includes(section.id) : false;
        if (section.id === activeId || section.children.some((child) => child.id === activeId)) {
          section.isOpen = true;
          domain.isOpen = true;
        }
        if (section._hideTitle) {
          section.isOpen = true;
        }
      }
    }
    if (!domainSections.some((domain) => domain.isOpen)) {
      const defaultDomain = domainSections.find((domain) => domain.key === "project_center");
      if (defaultDomain) defaultDomain.isOpen = true;
      else domainSections[0].isOpen = true;
    }
    this.state.sections = domainSections;
    this.state.pinnedEntries = buildPinnedEntries(PINNED_ENTRIES, menus, this.menuMap);
    this.state.visible = true;
    this.state.debugMessage = "";
    this._lastCompanyKey = getCompanyKeyFromHash() || getCompanyKey(this.user);
    this.menuIndex = buildMenuIndex(domainSections);
    this.state.recentMenus = loadMenuEntries(this.recentKey);
    this.state.favoriteMenus = loadMenuEntries(this.favoriteKey);
    this.syncCompanyState();

    const hashParams = parseHashParams();
    if (!hashParams.action) {
      const fallback = findFirstActionFromSections(sections);
      if (fallback) {
        await this.action.doAction(fallback.actionId, { clearBreadcrumbs: false });
      }
    }
    this._loading = false;
  }

  syncActiveMenu() {
    const id = getActiveMenuId();
    this.state.activeMenuId = id || 0;
    if (id) this.scrollActiveIntoView();
    this.maybeReloadForCompany();
  }

  scrollActiveIntoView() {
    if (!this.state.visible) return;
    const item = document.querySelector(".sc-sidebar__item.is-active");
    if (item && typeof item.scrollIntoView === "function") {
      item.scrollIntoView({ block: "nearest" });
    }
  }

  async getRootMenuId() {
    return null;
  }

  resolveRootMenu(menus, rootId) {
    const normalized = normalizeMenus(menus, (map) => (this.menuMap = map));
    if (rootId && !normalized && this.menuMap && this.menuMap[rootId]) return this.menuMap[rootId];
    if (!normalized && this.menuMap) {
      const byXmlid = findMenuByXmlid(null, this.menuMap, ROOT_XMLID);
      if (byXmlid) return byXmlid;
      const byName = findMenuByName(null, this.menuMap, ROOT_NAME);
      if (byName) return byName;
    }
    if (!normalized) return null;
    if (!this.menuMap) this.menuMap = buildMenuMap(normalized);
    if (rootId) return findMenuById(normalized, rootId, this.menuMap);
    return findMenuByXmlid(normalized, this.menuMap, ROOT_XMLID) || findMenuByName(normalized, this.menuMap, ROOT_NAME);
  }

  get sectionsForRender() {
    const term = normalizeSearch(this.state.searchTerm);
    if (!term) return this.state.sections;
    const parts = term.split(/\s+/).filter(Boolean);
    const filteredDomains = [];
    for (const domain of this.state.sections) {
      const domainName = resolveName(domain.name);
      const domainMatch = matchesText(domainName, parts);
      const domainLabel = highlightLabel(domainName, parts);
      const matchedSections = [];
      for (const section of domain.sections) {
        const sectionName = resolveName(section.name);
        const sectionMatch = matchesText(sectionName, parts);
        const sectionLabel = highlightLabel(sectionName, parts);
        if (sectionMatch) {
          matchedSections.push({
            ...section,
            isOpen: true,
            _label: sectionLabel,
            _hideTitle: shouldFlattenSection(domain, section, domain.sections.length === 1),
          });
          continue;
        }
        const children = section.children
          .filter((child) => matchesText(resolveName(child.name), parts))
          .map((child) => ({ ...child, _label: highlightLabel(resolveName(child.name), parts) }));
        if (children.length) {
          matchedSections.push({
            ...section,
            children,
            isOpen: true,
            _label: sectionLabel,
            _hideTitle: shouldFlattenSection(domain, section, domain.sections.length === 1),
          });
        }
      }
      if (domainMatch) {
        filteredDomains.push({
          ...domain,
          isOpen: true,
          _label: domainLabel,
          sections: domain.sections.map((section) => ({
            ...section,
            isOpen: section._hideTitle ? true : section.isOpen,
            _hideTitle: shouldFlattenSection(domain, section, domain.sections.length === 1),
          })),
        });
        continue;
      }
      if (matchedSections.length) {
        filteredDomains.push({ ...domain, sections: matchedSections, isOpen: true, _label: domainLabel });
      }
    }
    return filteredDomains;
  }

  get recentForRender() {
    const term = normalizeSearch(this.state.searchTerm);
    if (!term) return this.state.recentMenus;
    const parts = term.split(/\s+/).filter(Boolean);
    return this.state.recentMenus
      .filter((entry) => matchesText(entry.name, parts))
      .map((entry) => ({ ...entry, _label: highlightLabel(entry.name, parts) }));
  }

  get favoritesForRender() {
    const term = normalizeSearch(this.state.searchTerm);
    if (!term) return this.state.favoriteMenus;
    const parts = term.split(/\s+/).filter(Boolean);
    return this.state.favoriteMenus
      .filter((entry) => matchesText(entry.name, parts))
      .map((entry) => ({ ...entry, _label: highlightLabel(entry.name, parts) }));
  }

  maybeReloadForCompany() {
    const companyKey = getCompanyKeyFromHash() || getCompanyKey(this.user);
    if (companyKey && companyKey !== this._lastCompanyKey) {
      this._lastCompanyKey = companyKey;
      this.syncCompanyState();
      this.loadSections();
    }
  }

  syncCompanyState() {
    const allowed = getAllowedCompanies(this.user, this.companyService);
    const selected = getSelectedCompanyIds(this.user, this.companyService, allowed);
    this.state.allowedCompanies = allowed;
    this.state.selectedCompanyIds = selected;
  }

  get companyLabel() {
    return buildCompanyLabel(this.state.allowedCompanies, this.state.selectedCompanyIds);
  }
}

mainComponents.add("smart_construction_sidebar", { Component: ScSidebar });

function parseHashParams() {
  const hash = window.location.hash || "";
  const q = hash.startsWith("#") ? hash.slice(1) : hash;
  const out = {};
  for (const part of q.split("&")) {
    if (!part) continue;
    const idx = part.indexOf("=");
    if (idx < 0) continue;
    const k = decodeURIComponent(part.slice(0, idx));
    const v = decodeURIComponent(part.slice(idx + 1));
    out[k] = v;
  }
  return out;
}

function setHashParams(patch) {
  const params = parseHashParams();
  const next = { ...params, ...patch };
  const q = Object.entries(next)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join("&");
  window.location.hash = q;
}

function getCompanyKeyFromHash() {
  const params = parseHashParams();
  if (params.cids) return params.cids;
  if (params.company_id) return params.company_id;
  return null;
}

function getActiveMenuId() {
  return parseInt(parseHashParams().menu_id || "0", 10);
}

export function normalizeMenus(raw, onMap) {
  if (!raw) return null;
  if (looksLikeMenuMap(raw)) {
    if (onMap) onMap(raw);
    return null;
  }
  if (raw.menu_data && typeof raw.menu_data === "object" && !Array.isArray(raw.menu_data)) {
    if (onMap) onMap(raw.menu_data);
  }
  if (raw.root) return normalizeMenus(raw.root, onMap);
  if (raw.menus) return normalizeMenus(raw.menus, onMap);
  if (raw.menu) return normalizeMenus(raw.menu, onMap);
  if (raw.menu_data) return normalizeMenus(raw.menu_data, onMap);
  if (raw.result) return normalizeMenus(raw.result, onMap);
  if (typeof raw === "object" && Array.isArray(raw.children)) return raw;
  return null;
}

function looksLikeMenuMap(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return false;
  const keys = Object.keys(raw);
  if (!keys.length) return false;
  const numericKeys = keys.filter((key) => /^\d+$/.test(key));
  if (!numericKeys.length) return false;
  const sample = raw[numericKeys[0]];
  return !!(sample && typeof sample === "object" && typeof sample.id === "number");
}

function buildMenuMap(root) {
  if (!root || typeof root !== "object") return null;
  const map = {};
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    if (!node || typeof node !== "object") continue;
    if (typeof node.id === "number") map[node.id] = node;
    const children = node.children;
    if (Array.isArray(children)) {
      for (const child of children) {
        if (child && typeof child === "object") stack.push(child);
      }
    }
  }
  return Object.keys(map).length ? map : null;
}

function findMenuById(node, id, menuMap) {
  if (menuMap && menuMap[id]) return menuMap[id];
  if (!node) return null;
  if (node.id === id) return node;
  const children = resolveChildren(node, menuMap);
  for (const child of children) {
    const found = findMenuById(child, id, menuMap);
    if (found) return found;
  }
  return null;
}

function findMenuByXmlid(node, menuMap, xmlid) {
  if (!xmlid) return null;
  if (menuMap) {
    for (const key of Object.keys(menuMap)) {
      const item = menuMap[key];
      if (item && item.xmlid === xmlid) return item;
    }
  }
  if (!node) return null;
  if (node.xmlid === xmlid) return node;
  const children = resolveChildren(node, menuMap);
  for (const child of children) {
    const found = findMenuByXmlid(child, menuMap, xmlid);
    if (found) return found;
  }
  return null;
}

function findMenuByName(node, menuMap, name) {
  if (!name) return null;
  if (menuMap) {
    for (const key of Object.keys(menuMap)) {
      const item = menuMap[key];
      if (!item || typeof item !== "object") continue;
      if (resolveName(item.name) === name) return item;
    }
  }
  if (!node) return null;
  if (resolveName(node.name) === name) return node;
  const children = resolveChildren(node, menuMap);
  for (const child of children) {
    const found = findMenuByName(child, menuMap, name);
    if (found) return found;
  }
  return null;
}

export function resolveChildren(node, menuMap) {
  const children = node && node.children ? node.children : [];
  if (!children.length) return [];
  if (typeof children[0] === "number" && menuMap) {
    return children.map((id) => menuMap[id]).filter(Boolean);
  }
  return children;
}

export function parseActionId(menu) {
  const action = menu && menu.action;
  if (!action) return null;
  if (typeof action === "number") return action;
  if (Array.isArray(action)) return action[0] || null;
  if (typeof action === "object" && typeof action.id === "number") return action.id;
  if (typeof action !== "string") return null;
  const parts = action.split(",");
  if (parts.length < 2) return null;
  const id = parseInt(parts[1], 10);
  return Number.isNaN(id) ? null : id;
}

function resolveNodeAction(node, menuMap) {
  const actionId = parseActionId(node);
  if (actionId) return { actionId, disabled: false };
  const fallback = findFirstActionMenu(node, menuMap);
  if (fallback) return { actionId: parseActionId(fallback), disabled: false };
  return { actionId: null, disabled: true };
}

function findFirstActionMenu(menu, menuMap) {
  const candidates = collectActionCandidates(menu, menuMap);
  if (!candidates.length) return null;
  candidates.sort((a, b) => {
    const scoreA = scoreViewMode(a);
    const scoreB = scoreViewMode(b);
    if (scoreA !== scoreB) return scoreA - scoreB;
    return sortBySequenceThenName(a, b, menuMap);
  });
  return candidates[0] || null;
}

function collectActionCandidates(menu, menuMap) {
  const out = [];
  const queue = [menu];
  while (queue.length) {
    const node = queue.shift();
    if (parseActionId(node)) out.push(node);
    const children = resolveChildren(node, menuMap).slice();
    children.sort((a, b) => sortBySequenceThenName(a, b, menuMap));
    for (const child of children) queue.push(child);
  }
  return out;
}

function scoreViewMode(node) {
  const raw = node && (node.view_mode || node.viewMode);
  const viewMode = raw ? String(raw).toLowerCase() : "";
  if (viewMode.includes("tree") || viewMode.includes("list")) return 0;
  if (viewMode.includes("kanban")) return 1;
  if (viewMode.includes("form")) return 2;
  return 9;
}

export function buildMenuSections(rootMenu, menuMap) {
  const sections = [];
  const children = resolveChildren(rootMenu, menuMap).slice();
  children.sort((a, b) => sortBySequenceThenName(a, b, menuMap));
  if (!OVERVIEW_MENU_IDS.size) {
    for (const child of children) {
      const menuRecord = menuMap && menuMap[child.id] ? menuMap[child.id] : child;
      if (menuRecord && menuRecord.xmlid && OVERVIEW_MENU_XMLIDS.has(menuRecord.xmlid)) {
        OVERVIEW_MENU_IDS.add(child.id);
      }
    }
  }
  for (const child of children) {
    const menuRecord = menuMap && menuMap[child.id] ? menuMap[child.id] : child;
    const childAction = parseActionId(child);
    const childName = resolveName(child && child.name);
    const item = {
      id: child.id,
      name: childName,
      actionId: childAction,
      overviewActionId: null,
      xmlid: menuRecord && menuRecord.xmlid ? menuRecord.xmlid : null,
      showOverviewEntry: false,
      children: [],
      sequence: resolveMenuSequence(child, menuRecord),
    };
    item.showOverviewEntry = shouldShowOverviewEntry(item);
    if (item.showOverviewEntry) {
      item.overviewActionId = OVERVIEW_ACTION_XMLID;
    }
    const sub = resolveChildren(child, menuMap);
    for (const node of sub) {
      const resolved = resolveNodeAction(node, menuMap);
      const entryName = resolveName(node && node.name);
      const sequence = resolveMenuSequence(node, menuMap && menuMap[node.id] ? menuMap[node.id] : node);
      if (resolved.actionId) {
        item.children.push({
          id: node.id,
          name: entryName,
          actionId: resolved.actionId,
          sequence,
        });
        continue;
      }
      if (entryName) {
        item.children.push({
          id: node.id,
          name: entryName,
          actionId: null,
          disabled: true,
          sequence,
        });
      }
    }
    item.children.sort((a, b) => sortBySequenceThenName(a, b, menuMap));
    if (item.actionId || item.children.length) {
      sections.push(item);
    }
  }
  sections.sort((a, b) => sortBySequenceThenName(a, b, menuMap));
  return sections;
}

function shouldShowOverviewEntry(section) {
  if (!SHOW_OVERVIEW) return false;
  if (!section) return false;
  if (section.xmlid && OVERVIEW_MENU_XMLIDS.has(section.xmlid)) return true;
  if (OVERVIEW_MENU_IDS.has(section.id)) return true;
  if (section.name && OVERVIEW_MENU_NAMES.has(section.name)) return true;
  return false;
}

function resolveName(name) {
  if (!name) return "";
  if (typeof name === "string") return name;
  if (typeof name === "object") {
    if (name.zh_CN) return name.zh_CN;
    const keys = Object.keys(name);
    return keys.length ? name[keys[0]] : "";
  }
  return String(name);
}

function shouldFlattenSection(domain, section, isSingleSection) {
  if (!domain || !section) return false;
  if (isSingleSection) return true;
  if (!section.children || !section.children.length) return false;
  const domainName = resolveName(domain.name);
  const sectionName = resolveName(section.name);
  if (domainName && sectionName && domainName === sectionName) return true;
  if (Array.isArray(domain.menu_xmlids) && domain.menu_xmlids.includes(section.xmlid)) return true;
  return false;
}

function findFirstActionFromSections(sections) {
  for (const domain of sections) {
    for (const section of domain.sections) {
      if (section.actionId) return { menuId: section.id, actionId: section.actionId };
      for (const child of section.children) {
        if (child.actionId) return { menuId: child.id, actionId: child.actionId };
      }
    }
  }
  return null;
}

function findSectionById(domains, sectionId) {
  for (const domain of domains) {
    for (const section of domain.sections) {
      if (section.id === sectionId) return section;
    }
  }
  return null;
}

function resolveMenuSequence(node, menuRecord) {
  if (menuRecord && typeof menuRecord.sequence === "number") return menuRecord.sequence;
  if (node && typeof node.sequence === "number") return node.sequence;
  return 0;
}

function sortBySequenceThenName(a, b, menuMap) {
  const seqA = resolveMenuSequence(a, menuMap && menuMap[a.id] ? menuMap[a.id] : a);
  const seqB = resolveMenuSequence(b, menuMap && menuMap[b.id] ? menuMap[b.id] : b);
  if (seqA !== seqB) return seqA - seqB;
  const nameA = resolveName(a && a.name);
  const nameB = resolveName(b && b.name);
  return nameA.localeCompare(nameB, "zh-Hans-CN");
}

function normalizeDomainMap() {
  const map = Array.isArray(DOMAIN_NAV_MAP) ? DOMAIN_NAV_MAP : [];
  const normalized = map
    .map((domain) => ({
      key: domain.key,
      name: domain.name_cn || domain.name || domain.key,
      icon: domain.icon || "",
      sequence: typeof domain.sequence === "number" ? domain.sequence : 0,
      menu_xmlids: Array.isArray(domain.menu_xmlids) ? domain.menu_xmlids : [],
      menu_name_keywords: Array.isArray(domain.menu_name_keywords) ? domain.menu_name_keywords : [],
    }))
    .sort((a, b) => a.sequence - b.sequence);
  return ensureDefaultDomain(normalized);
}

function ensureDefaultDomain(domainMap) {
  const out = Array.isArray(domainMap) ? domainMap.slice() : [];
  if (!out.some((item) => item.key === DEFAULT_DOMAIN_KEY)) {
    out.push({
      key: DEFAULT_DOMAIN_KEY,
      name: "其他",
      icon: "",
      sequence: 9999,
      menu_xmlids: [],
      menu_name_keywords: [],
    });
  }
  return out;
}

function mapSectionToDomain(section, domainMap) {
  if (!section) return null;
  const xmlid = section.xmlid || section.menu_xmlid || "";
  if (xmlid) {
    for (const domain of domainMap) {
      if (domain.menu_xmlids.includes(xmlid)) return domain;
    }
  }
  const name = resolveName(section.name);
  if (name) {
    const hits = [];
    for (const domain of domainMap) {
      if (domain.menu_name_keywords.some((keyword) => name.includes(keyword))) {
        hits.push(domain);
      }
    }
    if (hits.length === 1) return hits[0];
    if (hits.length > 1) {
      console.warn("[sc_sidebar] domain keyword conflict", {
        name,
        xmlid,
        hits: hits.map((hit) => hit.key),
      });
      return null;
    }
  }
  return null;
}

function buildDomainSections(menuSections, menuMap) {
  const domainMap = normalizeDomainMap();
  const buckets = new Map();
  const defaultDomain =
    domainMap.find((item) => item.key === DEFAULT_DOMAIN_KEY) || ensureDefaultDomain([])[0];
  for (const section of menuSections) {
    const domain = mapSectionToDomain(section, domainMap) || defaultDomain;
    if (!buckets.has(domain.key)) {
      buckets.set(domain.key, {
        id: `domain:${domain.key}`,
        key: domain.key,
        name: domain.name,
        icon: domain.icon,
        sequence: domain.sequence,
        sections: [],
        isOpen: false,
      });
    }
    buckets.get(domain.key).sections.push(section);
  }
  const out = Array.from(buckets.values());
  for (const domain of out) {
    domain.sections.sort((a, b) => sortBySequenceThenName(a, b, menuMap));
  }
  out.sort((a, b) => a.sequence - b.sequence);
  return out;
}

function getStorageKey(user, suffix) {
  const userId = getUserId(user);
  const { db, uid } = getSessionKeyParts(userId);
  return {
    key: `sc:${db}:${uid}:sidebar:${suffix}`,
    legacy: suffix,
  };
}

function getSessionKeyParts(userId) {
  const session = window.odoo && window.odoo.session_info ? window.odoo.session_info : {};
  const db = session.db || session.database || "unknown";
  const uid = typeof session.uid === "number" ? session.uid : userId || 0;
  return { db, uid };
}

function getUserId(user) {
  if (!user) return null;
  if (typeof user.userId === "number") return user.userId;
  if (typeof user.uid === "number") return user.uid;
  if (typeof user.id === "number") return user.id;
  return null;
}

function normalizeStorageKey(key) {
  if (!key) return { key: null, legacy: null };
  if (typeof key === "string") return { key, legacy: null };
  if (typeof key === "object" && key.key) return { key: key.key, legacy: key.legacy || null };
  return { key: null, legacy: null };
}

function readStorageValue(key) {
  const { key: storageKey, legacy } = normalizeStorageKey(key);
  if (!storageKey) return null;
  try {
    let raw = window.localStorage.getItem(storageKey);
    if (raw === null && legacy) {
      const legacyValue = window.localStorage.getItem(legacy);
      if (legacyValue !== null) {
        window.localStorage.setItem(storageKey, legacyValue);
        raw = legacyValue;
      }
    }
    return raw;
  } catch (err) {
    return null;
  }
}

function writeStorageValue(key, value) {
  const { key: storageKey } = normalizeStorageKey(key);
  if (!storageKey) return;
  try {
    window.localStorage.setItem(storageKey, value);
  } catch (err) {
    // ignore
  }
}

function loadOpenSectionIds(key) {
  const raw = readStorageValue(key);
  if (!raw) return null;
  try {
    const ids = JSON.parse(raw);
    if (!Array.isArray(ids)) return null;
    return ids
      .map((id) => {
        if (typeof id === "string") return id;
        const parsed = parseInt(id, 10);
        return Number.isFinite(parsed) ? parsed : null;
      })
      .filter((id) => id !== null);
  } catch (err) {
    return null;
  }
}

function saveOpenSectionIds(key, ids) {
  writeStorageValue(key, JSON.stringify(ids || []));
}

function normalizeSearch(term) {
  return (term || "").trim().toLowerCase();
}

function matchesText(text, parts) {
  if (!parts.length) return true;
  const hay = (text || "").toString().toLowerCase();
  return parts.every((part) => hay.includes(part));
}

function highlightLabel(text, parts) {
  if (!text || !parts.length) return [{ text: text || "", match: false }];
  const source = text.toString();
  const lower = source.toLowerCase();
  const ranges = [];
  for (const part of parts) {
    if (!part) continue;
    const needle = part.toLowerCase();
    let start = 0;
    while (start < lower.length) {
      const idx = lower.indexOf(needle, start);
      if (idx === -1) break;
      ranges.push([idx, idx + needle.length]);
      start = idx + needle.length;
    }
  }
  if (!ranges.length) return [{ text: source, match: false }];
  ranges.sort((a, b) => a[0] - b[0]);
  const merged = [];
  for (const [s, e] of ranges) {
    if (!merged.length || s > merged[merged.length - 1][1]) {
      merged.push([s, e]);
    } else {
      merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], e);
    }
  }
  const tokens = [];
  let cursor = 0;
  for (const [s, e] of merged) {
    if (s > cursor) tokens.push({ text: source.slice(cursor, s), match: false });
    tokens.push({ text: source.slice(s, e), match: true });
    cursor = e;
  }
  if (cursor < source.length) tokens.push({ text: source.slice(cursor), match: false });
  return tokens;
}

function getConfigFlag(key, fallback) {
  try {
    const params = new URLSearchParams(window.location.search || "");
    if (params.has(key)) {
      const raw = params.get(key);
      return raw === "1" || raw === "true";
    }
    const stored = window.localStorage.getItem(key);
    if (stored === null) return fallback;
    return stored === "1" || stored === "true";
  } catch (err) {
    return fallback;
  }
}

function loadMenuEntries(key) {
  if (!key) return [];
  const raw = readStorageValue(key);
  if (!raw) return [];
  try {
    const items = JSON.parse(raw);
    if (!Array.isArray(items)) return [];
    return items
      .map((entry) => ({
        menuId: parseInt(entry.menuId, 10),
        actionId: entry.actionId ? parseInt(entry.actionId, 10) : null,
        name: entry.name || "",
      }))
      .filter((entry) => Number.isFinite(entry.menuId));
  } catch (err) {
    return [];
  }
}

function saveMenuEntries(key, entries) {
  if (!key) return;
  writeStorageValue(key, JSON.stringify(entries || []));
}

function addRecentEntry(list, entry, limit) {
  const next = [entry, ...list.filter((item) => item.menuId !== entry.menuId)];
  return next.slice(0, limit);
}

function toggleFavoriteEntry(list, entry, limit) {
  const exists = list.some((item) => item.menuId === entry.menuId);
  if (exists) return list.filter((item) => item.menuId !== entry.menuId);
  const next = [entry, ...list];
  return next.slice(0, limit);
}

function resolveMenuLabel(menuId, index) {
  const item = index && index[menuId];
  return item ? item.name : "";
}

function buildMenuIndex(sections) {
  const index = {};
  for (const domain of sections) {
    for (const section of domain.sections) {
      index[section.id] = { name: section.name, actionId: section.actionId };
      for (const child of section.children) {
        index[child.id] = { name: child.name, actionId: child.actionId };
      }
    }
  }
  return index;
}

function buildPinnedEntries(config, menus, menuMap) {
  const entries = Array.isArray(config) ? config : [];
  return entries
    .map((entry, idx) => {
      if (!entry) return null;
      const key = entry.key || `pinned_${idx}`;
      const name = entry.name || "";
      let menuId = null;
      let actionId = null;
      let disabled = false;
      let menuNode = null;
      if (entry.menu_xmlid) {
        menuNode = findMenuByXmlid(null, menuMap || menus, entry.menu_xmlid);
      }
      if (menuNode) {
        menuId = menuNode.id;
        const resolved = resolveNodeAction(menuNode, menuMap);
        actionId = resolved.actionId;
        disabled = resolved.disabled;
      }
      if (!actionId && entry.action_xmlid) {
        actionId = entry.action_xmlid;
      }
      if (!actionId) disabled = true;
      const href = actionId
        ? menuId
          ? `#menu_id=${menuId}&action=${actionId}`
          : `#action=${actionId}`
        : "#";
      return {
        key,
        name,
        icon: entry.icon || "",
        tag: entry.tag || "",
        menuId,
        actionId,
        href,
        disabled,
      };
    })
    .filter((entry) => entry && entry.name);
}

function getCompanyKey(user) {
  const context = user && user.context ? user.context : null;
  const allowed = context && Array.isArray(context.allowed_company_ids) ? context.allowed_company_ids : null;
  if (allowed && allowed.length) return allowed.join(",");
  const session = window.odoo && window.odoo.__session_info__ ? window.odoo.__session_info__ : null;
  const sessionCtx = session && session.user_context ? session.user_context : null;
  const sessionAllowed = sessionCtx && Array.isArray(sessionCtx.allowed_company_ids) ? sessionCtx.allowed_company_ids : null;
  if (sessionAllowed && sessionAllowed.length) return sessionAllowed.join(",");
  return null;
}

function getAllowedCompanies(user, companyService) {
  const fromService = normalizeCompanies(getCompaniesFromService(companyService));
  if (fromService.length) return fromService;
  const fromSession = normalizeCompanies(getCompaniesFromSession());
  if (fromSession.length) return fromSession;
  const context = user && user.context ? user.context : null;
  const allowed = context && Array.isArray(context.allowed_company_ids) ? context.allowed_company_ids : null;
  if (allowed && allowed.length) {
    return allowed.map((id) => ({ id, name: `公司 ${id}` }));
  }
  return [];
}

function getSelectedCompanyIds(user, companyService, allowedCompanies) {
  const fromHash = getCompanyIdsFromHash();
  if (fromHash.length) return ensureCompanySubset(fromHash, allowedCompanies);
  const fromService = getSelectedCompanyIdsFromService(companyService);
  if (fromService && fromService.length) return ensureCompanySubset(fromService, allowedCompanies);
  const context = user && user.context ? user.context : null;
  const allowed = context && Array.isArray(context.allowed_company_ids) ? context.allowed_company_ids : null;
  if (allowed && allowed.length) return ensureCompanySubset(allowed, allowedCompanies);
  if (allowedCompanies.length) return [allowedCompanies[0].id];
  return [];
}

function getCompaniesFromService(companyService) {
  if (!companyService) return null;
  if (typeof companyService.getCompanies === "function") return companyService.getCompanies();
  if (Array.isArray(companyService.allowedCompanies)) return companyService.allowedCompanies;
  if (Array.isArray(companyService.companies)) return companyService.companies;
  if (companyService.allowedCompanies && typeof companyService.allowedCompanies === "object") {
    return Object.values(companyService.allowedCompanies);
  }
  return null;
}

function getSelectedCompanyIdsFromService(companyService) {
  if (!companyService) return null;
  if (Array.isArray(companyService.currentCompanyIds)) return companyService.currentCompanyIds;
  if (Array.isArray(companyService.allowedCompanyIds)) return companyService.allowedCompanyIds;
  if (Array.isArray(companyService.companyIds)) return companyService.companyIds;
  if (typeof companyService.currentCompanyId === "number") return [companyService.currentCompanyId];
  if (companyService.currentCompany && typeof companyService.currentCompany.id === "number") {
    return [companyService.currentCompany.id];
  }
  return null;
}

function getCompaniesFromSession() {
  const session = window.odoo && window.odoo.__session_info__ ? window.odoo.__session_info__ : null;
  const userCompanies = session && session.user_companies ? session.user_companies : null;
  if (!userCompanies) return null;
  if (Array.isArray(userCompanies.allowed_companies)) return userCompanies.allowed_companies;
  if (Array.isArray(userCompanies.allowedCompanies)) return userCompanies.allowedCompanies;
  if (userCompanies.allowed_companies && typeof userCompanies.allowed_companies === "object") {
    return mapCompaniesObject(userCompanies.allowed_companies);
  }
  if (userCompanies.allowedCompanies && typeof userCompanies.allowedCompanies === "object") {
    return mapCompaniesObject(userCompanies.allowedCompanies);
  }
  return null;
}

function mapCompaniesObject(raw) {
  const out = [];
  for (const [key, value] of Object.entries(raw || {})) {
    const id = parseInt(key, 10);
    if (!Number.isFinite(id)) continue;
    if (typeof value === "string") {
      out.push({ id, name: value });
      continue;
    }
    if (value && typeof value === "object") {
      out.push({ id, name: value.name || value.display_name || `公司 ${id}` });
    }
  }
  return out;
}

function normalizeCompanies(raw) {
  if (!raw) return [];
  const list = Array.isArray(raw) ? raw : Object.values(raw);
  const out = [];
  for (const entry of list) {
    const normalized = normalizeCompanyEntry(entry);
    if (normalized) out.push(normalized);
  }
  return out;
}

function normalizeCompanyEntry(entry) {
  if (!entry) return null;
  if (Array.isArray(entry)) {
    const id = parseInt(entry[0], 10);
    if (!Number.isFinite(id)) return null;
    return { id, name: entry[1] || `公司 ${id}` };
  }
  if (typeof entry === "object") {
    if (typeof entry.id === "number") {
      return { id: entry.id, name: entry.name || entry.display_name || `公司 ${entry.id}` };
    }
  }
  return null;
}

function getCompanyIdsFromHash() {
  const params = parseHashParams();
  if (params.cids) return parseCompanyIds(params.cids);
  if (params.company_id) return parseCompanyIds(params.company_id);
  return [];
}

function parseCompanyIds(raw) {
  if (!raw) return [];
  return raw
    .toString()
    .split(",")
    .map((id) => parseInt(id, 10))
    .filter((id) => Number.isFinite(id));
}

function ensureCompanySubset(ids, allowedCompanies) {
  const allowedSet = new Set((allowedCompanies || []).map((company) => company.id));
  const filtered = normalizeCompanyIds(ids).filter((id) => !allowedSet.size || allowedSet.has(id));
  if (filtered.length) return filtered;
  if (allowedCompanies && allowedCompanies.length) return [allowedCompanies[0].id];
  return [];
}

function normalizeCompanyIds(ids) {
  return Array.from(new Set((ids || []).map((id) => parseInt(id, 10)).filter((id) => Number.isFinite(id)))).sort(
    (a, b) => a - b
  );
}

function buildCompanyLabel(allowedCompanies, selectedIds) {
  if (!allowedCompanies.length) return "公司";
  const selected = allowedCompanies.filter((company) => selectedIds.includes(company.id));
  if (!selected.length) return allowedCompanies[0].name;
  if (selected.length === 1) return selected[0].name;
  return `${selected[0].name} 等${selected.length}家`;
}

function arraysEqual(left, right) {
  if (left.length !== right.length) return false;
  for (let i = 0; i < left.length; i++) {
    if (left[i] !== right[i]) return false;
  }
  return true;
}
