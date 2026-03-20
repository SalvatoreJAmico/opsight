import os
import matplotlib.pyplot as plt
import pandas as pd

PLOT_DIR = "static/plots"


def _ensure_plot_dir():
    os.makedirs(PLOT_DIR, exist_ok=True)


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

    plt.figure(figsize=(5, 3))
    plt.bar(counts.index.astype(str), counts.values)
    plt.title("Category Counts")
    plt.xlabel("Category")
    plt.ylabel("Count")
    plt.grid(True, axis="y")

    plt.savefig(full_path, dpi=80, bbox_inches="tight")
    plt.close()

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

    plt.figure(figsize=(5, 3))
    plt.bar(grouped.index.astype(str), grouped.values)
    plt.title("Average metric_value by Category")
    plt.xlabel("Category")
    plt.ylabel("Average metric_value")
    plt.grid(True, axis="y")

    plt.savefig(full_path, dpi=80, bbox_inches="tight")
    plt.close()

    return f"/static/plots/{filename}"