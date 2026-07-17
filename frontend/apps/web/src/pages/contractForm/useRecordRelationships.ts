/* eslint-disable @typescript-eslint/no-explicit-any */
import type { FieldDescriptor } from '@sc/schema';
import type { RelationOption, RelationSearchColumn, RelationSearchRow } from './types';
import { useRecordRelationshipFields } from './useRecordRelationshipFields';
import { useRecordRelationshipNavigation } from './useRecordRelationshipNavigation';

type RelationshipDependencies = Record<string, any>;

/** Owns relation discovery, access-aware navigation, and inline relation editing. */
export function useRecordRelationships(dependencies: RelationshipDependencies) {
  const { ApiError, actionId, clearedDynamicRelationFields, closeRelationSearchDialog, confirmRelationSearchSelectionFromRuntime, contract, contractFieldLabel, createContractFormRecord, deniedRelationModels, dynamicDomainDependencyFields, dynamicRelationDomainFromDescriptor, ensureOne2manyRows, fallbackRelationSearchColumns, fetchRelationOptionsFromRuntime, fieldModifierMap, fieldType, filteredRelationOptionsFromRuntime, findNativeFieldNodeInTree, formData, formUiLabelFromLabels, formUiLabelsFromFormView, invalidatedRelationKeywords, isWritableFieldVisible, layoutNodes, listContractFormRecords, loadModelContractRaw, markFieldChanged, mergeHydratedOne2manyRecords, mergeRelationDomains, mergeRelationOptions, model, nativeFieldSubviewFromTree, nativeFormLayoutNodes, nativeNodeFieldDescriptorFromNode, normalizeFieldValue, normalizeRelationIds, normalizeRelationSearchColumns, normalizeRouteQueryValues, onchangeModifiersPatch, one2manyCanCreateFromPolicies, one2manyColumnsFromSubview, one2manyCreateLabelFromPolicies, one2manyDraftSummary, one2manyFieldRows, one2manyPrimaryColumnFromColumns, one2manyRowLabelFromPrimary, one2manySubviewPolicies, one2manyValidation, openRelationSearchFromRuntime, pickContractNavQuery, queryRelationOptionsFromRuntime, rawNativeFormLayoutNodes, readContractFormRecord, recordId, relationCreateMode, relationDomainFromDescriptor, relationEntry, relationFieldDescriptors, relationInlineCreate, relationKeyword, relationKeywords, relationModelFromDescriptor, relationOptions, relationOptionsForFieldFromRuntime, relationOptionsFromRecords, relationOrder, relationQueryTimers, relationReadFields, relationSearchColumnsFromContract, relationSearchDialog, relationSearchDialogContract, relationSearchLimit, relationSearchOrder, relationSearchReadFields, relationSearchRowsFromRecords, relationUiLabel, relationUiLabels, reload, route, router, runRelationSearchFromRuntime, runtimeRelationDomainFromModifiers, sanitizeUiErrorMessage, selectOne2manySubview, selectRelationSearchOptionFromRuntime, selectedRelationOptionsFromRuntime, setRelationKeywordValue, validationErrors } = dependencies;
  const {
    relationIds, selectedRelationOptions, many2oneValue, relationOptionsForField, hydrateSelectedRelationOptions,
    one2manyRelationModel, one2manyRelationFieldDescriptor, nativeNodeFieldDescriptor, findNativeFieldNode, effectiveFieldDescriptor,
    mergeNativeLayoutFieldDescriptorsIntoContract, nativeFieldSubview, one2manyColumns, one2manyPolicies, one2manyCanCreate,
    one2manyCreateLabel, one2manyPrimaryColumn, one2manyRowLabel, one2manySummary, hydrateOne2manyRows,
    hydrateVisibleOne2manyRows, one2manyRowErrors,
  } = useRecordRelationshipFields({
    ApiError, contract, contractFieldLabel, deniedRelationModels,
    ensureOne2manyRows, fieldType, findNativeFieldNodeInTree, formData,
    isWritableFieldVisible, mergeHydratedOne2manyRecords, mergeRelationOptions, nativeFieldSubviewFromTree,
    nativeFormLayoutNodes, nativeNodeFieldDescriptorFromNode, normalizeRelationIds, one2manyCanCreateFromPolicies,
    one2manyColumnsFromSubview, one2manyCreateLabelFromPolicies, one2manyDraftSummary, one2manyFieldRows,
    one2manyPrimaryColumnFromColumns, one2manyRowLabelFromPrimary, one2manySubviewPolicies, one2manyValidation,
    rawNativeFormLayoutNodes, readContractFormRecord, relationFieldDescriptors, relationModel,
    relationOptions, relationOptionsForFieldFromRuntime, relationOptionsFromRecords, relationReadFields,
    selectOne2manySubview, selectedRelationOptionsFromRuntime,
  });
  function setRelationKeyword(name: string, keyword: string) {
    setRelationKeywordValue(name, keyword);
    const descriptor = effectiveFieldDescriptor(name);
    const widget = String((descriptor as Record<string, unknown> | undefined)?.widget || '').trim().toLowerCase();
    if (fieldType(descriptor) === 'many2many' && widget === 'many2many_tags') {
      markFieldChanged(name);
    }
    if (relationQueryTimers[name]) {
      clearTimeout(relationQueryTimers[name]);
    }
    relationQueryTimers[name] = setTimeout(() => {
      const currentKeyword = relationKeywords[name] || '';
      void queryRelationOptions(name, currentKeyword);
    }, 260);
  }

  function filteredRelationOptions(name: string) {
    return filteredRelationOptionsFromRuntime(name, formData[name]);
  }

  function relationModel(name: string) {
    return relationModelFromDescriptor(effectiveFieldDescriptor(name));
  }

  function formUiLabels(): Record<string, string> {
    return formUiLabelsFromFormView(contract.value?.views?.form);
  }

  function formUiLabel(key: string) {
    return formUiLabelFromLabels(formUiLabels(), key);
  }

  function dynamicDomainFromDescriptor(descriptor?: FieldDescriptor) {
    return dynamicRelationDomainFromDescriptor({
      descriptor,
      resolveDependencyValue: resolveDynamicDomainDependencyValue,
      normalizeDependencyValue: normalizeFieldValue,
      currentFieldValue: (fieldName) => formData[fieldName],
    });
  }

  function resolveDynamicDomainDependencyValue(valueField: string) {
    const direct = formData[valueField]
      ?? route.query[`default_${valueField}`]
      ?? route.query[valueField];
    if (direct !== undefined && direct !== null && direct !== '') return direct;
    const keyword = relationKeyword(valueField).trim().toLowerCase();
    if (!keyword) return direct;
    const option = (relationOptions.value[valueField] || []).find((item) => {
      const label = item.label.trim().toLowerCase();
      return label === keyword || label.includes(keyword) || keyword.includes(label);
    });
    return option?.id || direct;
  }

  function clearDynamicRelationDependents(changedName: string) {
    const fields = contract.value?.fields || {};
    const changed = String(changedName || '').trim();
    if (!changed) return;
    Object.entries(fields).forEach(([name, descriptor]) => {
      descriptor = effectiveFieldDescriptor(name) || descriptor;
      if (name === changed) return;
      if (!['many2one', 'many2many'].includes(fieldType(descriptor))) return;
      if (!dynamicDomainDependencyFields(descriptor).includes(changed)) return;
      const currentIds = relationIds(name);
      const selectedOption = currentIds.length
        ? (relationOptions.value[name] || []).find((option) => option.id === currentIds[0])
        : null;
      const staleKeyword = relationKeyword(name).trim() || String(selectedOption?.label || '').trim();
      if (staleKeyword) invalidatedRelationKeywords[name] = staleKeyword;
      clearedDynamicRelationFields[name] = true;
      if (fieldType(descriptor) === 'many2many') {
        formData[name] = [];
      } else {
        formData[name] = false;
      }
      if (relationQueryTimers[name]) {
        clearTimeout(relationQueryTimers[name]);
        delete relationQueryTimers[name];
      }
      relationKeywords[name] = '';
      relationOptions.value = {
        ...relationOptions.value,
        [name]: [],
      };
      void queryRelationOptions(name, '');
    });
  }

  function relationDomain(descriptor?: FieldDescriptor) {
    return relationDomainFromDescriptor({
      descriptor,
      dynamicDomain: dynamicDomainFromDescriptor(descriptor),
      routeDefaultType: String(route.query.default_type || '').trim(),
    });
  }

  function runtimeRelationDomain(name: string) {
    return runtimeRelationDomainFromModifiers({
      fieldName: name,
      baseModifiers: fieldModifierMap.value,
      patchModifiers: onchangeModifiersPatch.value,
    });
  }

  function mergedRelationDomain(name: string, descriptor?: FieldDescriptor) {
    return mergeRelationDomains(relationDomain(descriptor), runtimeRelationDomain(name));
  }

  async function queryRelationOptions(name: string, keyword: string): Promise<RelationOption[]> {
    const descriptor = effectiveFieldDescriptor(name);
    const relation = relationModel(name);
    const entry = relationEntry(descriptor);
    const domain = mergedRelationDomain(name, descriptor);
    return queryRelationOptionsFromRuntime({
      fieldName: name,
      keyword,
      relation,
      canRead: entry?.canRead !== false,
      hasDynamicFallback: Boolean(dynamicDomainDependencyFields(descriptor).length || runtimeRelationDomain(name).length),
      currentValue: formData[name],
      isDeniedError: (err) => err instanceof ApiError && (
        err.status === 403 || String(err.reasonCode || '').toUpperCase() === 'PERMISSION_DENIED'
      ),
      fetchOptions: async (search, limit) => {
        const listed = await listContractFormRecords({
          model: relation,
          fields: relationReadFields(descriptor),
          limit,
          order: relationOrder(descriptor),
          domain,
          search_term: search || undefined,
          context: pickContractNavQuery(route.query as Record<string, unknown>),
          silentErrors: true,
        });
        return relationOptionsFromRecords(listed?.records, descriptor);
      },
    });
  }

  async function fetchRelationOptions(name: string, keyword: string, limit = 80): Promise<RelationOption[]> {
    const descriptor = effectiveFieldDescriptor(name);
    const relation = relationModel(name);
    const entry = relationEntry(descriptor);
    const domain = mergedRelationDomain(name, descriptor);
    return fetchRelationOptionsFromRuntime({
      relation,
      canRead: entry?.canRead !== false,
      keyword,
      limit,
      fetchOptions: async (search, limitValue) => {
        const listed = await listContractFormRecords({
          model: relation,
          fields: relationReadFields(descriptor),
          limit: limitValue,
          order: relationOrder(descriptor),
          domain,
          search_term: search || undefined,
          context: pickContractNavQuery(route.query as Record<string, unknown>),
          silentErrors: true,
        });
        return relationOptionsFromRecords(listed?.records, descriptor);
      },
    });
  }

  async function loadRelationSearchColumns(fieldName: string): Promise<RelationSearchColumn[]> {
    const descriptor = effectiveFieldDescriptor(fieldName);
    const contractColumns = relationSearchColumnsFromContract(relationSearchDialogContract(descriptor));
    if (contractColumns.length) return contractColumns;
    const relation = relationModel(fieldName);
    if (!relation) return fallbackRelationSearchColumns(descriptor);
    try {
      const response = await loadModelContractRaw(relation, {
        viewType: 'tree',
        renderProfile: 'readonly',
      });
      const data = response?.data && typeof response.data === 'object'
        ? response.data as Record<string, unknown>
        : response as unknown as Record<string, unknown>;
      return normalizeRelationSearchColumns(data, descriptor);
    } catch {
      return fallbackRelationSearchColumns(descriptor);
    }
  }

  async function fetchRelationSearchRows(name: string, keyword: string, limit = 120): Promise<RelationSearchRow[]> {
    const descriptor = effectiveFieldDescriptor(name);
    const relation = relationModel(name);
    if (!relation) return [];
    const entry = relationEntry(descriptor);
    if (entry && entry.canRead === false) return [];
    const domain = mergedRelationDomain(name, descriptor);
    const dialog = relationSearchDialogContract(descriptor);
    const columns = relationSearchDialog.columns.length ? relationSearchDialog.columns : relationSearchColumnsFromContract(dialog);
    const listed = await listContractFormRecords({
      model: relation,
      fields: relationSearchReadFields(columns.length ? columns : fallbackRelationSearchColumns(descriptor), dialog),
      limit: relationSearchLimit(dialog, limit),
      order: relationSearchOrder(dialog),
      domain,
      search_term: String(keyword || '').trim() || undefined,
      silentErrors: true,
    });
    const records = Array.isArray(listed?.records) ? listed.records : [];
    return relationSearchRowsFromRecords(records, columns);
  }

  function onRelationDialogDocumentKeydown(event: KeyboardEvent) {
    if (!relationSearchDialog.open || event.key !== 'Escape') return;
    event.preventDefault();
    closeRelationSearchDialog();
  }

  async function openRelationSearchDialog(fieldName: string, descriptor?: FieldDescriptor) {
    const relation = relationModel(fieldName);
    if (!relation) return;
    const labels = relationUiLabels(descriptor);
    const resolvedDescriptor = effectiveFieldDescriptor(fieldName);
    await openRelationSearchFromRuntime({
      fieldName,
      descriptor,
      labels,
      keyword: relationKeyword(fieldName),
      columns: relationSearchColumnsFromContract(relationSearchDialogContract(resolvedDescriptor)),
      createMode: relationCreateMode(resolvedDescriptor),
      loadColumns: () => loadRelationSearchColumns(fieldName),
      runSearch: runRelationSearch,
    });
  }

  async function runRelationSearch() {
    await runRelationSearchFromRuntime({
      fetchRows: (fieldName, keyword) => fetchRelationSearchRows(fieldName, keyword, 120),
      sanitizeError: (error, fallback) => sanitizeUiErrorMessage(error instanceof Error ? error.message : error, fallback),
    });
  }

  function confirmRelationSearchSelection(rowArg?: RelationSearchRow) {
    confirmRelationSearchSelectionFromRuntime(selectRelationSearchOption, rowArg);
  }

  function selectRelationSearchOption(option: RelationOption) {
    selectRelationSearchOptionFromRuntime(option, setMany2oneOption);
  }

  function setMany2oneOption(fieldName: string, option: RelationOption) {
    formData[fieldName] = option.id;
    relationKeywords[fieldName] = option.label;
    mergeRelationOptions(fieldName, [option]);
    clearDynamicRelationDependents(fieldName);
    markFieldChanged(fieldName);
    void switchFormByRelationOption(fieldName, option);
  }

  async function switchFormByRelationOption(fieldName: string, option: RelationOption) {
    if (recordId.value) return;
    const descriptor = contract.value?.fields?.[fieldName];
    const entry = relationEntry(descriptor);
    if (!entry?.switchContext?.enabled || !option.switchContext?.code) return;
    const nextCode = option.switchContext.code;
    const currentCode = String(route.query.current_business_category_code || route.query.default_business_category_code || '').trim();
    if (currentCode === nextCode) return;
    const query = normalizeRouteQueryValues(route.query as Record<string, unknown>);
    for (const key of entry.switchContext.defaultClearFields || []) {
      delete query[`default_${key}`];
    }
    query.current_business_category_code = nextCode;
    query.default_business_category_code = nextCode;
    query.current_business_category_label = option.switchContext.label || option.label;
    query.default_business_category_label = option.switchContext.label || option.label;
    query.default_business_category_id = String(option.id);
    query.ctx_source = 'business_category_relation_switch';
    Object.entries(option.switchContext.defaultValues || {}).forEach(([key, value]) => {
      const normalizedKey = String(key || '').trim();
      if (!normalizedKey || value === undefined || value === null) return;
      if (Array.isArray(value) || typeof value === 'object') return;
      query[`default_${normalizedKey}`] = String(value);
    });
    await router.replace({ query });
    await reload();
  }

  async function createRelationFromSearchDialog() {
    const fieldName = relationSearchDialog.fieldName;
    if (!fieldName) return;
    const descriptor = contract.value?.fields?.[fieldName];
    const label = relationSearchDialog.keyword.trim();
    const mode = relationCreateMode(descriptor);
    const exact = label
      ? relationSearchDialog.options.find((item) => item.label.trim().toLowerCase() === label.toLowerCase())
      : null;
    if (exact && mode !== 'page') {
      selectRelationSearchOption(exact);
      return;
    }
    if (mode === 'quick') {
      if (!label) {
        relationSearchDialog.error = relationSearchDialog.labels.missing_name || '';
        return;
      }
      validationErrors.value = [];
      await quickCreateRelation(fieldName, descriptor, label, { stayInDialog: true });
      if (!validationErrors.value.length) {
        closeRelationSearchDialog();
      } else {
        relationSearchDialog.error = validationErrors.value.join('；');
        validationErrors.value = [];
      }
      return;
    }
    closeRelationSearchDialog();
    await openRelationCreateForm(fieldName, descriptor);
  }

  const {
    ensureRelationFieldDescriptors, openRelationCreateForm, currentRelationRecordId, canOpenRelationRecordForm,
    openRelationRecordForm, quickCreateRelation, loadRelationOptions,
  } = useRecordRelationshipNavigation({
    ApiError, actionId, contract, createContractFormRecord,
    deniedRelationModels, fetchRelationOptions, fieldType, formData,
    isWritableFieldVisible, layoutNodes, listContractFormRecords, loadModelContractRaw,
    mergeRelationOptions, mergedRelationDomain, model, normalizeFieldValue,
    one2manyRelationModel, pickContractNavQuery, queryRelationOptions, relationCreateMode,
    relationEntry, relationFieldDescriptors, relationIds, relationInlineCreate,
    relationKeyword, relationModel, relationOptionsFromRecords, relationOrder,
    relationReadFields, relationUiLabel, route, router,
    sanitizeUiErrorMessage, setMany2oneOption, validationErrors,
  });

  return {
    relationIds, selectedRelationOptions, many2oneValue, relationOptionsForField, hydrateSelectedRelationOptions,
    one2manyRelationModel, one2manyRelationFieldDescriptor, nativeNodeFieldDescriptor, findNativeFieldNode, effectiveFieldDescriptor,
    mergeNativeLayoutFieldDescriptorsIntoContract, nativeFieldSubview, one2manyColumns, one2manyPolicies, one2manyCanCreate,
    one2manyCreateLabel, one2manyPrimaryColumn, one2manyRowLabel, one2manySummary, hydrateOne2manyRows,
    hydrateVisibleOne2manyRows, one2manyRowErrors, setRelationKeyword, filteredRelationOptions, relationModel,
    formUiLabels, formUiLabel, dynamicDomainFromDescriptor, resolveDynamicDomainDependencyValue, clearDynamicRelationDependents,
    relationDomain, runtimeRelationDomain, mergedRelationDomain, queryRelationOptions, fetchRelationOptions,
    loadRelationSearchColumns, fetchRelationSearchRows, onRelationDialogDocumentKeydown, openRelationSearchDialog, runRelationSearch,
    confirmRelationSearchSelection, selectRelationSearchOption, setMany2oneOption, switchFormByRelationOption, createRelationFromSearchDialog,
    ensureRelationFieldDescriptors, openRelationCreateForm, currentRelationRecordId, canOpenRelationRecordForm, openRelationRecordForm,
    quickCreateRelation, loadRelationOptions,
  };
}
