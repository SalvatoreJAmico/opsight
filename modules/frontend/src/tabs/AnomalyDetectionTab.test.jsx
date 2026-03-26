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
    render(<AnomalyDetectionTab hasDataset={false} />);

    expect(screen.getByText("You must run a dataset first")).toBeInTheDocument();

    const checkboxes = screen.getAllByRole("checkbox");
    checkboxes.forEach((checkbox) => {
      expect(checkbox).toBeDisabled();
    });

    fireEvent.click(screen.getByLabelText("Z-Score"));
    expect(runZscoreAnomaly).not.toHaveBeenCalled();
  });

  it("enables anomaly execution when a dataset is loaded", async () => {
    runZscoreAnomaly.mockResolvedValue({
      ok: true,
      data: {
        summary: { total_records: 5, anomaly_count: 2 },
      },
    });

    render(<AnomalyDetectionTab hasDataset />);

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

    render(<AnomalyDetectionTab hasDataset />);

    fireEvent.click(screen.getByLabelText("K-Means"));

    await waitFor(() => {
      expect(runKmeansAnomaly).toHaveBeenCalledTimes(1);
    });

    expect(screen.getByText("1 records were flagged as unusual out of 10.")).toBeInTheDocument();
    expect(screen.getByText("K-Means clustering using distance from centroid.")).toBeInTheDocument();
  });
});
