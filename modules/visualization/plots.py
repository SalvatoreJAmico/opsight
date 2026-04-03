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


def create_histogram(df: pd.DataFrame) -> str:
    _ensure_plot_dir()
    filename = "hist_metric.png"
    full_path = os.path.join(PLOT_DIR, filename)

    column = "metric_value"

    plt.figure(figsize=(5, 3))
    df[column].dropna().hist()
    plt.title(f"Distribution of {column}")
    plt.xlabel(column)
    plt.ylabel("Frequency")
    plt.grid(True)

    plt.savefig(full_path, dpi=80, bbox_inches="tight")
    plt.close()

    return f"/static/plots/{filename}"


def create_bar_category_chart(df: pd.DataFrame) -> str:
    _ensure_plot_dir()
    filename = "bar_category.png"
    full_path = os.path.join(PLOT_DIR, filename)

    counts = df["category"].value_counts().sort_index()

    labels = counts.index.astype(str).tolist()

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(range(len(labels)), counts.values)
    ax.set_title("Category Counts")
    ax.set_xlabel("Category")
    ax.set_ylabel("Count")
    ax.grid(True, axis="y")
    _style_category_axis(ax, labels)
    fig.tight_layout()

    fig.savefig(full_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"


def create_boxplot(df: pd.DataFrame) -> str:
    _ensure_plot_dir()
    filename = "boxplot_metric.png"
    full_path = os.path.join(PLOT_DIR, filename)

    plt.figure(figsize=(5, 3))
    plt.boxplot(df["metric_value"].dropna())
    plt.title("Box Plot of metric_value")
    plt.ylabel("metric_value")
    plt.grid(True, axis="y")

    plt.savefig(full_path, dpi=80, bbox_inches="tight")
    plt.close()

    return f"/static/plots/{filename}"


def create_scatter_plot(df: pd.DataFrame) -> str:
    _ensure_plot_dir()
    filename = "scatter_metric_secondary.png"
    full_path = os.path.join(PLOT_DIR, filename)

    plt.figure(figsize=(5, 3))
    plt.scatter(df["metric_value"], df["secondary_metric"])
    plt.title("metric_value vs secondary_metric")
    plt.xlabel("metric_value")
    plt.ylabel("secondary_metric")
    plt.grid(True)

    plt.savefig(full_path, dpi=80, bbox_inches="tight")
    plt.close()

    return f"/static/plots/{filename}"


def create_grouped_comparison_chart(df: pd.DataFrame) -> str:
    _ensure_plot_dir()
    filename = "grouped_comparison.png"
    full_path = os.path.join(PLOT_DIR, filename)

    grouped = df.groupby("category")["metric_value"].mean().sort_index()

    labels = grouped.index.astype(str).tolist()

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(range(len(labels)), grouped.values)
    ax.set_title("Average metric_value by Category")
    ax.set_xlabel("Category")
    ax.set_ylabel("Average metric_value")
    ax.grid(True, axis="y")
    _style_category_axis(ax, labels)
    fig.tight_layout()

    fig.savefig(full_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return f"/static/plots/{filename}"