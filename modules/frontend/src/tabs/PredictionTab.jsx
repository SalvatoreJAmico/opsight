import { useState } from "react";
import ModelCard from "./ModelCard";
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
const predictionResults = {
  linear_regression: {
    status: "Ready",
    summary: "Linear regression prediction model available.",
    notes: "Best for simple trend-based forecasts.",
  },
  moving_average: {
    status: "Ready",
    summary: "Moving average prediction model available.",
    notes: "Best for short-horizon smoothing and baseline forecasting.",
  },
};
export default function PredictionTab() {
  const [selectedModels, setSelectedModels] = useState({});

  const toggleModel = (key) => {
    setSelectedModels((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  return (
    <div>
      <h2>Prediction</h2>

      {predictionModels.map((model) => (
            <ModelCard
                key={model.key}
                model={model}
                checked={!!selectedModels[model.key]}
                onToggle={() => toggleModel(model.key)}
                result={predictionResults[model.key]}
            />
            ))}
    </div>
  );
}