"""Dataset-derived chart fields. Never invent measurements or rename Freight to Sales."""
import numpy as np
import pandas as pd

LEGACY_LABELS = {
    'sales': 'Sales', 'profit': 'Profit', 'quantity': 'Quantity',
    'discount': 'Discount', 'category': 'Category', 'timestamp': 'Order Date',
    'order date': 'Order Date', 'orderdate': 'Order Date',
}

def normalize(value):
    return str(value).strip().lower().replace('_', ' ')

def schema_for(df):
    fields, types = {}, {}
    for col in df.columns:
        key = normalize(col)
        if key == 'entity id':
            continue
        label = LEGACY_LABELS.get(key, str(col))
        # Keep the historical sales view label, but do not claim every
        # canonical timestamp (e.g. employee hire time) is an order date.
        if key == 'timestamp' and not any(normalize(c) == 'sales' for c in df.columns):
            label = 'Timestamp'
        if label in fields:
            label = str(col)
        series = df[col]
        nonnull = series.dropna()
        is_date = key == 'timestamp' or pd.api.types.is_datetime64_any_dtype(series)
        if not is_date and any(token in key for token in ('date', 'time')) and not nonnull.empty:
            is_date = pd.to_datetime(nonnull, errors='coerce', format='mixed').notna().any()
        if is_date:
            kind = 'date'
        elif pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
            kind = 'numeric'
        else:
            kind = 'categorical'
        fields[label], types[label] = col, kind
    ordered = [label for label in ("Sales", "Profit", "Quantity", "Discount", "Category", "Order Date") if label in fields]
    ordered += [label for label in fields if label not in ordered]
    return {label: fields[label] for label in ordered}, {label: types[label] for label in ordered}

def usable_series(df, column, kind):
    series = df[column]
    if kind == 'numeric':
        return pd.to_numeric(series, errors='coerce').replace([np.inf, -np.inf], np.nan)
    if kind == 'date':
        return pd.to_datetime(series, errors='coerce', format='mixed')
    return series

def default_target(df):
    fields, types = schema_for(df)
    choices = [label for label, col in fields.items()
               if types[label] == 'numeric' and usable_series(df, col, 'numeric').notna().any()]
    return ('Sales' if 'Sales' in choices else next(iter(choices), None)), choices
