import os
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

PLOT_DIR = "static/plots"
MAX_CATEGORY_LABEL_CHARS = 18
MAX_VISIBLE_X_TICKS = 12


def _ensure_plot_dir():
    os.makedirs(PLOT_DIR, exist_ok=True)


def _truncate_label(label: str, max_chars: int = MAX_CATEGORY_LABEL_CHARS) -> str:
    text = str(label)
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 1]}…"


def _style_category_axis(ax, labels: list[str]) -> None:
    positions = list(range(len(labels)))
    truncated_labels = [_truncate_label(label) for label in labels]

    ax.set_xticks(positions)
    ax.set_xticklabels(truncated_labels, rotation=40, ha="right", fontsize=8)

    if len(labels) > MAX_VISIBLE_X_TICKS:
        step = max(1, len(labels) // MAX_VISIBLE_X_TICKS)
        visible_positions = set(range(0, len(labels), step))
        visible_positions.add(len(labels) - 1)

        for index, tick in enumerate(ax.get_xticklabels()):
            if index not in visible_positions:
                tick.set_visible(False)


def _get_plot_series(df: pd.DataFrame, column_name, field_label: str) -> pd.Series:
    series = df[column_name]
    if field_label == "Order Date":
        return pd.to_datetime(series, errors="coerce")
    return series


def _get_scatter_axis_series(df: pd.DataFrame, column_name, field_label: str) -> tuple[pd.Series, str]:
    series = _get_plot_series(df, column_name, field_label)

    if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
        return series, field_label

    encoded_values, _ = pd.factorize(series.fillna("Missing").astype(str))
    return pd.Series(encoded_values, index=series.index), f"{field_label} (encoded)"


def create_histogram(df: pd.DataFrame, target_column, target_label: str) -> str:
    _ensure_plot_dir()
    filename = "hist_metric.png"
    full_path = os.path.join(PLOT_DIR, filename)

    series = _get_plot_series(df, target_column, target_label).dropna()

    plt.figure(figsize=(5, 3))
    series.hist()
    plt.title(f"Distribution of {target_label}")
    plt.xlabel(target_label)
    plt.ylabel("Frequency")
    plt.grid(True)

    plt.savefig(full_path, dpi=80, bbox_inches="tight")
    plt.close()

    return f"/static/plots/{filename}"


def create_bar_category_chart(df: pd.DataFrame, compare_column, compare_label: str) -> str:
    _ensure_plot_dir()
    filename = "bar_category.png"
    full_path = os.path.join(PLOT_DIR, filename)

    counts = _get_plot_series(df, compare_column, compare_label).dropna().astype(str).value_counts().sort_index()

    labels = counts.index.astype(str).tolist()

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(range(len(labels)), counts.values)
    ax.set_title(f"{compare_label} Counts")
    ax.set_xlabel(compare_label)
    ax.set_ylabel("Count")
    ax.grid(True, axis="y")
    _style_category_axis(ax, labels)
    fig.tight_layout()

    fig.savefig(full_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"


def create_boxplot(df: pd.DataFrame, target_column, target_label: str) -> str:
    _ensure_plot_dir()
    filename = "boxplot_metric.png"
    full_path = os.path.join(PLOT_DIR, filename)

    series = _get_plot_series(df, target_column, target_label).dropna()

    plt.figure(figsize=(5, 3))
    plt.boxplot(series)
    plt.title(f"Box Plot of {target_label}")
    plt.ylabel(target_label)
    plt.grid(True, axis="y")

    plt.savefig(full_path, dpi=80, bbox_inches="tight")
    plt.close()

    return f"/static/plots/{filename}"


def create_scatter_plot(
    df: pd.DataFrame,
    target_column,
    compare_column,
    target_label: str,
    compare_label: str,
) -> str:
    _ensure_plot_dir()
    filename = "scatter_metric_secondary.png"
    full_path = os.path.join(PLOT_DIR, filename)

    target_series, x_axis_label = _get_scatter_axis_series(df, target_column, target_label)
    compare_series, y_axis_label = _get_scatter_axis_series(df, compare_column, compare_label)
    plot_frame = pd.DataFrame({"x": target_series, "y": compare_series}).dropna()

    plt.figure(figsize=(5, 3))
    plt.scatter(plot_frame["x"], plot_frame["y"])
    plt.title(f"{target_label} vs {compare_label}")
    plt.xlabel(x_axis_label)
    plt.ylabel(y_axis_label)
    plt.grid(True)

    plt.savefig(full_path, dpi=80, bbox_inches="tight")
    plt.close()

    return f"/static/plots/{filename}"


def create_grouped_comparison_chart(
    df: pd.DataFrame,
    target_column,
    compare_column,
    target_label: str,
    compare_label: str,
) -> str:
    _ensure_plot_dir()
    filename = "grouped_comparison.png"
    full_path = os.path.join(PLOT_DIR, filename)

    plot_frame = pd.DataFrame(
        {
            "target": _get_plot_series(df, target_column, target_label),
            "compare": _get_plot_series(df, compare_column, compare_label),
        }
    ).dropna()
    grouped = plot_frame.groupby("compare")["target"].mean().sort_index()

    labels = grouped.index.astype(str).tolist()

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(range(len(labels)), grouped.values)
    ax.set_title(f"Average {target_label} by {compare_label}")
    ax.set_xlabel(compare_label)
    ax.set_ylabel(f"Average {target_label}")
    ax.grid(True, axis="y")
    _style_category_axis(ax, labels)
    fig.tight_layout()

    fig.savefig(full_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"


def create_grouped_boxplot_chart(
    df: pd.DataFrame,
    target_column,
    compare_column,
    target_label: str,
    compare_label: str,
) -> str:
    _ensure_plot_dir()
    filename = "grouped_boxplot.png"
    full_path = os.path.join(PLOT_DIR, filename)

    plot_frame = pd.DataFrame(
        {
            "target": _get_plot_series(df, target_column, target_label),
            "compare": _get_plot_series(df, compare_column, compare_label),
        }
    ).dropna()

    if plot_frame.empty:
        raise ValueError("No valid rows available for grouped box plot.")

    grouped_series = []
    labels = []
    for category, category_rows in plot_frame.groupby("compare"):
        values = pd.to_numeric(category_rows["target"], errors="coerce").dropna()
        if values.empty:
            continue
        grouped_series.append(values.values)
        labels.append(str(category))

    if not grouped_series:
        raise ValueError("Grouped box plot requires numeric target values.")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.boxplot(grouped_series)
    ax.set_title(f"{target_label} Distribution by {compare_label}")
    ax.set_xlabel(compare_label)
    ax.set_ylabel(target_label)
    ax.grid(True, axis="y")
    _style_category_axis(ax, labels)
    fig.tight_layout()

    fig.savefig(full_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"


def create_time_line_chart(
    df: pd.DataFrame,
    target_column,
    compare_column,
    target_label: str,
    compare_label: str,
) -> str:
    _ensure_plot_dir()
    filename = "time_line.png"
    full_path = os.path.join(PLOT_DIR, filename)

    target_series = pd.to_numeric(_get_plot_series(df, target_column, target_label), errors="coerce")
    compare_series = pd.to_datetime(_get_plot_series(df, compare_column, compare_label), errors="coerce")

    plot_frame = pd.DataFrame({"target": target_series, "compare": compare_series}).dropna()
    if plot_frame.empty:
        raise ValueError("Time line chart requires numeric values and a valid date/time field.")

    plot_frame = plot_frame.sort_values("compare")
    plot_frame = plot_frame.set_index("compare").resample("D")["target"].mean().dropna()
    if plot_frame.empty:
        raise ValueError("Time line chart has no plottable points after date aggregation.")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(plot_frame.index, plot_frame.values, marker="o", linewidth=1.8)
    ax.set_title(f"{target_label} Trend by {compare_label}")
    ax.set_xlabel(compare_label)
    ax.set_ylabel(f"Average {target_label}")
    ax.grid(True)
    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(full_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"