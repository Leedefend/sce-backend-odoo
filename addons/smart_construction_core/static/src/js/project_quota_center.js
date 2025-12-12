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
        this.listBodyRef = useRef("listBody");
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
                await this.loadList();
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
        await this.loadList();
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
                await this.reloadCurrent();
                this.state.appliedSearchTerm = "";
            }, 300);
            return;
        }

        if (normalized.length < 2) {
            return;
        }

        this._searchTimer = setTimeout(async () => {
            await this.reloadCurrent();
            this.state.appliedSearchTerm = this.state.searchTerm || "";
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
        await this.loadList();
    }

    async loadList() {
        try {
            this.state.loadingList = true;
            const finalDomain = await this.orm.call(
                "project.dictionary",
                "get_quota_search_domain",
                [this.state.currentNodeId, this.state.searchTerm, this.state.onlyActive],
                {}
            );
            console.time("quota.searchRead");
            console.log("quota.searchRead domain:", finalDomain);
            const lines = await this.orm.searchRead(
                "project.dictionary",
                finalDomain,
                FIELDS,
                { limit: 200, order: "discipline_id, chapter_id, quota_code" }
            );
            console.timeEnd("quota.searchRead");
            console.log("quota.searchRead lines:", lines ? lines.length : 0);
            this.state.lines = lines;
            this.state.error = null;
            this.state.appliedSearchTerm = this.state.searchTerm || "";

            if (!lines.length) {
                this.state.selectedLineId = null;
            } else if (!lines.find((l) => l.id === this.state.selectedLineId)) {
                this.state.selectedLineId = lines[0].id;
            }
        } catch (err) {
            console.error("project_quota_center load error", err);
            this.state.error = err.message || String(err);
        } finally {
            this.state.loadingList = false;
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
        this.reloadCurrent();
    }

    onKeyDown(ev) {
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
}

actionRegistry.add("project_quota_center", ProjectQuotaCenter);
