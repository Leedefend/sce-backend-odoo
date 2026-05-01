# -*- coding: utf-8 -*-

from .payment_slice_entry_form_builder import PaymentSliceEntryFormBuilder
from .payment_slice_list_builder import PaymentSliceListBuilder
from .payment_slice_next_actions_builder import PaymentSliceNextActionsBuilder
from .payment_slice_summary_builder import PaymentSliceSummaryBuilder


BUILDERS = (
    PaymentSliceEntryFormBuilder,
    PaymentSliceListBuilder,
    PaymentSliceSummaryBuilder,
    PaymentSliceNextActionsBuilder,
)
