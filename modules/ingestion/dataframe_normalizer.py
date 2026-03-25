from collections.abc import Mapping

import pandas as pd


HEADER_KEYWORDS = ("id", "date", "time", "name", "amount", "salary", "department")


def normalize_loaded_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Normalize parsed tabular data into an adapter-friendly DataFrame."""
    if not isinstance(dataframe, pd.DataFrame):
        return dataframe

    normalized = _expand_single_object_column(dataframe)
    normalized = _promote_embedded_header_row(normalized)
    return _drop_empty_axes(normalized)


def _expand_single_object_column(dataframe: pd.DataFrame) -> pd.DataFrame:
    if len(dataframe.columns) != 1:
        return dataframe

    series = dataframe.iloc[:, 0].dropna()
    if series.empty:
        return dataframe

    if all(isinstance(value, Mapping) for value in series):
        return pd.DataFrame(series.tolist())

    first_value = series.iloc[0]
    if len(series) == 1 and isinstance(first_value, list) and all(
        isinstance(item, Mapping) for item in first_value
    ):
        return pd.DataFrame(first_value)

    return dataframe


def _promote_embedded_header_row(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty or not _has_placeholder_columns(dataframe.columns):
        return dataframe

    header_row_index = _find_header_row(dataframe)
    if header_row_index is None:
        return dataframe

    raw_headers = dataframe.iloc[header_row_index].tolist()
    headers = _dedupe_headers([_clean_header_value(value) for value in raw_headers])
    header_count = len([header for header in headers if header])
    if header_count < 2:
        return dataframe

    normalized = dataframe.iloc[header_row_index + 1 :].copy()
    normalized.columns = headers
    return normalized


def _drop_empty_axes(dataframe: pd.DataFrame) -> pd.DataFrame:
    return dataframe.dropna(axis=0, how="all").dropna(axis=1, how="all").reset_index(drop=True)


def _has_placeholder_columns(columns) -> bool:
    return all(pd.isna(column) or str(column).startswith("Unnamed:") for column in columns)


def _find_header_row(dataframe: pd.DataFrame) -> int | None:
    best_index = None
    best_score = -1

    for index in range(min(len(dataframe), 10)):
        row = dataframe.iloc[index]
        non_null_values = [value for value in row.tolist() if pd.notna(value)]
        if len(non_null_values) < 2:
            continue

        text_values = [value for value in non_null_values if isinstance(value, str) and value.strip()]
        if len(text_values) != len(non_null_values):
            continue

        score = len(text_values)
        normalized_values = [value.strip().lower() for value in text_values]
        if len(set(normalized_values)) != len(normalized_values):
            continue

        score += sum(
            3 for value in normalized_values if any(keyword in value for keyword in HEADER_KEYWORDS)
        )

        if score > best_score:
            best_score = score
            best_index = index

    return best_index


def _clean_header_value(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _dedupe_headers(headers: list[str]) -> list[str]:
    counts = {}
    normalized_headers = []

    for index, header in enumerate(headers, start=1):
        candidate = header or f"column_{index}"
        counts[candidate] = counts.get(candidate, 0) + 1
        if counts[candidate] > 1:
            candidate = f"{candidate}_{counts[candidate]}"
        normalized_headers.append(candidate)

    return normalized_headers