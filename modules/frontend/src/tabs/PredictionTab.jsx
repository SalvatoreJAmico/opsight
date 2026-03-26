import React, { useState } from "react";
import ModelCard from "./ModelCard";
import { runRegressionPrediction, runMovingAveragePrediction } from "../api/client";

const predictionModels = [
  {
    key: "linear_regression",
    name: "Linear Regression",
    education: "Fits a straight-line trend through numeric values.",
    recommendation: "Best for simple trend-based forecasting.",
  },
  {
    key: "moving_average",
    name: "Moving Average",
    education: "Uses recent values to estimate future values.",
    recommendation: "Best for simple smoothing and short-horizon forecasts.",
  },
];

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
        const result = state.data ? {
          status: "Ready",
          summary: `Generated ${state.data.result?.length || 0} prediction records.`,
          notes: "Includes historical and future predictions from backend model.",
          datasetContext: state.data?.dataset_context || null,
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