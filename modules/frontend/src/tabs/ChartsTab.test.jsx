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
        variables: 6,
        shape: { rows: 10, columns: 15 },
        fields: ["Sales", "Profit", "Quantity", "Discount", "Category", "Order Date"],
        assignment_analysis: {
          target_variable: "Sales",
          target_options: ["Sales"],
          compare_options: ["Profit", "Quantity", "Discount", "Category", "Order Date"],
        },
        missing_by_column: {
          Sales: 1,
          Profit: 0,
          Quantity: 0,
          Discount: 0,
          Category: 2,
          "Order Date": 0,
        },
        numeric_summary: [
          {
            field: "Sales",
            count: 9,
            missing: 1,
            min: 1,
            max: 20,
            mean: 10,
            median: 9,
            std: 3.5,
          },
          {
            field: "Profit",
            count: 10,
            missing: 0,
            min: 1,
            max: 9,
            mean: 5,
            median: 5,
            std: 2.1,
          },
          {
            field: "Quantity",
            count: 10,
            missing: 0,
            min: 1,
            max: 5,
            mean: 2,
            median: 2,
            std: 1.2,
          },
        ],
        date_summary: [
          {
            field: "Order Date",
            count: 10,
            missing: 0,
            min_date: "2026-01-01",
            max_date: "2026-01-03",
          },
        ],
        categorical_summary: [
          {
            field: "Category",
            count: 8,
            missing: 2,
            unique: 2,
            top_values: [
              { value: "Furniture", count: 5 },
              { value: "Office Supplies", count: 3 },
            ],
          },
          {
            field: "Segment",
            count: 10,
            missing: 0,
            unique: 2,
            top_values: [
              { value: "Consumer", count: 6 },
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

  it("limits target and compare selectors to the assignment analysis fields", async () => {
    render(<ChartsTab activeDatasetId="sales_csv" />);

    const targetSelect = await screen.findByLabelText("Target Variable");
    const compareSelect = screen.getByLabelText("Compare Variable");

    expect(targetSelect).toHaveValue("Sales");
    expect(screen.getAllByRole("option", { name: "Sales" })).not.toHaveLength(0);
    expect(screen.getByRole("option", { name: "Profit" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Quantity" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Discount" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Category" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Order Date" })).toBeInTheDocument();

    fireEvent.change(compareSelect, { target: { value: "Category" } });
    fireEvent.click(screen.getByRole("radio", { name: "Category Bar Chart" }));

    await waitFor(() => {
      expect(getBarCategory).toHaveBeenCalledWith(
        expect.objectContaining({
          baseUrl: "/api-local",
          targetVariable: "Sales",
          compareVariable: "Category",
        }),
      );
    });
  });

  it("shows dataset source metadata in overview when available", async () => {
    render(<ChartsTab activeDatasetId="sales_csv" />);

    expect(await screen.findByText("Source: Superstore Sales Dataset")).toBeInTheDocument();
    expect(screen.getByText("Source Location: opsight-raw/csv/Sample - Superstore.csv")).toBeInTheDocument();
    expect(screen.getByText("Source URL: https://www.kaggle.com/datasets/vivek468/superstore-dataset-final")).toBeInTheDocument();
    expect(screen.getByText("Shape: 10 x 15")).toBeInTheDocument();
    expect(screen.getByText("Sales: 1")).toBeInTheDocument();
    expect(screen.getByText("Category: 2")).toBeInTheDocument();
    expect(screen.queryByText("Profit: 0")).not.toBeInTheDocument();
    expect(screen.getByText("Analysis Fields: Sales, Profit, Quantity, Discount, Category, Order Date")).toBeInTheDocument();
    expect(screen.queryByText("No categorical summary available for the selected variables.")).not.toBeInTheDocument();
  });

  it("shows a single message when the dataset has no missing values", async () => {
    getChartOverview.mockResolvedValueOnce({
      ok: true,
      status: 200,
      error: null,
      data: {
        source: "Superstore Sales Dataset",
        source_metadata: {
          source_name: "Superstore Sales Dataset",
        },
        rows: 10,
        variables: 6,
        shape: { rows: 10, columns: 15 },
        fields: ["Sales", "Profit", "Quantity", "Discount", "Category", "Order Date"],
        assignment_analysis: {
          target_variable: "Sales",
          target_options: ["Sales"],
          compare_options: ["Profit", "Quantity", "Discount", "Category", "Order Date"],
        },
        missing_by_column: {
          Sales: 0,
          Profit: 0,
          Quantity: 0,
          Discount: 0,
          Category: 0,
          "Order Date": 0,
        },
        numeric_summary: [
          {
            field: "Sales",
            count: 10,
            missing: 0,
            min: 1,
            max: 20,
            mean: 10,
            median: 9,
            std: 3.5,
          },
          {
            field: "Profit",
            count: 10,
            missing: 0,
            min: 1,
            max: 9,
            mean: 5,
            median: 5,
            std: 2.1,
          },
        ],
        date_summary: [
          {
            field: "Order Date",
            count: 10,
            missing: 0,
            min_date: "2026-01-01",
            max_date: "2026-01-03",
          },
        ],
        categorical_summary: [],
      },
    });

    render(<ChartsTab activeDatasetId="sales_csv" />);

    expect(await screen.findByText("Missing Values: None detected")).toBeInTheDocument();
    expect(screen.queryByText("Sales: 0")).not.toBeInTheDocument();
    expect(screen.queryByText("Category: 0")).not.toBeInTheDocument();
  });

  it("shows only summaries for the selected target and compare variables", async () => {
    render(<ChartsTab activeDatasetId="sales_csv" />);

    expect(await screen.findByTestId("numeric-summary-card-sales")).toBeInTheDocument();
    expect(screen.getByTestId("numeric-summary-card-profit")).toBeInTheDocument();
    expect(screen.queryByTestId("numeric-summary-card-quantity")).not.toBeInTheDocument();
    expect(screen.queryByText(/Category \(Unique:/)).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Compare Variable"), { target: { value: "Category" } });

    expect(await screen.findByTestId("categorical-summary-card-category")).toBeInTheDocument();
    expect(screen.getByText("Furniture: 5")).toBeInTheDocument();
    expect(screen.getByText("Office Supplies: 3")).toBeInTheDocument();
    expect(screen.queryByTestId("numeric-summary-card-profit")).not.toBeInTheDocument();
    expect(screen.queryByText(/Order Date \(Unique:/)).not.toBeInTheDocument();
  });

  it("matches selected variables to summary fields even when backend field names use lowercase or underscores", async () => {
    getChartOverview.mockResolvedValueOnce({
      ok: true,
      status: 200,
      error: null,
      data: {
        source: "Superstore Sales Dataset",
        source_metadata: {
          source_name: "Superstore Sales Dataset",
        },
        rows: 10,
        variables: 6,
        shape: { rows: 10, columns: 15 },
        fields: ["Sales", "Profit", "Quantity", "Discount", "Category", "Order Date"],
        assignment_analysis: {
          target_variable: "Sales",
          target_options: ["Sales"],
          compare_options: ["Profit", "Quantity", "Discount", "Category", "Order Date"],
        },
        missing_by_column: {
          Sales: 1,
          Profit: 0,
          Category: 2,
          "Order Date": 0,
        },
        numeric_summary: [
          {
            field: "sales",
            count: 9,
            missing: 1,
            min: 1,
            max: 20,
            mean: 10,
            median: 9,
            std: 3.5,
          },
          {
            field: "profit",
            count: 10,
            missing: 0,
            min: 1,
            max: 9,
            mean: 5,
            median: 5,
            std: 2.1,
          },
        ],
        date_summary: [
          {
            field: "order_date",
            count: 10,
            missing: 0,
            min_date: "2026-01-01",
            max_date: "2026-01-03",
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
            ],
          },
          {
            field: "segment",
            count: 10,
            missing: 0,
            unique: 2,
            top_values: [
              { value: "Consumer", count: 6 },
            ],
          },
        ],
      },
    });

    render(<ChartsTab activeDatasetId="sales_csv" />);

    expect(await screen.findByTestId("numeric-summary-card-sales")).toBeInTheDocument();
    expect(screen.getByTestId("numeric-summary-card-profit")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Compare Variable"), { target: { value: "Order Date" } });

    expect(await screen.findByTestId("date-summary-card-order-date")).toBeInTheDocument();
    expect(screen.getByText("Min Date: 2026-01-01")).toBeInTheDocument();
    expect(screen.getByText("Max Date: 2026-01-03")).toBeInTheDocument();
  });

  it("shows a date summary when Order Date is selected", async () => {
    render(<ChartsTab activeDatasetId="sales_csv" />);

    fireEvent.change(await screen.findByLabelText("Compare Variable"), { target: { value: "Order Date" } });

    expect(await screen.findByTestId("date-summary-card-order-date")).toBeInTheDocument();
    expect(screen.getByText("Min Date: 2026-01-01")).toBeInTheDocument();
    expect(screen.getByText("Max Date: 2026-01-03")).toBeInTheDocument();
    expect(screen.getByText("Count: 10")).toBeInTheDocument();
    expect(screen.getByText("Missing: 0")).toBeInTheDocument();
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
