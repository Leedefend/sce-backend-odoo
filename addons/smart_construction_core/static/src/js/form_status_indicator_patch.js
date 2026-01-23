/** @odoo-module **/

import { FormStatusIndicator } from "@web/views/form/form_status_indicator/form_status_indicator";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(FormStatusIndicator.prototype, {
    get scSaveLabel() {
        return _t("保存");
    },
    get scDiscardLabel() {
        return _t("放弃变更");
    },
});
