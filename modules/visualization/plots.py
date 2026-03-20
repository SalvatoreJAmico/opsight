from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLOT_DIR = PROJECT_ROOT / "static" / "plots"
WEB_PLOT_DIR = "/static/plots"


def create_histogram(df):
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    filename = "hist_metric.png"
    full_path = PLOT_DIR / filename

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    plt.figure(figsize=(5, 3))
    if numeric_cols:
        column = "metric_value" if "metric_value" in numeric_cols else numeric_cols[0]
        df[column].hist(bins=20)
        plt.title(f"Distribution: {column}")
        plt.xlabel(column)
        plt.ylabel("Frequency")
        plt.grid(True)
    else:
        plt.text(0.5, 0.5, "No numeric data available", ha="center", va="center")
        plt.title("Metric Distribution")
        plt.axis("off")

    plt.savefig(full_path, dpi=80, bbox_inches="tight")
    plt.close()

    return f"{WEB_PLOT_DIR}/{filename}"