import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import AnomalyDetectionTab from "./AnomalyDetectionTab";
import {
  runIsolationForestAnomaly,
  runKmeansAnomaly,
  runZscoreAnomaly,
} from "../api/client";

vi.mock("../api/client", () => ({
  runZscoreAnomaly: vi.fn(),
  runIsolationForestAnomaly: vi.fn(),
  runKmeansAnomaly: vi.fn(),
}));

describe("AnomalyDetectionTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a blocked message and disables model actions when no dataset is loaded", () => {
    render(<AnomalyDetectionTab pipelineCompleted={false} />);

    expect(screen.getByText("You must run a dataset first")).toBeInTheDocument();

    const checkboxes = screen.getAllByRole("checkbox");
    checkboxes.forEach((checkbox) => {
      expect(checkbox).toBeDisabled();
    });

    fireEvent.click(screen.getByLabelText("Z-Score"));
    expect(runZscoreAnomaly).not.toHaveBeenCalled();
  });

  it("enables anomaly execution after the pipeline completes", async () => {
    runZscoreAnomaly.mockResolvedValue({
      ok: true,
      data: {
        summary: { total_records: 5, anomaly_count: 2 },
      },
    });

    render(<AnomalyDetectionTab pipelineCompleted />);

    fireEvent.click(screen.getByLabelText("Z-Score"));

    await waitFor(() => {
      expect(runZscoreAnomaly).toHaveBeenCalledTimes(1);
    });

    expect(screen.queryByText("You must run a dataset first")).not.toBeInTheDocument();
    expect(screen.getByText("2 records were flagged as unusual out of 5.")).toBeInTheDocument();
  });

  it("runs K-Means when selected", async () => {
    runKmeansAnomaly.mockResolvedValue({
      ok: true,
      data: {
        summary: { total_records: 10, anomaly_count: 1 },
        notes: "K-Means clustering using distance from centroid.",
      },
    });

    render(<AnomalyDetectionTab pipelineCompleted />);

    fireEvent.click(screen.getByLabelText("K-Means"));

    await waitFor(() => {
      expect(runKmeansAnomaly).toHaveBeenCalledTimes(1);
    });

    expect(screen.getByText("1 records were flagged as unusual out of 10.")).toBeInTheDocument();
    expect(screen.getByText("K-Means clustering using distance from centroid.")).toBeInTheDocument();
  });

  it("renders top anomaly sample table for Isolation Forest when present", async () => {
    runIsolationForestAnomaly.mockResolvedValue({
      ok: true,
      data: {
        summary: { total_records: 100, anomaly_count: 10 },
        anomaly_sample_top10: [
          {
            row_id: 1023,
            Sales: 2000,
            Profit: -500,
            Discount: 0.8,
            anomaly_score: -0.723456,
          },
        ],
      },
    });

    render(<AnomalyDetectionTab pipelineCompleted />);

    fireEvent.click(screen.getByLabelText("Isolation Forest"));

    await waitFor(() => {
      expect(runIsolationForestAnomaly).toHaveBeenCalledTimes(1);
    });

    expect(screen.getByText("Top 10 Anomalous Records")).toBeInTheDocument();
    expect(screen.getByText("Row ID")).toBeInTheDocument();
    expect(screen.getByText("Sales")).toBeInTheDocument();
    expect(screen.getByText("Profit")).toBeInTheDocument();
    expect(screen.getByText("Discount")).toBeInTheDocument();
    expect(screen.getByText("Anomaly Score")).toBeInTheDocument();
    expect(screen.getByText("1023")).toBeInTheDocument();
    expect(screen.getByText("-0.7235")).toBeInTheDocument();
  });
});


it("does not advertise a duplicate Threshold algorithm", () => {
  render(<AnomalyDetectionTab pipelineCompleted />);
  expect(screen.queryByLabelText("Threshold")).not.toBeInTheDocument();
  expect(screen.getAllByRole("checkbox")).toHaveLength(3);
});

it("shows the actual target field and actionable API selection errors", async () => {
  runZscoreAnomaly.mockResolvedValueOnce({ ok: false, error: "Choose a numeric target in Charts before running ML." });
  render(<AnomalyDetectionTab pipelineCompleted />);
  fireEvent.click(screen.getByLabelText("Z-Score"));
  expect(await screen.findByText("Choose a numeric target in Charts before running ML.")).toBeInTheDocument();
  fireEvent.click(screen.getByLabelText("Z-Score"));
  runZscoreAnomaly.mockResolvedValueOnce({ ok: true, data: { summary: { total_records: 5, anomaly_count: 1 }, dataset_context: { value: "Freight" }, data_quality: { input_records: 7, usable_records: 5, excluded_records: 2 } } });
  fireEvent.click(screen.getByLabelText("Z-Score"));
  expect(await screen.findByText("Freight")).toBeInTheDocument();
  expect(screen.getByText(/2 rows excluded because/)).toBeInTheDocument();
});
