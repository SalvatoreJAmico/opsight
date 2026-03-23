import { useState } from "react";
import ModelCard from "./ModelCard";
import { runRegressionPrediction, runMovingAveragePrediction } from "../api/client";

const DEMO_RECORDS = [
  { entity_id: "101", timestamp: "2026-03-12", value: 25.5 },
  { entity_id: "102", timestamp: "2026-03-13", value: 42.1 },
  { entity_id: "103", timestamp: "2026-03-14", value: 13.75 },
  { entity_id: "104", timestamp: "2026-03-15", value: 28.2 },
  { entity_id: "105", timestamp: "2026-03-16", value: 31.4 },
];

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
  linear_regression: () => runRegressionPrediction(DEMO_RECORDS, 3),
  moving_average: () => runMovingAveragePrediction(DEMO_RECORDS, 3),
};

export default function PredictionTab() {
  const [selectedModels, setSelectedModels] = useState({});
  const [resultsByModel, setResultsByModel] = useState({});

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
      return;
    }

    setResultsByModel((prev) => ({
      ...prev,
      [modelKey]: {
        loading: false,
        error: "",
        data: response.data,
      },
    }));
  };

  const toggleModel = (key) => {
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

      {predictionModels.map((model) => {
        const state = resultsByModel[model.key] || {};
        const result = state.data ? {
          status: "Ready",
          summary: `Generated ${state.data.result?.length || 0} prediction records.`,
          notes: "Includes historical and future predictions from backend model.",
        } : null;

        return (
          <ModelCard
            key={model.key}
            model={model}
            checked={!!selectedModels[model.key]}
            onToggle={() => toggleModel(model.key)}
            loading={state.loading || false}
            error={state.error || ""}
            result={result}
          />
        );
      })}
    </div>
  );
}