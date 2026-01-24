/** @odoo-module **/

import { FormStatusIndicator } from "@web/views/form/form_status_indicator/form_status_indicator";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(FormStatusIndicator.prototype, {
    get scSaveLabel() {
        const root = this.props?.model?.root;
        const resModel = (root && root.resModel) || this.props?.resModel || "";
        const state = root && root.data ? root.data.lifecycle_state : "";
        if (resModel === "project.project" && state === "draft") {
            return _t("暂存");
        }
        return _t("保存");
    },
    get scDiscardLabel() {
        return _t("放弃变更");
    },
});
