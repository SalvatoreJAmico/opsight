import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import MlTab from "./MlTab";
import { runIsolationForestAnomaly, runZscoreAnomaly } from "../api/client";

vi.mock("../api/client", () => ({
  runZscoreAnomaly: vi.fn(),
  runIsolationForestAnomaly: vi.fn(),
}));

describe("MlTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a blocked message and disables model actions when no dataset is loaded", () => {
    render(<MlTab hasDataset={false} />);

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

    render(<MlTab hasDataset />);

    fireEvent.click(screen.getByLabelText("Z-Score"));

    await waitFor(() => {
      expect(runZscoreAnomaly).toHaveBeenCalledTimes(1);
    });

    expect(screen.queryByText("You must run a dataset first")).not.toBeInTheDocument();
    expect(screen.getByText("2 anomalies detected out of 5 records")).toBeInTheDocument();
  });
});