import React, { useState } from "react";
import ModelCard from "./ModelCard";
import {
  runIsolationForestAnomaly,
  runKmeansAnomaly,
  runZscoreAnomaly,
} from "../api/client";

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
  {
    key: "kmeans",
    name: "K-Means",
    education: "Clusters records and flags points far from their assigned centroid.",
    recommendation: "Useful classical baseline for unsupervised anomaly comparison.",
  },
];

const MODEL_RUNNERS = {
  zscore: () => runZscoreAnomaly(),
  isolation_forest: () => runIsolationForestAnomaly(),
  kmeans: () => runKmeansAnomaly(),
  threshold: () => runZscoreAnomaly(),
};

export default function MlTab({ onAction, hasDataset }) {
  const [selectedModels, setSelectedModels] = useState({});
  const [resultsByModel, setResultsByModel] = useState({});
  const isBlocked = !hasDataset;

  const loadModelResults = async (modelKey) => {
    console.log(`[MlTab] Starting load for ${modelKey}`);
    
    setResultsByModel((prev) => ({
      ...prev,
      [modelKey]: { loading: true, error: "", data: null },
    }));

    try {
      const response = await MODEL_RUNNERS[modelKey]();
      console.log(`[MlTab] Response for ${modelKey}:`, response);

      if (!response || !response.ok) {
        const errorMsg = response?.error || "Failed to load results";
        console.error(`[MlTab] Error for ${modelKey}:`, errorMsg);
        
        setResultsByModel((prev) => ({
          ...prev,
          [modelKey]: {
            loading: false,
            error: errorMsg,
            data: null,
          },
        }));
        return;
      }

      console.log(`[MlTab] Success for ${modelKey}, data:`, response.data);
      
      setResultsByModel((prev) => ({
        ...prev,
        [modelKey]: {
          loading: false,
          error: "",
          data: response.data,
        },
      }));
    } catch (err) {
      console.error(`[MlTab] Exception for ${modelKey}:`, err);
      
      setResultsByModel((prev) => ({
        ...prev,
        [modelKey]: {
          loading: false,
          error: err.message || "Network error",
          data: null,
        },
      }));
    } finally {
      onAction?.();
    }
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
      <h2>Anomaly Detection</h2>

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
          <p style={{ marginTop: "0.5rem" }}>You must run a dataset first</p>
        </div>
      ) : null}

      {anomalyModels.map((model) => {
        const state = resultsByModel[model.key] || {};
        const summary = state.data?.summary;
        const result = summary ? {
          status: "Ready",
          summary: `${summary.anomaly_count} anomalies detected out of ${summary.total_records} records`,
          notes: state.data?.notes || "Backend-driven result from selected model.",
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