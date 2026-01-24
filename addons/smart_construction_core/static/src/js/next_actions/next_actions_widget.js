/** @odoo-module **/

import { Component, onWillStart, useState, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ScNextActionsWidget extends Component {
  static template = xml`
    <div class="sc-next-actions">
      <div class="fw-bold mb-2">建议动作</div>
      <t t-if="state.loading">
        <div class="text-muted">正在生成建议动作…</div>
      </t>
      <t t-elif="!resId">
        <div class="text-muted">保存项目后生成建议动作。</div>
      </t>
      <t t-elif="state.error">
        <div class="text-muted">建议动作生成失败，请稍后重试。</div>
      </t>
      <t t-elif="state.items.length === 0">
        <div class="text-muted">暂无建议动作。</div>
      </t>
      <t t-else="">
        <div class="sc-next-actions__list">
          <t t-foreach="state.items" t-as="item" t-key="item.action_ref + item.name">
            <div class="sc-next-actions__item d-flex align-items-center flex-wrap gap-2">
              <button type="button" class="btn btn-secondary"
                      t-on-click="() => this.onActionClick(item)">
                <t t-esc="item.name"/>
              </button>
              <span class="text-muted" t-if="item.hint" t-esc="item.hint"/>
            </div>
          </t>
        </div>
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
      const items = await this.orm.call(this.model, "sc_get_next_actions", [[resId], this.limit]);
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
      ]);
      if (result) {
        await this.action.doAction(result, { clearBreadcrumbs: false });
      }
      await this.load();
    } catch (err) {
      this.notification.add("执行下一步动作失败，请稍后重试。", { type: "danger" });
    }
  }
}
