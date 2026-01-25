/** @odoo-module **/

import { Component, onWillStart, useState, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ScStageRequirementsWidget extends Component {
  static template = xml`
    <div class="sc-stage-req">
      <t t-if="state.loading">
        <div class="text-muted">正在加载阶段要求…</div>
      </t>
      <t t-elif="state.error">
        <div class="text-muted">阶段要求加载失败。</div>
      </t>
      <t t-else="">
        <t t-foreach="state.items" t-as="item" t-key="item.title">
          <div class="sc-stage-req__item d-flex align-items-center justify-content-between">
            <div>
              <t t-if="item.done">✓</t>
              <t t-else="">✗</t>
              <span t-esc="item.title"/>
            </div>
            <t t-if="!item.done">
              <button type="button" class="btn btn-link btn-sm"
                      t-on-click="() => this.onActionClick(item)">去完成</button>
            </t>
          </div>
        </t>
      </t>
    </div>
  `;
  static props = {
    model: { type: String, optional: true },
    resId: { type: Number, optional: true },
    limit: { type: Number, optional: true },
  };

  setup() {
    this.orm = useService("orm");
    this.action = useService("action");
    this.notification = useService("notification");
    this.state = useState({ loading: true, items: [], error: null });
    onWillStart(() => this.load());
  }

  get resId() {
    return Number.isFinite(this.props.resId) ? this.props.resId : 0;
  }

  get model() {
    return this.props.model || "project.project";
  }

  get limit() {
    return Number.isFinite(this.props.limit) ? this.props.limit : 3;
  }

  async load() {
    const resId = this.resId;
    this.state.loading = true;
    this.state.error = null;
    this.state.items = [];
    if (!resId) {
      this.state.loading = false;
      return;
    }
    try {
      const items = await this.orm.call(this.model, "sc_get_stage_requirements", [[resId], this.limit]);
      this.state.items = Array.isArray(items) ? items : [];
    } catch (err) {
      this.state.error = err;
    } finally {
      this.state.loading = false;
    }
  }

  async onActionClick(item) {
    if (!item) return;
    try {
      const result = await this.orm.call(this.model, "sc_execute_next_action", [
        [this.resId],
        item.action_type,
        item.action_ref,
        item.payload || {},
      ]);
      if (result) {
        await this.action.doAction(result, { clearBreadcrumbs: false });
      }
    } catch (err) {
      this.notification.add("执行失败，请稍后重试。", { type: "danger" });
    }
  }
}
