import React, { useState } from "react";
import ModelCard from "./ModelCard";
import { runRegressionPrediction, runMovingAveragePrediction } from "../api/client";

const predictionModels = [
  {
    key: "linear_regression",
    name: "Linear Regression",
    education: "Projects a simple trend from past values into future values.",
    recommendation: "Use for a quick trend-over-time estimate.",
  },
  {
    key: "moving_average",
    name: "Moving Average",
    education: "Uses the most recent values to estimate the next values.",
    recommendation: "Use for short-term, rolling forecasts.",
  },
];

const PREDICTION_EXPLANATIONS = {
  linear_regression: {
    what: "Shows estimated future values based on the trend in earlier values.",
    time: "Time is used. Values are ordered by timestamp before projecting forward.",
    comparison: "Compares how value changes over time, then extends that trend.",
    where: "This card summarizes returned predictions; predicted rows appear in the model output payload.",
  },
  moving_average: {
    what: "Shows estimated future values based on recent value history.",
    time: "Time is used. Values are ordered by timestamp before averaging recent points.",
    comparison: "Compares each new step to prior recent values over time.",
    where: "This card summarizes returned predictions; predicted rows appear in the model output payload.",
  },
};

const MODEL_RUNNERS = {
  linear_regression: () => runRegressionPrediction(5),
  moving_average: () => runMovingAveragePrediction(5),
};

export default function PredictionTab({ onAction, pipelineCompleted }) {
  const [selectedModels, setSelectedModels] = useState({});
  const [resultsByModel, setResultsByModel] = useState({});
  const isBlocked = !pipelineCompleted;

  const loadModelResults = async (modelKey) => {
    setResultsByModel((prev) => ({
      ...prev,
      [modelKey]: { loading: true, error: "", data: null },
    }));

    const response = await MODEL_RUNNERS[modelKey]();

    if (!response.ok) {
      setResultsByModel((prev) => ({
        ...prev,
        [modelKey]: {
          loading: false,
          error: response.error || "Failed to load results",
          data: null,
        },
      }));
    } else {
      setResultsByModel((prev) => ({
        ...prev,
        [modelKey]: {
          loading: false,
          error: "",
          data: response.data,
        },
      }));
    }
    onAction?.();
  };

  const toggleModel = (key) => {
    if (isBlocked) {
      return;
    }

    const shouldSelect = !selectedModels[key];
    setSelectedModels((prev) => ({
      ...prev,
      [key]: shouldSelect,
    }));

    if (shouldSelect && !resultsByModel[key]?.data) {
      loadModelResults(key);
    }
  };

  return (
    <div>
      <h2>Prediction</h2>

      {isBlocked ? (
        <div
          style={{
            marginTop: "1rem",
            marginBottom: "1rem",
            padding: "1rem",
            border: "1px solid #d8b25f",
            borderRadius: "10px",
          }}
        >
          <strong>Unavailable</strong>
          <p style={{ marginTop: "0.5rem" }}>Run the pipeline before prediction</p>
        </div>
      ) : null}

      {predictionModels.map((model) => {
        const state = resultsByModel[model.key] || {};
        const predictionRows = state.data?.result || [];
        const futureRows = predictionRows.filter((row) => String(row?.timestamp || "").startsWith("t+"));
        const result = state.data ? {
          status: "Completed",
          summary: `Returned ${predictionRows.length} rows, including ${futureRows.length} future estimates.`,
          notes: "Future estimates are labeled with timestamps like t+1, t+2, and so on.",
          datasetContext: state.data?.dataset_context || null,
          explanation: PREDICTION_EXPLANATIONS[model.key],
        } : null;

        return (
          <ModelCard
            key={model.key}
            model={model}
            checked={!!selectedModels[model.key]}
            onToggle={() => toggleModel(model.key)}
            disabled={isBlocked}
            loading={state.loading || false}
            error={state.error || ""}
            result={result}
          />
        );
      })}
    </div>
  );
}