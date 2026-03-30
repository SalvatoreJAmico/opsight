import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import DatasetTab from "./DatasetTab";
import { triggerPipeline } from "../api/client";

const expectedDefaultBaseUrl = import.meta.env.DEV ? "/api-local" : "/api-cloud";

vi.mock("../api/client", () => ({
  triggerPipeline: vi.fn(),
}));

describe("DatasetTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state while request is in progress", async () => {
    triggerPipeline.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, data: { status: "processed" } }), 20)),
    );

    render(<DatasetTab />);

    fireEvent.change(screen.getByLabelText("Dataset"), { target: { value: "sales_csv" } });

    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(screen.getByRole("button", { name: "Running..." })).toBeDisabled();

    await waitFor(() => {
      expect(screen.getByText(/Dataset run triggered successfully/)).toBeInTheDocument();
    });
  });

  it("handles API error response", async () => {
    triggerPipeline.mockResolvedValue({
      ok: false,
      status: 500,
      error: "Internal server error",
      data: null,
    });

    render(<DatasetTab />);

    fireEvent.change(screen.getByLabelText("Dataset"), { target: { value: "sales_csv" } });

    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(await screen.findByText("Internal server error")).toBeInTheDocument();
  });

  it("renders success and response payload when trigger succeeds", async () => {
    triggerPipeline.mockResolvedValue({
      ok: true,
      status: 200,
      error: null,
      data: {
        status: "processed",
        dataset_id: "sales_csv",
        dataset_source_type: "blob",
        dataset_path: "opsight-raw/csv/Sample - Superstore.csv",
        records_ingested: 3,
      },
    });

    render(<DatasetTab />);

    fireEvent.change(screen.getByLabelText("Dataset"), { target: { value: "sales_csv" } });

    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(await screen.findByText(/Dataset run triggered successfully/)).toBeInTheDocument();
    expect(screen.getByText(/Response/)).toBeInTheDocument();
    expect(screen.getByText("Dataset Execution")).toBeInTheDocument();
    expect(screen.getByText(/Dataset:/)).toBeInTheDocument();
    expect(screen.getByText(/Source:/)).toBeInTheDocument();
    expect(screen.getByText(/File:/)).toBeInTheDocument();
    expect(screen.getByText(/records_ingested/)).toBeInTheDocument();
    expect(triggerPipeline).toHaveBeenCalledWith(
      expect.objectContaining({
        target: expectedDefaultBaseUrl === "/api-local" ? "local" : "cloud",
        dataset_id: "sales_csv",
      }),
      expect.objectContaining({ baseUrl: expectedDefaultBaseUrl }),
    );
  });

  it("switches to local target when Local button is clicked", async () => {
    triggerPipeline.mockResolvedValue({
      ok: false,
      status: 0,
      error: "Network error",
      data: null,
    });

    render(<DatasetTab />);

    fireEvent.change(screen.getByLabelText("Dataset"), { target: { value: "sales_csv" } });

    fireEvent.click(screen.getByRole("button", { name: "Local" }));
    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(await screen.findByText(/Local API is unavailable/)).toBeInTheDocument();
    expect(triggerPipeline).toHaveBeenCalledWith(
      expect.objectContaining({ target: "local", dataset_id: "sales_csv" }),
      expect.objectContaining({ baseUrl: "/api-local" }),
    );
  });

  it("switches to cloud target when Cloud button is clicked", async () => {
    triggerPipeline.mockResolvedValue({
      ok: true,
      status: 200,
      error: null,
      data: { status: "processed" },
    });

    render(<DatasetTab />);

    fireEvent.change(screen.getByLabelText("Dataset"), { target: { value: "sales_csv" } });

    fireEvent.click(screen.getByRole("button", { name: "Cloud" }));
    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(await screen.findByText(/Dataset run triggered successfully on deployed API/)).toBeInTheDocument();
    expect(triggerPipeline).toHaveBeenCalledWith(
      expect.objectContaining({ target: "cloud", dataset_id: "sales_csv" }),
      expect.objectContaining({ baseUrl: "/api-cloud" }),
    );
  });

  it("triggers pipeline for SQL dataset", async () => {
    triggerPipeline.mockResolvedValue({
      ok: true,
      status: 200,
      error: null,
      data: {
        status: "processed",
        dataset_id: "sales_sql",
        dataset_source_type: "sql",
        dataset_schema: "dbo",
        dataset_table: "Orders",
        records_ingested: 10,
      },
    });

    render(<DatasetTab />);

    fireEvent.change(screen.getByLabelText("Dataset"), { target: { value: "sales_sql" } });
    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    expect(await screen.findByText(/Dataset run triggered successfully/)).toBeInTheDocument();
    expect(triggerPipeline).toHaveBeenCalledWith(
      expect.objectContaining({
        target: expectedDefaultBaseUrl === "/api-local" ? "local" : "cloud",
        dataset_id: "sales_sql",
      }),
      expect.objectContaining({ baseUrl: expectedDefaultBaseUrl }),
    );
  });
});
