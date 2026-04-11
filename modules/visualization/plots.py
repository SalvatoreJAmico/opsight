import os
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
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
    "x_min": None,
    "x_max": None,
    "y_min": None,
    "y_max": None,
    "log_scale_x": False,
    "log_scale_y": False,
    "clip_mode": "none",
    "clip_percentile": 95.0,
    "clip_max": None,
    "zoom_preset": "full_range",
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

    for key in ["show_legend", "show_grid", "log_scale_x", "log_scale_y"]:
        value = normalized[key]
        if isinstance(value, str):
            normalized[key] = value.strip().lower() in {"1", "true", "yes", "y", "on"}
        else:
            normalized[key] = bool(value)

    try:
        normalized["clip_percentile"] = float(normalized["clip_percentile"])
    except (TypeError, ValueError):
        normalized["clip_percentile"] = 95.0

    if normalized["clip_percentile"] <= 0:
        normalized["clip_percentile"] = 95.0
    if normalized["clip_percentile"] > 100:
        normalized["clip_percentile"] = 100.0

    if normalized["clip_max"] is not None:
        try:
            normalized["clip_max"] = float(normalized["clip_max"])
        except (TypeError, ValueError):
            normalized["clip_max"] = None

    normalized["clip_mode"] = str(normalized.get("clip_mode") or "none").strip().lower()
    if normalized["clip_mode"] not in {"none", "percentile", "manual"}:
        normalized["clip_mode"] = "none"

    normalized["zoom_preset"] = str(normalized.get("zoom_preset") or "full_range").strip().lower()
    if normalized["zoom_preset"] not in {"full_range", "focus_low_range", "iqr"}:
        normalized["zoom_preset"] = "full_range"

    return normalized


def _coerce_axis_bound(raw_value, reference_series: pd.Series | None):
    if raw_value is None:
        return None

    text = str(raw_value).strip()
    if text == "":
        return None

    if reference_series is not None and pd.api.types.is_datetime64_any_dtype(reference_series):
        parsed = pd.to_datetime(text, errors="coerce")
        return None if pd.isna(parsed) else parsed.to_pydatetime()

    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _compute_zoom_limits(series: pd.Series | None, zoom_preset: str):
    if series is None or series.empty:
        return None, None

    if zoom_preset == "focus_low_range":
        return 0.0, 5000.0

    if zoom_preset != "iqr":
        return None, None

    if pd.api.types.is_datetime64_any_dtype(series):
        return None, None

    numeric_series = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if numeric_series.empty:
        return None, None

    q1 = numeric_series.quantile(0.25)
    q3 = numeric_series.quantile(0.75)
    iqr = q3 - q1
    if pd.isna(iqr):
        return None, None

    if float(iqr) == 0:
        return float(q1), float(q3)

    return float(q1 - 1.5 * iqr), float(q3 + 1.5 * iqr)


def _merge_explicit_and_zoom_limits(
    explicit_min,
    explicit_max,
    zoom_min,
    zoom_max,
):
    final_min = explicit_min if explicit_min is not None else zoom_min
    final_max = explicit_max if explicit_max is not None else zoom_max
    return final_min, final_max


def _get_clip_upper_bound(series: pd.Series, normalized: dict):
    clip_mode = normalized.get("clip_mode", "none")
    if clip_mode == "none":
        return None

    numeric_series = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if numeric_series.empty:
        return None

    if clip_mode == "percentile":
        percentile = float(normalized.get("clip_percentile") or 95.0)
        return float(numeric_series.quantile(percentile / 100.0))

    if clip_mode == "manual":
        clip_max = normalized.get("clip_max")
        if clip_max is None:
            return None
        return float(clip_max)

    return None


def _clip_numeric_series_for_display(series: pd.Series, normalized: dict) -> pd.Series:
    upper_bound = _get_clip_upper_bound(series, normalized)
    if upper_bound is None:
        return series

    numeric_series = pd.to_numeric(series, errors="coerce")
    clipped = numeric_series.where(numeric_series <= upper_bound)
    return clipped


def _can_apply_log_scale(series: pd.Series | None, is_categorical: bool) -> bool:
    if is_categorical or series is None or series.empty:
        return False
    return pd.api.types.is_numeric_dtype(series)


def _apply_axis_controls(
    ax,
    *,
    normalized: dict,
    x_series: pd.Series | None = None,
    y_series: pd.Series | None = None,
    x_is_categorical: bool = False,
    y_is_categorical: bool = False,
) -> None:
    if normalized.get("log_scale_x") and _can_apply_log_scale(x_series, x_is_categorical):
        ax.set_xscale("log")
    if normalized.get("log_scale_y") and _can_apply_log_scale(y_series, y_is_categorical):
        ax.set_yscale("log")

    if not x_is_categorical:
        x_min = _coerce_axis_bound(normalized.get("x_min"), x_series)
        x_max = _coerce_axis_bound(normalized.get("x_max"), x_series)
        zoom_x_min, zoom_x_max = _compute_zoom_limits(x_series, normalized.get("zoom_preset", "full_range"))
        x_min, x_max = _merge_explicit_and_zoom_limits(x_min, x_max, zoom_x_min, zoom_x_max)
        if x_min is not None and x_max is not None and x_min < x_max:
            ax.set_xlim(left=x_min, right=x_max)
        elif x_min is not None and x_max is None:
            ax.set_xlim(left=x_min)
        elif x_min is None and x_max is not None:
            ax.set_xlim(right=x_max)

    if not y_is_categorical:
        y_min = _coerce_axis_bound(normalized.get("y_min"), y_series)
        y_max = _coerce_axis_bound(normalized.get("y_max"), y_series)
        zoom_y_min, zoom_y_max = _compute_zoom_limits(y_series, normalized.get("zoom_preset", "full_range"))
        y_min, y_max = _merge_explicit_and_zoom_limits(y_min, y_max, zoom_y_min, zoom_y_max)
        if y_min is not None and y_max is not None and y_min < y_max:
            ax.set_ylim(bottom=y_min, top=y_max)
        elif y_min is not None and y_max is None:
            ax.set_ylim(bottom=y_min)
        elif y_min is None and y_max is not None:
            ax.set_ylim(top=y_max)


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

    normalized = _normalize_enhancements(enhancements)
    series = pd.to_numeric(_get_plot_series(df, target_column, target_label), errors="coerce")
    series = _clip_numeric_series_for_display(series, normalized).dropna()

    if normalized["log_scale_x"]:
        series = series[series > 0]

    if series.empty:
        raise ValueError("No plottable values available after applying visualization controls.")

    fig, ax = plt.subplots(figsize=(5, 3))
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

    _apply_axis_controls(
        ax,
        normalized=normalized,
        x_series=series,
        y_series=None,
    )

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

    _apply_axis_controls(
        ax,
        normalized=normalized,
        y_series=counts,
        x_is_categorical=True,
    )

    fig.tight_layout()

    fig.savefig(full_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"


def create_boxplot(df: pd.DataFrame, target_column, target_label: str, enhancements: dict | None = None) -> str:
    _ensure_plot_dir()
    filename = "boxplot_metric.png"
    full_path = os.path.join(PLOT_DIR, filename)

    normalized = _normalize_enhancements(enhancements)
    series = pd.to_numeric(_get_plot_series(df, target_column, target_label), errors="coerce")
    series = _clip_numeric_series_for_display(series, normalized).dropna()

    if normalized["log_scale_y"]:
        series = series[series > 0]

    if series.empty:
        raise ValueError("No plottable values available after applying visualization controls.")

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

    _apply_axis_controls(
        ax,
        normalized=normalized,
        x_series=None,
        y_series=series,
        x_is_categorical=True,
    )

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
    normalized = _normalize_enhancements(enhancements)

    if pd.api.types.is_numeric_dtype(target_series):
        target_series = _clip_numeric_series_for_display(target_series, normalized)
    if pd.api.types.is_numeric_dtype(compare_series):
        compare_series = _clip_numeric_series_for_display(compare_series, normalized)

    if normalized["log_scale_x"] and pd.api.types.is_numeric_dtype(target_series):
        target_series = pd.to_numeric(target_series, errors="coerce")
        target_series = target_series.where(target_series > 0)
    if normalized["log_scale_y"] and pd.api.types.is_numeric_dtype(compare_series):
        compare_series = pd.to_numeric(compare_series, errors="coerce")
        compare_series = compare_series.where(compare_series > 0)

    plot_frame = pd.DataFrame({"x": target_series, "y": compare_series}).dropna()

    if plot_frame.empty:
        raise ValueError("No plottable values available after applying visualization controls.")

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

    _apply_axis_controls(
        ax,
        normalized=normalized,
        x_series=plot_frame["x"],
        y_series=plot_frame["y"],
    )

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

    normalized = _normalize_enhancements(enhancements)
    target_series = pd.to_numeric(_get_plot_series(df, target_column, target_label), errors="coerce")
    target_series = _clip_numeric_series_for_display(target_series, normalized)
    if normalized["log_scale_y"]:
        target_series = target_series.where(target_series > 0)

    plot_frame = pd.DataFrame(
        {
            "target": target_series,
            "compare": _get_plot_series(df, compare_column, compare_label),
        }
    ).dropna()

    if plot_frame.empty:
        raise ValueError("No plottable values available after applying visualization controls.")

    grouped = plot_frame.groupby("compare")["target"].mean().sort_index()

    labels = grouped.index.astype(str).tolist()

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

    _apply_axis_controls(
        ax,
        normalized=normalized,
        y_series=grouped,
        x_is_categorical=True,
    )

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

    normalized = _normalize_enhancements(enhancements)
    target_series = pd.to_numeric(_get_plot_series(df, target_column, target_label), errors="coerce")
    target_series = _clip_numeric_series_for_display(target_series, normalized)
    if normalized["log_scale_y"]:
        target_series = target_series.where(target_series > 0)

    plot_frame = pd.DataFrame(
        {
            "target": target_series,
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

    flattened_values = pd.Series(np.concatenate(grouped_series)) if grouped_series else pd.Series(dtype=float)
    _apply_axis_controls(
        ax,
        normalized=normalized,
        y_series=flattened_values,
        x_is_categorical=True,
    )

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

    normalized = _normalize_enhancements(enhancements)
    target_series = pd.to_numeric(_get_plot_series(df, target_column, target_label), errors="coerce")
    target_series = _clip_numeric_series_for_display(target_series, normalized)
    if normalized["log_scale_y"]:
        target_series = target_series.where(target_series > 0)

    compare_series = pd.to_datetime(_get_plot_series(df, compare_column, compare_label), errors="coerce")

    plot_frame = pd.DataFrame({"target": target_series, "compare": compare_series}).dropna()
    if plot_frame.empty:
        raise ValueError("Time line chart requires numeric values and a valid date/time field.")

    plot_frame = plot_frame.sort_values("compare")
    plot_frame = plot_frame.set_index("compare").resample("D")["target"].mean().dropna()
    if plot_frame.empty:
        raise ValueError("Time line chart has no plottable points after date aggregation.")

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

    _apply_axis_controls(
        ax,
        normalized=normalized,
        x_series=pd.Series(plot_frame.index),
        y_series=pd.Series(plot_frame.values),
    )

    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(full_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"