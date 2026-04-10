import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import ChartsTab from "./ChartsTab";
import {
  getHistogram,
  getBarCategory,
  getBoxplot,
  getScatter,
  getGroupedComparison,
  getChartOverview,
  resolveApiAssetUrl,
} from "../api/client";

vi.mock("../api/client", () => ({
  getHistogram: vi.fn(),
  getBarCategory: vi.fn(),
  getBoxplot: vi.fn(),
  getScatter: vi.fn(),
  getGroupedComparison: vi.fn(),
  getChartOverview: vi.fn(),
  resolveApiAssetUrl: vi.fn((imagePath) => imagePath),
}));

const SUCCESS_RESPONSE = (image) => ({
  ok: true,
  status: 200,
  error: null,
  data: { image },
});

describe("ChartsTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    getHistogram.mockResolvedValue(SUCCESS_RESPONSE("/static/plots/hist_metric.png"));
    getBarCategory.mockResolvedValue(SUCCESS_RESPONSE("/static/plots/bar_category.png"));
    getBoxplot.mockResolvedValue(SUCCESS_RESPONSE("/static/plots/boxplot_metric.png"));
    getScatter.mockResolvedValue(SUCCESS_RESPONSE("/static/plots/scatter_metric_secondary.png"));
    getGroupedComparison.mockResolvedValue(SUCCESS_RESPONSE("/static/plots/grouped_comparison.png"));
    getChartOverview.mockResolvedValue({
      ok: true,
      status: 200,
      error: null,
      data: {
        source: "Superstore Sales Dataset",
        source_metadata: {
          source_name: "Superstore Sales Dataset",
          source_location: "opsight-raw/csv/Sample - Superstore.csv",
          source_url: "https://www.kaggle.com/datasets/vivek468/superstore-dataset-final",
        },
        rows: 10,
        variables: 3,
        shape: { rows: 10, columns: 3 },
        fields: ["entity_id", "metric_value", "category"],
        missing_by_column: {
          entity_id: 0,
          metric_value: 1,
          category: 2,
        },
        numeric_summary: [
          {
            field: "metric_value",
            count: 9,
            missing: 1,
            min: 1,
            max: 20,
            mean: 10,
            median: 9,
            std: 3.5,
          },
        ],
        categorical_summary: [
          {
            field: "category",
            count: 8,
            missing: 2,
            unique: 2,
            top_values: [
              { value: "Furniture", count: 5 },
              { value: "Office Supplies", count: 3 },
            ],
          },
        ],
      },
    });
  });

  it("allows only one chart selection and shows only the active chart", async () => {
    render(<ChartsTab />);

    fireEvent.click(screen.getByRole("radio", { name: "Histogram" }));

    expect(await screen.findByAltText("Histogram visualization")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("radio", { name: "Category Bar Chart" }));

    await waitFor(() => {
      expect(screen.queryByAltText("Histogram visualization")).not.toBeInTheDocument();
    });

    expect(await screen.findByAltText("Category Bar Chart visualization")).toBeInTheDocument();

    const checkedRadios = screen.getAllByRole("radio").filter((radio) => radio.checked);
    expect(checkedRadios).toHaveLength(1);
  });

  it("shows loading state while waiting for the API", async () => {
    let resolveHistogram;
    getHistogram.mockImplementation(
      () => new Promise((resolve) => {
        resolveHistogram = () => resolve(SUCCESS_RESPONSE("/static/plots/hist_metric.png"));
      }),
    );

    render(<ChartsTab />);

    fireEvent.click(screen.getByRole("radio", { name: "Histogram" }));

    expect(screen.getByText("Loading chart...")).toBeInTheDocument();

    resolveHistogram();

    await waitFor(() => {
      expect(screen.getByAltText("Histogram visualization")).toBeInTheDocument();
    });
  });

  it("shows readable error message and keeps UI stable when API fails", async () => {
    getScatter.mockResolvedValue({
      ok: false,
      status: 500,
      error: "scatter generation failed",
      data: null,
    });

    render(<ChartsTab />);

    fireEvent.click(screen.getByRole("radio", { name: "Scatter Plot" }));

    expect(await screen.findByText("Error")).toBeInTheDocument();
    expect(screen.getByText("scatter generation failed")).toBeInTheDocument();
    expect(screen.getByText("Dataset Overview")).toBeInTheDocument();
  });

  it("renders explainability text for each supported chart", async () => {
    render(<ChartsTab />);

    const scenarios = [
      {
        label: "Histogram",
        expected: "This chart shows how many records fall into each value range.",
      },
      {
        label: "Category Bar Chart",
        expected: "This chart shows how records are distributed by group.",
      },
      {
        label: "Box Plot",
        expected: "This chart summarizes typical values and possible outliers.",
      },
      {
        label: "Scatter Plot",
        expected: "This chart shows how one value field moves relative to another.",
      },
      {
        label: "Grouped Comparison",
        expected: "This chart shows average values for each group.",
      },
    ];

    for (const scenario of scenarios) {
      fireEvent.click(screen.getByRole("radio", { name: scenario.label }));

      await waitFor(() => {
        expect(screen.getByText(/How to read this chart/)).toBeInTheDocument();
      });

      expect(screen.getByText(new RegExp(scenario.expected, "i"))).toBeInTheDocument();
    }
  });

  it("uses resolver with the local proxy base when rendering chart images", async () => {
    render(<ChartsTab />);

    fireEvent.click(screen.getByRole("radio", { name: "Grouped Comparison" }));

    await waitFor(() => {
      expect(resolveApiAssetUrl).toHaveBeenCalledWith("/static/plots/grouped_comparison.png", "/api-local");
    });
  });

  it("shows dataset source metadata in overview when available", async () => {
    render(<ChartsTab activeDatasetId="sales_csv" />);

    expect(await screen.findByText("Source: Superstore Sales Dataset")).toBeInTheDocument();
    expect(screen.getByText("Source Location: opsight-raw/csv/Sample - Superstore.csv")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "https://www.kaggle.com/datasets/vivek468/superstore-dataset-final" })).toBeInTheDocument();
    expect(screen.getByText("Shape: 10 x 3")).toBeInTheDocument();
    expect(screen.getByText("entity_id: 0")).toBeInTheDocument();
    expect(screen.getByText("metric_value: 1")).toBeInTheDocument();
    expect(screen.getByText("category: 2")).toBeInTheDocument();
    expect(screen.getByText("Furniture: 5")).toBeInTheDocument();
    expect(screen.getByText("Office Supplies: 3")).toBeInTheDocument();
  });

  it("exports summary as json when export button is clicked", async () => {
    const originalCreateObjectURL = URL.createObjectURL;
    const originalRevokeObjectURL = URL.revokeObjectURL;

    URL.createObjectURL = vi.fn(() => "blob:summary");
    URL.revokeObjectURL = vi.fn(() => {});

    const appendSpy = vi.spyOn(document.body, "appendChild");
    const removeSpy = vi.spyOn(document.body, "removeChild");

    const originalCreateElement = document.createElement.bind(document);
    const clickSpy = vi.fn();
    const createElementSpy = vi.spyOn(document, "createElement").mockImplementation((tagName) => {
      const element = originalCreateElement(tagName);
      if (String(tagName).toLowerCase() === "a") {
        element.click = clickSpy;
      }
      return element;
    });

    render(<ChartsTab activeDatasetId="sales_csv" />);

    const exportButton = await screen.findByRole("button", { name: "Export Summary (JSON)" });
    fireEvent.click(exportButton);

    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalled();
    expect(appendSpy).toHaveBeenCalled();
    expect(removeSpy).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:summary");

    createElementSpy.mockRestore();
    URL.createObjectURL = originalCreateObjectURL;
    URL.revokeObjectURL = originalRevokeObjectURL;
  });
});
