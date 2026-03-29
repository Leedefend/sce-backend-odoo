import type { FormSectionFieldSchema } from './formSection.types';

export type DetailActionItem = {
  key: string;
  label: string;
  enabled: boolean;
  hint: string;
  semantic?: string;
};

export type DetailStatusbarStep = {
  key: string;
  label: string;
  active: boolean;
};

export type DetailSectionView = {
  key: string;
  title: string;
  hint: string;
  tone: 'core' | 'advanced';
  isAdvanced: boolean;
  shellClass: string;
  eyebrow: string;
  summary: string;
  fields: FormSectionFieldSchema[];
};

export type DetailShellView = {
  key: string;
  title: string;
  kind: 'default' | 'header' | 'sheet' | 'group' | 'notebook' | 'page';
  shellClass: string;
  eyebrow: string;
  summary: string;
  sections: DetailSectionView[];
  tabs?: Array<{
    key: string;
    label: string;
    summary: string;
    sections: DetailSectionView[];
  }>;
};
