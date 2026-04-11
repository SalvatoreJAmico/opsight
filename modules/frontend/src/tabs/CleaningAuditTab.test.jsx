import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import CleaningAuditTab from "./CleaningAuditTab";
import { getCleaningAudit } from "../api/client";

vi.mock("../api/client", () => ({
  getCleaningAudit: vi.fn(),
}));

describe("CleaningAuditTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows no-dataset message when nothing is active", () => {
    render(<CleaningAuditTab activeDatasetId={null} />);

    expect(screen.getByText("No dataset loaded. Run a dataset to view the cleaning audit.")).toBeInTheDocument();
    expect(getCleaningAudit).not.toHaveBeenCalled();
  });

  it("renders audit metrics and missing values table", async () => {
    getCleaningAudit.mockResolvedValue({
      ok: true,
      status: 200,
      error: null,
      data: {
        source: {
          dataset_id: "sales_csv",
          source_name: "Superstore Sales Dataset",
          source_type: "blob",
          source_location: "opsight-raw/csv/Sample - Superstore.csv",
        },
        row_counts: { before: 12, after: 10 },
        missing_by_column: {
          before: { Sales: 2, Profit: 1 },
          after: { Sales: 0, Profit: 0 },
        },
        duplicates: { before: 3, after: 1 },
        invalid_rows_removed: {
          count: 2,
          reason_counts: {
            "Missing timestamp": 1,
            "Missing features": 1,
          },
        },
      },
    });

    render(<CleaningAuditTab activeDatasetId="sales_csv" />);

    expect(await screen.findByText("Rows Before")).toBeInTheDocument();
    expect(screen.getByText("Rows After")).toBeInTheDocument();
    expect(screen.getByText("Duplicates Before")).toBeInTheDocument();
    expect(screen.getByText("Duplicates After")).toBeInTheDocument();
    expect(screen.getByText("Missing Values By Column")).toBeInTheDocument();
    expect(screen.getByText("Sales")).toBeInTheDocument();
    expect(screen.getByText("Profit")).toBeInTheDocument();
    expect(screen.getByText("Total Removed: 2")).toBeInTheDocument();
    expect(screen.getByText("Missing timestamp: 1")).toBeInTheDocument();
  });

  it("switches API target in dev mode and refetches", async () => {
    getCleaningAudit.mockResolvedValue({
      ok: true,
      status: 200,
      error: null,
      data: {
        row_counts: { before: 1, after: 1 },
        missing_by_column: { before: {}, after: {} },
        duplicates: { before: 0, after: 0 },
        invalid_rows_removed: { count: 0, reason_counts: {} },
      },
    });

    render(<CleaningAuditTab activeDatasetId="sales_csv" />);

    await waitFor(() => {
      expect(getCleaningAudit).toHaveBeenCalledTimes(1);
    });

    fireEvent.click(screen.getByRole("button", { name: "Cloud" }));

    await waitFor(() => {
      expect(getCleaningAudit).toHaveBeenCalledTimes(2);
    });
  });
});
