export const PRODUCT_PAGE_REGION_CLASSES = {
  pageHeader: 'sc-product-page-header',
  pageToolbar: 'sc-product-page-toolbar',
  summaryStrip: 'sc-product-summary-strip',
  mainSurface: 'sc-product-main-surface',
  primaryActions: 'sc-product-primary-actions',
  feedbackLayer: 'sc-product-feedback-layer',
} as const;

export type ProductPageRegionClass = typeof PRODUCT_PAGE_REGION_CLASSES[keyof typeof PRODUCT_PAGE_REGION_CLASSES];
