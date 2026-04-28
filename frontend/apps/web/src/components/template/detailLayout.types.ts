import type { FormSectionFieldSchema } from './formSection.types';

export type DetailSectionView = {
  key: string;
  title: string;
  hint?: string;
  tone?: string;
  isAdvanced?: boolean;
  columns?: 1 | 2;
  shellClass?: string;
  eyebrow?: string;
  summary?: string;
  fields: FormSectionFieldSchema[];
};

export type DetailShellView = {
  key: string;
  title: string;
  kind: string;
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
