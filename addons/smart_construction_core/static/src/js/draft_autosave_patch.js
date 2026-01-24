/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { _t } from "@web/core/l10n/translation";
import { debounce } from "@web/core/utils/timing";
import { patch } from "@web/core/utils/patch";
import { useBus, useService } from "@web/core/utils/hooks";

const originalSetup = FormController.prototype.setup;

patch(FormController.prototype, {
    setup() {
        originalSetup.call(this, ...arguments);
        this.notification = useService("notification");
        this._scAutosaveInFlight = false;
        this._scAutosaveTrigger = debounce(this._scAutosave.bind(this), 1500);
        useBus(this.model.bus, "FIELD_IS_DIRTY", this._scOnDirty.bind(this));
    },

    _scIsDraftProject() {
        const root = this.model?.root;
        if (!root) {
            return false;
        }
        const resModel =
            root.resModel ||
            root.model ||
            root.res_model ||
            root.modelName ||
            this.props?.resModel ||
            this.props?.model ||
            "";
        if (resModel !== "project.project") {
            return false;
        }
        const state = root.data?.lifecycle_state || root.data?.state || "";
        return state === "draft";
    },

    _scAutosaveContext() {
        const base = this.props?.context || this.model?.config?.context || {};
        return { ...base, sc_autosave: 1 };
    },

    _scOnDirty(ev) {
        if (!this._scIsDraftProject()) {
            return;
        }
        if (!ev?.detail) {
            return;
        }
        this._scAutosaveTrigger();
    },

    async _scAutosave() {
        if (!this._scIsDraftProject()) {
            return;
        }
        const root = this.model?.root;
        if (!root || !root.dirty) {
            return;
        }
        if (this._scAutosaveInFlight) {
            return;
        }
        this._scAutosaveInFlight = true;
        try {
            const saved = await this.save({ context: this._scAutosaveContext(), reload: false });
            if (saved) {
                this.notification?.add(_t("草稿已自动保存"), { type: "success" });
            } else {
                this.notification?.add(_t("草稿自动保存失败"), { type: "warning" });
            }
        } catch (err) {
            this.notification?.add(_t("草稿自动保存失败"), { type: "danger" });
        } finally {
            this._scAutosaveInFlight = false;
        }
    },
});
