import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import PredictionTab from "./PredictionTab";
import { runMovingAveragePrediction, runRegressionPrediction } from "../api/client";

vi.mock("../api/client", () => ({
  runRegressionPrediction: vi.fn(),
  runMovingAveragePrediction: vi.fn(),
}));

describe("PredictionTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a blocked message and disables prediction actions before pipeline completion", () => {
    render(<PredictionTab pipelineCompleted={false} />);

    expect(screen.getByText("Run the pipeline before prediction")).toBeInTheDocument();

    const checkboxes = screen.getAllByRole("checkbox");
    checkboxes.forEach((checkbox) => {
      expect(checkbox).toBeDisabled();
    });

    fireEvent.click(screen.getByLabelText("Linear Regression"));
    expect(runRegressionPrediction).not.toHaveBeenCalled();
  });

  it("enables prediction execution after pipeline completion", async () => {
    runRegressionPrediction.mockResolvedValue({
      ok: true,
      data: {
        result: [{ value: 1 }, { value: 2 }, { value: 3 }],
      },
    });

    render(<PredictionTab pipelineCompleted />);

    fireEvent.click(screen.getByLabelText("Linear Regression"));

    await waitFor(() => {
      expect(runRegressionPrediction).toHaveBeenCalledTimes(1);
    });

    expect(screen.queryByText("Run the pipeline before prediction")).not.toBeInTheDocument();
    expect(screen.getByText("Generated 3 prediction records.")).toBeInTheDocument();
  });
});