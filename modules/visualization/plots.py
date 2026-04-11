import os
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

PLOT_DIR = "static/plots"
MAX_CATEGORY_LABEL_CHARS = 18
MAX_VISIBLE_X_TICKS = 12


DEFAULT_ENHANCEMENTS = {
    "title": None,
    "subtitle": None,
    "x_label": None,
    "y_label": None,
    "show_legend": False,
    "show_grid": True,
    "color": None,
    "annotation": None,
}


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


def _normalize_enhancements(enhancements: dict | None) -> dict:
    normalized = DEFAULT_ENHANCEMENTS.copy()
    if not enhancements:
        return normalized

    for key in normalized:
        value = enhancements.get(key)
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                value = None
        if value is not None:
            normalized[key] = value

    normalized["show_legend"] = bool(normalized["show_legend"])
    normalized["show_grid"] = bool(normalized["show_grid"])
    return normalized


def _apply_common_enhancements(
    fig,
    ax,
    *,
    default_title: str,
    default_x_label: str,
    default_y_label: str,
    enhancements: dict | None,
) -> dict:
    normalized = _normalize_enhancements(enhancements)

    ax.set_title(normalized["title"] or default_title)
    ax.set_xlabel(normalized["x_label"] or default_x_label)
    ax.set_ylabel(normalized["y_label"] or default_y_label)
    ax.grid(normalized["show_grid"])

    if normalized["subtitle"]:
        fig.text(0.5, 0.98, normalized["subtitle"], ha="center", va="top", fontsize=9)

    if normalized["annotation"]:
        ax.annotate(
            normalized["annotation"],
            xy=(0.02, 0.96),
            xycoords="axes fraction",
            ha="left",
            va="top",
            fontsize=8,
            bbox={"boxstyle": "round,pad=0.2", "fc": "#fffbe6", "ec": "#bfae5a", "alpha": 0.9},
        )

    return normalized


def create_histogram(df: pd.DataFrame, target_column, target_label: str, enhancements: dict | None = None) -> str:
    _ensure_plot_dir()
    filename = "hist_metric.png"
    full_path = os.path.join(PLOT_DIR, filename)

    series = _get_plot_series(df, target_column, target_label).dropna()

    fig, ax = plt.subplots(figsize=(5, 3))
    normalized = _normalize_enhancements(enhancements)
    series.hist(ax=ax, color=normalized["color"])
    ax.bar_label(ax.containers[0], fmt="%d", fontsize=7)
    _apply_common_enhancements(
        fig,
        ax,
        default_title=f"Distribution of {target_label}",
        default_x_label=target_label,
        default_y_label="Frequency",
        enhancements=normalized,
    )

    if normalized["show_legend"]:
        ax.legend([target_label])

    fig.tight_layout()
    fig.savefig(full_path, dpi=80, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"


def create_bar_category_chart(df: pd.DataFrame, compare_column, compare_label: str, enhancements: dict | None = None) -> str:
    _ensure_plot_dir()
    filename = "bar_category.png"
    full_path = os.path.join(PLOT_DIR, filename)

    counts = _get_plot_series(df, compare_column, compare_label).dropna().astype(str).value_counts().sort_index()

    labels = counts.index.astype(str).tolist()
    normalized = _normalize_enhancements(enhancements)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(range(len(labels)), counts.values, color=normalized["color"], label=compare_label)
    _apply_common_enhancements(
        fig,
        ax,
        default_title=f"{compare_label} Counts",
        default_x_label=compare_label,
        default_y_label="Count",
        enhancements=normalized,
    )
    _style_category_axis(ax, labels)

    if normalized["show_legend"]:
        ax.legend()

    fig.tight_layout()

    fig.savefig(full_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"


def create_boxplot(df: pd.DataFrame, target_column, target_label: str, enhancements: dict | None = None) -> str:
    _ensure_plot_dir()
    filename = "boxplot_metric.png"
    full_path = os.path.join(PLOT_DIR, filename)

    series = _get_plot_series(df, target_column, target_label).dropna()

    normalized = _normalize_enhancements(enhancements)

    fig, ax = plt.subplots(figsize=(5, 3))
    box = ax.boxplot(series, patch_artist=True)
    if normalized["color"]:
        for patch in box["boxes"]:
            patch.set_facecolor(normalized["color"])
            patch.set_alpha(0.55)

    _apply_common_enhancements(
        fig,
        ax,
        default_title=f"Box Plot of {target_label}",
        default_x_label=target_label,
        default_y_label=target_label,
        enhancements=normalized,
    )

    if normalized["show_legend"]:
        ax.legend([target_label])

    fig.tight_layout()
    fig.savefig(full_path, dpi=80, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"


def create_scatter_plot(
    df: pd.DataFrame,
    target_column,
    compare_column,
    target_label: str,
    compare_label: str,
    enhancements: dict | None = None,
) -> str:
    _ensure_plot_dir()
    filename = "scatter_metric_secondary.png"
    full_path = os.path.join(PLOT_DIR, filename)

    target_series, x_axis_label = _get_scatter_axis_series(df, target_column, target_label)
    compare_series, y_axis_label = _get_scatter_axis_series(df, compare_column, compare_label)
    plot_frame = pd.DataFrame({"x": target_series, "y": compare_series}).dropna()
    normalized = _normalize_enhancements(enhancements)

    fig, ax = plt.subplots(figsize=(5, 3))
    ax.scatter(plot_frame["x"], plot_frame["y"], color=normalized["color"], label=f"{target_label} vs {compare_label}")
    _apply_common_enhancements(
        fig,
        ax,
        default_title=f"{target_label} vs {compare_label}",
        default_x_label=x_axis_label,
        default_y_label=y_axis_label,
        enhancements=normalized,
    )

    if normalized["show_legend"]:
        ax.legend()

    fig.tight_layout()
    fig.savefig(full_path, dpi=80, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"


def create_grouped_comparison_chart(
    df: pd.DataFrame,
    target_column,
    compare_column,
    target_label: str,
    compare_label: str,
    enhancements: dict | None = None,
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
    normalized = _normalize_enhancements(enhancements)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(range(len(labels)), grouped.values, color=normalized["color"], label=target_label)
    _apply_common_enhancements(
        fig,
        ax,
        default_title=f"Average {target_label} by {compare_label}",
        default_x_label=compare_label,
        default_y_label=f"Average {target_label}",
        enhancements=normalized,
    )
    _style_category_axis(ax, labels)

    if normalized["show_legend"]:
        ax.legend()

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
    enhancements: dict | None = None,
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

    normalized = _normalize_enhancements(enhancements)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    box = ax.boxplot(grouped_series, patch_artist=True)
    if normalized["color"]:
        for patch in box["boxes"]:
            patch.set_facecolor(normalized["color"])
            patch.set_alpha(0.45)

    _apply_common_enhancements(
        fig,
        ax,
        default_title=f"{target_label} Distribution by {compare_label}",
        default_x_label=compare_label,
        default_y_label=target_label,
        enhancements=normalized,
    )
    _style_category_axis(ax, labels)

    if normalized["show_legend"]:
        ax.legend([target_label])

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
    enhancements: dict | None = None,
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

    normalized = _normalize_enhancements(enhancements)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(
        plot_frame.index,
        plot_frame.values,
        marker="o",
        linewidth=1.8,
        color=normalized["color"],
        label=target_label,
    )
    _apply_common_enhancements(
        fig,
        ax,
        default_title=f"{target_label} Trend by {compare_label}",
        default_x_label=compare_label,
        default_y_label=f"Average {target_label}",
        enhancements=normalized,
    )

    if normalized["show_legend"]:
        ax.legend()

    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(full_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"