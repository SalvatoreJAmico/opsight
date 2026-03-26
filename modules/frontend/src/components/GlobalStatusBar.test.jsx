import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import GlobalStatusBar, { resolveStatusMessage } from "./GlobalStatusBar";

describe("resolveStatusMessage", () => {
  it("returns no-dataset message when sessionState is null", () => {
    const msg = resolveStatusMessage(null);
    expect(msg.text).toBe("No dataset loaded \u2014 select a dataset to get started");
    expect(msg.type).toBe("default");
  });

  it("returns no-dataset message when active_dataset is null", () => {
    const msg = resolveStatusMessage({ active_dataset: null });
    expect(msg.text).toBe("No dataset loaded \u2014 select a dataset to get started");
    expect(msg.type).toBe("default");
  });

  it("returns dataset loaded message in idle state", () => {
    const msg = resolveStatusMessage({
      active_dataset: "sales_csv",
      pipeline_status: "not_run",
      anomaly_status: "idle",
      prediction_status: "idle",
    });
    expect(msg.text).toBe("Dataset loaded: sales_csv");
    expect(msg.type).toBe("default");
  });

  it("prioritises pipeline failed over all other states", () => {
    const msg = resolveStatusMessage({
      active_dataset: "sales_csv",
      pipeline_status: "failed",
      anomaly_status: "running",
    });
    expect(msg.text).toBe("Pipeline failed \u2014 check the logs");
    expect(msg.type).toBe("failed");
  });

  it("returns pipeline running message", () => {
    const msg = resolveStatusMessage({
      active_dataset: "sales_csv",
      pipeline_status: "running",
    });
    expect(msg.text).toBe("Pipeline is running...");
    expect(msg.type).toBe("running");
  });

  it("returns anomaly running message when pipeline is not running", () => {
    const msg = resolveStatusMessage({
      active_dataset: "sales_csv",
      pipeline_status: "completed",
      anomaly_status: "running",
    });
    expect(msg.text).toBe("Anomaly detection running...");
    expect(msg.type).toBe("running");
  });

  it("returns prediction running message", () => {
    const msg = resolveStatusMessage({
      active_dataset: "sales_csv",
      pipeline_status: "not_run",
      anomaly_status: "idle",
      prediction_status: "running",
    });
    expect(msg.text).toBe("Prediction model running...");
    expect(msg.type).toBe("running");
  });

  it("returns pipeline completed message", () => {
    const msg = resolveStatusMessage({
      active_dataset: "sales_csv",
      pipeline_status: "completed",
      anomaly_status: "idle",
      prediction_status: "idle",
    });
    expect(msg.text).toBe("Pipeline completed successfully");
    expect(msg.type).toBe("completed");
  });

  it("returns anomaly completed message", () => {
    const msg = resolveStatusMessage({
      active_dataset: "sales_csv",
      pipeline_status: "not_run",
      anomaly_status: "completed",
      prediction_status: "idle",
    });
    expect(msg.text).toBe("Anomaly detection complete");
    expect(msg.type).toBe("completed");
  });

  it("returns prediction completed message", () => {
    const msg = resolveStatusMessage({
      active_dataset: "sales_csv",
      pipeline_status: "not_run",
      anomaly_status: "idle",
      prediction_status: "completed",
    });
    expect(msg.text).toBe("Prediction complete");
    expect(msg.type).toBe("completed");
  });
});

describe("GlobalStatusBar", () => {
  it("renders the resolved message in the status bar", () => {
    render(
      <GlobalStatusBar
        sessionState={{
          active_dataset: "sales_csv",
          pipeline_status: "completed",
          anomaly_status: "idle",
          prediction_status: "idle",
        }}
      />,
    );
    expect(screen.getByText("Pipeline completed successfully")).toBeTruthy();
  });

  it("renders no-dataset message when sessionState is null", () => {
    render(<GlobalStatusBar sessionState={null} />);
    expect(
      screen.getByText("No dataset loaded — select a dataset to get started"),
    ).toBeTruthy();
  });

  it("renders failure message with higher priority than running", () => {
    render(
      <GlobalStatusBar
        sessionState={{
          active_dataset: "sales_csv",
          pipeline_status: "failed",
          anomaly_status: "running",
        }}
      />,
    );
    expect(screen.getByText("Pipeline failed \u2014 check the logs")).toBeTruthy();
  });
});
