# 运行态表单结构标准化审计

## 结论摘要

- 扫描 XML form 视图：1086
- 完整 form：1086
- 继承片段：0
- 可直接标准化：157
- 需契约层生成默认页签：484
- 需补语义标注：172
- 需补 XML 主结构：273

本审计通过 Odoo registry 读取运行态合并后的 form arch。

## 分类分布

| classification | views |
| --- | --- |
| contract_auto_with_default_tabs | 484 |
| needs_xml_structure | 273 |
| needs_semantic_annotation | 172 |
| auto_standardizable | 157 |

## 模块分布

| module | views |
| --- | --- |
| runtime | 1086 |

## 可作为标准化输入的样本

| model | xmlid | score | features |
| --- | --- | --- | --- |
| account.move | account.view_move_form | 16 | statusbar,button_box,notebook,chatter |
| account.move | account.view_move_form | 16 | statusbar,button_box,notebook,chatter |
| account.move | account_payment.account_invoice_view_form_inherit_payment | 16 | statusbar,button_box,notebook,chatter |
| account.move | purchase.view_move_form_inherit_purchase | 16 | statusbar,button_box,notebook,chatter |
| account.move | smart_construction_core.view_move_form_sc_cost | 16 | statusbar,button_box,notebook,chatter |
| stock.picking | stock.view_picking_form | 16 | statusbar,button_box,notebook,chatter |
| stock.picking | stock.view_picking_form | 16 | statusbar,button_box,notebook,chatter |
| stock.picking | stock_account.stock_valuation_layer_picking | 16 | statusbar,button_box,notebook,chatter |
| res.partner | account.partner_view_buttons | 15 | button_box,notebook,chatter |
| product.template | account.product_template_form_view | 15 | button_box,notebook,chatter |
| account.journal | account.view_account_journal_form | 15 | button_box,notebook,chatter |
| account.journal | account.view_account_journal_form | 15 | button_box,notebook,chatter |
| account.reconcile.model | account.view_account_reconcile_model_form | 15 | button_box,notebook,chatter |
| account.reconcile.model | account.view_account_reconcile_model_form | 15 | button_box,notebook,chatter |
| res.partner | account.view_partner_property_form | 15 | button_box,notebook,chatter |
| res.partner | account_add_gln.view_partner_form_inherit | 15 | button_box,notebook,chatter |
| res.partner | account_edi_ubl_cii.view_partner_property_form | 15 | button_box,notebook,chatter |
| account.journal | account_payment.view_account_journal_form | 15 | button_box,notebook,chatter |
| res.users | auth_signup.res_users_view_form | 15 | statusbar,button_box,notebook |
| res.users | auth_totp.view_totp_form | 15 | statusbar,button_box,notebook |

## 优先处理缺口样本

| model | xmlid | score | classification | gaps |
| --- | --- | --- | --- | --- |
| stock.quant | stock.duplicated_sn_warning | 2 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter;missing_semantic_anchor |
| account.unreconcile | account.account_unreconcile_view | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| account.unreconcile | account.account_unreconcile_view | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.company | account.res_company_form_view_onboarding_sale_tax | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.company | account.res_company_view_form_terms | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | account.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | account_edi_ubl_cii.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | account_payment.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | auth_signup.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| change.password.wizard | base.change_password_wizard_view | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| change.password.wizard | base.change_password_wizard_view | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| ir.demo_failure.wizard | base.demo_failures_dialog | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| ir.demo_failure.wizard | base.demo_failures_dialog | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| ir.demo | base.demo_force_install_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| ir.demo | base.demo_force_install_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| base.language.install | base.language_install_view_form_lang_switch | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.installer | base.res_config_installer | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.installer | base.res_config_installer | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | base.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | base.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.users.identitycheck | base.res_users_identitycheck_view_form_revokedevices | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| base.module.upgrade | base.view_base_module_upgrade | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| base.module.upgrade | base.view_base_module_upgrade | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| base.module.upgrade | base.view_base_module_upgrade_install | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | base_setup.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | base_tier_validation.res_config_settings_view_form_budget | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | digest.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | google_gmail.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | hr.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | iap.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| mail.resend.message | mail.mail_resend_message_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| mail.resend.message | mail.mail_resend_message_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| mail.template.reset | mail.mail_template_reset_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| mail.template.reset | mail.mail_template_reset_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| mail.template | mail.mail_template_view_form_confirm_delete | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | mail.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | partner_autocomplete.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| res.config.settings | portal.res_config_settings_view_form | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| portal.wizard | portal.wizard_view | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| portal.wizard | portal.wizard_view | 3 | needs_xml_structure | missing_sheet;missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |

## 判定口径

- `auto_standardizable`：已有 `sheet/group/notebook/page`，并带有足够标题或锚点，可直接进入项目式契约标准化。
- `contract_auto_with_default_tabs`：已有主信息区，但缺少 notebook/page，可由契约层生成“主信息/明细/来源追溯/备注”等默认页签。
- `needs_semantic_annotation`：结构基本存在，但缺少标题或 `data-sc-anchor`，建议补少量语义标注。
- `needs_xml_structure`：缺少 `sheet` 或 `group`，契约层难以稳定判断主信息结构，建议先补 XML 主骨架。
- `inherit_fragment`：静态 XML 只是继承补丁，需运行态合并后确认。
