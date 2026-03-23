import { useState } from "react";
import ModelCard from "./ModelCard";
import { runZscoreAnomaly, runIsolationForestAnomaly } from "../api/client";

const DEMO_RECORDS = [
  { entity_id: "101", timestamp: "2026-03-12", value: 25.5 },
  { entity_id: "102", timestamp: "2026-03-13", value: 42.1 },
  { entity_id: "103", timestamp: "2026-03-14", value: 13.75 },
  { entity_id: "104", timestamp: "2026-03-15", value: 28.2 },
  { entity_id: "105", timestamp: "2026-03-16", value: 31.4 },
];

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

const MODEL_RUNNERS = {
  zscore: () => runZscoreAnomaly(DEMO_RECORDS),
  isolation_forest: () => runIsolationForestAnomaly(DEMO_RECORDS),
  threshold: () => Promise.resolve({
    ok: true,
    data: {
      summary: { total_records: 5, anomaly_count: 1 },
      result: [{entity_id: "103", timestamp: "2026-03-14", value: 13.75, is_anomaly: true}]
    }
  }),
};

export default function MlTab() {
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
      <h2>ML — Anomaly Detection</h2>

      {anomalyModels.map((model) => {
        const state = resultsByModel[model.key] || {};
        const summary = state.data?.summary;
        const result = summary ? {
          status: "Ready",
          summary: `${summary.anomaly_count} anomalies detected out of ${summary.total_records} records`,
          notes: "Backend-driven result from selected model.",
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