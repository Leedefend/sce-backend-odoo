/** @odoo-module **/

import { Component, onWillStart, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const actionRegistry = registry.category("actions");
const FIELDS = [
    "discipline_id",
    "chapter_id",
    "quota_code",
    "name",
    "uom_id",
    "price_total",
    "price_direct",
    "price_labor",
    "price_material",
    "price_machine",
    "amount_misc",
    "rate_misc",
    "active",
];

export class ProjectQuotaCenter extends Component {
    static template = "project_quota_center.Main";
    static props = {
        action: { type: Object, optional: true },
        actionId: { type: [Number, String], optional: true },
        className: { type: String, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this._searchTimer = null;
        this._isComposing = false;
        this._reqSeq = 0;
        this._lastAppliedKey = "";
        this.listBodyRef = useRef("listBody");
        this.searchInputRef = useRef("searchInput");
        this.state = useState({
            tree: [],
            currentNodeId: null,
            currentNodeLabel: "全部子目",
            searchTerm: "",
            appliedSearchTerm: "",
            onlyActive: true,
            lines: [],
            loading: true,
            error: null,
            selectedLineId: null,
            initialized: false,
            loadingList: false,
            pageSize: 200,
            offset: 0,
            hasMore: true,
            loadingMore: false,
        });

        onWillStart(async () => {
            try {
                console.time("quota.get_quota_tree");
                const nodes = await this.orm.call("project.dictionary", "get_quota_tree", [], {});
                console.timeEnd("quota.get_quota_tree");
                console.log("quota.get_quota_tree nodes:", nodes ? nodes.length : 0);

                console.time("quota.annotateLevels");
                this.state.tree = this._annotateLevels(nodes);
                console.timeEnd("quota.annotateLevels");

                console.time("quota.loadList.init");
                this.state.loading = true;
                this.state.loadingList = true;
                await this.loadList({ force: true });
                console.timeEnd("quota.loadList.init");

                this.state.initialized = true;
            } catch (err) {
                console.error("project_quota_center init error", err);
                this.state.error = err.message || String(err);
            } finally {
                this.state.loading = false;
                this.state.loadingList = false;
            }
        });
    }

    get selectedLine() {
        const id = this.state.selectedLineId;
        const lines = this.state.lines || [];
        if (!id || !lines.length) {
            return null;
        }
        const line = lines.find((l) => l.id === id);
        return line || null;
    }

    _annotateLevels(nodes) {
        const byId = {};
        const children = {};

        for (const raw of nodes) {
            let parentId = raw.parent_id;
            if (Array.isArray(parentId)) {
                parentId = parentId[0];
            }
            parentId = parentId || null;
            byId[raw.id] = { ...raw, parent_id: parentId, level: 1 };
            if (!children[parentId || 0]) {
                children[parentId || 0] = [];
            }
            if (!children[raw.id]) {
                children[raw.id] = [];
            }
        }

        for (const node of Object.values(byId)) {
            if (children[node.parent_id || 0]) {
                children[node.parent_id || 0].push(node.id);
            }
        }

        const roots = Object.values(byId).filter((n) => !n.parent_id || !byId[n.parent_id]);
        const queue = [...roots];
        const visited = new Set();

        while (queue.length) {
            const node = queue.shift();
            if (visited.has(node.id)) {
                continue;
            }
            visited.add(node.id);

            for (const childId of children[node.id] || []) {
                if (childId === node.id) {
                    console.warn("project_quota_center: self-loop detected", byId[childId]);
                    continue;
                }
                const child = byId[childId];
                child.level = node.level + 1;
                queue.push(child);
            }
        }

        for (const node of Object.values(byId)) {
            if (!visited.has(node.id)) {
                console.warn("project_quota_center: cycle suspected", node);
                node.level = node.level || 1;
            }
        }

        return Object.values(byId).sort((a, b) => {
            if (a.level !== b.level) {
                return a.level - b.level;
            }
            return a.id - b.id;
        });
    }

    async onNodeClick(nodeId, nodeLabel) {
        this.state.currentNodeId = nodeId;
        this.state.currentNodeLabel = nodeLabel || "全部子目";
        await this.loadList({ reset: true, force: true });
    }

    onLineClick(line) {
        this.state.selectedLineId = line.id;
    }

    async onLineDblClick(line) {
        this.state.selectedLineId = line.id;
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "project.dictionary",
            res_id: line.id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    _scheduleSearch(term) {
        const normalized = (term || "").trim();
        const prevApplied = this.state.appliedSearchTerm || "";

        this.state.searchTerm = normalized;

        if (normalized === prevApplied) {
            return;
        }

        if (this._searchTimer) {
            clearTimeout(this._searchTimer);
            this._searchTimer = null;
        }

        if (!normalized) {
            if (!prevApplied) {
                return;
            }
            this._searchTimer = setTimeout(async () => {
                await this.loadList({ reset: true, force: true });
            }, 300);
            return;
        }

        if (normalized.length < 2) {
            return;
        }

        this._searchTimer = setTimeout(async () => {
            await this.loadList({ reset: true });
        }, 600);
    }

    onSearchInput(ev) {
        const raw = ev.target.value || "";
        const composingFlag =
            ev.isComposing || this._isComposing || ev.inputType === "insertCompositionText";

        if (composingFlag) {
            return;
        }

        this._scheduleSearch(raw);
    }

    onSearchCompositionStart() {
        this._isComposing = true;
        if (this._searchTimer) {
            clearTimeout(this._searchTimer);
            this._searchTimer = null;
        }
    }

    onSearchCompositionEnd(ev) {
        this._isComposing = false;
        const raw = ev.target.value || "";
        this._scheduleSearch(raw);
    }

    onSearchKeydown(ev) {
        if (ev.isComposing || this._isComposing || ev.keyCode === 229) {
            return;
        }
        if (ev.key !== "Enter") {
            return;
        }
        ev.preventDefault();

        const raw = ev.target.value || "";
        if (this._searchTimer) {
            clearTimeout(this._searchTimer);
            this._searchTimer = null;
        }
        this._scheduleSearch(raw);
    }

    async reloadCurrent() {
        await this.loadList({ reset: true });
    }

    async loadList({ reset = true, force = false } = {}) {
        const seq = ++this._reqSeq;
        const term = (this.state.searchTerm || "").trim();
        const key = JSON.stringify({
            node: this.state.currentNodeId || null,
            term,
            onlyActive: !!this.state.onlyActive,
        });

        try {
            if (!force && key === this._lastAppliedKey && !reset) {
                return;
            }

            if (reset) {
                this.state.offset = 0;
                this.state.hasMore = true;
                this.state.loadingMore = false;
                this.state.lines = [];
                this.state.selectedLineId = null;
            }

            this.state.loadingList = true;
            const finalDomain = await this.orm.call(
                "project.dictionary",
                "get_quota_search_domain",
                [this.state.currentNodeId, term, this.state.onlyActive],
                {}
            );
            if (seq !== this._reqSeq) {
                return;
            }
            console.time("quota.searchRead");
            console.log("quota.searchRead domain:", finalDomain);
            const limit = this.state.pageSize || 200;
            const offset = this.state.offset || 0;
            const lines = await this.orm.searchRead(
                "project.dictionary",
                finalDomain,
                FIELDS,
                { limit, offset, order: "discipline_id, chapter_id, quota_code" }
            );
            if (seq !== this._reqSeq) {
                return;
            }
            console.timeEnd("quota.searchRead");
            console.log("quota.searchRead lines:", lines ? lines.length : 0);
            this._lastAppliedKey = key;
            const chunk = lines || [];
            this.state.lines = reset ? chunk : [...(this.state.lines || []), ...chunk];
            this.state.error = null;
            this.state.appliedSearchTerm = term;

            this.state.hasMore = chunk.length === limit;
            this.state.offset = (offset + chunk.length);

            if (!this.state.lines.length) {
                this.state.selectedLineId = null;
            } else if (!this.state.selectedLineId || !this.state.lines.find((l) => l && l.id === this.state.selectedLineId)) {
                this.state.selectedLineId = this.state.lines[0].id;
            }
        } catch (err) {
            if (seq === this._reqSeq) {
                console.error("project_quota_center load error", err);
                this.state.error = err.message || String(err);
            }
        } finally {
            if (seq === this._reqSeq) {
                this.state.loadingList = false;
            }
        }
    }

    async loadMore() {
        if (this.state.loadingList || this.state.loadingMore || !this.state.hasMore) {
            return;
        }
        this.state.loadingMore = true;
        try {
            await this.loadList({ reset: false, force: true });
        } finally {
            this.state.loadingMore = false;
        }
    }

    onLineClick(line) {
        this.state.selectedLineId = line.id;
    }

    async onLineDblClick(line) {
        this.state.selectedLineId = line.id;
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "project.dictionary",
            res_id: line.id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    onToggleOnlyActive(ev) {
        const checked = ev.target.checked;
        if (checked === this.state.onlyActive) {
            return;
        }
        this.state.onlyActive = checked;
        this.loadList({ reset: true, force: true });
    }

    onKeyDown(ev) {
        if (ev.key === "/" && !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
            ev.preventDefault();
            const el = this.searchInputRef.el;
            if (el) {
                el.focus();
            }
            return;
        }
        if (!this.state.lines.length) {
            return;
        }
        const key = ev.key;
        if (!["ArrowDown", "ArrowUp", "Enter"].includes(key)) {
            return;
        }
        ev.preventDefault();

        const lines = this.state.lines;
        let idx = lines.findIndex((l) => l.id === this.state.selectedLineId);

        if (key === "ArrowDown") {
            idx = idx < 0 ? 0 : Math.min(idx + 1, lines.length - 1);
            const line = lines[idx];
            this.onLineClick(line);
            this._scrollToLine(line.id);
        } else if (key === "ArrowUp") {
            idx = idx < 0 ? 0 : Math.max(idx - 1, 0);
            const line = lines[idx];
            this.onLineClick(line);
            this._scrollToLine(line.id);
        } else if (key === "Enter") {
            if (idx < 0) {
                idx = 0;
            }
            const line = lines[idx];
            this.onLineDblClick(line);
        }
    }

    onListScroll(ev) {
        const el = ev.currentTarget;
        if (!el) {
            return;
        }
        const threshold = 160;
        const remaining = el.scrollHeight - el.scrollTop - el.clientHeight;
        if (remaining < threshold) {
            this.loadMore();
        }
    }

    _scrollToLine(lineId) {
        const container = this.listBodyRef.el;
        if (!container) {
            return;
        }
        const row = container.querySelector(`tr[data-id="${lineId}"]`);
        if (row) {
            row.scrollIntoView({ block: "nearest" });
        }
    }

    _escapeHtml(s) {
        return String(s ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    highlight(text) {
        const raw = String(text ?? "");
        const term = (this.state.searchTerm || "").trim();
        if (!term) {
            return this._escapeHtml(raw);
        }
        const tokens = term.split(/\s+/).filter(Boolean);
        if (!tokens.length) {
            return this._escapeHtml(raw);
        }
        let html = this._escapeHtml(raw);
        for (const t of tokens) {
            const escaped = this._escapeHtml(t);
            if (!escaped) {
                continue;
            }
            const re = new RegExp(escaped.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "ig");
            html = html.replace(re, (m) => `<span class="o_quota_hit">${m}</span>`);
        }
        return html;
    }
}

actionRegistry.add("project_quota_center", ProjectQuotaCenter);
