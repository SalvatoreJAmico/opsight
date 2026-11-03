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
};

function formatAnomalyScore(value) {
  if (typeof value !== "number" || Number.isNaN(value) || !Number.isFinite(value)) {
    return "";
  }
  return value.toFixed(4);
}

export default function AnomalyDetectionTab({ onAction, pipelineCompleted }) {
  const [selectedModels, setSelectedModels] = useState({});
  const [resultsByModel, setResultsByModel] = useState({});
  const isBlocked = !pipelineCompleted;

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

    if (shouldSelect && !resultsByModel[key]?.data && !resultsByModel[key]?.loading) {
      loadModelResults(key);
    }
  };

  return (
    <div>
      <h2>Anomaly Detection</h2>
      <p>Models use the numeric target selected in Charts. Select a target there if your dataset has multiple numeric fields.</p>

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
        const anomalySample = state.data?.anomaly_sample_top10;
        const showIsolationSampleTable =
          model.key === "isolation_forest" &&
          Array.isArray(anomalySample) &&
          anomalySample.length > 0;
        const result = summary
          ? {
              status: "Completed",
              summary: `${summary.anomaly_count} records were flagged as unusual out of ${summary.total_records}.`,
              notes: state.data?.notes || "This result highlights records that differ from typical values.",
              datasetContext: state.data?.dataset_context || null,
              dataQuality: state.data?.data_quality || null,
              explanation: ANOMALY_EXPLANATIONS[model.key] || ANOMALY_EXPLANATIONS.zscore,
            }
          : null;

        const sampleTarget = state.data?.dataset_context?.value || anomalySample?.find((row) => row.target_field)?.target_field;
        const sampleColumns = [
          ...(sampleTarget ? [{ key: "target_value", label: sampleTarget }] : []),
          ...["Sales", "Profit", "Discount"]
            .filter((field) => field !== sampleTarget && anomalySample?.some((row) => row[field] != null))
            .map((field) => ({ key: field, label: field })),
        ];

        const resultFooter = showIsolationSampleTable ? (
          <div
            style={{
              marginTop: "0.75rem",
              padding: "0.6rem",
              border: "1px solid #ddd",
              borderRadius: "6px",
              background: "#fff",
              overflowX: "auto",
            }}
          >
            <h4 style={{ margin: "0 0 0.5rem 0" }}>Top 10 Anomalous Records</h4>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.95rem" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.35rem" }}>Row ID</th>
                  {sampleColumns.map((column) => (
                    <th key={column.key} style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.35rem" }}>{column.label}</th>
                  ))}
                  <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.35rem" }}>Anomaly Score</th>
                </tr>
              </thead>
              <tbody>
                {anomalySample.map((row, index) => (
                  <tr key={`${row.row_id ?? "row"}-${index}`}>
                    <td style={{ borderBottom: "1px solid #f0f0f0", padding: "0.35rem" }}>{row.row_id ?? ""}</td>
                    {sampleColumns.map((column) => (
                      <td key={column.key} style={{ borderBottom: "1px solid #f0f0f0", padding: "0.35rem" }}>
                        {row[column.key] ?? (column.key === "target_value" ? row[sampleTarget] : null) ?? ""}
                      </td>
                    ))}
                    <td style={{ borderBottom: "1px solid #f0f0f0", padding: "0.35rem" }}>
                      {formatAnomalyScore(row.anomaly_score)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null;

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
            resultFooter={resultFooter}
          />
        );
      })}
    </div>
  );
}
