import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import App from "./App";

const clientMocks = vi.hoisted(() => ({
  getHealth: vi.fn(),
  getSessionState: vi.fn(),
  resetSession: vi.fn(),
}));

vi.mock("./api/client", () => ({
  getHealth: clientMocks.getHealth,
  getSessionState: clientMocks.getSessionState,
  resetSession: clientMocks.resetSession,
}));

vi.mock("./tabs/DatasetTab", () => ({
  default: function MockDatasetTab({ onPipelineComplete, onPipelineStart, onAction, onDatasetChange }) {
    return (
      <div>
        <h2>Dataset</h2>
        <button onClick={() => onPipelineStart?.("sales_csv")}>Start Sales Run</button>
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

vi.mock("./tabs/CleaningAuditTab", () => ({
  default: function MockCleaningAuditTab() {
    return <div>Cleaning Audit</div>;
  },
}));

vi.mock("./tabs/AnomalyDetectionTab", () => ({
  default: function MockAnomalyDetectionTab({ pipelineCompleted, onAction }) {
    const [result, setResult] = React.useState(false);
    return <div><button disabled={!pipelineCompleted} onClick={() => setResult(true)}>Run anomaly</button>
      <button onClick={onAction}>Refresh analysis state</button>
      {result && <p>Old anomaly result</p>}</div>;
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
    clientMocks.resetSession.mockResolvedValue({
      ok: true,
      data: {
        status: "reset",
        session: {
          active_dataset: null,
          pipeline_status: "not_run",
          anomaly_status: "idle",
          prediction_status: "idle",
        },
      },
    });
  });

  it("distinguishes the working demo from its long-term dataset goal", async () => {
    clientMocks.getSessionState.mockResolvedValue({ ok: true, data: {} });
    render(<App />);
    expect(screen.getByText("A working demo for operational analytics, visualization, and anomaly detection.")).toBeInTheDocument();
    expect(screen.getByText("Tested with selected CSV, SQL, JSON, Parquet, and XLSX datasets. Long-term goal: support every dataset.")).toBeInTheDocument();
    await screen.findByText("API connected");
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

  it("resets session and clears stale UI state", async () => {
    let sessionResponse = {
      active_dataset: "sales_csv",
      pipeline_status: "completed",
      anomaly_status: "idle",
      prediction_status: "idle",
    };

    clientMocks.resetSession.mockImplementation(async () => {
      sessionResponse = {
        active_dataset: null,
        pipeline_status: "not_run",
        anomaly_status: "idle",
        prediction_status: "idle",
      };

      return {
        ok: true,
        data: {
          status: "reset",
          session: sessionResponse,
        },
      };
    });

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

    fireEvent.click(screen.getByRole("button", { name: "Reset Session" }));

    await waitFor(() => {
      expect(clientMocks.resetSession).toHaveBeenCalledTimes(1);
    });

    expect(screen.getByRole("heading", { name: "Dataset" })).toBeInTheDocument();
    expect(screen.getByText("No dataset loaded — select a dataset to get started")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Metrics" }));
    expect(screen.getByText("No data yet. Run the pipeline from the Dataset tab.")).toBeInTheDocument();
    expect(screen.queryByText("11")).not.toBeInTheDocument();
  });
});

describe("App analysis safety", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clientMocks.getHealth.mockResolvedValue({ ok: true, data: {} });
  });

  it("restores completed run metrics from the session after reload", async () => {
    clientMocks.getSessionState.mockResolvedValue({ ok: true, data: {
      active_dataset: "sales_csv", pipeline_status: "completed", pipeline_run_id: "run-1",
      pipeline_summary: { records_ingested: 17, records_valid: 16, records_invalid: 1, records_persisted: 16 },
    } });
    render(<App />);
    await screen.findByText("Pipeline completed successfully");
    fireEvent.click(screen.getByRole("button", { name: "Metrics" }));
    expect(screen.getByText("17")).toBeInTheDocument();
  });

  it.each(["not_run", "running", "failed"])("blocks anomaly for a selected dataset with %s status", async (status) => {
    clientMocks.getSessionState.mockResolvedValue({ ok: true, data: { active_dataset: "sales_csv", pipeline_status: status } });
    render(<App />);
    await waitFor(() => expect(clientMocks.getSessionState).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Anomaly Detection" }));
    expect(screen.getByRole("button", { name: "Run anomaly" })).toBeDisabled();
  });

  it("blocks anomaly immediately when rerunning the same dataset", async () => {
    clientMocks.getSessionState.mockResolvedValue({ ok: true, data: { active_dataset: "sales_csv", pipeline_status: "completed" } });
    render(<App />);
    await screen.findByText("Pipeline completed successfully");
    fireEvent.click(screen.getByRole("button", { name: "Start Sales Run" }));
    fireEvent.click(screen.getByRole("button", { name: "Anomaly Detection" }));
    expect(screen.getByRole("button", { name: "Run anomaly" })).toBeDisabled();
  });

  it.each([
    { pipeline_run_id: "run-2" },
    { selected_variables: { target: "Profit" } },
    { active_dataset: "customers_json" },
    { pipeline_status: "failed" },
  ])("clears model results after session identity changes: %j", async (change) => {
    let session = { active_dataset: "sales_csv", pipeline_status: "completed", pipeline_run_id: "run-1", selected_variables: { target: "Sales" } };
    clientMocks.getSessionState.mockImplementation(async () => ({ ok: true, data: session }));
    render(<App />);
    await screen.findByText("Pipeline completed successfully");
    fireEvent.click(screen.getByRole("button", { name: "Anomaly Detection" }));
    fireEvent.click(screen.getByRole("button", { name: "Run anomaly" }));
    expect(screen.getByText("Old anomaly result")).toBeInTheDocument();
    session = { ...session, ...change };
    fireEvent.click(screen.getByRole("button", { name: "Refresh analysis state" }));
    await waitFor(() => expect(screen.queryByText("Old anomaly result")).not.toBeInTheDocument());
  });

  it("ignores a stale initial session response after a dataset selection", async () => {
    let resolveSession;
    clientMocks.getSessionState.mockImplementation(() => new Promise(resolve => { resolveSession = resolve; }));
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Switch To Customers" }));
    await act(async () => resolveSession({ ok: true, data: { active_dataset: "sales_csv", pipeline_status: "completed" } }));
    expect(screen.getByText("Dataset loaded: customers_json")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Anomaly Detection" }));
    expect(screen.getByRole("button", { name: "Run anomaly" })).toBeDisabled();
  });
});
