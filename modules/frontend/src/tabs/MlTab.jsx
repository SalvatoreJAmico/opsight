import { useState } from "react";
import ModelCard from "./ModelCard";

const anomalyModels = [
  {
    key: "threshold",
    name: "Threshold",
    education: "Flags values above a fixed threshold.",
    recommendation: "Use for simple rule-based anomaly detection.",
  },
  {
    key: "zscore",
    name: "Z-Score",
    education: "Detects values far from the mean using standard deviation.",
    recommendation: "Good baseline, explainable model.",
  },
  {
    key: "isolation_forest",
    name: "Isolation Forest",
    education: "Uses tree-based isolation to detect anomalies.",
    recommendation: "Best for complex, less obvious anomalies.",
  },
];

const anomalyResults = {
  threshold: {
    status: "Ready",
    summary: "Threshold-based anomaly detection available.",
    notes: "Best for simple rule-based checks and demos.",
  },
  zscore: {
    status: "Ready",
    summary: "Z-Score baseline available for explainable anomaly detection.",
    notes: "Useful when you want a statistical baseline.",
  },
  isolation_forest: {
    status: "Ready",
    summary: "Isolation Forest available for more complex anomaly patterns.",
    notes: "Good for less obvious outliers in operational data.",
  },
};

export default function MlTab() {
  const [selectedModels, setSelectedModels] = useState({});

  const toggleModel = (key) => {
    setSelectedModels((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  return (
    <div>
      <h2>ML — Anomaly Detection</h2>

      {anomalyModels.map((model) => (
        <ModelCard
          key={model.key}
          model={model}
          checked={!!selectedModels[model.key]}
          onToggle={() => toggleModel(model.key)}
          result={anomalyResults[model.key]}
        />
      ))}
    </div>
  );
}