/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed, watch } from 'vue';
import type { ContractFieldGovernanceAction, ContractFieldGovernanceRow, LowCodeFieldSize } from './types';

type PresentationDependencies = Record<string, any>;

export function useRecordFormDesignerPresentation(dependencies: PresentationDependencies) {
  const { activeContractMode, applyRuntimeInferredFormColumns, buildFormConfigFieldLabelReplacementEntries, busy, changedFieldGroupFromDrafts, changedFieldVisibilityFromDrafts, contract, contractActionRuleClientMode, contractActionRuleControl, contractActionRuleKey, contractFieldLabel, contractV2ActionRules, effectiveFieldGroupTitleFromDrafts, fieldGroupBase, fieldGroupDraft, fieldGroupSavedBase, fieldLayoutDirtyKeys, fieldMoveTargetDraft, fieldOrderDraft, fieldOrderPreviewActive, fieldSizeBase, fieldSizeDraft, fieldVisibilityBase, fieldVisibilityDirty, fieldVisibilityDirtyKeys, fieldVisibilityDraft, formConfigAuditResult, formConfigFieldLabelCache, formLayoutColumnsBase, formLayoutColumnsConfigured, formLayoutColumnsDraft, formLayoutDirty, formSettingsActiveTab, formatFormConfigOperationSummaryText, groupColumnsBase, groupColumnsDraft, groupLayoutDirtyKeys, groupVisibilityBase, groupVisibilityDraft, hydrateLowCodeDraftFromContract, isContractFieldOrderEditable, isSuggestedInternalFormField, loadLowCodeContractList, lowCodeContractLoaded, lowCodeFormLayoutBase, nativeFormDesignFieldKeys, nativeFormDesignFieldLabels, normalizeFieldGroupTitle, parseMaybeJsonRecord, refreshLowCodeFormLayoutBase, resolveFormDesignFieldLabel, selectedFormSettingsFieldGroupTitleDraft, selectedFormSettingsFieldKey, selectedFormSettingsFieldLabel, selectedFormSettingsOrderTargetKey, v2ContractStore } = dependencies;
  const contractModeBaseFieldRows = computed<ContractFieldGovernanceRow[]>(() => {
    const mode = activeContractMode.value;
    if (!mode) return [];
    const rows = new Map<string, ContractFieldGovernanceRow>();
    contractV2ActionRules.value.forEach((rule) => {
      const sourceWidgetId = String(rule.sourceWidgetId || rule.source_widget_id || '').trim();
      if (!sourceWidgetId.startsWith('field.')) return;
      const expectedMode = contractActionRuleClientMode(rule);
      if (expectedMode && expectedMode !== mode) return;
      const fieldKey = sourceWidgetId.slice('field.'.length);
      if (!fieldKey) return;
      const control = contractActionRuleControl(rule);
      const target = parseMaybeJsonRecord(rule.target);
      const params = parseMaybeJsonRecord(target.params || rule.params);
      const fieldLabel = String(params.label || fieldKey).trim();
      const action: ContractFieldGovernanceAction = {
        key: contractActionRuleKey(rule),
        label: String(control.label || rule.label || contractActionRuleKey(rule)).trim(),
        value: String(control.value || contractActionRuleKey(rule)).trim(),
        checked: control.checked === true,
        disabled: control.disabled === true || busy.value,
        title: String(control.title || '').trim(),
        raw: rule,
      };
      if (!rows.has(fieldKey)) {
        rows.set(fieldKey, { fieldKey, label: fieldLabel, actions: [] });
      }
      rows.get(fieldKey)?.actions.push(action);
    });
    return Array.from(rows.values())
      .map((row) => ({
        ...row,
        actions: row.actions.sort((left, right) => {
          const order = (value: string) => (value === 'show' ? 0 : value === 'hide' ? 1 : 2);
          return order(left.value) - order(right.value) || left.label.localeCompare(right.label);
        }),
      }));
  });

  const activeContractModeFieldRows = computed<ContractFieldGovernanceRow[]>(() => {
    const computedRows = contractModeBaseFieldRows.value;
    const rowsWithDraftVisibility = computedRows.map((row) => ({
      ...row,
      actions: row.actions.map((action) => ({
        ...action,
        checked: Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, row.fieldKey)
          ? fieldVisibilityDraft[row.fieldKey] === (action.value === 'show')
          : action.checked,
      })),
    }));
    if (!isContractFieldOrderEditable.value || !fieldOrderDraft.value.length) return rowsWithDraftVisibility;
    const rank = new Map<string, number>(fieldOrderDraft.value.map((key: string, index: number) => [key, index]));
    return rowsWithDraftVisibility.sort((left, right) => (rank.get(left.fieldKey) ?? 9999) - (rank.get(right.fieldKey) ?? 9999));
  });

  watch(contractModeBaseFieldRows, (rows) => {
    const keys = rows.map((row) => row.fieldKey);
    if (!isContractFieldOrderEditable.value || !keys.length) {
      fieldOrderDraft.value = [];
      fieldVisibilityBase.value = {};
      fieldGroupBase.value = {};
      fieldGroupSavedBase.value = {};
      formLayoutColumnsBase.value = 3;
      formLayoutColumnsDraft.value = 3;
      formLayoutColumnsConfigured.value = false;
      groupVisibilityBase.value = {};
      Object.keys(groupVisibilityDraft).forEach((key) => delete groupVisibilityDraft[key]);
      groupColumnsBase.value = {};
      Object.keys(groupColumnsDraft).forEach((key) => delete groupColumnsDraft[key]);
      fieldSizeBase.value = {};
      Object.keys(fieldSizeDraft).forEach((key) => delete fieldSizeDraft[key]);
      formLayoutDirty.value = false;
      Object.keys(groupLayoutDirtyKeys).forEach((key) => delete groupLayoutDirtyKeys[key]);
      Object.keys(fieldLayoutDirtyKeys).forEach((key) => delete fieldLayoutDirtyKeys[key]);
      lowCodeFormLayoutBase.value = [];
      Object.keys(fieldGroupDraft).forEach((key) => delete fieldGroupDraft[key]);
      Object.keys(fieldMoveTargetDraft).forEach((key) => delete fieldMoveTargetDraft[key]);
      return;
    }
    if (!fieldOrderDraft.value.length) {
      fieldOrderDraft.value = [...keys];
      return;
    }
    const inRows = new Set(keys);
    const kept = fieldOrderDraft.value.filter((key) => inRows.has(key));
    const missing = keys.filter((key) => !kept.includes(key));
    fieldOrderDraft.value = [...kept, ...missing];
    const nextVisibilityBase = { ...fieldVisibilityBase.value };
    rows.forEach((row) => {
      const selected = row.actions.find((action) => Boolean(action.checked));
      if (!selected) return;
      const visible = selected.value === 'show';
      if (!Object.prototype.hasOwnProperty.call(nextVisibilityBase, row.fieldKey)) {
        nextVisibilityBase[row.fieldKey] = visible;
      }
      if (!Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, row.fieldKey)) {
        fieldVisibilityDraft[row.fieldKey] = visible;
      }
    });
    fieldVisibilityBase.value = nextVisibilityBase;
  }, { immediate: true });

  watch(isContractFieldOrderEditable, (enabled) => {
    if (!enabled) {
      lowCodeContractLoaded.value = false;
      selectedFormSettingsFieldKey.value = '';
      selectedFormSettingsFieldLabel.value = '';
      selectedFormSettingsFieldGroupTitleDraft.value = '';
      fieldVisibilityDirty.value = false;
      formConfigAuditResult.value = null;
      return;
    }
    formSettingsActiveTab.value = 'fields';
    syncFieldOrderDraftWithDesignKeys();
    void loadLowCodeContractList();
    void hydrateLowCodeDraftFromContract();
    void refreshLowCodeFormLayoutBase();
  }, { immediate: true });

  watch(
    () => [v2ContractStore.value, contract.value, isContractFieldOrderEditable.value],
    () => {
      applyRuntimeInferredFormColumns();
    },
    { flush: 'post' },
  );

  const currentFormDesignFieldKeys = computed(() => {
    const keys = new Set<string>();
    contractModeBaseFieldRows.value.forEach((row) => {
      if (row.fieldKey) keys.add(row.fieldKey);
    });
    nativeFormDesignFieldKeys.value.forEach((fieldKey) => {
      if (fieldKey) keys.add(fieldKey);
    });
    return Array.from(keys);
  });

  const currentFormOrderedFieldKeys = computed(() => {
    const baseKeys = currentFormDesignFieldKeys.value;
    if (!fieldOrderDraft.value.length) return baseKeys;
    const baseSet = new Set(baseKeys);
    const ordered = fieldOrderDraft.value.filter((fieldKey) => baseSet.has(fieldKey));
    const missing = baseKeys.filter((fieldKey) => !ordered.includes(fieldKey));
    return [...ordered, ...missing];
  });

  const selectedFormSettingsOrderTargetOptions = computed(() => {
    const selectedFieldKey = selectedFormSettingsFieldKey.value;
    return currentFormOrderedFieldKeys.value
      .filter((fieldKey) => fieldKey && fieldKey !== selectedFieldKey)
      .map((fieldKey) => ({
        fieldKey,
        label: formDesignFieldLabel(fieldKey),
      }));
  });

  watch([selectedFormSettingsFieldKey, selectedFormSettingsOrderTargetOptions], () => {
    if (!selectedFormSettingsFieldKey.value) {
      selectedFormSettingsOrderTargetKey.value = '';
      return;
    }
    const options = selectedFormSettingsOrderTargetOptions.value;
    if (!options.length) {
      selectedFormSettingsOrderTargetKey.value = '';
      return;
    }
    if (!options.some((option) => option.fieldKey === selectedFormSettingsOrderTargetKey.value)) {
      const selectedIndex = currentFormOrderedFieldKeys.value.indexOf(selectedFormSettingsFieldKey.value);
      const preferred = currentFormOrderedFieldKeys.value[selectedIndex + 1]
        || currentFormOrderedFieldKeys.value[selectedIndex - 1]
        || options[0].fieldKey;
      selectedFormSettingsOrderTargetKey.value = options.some((option) => option.fieldKey === preferred)
        ? preferred
        : options[0].fieldKey;
    }
  }, { immediate: true });

  function syncFieldOrderDraftWithDesignKeys(rawKeys = currentFormDesignFieldKeys.value) {
    if (!isContractFieldOrderEditable.value) return;
    const keys = Array.from(new Set(rawKeys.map((key) => String(key || '').trim()).filter(Boolean)));
    if (!keys.length) return;
    if (!fieldOrderPreviewActive.value) {
      const same = keys.length === fieldOrderDraft.value.length
        && keys.every((key, index) => fieldOrderDraft.value[index] === key);
      if (!same) fieldOrderDraft.value = keys;
      return;
    }
    const keySet = new Set(keys);
    const kept = fieldOrderDraft.value.filter((key) => keySet.has(key));
    const missing = keys.filter((key) => !kept.includes(key));
    fieldOrderDraft.value = [...kept, ...missing];
  }

  watch(currentFormDesignFieldKeys, (keys) => {
    syncFieldOrderDraftWithDesignKeys(keys);
    if (isContractFieldOrderEditable.value && keys.length && !lowCodeContractLoaded.value) {
      void hydrateLowCodeDraftFromContract();
    }
    if (isContractFieldOrderEditable.value && keys.length) {
      void refreshLowCodeFormLayoutBase();
    }
  }, { immediate: true });

  const hasFieldOrderChanges = computed(() => {
    if (!fieldOrderPreviewActive.value) return false;
    const rows = currentFormDesignFieldKeys.value;
    if (!rows.length || !fieldOrderDraft.value.length) return false;
    return rows.some((key, index) => fieldOrderDraft.value[index] !== key);
  });

  const formVisibilityDraftFieldKeys = computed(() => Array.from(new Set([
    ...currentFormDesignFieldKeys.value,
    ...Object.keys(fieldVisibilityDraft),
    ...Object.keys(fieldVisibilityBase.value),
  ].map((key) => String(key || '').trim()).filter(Boolean))));

  const hasFieldVisibilityChanges = computed(() => formVisibilityDraftFieldKeys.value.some((fieldKey) => {
    if (!Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)) return false;
    if (!Object.prototype.hasOwnProperty.call(fieldVisibilityBase.value, fieldKey)) return false;
    return fieldVisibilityDraft[fieldKey] !== fieldVisibilityBase.value[fieldKey];
  }));

  const hasFieldGroupChanges = computed(() => Object.keys(fieldGroupDraft).some((fieldKey) => {
    const draft = effectiveFieldGroupTitleForDraft(fieldKey);
    const base = normalizeFieldGroupTitle(fieldGroupSavedBase.value[fieldKey] || fieldGroupBase.value[fieldKey]);
    return Boolean(draft) && draft !== base;
  }));

  function effectiveGroupVisible(title: string) {
    const key = normalizeFieldGroupTitle(title);
    if (!key) return true;
    if (Object.prototype.hasOwnProperty.call(groupVisibilityDraft, key)) return groupVisibilityDraft[key] !== false;
    if (Object.prototype.hasOwnProperty.call(groupVisibilityBase.value, key)) return groupVisibilityBase.value[key] !== false;
    return true;
  }

  function effectiveGroupColumns(title: string): 1 | 2 | 3 {
    const key = normalizeFieldGroupTitle(title);
    if (!key) return formLayoutColumnsDraft.value;
    return groupColumnsDraft[key] || groupColumnsBase.value[key] || formLayoutColumnsDraft.value;
  }

  function effectiveFieldSize(fieldKey: string): LowCodeFieldSize {
    const key = String(fieldKey || '').trim();
    if (!key) return 'normal';
    return fieldSizeDraft[key] || fieldSizeBase.value[key] || 'normal';
  }

  const hasFormLayoutChanges = computed(() => formLayoutDirty.value);

  const hasGroupLayoutChanges = computed(() => Object.keys(groupLayoutDirtyKeys).length > 0);

  const hasFieldLayoutChanges = computed(() => Object.keys(fieldLayoutDirtyKeys).length > 0);

  const hasCurrentFormFieldDraftChanges = computed(() => (
    hasFieldOrderChanges.value
    || hasFieldVisibilityChanges.value
    || hasFieldGroupChanges.value
    || hasFormLayoutChanges.value
    || hasGroupLayoutChanges.value
    || hasFieldLayoutChanges.value
    || fieldVisibilityDirty.value
  ));

  function formConfigFieldLabelReplacementEntries() {
    return buildFormConfigFieldLabelReplacementEntries({
      cachedLabels: formConfigFieldLabelCache,
      nativeLabels: nativeFormDesignFieldLabels.value,
      activeRows: activeContractModeFieldRows.value,
      fieldKeys: currentFormDesignFieldKeys.value,
      resolveContractLabel: (fieldKey) => contractFieldLabel(fieldKey),
      resolveDescriptorLabel: (fieldKey) => {
        const descriptor = contract.value?.fields?.[fieldKey] as Record<string, unknown> | undefined;
        return String(descriptor?.string || descriptor?.label || '').trim();
      },
    });
  }

  function formatFormConfigOperationSummary(summary: string) {
    return formatFormConfigOperationSummaryText(summary, formConfigFieldLabelReplacementEntries());
  }

  function formDesignFieldLabel(fieldKey: string) {
    return resolveFormDesignFieldLabel({
      fieldKey,
      selectedFieldKey: selectedFormSettingsFieldKey.value,
      selectedFieldLabel: selectedFormSettingsFieldLabel.value,
      cachedLabels: formConfigFieldLabelCache,
      nativeLabels: nativeFormDesignFieldLabels.value,
      activeRows: activeContractModeFieldRows.value,
      resolveContractLabel: (key) => contractFieldLabel(key),
      resolveDescriptorLabel: (key) => {
        const descriptor = contract.value?.fields?.[key] as Record<string, unknown> | undefined;
        return String(descriptor?.string || descriptor?.label || '').trim();
      },
    });
  }

  function rememberFormConfigFieldLabel(fieldKey: string, label: string) {
    const key = String(fieldKey || '').trim();
    const normalizedLabel = String(label || '').trim();
    if (!key || !normalizedLabel || normalizedLabel === key) return;
    formConfigFieldLabelCache[key] = normalizedLabel;
  }

  const suggestedHiddenFieldRows = computed(() => currentFormDesignFieldKeys.value
    .map((fieldKey) => ({ fieldKey, label: formDesignFieldLabel(fieldKey) }))
    .filter((row) => {
      if (!isSuggestedInternalFormField(row.fieldKey, row.label)) return false;
      return fieldVisibilityDraft[row.fieldKey] !== false;
    }));

  watch(hasCurrentFormFieldDraftChanges, (changed) => {
    if (changed) formConfigAuditResult.value = null;
  });

  function changedFieldVisibilityDraft() {
    return changedFieldVisibilityFromDrafts({
      fieldKeys: formVisibilityDraftFieldKeys.value,
      draft: fieldVisibilityDraft,
      base: fieldVisibilityBase.value,
      dirtyKeys: fieldVisibilityDirtyKeys,
    });
  }

  function changedFieldGroupDraft() {
    return changedFieldGroupFromDrafts({
      draftGroups: fieldGroupDraft,
      nativeBaseGroups: fieldGroupBase.value,
      savedBaseGroups: fieldGroupSavedBase.value,
      resolveDraftTitle: effectiveFieldGroupTitleForDraft,
    });
  }

  function effectiveFieldGroupTitleForDraft(fieldKey: string) {
    return effectiveFieldGroupTitleFromDrafts({
      fieldKey,
      draftGroups: fieldGroupDraft,
      nativeBaseGroups: fieldGroupBase.value,
      savedBaseGroups: fieldGroupSavedBase.value,
    });
  }


  return {
    contractModeBaseFieldRows,
    activeContractModeFieldRows,
    currentFormDesignFieldKeys,
    currentFormOrderedFieldKeys,
    selectedFormSettingsOrderTargetOptions,
    syncFieldOrderDraftWithDesignKeys,
    hasFieldOrderChanges,
    formVisibilityDraftFieldKeys,
    hasFieldVisibilityChanges,
    hasFieldGroupChanges,
    effectiveGroupVisible,
    effectiveGroupColumns,
    effectiveFieldSize,
    hasFormLayoutChanges,
    hasGroupLayoutChanges,
    hasFieldLayoutChanges,
    hasCurrentFormFieldDraftChanges,
    formConfigFieldLabelReplacementEntries,
    formatFormConfigOperationSummary,
    formDesignFieldLabel,
    rememberFormConfigFieldLabel,
    suggestedHiddenFieldRows,
    changedFieldVisibilityDraft,
    changedFieldGroupDraft,
    effectiveFieldGroupTitleForDraft,
  };
}
