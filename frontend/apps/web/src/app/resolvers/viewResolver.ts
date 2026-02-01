import type { FormField, ViewContract } from '@sc/schema';
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

  layout.groups?.forEach((group) => {
    group.fields?.forEach((field) => pushField(field));
    group.sub_groups?.forEach((sub) => sub.fields?.forEach((field) => pushField(field)));
  });

  layout.notebooks?.forEach((notebook) => {
    notebook.pages?.forEach((page) => {
      page.groups?.forEach((group) => {
        group.fields?.forEach((field) => pushField(field));
      });
    });
  });

  if (layout.titleField) {
    pushField({ name: layout.titleField });
  }

  return names;
}
