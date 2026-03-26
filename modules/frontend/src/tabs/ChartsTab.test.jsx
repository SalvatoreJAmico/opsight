import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import ChartsTab from "./ChartsTab";
import {
  getHistogram,
  getBarCategory,
  getBoxplot,
  getScatter,
  getGroupedComparison,
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

  it("renders observation text for each supported chart", async () => {
    render(<ChartsTab />);

    const scenarios = [
      {
        label: "Histogram",
        expected: "The distribution of metric_value shows how values are spread across the dataset.",
      },
      {
        label: "Category Bar Chart",
        expected: "The bar chart shows how records are distributed across categories.",
      },
      {
        label: "Box Plot",
        expected: "The box plot highlights the spread and potential outliers in metric_value.",
      },
      {
        label: "Scatter Plot",
        expected: "The scatter plot shows the relationship between metric_value and secondary_metric.",
      },
      {
        label: "Grouped Comparison",
        expected: "The grouped comparison chart shows average metric_value across categories.",
      },
    ];

    for (const scenario of scenarios) {
      fireEvent.click(screen.getByRole("radio", { name: scenario.label }));

      await waitFor(() => {
        expect(screen.getByText(/Observations/)).toBeInTheDocument();
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
});
