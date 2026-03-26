import React, { useState } from "react";
const isDev = import.meta.env.DEV;
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
    education: "Marks records as unusual when values are far from the normal range.",
    recommendation: "Use when you want a simple first-pass anomaly check.",
  },
  {
    key: "zscore",
    name: "Z-Score",
    education: "Finds records with values far from the dataset average.",
    recommendation: "Use when you want a clear baseline for unusual values.",
  },
  {
    key: "isolation_forest",
    name: "Isolation Forest",
    education: "Finds records that are hard to group with the rest of the dataset.",
    recommendation: "Use when unusual values are subtle or mixed.",
  },
  {
    key: "kmeans",
    name: "K-Means",
    education: "Groups records and flags values that sit far from their group center.",
    recommendation: "Use for cluster-based anomaly comparison.",
  },
];

const ANOMALY_EXPLANATIONS = {
  threshold: {
    what: "Shows how many records were marked unusual by a threshold rule.",
    time: "Time is not used. Records are compared across the dataset.",
    comparison: "Each value is compared to a baseline range from dataset values.",
    where: "The anomaly count and model summary are shown in this card.",
  },
  zscore: {
    what: "Shows records with values far from the average value.",
    time: "Time is not used. Records are compared across the dataset.",
    comparison: "Each value is compared to the dataset mean and spread.",
    where: "The anomaly count and model summary are shown in this card.",
  },
  isolation_forest: {
    what: "Shows records that behave differently from most other records.",
    time: "Time is not used. Records are compared across the dataset.",
    comparison: "Each record is compared to overall value patterns in the dataset.",
    where: "The anomaly count and model summary are shown in this card.",
  },
  kmeans: {
    what: "Shows records that are far from the center of their value group.",
    time: "Time is not used. Records are compared across the dataset.",
    comparison: "Each value is compared to its cluster center distance.",
    where: "The anomaly count and model summary are shown in this card.",
  },
};

const MODEL_RUNNERS = {
  zscore: () => runZscoreAnomaly(),
  isolation_forest: () => runIsolationForestAnomaly(),
  kmeans: () => runKmeansAnomaly(),
  threshold: () => runZscoreAnomaly(),
};

export default function AnomalyDetectionTab({ onAction, hasDataset }) {
  const [selectedModels, setSelectedModels] = useState({});
  const [resultsByModel, setResultsByModel] = useState({});
  const isBlocked = !hasDataset;

  const loadModelResults = async (modelKey) => {
    setResultsByModel((prev) => ({
      ...prev,
      [modelKey]: { loading: true, error: "", data: null },
    }));

    try {
      const response = await MODEL_RUNNERS[modelKey]();

      if (!response || !response.ok) {
        const errorMsg = response?.error || "Failed to load results";
        if (isDev) console.error(`[AnomalyDetectionTab] Error for ${modelKey}:`, errorMsg);

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

      setResultsByModel((prev) => ({
        ...prev,
        [modelKey]: {
          loading: false,
          error: "",
          data: response.data,
        },
      }));
    } catch (err) {
      if (isDev) console.error(`[AnomalyDetectionTab] Exception for ${modelKey}:`, err);

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
        const result = summary
          ? {
              status: "Completed",
              summary: `${summary.anomaly_count} records were flagged as unusual out of ${summary.total_records}.`,
              notes: state.data?.notes || "This result highlights records that differ from typical values.",
              datasetContext: state.data?.dataset_context || null,
              explanation: ANOMALY_EXPLANATIONS[model.key] || ANOMALY_EXPLANATIONS.zscore,
            }
          : null;

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
