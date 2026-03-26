import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import App from "./App";

const clientMocks = vi.hoisted(() => ({
  getHealth: vi.fn(),
  getSessionState: vi.fn(),
}));

vi.mock("./api/client", () => ({
  getHealth: clientMocks.getHealth,
  getSessionState: clientMocks.getSessionState,
}));

vi.mock("./tabs/UploadTab", () => ({
  default: function MockDatasetTab({ onPipelineComplete, onAction, onDatasetChange }) {
    return (
      <div>
        <h2>Dataset</h2>
        <button type="button" onClick={() => onPipelineComplete({ records_ingested: 11, records_valid: 10, records_invalid: 1, records_persisted: 10 })}>
          Seed Sales Metrics
        </button>
        <button type="button" onClick={() => onPipelineComplete({ records_ingested: 4, records_valid: 4, records_invalid: 0, records_persisted: 4 })}>
          Seed Customer Metrics
        </button>
        <button type="button" onClick={() => onDatasetChange("customers_json")}>
          Switch To Customers
        </button>
        <button type="button" onClick={() => onAction?.()}>
          Refresh Session
        </button>
      </div>
    );
  },
}));

vi.mock("./tabs/ChartsTab", () => ({
  default: function MockChartsTab() {
    return <div>Charts</div>;
  },
}));

vi.mock("./tabs/MlTab", () => ({
  default: function MockMlTab() {
    return <div>ML</div>;
  },
}));

vi.mock("./tabs/PredictionTab", () => ({
  default: function MockPredictionTab() {
    return <div>Prediction</div>;
  },
}));

describe("App dataset switching", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clientMocks.getHealth.mockResolvedValue({
      ok: true,
      data: { version: "test" },
    });
  });

  it("clears stale metrics and only shows new dataset results after a switch", async () => {
    let sessionResponse = {
      active_dataset: "sales_csv",
      pipeline_status: "completed",
      anomaly_status: "idle",
      prediction_status: "idle",
    };

    clientMocks.getSessionState.mockImplementation(async () => ({
      ok: true,
      data: sessionResponse,
    }));

    render(<App />);

    await screen.findByText("Pipeline completed successfully");

    fireEvent.click(screen.getByRole("button", { name: "Seed Sales Metrics" }));
    fireEvent.click(screen.getByRole("button", { name: "Metrics" }));

    await waitFor(() => {
      expect(screen.getByText("11")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Dataset" }));
    fireEvent.click(screen.getByRole("button", { name: "Switch To Customers" }));

    expect(screen.getByText("Dataset loaded: customers_json")).toBeInTheDocument();
    expect(screen.queryByText("Pipeline completed successfully")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Metrics" }));

    expect(screen.getByText("No data yet. Run the pipeline from the Dataset tab.")).toBeInTheDocument();
    expect(screen.queryByText("11")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Dataset" }));
    sessionResponse = {
      active_dataset: "customers_json",
      pipeline_status: "completed",
      anomaly_status: "idle",
      prediction_status: "idle",
    };

    fireEvent.click(screen.getByRole("button", { name: "Seed Customer Metrics" }));
    fireEvent.click(screen.getByRole("button", { name: "Refresh Session" }));

    await waitFor(() => {
      expect(screen.getByText("Pipeline completed successfully")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Metrics" }));

    expect(screen.getAllByText("4").length).toBeGreaterThan(0);
    expect(screen.queryByText("11")).not.toBeInTheDocument();
  });

  it("keeps the pending dataset reset visible when polling still returns the old dataset", async () => {
    clientMocks.getSessionState.mockResolvedValue({
      ok: true,
      data: {
        active_dataset: "sales_csv",
        pipeline_status: "completed",
        anomaly_status: "idle",
        prediction_status: "idle",
      },
    });

    render(<App />);

    await screen.findByText("Pipeline completed successfully");

    fireEvent.click(screen.getByRole("button", { name: "Switch To Customers" }));
    fireEvent.click(screen.getByRole("button", { name: "Refresh Session" }));

    await waitFor(() => {
      expect(screen.getByText("Dataset loaded: customers_json")).toBeInTheDocument();
    });

    expect(screen.queryByText("Pipeline completed successfully")).not.toBeInTheDocument();
  });
});