/* eslint-disable @typescript-eslint/no-explicit-any */
import type { FieldDescriptor } from '@sc/schema';
import type { RelationOption } from './types';

type NavigationDependencies = Record<string, any>;

export function useRecordRelationshipNavigation(dependencies: NavigationDependencies) {
  const { ApiError, actionId, contract, createContractFormRecord, deniedRelationModels, fetchRelationOptions, fieldType, formData, isWritableFieldVisible, layoutNodes, listContractFormRecords, loadModelContractRaw, mergeRelationOptions, mergedRelationDomain, model, normalizeFieldValue, one2manyRelationModel, pickContractNavQuery, queryRelationOptions, relationCreateMode, relationEntry, relationFieldDescriptors, relationIds, relationInlineCreate, relationKeyword, relationModel, relationOptionsFromRecords, relationOrder, relationReadFields, relationUiLabel, route, router, sanitizeUiErrorMessage, setMany2oneOption, validationErrors } = dependencies;
  async function ensureRelationFieldDescriptors(name: string) {
    const relation = one2manyRelationModel(name);
    if (!relation) return;
    if (relationFieldDescriptors.value[relation]) return;
    try {
      const response = await loadModelContractRaw(relation, {
        viewType: 'form',
        renderProfile: 'edit',
      });
      const fields = response?.data?.fields;
      if (fields && typeof fields === 'object') {
        relationFieldDescriptors.value = {
          ...relationFieldDescriptors.value,
          [relation]: fields as Record<string, FieldDescriptor>,
        };
      }
    } catch {
      // best effort; fallback to char fields
    }
  }

  async function openRelationCreateForm(fieldName: string, descriptor?: FieldDescriptor) {
    const relation = String((descriptor as Record<string, unknown> | undefined)?.relation || '').trim();
    if (!relation) return;
    const mode = relationCreateMode(descriptor);
    if (mode === 'none') {
      validationErrors.value = [relationUiLabel(descriptor, 'missing_create_entry')];
      return;
    }
    if (mode === 'quick') {
      const currentKeyword = relationKeyword(fieldName).trim();
      if (!currentKeyword) {
        validationErrors.value = [relationUiLabel(descriptor, 'missing_name', relationUiLabel(descriptor, 'quick_create_prompt', '请先输入要新增的名称'))];
        return;
      }
      await quickCreateRelation(fieldName, descriptor, currentKeyword);
      return;
    }
    const entry = relationEntry(descriptor);
    const relationActionId = entry?.actionId || null;
    const menuId = entry?.menuId || 0;
    if (!relationActionId) {
      validationErrors.value = [relationUiLabel(descriptor, 'missing_page_entry')];
      return;
    }
    const defaultQuery = Object.entries(entry?.defaultVals || {}).reduce<Record<string, unknown>>((acc, [key, value]) => {
      if (!key) return acc;
      acc[`default_${key}`] = value;
      return acc;
    }, {});
    Object.entries(entry?.defaultFromFields || {}).forEach(([targetField, sourceFieldRaw]) => {
      const sourceField = String(sourceFieldRaw || '').trim();
      if (!targetField || !sourceField) return;
      const value = normalizeFieldValue(sourceField, formData[sourceField]);
      if (value === undefined || value === null || value === '') return;
      defaultQuery[`default_${targetField}`] = value;
    });
    const nextQuery = pickContractNavQuery(route.query as Record<string, unknown>, {
      action_id: relationActionId,
      menu_id: menuId || undefined,
      view_mode: 'form',
      ...defaultQuery,
    });
    const returnUrl = `${window.location.pathname}${window.location.search}`;
    try {
      await router.push({
        name: 'model-form',
        params: { model: relation, id: 'new' },
        query: {
          ...nextQuery,
          return_url: encodeURIComponent(returnUrl),
          return_field: fieldName,
          return_model: model.value,
          return_action_id: actionId.value || undefined,
          return_menu_id: Number(route.query.menu_id || 0) || undefined,
        },
      });
    } catch (err) {
      validationErrors.value = [sanitizeUiErrorMessage(err instanceof Error ? err.message : err, relationUiLabel(descriptor, 'create_page_failed'))];
    }
  }

  function currentRelationRecordId(fieldName: string) {
    const id = Number(relationIds(fieldName)[0] || 0);
    return Number.isFinite(id) && id > 0 ? Math.trunc(id) : 0;
  }

  function canOpenRelationRecordForm(fieldName: string, descriptor?: FieldDescriptor) {
    const relation = relationModel(fieldName);
    const entry = relationEntry(descriptor);
    return Boolean(relation && currentRelationRecordId(fieldName) > 0 && entry?.canRead !== false && entry?.canOpen !== false);
  }

  async function openRelationRecordForm(fieldName: string, descriptor?: FieldDescriptor) {
    const relation = relationModel(fieldName);
    const recordId = currentRelationRecordId(fieldName);
    const entry = relationEntry(descriptor);
    if (!relation || recordId <= 0) return;
    if (entry?.canRead === false) {
      validationErrors.value = [relationUiLabel(descriptor, 'missing_read_entry')];
      return;
    }
    const relationActionId = entry?.actionId || null;
    const menuId = entry?.menuId || 0;
    const nextQuery = pickContractNavQuery(route.query as Record<string, unknown>, {
      action_id: relationActionId || undefined,
      menu_id: menuId || undefined,
      view_mode: 'form',
    });
    const returnUrl = `${window.location.pathname}${window.location.search}`;
    try {
      await router.push({
        name: 'model-form',
        params: { model: relation, id: String(recordId) },
        query: {
          ...nextQuery,
          return_url: encodeURIComponent(returnUrl),
          return_field: fieldName,
          return_model: model.value,
          return_action_id: actionId.value || undefined,
          return_menu_id: Number(route.query.menu_id || 0) || undefined,
        },
      });
    } catch (err) {
      validationErrors.value = [sanitizeUiErrorMessage(err instanceof Error ? err.message : err, relationUiLabel(descriptor, 'open_record_failed'))];
    }
  }

  async function quickCreateRelation(
    fieldName: string,
    descriptor: FieldDescriptor | undefined,
    label: string,
    options: { stayInDialog?: boolean } = {},
  ) {
    const relation = String((descriptor as Record<string, unknown> | undefined)?.relation || '').trim();
    if (!relation) return;
    const entry = relationEntry(descriptor);
    try {
      const existing = await fetchRelationOptions(fieldName, label, 20);
      const exact = existing.find((item) => item.label.trim().toLowerCase() === label.trim().toLowerCase());
      if (exact) {
        setMany2oneOption(fieldName, exact);
        return;
      }
      const inline = relationInlineCreate(descriptor);
      const nameField = inline.nameField || 'name';
      const vals: Record<string, unknown> = { ...(entry?.defaultVals || {}), [nameField]: label };
      const created = await createContractFormRecord({ model: relation, vals });
      const id = Number(created?.id || 0);
      if (Number.isFinite(id) && id > 0) {
        const option = { id: Math.trunc(id), label };
        setMany2oneOption(fieldName, option);
        if (!options.stayInDialog) await queryRelationOptions(fieldName, label);
      }
    } catch (err) {
      const message = sanitizeUiErrorMessage(err instanceof Error ? err.message : err, relationUiLabel(descriptor, 'quick_create_failed'));
      validationErrors.value = [message];
    }
  }

  async function loadRelationOptions() {
    const fields = contract.value?.fields || {};
    const visibleRelationFields = new Set(
      layoutNodes.value
        .filter((node) => node.kind === 'field' && isWritableFieldVisible(node.name))
        .map((node) => node.name),
    );
    const entries = Object.entries(fields).filter(([name]) => {
      if (!visibleRelationFields.size) return relationIds(name).length > 0;
      if (visibleRelationFields.has(name)) return true;
      return relationIds(name).length > 0;
    });
    const one2manyNames = entries
      .filter(([, descriptor]) => fieldType(descriptor) === 'one2many')
      .map(([name]) => name);
    await Promise.all(one2manyNames.map((name) => ensureRelationFieldDescriptors(name)));
    const next: Record<string, RelationOption[]> = {};
    await Promise.all(entries.map(async ([name, descriptor]) => {
      if (!descriptor || typeof descriptor !== 'object') return;
      const type = fieldType(descriptor);
      if (!['many2one', 'many2many', 'one2many'].includes(type)) return;
      const relation = String((descriptor as Record<string, unknown>).relation || '').trim();
      if (!relation) return;
      const entry = relationEntry(descriptor as FieldDescriptor);
      if (entry && entry.canRead === false) {
        deniedRelationModels.add(relation);
        next[name] = [];
        return;
      }
      if (deniedRelationModels.has(relation)) {
        next[name] = [];
        return;
      }
      const domain = mergedRelationDomain(name, descriptor as FieldDescriptor);
      try {
        const listed = await listContractFormRecords({
          model: relation,
          fields: relationReadFields(descriptor as FieldDescriptor),
          limit: 80,
          order: relationOrder(descriptor as FieldDescriptor),
          domain,
          silentErrors: true,
        });
        next[name] = relationOptionsFromRecords(listed?.records, descriptor as FieldDescriptor);
      } catch (err) {
        if (err instanceof ApiError) {
          const denied = err.status === 403 || String(err.reasonCode || '').toUpperCase() === 'PERMISSION_DENIED';
          if (denied) deniedRelationModels.add(relation);
        }
        next[name] = [];
      }
    }));
    Object.entries(next).forEach(([fieldName, options]) => {
      mergeRelationOptions(fieldName, options);
    });
  }


  return { ensureRelationFieldDescriptors, openRelationCreateForm, currentRelationRecordId, canOpenRelationRecordForm, openRelationRecordForm, quickCreateRelation, loadRelationOptions };
}
