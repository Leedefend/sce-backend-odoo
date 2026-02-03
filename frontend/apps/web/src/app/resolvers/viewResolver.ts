import type { FormField, ViewContract } from '@sc/schema';
import { asArray } from '../../utils/guards';
import { intentRequest } from '../../api/intents';

export async function resolveView(model: string, viewType: string) {
  return intentRequest<ViewContract>({
    intent: 'load_view',
    params: { model, view_type: viewType },
  });
}

export function extractFieldNames(layout: ViewContract['layout']) {
  const names: string[] = [];
  const pushField = (field?: FormField) => {
    if (field?.name && !names.includes(field.name)) {
      names.push(field.name);
    }
  };

  asArray(layout.groups).forEach((group) => {
    asArray(group.fields).forEach((field) => pushField(field));
    asArray(group.sub_groups).forEach((sub) => asArray(sub.fields).forEach((field) => pushField(field)));
  });

  asArray(layout.notebooks).forEach((notebook) => {
    asArray(notebook.pages).forEach((page) => {
      asArray(page.groups).forEach((group) => {
        asArray(group.fields).forEach((field) => pushField(field));
      });
    });
  });

  if (layout.titleField) {
    pushField({ name: layout.titleField });
  }

  return names;
}
